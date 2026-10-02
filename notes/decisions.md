# Strategic & Technical Decisions (Form Q4)

This document records the foundational positions, pushbacks, and technical decisions made during the Kestrel Home Returns Risk engagement.

---

### 1. Pushing Back on the 95% Accuracy Expectation
* **Client Request:** Ritu (Head of D2C Ops) requested 95%+ accuracy to report to the board.
* **My Decision:** Explicitly rejected the 95% classification accuracy target as scientifically invalid for this problem.
* **Rationale:** Returns represent only ~11.5% of orders. A naive, useless model predicting "NO return" on every order achieves **88.5% accuracy** with zero operational value. In severe class imbalance with human behavioral entropy, 95% accuracy is mathematically unachievable without suppressing almost all true returns.
* **Alternative Provided:** Replaced accuracy with ROC-AUC (`0.77`), PR-AUC (`0.39`), and rupee net savings (+₹10,785/month) at economically calibrated operating thresholds.

---

### 2. Operational Decision: Confirmation Calls vs. Order Holds
* **Client Proposal:** "Flag high-risk orders and hold dispatch."
* **My Decision:** Adopted a **Pre-Dispatch Confirmation Call** policy; firmly rejected dispatch holding.
* **Rationale:** Holding orders over 24 hours induces a 12% customer cancellation rate. Because ~80% of placed orders are kept, holding destroys gross margin on legitimate purchases, resulting in a net monthly loss of **-₹43,722/month** (at 15% margin). In contrast, proactive ₹45 confirmation calls resolve customer confusion, verify delivery addresses, and prevent 35% of returns, netting **+₹10,785/month** in pure profit.

---

### 3. VIP Treatment for Kestrel Shield Members
* **Client Proposal:** "Deal with Shield members later / treat everyone the same."
* **My Decision:** Shield members receive priority VIP confirmation calls, never dispatch holds.
* **Rationale:** Shield members have high return rates (20.7%) due to free return policies, but represent Kestrel's highest Lifetime Value (LTV) cohort (buying ~3 appliances/year). Subjecting them to order delays or cancellations alienates key brand advocates. Proactive customer concierge calls protect loyalty while clarifying sizing/installation.

---

### 4. True All-In Return Cost: ₹1,150 (Not ₹600)
* **Client Proposal:** Initial internal assumption that each return costs ~₹600.
* **My Decision:** Enforced the ₹1,150 all-in unit return cost provided by Finance (Farhan).
* **Rationale:** ₹600 accounted only for two-way shipping, ignoring reverse handling, QA testing, refurbishment, repackaging, and secondary channel liquidation discounts.

---

### 5. Strict Dropping of Post-Order Leakage Columns
* **Data Context:** The dataset contained `last_service_event_type` and `pickup_scheduled_at`.
* **My Decision:** Blacklisted and permanently dropped both columns from feature extraction and models.
* **Rationale:** `pickup_scheduled_at` is generated only after a customer return is approved; `last_service_event_type` records `REVERSE_PICKUP` post-delivery. Using them would constitute target leakage and render pre-dispatch scoring impossible in live production.

---

### 6. Deduplication and Data Repair
* **Deduplication:** Dropped all 651 `source == 'partner_feed'` duplicate rows, retaining only canonical `crm` records.
* **Currency Glitch Repair:** Corrected the October 2025 gateway bug by dividing inflated values (>5x expected list price) by 100 across 700 rows.
* **Address Flag:** Converted pincode to string, mapping `000000` to a dedicated `no_address` binary indicator.
