"""
service/app.py — FastAPI Returns Risk Prediction Service.

Endpoints:
  - GET /health: Service health and model status
  - GET /: Web UI interface
  - GET /catalog: Product catalog and valid categories for UI dropdowns
  - POST /predict: Score an order, returns risk band, action, top 3 reasons, warnings

Clean-machine: reads only outputs/model_lr.joblib and service/catalog.json.
No runtime dependency on data/.
"""

import json
import re
import pathlib
import sys
from typing import Optional, List, Dict, Any
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, field_validator

ROOT = pathlib.Path(__file__).resolve().parent.parent
SERVICE_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.features import FEATURE_COLS
from service.reasons import compute_top_reasons

# --------------- Constants duplicated from src/cleaning.py --------------- #
# So the service never imports data-dependent modules at runtime beyond features list
INSTALLABLE_FAMILIES = {"Ceiling Fan", "Robot Vacuum", "Water Purifier"}

_DELIVERY_NOTE_RE = re.compile(r"\d+")


def _delivery_note_template(note: str) -> str:
    """Reduce delivery_note to a template category (digits removed, truncated)."""
    if note is None or (isinstance(note, float) and np.isnan(note)):
        return "NONE"
    if not isinstance(note, str):
        note = str(note)
    tpl = _DELIVERY_NOTE_RE.sub("", note).strip()
    tpl = tpl[:80].split(".")[0].strip()
    return tpl if tpl else "NONE"


# -------------------------------------------------------------------------- #
# Initialize FastAPI App
# -------------------------------------------------------------------------- #
app = FastAPI(
    title="Kestrel Home — Pre-Dispatch Return Risk Engine",
    description="Operational ML service to score order return risk and trigger pre-dispatch confirmation calls.",
    version="1.0.0",
)


# -------------------------------------------------------------------------- #
# CSP Middleware (PLAN.md Section 11)
# -------------------------------------------------------------------------- #
@app.middleware("http")
async def add_csp_header(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "script-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:"
    )
    return response


# -------------------------------------------------------------------------- #
# Load artifacts
# -------------------------------------------------------------------------- #
MODEL_PATH = ROOT / "outputs" / "model_lr.joblib"
CATALOG_PATH = SERVICE_DIR / "catalog.json"

MODEL = None
CATALOG: Dict[str, Any] = {}
PRODUCTS_LOOKUP: Dict[str, Dict[str, Any]] = {}
VALID_STATES: List[str] = []

# Operational Threshold (Section 6 & 9: 0.34 optimal cutoff from Window A)
DECISION_THRESHOLD = 0.34
LOW_RISK_CUTOFF = 0.25
MODEL_VERSION = "1.0.0-logistic-regression"


def load_resources():
    global MODEL, CATALOG, PRODUCTS_LOOKUP, VALID_STATES
    if MODEL_PATH.exists():
        MODEL = joblib.load(MODEL_PATH)
    if CATALOG_PATH.exists():
        CATALOG = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        for prod in CATALOG.get("products", []):
            PRODUCTS_LOOKUP[prod["sku"]] = prod
        VALID_STATES = CATALOG.get("states", [])


load_resources()


