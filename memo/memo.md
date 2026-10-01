# Executive Memo: Pre-Dispatch Return Risk Strategy

**TO:** Ritu, Head of D2C Operations  
**FROM:** Kestrel Analytics & Operations Team  
**DATE:** October 1, 2026  
**SUBJECT:** Operational Policy & Financial Return on Returns Risk Model (Variant A)

---

### 1. The Decision: Pre-Dispatch Verification Calls (Not Order Holds)

We strongly recommend implementing **pre-dispatch confirmation calls** on high-risk orders rather than **holding or pausing dispatches**. 

* **Why Holding Orders Fails:** When an order is held, historical customer behavior shows a 12% cancellation rate. Because over 80% of placed orders are legitimate purchases that would not have been returned, holding orders destroys substantial gross margin on good sales.
* **Why Confirmation Calls Succeed:** A short, friendly confirmation call costs only ₹45 and prevents 35% of returns by resolving address ambiguities, clarifying installation needs (e.g., Water Purifiers and Ceiling Fans), and re-confirming Cash-on-Delivery (COD) buyer intent before shipping.
* **Policy on Kestrel Shield Members:** Shield members exhibit more than double the standard return rate (20.7% vs 8.8%) due to frictionless return privileges. **Shield members must receive proactive VIP confirmation calls, never order holds.** This preserves brand trust and loyalty while preventing unnecessary logistics expense.

---

### 2. The Number: Honest Ranking vs. The 95% Accuracy Fallacy

* **Why 95% Accuracy is the Wrong Metric:** Returns account for only 11.5% of our orders. A naive system that simply guesses "NO return" on every single order would achieve **88.5% accuracy**, yet it would catch zero returns and save ₹0. Reaching 95% raw accuracy on imbalanced data is mathematically impossible without missing most returns.
* **The Honest Performance Metric:** Our model is evaluated on its ability to accurately separate high-risk orders from low-risk orders (ROC-AUC). Across 3 rigorous out-of-sample backtests, the model achieved a consistent **AUC of 0.77** (95% confidence interval: 0.74 to 0.80).
* **Operational Impact:** At our operating threshold (0.34), the model flags the riskiest ~49% of orders and successfully captures **over 81% of all returning orders** before they leave the warehouse.

---

### 3. The Rupees: Monthly Financial Impact (per 700 Orders)

At our current monthly volume of 700 orders (and ₹1,150 average return cost):

| Operational Strategy | Monthly Policy Impact | Net Monthly Saving vs. Status Quo |
|---|---|---|
| **Do Nothing** (Status Quo) | -₹92,252 (Return losses) | Baseline (₹0) |
| **Pre-Dispatch Call** (Recommended) | -₹81,467 (Net costs + calls) | **+₹10,785 Net Savings** |
| **Hold Dispatch** (Ritu's Initial Plan) | -₹135,974 (Returns + lost margin) | **-₹43,722 Net Loss** |

* **Call Economics Breakdown:** Calling the flagged slice costs ₹15,624 in agent time (347 calls @ ₹45) and prevents ~23 returns, avoiding ₹26,409 in reverse logistics and restocking losses. Net benefit: **+₹10,785/month** (~₹1.3 Lakhs annually).
* **Software Operating Cost:** **₹0 per month.** The service runs entirely on existing CPU infrastructure with zero external API fees or cloud token expenses.

---

### 4. Next Week: 4-Week Operational Pilot

To roll out safely and prove value on live operations:

1. **Week 1 (A/B Pilot Launch):** Deploy the web screening tool to the fulfillment team. For orders above the 0.34 risk threshold, randomly assign 50% to receive confirmation calls (Treatment) and 50% to standard dispatch (Control).
2. **Week 2–3 (Call Script Execution):** Customer support agents use the top 3 plain-language risk reasons provided by the service (e.g., unverified pincode, high past return history, COD confirmation) to guide polite customer outreach.
3. **Week 4 (Financial Review):** Compare actual return rates between Treatment and Control groups to confirm the ~₹10.8k/month net savings rate before expanding to 100% of flagged volume.
