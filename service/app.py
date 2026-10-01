"""
service/app.py — FastAPI Returns Risk Prediction Service.

Endpoints:
  - GET /health: Service health and model status
  - GET /: Web UI interface
  - POST /predict: Score an order, returns risk band, action, top 3 reasons, warnings
"""

import pathlib
import sys
from typing import Optional, List, Dict, Any
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, field_validator

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.features import FEATURE_COLS
from src.cleaning import _delivery_note_template, INSTALLABLE_FAMILIES
from service.reasons import compute_top_reasons

# Initialize FastAPI App
app = FastAPI(
    title="Kestrel Home — Pre-Dispatch Return Risk Engine",
    description="Operational ML service to score order return risk and trigger pre-dispatch confirmation calls.",
    version="1.0.0",
)

# Load artifacts and lookup tables
MODEL_PATH = ROOT / "outputs" / "model_lr.joblib"
PRODUCTS_PATH = ROOT / "data" / "products.csv"
CUSTOMERS_PATH = ROOT / "data" / "customers.csv"

MODEL = None
PRODUCTS_DF = None
CUSTOMERS_DF = None
PRODUCTS_LOOKUP: Dict[str, Dict[str, Any]] = {}
CUSTOMERS_LOOKUP: Dict[str, Dict[str, Any]] = {}

# Operational Threshold (Section 6 & 9: 0.34 optimal cutoff from Window A)
DECISION_THRESHOLD = 0.34
LOW_RISK_CUTOFF = 0.25
MODEL_VERSION = "1.0.0-logistic-regression"


def load_resources():
    global MODEL, PRODUCTS_DF, CUSTOMERS_DF, PRODUCTS_LOOKUP, CUSTOMERS_LOOKUP
    if MODEL_PATH.exists():
        MODEL = joblib.load(MODEL_PATH)
    if PRODUCTS_PATH.exists():
        PRODUCTS_DF = pd.read_csv(PRODUCTS_PATH)
        for _, row in PRODUCTS_DF.iterrows():
            PRODUCTS_LOOKUP[row["sku"]] = row.to_dict()
    if CUSTOMERS_PATH.exists():
        CUSTOMERS_DF = pd.read_csv(CUSTOMERS_PATH)
        for _, row in CUSTOMERS_DF.iterrows():
            CUSTOMERS_LOOKUP[row["customer_id"]] = row.to_dict()


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
    customer_id: Optional[str] = Field(default=None, description="Customer ID for lookup (KCxxxxx)")
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
    shield_member: Optional[str] = Field(default=None, description="Shield membership flag: Y or N")
    state: Optional[str] = Field(default=None, description="Delivery State code (e.g. MH, KA, DL)")

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
        "customers_count": len(CUSTOMERS_LOOKUP),
    }


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

    # 1. Product SKU Lookup
    sku_info = PRODUCTS_LOOKUP.get(order.sku)
    if sku_info:
        family = sku_info["family"]
        list_price_inr = float(sku_info["list_price_inr"])
        warranty_months = int(sku_info["warranty_months"])
        launch_date = pd.to_datetime(sku_info["launch_date"])
        installable = 1 if family in INSTALLABLE_FAMILIES else 0
    else:
        # Fallback for unknown SKU
        warnings.append(f"SKU '{order.sku}' not recognized in product catalog. Using default estimates.")
        family = "Mixer Grinder"
        list_price_inr = 4000.0
        warranty_months = 12
        launch_date = pd.to_datetime("2024-01-01")
        installable = 0

    # 2. Customer Lookup / Fallback
    cust_info = CUSTOMERS_LOOKUP.get(order.customer_id) if order.customer_id else None
    if cust_info:
        shield_member = order.shield_member if order.shield_member is not None else cust_info.get("shield_member", "N")
        state = order.state if order.state is not None else cust_info.get("state", "MH")
    else:
        shield_member = order.shield_member if order.shield_member is not None else "N"
        state = order.state if order.state is not None else "MH"

    shield_member = str(shield_member).upper()
    if shield_member not in {"Y", "N"}:
        shield_member = "N"

    # 3. Order Value Calculation / Fix
    if order.order_value_inr is not None and order.order_value_inr > 0:
        order_value_fixed = float(order.order_value_inr)
    else:
        order_value_fixed = float(list_price_inr * order.qty * (1.0 - (order.discount_pct / 100.0)))

    # 4. Pincode & Address
    pincode_str = str(order.delivery_pincode).strip().zfill(6)
    if pincode_str == "000000" or not pincode_str.isdigit() or len(pincode_str) != 6:
        no_address = 1
        pincode_prefix = "000"
        if pincode_str == "000000":
            warnings.append("Delivery pincode is 000000 (unverified address).")
    else:
        no_address = 0
        pincode_prefix = pincode_str[:3]

    # 5. Customer History
    prior_orders = max(0, int(order.customer_prior_orders))
    prior_returns = max(0, int(order.customer_prior_returns))
    if prior_returns > prior_orders:
        prior_orders = prior_returns
        warnings.append(f"Adjusted prior orders ({prior_orders}) to match prior returns ({prior_returns}).")

    prior_return_rate = (prior_returns / prior_orders) if prior_orders > 0 else 0.0

    # 6. Dates & Time
    try:
        placed_dt = pd.to_datetime(order.order_placed_at)
    except Exception:
        placed_dt = pd.Timestamp.now()
        warnings.append("Invalid order timestamp format. Defaulted to current time.")

    hour = int(placed_dt.hour)
    weekday = int(placed_dt.weekday())
    product_age_days = max(0, int((placed_dt - launch_date).days))

    # 7. Delivery note template
    delivery_note_template = _delivery_note_template(order.delivery_note)

    # 8. Assemble Feature Row
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
