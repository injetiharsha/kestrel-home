# Prompt 01 — Phase P1: Data Audit

Read PLAN.md and AGENT_RULES.md first.

Your task is Phase P1: Data Audit.
1. Write a script `scripts/audit.py` to reproduce and verify the data facts outlined in Section 3 of PLAN.md.
2. Verify row counts, deduplication numbers (651 partner_feed rows), and the Oct 2025 order value inflation (x100).
3. Analyze the right-censoring lag (up to 19 days) and output the censoring check results.
4. Ensure all findings are output via code to a new file named `notes/data_audit.md`. Every number in this document must come directly from your code execution.
5. Save the exact text of this prompt to `prompts/01-data-audit.md`.

When finished: update notes/STATUS.md, run `python scripts/log.py note "Completed Phase P1 data audit"`, execute a git commit, and report back that the P1 gate is met.
