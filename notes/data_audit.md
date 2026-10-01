# Data Audit Report

_All numbers produced by `scripts/audit.py`. No manual edits._


## 3.1 File-level facts

| File | Rows | Cols |
|---|---|---|
| train.csv | 11,155 | 19 |
| test_unlabelled.csv | 2,096 | 18 |
| sample_submission.csv | 2,096 | 2 |
| customers.csv | 9,000 | 5 |
| products.csv | 21 | 6 |

Train date range: 2025-04-01 to 2026-06-30
Test date range: 2026-07-01 to 2026-09-30

Train returned rate (raw): 0.1136 (11.4%)

## 3.2 Item 1: Partner-feed duplicate check

Rows with source=partner_feed: 651
Rows with source=crm: 10,504
Total raw: 11,155

Partner_feed sales_channel distribution:
  partner_outlet: 552
  marketplace: 37
  web: 31
  app: 31

Partner_feed order_ids that also appear in crm: 651 of 651

Test rows with source=partner_feed: 0

Duplicate order_ids within crm rows: 0
Train after dedupe (source==crm): 10,504
Returned rate after dedupe: 0.1142 (11.4%)


## Null counts

### Train nulls

- delivery_note: 2,589 (24.6%)
- pickup_scheduled_at: 9,273 (88.3%)

### Test nulls

- delivery_note: 538 (25.7%)
- pickup_scheduled_at: 2,096 (100.0%)


## 3.2 Item 2: last_service_event_type leakage check

Train last_service_event_type breakdown:

| Event type | Count | Return rate |
|---|---|---|
| NONE | 6,536 | 4.3% |
| DEMO_DONE | 1,417 | 0.0% |
| INSTALL_DONE | 1,354 | 0.0% |
| REVERSE_PICKUP | 750 | 100.0% |
| TECH_VISIT | 447 | 38.5% |

Test last_service_event_type values:
  NONE: 1553
  INSTALL_BOOKED: 543

INSTALL_BOOKED in train: 0


## 3.2 Item 3: pickup_scheduled_at leakage check

Train rows with pickup_scheduled_at not null: 1,231
Of those, returned=1: 1,130 (91.8%)
Test pickup_scheduled_at null count: 2,096 of 2,096 (100%)

Pickup lag (days): min=4, max=19, median=11


## 3.2 Item 4: October 2025 order_value inflation

Value ratio (order_value_inr / expected) by month:

| Month | Count | Median ratio | Min ratio | Max ratio |
|---|---|---|---|---|
| 2025-04 | 661 | 1.00 | 1.00 | 1.00 |
| 2025-05 | 674 | 1.00 | 1.00 | 1.00 |
| 2025-06 | 678 | 1.00 | 1.00 | 1.00 |
| 2025-07 | 736 | 1.00 | 1.00 | 1.00 |
| 2025-08 | 714 | 1.00 | 1.00 | 1.00 |
| 2025-09 | 707 | 1.00 | 1.00 | 1.00 |
| 2025-10 | 700 | 100.00 | 100.00 | 100.00 |
| 2025-11 | 698 | 1.00 | 1.00 | 1.00 |
| 2025-12 | 684 | 1.00 | 1.00 | 1.00 |
| 2026-01 | 719 | 1.00 | 1.00 | 1.00 |
| 2026-02 | 664 | 1.00 | 1.00 | 1.00 |
| 2026-03 | 743 | 1.00 | 1.00 | 1.00 |
| 2026-04 | 705 | 1.00 | 1.00 | 1.00 |
| 2026-05 | 722 | 1.00 | 1.00 | 1.00 |
| 2026-06 | 699 | 1.00 | 1.00 | 1.00 |

October 2025 rows: 700
October 2025 value_ratio range: 100.00 to 100.00
All Oct 2025 ratios approximately 100x: True

Test value_ratio range: 1.00 to 1.00 (clean)


## 3.2 Item 5: Pincode 000000

Train rows with pincode 000000: 848
Test rows with pincode 000000: 176

Train pincode=000000 by sales_channel:
  app: 300
  marketplace: 238
  web: 218
  partner_outlet: 92
  partner_outlet: 92, other channels: 756

Return rate for pincode 000000: 12.5%


## 3.2 Item 6: signup_date after order date

Train rows where signup_date > order_placed_at: 1,999
Test rows where signup_date > order_placed_at: 18


## 3.2 Item 7: customer_prior_* counters

Repeat customers (>1 order in deduped train): 2,970
Repeat customers with non-monotone customer_prior_orders: 1,471 of 2,970

Return rate by customer_prior_returns:

| Prior returns | Count | Return rate |
|---|---|---|
| 0 | 9,119 | 9.1% |
| 1 | 1,038 | 19.9% |
| 2 | 223 | 40.8% |
| 3 | 82 | 53.7% |
| 4 | 31 | 71.0% |
| 5 | 8 | 87.5% |
| 6 | 3 | 100.0% |

