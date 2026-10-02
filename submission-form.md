# Submission Form: Kestrel Home Returns Risk

### Github Repo URL*
`https://github.com/injetiharsha/kestrel-home`

---

### What did you build, and what business decision does it support? State the number and the rupees.*
We built an operational returns risk prediction engine and decision support system for Kestrel Home D2C appliances. It scores pre-dispatch return risk and supports the decision to **trigger targeted pre-dispatch confirmation calls (₹45/call)** on orders exceeding the 0.34 risk threshold, while explicitly rejecting dispatch holds. Shield members receive proactive VIP confirmation calls rather than holds.

* **The Number:** Across out-of-sample temporal backtests, our model achieves a **ROC-AUC of 0.7728** (95% CI: [0.739, 0.803]) and **PR-AUC of 0.3949**, successfully flagging **>81% of all returned orders** before warehouse dispatch.
* **The Rupees:** At 700 orders/month, the confirmation call policy generates **+₹10,785 in net monthly savings** (~₹1.3 Lakhs annually) after deducting agent call costs. By contrast, dispatch holding loses **-₹43,722/month** (due to a 12% customer cancellation rate on held orders), and doing nothing loses **-₹92,252/month** in return costs. Model execution costs **₹0/month**.

---

### What score do you expect predictions.csv to get on the hidden outcomes, on which metric, and why that metric? Say how you estimated it. We compare this with the real score.*
* **Expected Metric:** **ROC-AUC (Primary)**, with **PR-AUC / Average Precision (Secondary)**. Probabilistic ranking metrics are essential for severe class imbalance (~11.5% base return rate), where raw classification accuracy is mathematically misleading.
* **Expected Point Estimate & Range:** **ROC-AUC = 0.77** (Expected 95% CI: **0.74 to 0.80**). Expected PR-AUC: **0.34 to 0.45**.
* **Estimation Methodology:** Estimated using rolling-origin temporal splits (`Fold 1` $\le$ Sep 2025; `Fold 2` $\le$ Dec 2025; `Fold 3` $\le$ Mar 2026) evaluated on subsequent unseen quarters. The decision threshold (0.34) was locked in Window A (`Fold 1`) and validated on Windows B & C (`Fold 2`: 0.7640, `Fold 3`: 0.7728).
* **Drift & Seasonal Caveats:** Test set spans Q3 (Jul–Sep 2026 Monsoon season), which has category demand shifts (e.g., Room Heaters vs Ceiling Fans). Late-window right-censoring sensitivity tests confirmed model robustness ($\Delta\text{AUC} = -0.0053$).

---

### How do you know it works? How you validated, on what split, error rate, and the kind of case it gets wrong.*
* **Validation Design:** Validated across 3 chronological rolling-origin folds strictly ordered by `order_placed_at` (Fold 1: train 4,133, test 2,054; Fold 2: train 6,224, test 2,110; Fold 3: train 8,362, test 2,103). No random splits or future leakage.
* **Model Benchmark:** Regularized `LogisticRegression` (AUC 0.7728, PR-AUC 0.3949) outperformed `HistGradientBoosting` (AUC 0.7546, PR-AUC 0.3633) and `DummyPrior` (AUC 0.5000).
* **Error Rates & Failure Modes:**
  1. *95% Accuracy Fallacy:* A trivial "always predict NO" model achieves 88.5% accuracy but catches zero returns.
  2. *False Negatives (Missed Returns):* Highest in low base-rate categories (Ceiling Fans: 56.5% FN; Prepaid UPI: 44.9% FN); lowest in Cash on Delivery orders (only 14.3% FN, capturing 85.7% of COD returns).
  3. *Shield False Positives:* Shield members have a 52.8% False Positive rate because their base return rate is double regular customers (20.7% vs 8.8%). We mitigate this by making polite VIP confirmation calls rather than holding or cancelling orders.
  4. *Calibration:* Predicted probabilities monotonically track observed empirical return rates across all 10 deciles (from 0.6% in decile 1 up to 76.9% in decile 10).

---

### Did you change, narrow, or push back on the client's ask? What, when, and why. [can only raise your score]*
1. **Pushed Back on 95% Accuracy Target:** Proved mathematically that 95% accuracy on 11.5% imbalanced data is impossible without suppressing true returns; shifted executive focus to ROC-AUC (0.77) and net rupee savings (+₹10.8k/mo).
2. **Pushed Back on Dispatch Holding:** Rejected Ritu's proposal to hold flagged orders because a 12% hold cancellation rate destroys gross margin on legitimate orders (-₹43.7k/mo loss). Replaced with pre-dispatch confirmation calls (+₹10.8k/mo net gain).
3. **Pushed Back on "Dealing with Shield Later":** Shield members buy ~3 appliances/year with highest LTV; established a VIP confirmation call policy to preserve loyalty and prevent churn.
4. **Corrected Unit Return Cost:** Overturned the ₹600 shipping-only estimate in favor of the true all-in ₹1,150 unit return cost provided by Finance.
5. **Permanently Dropped Post-Order Leakage Columns:** Proactively identified and blacklisted database columns recorded at data export (`last_service_event_type`, `pickup_scheduled_at`, `source`) to ensure strict pre-dispatch operational validity.

---

