# Deliberate Trade-offs & Rejected Approaches (Form Q7)

This document records engineering and statistical approaches that were evaluated and deliberately rejected, along with the rationale.

---

### 1. Rejection of Deep Learning & External LLM Scoring
* **Alternative Considered:** Calling commercial LLMs or deep neural networks for text and order scoring.
* **Why Rejected:** 
  1. High per-prediction API cost (violates ₹0 marginal cost constraint).
  2. Rate limit fragility (5 RPM / 20 RPD quotas cause operational bottlenecks at dispatch).
  3. Extreme latency (1–3 seconds vs 2 ms for Logistic Regression).
  4. Tabular data with 10.5k rows does not benefit from deep representation learning.

---

### 2. Rejection of Heavy Non-Linear Tree Ensembles (HistGradientBoosting)
* **Alternative Considered:** Non-linear gradient boosted trees (`HistGradientBoostingClassifier`) for return classification.
* **Why Rejected:** In my strict rolling temporal cross-validation, `LogisticRegression` outperformed `HistGradientBoosting` on both discrimination (AUC 0.7728 vs 0.7546) and economics (+₹12,436 vs +₹11,282 on Fold 3). Logistic regression generalized better to future quarters, avoided tree-overfitting on categorical noise, and enabled clean linear perturbation explainability.

---

### 3. Rejection of Random K-Fold Cross-Validation
* **Alternative Considered:** Standard random 5-fold or 10-fold cross-validation.
* **Why Rejected:** Random splits violate temporal causality by mixing past and future orders. Rolling-origin temporal splits (`Fold 1`, `Fold 2`, `Fold 3`) provide realistic out-of-sample backtesting that mirrors live deployment.

---

### 4. Rejection of Post-Order Leakage Columns
* **Alternative Considered:** Using `pickup_scheduled_at` or `last_service_event_type`.
* **Why Rejected:** `pickup_scheduled_at` is populated upon return approval (post-dispatch), and `last_service_event_type` records service events up to export time. Both were blacklisted and dropped to ensure strict pre-dispatch validity.

---

### 5. Rejection of Heavy SHAP Dependency for Explainability
* **Alternative Considered:** Installing and running the full Python SHAP library for post-hoc explanation.
* **Why Rejected:** SHAP introduces heavy native C++ build dependencies that risk failure on fresh clean machines. Replaced with model-agnostic feature perturbation against baseline values (`service/reasons.py`), yielding instant, deterministic top-3 risk reasons with zero additional dependencies.

---

### 6. Non-Informative Feature Shortcut
* **Trade-off:** Features `hour`, `weekday`, `delivery_note_template`, and `pincode_prefix` add no measurable signal (ablation AUC changes span +0.0002 to +0.004).
* **Why Retained:** They remain in the final model because I did not retrain after the expected score and predictions were locked. A cleaner future iteration would drop them.
