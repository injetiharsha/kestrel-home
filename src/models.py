"""
src/models.py — Model definitions and encoding pipeline.

Models:
  - DummyClassifier (prior baseline)
  - LogisticRegression (primary, regularised)
  - HistGradientBoostingClassifier (challenger)
"""

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

from src.features import FEATURE_COLS

# Split features by type
NUMERIC_FEATURES = [
    "discount_pct", "qty", "order_value_fixed", "promised_delivery_days",
    "no_address", "customer_prior_orders", "customer_prior_returns",
    "prior_return_rate", "list_price_inr", "warranty_months",
    "product_age_days", "installable", "hour", "weekday",
]

CATEGORICAL_FEATURES = [
    "sales_channel", "payment_mode", "is_gift", "family", "sku",
    "shield_member", "state", "pincode_prefix", "delivery_note_template",
]


def _make_preprocessor():
    """Build column transformer for encoding."""
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERIC_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="infrequent_if_exist",
                                  sparse_output=False, min_frequency=5),
             CATEGORICAL_FEATURES),
        ],
        remainder="drop",
    )


def make_dummy_pipeline():
    """DummyClassifier — always predicts the prior probability."""
    return Pipeline([
        ("preprocessor", _make_preprocessor()),
        ("classifier", DummyClassifier(strategy="prior")),
    ])


def make_lr_pipeline(C=1.0, max_iter=1000):
    """LogisticRegression — primary model, regularised."""
    return Pipeline([
        ("preprocessor", _make_preprocessor()),
        ("classifier", LogisticRegression(
            C=C, max_iter=max_iter, solver="lbfgs",
            class_weight="balanced", random_state=42,
        )),
    ])


def make_hgb_pipeline(max_iter=200, max_depth=4, learning_rate=0.1):
    """HistGradientBoostingClassifier — challenger model."""
    # HGB handles categoricals and missing values natively,
    # but I keep the same preprocessor for consistency
    return Pipeline([
        ("preprocessor", _make_preprocessor()),
        ("classifier", HistGradientBoostingClassifier(
            max_iter=max_iter, max_depth=max_depth,
            learning_rate=learning_rate, random_state=42,
        )),
    ])


def get_all_models():
    """Return dict of model_name -> pipeline."""
    return {
        "DummyPrior": make_dummy_pipeline(),
        "LogisticRegression": make_lr_pipeline(),
        "HistGBT": make_hgb_pipeline(),
    }