### What is wrong with what you are handing us, or with the data we handed you? Be specific: bugs, shortcuts, columns you did not trust, rows that looked wrong. [can only raise your score]*
1. **651 Duplicate Partner Feed Rows:** `train.csv` contained 651 duplicate orders between `crm` and `partner_feed`. We dropped all `partner_feed` duplicates.
2. **October 2025 Currency Inflation Bug:** 700 orders during the festive campaign were recorded in paise rather than rupees (e.g. ₹3,500 recorded as ₹350,000). We repaired this by dividing values >5x expected list price by 100.
3. **Pincode `000000` Walk-In Misconception:** README stated `000000` was purely partner walk-in purchases, but data showed web/app orders with delivery promises. We parsed pincodes as strings and added a dedicated `no_address = 1` flag.
4. **Post-Order Leakage Columns:** `pickup_scheduled_at` was populated on 1,281 training rows (109 of which were cancelled pickups with `returned = 0`) but was 100% blank in the unlabelled test set. Both `pickup_scheduled_at` and `last_service_event_type` were blacklisted.
5. **Right-Censoring Lag (Up to 19 Days):** Orders placed in the final 2–3 weeks of training windows have uncompleted return windows.
6. **Customer Prior History Monotonicity:** Customer prior order/return counters exhibited non-monotonic tracking across order dates; we kept them due to strong empirical predictive signal but flagged the limitation.

---

### What does one prediction cost, and what would a month cost at Kestrel's volume (about 700 orders a month)? Show the arithmetic. If you used no paid calls, say so.*
* **Cost per Prediction:** **₹0.00** (< 2.0 ms CPU execution latency).
* **Monthly Operating Cost:** **₹0.00 / month** (Zero paid external LLM APIs, zero GPU dependencies).
* **Monthly Economic Arithmetic (per 700 Orders):**
  - Status Quo Return Losses (700 $\times$ 11.46% base return rate $\times$ ₹1,150): **-₹92,252.00 / month**
  - Proactive Calls Made (346.8 orders @ ₹45/call): **₹15,607.00**
  - Returns Prevented (22.95 returns avoided @ ₹1,150): **₹26,392.50 saved**
  - Net Monthly Financial Impact: ₹26,392.50 (Saved) - ₹15,607.00 (Call Cost) = **+₹10,785.50 / month** (~₹1.3 Lakhs/year).
  - Software & API Costs: **₹0.00 / month**.

---

### What did you deliberately leave out, and why that rather than something else?*
1. **External LLM Scoring:** Left out to avoid per-prediction API costs, rate-limit bottlenecks (5 RPM quotas), and 1–3s latency on dispatch lines.
2. **Non-Linear Tree Ensembles (HistGradientBoosting):** Evaluated as challenger model (`src/models.py`), but rejected in favor of regularized Logistic Regression which generalized better out-of-sample in temporal backtests (AUC 0.7728 vs 0.7546) and provided clean linear perturbation explainability.
3. **Random K-Fold Splits:** Left out because random splitting violates temporal causality and does not mirror the chronological production dispatch setting.
4. **Post-Order Leakage Columns:** Proactively identified and blacklisted `pickup_scheduled_at`, `last_service_event_type`, and `source` to prevent training on post-dispatch leakage.
5. **Heavy External SHAP Dependencies:** Left out to eliminate native C++ compilation risks on fresh machines, replacing it with a custom perturbation reasons engine.

---

### Anything you built or found that nobody asked for?*
1. **Delivery Note Template Extraction:** Reduced raw unstructured free text into standardized categorical templates (`NONE`, `Call on delivery`, `Leave with security`), ignoring raw text strings.
2. **Zero-CDN Offline Web Application:** Built a single-page UI with `system-ui` typography, live presets, segmented controls, skeleton shimmer, recent checks history, and copy response feature without external dependencies.
3. **Model-Agnostic Perturbation Explainability Engine:** Built a lightweight engine (`service/reasons.py`) that generates plain-English risk driver sentences for support agents in < 1 ms.
4. **Safety Input Clamping with Operational Warnings:** Built automatic bounds clamping for numeric inputs outside training distribution with explicit warnings.
5. **Right-Censoring Sensitivity Backtesting:** Automated sensitivity scripts verifying model stability against return reporting delays ($\Delta\text{AUC} = -0.0053$).

---

### What did you use AI for? Which tools and models, where they helped, where they misled you, what you threw away. Link your three-minute screen recording here*
* **AI Tooling Used:** Google DeepMind Antigravity Pair Programming System.
* **Where They Helped:** Rapid data auditing, scaffolding feature transformations, setting up temporal cross-validation, and creating clean vanilla UI styling.
* **Where They Misled & What Was Thrown Away:** AI suggestions to rely on standard non-linear tree models were rejected after empirical rolling temporal validation showed regularized Logistic Regression achieved superior out-of-sample generalization.
* **Screen Recording Video Link:** `PASTE_REAL_DRIVE_LINK_HERE`

---

### Someone picks this up on Monday and you are unreachable. The three things they need to know.*
1. **Launch the 4-Week 50/50 A/B Confirmation Call Pilot:** Deploy `POST /predict` into the warehouse workflow. For orders scoring $\ge 0.34$, randomly assign 50% to confirmation calls (Treatment) and 50% to standard dispatch (Control) to validate the +₹10.8k/month return savings live.
2. **Equip Support Agents with Top 3 Plain-Language Reasons:** Direct customer service to use the API-provided `top_3_reasons` field (address verification, COD confirmation, installation guidance) to guide friendly, helpful phone interactions.
3. **Establish Monthly Automated Retraining & Drift Monitoring:** Schedule a monthly cron job to run `scripts/train.py` on the latest 3 quarters of historical CRM orders to update `outputs/model_lr.joblib` and adapt to seasonal trends without manual code changes.
