# 3-Minute Screen Recording Video Script

_No slides. Live walkthrough of codebase, data audit, and web interface._

---

### [0:00 - 0:45] 1. What We Tried & Data Audit
* **Intro:** "Hi, this is the walkthrough for the Kestrel Home Returns Risk project. We set out to evaluate pre-dispatch return risk across 10,500 appliance orders."
* **Data Discoveries:**
  - "During our initial audit, we uncovered 651 duplicate partner feed rows and a 100x currency glitch in October 2025 where ₹3,500 orders were recorded in paise as ₹350,000. We repaired these deterministically."
  - "Crucially, we identified two post-order columns: `pickup_scheduled_at` and `last_service_event_type`. In the test set, these are blank. We strictly blacklisted them from feature engineering to prevent target leakage."

---

### [0:45 - 1:45] 2. Modeling, Validation & Economics
* **Model Benchmark:**
  - "We tested three architectures under strict rolling-origin temporal splits: a Dummy baseline, regularized Logistic Regression, and HistGradientBoosting."
  - "Logistic Regression emerged as the winner with an out-of-sample ROC-AUC of 0.7728 and PR-AUC of 0.3949, beating tree ensembles while maintaining full explainability."
* **Economic Reality Check (The Rupees):**
  - "We evaluated the business ask: Ritu originally wanted 95% accuracy and an order hold policy."
  - "We demonstrated that 95% accuracy is mathematically unreachable (a dumb model that predicts 'NO return' already gets 88.5%)."
  - "More importantly, holding orders induces a 12% cancellation rate, losing ₹43,700 every month on good orders. Instead, our ₹45 pre-dispatch confirmation call policy saves **+₹10,785 per month** at 700 orders."

---

### [1:45 - 2:30] 3. What We Discarded & Why
* **Discarded Approaches:**
  - "We discarded random K-Fold validation because it leaked seasonal and repeat customer history."
  - "We discarded heavy ML dependencies like SHAP and complex trees, implementing a fast, zero-dependency perturbation engine."
  - "We discarded raw text parsing after finding prompt injection attempts in delivery notes, collapsing them into clean structural templates."

---

### [2:30 - 3:00] 4. Working Service Demo & Handoff
* **Live Service Walkthrough:**
  - "Here is the FastAPI service running locally with our zero-CDN vanilla web UI."
  - "When we evaluate a high-risk COD Robot Vacuum order, it scores 78%, flags a High Risk badge, triggers a 'Confirmation Call' recommendation, and explains the top 3 drivers: customer prior return history, COD payment mode, and product category complexity."
  - "When we test a low-risk prepaid Mixer Grinder, it scores 12% and recommends immediate dispatch."
* **Wrap-up:** "All predictions are validated in `predictions.csv`, the model runs at ₹0 operating cost, and the team is ready to launch the 4-week A/B pilot on Monday. Thank you!"
