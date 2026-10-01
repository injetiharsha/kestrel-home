# Discarded Hypotheses & Explored Approaches (Form Q9)

This document catalogs approaches, features, and model concepts that were explored and subsequently discarded during the project.

---

### 1. Complex Tree Classifiers (HistGradientBoosting / XGBoost)
* **What was tried:** Tuned `HistGradientBoostingClassifier` across max depth, min samples leaf, and learning rates.
* **Why discarded:** In temporal backtests on Fold 3, HistGBT achieved AUC 0.7546 and PR-AUC 0.3633, lagging behind regularized Logistic Regression (AUC 0.7728, PR-AUC 0.3949). The tree model overfit to high-cardinality noise in the 10.5k dataset.

---

### 2. Random K-Fold Cross-Validation Splitting
* **What was tried:** Tested standard 5-fold stratified random splitting on `train.csv`.
* **Why discarded:** Produced unrealistically high AUC scores (0.83+), masking severe temporal leakage of customer repeat behavior across time. Replaced with rolling-origin time-based folds strictly ordered by `order_placed_at`.

---

### 3. Dispatch Hold Policy
* **What was tried:** Simulated Ritu's original proposal of pausing/holding flagged orders.
* **Why discarded:** Economic simulation revealed that a 12% cancellation rate on held orders destroys gross margin on legitimate orders, resulting in a net loss of **-₹43,722/month** (at 15% margin). Discarded in favor of pre-dispatch confirmation calls (+₹10,785/month).

---

### 4. Raw Free-Text Embeddings from Delivery Notes
* **What was tried:** Considered tokenizing and embedding raw `delivery_note` text strings.
* **Why discarded:** Discovered adversarial prompt injection strings in raw notes. Furthermore, feature ablation confirmed raw text adds negligible signal over simple structural templates (`NONE`, `Call on delivery`, `Leave with security`, `Office address`).

---

### 5. Order Timing Features (`hour`, `weekday`)
* **What was tried:** Extracted purchase hour of day and day of week.
* **Why discarded:** Ablation study showed $\Delta\text{AUC} = +0.0002$ when dropped. Order placement hour is largely noise in appliance D2C purchasing.
