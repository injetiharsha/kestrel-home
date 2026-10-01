# Deliberate Trade-offs & Rejected Approaches (Form Q7)

This document records engineering and statistical approaches that were evaluated and deliberately rejected, along with the rationale.

---

### 1. Rejection of Deep Learning & External LLM Scoring
* **Alternative Considered:** Calling commercial LLMs or deep neural networks for text and order scoring.
* **Why Rejected:** 
  1. High per-prediction API cost (violates Farhan's ₹0 marginal cost constraint).
  2. Rate limit fragility (5 RPM / 20 RPD quotas cause operational bottlenecks at dispatch).
  3. Extreme latency (1–3 seconds vs 2 ms for Logistic Regression).
  4. Tabular data with 10.5k rows does not benefit from deep representation learning.

---

### 2. Rejection of Heavy Non-Linear Trees (HistGradientBoosting / XGBoost / LightGBM)
* **Alternative Considered:** Non-linear gradient boosted trees for return classification.
* **Why Rejected:** In our strict rolling temporal cross-validation, `LogisticRegression` outperformed `HistGradientBoosting` on both discrimination (AUC 0.7728 vs 0.7546) and economics (+₹12,436 vs +₹11,282). Logistic regression generalized better to future quarters, avoided tree-overfitting on categorical noise, and simplified linear perturbation explainability.

---

### 3. Rejection of Random K-Fold Cross-Validation
* **Alternative Considered:** Standard random 5-fold or 10-fold cross-validation.
* **Why Rejected:** Random splits leak seasonal patterns and future customer order history into training sets, artificially inflating estimated AUC to ~0.82–0.84. Rolling-origin temporal splits (`Fold 1`, `Fold 2`, `Fold 3`) provide realistic out-of-sample backtesting that mirrors live deployment.

---

### 4. Rejection of Synthetic Oversampling (SMOTE)
* **Alternative Considered:** Synthesizing return samples via SMOTE to balance classes.
* **Why Rejected:** SMOTE distorts the baseline probability calibration of logistic regression, making predicted probabilities unrepresentative of empirical base return rates (~11.5%) and undermining economic threshold calculations. Balanced class weighting (`class_weight='balanced'`) preserved proper probabilistic ranking without distorting feature spaces.

---

### 5. Rejection of Heavy SHAP Dependency for Explainability
* **Alternative Considered:** Installing and running the full Python SHAP library for post-hoc explanation.
* **Why Rejected:** SHAP introduces heavy native C++ build dependencies that risk failure on fresh clean machines. Replaced with model-agnostic feature perturbation against baseline values, yielding instant, deterministic top-3 risk reasons with zero additional dependencies.
