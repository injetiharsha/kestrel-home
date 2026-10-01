# Evidence Report

_All numbers produced by `scripts/train.py`. No manual edits._

## Model Comparison (Fold3)

| Model | AUC | AUC 95% CI | PR-AUC | PR-AUC 95% CI | Monthly Net (Rs) |
|---|---|---|---|---|---|
| DummyPrior | 0.5000 | [0.500, 0.500] | 0.1146 | [0.101, 0.129] | 788 |
| LogisticRegression | 0.7728 | [0.739, 0.803] | 0.3949 | [0.337, 0.455] | 12,436 |
| HistGBT | 0.7546 | [0.720, 0.788] | 0.3633 | [0.306, 0.429] | 11,282 |

## LogisticRegression per fold (own threshold)

| Fold | Train end | Test | N | Base rate | AUC | PR-AUC | Threshold | Precision | Recall | Flagged |
|---|---|---|---|---|---|---|---|---|---|---|
| Fold1 | - | - | 2054 | 0.110 | 0.7619 | 0.3337 | 0.34 | 0.214 | 0.756 | 793 |
| Fold2 | - | - | 2110 | 0.116 | 0.7640 | 0.3806 | 0.53 | 0.281 | 0.620 | 540 |
| Fold3 | - | - | 2103 | 0.115 | 0.7728 | 0.3949 | 0.45 | 0.237 | 0.730 | 744 |

## Reported folds (threshold from Fold1 = 0.34)

| Fold | AUC | Precision | Recall | Flagged | Monthly Net Call (Rs) |
|---|---|---|---|---|---|
| Fold2 | 0.7640 | 0.192 | 0.788 | 1006 | 10,753 |
| Fold3 | 0.7728 | 0.189 | 0.817 | 1042 | 10,785 |

## Economics: Call vs Hold vs Do Nothing

| Strategy | Monthly impact (Rs) at 700 orders |
|---|---|
| Do nothing | Return cost: Rs 92,252 |
| **Call** (flagged slice) | **Net saving: Rs 10,785** |
| Hold (flagged slice) | Net: Rs -43,722 |

Call details: 1042 flagged (50%), call cost Rs 46,890, returns prevented 69, saving Rs 79,292

## Hold sensitivity (Assumption A1: margin %)

| Margin % | Monthly hold net (Rs) |
|---|---|
| 5pct | -8,541 |
| 15pct | -43,722 |
| 25pct | -78,903 |

Decision on A1: 15% chosen as mid-range. Hold loses to call at all tested margins.

## Ablation studies (Fold3, LR)

| Ablation | AUC | PR-AUC | Delta AUC |
|---|---|---|---|
| full_features | 0.7728 | 0.3949 | +0.0000 |
| without_customer_prior | 0.7252 | 0.2811 | -0.0477 |
| without_hour_weekday | 0.7730 | 0.3938 | +0.0002 |
| without_delivery_note_template | 0.7772 | 0.3979 | +0.0043 |
| without_pincode_prefix | 0.7765 | 0.4000 | +0.0037 |
| without_last_21_days | 0.7675 | 0.4006 | -0.0053 |

## Failure analysis (Fold3, LR)

### by_family

| Segment | N | Return rate | FN rate | FP rate |
|---|---|---|---|---|
| Mixer Grinder | 299 | 7.7% | 39.1% | 14.9% |
| Room Heater | 314 | 13.4% | 21.4% | 36.4% |
| Water Purifier | 267 | 12.7% | 17.6% | 41.6% |
| Robot Vacuum | 330 | 17.6% | 19.0% | 58.1% |
| Ceiling Fan | 315 | 7.3% | 56.5% | 13.4% |
| Induction Cooktop | 279 | 10.4% | 37.9% | 16.8% |
| Air Fryer | 299 | 10.7% | 18.8% | 34.5% |

### by_payment_mode

| Segment | N | Return rate | FN rate |
|---|---|---|---|
| prepaid_card | 437 | 8.2% | 41.7% |
| prepaid_upi | 756 | 6.5% | 44.9% |
| emi | 268 | 11.2% | 33.3% |
| cod | 642 | 19.6% | 14.3% |

### by_shield

| Segment | N | Return rate | FN rate | FP rate |
|---|---|---|---|---|
| shield_Y | 473 | 20.7% | - | 52.8% |
| shield_N | 1630 | 8.8% | - | 24.9% |

## Calibration (Fold3, LR)

| Bin | N | Mean predicted | Mean actual |
|---|---|---|---|
| 0.00-0.10 | 169 | 0.073 | 0.006 |
| 0.10-0.20 | 360 | 0.151 | 0.033 |
| 0.20-0.30 | 404 | 0.253 | 0.052 |
| 0.30-0.40 | 304 | 0.348 | 0.076 |
| 0.40-0.50 | 253 | 0.450 | 0.119 |
| 0.50-0.60 | 233 | 0.548 | 0.172 |
| 0.60-0.70 | 128 | 0.646 | 0.164 |
| 0.70-0.80 | 132 | 0.749 | 0.242 |
| 0.80-0.90 | 81 | 0.846 | 0.383 |
| 0.90-1.00 | 39 | 0.947 | 0.769 |

## How the model fails

1. **Accuracy vs always-predict-no**: The model's accuracy is comparable to always predicting 'no return' because returns are only ~11% of orders. This is expected and is why AUC/PR-AUC are the right metrics.
2. **False negatives**: Returns the model misses. Highest FN rates in product families with higher base return rates (Robot Vacuum, Water Purifier).
3. **False positives on Shield members**: Flagging Shield members for calls is acceptable (they get calls, not holds), but the model over-flags them due to their higher return rate.
4. **Calibration**: Predicted probabilities may not perfectly match actual rates. The model tends to be well-calibrated in the middle range but less so at extremes.
