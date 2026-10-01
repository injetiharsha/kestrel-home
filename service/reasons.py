"""
service/reasons.py — Model-agnostic perturbation reasons engine.

PLAN.md Section 7:
Replaces each feature with typical baseline values, measures score reduction,
and maps the top contributors to human-readable plain text sentences.
"""

from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np

# Safe / low-risk baseline values for perturbation
BASELINES = {
    "payment_mode": "prepaid_upi",
    "prior_return_rate": 0.0,
    "customer_prior_returns": 0,
    "customer_prior_orders": 2,
    "discount_pct": 5.0,
    "promised_delivery_days": 2,
    "no_address": 0,
    "is_gift": "N",
    "sales_channel": "web",
    "shield_member": "N",
    "delivery_note_template": "NONE",
    "family": "Mixer Grinder",
    "qty": 1,
}

REASON_TEMPLATES = {
    "prior_return_rate": "Customer has a history of high returns ({val:.0%} return rate on prior orders).",
    "payment_mode": "Cash on Delivery (COD) payment mode carries higher rejection and return risk.",
    "shield_member": "Shield membership accounts show significantly higher warranty and return claim frequency.",
    "family": "Product category '{val}' experiences elevated return rates due to setup and handling complexity.",
    "discount_pct": "High promotional discount ({val:.0f}%) is associated with speculative buying.",
    "promised_delivery_days": "Extended delivery timeline ({val} days) increases cancellation and buyer remorse risk.",
    "no_address": "Delivery pincode 000000 indicates an incomplete or unverified delivery address.",
    "sales_channel": "Orders via '{val}' channel experience higher return friction than direct web orders.",
    "qty": "High order quantity ({val} units) increases bulk return probability.",
    "delivery_note_template": "Special delivery constraints noted in delivery instructions.",
    "is_gift": "Gift orders have higher mismatch probability upon recipient delivery.",
}


def compute_top_reasons(
    model,
    feature_row: pd.DataFrame,
    base_prob: float,
    top_k: int = 3,
) -> List[str]:
    """Identify top risk-increasing features via perturbation."""
    deltas: List[Tuple[str, float, Any]] = []

    for col, baseline_val in BASELINES.items():
        if col not in feature_row.columns:
            continue
        current_val = feature_row[col].iloc[0]

        # If current value already equal to baseline, no risk increase from this factor
        if current_val == baseline_val:
            continue

        # Perturb single feature to baseline
        perturbed_df = feature_row.copy()
        perturbed_df[col] = baseline_val

        # If prior_return_rate is perturbed, align customer_prior_returns too
        if col == "prior_return_rate":
            perturbed_df["customer_prior_returns"] = 0

        # Predict with perturbed row
        perturbed_prob = float(model.predict_proba(perturbed_df)[:, 1][0])
        score_drop = base_prob - perturbed_prob

        if score_drop > 0.005:  # meaningful positive risk contribution
            deltas.append((col, score_drop, current_val))

    # Sort by largest risk contribution (score drop when normalized to baseline)
    deltas.sort(key=lambda x: x[1], reverse=True)

    reasons: List[str] = []
    for col, drop, val in deltas[:top_k]:
        if col == "prior_return_rate":
            reasons.append(REASON_TEMPLATES[col].format(val=val))
        elif col == "discount_pct":
            reasons.append(REASON_TEMPLATES[col].format(val=val))
        elif col == "family":
            reasons.append(REASON_TEMPLATES[col].format(val=val))
        elif col == "promised_delivery_days":
            reasons.append(REASON_TEMPLATES[col].format(val=val))
        elif col == "sales_channel":
            reasons.append(REASON_TEMPLATES[col].format(val=val))
        elif col == "qty":
            reasons.append(REASON_TEMPLATES[col].format(val=val))
        elif col in REASON_TEMPLATES:
            reasons.append(REASON_TEMPLATES[col])

    # Fallbacks if fewer than top_k reasons found
    if not reasons:
        if base_prob >= 0.34:
            reasons.append("Overall feature profile exceeds risk threshold for pre-dispatch intervention.")
            reasons.append("Order parameters match patterns with elevated historical return rates.")
            reasons.append("Customer or delivery attributes suggest pre-dispatch verification.")
        else:
            reasons.append("Low risk: Customer order history shows stable delivery completion.")
            reasons.append("Standard product category with low return rates.")
            reasons.append("Prepaid transaction with standard delivery timeline.")

    while len(reasons) < top_k:
        if base_prob >= 0.34:
            reasons.append("Secondary order risk factors align with historical return cases.")
        else:
            reasons.append("Standard order profile with no significant risk flags.")

    return reasons[:top_k]
