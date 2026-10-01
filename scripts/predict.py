#!/usr/bin/env python3
"""
scripts/predict.py — Final model training on all deduped training data and test inference.

PLAN.md Section 10 & Phase P4.
"""

import pathlib
import sys
import pandas as pd
import numpy as np
import joblib

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.cleaning import clean_train, clean_test, load_products, load_customers
from src.features import build_features, FEATURE_COLS
from src.models import make_lr_pipeline


def main():
    print("Loading data...")
    products = load_products()
    customers = load_customers()
    train_raw = pd.read_csv(ROOT / "data" / "train.csv")
    test_path = ROOT / "data" / "test_unlabelled.csv" if (ROOT / "data" / "test_unlabelled.csv").exists() else ROOT / "data" / "test.csv"
    test_raw = pd.read_csv(test_path)
    sample_sub = pd.read_csv(ROOT / "data" / "sample_submission.csv")

    print(f"Raw train: {len(train_raw)} rows | Raw test: {len(test_raw)} rows")

    # Clean data
    train_clean = clean_train(train_raw, products)
    test_clean = clean_test(test_raw, products)
    print(f"Clean train: {len(train_clean)} rows | Clean test: {len(test_clean)} rows")

    # Build features
    train_feat = build_features(train_clean, products, customers)
    test_feat = build_features(test_clean, products, customers)

    X_train = train_feat[FEATURE_COLS]
    y_train = train_feat["returned"].values
    X_test = test_feat[FEATURE_COLS]

    print(f"Feature matrix: {X_train.shape[1]} features")

    # Final fit on ALL deduped training data (no hyperparameter tuning)
    print("Fitting final LogisticRegression pipeline on all deduped training data...")
    final_model = make_lr_pipeline(C=1.0, max_iter=1000)
    final_model.fit(X_train, y_train)

    # Save model artifact
    model_path = ROOT / "outputs" / "model_lr.joblib"
    joblib.dump(final_model, model_path)
    print(f"Saved final model artifact: {model_path}")

    # Predict test probabilities
    test_scores = final_model.predict_proba(X_test)[:, 1]

    # Create predictions DataFrame
    preds_df = pd.DataFrame({
        "order_id": test_clean["order_id"].values,
        "score": test_scores,
    })

    # Validate predictions match sample_submission exactly
    assert len(preds_df) == 2096, f"Expected 2096 test predictions, got {len(preds_df)}"
    assert preds_df["score"].isna().sum() == 0, "Found NaNs in predictions"
    assert not preds_df["order_id"].duplicated().any(), "Found duplicate order_ids"
    assert (preds_df["score"] >= 0.0).all() and (preds_df["score"] <= 1.0).all(), "Scores out of [0, 1] range"
    assert list(preds_df["order_id"]) == list(sample_sub["order_id"]), "order_id order does not match sample_submission.csv"

    # Save predictions.csv
    out_preds_path = ROOT / "outputs" / "predictions.csv"
    preds_df.to_csv(out_preds_path, index=False)
    print(f"Saved predictions to: {out_preds_path}")
    print(preds_df.head(10))
    print("\nSummary statistics of predicted test scores:")
    print(preds_df["score"].describe())


if __name__ == "__main__":
    main()
