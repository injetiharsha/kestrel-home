# Kestrel Home — Returns Risk Prediction Engine

> **Variant A: Pre-Dispatch Order Verification System**  
> Operational machine learning engine and decision support service for D2C appliances.

---

## 1. Quickstart (Fresh Machine / Local Run)

This project requires **Python 3.10+** and zero external cloud API keys.

### 1.1. Setup Virtual Environment
```bash
# Clone or navigate to the repository
git clone https://github.com/injetiharsha/kestrel-home.git
cd kestrel-home

# Create and activate virtual environment
python -m venv .venv

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 1.2. Run Test Suite
Verify data blacklist rules, cleaning pipelines, and API endpoints:
```bash
python -m pytest -v
```

### 1.3. Launch the Web Service
```bash
uvicorn service.app:app --host 0.0.0.0 --port 8000
```
Open your browser at **`http://localhost:8000`** to access the interactive web screening dashboard.

---

## 2. API Endpoints

### `POST /predict`
Scores pre-dispatch return risk for a single order.

**Request Body:**
```json
{
  "order_id": "KO26-TEST-001",
  "sku": "KH-RV-01",
  "payment_mode": "cod",
  "sales_channel": "marketplace",
  "discount_pct": 20.0,
  "qty": 1,
  "delivery_pincode": "411001",
  "promised_delivery_days": 5,
  "customer_prior_orders": 3,
  "customer_prior_returns": 2,
  "shield_member": "Y",
  "is_gift": "N",
  "delivery_note": "Call before delivery"
}
```

**Response Body (200 OK):**
```json
{
  "order_id": "KO26-TEST-001",
  "score": 0.7852,
  "risk_band": "high",
  "recommended_action": "confirm_call",
  "action_label": "Trigger Pre-Dispatch Confirmation Call",
  "top_3_reasons": [
    "Customer has a history of high returns (67% return rate on prior orders).",
    "Cash on Delivery (COD) payment mode carries higher rejection and return risk.",
    "Shield membership accounts show significantly higher warranty and return claim frequency."
  ],
  "model_version": "1.0.0-logistic-regression",
  "threshold_applied": 0.34,
  "warnings": []
}
```

### `GET /health`
Returns health status, loaded model version, and catalog dimensions.

---

## 3. Project Structure

```
├── data/                  # Raw dataset files (gitignored in production)
├── memo/
│   └── memo.md            # One-page executive memo to Ritu (Head of Ops)
├── notes/
│   ├── cost.md            # Rs 0 prediction cost arithmetic
│   ├── data_audit.md      # P1 audit findings & data verification
│   ├── decisions.md       # Strategic pushbacks and decision rationale
│   ├── discarded.md       # Discarded models and approaches
│   ├── expected_score.md  # Expected ROC-AUC lock-in before final fit
│   ├── extras.md          # Unasked value (security, offline UI, explainability)
│   ├── handoff.md         # 3 Monday handoff priorities
│   ├── known_issues.md    # Audit anomalies and bug fixes
│   ├── tradeoffs.md       # Deliberate engineering trade-offs
│   ├── video_script.md    # 3-minute screen recording script
│   └── STATUS.md          # Phase progress tracker
├── outputs/
│   ├── economics.json     # Full JSON metrics, ablations, sensitivities
│   ├── model_lr.joblib    # Trained production Logistic Regression pipeline
│   └── predictions.csv    # Final test set predictions (2,096 rows)
├── prompts/               # Verbatim prompt history (01 to 08)
├── scripts/
│   ├── audit.py           # Data audit runner
│   ├── log.py             # CLI logging tool for notes/LOG.md
│   ├── predict.py         # Test inference runner
│   └── train.py           # End-to-end training & cross-validation runner
├── service/
│   ├── app.py             # FastAPI backend
│   ├── reasons.py         # Model-agnostic perturbation explainability
│   └── static/index.html  # Zero-CDN vanilla HTML/CSS/JS frontend
├── src/
│   ├── cleaning.py        # Deduplication, Oct-fix, address standardization
│   ├── evaluation.py      # Rolling time folds, metrics, rupee economics
│   ├── features.py        # Feature matrix builder (strict blacklist)
│   └── models.py          # Scikit-learn model pipelines
├── tests/
│   ├── test_blacklist.py  # 18 blacklist & leakage prevention tests
│   └── test_service.py    # 6 API and explainability tests
├── requirements.txt       # Pinned dependencies
├── SUBMISSION.md          # Complete engagement submission form
└── PLAN.md                # Single source of truth plan & change log
```

---

## 4. Key Performance & Business Numbers

* **Model Discrimination:** ROC-AUC = **0.7728** [95% CI: 0.739 – 0.803], PR-AUC = **0.3949** across out-of-sample temporal cross-validation folds.
* **Operating Decision:** Proactive confirmation call (₹45/call) on orders $\ge 0.34$ threshold.
* **Monthly Economic Benefit:** **+₹10,785 net savings/month** at 700 orders (preventing ~23 returns/month).
* **Dispatch Hold Policy Result:** Holding orders causes a 12% customer cancellation rate, losing **-₹43,722/month**.
* **Marginal Software Operating Cost:** **₹0.00 / month** (Runs locally on CPU in < 2 ms).
