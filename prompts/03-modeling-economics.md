# Prompt 03 — Phase P3: Baselines, Modeling, and Economics

Read PLAN.md and AGENT_RULES.md first.

Your task is Phase P3: Baselines, modeling, and economics.
1. Implement DummyClassifier (prior), LogisticRegression (primary), and HistGradientBoostingClassifier (challenger) in `src/`.
2. Set up rolling time folds based on `order_placed_at` as defined in Section 9. Do not use random splits.
3. Run ablation and sensitivity tests (e.g., with/without `customer_prior_*`, Shield vs non-Shield).
4. Implement the economics method exactly as defined in Section 6: Rs 45 cost per call, Rs 1150 return cost, 35% prevention benefit. Decide on Assumption A1 (margin lost per cancelled held order) and document it.
5. Generate performance metrics (AUC, PR-AUC, bootstrap CI, rupee net per 700 orders) and save a structured JSON to `outputs/economics.json`. Write a draft of `validation/EVIDENCE.md` based on these runs.
6. Save the exact text of this prompt to `prompts/03-modeling-economics.md`.

When finished: update notes/STATUS.md, run `python scripts/log.py note "Completed Phase P3 modeling and economics"`, execute a git commit, and report back that the P3 gate is met.