Correlation of customer_prior_returns with returned: 0.243


## 3.2 Item 9: delivery_note analysis

Train rows with delivery_note not null: 7,915
Unique templates (digits removed): 24
Raw unique strings: 738

Train orders with long delivery_note (>100 chars): 4 (rows: 4)
Test orders with long delivery_note (>100 chars): 0


## 3.2 Item 10: Right-censoring check

Latest train order date: 2026-06-30

Weekly return rate (last 14 weeks):

| Week | Orders | Returns | Rate |
|---|---|---|---|
| 2026-03-30/2026-04-05 | 161 | 17 | 10.6% |
| 2026-04-06/2026-04-12 | 169 | 22 | 13.0% |
| 2026-04-13/2026-04-19 | 156 | 24 | 15.4% |
| 2026-04-20/2026-04-26 | 181 | 15 | 8.3% |
| 2026-04-27/2026-05-03 | 135 | 17 | 12.6% |
| 2026-05-04/2026-05-10 | 182 | 24 | 13.2% |
| 2026-05-11/2026-05-17 | 144 | 18 | 12.5% |
| 2026-05-18/2026-05-24 | 182 | 14 | 7.7% |
| 2026-05-25/2026-05-31 | 160 | 21 | 13.1% |
| 2026-06-01/2026-06-07 | 163 | 27 | 16.6% |
| 2026-06-08/2026-06-14 | 160 | 16 | 10.0% |
| 2026-06-15/2026-06-21 | 176 | 11 | 6.2% |
| 2026-06-22/2026-06-28 | 148 | 16 | 10.8% |
| 2026-06-29/2026-07-05 | 52 | 7 | 13.5% |

Weekly rate range: 6.2% to 16.6%
Overall rate: 11.4%

Last 3 weeks avg rate: 10.2%
Earlier 11 weeks avg rate: 12.1%
No clear censoring drop detected in last 3 weeks

Pickup lag stats (days after order):
  Min: 4
  Max: 19
  Median: 11
  Mean: 11.4
  95th pct: 19

Orders within last 21 days of train: 520
Recommendation: optionally drop last 21 days as sensitivity check


## 3.2 Item 11: Drift check — monthly return rate

| Month | Orders | Returns | Rate |
|---|---|---|---|
| 2025-04 | 661 | 99 | 15.0% |
| 2025-05 | 674 | 81 | 12.0% |
| 2025-06 | 678 | 64 | 9.4% |
| 2025-07 | 736 | 87 | 11.8% |
| 2025-08 | 714 | 92 | 12.9% |
| 2025-09 | 707 | 60 | 8.5% |
| 2025-10 | 700 | 81 | 11.6% |
| 2025-11 | 698 | 74 | 10.6% |
| 2025-12 | 684 | 70 | 10.2% |
| 2026-01 | 719 | 81 | 11.3% |
| 2026-02 | 664 | 85 | 12.8% |
| 2026-03 | 743 | 81 | 10.9% |
| 2026-04 | 705 | 85 | 12.1% |
| 2026-05 | 722 | 83 | 11.5% |
| 2026-06 | 699 | 77 | 11.0% |

Monthly rate range: 8.5% to 15.0%


## 3.2 Item 12: Customer overlap between train and test

Unique customers in train: 6,131
Unique customers in test: 1,878
Test customers also in train: 1,290 (68.7%)


## Additional verification

Test and sample_submission order_ids match exactly: True
Test order_id duplicates: 0
Sample scores all 0.5: True

Train-test order_id overlap: 0

Customers.csv: 9,000 rows, unique customer_ids: 9,000
Customers.csv nulls: 0
All train customers in customers.csv: True
All test customers in customers.csv: True

Products.csv: 21 rows, families: 7, models per family: ~3
All train SKUs in products.csv: True
All test SKUs in products.csv: True


## 3.3 Useful signal summary (deduped train)

### payment_mode return rates

- cod: 18.8%
- emi: 9.1%
- prepaid_card: 8.8%
- prepaid_upi: 7.7%

### family return rates

- Robot Vacuum: 19.5%
- Water Purifier: 14.8%
- Air Fryer: 12.0%
- Room Heater: 11.7%
- Induction Cooktop: 8.3%
- Mixer Grinder: 6.8%
- Ceiling Fan: 6.7%

### warranty_months return rates

- 12 months: 13.3%
- 24 months: 6.7%

### shield_member return rates

- N: 9.4% (orders: 78%, returns: 64%)
- Y: 18.6% (orders: 22%, returns: 36%)

### sales_channel return rates

- marketplace: 13.6%
- web: 11.2%
- app: 10.7%
- partner_outlet: 9.1%

### is_gift return rates

- N: 11.0%
- Y: 16.5%