# -------------------------------------------------------------------------- #
# Request & Response Schemas
# -------------------------------------------------------------------------- #
class OrderInput(BaseModel):
    order_id: Optional[str] = Field(default="KO-ONLINE-TEST", description="Unique order identifier")
    order_placed_at: Optional[str] = Field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"),
        description="Order timestamp YYYY-MM-DD HH:MM",
    )
    sku: str = Field(..., description="Product SKU (e.g. KH-RV-01, KH-MG-01)")
    sales_channel: str = Field(default="web", description="Sales channel: web, app, marketplace")
    payment_mode: str = Field(default="prepaid_upi", description="Payment mode: cod, prepaid_upi, prepaid_card, emi")
    discount_pct: float = Field(default=0.0, ge=0.0, le=100.0, description="Discount percentage (0-100)")
    qty: int = Field(default=1, ge=1, le=50, description="Quantity of items")
    order_value_inr: Optional[float] = Field(default=None, ge=0.0, description="Order value in INR")
    promised_delivery_days: int = Field(default=3, ge=1, le=30, description="Promised delivery timeline in days")
    delivery_pincode: str = Field(default="411001", description="6-digit delivery pincode or 000000")
    is_gift: str = Field(default="N", description="Gift order flag: Y or N")
    customer_prior_orders: int = Field(default=0, ge=0, description="Number of prior orders placed by customer")
    customer_prior_returns: int = Field(default=0, ge=0, description="Number of prior returns by customer")
    delivery_note: Optional[str] = Field(default="", description="Customer delivery note text")
    shield_member: str = Field(default="N", description="Shield membership flag: Y or N")
    state: str = Field(default="MH", description="Delivery State code (e.g. MH, KA, DL)")

    @field_validator("sales_channel")
    @classmethod
    def validate_channel(cls, v: str) -> str:
        v_clean = str(v).lower().strip()
        if v_clean not in {"web", "app", "marketplace"}:
            raise ValueError(f"Invalid sales_channel '{v}'. Allowed: web, app, marketplace")
        return v_clean

    @field_validator("payment_mode")
    @classmethod
    def validate_payment(cls, v: str) -> str:
        v_clean = str(v).lower().strip()
        if v_clean not in {"cod", "prepaid_upi", "prepaid_card", "emi"}:
            raise ValueError(f"Invalid payment_mode '{v}'. Allowed: cod, prepaid_upi, prepaid_card, emi")
        return v_clean

    @field_validator("is_gift")
    @classmethod
    def validate_gift(cls, v: str) -> str:
        v_clean = str(v).upper().strip()
        if v_clean not in {"Y", "N"}:
            raise ValueError(f"Invalid is_gift '{v}'. Allowed: Y, N")
        return v_clean

    @field_validator("shield_member")
    @classmethod
    def validate_shield(cls, v: str) -> str:
        v_clean = str(v).upper().strip()
        if v_clean not in {"Y", "N"}:
            raise ValueError(f"Invalid shield_member '{v}'. Allowed: Y, N")
        return v_clean


class PredictionResponse(BaseModel):
    order_id: str
    score: float = Field(..., description="Predicted return probability (0.0 to 1.0)")
    risk_band: str = Field(..., description="Risk category: low, medium, high")
    recommended_action: str = Field(..., description="Action: 'none' (proceed to dispatch) or 'confirm_call' (trigger call)")
    action_label: str = Field(..., description="Human friendly action label")
    top_3_reasons: List[str] = Field(..., description="Top 3 risk drivers in plain language")
    model_version: str
    threshold_applied: float
    warnings: List[str] = Field(default_factory=list)


# -------------------------------------------------------------------------- #
# Error Handlers
# -------------------------------------------------------------------------- #
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        field = " -> ".join(str(loc) for loc in err.get("loc", []))
        msg = err.get("msg", "Invalid input")
        errors.append(f"{field}: {msg}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Input validation error",
            "errors": errors,
            "message": "Please review and correct the submitted order fields.",
        },
    )


# -------------------------------------------------------------------------- #
# Endpoints
# -------------------------------------------------------------------------- #
@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "model_loaded": MODEL is not None,
        "model_version": MODEL_VERSION,
        "decision_threshold": DECISION_THRESHOLD,
        "products_count": len(PRODUCTS_LOOKUP),
    }


@app.get("/catalog")
def get_catalog():
    """Return product catalog and valid categories for UI dropdowns."""
    return CATALOG


