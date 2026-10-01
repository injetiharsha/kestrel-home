# Prompt 06 — Phase P6: Evidence Documentation

Read PLAN.md and AGENT_RULES.md first.

Your task is Phase P6: Evidence documentation.
1. Finalize `validation/EVIDENCE.md`.
2. Document exactly how the model works and how often it fails.
3. Include failure analysis: where the model is wrong, specifically breaking down false negatives by family/payment/segment and false positives by Shield members.
4. Ensure every single metric and number matches the code outputs stored in `outputs/economics.json` and your validation logs.
5. Save the exact text of this prompt to `prompts/06-evidence-report.md`.

When finished: update notes/STATUS.md, run `python scripts/log.py note "Completed Phase P6 evidence report"`, execute a git commit, and report back that the P6 gate is met.
