"""
scripts/build_catalog.py — Build service/catalog.json from source data + model.

Extracts:
  - 21 product rows (sku, family, list_price_inr, warranty_months, launch_date)
  - Valid state codes from the fitted model's OneHotEncoder categories
  - Valid sales_channel, payment_mode, is_gift, shield_member, pincode_prefix,
    delivery_note_template categories

Sensitivity: products.csv is public catalog info (K16).
             customers.csv is NOT shipped.
"""

import json
import pathlib
import sys

import joblib
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.features import FEATURE_COLS
from src.cleaning import INSTALLABLE_FAMILIES

MODEL_PATH = ROOT / "outputs" / "model_lr.joblib"
PRODUCTS_PATH = ROOT / "data" / "products.csv"
OUTPUT_PATH = ROOT / "service" / "catalog.json"

# Categorical feature names in the same order as FEATURE_COLS
CAT_FEATURES = [c for c in FEATURE_COLS if c in [
    "sales_channel", "payment_mode", "is_gift", "family", "sku",
    "shield_member", "state", "pincode_prefix", "delivery_note_template",
]]


def main():
    # --- Products ---
    products = pd.read_csv(PRODUCTS_PATH)
    product_rows = []
    for _, row in products.iterrows():
        product_rows.append({
            "sku": row["sku"],
            "family": row["family"],
            "list_price_inr": float(row["list_price_inr"]),
            "warranty_months": int(row["warranty_months"]),
            "launch_date": str(row["launch_date"]),
        })

    # --- Model categories ---
    model = joblib.load(MODEL_PATH)
    preprocessor = model.named_steps["preprocessor"]
    cat_encoder = preprocessor.named_transformers_["cat"]
    cat_categories = cat_encoder.categories_

    # Map category arrays to feature names
    categories = {}
    for i, feat_name in enumerate(CAT_FEATURES):
        categories[feat_name] = sorted(cat_categories[i].tolist())

    # Extract states specifically
    states = categories.get("state", [])

    # Installable families
    installable = sorted(list(INSTALLABLE_FAMILIES))

    # --- Training ranges for numeric input clamping (Section A.1) ---
    ranges = {
        "discount_pct": [0.0, 60.0],
        "qty": [1, 2],
        "promised_delivery_days": [1, 12],
        "customer_prior_orders": [0, 10],
        "customer_prior_returns": [0, 6],
        "order_value_inr": [1000.0, 60000.0],
    }
    train_path = ROOT / "data" / "train.csv"
    if train_path.exists():
        from src.cleaning import clean_train
        train_raw = pd.read_csv(train_path)
        ctrain = clean_train(train_raw, products)
        ranges["discount_pct"] = [float(ctrain["discount_pct"].min()), float(ctrain["discount_pct"].max())]
        ranges["qty"] = [int(ctrain["qty"].min()), int(ctrain["qty"].max())]
        ranges["promised_delivery_days"] = [int(ctrain["promised_delivery_days"].min()), int(ctrain["promised_delivery_days"].max())]
        ranges["customer_prior_orders"] = [int(ctrain["customer_prior_orders"].min()), int(ctrain["customer_prior_orders"].max())]
        ranges["customer_prior_returns"] = [int(ctrain["customer_prior_returns"].min()), int(ctrain["customer_prior_returns"].max())]
        ranges["order_value_inr"] = [1000.0, 60000.0]

    catalog = {
        "products": product_rows,
        "states": states,
        "categories": categories,
        "installable_families": installable,
        "ranges": ranges,
    }

    OUTPUT_PATH.write_text(json.dumps(catalog, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[build_catalog] Wrote {len(product_rows)} products, {len(states)} states, ranges to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
