# Executive Memo: Pre-Dispatch Return Risk Strategy

**TO:** Ritu, Head of D2C Operations  
**FROM:** Udaya Harsha, Machine Learning Lead  
**DATE:** October 2, 2026  
**SUBJECT:** Operational Policy & Financial Return on Returns Risk Model

---

### 1. The Decision: Pre-Dispatch Verification Calls (Not Order Holds)

I recommend implementing **pre-dispatch confirmation calls (₹45/call)** on high-risk orders rather than **holding dispatches**.

* **Why Holding Fails:** Held orders suffer a 12% customer cancellation rate. Since >80% of orders are good purchases, holding orders destroys margin on legitimate sales.
* **Why Calls Succeed:** A brief call costs ₹45 and prevents 35% of returns by resolving address issues, clarifying installation needs (Water Purifiers, Ceiling Fans), and re-confirming COD buyer intent.
* **Kestrel Shield Policy:** Shield members return at double the base rate (20.7% vs 8.8%) due to free return privileges. **Shield members must receive priority VIP confirmation calls, never order holds.** This preserves high customer lifetime value while preventing return losses.

---

### 2. The Number: Honest Ranking vs. The 95% Accuracy Fallacy

* **Why 95% Accuracy is the Wrong Target:** Returns are ~11.5% of your orders. Guessing "NO return" achieves **88.5% accuracy** while catching zero returns. Reaching 95% raw accuracy on imbalanced data is impossible without missing true returns.
* **The Honest Ranking Metric:** My regularized Logistic Regression model achieves an out-of-sample **ROC-AUC of 0.7728** (95% CI: [0.739, 0.803]) and **PR-AUC of 0.3949**.
* **Operational Impact:** At the 0.34 threshold, the model flags ~49% of orders, capturing **>81% of all returned orders** before dispatch.

---

### 3. The Rupees: Monthly Financial Impact (per 700 Orders)

At your current volume of 700 orders/month (and ₹1,150 unit return cost):

| Operational Strategy | Monthly Policy Impact | Net Monthly Saving vs. Status Quo |
|---|---|---|
| **Do Nothing** (Status Quo) | -₹92,252 (Return losses) | Baseline (₹0) |
| **Pre-Dispatch Call** (Recommended) | -₹81,467 (Net costs + calls) | **+₹10,785 Net Savings** |
| **Hold Dispatch** (Initial Proposal) | -₹135,974 (Returns + lost margin) | **-₹43,722 Net Loss** |

* Calling the flagged slice costs ₹15,607 in agent time (347 calls @ ₹45) and avoids ₹26,393 in return losses, delivering **+₹10,785/month in net savings** (~₹1.3 Lakhs annually).
* **Model software cost is ₹0/month** (runs locally on CPU with zero API fees).

---

### 4. Next Week: 4-Week Operational Pilot

1. **Week 1 (Launch):** For orders scoring $\ge 0.34$, randomly assign 50% to confirmation calls (Treatment) and 50% to standard dispatch (Control).
2. **Weeks 2–3 (Execution):** Support agents use the top 3 plain-language risk reasons provided by the service to guide outreach.
3. **Week 4 (Review):** Compare return rates between Treatment and Control to confirm the ~₹10.8k/month savings before expanding to 100% of flagged volume.
