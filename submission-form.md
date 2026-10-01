# Kestrel Home — Engagement Submission Form

---

### GitHub Repository URL
`https://github.com/injetiharsha/kestrel-home` (Private Repository)

---

### Q1: What was built, the operational decision, the core number, and the rupees
* **What Was Built:** An end-to-end machine learning system and operational decision engine for Kestrel Home D2C appliances, featuring an audit-repaired feature engineering pipeline, regularized Logistic Regression classifier, model-agnostic explainability engine, FastAPI service, and a self-contained zero-CDN web console.
* **The Decision:** Implement **pre-dispatch confirmation calls** (₹45/call) on orders exceeding the 0.34 risk threshold. Explicitly reject dispatch holding (which triggers a 12% customer cancellation rate and destroys gross margin on good orders). Shield members receive VIP confirmation calls, never holds.
* **The Core Number:** **ROC-AUC of 0.7728** (95% CI: [0.739, 0.803]) and **PR-AUC of 0.3949** across out-of-sample temporal backtests, capturing **>81% of all returning orders** before dispatch.
* **The Rupees:** At 700 orders/month, the call policy delivers **+₹10,785 in net monthly profit** (~₹1.3 Lakhs/year) after subtracting agent call costs. By comparison, dispatch holding results in a net loss of **-₹43,722/month**, and status quo causes **-₹92,252/month** in return losses. Model operational cost is **₹0/month**.
* _Source Reference:_ [`memo/memo.md`](memo/memo.md), [`outputs/economics.json`](outputs/economics.json)

---

### Q2: Expected score on the hidden test set, evaluation metric, rationale, and estimation methodology
* **Evaluation Metric:** Primary: **ROC-AUC**; Secondary: **PR-AUC (Average Precision)**. The test set requires probabilistic ranking scores; ranking discrimination and precision are standard for extreme class imbalance (~11.5% base return rate).
* **Expected Point Estimate:** **ROC-AUC = 0.77** (Expected Range / 95% CI: **0.74 to 0.80**). PR-AUC: **0.34 to 0.45**.
* **Estimation Methodology:** Evaluated via 3 rolling-origin temporal splits (`Fold 1`, `Fold 2`, `Fold 3`) on 10,504 cleaned historical orders. The threshold (`0.34`) was tuned on Window A (`Fold 1`) and verified out-of-sample on later quarters (`Fold 2`: 0.7640, `Fold 3`: 0.7728).
* **Drift & Seasonal Caveats:** Test set covers Q3 (Jul–Sep 2026 Monsoon season) which may exhibit category shifts (e.g. Heaters vs Fans), but sensitivity backtests dropping late-window orders confirm high model stability ($\Delta\text{AUC} = -0.0053$).
* _Source Reference:_ [`notes/expected_score.md`](notes/expected_score.md) (Locked and committed before final inference)

---

### Q3: How we know the model works, validation split design, error rates, and failure modes
* **Validation Design:** Strictly time-based rolling folds (`Fold 1` $\le$ Sep 2025 $\rightarrow$ Oct-Dec 2025 test; `Fold 2` $\le$ Dec 2025 $\rightarrow$ Jan-Mar 2026 test; `Fold 3` $\le$ Mar 2026 $\rightarrow$ Apr-Jun 2026 test). No random splits or future leakage.
* **Model Benchmark:** `LogisticRegression` (AUC 0.7728, PR-AUC 0.3949) consistently outperformed `HistGradientBoosting` (AUC 0.7546, PR-AUC 0.3633) and `DummyPrior` (AUC 0.5000, PR-AUC 0.1146).
* **Failure Modes & Error Analysis:**
  1. *95% Accuracy Fallacy:* An "always predict NO" baseline achieves 88.5% accuracy but catches 0 returns. True discrimination requires AUC.
  2. *False Negatives:* Highest in low base-rate categories like Ceiling Fans (56.5% FN) and Prepaid UPI (44.9% FN); lowest in COD orders (only 14.3% FN, capturing 85.7% of returns).
  3. *Shield False Positives:* Shield members have a 52.8% FP rate due to high baseline return volume (20.7% return rate). Mitigated by polite VIP calls rather than order holds.
  4. *Calibration:* Verified monotonic alignment between predicted probabilities and actual return rates across all 10 deciles.
* _Source Reference:_ [`validation/EVIDENCE.md`](validation/EVIDENCE.md)

---

### Q4: Strategic changes, scope narrowing, and client pushbacks
* **Pushed Back on 95% Accuracy:** Rejected the 95% accuracy goal as mathematically impossible on 11.5% imbalanced data; educated stakeholders to measure ROC-AUC and net rupee savings.
* **Pushed Back on Order Holds:** Demonstrated that holding orders destroys ₹43.7k/month via a 12% customer cancellation rate, replacing it with a +₹10.8k/month pre-dispatch confirmation call policy.
* **Pushed Back on Treating Shield Members as Standard:** Shield members buy ~3 appliances/year and represent maximum LTV; established a VIP confirmation call policy to preserve loyalty.
* **Corrected Return Cost Baseline:** Enforced the ₹1,150 all-in unit return cost from Finance rather than the inaccurate ₹600 shipping-only figure.
* **Dropped Target Leakage Columns:** Removed post-order database artifacts (`last_service_event_type`, `pickup_scheduled_at`) to guarantee operational feasibility.
* _Source Reference:_ [`notes/decisions.md`](notes/decisions.md)

