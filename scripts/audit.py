#!/usr/bin/env python3
"""
scripts/audit.py — Data Audit Runner
Reproduces and verifies statistical distributions and data integrity across files.
"""

import pathlib
import pandas as pd
import numpy as np
from collections import OrderedDict

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

lines: list[str] = []


def w(text: str = ""):
    """Append a line to the report."""
    lines.append(text)


def section(title: str):
    w()
    w(f"## {title}")
    w()


def main():
    w("# Data Audit Report")
    w()
    w("_All numbers produced by `scripts/audit.py`. No manual edits._")
    w()

    # ------------------------------------------------------------------ #
    # Load raw files
    # ------------------------------------------------------------------ #
    train_raw = pd.read_csv(DATA / "train.csv")
    test = pd.read_csv(DATA / "test_unlabelled.csv")
    sample = pd.read_csv(DATA / "sample_submission.csv")
    customers = pd.read_csv(DATA / "customers.csv")
    products = pd.read_csv(DATA / "products.csv")

    # ------------------------------------------------------------------ #
    # 3.1 File-level facts
    # ------------------------------------------------------------------ #
    section("3.1 File-level facts")

    w(f"| File | Rows | Cols |")
    w(f"|---|---|---|")
    w(f"| train.csv | {len(train_raw):,} | {train_raw.shape[1]} |")
    w(f"| test_unlabelled.csv | {len(test):,} | {test.shape[1]} |")
    w(f"| sample_submission.csv | {len(sample):,} | {sample.shape[1]} |")
    w(f"| customers.csv | {len(customers):,} | {customers.shape[1]} |")
    w(f"| products.csv | {len(products):,} | {products.shape[1]} |")
    w()

    # Train date range
    train_raw["order_placed_at"] = pd.to_datetime(train_raw["order_placed_at"])
    test["order_placed_at"] = pd.to_datetime(test["order_placed_at"])
    w(f"Train date range: {train_raw['order_placed_at'].min().date()} to {train_raw['order_placed_at'].max().date()}")
    w(f"Test date range: {test['order_placed_at'].min().date()} to {test['order_placed_at'].max().date()}")
    w()

    # Train returned rate (raw)
    ret_rate_raw = train_raw["returned"].mean()
    w(f"Train returned rate (raw): {ret_rate_raw:.4f} ({ret_rate_raw*100:.1f}%)")

    # ------------------------------------------------------------------ #
    # 3.2 Item 1: Deduplication — partner_feed rows
    # ------------------------------------------------------------------ #
    section("3.2 Item 1: Partner-feed duplicate check")

    partner_feed = train_raw[train_raw["source"] == "partner_feed"]
    crm_only = train_raw[train_raw["source"] == "crm"]
    w(f"Rows with source=partner_feed: {len(partner_feed):,}")
    w(f"Rows with source=crm: {len(crm_only):,}")
    w(f"Total raw: {len(train_raw):,}")
    w()

    # Check partner_feed are all partner_outlet
    pf_channels = partner_feed["sales_channel"].value_counts()
    w(f"Partner_feed sales_channel distribution:")
    for ch, cnt in pf_channels.items():
        w(f"  {ch}: {cnt}")
    w()

    # Verify partner_feed order_ids are a subset of crm order_ids
    pf_ids = set(partner_feed["order_id"])
    crm_ids = set(crm_only["order_id"])
    overlap = pf_ids & crm_ids
    w(f"Partner_feed order_ids that also appear in crm: {len(overlap)} of {len(pf_ids)}")
    w()

    # Test has no partner_feed
    test_pf = test[test["source"] == "partner_feed"] if "source" in test.columns else pd.DataFrame()
    w(f"Test rows with source=partner_feed: {len(test_pf)}")
    w()

    # Dedupe: keep crm only
    train = crm_only.copy().reset_index(drop=True)
    # Also check for any remaining dup order_ids within crm
    dup_crm_ids = train["order_id"].duplicated().sum()
    w(f"Duplicate order_ids within crm rows: {dup_crm_ids}")
    w(f"Train after dedupe (source==crm): {len(train):,}")

    ret_rate_deduped = train["returned"].mean()
    w(f"Returned rate after dedupe: {ret_rate_deduped:.4f} ({ret_rate_deduped*100:.1f}%)")
    w()

    # ------------------------------------------------------------------ #
    # Null analysis
    # ------------------------------------------------------------------ #
    section("Null counts")

    w("### Train nulls")
    w()
    train_nulls = train.isnull().sum()
    for col in train.columns:
        n = train_nulls[col]
        if n > 0:
            w(f"- {col}: {n:,} ({n/len(train)*100:.1f}%)")
    if train_nulls.sum() == 0:
        w("- No nulls")
    w()

    w("### Test nulls")
    w()
    test_nulls = test.isnull().sum()
    for col in test.columns:
        n = test_nulls[col]
        if n > 0:
            pct = n / len(test) * 100
            w(f"- {col}: {n:,} ({pct:.1f}%)")
    if test_nulls.sum() == 0:
        w("- No nulls")
    w()

    # ------------------------------------------------------------------ #
    # 3.2 Item 2: last_service_event_type leakage
    # ------------------------------------------------------------------ #
    section("3.2 Item 2: last_service_event_type leakage check")

    lset_train = train.groupby("last_service_event_type").agg(
        count=("returned", "size"),
        return_rate=("returned", "mean")
    ).sort_values("count", ascending=False)
    w("Train last_service_event_type breakdown:")
    w()
    w("| Event type | Count | Return rate |")
    w("|---|---|---|")
    for idx, row in lset_train.iterrows():
        w(f"| {idx} | {int(row['count']):,} | {row['return_rate']:.1%} |")
    w()

    test_lset_vals = test["last_service_event_type"].value_counts()
    w("Test last_service_event_type values:")
    for v, c in test_lset_vals.items():
        w(f"  {v}: {c}")
    w()

    # Check INSTALL_BOOKED in train
    ib_in_train = (train["last_service_event_type"] == "INSTALL_BOOKED").sum()
    w(f"INSTALL_BOOKED in train: {ib_in_train}")
    w()

    # ------------------------------------------------------------------ #
    # 3.2 Item 3: pickup_scheduled_at is the label
    # ------------------------------------------------------------------ #
    section("3.2 Item 3: pickup_scheduled_at leakage check")

    pickup_notnull = train["pickup_scheduled_at"].notna()
    n_pickup = pickup_notnull.sum()
    pickup_returned = train.loc[pickup_notnull, "returned"].sum()
    w(f"Train rows with pickup_scheduled_at not null: {n_pickup:,}")
    w(f"Of those, returned=1: {int(pickup_returned):,} ({pickup_returned/n_pickup:.1%})")
    w(f"Test pickup_scheduled_at null count: {test['pickup_scheduled_at'].isnull().sum():,} of {len(test):,} ({test['pickup_scheduled_at'].isnull().mean():.0%})")
    w()

    # Pickup lag analysis
    train["pickup_scheduled_at_dt"] = pd.to_datetime(train["pickup_scheduled_at"], errors="coerce")
    pickup_rows = train[train["pickup_scheduled_at_dt"].notna()].copy()
    pickup_rows["pickup_lag_days"] = (pickup_rows["pickup_scheduled_at_dt"] - pickup_rows["order_placed_at"]).dt.days
    w(f"Pickup lag (days): min={pickup_rows['pickup_lag_days'].min()}, max={pickup_rows['pickup_lag_days'].max()}, median={pickup_rows['pickup_lag_days'].median():.0f}")
    w()

    # ------------------------------------------------------------------ #
    # 3.2 Item 4: Oct 2025 order_value x100
    # ------------------------------------------------------------------ #
    section("3.2 Item 4: October 2025 order_value inflation")

    train_with_prod = train.merge(products[["sku", "list_price_inr"]], on="sku", how="left")
    train_with_prod["expected_value"] = (
        train_with_prod["list_price_inr"]
        * train_with_prod["qty"]
        * (1 - train_with_prod["discount_pct"] / 100)
    )
    train_with_prod["value_ratio"] = train_with_prod["order_value_inr"] / train_with_prod["expected_value"]
    train_with_prod["order_month"] = train_with_prod["order_placed_at"].dt.to_period("M")

    w("Value ratio (order_value_inr / expected) by month:")
    w()
    w("| Month | Count | Median ratio | Min ratio | Max ratio |")
    w("|---|---|---|---|---|")
    for month in sorted(train_with_prod["order_month"].unique()):
        subset = train_with_prod[train_with_prod["order_month"] == month]
        w(f"| {month} | {len(subset):,} | {subset['value_ratio'].median():.2f} | {subset['value_ratio'].min():.2f} | {subset['value_ratio'].max():.2f} |")
    w()

    oct_2025 = train_with_prod[train_with_prod["order_month"] == pd.Period("2025-10", "M")]
    w(f"October 2025 rows: {len(oct_2025):,}")
    w(f"October 2025 value_ratio range: {oct_2025['value_ratio'].min():.2f} to {oct_2025['value_ratio'].max():.2f}")
    all_100x = (oct_2025["value_ratio"].round(0) == 100).all()
    w(f"All Oct 2025 ratios approximately 100x: {all_100x}")
    w()

    # Test check
    test_with_prod = test.merge(products[["sku", "list_price_inr"]], on="sku", how="left")
    test_with_prod["expected_value"] = (
        test_with_prod["list_price_inr"]
        * test_with_prod["qty"]
        * (1 - test_with_prod["discount_pct"] / 100)
    )
    test_with_prod["value_ratio"] = test_with_prod["order_value_inr"] / test_with_prod["expected_value"]
    test_ratio_range = f"{test_with_prod['value_ratio'].min():.2f} to {test_with_prod['value_ratio'].max():.2f}"
    w(f"Test value_ratio range: {test_ratio_range} (clean)")
    w()

    # ------------------------------------------------------------------ #
    # 3.2 Item 5: Pincode 000000
    # ------------------------------------------------------------------ #
    section("3.2 Item 5: Pincode 000000")

    train["delivery_pincode_str"] = train["delivery_pincode"].astype(str).str.zfill(6)
    test["delivery_pincode_str"] = test["delivery_pincode"].astype(str).str.zfill(6)

    train_zero_pin = train[train["delivery_pincode_str"] == "000000"]
    test_zero_pin = test[test["delivery_pincode_str"] == "000000"]
    w(f"Train rows with pincode 000000: {len(train_zero_pin):,}")
    w(f"Test rows with pincode 000000: {len(test_zero_pin):,}")
    w()

    # Check channels for pincode 000000
    w("Train pincode=000000 by sales_channel:")
    pin_channels = train_zero_pin["sales_channel"].value_counts()
    for ch, cnt in pin_channels.items():
        w(f"  {ch}: {cnt}")
    partner_outlet_count = pin_channels.get("partner_outlet", 0)
    non_partner = len(train_zero_pin) - partner_outlet_count
    w(f"  partner_outlet: {partner_outlet_count}, other channels: {non_partner}")
    w()

    # Return rate for pincode 000000
    ret_zero_pin = train_zero_pin["returned"].mean()
    w(f"Return rate for pincode 000000: {ret_zero_pin:.1%}")
    w()

    # ------------------------------------------------------------------ #
    # 3.2 Item 6: signup_date after order date
    # ------------------------------------------------------------------ #
    section("3.2 Item 6: signup_date after order date")

    train_cust = train.merge(customers[["customer_id", "signup_date"]], on="customer_id", how="left")
    train_cust["signup_date_dt"] = pd.to_datetime(train_cust["signup_date"])
    train_signup_after = (train_cust["signup_date_dt"] > train_cust["order_placed_at"]).sum()
    w(f"Train rows where signup_date > order_placed_at: {train_signup_after:,}")

    test_cust = test.merge(customers[["customer_id", "signup_date"]], on="customer_id", how="left")
    test_cust["signup_date_dt"] = pd.to_datetime(test_cust["signup_date"])
    test_signup_after = (test_cust["signup_date_dt"] > test_cust["order_placed_at"]).sum()
    w(f"Test rows where signup_date > order_placed_at: {test_signup_after:,}")
    w()

    # ------------------------------------------------------------------ #
    # 3.2 Item 7: customer_prior_* counters
    # ------------------------------------------------------------------ #
    section("3.2 Item 7: customer_prior_* counters")

    # Check monotonicity: for each customer with multiple orders, prior_orders should increase
    repeat_cust = train.groupby("customer_id").filter(lambda g: len(g) > 1)
    n_repeat_customers = repeat_cust["customer_id"].nunique()
    w(f"Repeat customers (>1 order in deduped train): {n_repeat_customers:,}")

    non_mono_count = 0
    for cid, grp in repeat_cust.groupby("customer_id"):
        grp_sorted = grp.sort_values("order_placed_at")
        prior_orders = grp_sorted["customer_prior_orders"].values
        if not all(prior_orders[i] <= prior_orders[i+1] for i in range(len(prior_orders)-1)):
            non_mono_count += 1
    w(f"Repeat customers with non-monotone customer_prior_orders: {non_mono_count:,} of {n_repeat_customers:,}")
    w()

    # Return rate by prior_returns
    w("Return rate by customer_prior_returns:")
    w()
    w("| Prior returns | Count | Return rate |")
    w("|---|---|---|")
    for val in sorted(train["customer_prior_returns"].unique()):
        subset = train[train["customer_prior_returns"] == val]
        w(f"| {val} | {len(subset):,} | {subset['returned'].mean():.1%} |")
    w()

    # Correlation
    corr_prior = train["customer_prior_returns"].corr(train["returned"])
    w(f"Correlation of customer_prior_returns with returned: {corr_prior:.3f}")
    w()

    # ------------------------------------------------------------------ #
    # 3.2 Item 9: delivery_note templates
    # ------------------------------------------------------------------ #
    section("3.2 Item 9: delivery_note analysis")

    dn_notnull = train[train["delivery_note"].notna()].copy()
    w(f"Train rows with delivery_note not null: {len(dn_notnull):,}")

    # Template: strip digits
    import re
    dn_notnull["dn_template"] = dn_notnull["delivery_note"].apply(
        lambda x: re.sub(r'\d+', '', str(x)).strip() if pd.notna(x) else x
    )
    n_templates = dn_notnull["dn_template"].nunique()
    w(f"Unique templates (digits removed): {n_templates}")
    w(f"Raw unique strings: {dn_notnull['delivery_note'].nunique()}")
    w()

    # Long free text (> 100 chars)
    dn_notnull["dn_len"] = dn_notnull["delivery_note"].str.len()
    long_notes = dn_notnull[dn_notnull["dn_len"] > 100]
    long_orders = long_notes["order_id"].nunique()
    w(f"Train orders with long delivery_note (>100 chars): {long_orders} (rows: {len(long_notes)})")

    test_dn_long = test[test["delivery_note"].notna() & (test["delivery_note"].str.len() > 100)]
    w(f"Test orders with long delivery_note (>100 chars): {len(test_dn_long)}")
    w()

    # ------------------------------------------------------------------ #
    # 3.2 Item 10: Right-censoring check
    # ------------------------------------------------------------------ #
    section("3.2 Item 10: Right-censoring check")

    train["order_week"] = train["order_placed_at"].dt.to_period("W")
    max_date = train["order_placed_at"].max()
    w(f"Latest train order date: {max_date.date()}")
    w()

    # Weekly return rate for last 14 weeks
    weeks_sorted = sorted(train["order_week"].unique())
    last_14 = weeks_sorted[-14:]
    w("Weekly return rate (last 14 weeks):")
    w()
    w("| Week | Orders | Returns | Rate |")
    w("|---|---|---|---|")
    weekly_rates = []
    for wk in last_14:
        wk_data = train[train["order_week"] == wk]
        rate = wk_data["returned"].mean()
        weekly_rates.append(rate)
        w(f"| {wk} | {len(wk_data):,} | {int(wk_data['returned'].sum())} | {rate:.1%} |")
    w()
    w(f"Weekly rate range: {min(weekly_rates):.1%} to {max(weekly_rates):.1%}")
    w(f"Overall rate: {train['returned'].mean():.1%}")
    w()

    # Check for a drop in the last few weeks (censoring signal)
    last_3_rate = np.mean(weekly_rates[-3:])
    earlier_rate = np.mean(weekly_rates[:-3])
    w(f"Last 3 weeks avg rate: {last_3_rate:.1%}")
    w(f"Earlier 11 weeks avg rate: {earlier_rate:.1%}")
    if last_3_rate < earlier_rate * 0.7:
        w("WARNING: Possible censoring detected (last 3 weeks rate notably lower)")
    else:
        w("No clear censoring drop detected in last 3 weeks")
    w()

    # Pickup lag details
    w(f"Pickup lag stats (days after order):")
    w(f"  Min: {pickup_rows['pickup_lag_days'].min()}")
    w(f"  Max: {pickup_rows['pickup_lag_days'].max()}")
    w(f"  Median: {pickup_rows['pickup_lag_days'].median():.0f}")
    w(f"  Mean: {pickup_rows['pickup_lag_days'].mean():.1f}")
    w(f"  95th pct: {pickup_rows['pickup_lag_days'].quantile(0.95):.0f}")
    w()

    # Days from latest order to end of train window
    days_since_last = (max_date - train["order_placed_at"]).dt.days
    orders_last_21 = (days_since_last <= 21).sum()
    w(f"Orders within last 21 days of train: {orders_last_21:,}")
    w(f"Recommendation: optionally drop last 21 days as sensitivity check")
    w()

    # ------------------------------------------------------------------ #
    # 3.2 Item 11: Drift — monthly return rate
    # ------------------------------------------------------------------ #
    section("3.2 Item 11: Drift check — monthly return rate")

    train["order_month_str"] = train["order_placed_at"].dt.to_period("M").astype(str)
    monthly = train.groupby("order_month_str").agg(
        orders=("returned", "size"),
        returns=("returned", "sum"),
        rate=("returned", "mean"),
    )
    w("| Month | Orders | Returns | Rate |")
    w("|---|---|---|---|")
    for idx, row in monthly.iterrows():
        w(f"| {idx} | {int(row['orders']):,} | {int(row['returns'])} | {row['rate']:.1%} |")
    w()
    w(f"Monthly rate range: {monthly['rate'].min():.1%} to {monthly['rate'].max():.1%}")
    w()

    # ------------------------------------------------------------------ #
    # 3.2 Item 12: Customer overlap
    # ------------------------------------------------------------------ #
    section("3.2 Item 12: Customer overlap between train and test")

    train_cust_ids = set(train["customer_id"])
    test_cust_ids = set(test["customer_id"])
    overlap_cust = test_cust_ids & train_cust_ids
    overlap_pct = len(overlap_cust) / len(test_cust_ids) * 100
    w(f"Unique customers in train: {len(train_cust_ids):,}")
    w(f"Unique customers in test: {len(test_cust_ids):,}")
    w(f"Test customers also in train: {len(overlap_cust):,} ({overlap_pct:.1f}%)")
    w()

    # ------------------------------------------------------------------ #
    # Additional verification checks
    # ------------------------------------------------------------------ #
    section("Additional verification")

    # Test / sample alignment
    test_ids = test["order_id"].tolist()
    sample_ids = sample["order_id"].tolist()
    w(f"Test and sample_submission order_ids match exactly: {test_ids == sample_ids}")
    w(f"Test order_id duplicates: {test['order_id'].duplicated().sum()}")
    w(f"Sample scores all 0.5: {(sample['score'] == 0.5).all()}")
    w()

    # Zero overlap between train and test IDs
    train_test_id_overlap = set(train["order_id"]) & set(test["order_id"])
    w(f"Train-test order_id overlap: {len(train_test_id_overlap)}")
    w()

    # Customers.csv checks
    w(f"Customers.csv: {len(customers):,} rows, unique customer_ids: {customers['customer_id'].nunique():,}")
    w(f"Customers.csv nulls: {customers.isnull().sum().sum()}")
    all_train_cust_match = train["customer_id"].isin(customers["customer_id"]).all()
    all_test_cust_match = test["customer_id"].isin(customers["customer_id"]).all()
    w(f"All train customers in customers.csv: {all_train_cust_match}")
    w(f"All test customers in customers.csv: {all_test_cust_match}")
    w()

    # Products.csv checks
    w(f"Products.csv: {len(products)} rows, families: {products['family'].nunique()}, models per family: ~{len(products) // products['family'].nunique()}")
    all_train_sku_match = train["sku"].isin(products["sku"]).all()
    all_test_sku_match = test["sku"].isin(products["sku"]).all()
    w(f"All train SKUs in products.csv: {all_train_sku_match}")
    w(f"All test SKUs in products.csv: {all_test_sku_match}")
    w()

    # ------------------------------------------------------------------ #
    # 3.3 Signal summary (deduped train)
    # ------------------------------------------------------------------ #
    section("3.3 Useful signal summary (deduped train)")

    # Merge with products and customers for family/shield
    train_full = train.merge(products[["sku", "family", "warranty_months"]], on="sku", how="left")
    train_full = train_full.merge(customers[["customer_id", "shield_member"]], on="customer_id", how="left")

    # Payment mode return rates
    w("### payment_mode return rates")
    w()
    pm_rates = train_full.groupby("payment_mode")["returned"].mean().sort_values(ascending=False)
    for pm, rate in pm_rates.items():
        w(f"- {pm}: {rate:.1%}")
    w()

    # Family return rates
    w("### family return rates")
    w()
    fam_rates = train_full.groupby("family")["returned"].mean().sort_values(ascending=False)
    for fam, rate in fam_rates.items():
        w(f"- {fam}: {rate:.1%}")
    w()

    # Warranty return rates
    w("### warranty_months return rates")
    w()
    for wm in sorted(train_full["warranty_months"].unique()):
        subset = train_full[train_full["warranty_months"] == wm]
        w(f"- {wm} months: {subset['returned'].mean():.1%}")
    w()

    # Shield member
    w("### shield_member return rates")
    w()
    for sm in sorted(train_full["shield_member"].dropna().unique()):
        subset = train_full[train_full["shield_member"] == sm]
        shield_pct_orders = len(subset) / len(train_full) * 100
        shield_pct_returns = subset["returned"].sum() / train_full["returned"].sum() * 100
        w(f"- {sm}: {subset['returned'].mean():.1%} (orders: {shield_pct_orders:.0f}%, returns: {shield_pct_returns:.0f}%)")
    w()

    # Sales channel
    w("### sales_channel return rates")
    w()
    ch_rates = train_full.groupby("sales_channel")["returned"].mean().sort_values(ascending=False)
    for ch, rate in ch_rates.items():
        w(f"- {ch}: {rate:.1%}")
    w()

    # is_gift
    w("### is_gift return rates")
    w()
    for g in sorted(train_full["is_gift"].unique()):
        subset = train_full[train_full["is_gift"] == g]
        w(f"- {g}: {subset['returned'].mean():.1%}")
    w()

    # ------------------------------------------------------------------ #
    # Write output
    # ------------------------------------------------------------------ #
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Audit report written to {OUT}")
    print(f"Total lines: {len(lines)}")


if __name__ == "__main__":
    main()
