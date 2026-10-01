# Prompt 04 — Phase P4: Expected Score Lock-in and Final Predictions

Read PLAN.md and AGENT_RULES.md first.

Your task is Phase P4: Expected score lock-in and final predictions.
1. Read `outputs/economics.json`. Write `notes/expected_score.md` detailing the expected metric, range, and drift caveat as specified in Section 10.
2. **CRITICAL:** Git commit `notes/expected_score.md` immediately with a timestamp before proceeding to the final fit.
3. Train the final LogisticRegression model on ALL deduped training data. Do not tune hyperparameters on this final run.
4. Generate `outputs/predictions.csv` for the 2,096 test rows. Format strictly: `order_id,score`, no NaNs, no duplicates, order matching `sample_submission.csv`.
5. Save the final model artifact (joblib) to `outputs/`.
6. Save the exact text of this prompt to `prompts/04-expected-score.md`.

When finished: update notes/STATUS.md, run `python scripts/log.py note "Completed Phase P4 final fit and predictions"`, execute a git commit, and report back that the P4 gate is met.
