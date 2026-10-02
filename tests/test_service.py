"""
tests/test_service.py — Test FastAPI service endpoints and explainability engine.

PLAN.md Section 11 & AGENT_RULES.
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
    """POST /predict with invalid data returns polite 422 error."""
    # Invalid payment_mode and negative qty
    payload = {
        "sku": "KH-RV-01",
        "payment_mode": "bitcoins",
        "qty": -5,
        "discount_pct": 150.0,
    }
    resp = client.post("/predict", json=payload)
    assert resp.status_code == 422
    data = resp.json()
    assert "detail" in data or "errors" in data


def test_predict_unknown_sku_422(client):
    """POST /predict with unknown SKU returns 422 (not silent fallback)."""
    payload = {
        "order_id": "KO_UNKNOWN_SKU",
        "sku": "KH-UNKNOWN-99",
        "payment_mode": "prepaid_upi",
        "state": "MH",
    }
    resp = client.post("/predict", json=payload)
    assert resp.status_code == 422
    data = resp.json()
    assert "Unknown SKU" in data.get("detail", "")
