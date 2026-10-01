# Infrastructure & Prediction Cost Model (Form Q6)

---

### 1. Cost per Prediction
* **Cost:** **₹0.00**
* **Inference Latency:** < 2.0 milliseconds per request on standard CPU.
* **Architecture:** In-memory scikit-learn pipeline (`ColumnTransformer` + `LogisticRegression`) running in a lightweight FastAPI asynchronous worker.

---

### 2. Monthly Operating Cost (at 700 orders/month)
* **API / Cloud Token Cost:** **₹0.00 / month** (Zero external LLM API calls, zero paid third-party dependencies).
* **Compute Footprint:** Runs on any standard shared CPU container (0.25 vCPU, < 150 MB RAM). Co-locates freely with existing backend infrastructure.
* **Total Software Cost:** **₹0.00 / month**.

---

### 3. Full Economic Cost-Benefit Arithmetic (per 700 Orders)

```
========================================================================================
Monthly Inbound Orders:                       700 orders
Base Return Rate (Empirical):                 11.46% (approx. 80.2 returns/month)
All-in Unit Return Loss (C_R):                Rs 1,150
----------------------------------------------------------------------------------------
1. Baseline Loss (Do Nothing):
   700 orders * 11.46% * Rs 1,150           = Rs 92,252.00 / month

2. Pre-Dispatch Confirmation Call Strategy (Recommended):
   - Orders Flagged for Call (49.55%):        346.8 orders
   - Cost of Agent Calls (346.8 * Rs 45):     Rs 15,607.00
   - Returns Captured (81.74% Recall):        65.6 returns flagged
   - Returns Prevented (35% effectiveness):   22.95 returns avoided
   - Return Losses Saved (22.95 * Rs 1,150):  Rs 26,392.50
   - Net Monthly Financial Gain:
     Rs 26,392.50 (Saved) - Rs 15,607.00 (Cost) = +Rs 10,785.50 / month

3. Software & Model Operating Cost:           Rs 0.00 / month
----------------------------------------------------------------------------------------
NET MONTHLY PROFIT TO KESTREL HOME:           +Rs 10,785 / month (Rs 1.29 Lakhs/year)
========================================================================================
```
