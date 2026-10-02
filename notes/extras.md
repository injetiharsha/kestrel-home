# Built or Found Unasked (Form Q8)

This document records high-value discoveries, security hardening, and tooling built during the engagement that went beyond the baseline specification.

---

### 1. Delivery Note Template Normalization
* **Discovery:** Data audit showed hundreds of unstructured raw `delivery_note` strings that could introduce text variance.
* **Implementation:** Built a template normalization regex in `src/cleaning.py` that safely mapped all notes into standardized categories (`NONE`, `Leave with security`, `Call before delivery`, `Office address, weekdays only`), ignoring extraneous text.

---

### 2. Standalone, Zero-CDN Web Decision Console
* **Built:** A complete single-page operational application served directly from FastAPI using pure vanilla HTML, modern CSS (Flexbox/Grid, `system-ui` fonts), and vanilla JavaScript.
* **Feature:** Operates 100% offline with zero external CDN dependencies (no Google Fonts, no external Tailwind/Bootstrap). Includes interactive presets (Low Risk Air Fryer, High Risk Vacuum COD, Walk-in No Address), segmented controls, skeleton loading shimmer, recent checks history, and copy response feature.

---

### 3. Model-Agnostic Feature Perturbation Explainability Engine
* **Built:** A lightweight, dependency-free reasons engine (`service/reasons.py`) that systematically perturbs order features against empirical baselines to calculate marginal risk contribution $\Delta p$, automatically generating plain-English guidance for customer service agents in <1 ms.

---

### 4. Input Safety Clamping with Operational Warnings
* **Built:** Automatic bounds clamping for numeric inputs outside training distribution (discount, quantity, delivery days, prior orders/returns, order value) with clear operational warnings returned by the API.

---

### 5. Right-Censoring Sensitivity & Stability Verification
* **Analysis:** Discovered the 19-day empirical return resolution lag and built an automated sensitivity test in `scripts/train.py` dropping the last 21 days of training data to prove model stability against reporting delays ($\Delta\text{AUC} = -0.0053$).
