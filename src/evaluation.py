"""
src/evaluation.py — Evaluation: rolling folds, metrics, bootstrap, economics.

Validation design:
  - Rolling time folds, threshold on A, report on B.
  - Fold 1: train to 2025-09-30, test Oct-Dec 2025
  - Fold 2: train to 2025-12-31, test Jan-Mar 2026
  - Fold 3: train to 2026-03-31, test Apr-Jun 2026

Economics:
  - Call cost = Rs 45
  - Return cost = Rs 1,150
  - Call prevention rate = 35%
  - Hold cancel rate = 12%
  - Margin A1 = 15% of order value (sensitivity 5%-25%)
"""

import numpy as np
import pandas as pd
from sklearn.metrics import (
    roc_auc_score, average_precision_score, accuracy_score,
    precision_score, recall_score, confusion_matrix,
)

from src.features import FEATURE_COLS

# Economics constants
CALL_COST = 45          # Rs per call
RETURN_COST = 1150      # Rs all-in return cost
CALL_PREVENTION = 0.35  # 35% of returns prevented by call
HOLD_CANCEL_RATE = 0.12 # 12% of held orders cancel
MONTHLY_ORDERS = 700    # orders per month
MARGIN_PCT_A1 = 0.15    # Assumption A1: margin = 15% of order value

# Rolling fold definitions
FOLDS = [
    {
        "name": "Fold1",
        "train_end": "2025-09-30",
        "test_start": "2025-10-01",
        "test_end": "2025-12-31",
    },
    {
        "name": "Fold2",
        "train_end": "2025-12-31",
        "test_start": "2026-01-01",
        "test_end": "2026-03-31",
    },
    {
        "name": "Fold3",
        "train_end": "2026-03-31",
        "test_start": "2026-04-01",
        "test_end": "2026-06-30",
    },
]


def get_rolling_folds(df: pd.DataFrame) -> list[dict]:
    """Split data into rolling time folds.

    Returns list of dicts with train_idx, test_idx, fold_name.
    """
    folds = []
    dates = pd.to_datetime(df["order_placed_at"])
    for fold_def in FOLDS:
        train_mask = dates <= pd.Timestamp(fold_def["train_end"])
        test_mask = (dates >= pd.Timestamp(fold_def["test_start"])) & \
                    (dates <= pd.Timestamp(fold_def["test_end"]))
        if train_mask.sum() > 0 and test_mask.sum() > 0:
            folds.append({
                "name": fold_def["name"],
                "train_idx": df.index[train_mask],
                "test_idx": df.index[test_mask],
                "train_end": fold_def["train_end"],
                "test_start": fold_def["test_start"],
                "test_end": fold_def["test_end"],
            })
    return folds


def compute_metrics(y_true: np.ndarray, y_prob: np.ndarray, threshold: float = 0.5) -> dict:
    """Compute classification metrics."""
    y_pred = (y_prob >= threshold).astype(int)
    base_rate = y_true.mean()
    always_no_acc = 1 - base_rate

    metrics = {
        "n": len(y_true),
        "base_rate": float(base_rate),
        "auc": float(roc_auc_score(y_true, y_prob)) if len(np.unique(y_true)) > 1 else 0.5,
        "pr_auc": float(average_precision_score(y_true, y_prob)) if len(np.unique(y_true)) > 1 else float(base_rate),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "always_no_accuracy": float(always_no_acc),
        "threshold": float(threshold),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "n_flagged": int(y_pred.sum()),
        "n_returns": int(y_true.sum()),
    }
    return metrics


def bootstrap_ci(y_true: np.ndarray, y_prob: np.ndarray,
                 metric_fn, n_boot: int = 1000, ci: float = 0.95,
                 seed: int = 42) -> tuple[float, float, float]:
    """Bootstrap confidence interval for a metric.

    Returns (point_estimate, lower, upper).
    """
    rng = np.random.RandomState(seed)
    point = metric_fn(y_true, y_prob)
    scores = []
    n = len(y_true)
    for _ in range(n_boot):
        idx = rng.randint(0, n, size=n)
        yt = y_true[idx]
        yp = y_prob[idx]
        if len(np.unique(yt)) < 2:
            continue
        scores.append(metric_fn(yt, yp))
    alpha = (1 - ci) / 2
    lower = np.percentile(scores, alpha * 100)
    upper = np.percentile(scores, (1 - alpha) * 100)
    return float(point), float(lower), float(upper)


def find_threshold_on_fold(y_true: np.ndarray, y_prob: np.ndarray,
                           order_values: np.ndarray = None) -> float:
    """Find optimal threshold on window A by maximizing net rupee benefit.

    Net per flagged order = y * 0.35 * 1150 - 45
    """
    best_threshold = 0.5
    best_net = -np.inf

    for t in np.arange(0.05, 0.95, 0.01):
        flagged = y_prob >= t
        if flagged.sum() == 0:
            continue
        # Net = sum over flagged of (y_true * 0.35 * 1150 - 45)
        net = (y_true[flagged] * CALL_PREVENTION * RETURN_COST - CALL_COST).sum()
        if net > best_net:
            best_net = net
            best_threshold = t

    return float(round(best_threshold, 2))


