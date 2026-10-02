# Expected Score Lock-in

_Locked in before final prediction generation as the prior expected performance target._

## Metric
- **Primary Metric:** ROC-AUC (Area Under the Receiver Operating Characteristic Curve)
- **Secondary Metric:** PR-AUC (Average Precision / Area Under the Precision-Recall Curve)
- **Context:** The task submission requests a probabilistic ranking score `score` in `[0, 1]`. While the exact evaluation metric on the hidden test set is not explicitly stated in problem instructions, ranking discrimination (ROC-AUC) and positive-class precision (PR-AUC) are the standard evaluation criteria for severe class-imbalance return prediction (~11% return rate).

## Point Estimate and Range from Temporal Backtests
Based on out-of-fold temporal cross-validation across 3 rolling-origin folds (trained on historical quarters, evaluated on future quarters):

- **Expected ROC-AUC (Point Estimate):** `0.77`
- **Expected ROC-AUC (95% CI / Range):** `0.74 - 0.80`
  - Fold 1 (Oct-Dec 2025): 0.7619 [0.728, 0.792]
  - Fold 2 (Jan-Mar 2026): 0.7640 [0.730, 0.796]
  - Fold 3 (Apr-Jun 2026): 0.7728 [0.739, 0.803]
- **Expected PR-AUC:** `0.34 - 0.45` (Baseline prior base rate: ~0.11)

## Drift & Generalization Caveats
1. **Seasonal Shift:** Test set spans Q3 (Jul–Sep 2026), Monsoon/pre-festive season in India, whereas training data covers preceding quarters. Product demand patterns and return rates (e.g., Room Heaters vs Ceiling Fans vs Water Purifiers) fluctuate seasonally.
2. **Customer Base Evolution:** As customer tenure grows and repeat customer proportions increase, `customer_prior_*` features will have broader coverage.
3. **Right-Censoring Lag:** Orders placed in the final weeks of the test window may exhibit right-censoring lag if evaluated before full 14-day return window completion, though my model is robust to dropping late-window orders (tested sensitivity $\Delta\text{AUC} = -0.0053$).
4. **Policy Independence:** Scores reflect pre-dispatch return risk before operational intervention (call confirmation).

_Timestamp: 2026-10-01 18:57:00 IST. Do not modify after final test predictions are generated._
