# Monday Handoff: 3 Priorities for the Engineering & Ops Team (Form Q10)

When handing off this system to the Kestrel Home engineering and fulfillment team on Monday, execute these 3 concrete steps:

---

### 1. Launch the 4-Week 50/50 A/B Confirmation Call Pilot
* **Action:** Integrate `POST /predict` into the warehouse management workflow. For orders scoring $\ge 0.34$, randomly assign 50% to receive proactive confirmation calls (Treatment) and 50% to standard uncalled dispatch (Control).
* **Objective:** Empirically validate the 35% return prevention rate and verify the ~₹10,800/month net savings rate under live operational conditions before scaling to 100% of orders.

---

### 2. Equip Support Agents with the 3 Plain-Language Call Reasons
* **Action:** Direct fulfillment and customer support agents to use the `top_3_reasons` field emitted by the API (e.g., verifying pincode address completeness, confirming COD payment readiness, explaining installation procedures for appliances like Water Purifiers/Ceiling Fans).
* **Objective:** Keep customer phone interactions friendly, helpful, and focused on proactive assistance rather than interrogation or order cancellation.

---

### 3. Establish Monthly Automated Retraining & Drift Monitoring
* **Action:** Schedule a monthly cron job to run `scripts/train.py` on the latest 3 quarters of historical CRM orders, generating refreshed model artifacts (`outputs/model_lr.joblib`) and updating calibration metrics.
* **Objective:** Continuously adapt to seasonal shifts (festive sales vs monsoon appliance demand) and expanding customer repeat history without manual engineering intervention.
