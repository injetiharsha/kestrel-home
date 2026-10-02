# Known Issues & Data Audit Findings (Form Q5)

This document details anomalies, defects, and historical integrity issues discovered in the Kestrel Home data export during Phase P1.

---

### 1. Partner Feed Duplicate Orders (651 Duplicate Rows)
* **Finding:** Exactly 651 `order_id` values appear twice in `train.csv`—once with `source == 'crm'` and once with `source == 'partner_feed'`.
* **Impact:** `partner_feed` rows contained outdated fields and duplicate order timestamps.
* **Resolution:** Filtered dataset to `source == 'crm'` exclusively, dropping all 651 duplicates and reducing training rows from 11,155 to exactly 10,504 unique orders.

---

### 2. October 2025 Currency Unit Bug (x100 Inflation across 700 Rows)
* **Finding:** In October 2025 (festive campaign), order values for 700 orders were recorded in *paise* rather than *rupees* (e.g., an order worth ₹3,500 was recorded as ₹350,000) due to an unvalidated payment gateway update.
* **Impact:** Uncorrected values severely distort numeric scaling and revenue loss calculations.
* **Resolution:** Calculated expected order value ($P_{\text{list}} \times \text{qty} \times [1 - \text{discount}\%]$) and divided `order_value_inr` by 100 for all rows exceeding 5x expected value.

---

### 3. Pincode `000000` & Walk-In Address Ambiguity
* **Finding:** 152 orders contain `delivery_pincode == 000000`. 
* **Correction of README Assumption:** README suggested `000000` represented partner walk-in purchases. However, data shows these orders span multiple sales channels (web, app) with normal delivery promises, indicating missing or unverified address collection.
* **Resolution:** Pincodes parsed as 6-digit zero-padded strings, with `000000` encoded as a distinct `no_address = 1` boolean flag.

---

### 4. Post-Order Target Leakage in Data Export
* **Finding:** Columns `last_service_event_type` and `pickup_scheduled_at` reflect the state of the database *on the day of data export*, not *at order placement*.
* **Risk:** In `train.csv`, `pickup_scheduled_at` is populated on 1,281 orders (1,172 returned, 109 cancelled pickups). In `test_unlabelled.csv`, it is completely empty (`NaN` for all 2,096 rows).
* **Resolution:** Strictly blacklisted both columns in `src/features.py` and enforced via automated unit tests (`tests/test_blacklist.py`).

---

### 5. Right-Censoring Return Lag (Up to 19 Days)
* **Finding:** Customers have a 14-day return window (30 days for Shield members). In the data, the empirical lag from order placement to return resolution spans up to 19 days.
* **Impact:** Orders placed in the final 2–3 weeks of an observation window risk being labeled `returned = 0` simply because the return has not completed processing.
* **Validation:** Tested sensitivity by dropping the last 21 days in backtest Fold 3; model performance remained robust ($\Delta\text{AUC} = -0.0053$).

---

### 6. Free-Text Variations in Delivery Notes
* **Finding:** Delivery notes contained raw unstructured text variations, punctuation, and anomalies.
* **Resolution:** Treated raw text purely as data (never instructions), stripped freeform text, and collapsed delivery notes into safe categorical templates (`NONE`, `Leave with security`, `Call before delivery`, `Office address, weekdays only`).

---

### 7. Customer `signup_date` Inversion (Later DB Snapshot)
* **Finding:** `signup_date` is after `order_placed_at` on 1,999 train rows and 18 test rows because `customers.csv` reflects a later database export/backfill snapshot rather than true historical state at order placement.
* **Resolution:** I did not use customer tenure features in the model.

---

### 8. Zoho UTC Timestamp Offset (Policy Item 9)
* **Finding:** Legacy service events before 1 Oct 2025 were logged in UTC rather than IST (+5:30).
* **Resolution:** Moot, because `pickup_scheduled_at` and `last_service_event_type` are post-order target leakage and are completely dropped from feature engineering.

---

### 9. Clarification on `source` Column
* **Finding:** `source` is not a leakage column: it only marks duplicate partner-feed rows (none in test).
* **Resolution:** I dropped all `partner_feed` rows during cleaning and did not use the `source` column in feature engineering.

---

### 10. Non-Informative Feature Shortcut
* **Finding:** Features `hour`, `weekday`, `delivery_note_template`, and `pincode_prefix` add no measurable signal (ablation AUC changes span +0.0002 to +0.004).
* **Resolution:** They remain in the final locked model pipeline because I did not retrain after the expected score and test predictions were committed.
