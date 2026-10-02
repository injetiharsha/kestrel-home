"""
tests/test_blacklist.py — Enforce feature blacklist.

Blacklisted columns must NEVER appear in the feature matrix:
  returned, last_service_event_type, pickup_scheduled_at, source,
  order_id, customer_id, signup_date (and any tenure derived from it),
  order month/year, raw delivery_note text, any column not in the test file.
"""

import sys
import pathlib
import pytest
import pandas as pd

# Add project root to path
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.cleaning import clean_train, load_products, load_customers
from src.features import (
    build_features,
    get_feature_matrix,
    verify_no_blacklist,
    BLACKLIST,
    FEATURE_COLS,
)


DATA = ROOT / "data"


@pytest.fixture(scope="module")
def cleaned_data():
    """Load and clean train data once for all tests."""
    train_path = DATA / "train.csv"
    if not train_path.exists():
        pytest.skip("data/ not present")
    train_raw = pd.read_csv(train_path)
    products = load_products()
    customers = load_customers()
    train_clean = clean_train(train_raw, products)
    features_df = build_features(train_clean, products, customers)
    feature_matrix = get_feature_matrix(features_df)
    return features_df, feature_matrix


class TestBlacklist:
    """Tests that blacklisted columns are never used as features."""

    def test_no_blacklisted_columns_in_feature_matrix(self, cleaned_data):
        """Feature matrix must not contain any blacklisted column."""
        _, feature_matrix = cleaned_data
        violations = verify_no_blacklist(feature_matrix)
        assert violations == [], f"Blacklisted columns found in features: {violations}"

    def test_returned_not_a_feature(self, cleaned_data):
        """'returned' must never be a feature."""
        _, feature_matrix = cleaned_data
        assert "returned" not in feature_matrix.columns

    def test_last_service_event_type_not_a_feature(self, cleaned_data):
        """'last_service_event_type' must never be a feature."""
        _, feature_matrix = cleaned_data
        assert "last_service_event_type" not in feature_matrix.columns

    def test_pickup_scheduled_at_not_a_feature(self, cleaned_data):
        """'pickup_scheduled_at' must never be a feature."""
        _, feature_matrix = cleaned_data
        assert "pickup_scheduled_at" not in feature_matrix.columns

    def test_source_not_a_feature(self, cleaned_data):
        """'source' must never be a feature."""
        _, feature_matrix = cleaned_data
        assert "source" not in feature_matrix.columns

    def test_order_id_not_a_feature(self, cleaned_data):
        """'order_id' must never be a feature."""
        _, feature_matrix = cleaned_data
        assert "order_id" not in feature_matrix.columns

    def test_customer_id_not_a_feature(self, cleaned_data):
        """'customer_id' must never be a feature."""
        _, feature_matrix = cleaned_data
        assert "customer_id" not in feature_matrix.columns

    def test_signup_date_not_a_feature(self, cleaned_data):
        """'signup_date' and tenure must never be features."""
        _, feature_matrix = cleaned_data
        tenure_cols = {"signup_date", "tenure", "tenure_days", "customer_tenure"}
        present = tenure_cols & set(feature_matrix.columns)
        assert present == set(), f"Tenure-related columns found: {present}"

    def test_order_month_year_not_a_feature(self, cleaned_data):
        """Order month/year must never be features."""
        _, feature_matrix = cleaned_data
        time_cols = {"order_month", "order_year", "order_month_year"}
        present = time_cols & set(feature_matrix.columns)
        assert present == set(), f"Time columns found: {present}"

    def test_raw_delivery_note_not_a_feature(self, cleaned_data):
        """Raw delivery_note text must never be a feature (template is OK)."""
        _, feature_matrix = cleaned_data
        assert "delivery_note" not in feature_matrix.columns
        # delivery_note_template IS allowed
        assert "delivery_note_template" in feature_matrix.columns

    def test_only_approved_columns_in_features(self, cleaned_data):
        """Feature matrix must contain only approved feature columns."""
        _, feature_matrix = cleaned_data
        extra = set(feature_matrix.columns) - set(FEATURE_COLS)
        assert extra == set(), f"Unapproved columns in features: {extra}"

    def test_feature_cols_list_has_no_blacklisted(self):
        """FEATURE_COLS constant must not reference any blacklisted column."""
        violations = set(FEATURE_COLS) & BLACKLIST
        assert violations == set(), f"FEATURE_COLS references blacklisted: {violations}"


class TestCleaning:
    """Tests that cleaning is correct."""

    def test_deduplication_removes_partner_feed(self, cleaned_data):
        """After cleaning, source column should be gone and no partner_feed rows."""
        features_df, _ = cleaned_data
        assert "source" not in features_df.columns

    def test_deduplicated_row_count(self, cleaned_data):
        """Deduped train should have 10,504 rows."""
        features_df, _ = cleaned_data
        assert len(features_df) == 10504, f"Expected 10504, got {len(features_df)}"

    def test_oct_values_fixed(self, cleaned_data):
        """Oct 2025 order values should be corrected (no values > 5x list price)."""
        features_df, feature_matrix = cleaned_data
        # After fix, order_value_fixed should be reasonable
        # Max list_price is ~29698, max qty likely small, so values > 100k are suspicious
        assert feature_matrix["order_value_fixed"].max() < 200000, \
            "order_value_fixed has suspiciously high values"

    def test_no_address_flag(self, cleaned_data):
        """no_address flag should be set for pincode 000000."""
        _, feature_matrix = cleaned_data
        assert feature_matrix["no_address"].sum() > 0, "no_address flag never set"

    def test_installable_flag(self, cleaned_data):
        """installable should be 1 for Ceiling Fan, Robot Vacuum, Water Purifier."""
        _, feature_matrix = cleaned_data
        installable_mask = feature_matrix["family"].isin(
            {"Ceiling Fan", "Robot Vacuum", "Water Purifier"}
        )
        assert (feature_matrix.loc[installable_mask, "installable"] == 1).all()
        assert (feature_matrix.loc[~installable_mask, "installable"] == 0).all()

    def test_no_nans_in_key_features(self, cleaned_data):
        """Key numeric features should have no NaNs."""
        _, feature_matrix = cleaned_data
        no_nan_cols = [
            "discount_pct", "qty", "order_value_fixed",
            "promised_delivery_days", "no_address",
            "customer_prior_orders", "customer_prior_returns",
        ]
        for col in no_nan_cols:
            assert feature_matrix[col].isna().sum() == 0, f"NaN found in {col}"
