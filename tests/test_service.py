"""
tests/test_service.py — Test FastAPI service endpoints and explainability engine.

Tests that need data/ files skip cleanly with pytest.skip.
"""

import pytest
from fastapi.testclient import TestClient

from service.app import app, DECISION_THRESHOLD


@pytest.fixture
def client():
    return TestClient(app)


# ------------------------------------------------------------------ #
# Health & UI
# ------------------------------------------------------------------ #
def test_health_endpoint(client):
    """GET /health must return 200, model loaded status and version."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["model_loaded"] is True
    assert "1.0.0" in data["model_version"]
    assert data["decision_threshold"] == DECISION_THRESHOLD


def test_ui_endpoint(client):
    """GET / must serve the static HTML application without external CDN dependencies."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "Kestrel" in resp.text
    # Verify no external CDN or Google font links
    assert "fonts.googleapis.com" not in resp.text
    assert "cdn." not in resp.text


# ------------------------------------------------------------------ #
# Catalog endpoint
# ------------------------------------------------------------------ #
def test_catalog_endpoint(client):
    """GET /catalog returns products and states from catalog.json."""
    resp = client.get("/catalog")
    assert resp.status_code == 200
    data = resp.json()
    assert "products" in data
    assert len(data["products"]) == 21
    assert "states" in data
    assert len(data["states"]) > 0
    assert "categories" in data
    # Every product must have sku, family, list_price_inr
    for p in data["products"]:
        assert "sku" in p
        assert "family" in p
        assert "list_price_inr" in p


# ------------------------------------------------------------------ #
# CSP header
# ------------------------------------------------------------------ #
def test_csp_header_present(client):
    """All responses must include Content-Security-Policy header."""
    for path in ["/health", "/catalog", "/"]:
        resp = client.get(path)
        csp = resp.headers.get("content-security-policy", "")
        assert "default-src" in csp, f"CSP missing on {path}"
        assert "'self'" in csp


# ------------------------------------------------------------------ #
# Predictions
# ------------------------------------------------------------------ #
def test_predict_low_risk(client):
    """POST /predict for low-risk prepaid order."""
    payload = {
        "order_id": "KO_TEST_LOW",
        "sku": "KH-MG-01",  # Mixer grinder
        "payment_mode": "prepaid_upi",
        "sales_channel": "web",
        "discount_pct": 0.0,
        "qty": 1,
        "promised_delivery_days": 2,
        "delivery_pincode": "411001",
        "customer_prior_orders": 5,
        "customer_prior_returns": 0,
        "shield_member": "N",
        "is_gift": "N",
        "state": "MH",
    }
    resp = client.post("/predict", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert 0.0 <= data["score"] <= 1.0
    assert data["risk_band"] in ["low", "medium"]
    assert data["recommended_action"] == "none"
    assert len(data["top_3_reasons"]) == 3
    assert all(isinstance(r, str) and len(r) > 10 for r in data["top_3_reasons"])


def test_predict_high_risk(client):
    """POST /predict for high-risk COD order with prior returns."""
    payload = {
        "order_id": "KO_TEST_HIGH",
        "sku": "KH-RV-01",  # Robot vacuum (high base return)
        "payment_mode": "cod",
        "sales_channel": "marketplace",
        "discount_pct": 30.0,
        "qty": 2,
        "promised_delivery_days": 7,
        "delivery_pincode": "411001",
        "customer_prior_orders": 3,
        "customer_prior_returns": 2,  # 66% return history
        "shield_member": "Y",
        "is_gift": "N",
        "state": "MH",
    }
    resp = client.post("/predict", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert 0.0 <= data["score"] <= 1.0
    assert data["score"] >= DECISION_THRESHOLD
    assert data["risk_band"] == "high"
    assert data["recommended_action"] == "confirm_call"
    assert len(data["top_3_reasons"]) == 3


def test_predict_validation_error(client):
    """POST /predict with invalid payment_mode returns polite 422 error."""
    payload = {
        "sku": "KH-RV-01",
        "payment_mode": "bitcoins",
    }
    resp = client.post("/predict", json=payload)
    assert resp.status_code == 422
    data = resp.json()
    assert "detail" in data
    assert "errors" in data
    assert data["message"] == "Validation error"
    assert any("payment_mode" in e for e in data["errors"])


def test_predict_unknown_sku_422(client):
    """POST /predict with unknown SKU returns 422 standardized shape."""
    payload = {
        "order_id": "KO_UNKNOWN_SKU",
        "sku": "KH-UNKNOWN-99",
        "payment_mode": "prepaid_upi",
        "state": "MH",
    }
    resp = client.post("/predict", json=payload)
    assert resp.status_code == 422
    data = resp.json()
    assert "Unknown SKU" in data["detail"]
    assert "errors" in data
    assert any("sku" in e for e in data["errors"])
    assert data["message"] == "Validation error"


def test_predict_invalid_pincode_422(client):
    """POST /predict with invalid pincode '12' returns 422 standardized shape."""
    payload = {
        "sku": "KH-RV-01",
        "delivery_pincode": "12",
    }
    resp = client.post("/predict", json=payload)
    assert resp.status_code == 422
    data = resp.json()
    assert "Invalid delivery pincode" in data["detail"]
    assert "errors" in data
    assert any("delivery_pincode" in e for e in data["errors"])
    assert data["message"] == "Validation error"


def test_predict_discount_clamp_sweep(client):
    """Sweep discount percentage: 0%, 30%, 80% (clamped to 60 with warning)."""
    # 0% discount
    r0 = client.post("/predict", json={"sku": "KH-MG-01", "discount_pct": 0.0})
    assert r0.status_code == 200
    assert not any("Discount" in w for w in r0.json().get("warnings", []))

    # 30% discount
    r30 = client.post("/predict", json={"sku": "KH-MG-01", "discount_pct": 30.0})
    assert r30.status_code == 200
    assert not any("Discount" in w for w in r30.json().get("warnings", []))

    # 80% discount (clamped to 60.0)
    r80 = client.post("/predict", json={"sku": "KH-MG-01", "discount_pct": 80.0})
    assert r80.status_code == 200
    warnings = r80.json().get("warnings", [])
    assert any("Discount 80.0% clamped" in w for w in warnings)


def test_predict_qty_clamp_sweep(client):
    """Sweep quantity: 1, 2, 10 (clamped to 2 with warning)."""
    r1 = client.post("/predict", json={"sku": "KH-MG-01", "qty": 1})
    assert r1.status_code == 200
    assert not any("Quantity" in w for w in r1.json().get("warnings", []))

    r2 = client.post("/predict", json={"sku": "KH-MG-01", "qty": 2})
    assert r2.status_code == 200
    assert not any("Quantity" in w for w in r2.json().get("warnings", []))

    r10 = client.post("/predict", json={"sku": "KH-MG-01", "qty": 10})
    assert r10.status_code == 200
    warnings = r10.json().get("warnings", [])
    assert any("Quantity 10 clamped" in w for w in warnings)


def test_predict_order_value_clamp_sweep(client):
    """Sweep order value: 5000 (normal), 1000000 (clamped to 60000 with warning)."""
    r_normal = client.post("/predict", json={"sku": "KH-MG-01", "order_value_inr": 5000.0})
    assert r_normal.status_code == 200
    assert not any("Order value" in w for w in r_normal.json().get("warnings", []))

    r_huge = client.post("/predict", json={"sku": "KH-MG-01", "order_value_inr": 1000000.0})
    assert r_huge.status_code == 200
    warnings = r_huge.json().get("warnings", [])
    assert any("Order value" in w and "clamped" in w for w in warnings)