@app.post("/predict", response_model=PredictionResponse)
def predict_return_risk(order: OrderInput):
    """Score pre-dispatch return risk for a single order."""
    if MODEL is None:
        load_resources()
        if MODEL is None:
            raise HTTPException(
                status_code=500,
                detail="Model artifact 'outputs/model_lr.joblib' is not available.",
            )

    warnings: List[str] = []

    # 1. Product SKU Lookup — unknown SKU is 422, not silent fallback
    sku_info = PRODUCTS_LOOKUP.get(order.sku)
    if not sku_info:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown SKU '{order.sku}'. Use GET /catalog to see valid SKUs.",
        )

    family = sku_info["family"]
    list_price_inr = float(sku_info["list_price_inr"])
    warranty_months = int(sku_info["warranty_months"])
    launch_date = pd.to_datetime(sku_info["launch_date"])
    installable = 1 if family in INSTALLABLE_FAMILIES else 0

    # 2. State validation
    state = order.state
    if VALID_STATES and state not in VALID_STATES:
        warnings.append(f"State '{state}' not in training data; defaulting to MH.")
        state = "MH"

    # 3. Shield member
    shield_member = order.shield_member

    # 4. Order Value Calculation / Fix
    if order.order_value_inr is not None and order.order_value_inr > 0:
        order_value_fixed = float(order.order_value_inr)
    else:
        order_value_fixed = float(list_price_inr * order.qty * (1.0 - (order.discount_pct / 100.0)))

    # 5. Pincode & Address
    pincode_str = str(order.delivery_pincode).strip().zfill(6)
    if pincode_str == "000000" or not pincode_str.isdigit() or len(pincode_str) != 6:
        no_address = 1
        pincode_prefix = "000"
        if pincode_str == "000000":
            warnings.append("Delivery pincode is 000000 (unverified address).")
    else:
        no_address = 0
        pincode_prefix = pincode_str[:3]

    # 6. Customer History
    prior_orders = max(0, int(order.customer_prior_orders))
    prior_returns = max(0, int(order.customer_prior_returns))
    if prior_returns > prior_orders:
        prior_orders = prior_returns
        warnings.append(f"Adjusted prior orders ({prior_orders}) to match prior returns ({prior_returns}).")

    prior_return_rate = (prior_returns / prior_orders) if prior_orders > 0 else 0.0

    # 7. Dates & Time
    try:
        placed_dt = pd.to_datetime(order.order_placed_at)
    except Exception:
        placed_dt = pd.Timestamp.now()
        warnings.append("Invalid order timestamp format. Defaulted to current time.")

    hour = int(placed_dt.hour)
    weekday = int(placed_dt.weekday())
    product_age_days = max(0, int((placed_dt - launch_date).days))

    # 8. Delivery note template
    delivery_note_template = _delivery_note_template(order.delivery_note)

    # 9. Assemble Feature Row
    feature_data = {
        "discount_pct": [float(order.discount_pct)],
        "qty": [int(order.qty)],
        "order_value_fixed": [float(order_value_fixed)],
        "promised_delivery_days": [int(order.promised_delivery_days)],
        "no_address": [int(no_address)],
        "customer_prior_orders": [int(prior_orders)],
        "customer_prior_returns": [int(prior_returns)],
        "prior_return_rate": [float(prior_return_rate)],
        "list_price_inr": [float(list_price_inr)],
        "warranty_months": [int(warranty_months)],
        "product_age_days": [int(product_age_days)],
        "installable": [int(installable)],
        "hour": [int(hour)],
        "weekday": [int(weekday)],
        "sales_channel": [str(order.sales_channel)],
        "payment_mode": [str(order.payment_mode)],
        "is_gift": [str(order.is_gift)],
        "family": [str(family)],
        "sku": [str(order.sku)],
        "shield_member": [str(shield_member)],
        "state": [str(state)],
        "pincode_prefix": [str(pincode_prefix)],
        "delivery_note_template": [str(delivery_note_template)],
    }

    feature_df = pd.DataFrame(feature_data)[FEATURE_COLS]

    # Predict score
    score = float(MODEL.predict_proba(feature_df)[:, 1][0])

    # Assign risk band and recommended action
    if score >= DECISION_THRESHOLD:
        risk_band = "high"
        recommended_action = "confirm_call"
        action_label = "Trigger Pre-Dispatch Confirmation Call"
    elif score >= LOW_RISK_CUTOFF:
        risk_band = "medium"
        recommended_action = "none"
        action_label = "Proceed to Standard Dispatch (Monitor)"
    else:
        risk_band = "low"
        recommended_action = "none"
        action_label = "Proceed to Dispatch Immediately"

    # Compute top 3 reasons via perturbation
    top_reasons = compute_top_reasons(MODEL, feature_df, score, top_k=3)

    return PredictionResponse(
        order_id=order.order_id or "KO-ONLINE-ORDER",
        score=round(score, 4),
        risk_band=risk_band,
        recommended_action=recommended_action,
        action_label=action_label,
        top_3_reasons=top_reasons,
        model_version=MODEL_VERSION,
        threshold_applied=DECISION_THRESHOLD,
        warnings=warnings,
    )


# -------------------------------------------------------------------------- #
# Serve Single-Page Web Application
# -------------------------------------------------------------------------- #
STATIC_DIR = pathlib.Path(__file__).resolve().parent / "static"


@app.get("/", response_class=HTMLResponse)
def serve_ui():
    """Serve the single-page application HTML."""
    html_file = STATIC_DIR / "index.html"
    if html_file.exists():
        return HTMLResponse(content=html_file.read_text(encoding="utf-8"))
    return HTMLResponse(
        content="<h2>Kestrel Home Return Prediction Engine</h2><p>Static UI not found.</p>",
        status_code=404,
    )