---

### Q5: Data anomalies, handoff defects, and remediation
* **651 Partner Feed Duplicate Orders:** Deduplicated by keeping `source == 'crm'` exclusively, dropping 651 redundant rows.
* **October 2025 Currency Inflation (x100 Bug):** Repaired 700 orders recorded in paise rather than rupees during the festive campaign by dividing values >5x expected list price by 100.
* **Pincode `000000` & Missing Address Flag:** Disproved the README assumption that `000000` was purely partner walk-ins; encoded it as a distinct `no_address = 1` feature.
* **Right-Censoring Return Lag:** Audited empirical return resolution lag (up to 19 days) and proved stability via a 21-day cutoff sensitivity test.
* **Delivery Note Prompt Injection:** Discovered 4 malicious injection attacks in raw notes; sanitized text into structured categorical templates (`NONE`, `Leave with security`, `Call before delivery`, `Office address`).
* _Source Reference:_ [`notes/known_issues.md`](notes/known_issues.md), [`notes/data_audit.md`](notes/data_audit.md)

---

### Q6: Cost per prediction and monthly operating cost with full arithmetic
* **Cost per Prediction:** **₹0.00** (< 2.0 ms CPU execution latency).
* **Monthly Operating Cost:** **₹0.00 / month** (Zero paid external APIs or GPU infrastructure).
* **Monthly Economic Arithmetic (per 700 Orders):**
  - Status Quo Return Losses (700 $\times$ 11.46% $\times$ ₹1,150): **-₹92,252.00 / month**
  - Calls Executed (346.8 orders @ ₹45): **₹15,607.00**
  - Returns Prevented (22.95 avoided @ ₹1,150): **₹26,392.50 saved**
  - Net Monthly Gain: ₹26,392.50 (Saved) - ₹15,607.00 (Call Cost) = **+₹10,785.50 / month**
* _Source Reference:_ [`notes/cost.md`](notes/cost.md)

---

### Q7: Deliberately left out and rejected approaches
* **External LLM Scoring:** Rejected due to ₹ cost per prediction, rate limits, and latency.
* **Complex Gradient Boosted Trees (HistGBT/XGBoost):** Rejected after temporal backtests proved regularized Logistic Regression achieved superior out-of-sample AUC (+0.018) and better generalization.
* **Random K-Fold Validation:** Rejected because it masks temporal leakage and inflates performance.
* **SMOTE Oversampling:** Rejected because it distorts baseline probability calibration.
* **SHAP Library:** Rejected heavy C++ dependencies in favor of lightweight feature perturbation.
* _Source Reference:_ [`notes/tradeoffs.md`](notes/tradeoffs.md)

---

### Q8: Built or discovered unasked
* **Adversarial Prompt Injection Sanitizer:** Regex cleaning layer that neutralized security injections in customer delivery notes.
* **Zero-CDN Offline Web Console:** Complete, polished HTML/CSS/JS frontend operating 100% offline with zero external font/CDN dependencies.
* **Model-Agnostic Perturbation Explainability Engine:** Generates instant plain-English risk driver sentences for support agents.
* **Censoring Lag & Decile Calibration Backtesting:** Automated sensitivity scripts verifying right-censoring immunity and calibration across 10 deciles.
* _Source Reference:_ [`notes/extras.md`](notes/extras.md)

---

### Q9: AI tool usage, audit log, and video recording link
* **AI Tooling Used:** Google DeepMind Antigravity Pair Programming System (Claude Opus 4.6, Gemini 3.7 Flash) for code scaffolding, data audit script generation, temporal cross-validation, and evidence documentation.
* **Full Audit Log:** All prompts, execution timestamps, and contributions recorded in [`notes/LOG.md`](notes/LOG.md) and [`prompts/`](prompts/).
* **Discarded Concepts:** Documented in [`notes/discarded.md`](notes/discarded.md).
* **Screen Recording Video Link:** `https://drive.google.com/drive/folders/kestrel-home-video-submission` (Script: [`notes/video_script.md`](notes/video_script.md))
* _Source Reference:_ [`notes/LOG.md`](notes/LOG.md), [`notes/discarded.md`](notes/discarded.md), [`notes/video_script.md`](notes/video_script.md)

---

### Q10: Monday team handoff priorities
1. **Launch 4-Week 50/50 A/B Confirmation Call Pilot:** Deploy `POST /predict` to fulfillment; randomly split orders $\ge 0.34$ into Treatment (called) and Control (uncalled) to validate the +₹10.8k/month return savings live.
2. **Equip Support Agents with Top 3 Plain-Language Reasons:** Train customer service to use API-generated risk reasons for helpful, targeted customer conversations.
3. **Establish Monthly Automated Retraining & Drift Monitoring:** Schedule monthly cron jobs for `scripts/train.py` to continuously adapt to seasonal shifts and customer history expansion.
* _Source Reference:_ [`notes/handoff.md`](notes/handoff.md)
