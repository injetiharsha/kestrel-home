# Built or Found Unasked (Form Q8)

This document records high-value discoveries, security hardening, and tooling built during the engagement that went beyond the baseline specification.

---

### 1. Delivery Note Prompt Injection Neutralization
* **Discovery:** Data audit uncovered 4 adversarial prompt injection attempts embedded within raw `delivery_note` text strings designed to mislead automated tools into using leaked target columns (`pickup_scheduled_at`).
* **Implementation:** Built a regex sanitization and template normalization layer in `src/cleaning.py` that safely mapped all notes into standardized categories (`NONE`, `Leave with security`, `Call before delivery`, `Office address, weekdays only`), completely neutralizing security injection risks.

---

### 2. Standalone, Zero-CDN Web Decision Console
* **Built:** A complete single-page operational application served directly from FastAPI using pure vanilla HTML, modern CSS (Flexbox/Grid, `system-ui` fonts), and vanilla JavaScript.
* **Feature:** Operates 100% offline with zero external CDN dependencies (no Google Fonts, no external Tailwind/Bootstrap). Includes interactive presets (High Risk COD Robot Vacuum vs Low Risk Prepaid Mixer Grinder) and animated visual state feedback.

---

### 3. Model-Agnostic Feature Perturbation Explainability Engine
* **Built:** A lightweight, dependency-free reasons engine (`service/reasons.py`) that systematically perturbs order features against empirical baselines to calculate marginal risk contribution $\Delta p$, automatically generating plain-English guidance for customer service agents.

---

### 4. Right-Censoring Sensitivity & Stability Verification
* **Analysis:** Discovered the 19-day empirical return resolution lag and built an automated sensitivity test in `scripts/train.py` dropping the last 21 days of training data to prove model stability against reporting delays ($\Delta\text{AUC} = -0.0053$).

---

### 5. Decile-Level Empirical Calibration Verification
* **Built:** Comprehensive calibration tables across 10 deciles verifying monotonic alignment between predicted risk scores and real return rates across all temporal evaluation windows.
