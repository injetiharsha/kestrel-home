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

    catalog = {
        "products": product_rows,
        "states": states,
        "categories": categories,
        "installable_families": installable,
    }

    OUTPUT_PATH.write_text(json.dumps(catalog, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[build_catalog] Wrote {len(product_rows)} products, {len(states)} states to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
