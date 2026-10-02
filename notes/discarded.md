# Discarded Hypotheses & Explored Approaches (Form Q9)

This document catalogs approaches, features, and model concepts that were explored and subsequently discarded during the project.

---

### 1. Tree Classifiers (HistGradientBoosting)
* **What was tried:** Evaluated `HistGradientBoostingClassifier` pipeline against Logistic Regression in `src/models.py`.
* **Why discarded:** In temporal backtests on Fold 3, HistGBT achieved AUC 0.7546 and PR-AUC 0.3633, lagging behind regularized Logistic Regression (AUC 0.7728, PR-AUC 0.3949). The tree model showed signs of overfitting to categorical noise on the 10.5k dataset.

---

### 2. Random K-Fold Splitting
* **What was tried:** Considered standard random K-fold cross-validation.
* **Why discarded:** Violates chronological causality in time-series order data. Replaced with rolling-origin time-based folds strictly ordered by `order_placed_at`.

---

### 3. Dispatch Hold Policy
* **What was tried:** Simulated Ritu's original proposal of pausing/holding flagged orders.
* **Why discarded:** Economic simulation revealed that a 12% cancellation rate on held orders destroys gross margin on legitimate orders, resulting in a net loss of **-₹43,722/month** (at 15% margin). Discarded in favor of pre-dispatch confirmation calls (+₹10,785/month).

---

### 4. Raw Free-Text Embeddings from Delivery Notes
* **What was tried:** Considered tokenizing and embedding raw `delivery_note` free-text strings.
* **Why discarded:** Data audit confirmed raw text contains noise and unstructured variations that add negligible signal over normalized structural templates (`NONE`, `Call on delivery`, `Leave with security`, `Office address`).

---

### 5. Order Timing Features (hour, weekday) - tested, NOT removed
* Ablation (outputs/economics.json): dropping them changes AUC by +0.0002 (0.7728 to 0.7730). Negligible.
* They stay in the final model because I did not retrain after the expected score and predictions were locked. A cleaner model would drop them, plus delivery_note_template and pincode_prefix (dropping either gave AUC about 0.777).
