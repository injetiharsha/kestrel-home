"""
src/features.py — Feature engineering pipeline.

Order-time features:
  sales_channel, payment_mode, discount_pct, qty, order_value_fixed,
  promised_delivery_days, no_address, pincode_prefix (first 3 digits when not 000000),
  is_gift, customer_prior_orders, customer_prior_returns, prior_return_rate,
  family, sku, warranty_months, list_price_inr,
  product_age_days (order date - launch_date),
  shield_member, installable, state, hour, weekday,
  delivery_note_template (optional, for ablation).

Blacklist (never used, enforced by test):
  returned, last_service_event_type, pickup_scheduled_at, source,
  order_id, customer_id, signup_date, order month/year, raw delivery_note.
"""

import pandas as pd
import numpy as np
import pathlib

from src.cleaning import INSTALLABLE_FAMILIES

DATA = pathlib.Path(__file__).resolve().parent.parent / "data"

# Columns that must NEVER appear in the feature matrix
BLACKLIST = {
    "returned",
    "last_service_event_type",
    "pickup_scheduled_at",
    "source",
    "order_id",
    "customer_id",
    "signup_date",
    "delivery_note",       # raw text
    "order_month",
    "order_year",
    "order_month_year",
    "tenure",
    "tenure_days",
    "customer_tenure",
}

# The final feature columns (order matches model training)
FEATURE_COLS = [
    # Numeric
    "discount_pct",
    "qty",
    "order_value_fixed",
    "promised_delivery_days",
    "no_address",
    "customer_prior_orders",
    "customer_prior_returns",
    "prior_return_rate",
    "list_price_inr",
    "warranty_months",
    "product_age_days",
    "installable",
    "hour",
    "weekday",
    # Categorical (will be encoded)
    "sales_channel",
    "payment_mode",
    "is_gift",
    "family",
    "sku",
    "shield_member",
    "state",
    "pincode_prefix",
    "delivery_note_template",
]


def build_features(
    df: pd.DataFrame,
    products: pd.DataFrame,
    customers: pd.DataFrame,
) -> pd.DataFrame:
    """Build feature matrix from a cleaned dataframe.

    Returns a dataframe with FEATURE_COLS as columns plus 'order_placed_at'
    (kept for time-based splitting, dropped before model fitting).
    If 'returned' exists in df, it is carried through as the target.
    """
    out = pd.DataFrame(index=df.index)

    # ---- Passthrough numeric features ----
    out["discount_pct"] = df["discount_pct"].values
    out["qty"] = df["qty"].values
    out["order_value_fixed"] = df["order_value_inr"].values  # already corrected in cleaning
    out["promised_delivery_days"] = df["promised_delivery_days"].values
    out["no_address"] = df["no_address"].values
    out["customer_prior_orders"] = df["customer_prior_orders"].values
    out["customer_prior_returns"] = df["customer_prior_returns"].values

    # ---- Derived numeric features ----
    # prior_return_rate: customer_prior_returns / customer_prior_orders (0 if no prior orders)
    out["prior_return_rate"] = np.where(
        out["customer_prior_orders"] > 0,
        out["customer_prior_returns"] / out["customer_prior_orders"],
        0.0,
    )

    # ---- Product features (join with products.csv) ----
    prod_cols = products[["sku", "family", "list_price_inr", "warranty_months", "launch_date"]].copy()
    prod_cols["launch_date"] = pd.to_datetime(prod_cols["launch_date"])
    df_with_prod = df[["sku", "order_placed_at"]].merge(prod_cols, on="sku", how="left")

    out["list_price_inr"] = df_with_prod["list_price_inr"].values
    out["warranty_months"] = df_with_prod["warranty_months"].values
    out["family"] = df_with_prod["family"].values
    out["sku"] = df["sku"].values

    # product_age_days: order date - launch_date
    out["product_age_days"] = (
        df_with_prod["order_placed_at"] - df_with_prod["launch_date"]
    ).dt.days.values

    # installable flag: family in (Ceiling Fan, Robot Vacuum, Water Purifier)
    out["installable"] = out["family"].isin(INSTALLABLE_FAMILIES).astype(int)

    # ---- Customer features (join with customers.csv) ----
    cust_cols = customers[["customer_id", "shield_member", "state"]].copy()
    df_with_cust = df[["customer_id"]].merge(cust_cols, on="customer_id", how="left")

    out["shield_member"] = df_with_cust["shield_member"].values
    out["state"] = df_with_cust["state"].values

    # ---- Order features ----
    out["sales_channel"] = df["sales_channel"].values
    out["payment_mode"] = df["payment_mode"].values
    out["is_gift"] = df["is_gift"].values

    # Pincode prefix (first 3 digits, "000" for no_address)
    out["pincode_prefix"] = df["delivery_pincode"].str[:3].values

    # Hour and weekday from order_placed_at (ablation candidates)
    out["hour"] = df["order_placed_at"].dt.hour.values
    out["weekday"] = df["order_placed_at"].dt.weekday.values

    # Delivery note template (optional, for ablation)
    out["delivery_note_template"] = df["delivery_note_template"].values

    # ---- Keep order_placed_at for time-based splitting (not a feature) ----
    out["order_placed_at"] = df["order_placed_at"].values

    # ---- Carry through target if present ----
    if "returned" in df.columns:
        out["returned"] = df["returned"].values

    # ---- Carry through order_id for predictions (not a feature) ----
    out["_order_id"] = df["order_id"].values

    return out


def get_feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Extract only the feature columns (no target, no IDs, no dates).

    This is what goes into model.fit() / model.predict().
    """
    return df[FEATURE_COLS].copy()


def verify_no_blacklist(df: pd.DataFrame) -> list[str]:
    """Check that no blacklisted column appears in the feature matrix.

    Returns a list of violations (empty = pass).
    """
    violations = []
    feature_cols = set(df.columns)
    for col in BLACKLIST:
        if col in feature_cols:
            violations.append(col)
    return violations