def compute_economics_call(y_true: np.ndarray, y_prob: np.ndarray,
                           threshold: float, scale_to_monthly: int = MONTHLY_ORDERS) -> dict:
    """Compute call strategy economics.

    Per flagged order: cost = Rs 45, benefit = y * 0.35 * 1150
    Scale to monthly volume.
    """
    flagged = y_prob >= threshold
    n_flagged = int(flagged.sum())
    n_total = len(y_true)

    if n_flagged == 0:
        return {
            "strategy": "call",
            "threshold": threshold,
            "n_flagged": 0,
            "pct_flagged": 0.0,
            "net_per_window": 0.0,
            "net_per_flagged_order": 0.0,
            "monthly_net_700": 0.0,
            "returns_prevented": 0.0,
            "call_cost_total": 0.0,
        }

    returns_in_flagged = y_true[flagged].sum()
    returns_prevented = returns_in_flagged * CALL_PREVENTION
    saving = returns_prevented * RETURN_COST
    cost = n_flagged * CALL_COST
    net = saving - cost

    # Scale to 700 orders/month
    scale = scale_to_monthly / n_total if n_total > 0 else 1
    monthly_net = net * scale

    return {
        "strategy": "call",
        "threshold": float(threshold),
        "n_flagged": n_flagged,
        "pct_flagged": float(n_flagged / n_total * 100),
        "net_per_window": float(net),
        "net_per_flagged_order": float(net / n_flagged) if n_flagged else 0.0,
        "monthly_net_700": float(monthly_net),
        "returns_prevented": float(returns_prevented),
        "call_cost_total": float(cost),
        "saving_total": float(saving),
    }


def compute_economics_hold(y_true: np.ndarray, y_prob: np.ndarray,
                           order_values: np.ndarray, threshold: float,
                           margin_pct: float = MARGIN_PCT_A1,
                           scale_to_monthly: int = MONTHLY_ORDERS) -> dict:
    """Compute hold strategy economics.

    Hold: saving = 12% cancel * y_true * Rs 1150
          cost = 12% * (1-y_true) * margin_pct * order_value (margin lost on good orders that cancel)
    """
    flagged = y_prob >= threshold
    n_flagged = int(flagged.sum())
    n_total = len(y_true)

    if n_flagged == 0:
        return {
            "strategy": "hold",
            "threshold": threshold,
            "margin_pct": margin_pct,
            "n_flagged": 0,
            "pct_flagged": 0.0,
            "net_per_window": 0.0,
            "monthly_net_700": 0.0,
            "saving_total": 0.0,
            "margin_lost_total": 0.0,
        }

    yt = y_true[flagged]
    ov = order_values[flagged]

    # Saving: held returns that cancel (prevented return)
    saving = HOLD_CANCEL_RATE * yt.sum() * RETURN_COST

    # Cost: good orders that cancel, margin lost
    good_orders = (1 - yt)
    margin_lost = HOLD_CANCEL_RATE * (good_orders * margin_pct * ov).sum()

    net = saving - margin_lost
    scale = scale_to_monthly / n_total if n_total > 0 else 1
    monthly_net = net * scale

    return {
        "strategy": "hold",
        "threshold": float(threshold),
        "margin_pct": float(margin_pct),
        "n_flagged": n_flagged,
        "pct_flagged": float(n_flagged / n_total * 100),
        "net_per_window": float(net),
        "monthly_net_700": float(monthly_net),
        "saving_total": float(saving),
        "margin_lost_total": float(margin_lost),
    }


def compute_economics_nothing(y_true: np.ndarray,
                              scale_to_monthly: int = MONTHLY_ORDERS) -> dict:
    """Do nothing: all returns happen, cost = n_returns * RETURN_COST."""
    n_total = len(y_true)
    n_returns = int(y_true.sum())
    total_loss = n_returns * RETURN_COST
    scale = scale_to_monthly / n_total if n_total > 0 else 1

    return {
        "strategy": "do_nothing",
        "n_returns": n_returns,
        "total_return_cost": float(total_loss),
        "monthly_return_cost_700": float(total_loss * scale),
    }


def calibration_table(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> list[dict]:
    """Produce a calibration table: predicted vs actual return rate by decile."""
    bins = np.linspace(0, 1, n_bins + 1)
    table = []
    for i in range(n_bins):
        mask = (y_prob >= bins[i]) & (y_prob < bins[i + 1])
        if i == n_bins - 1:
            mask = (y_prob >= bins[i]) & (y_prob <= bins[i + 1])
        n = int(mask.sum())
        if n == 0:
            continue
        table.append({
            "bin": f"{bins[i]:.2f}-{bins[i+1]:.2f}",
            "n": n,
            "mean_predicted": float(y_prob[mask].mean()),
            "mean_actual": float(y_true[mask].mean()),
        })
    return table
