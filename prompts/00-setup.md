# Prompt 00 — Phase P0: Skeleton and Setup

Read PLAN.md and AGENT_RULES.md first.

Your task is Phase P0: Skeleton and setup.
1. Create the exact repository structure detailed in Section 16 of PLAN.md, including all specified directories (data/, src/, service/, scripts/, tests/, validation/, outputs/, memo/, notes/, prompts/, .scratch/).
2. Create a `.gitignore` file that explicitly ignores `data/`, `.env`, `.scratch/`, `cache/`, `outputs/*.parquet`, `*.log`, `__pycache__/`, `.pytest_cache/`, and `.venv/`.
3. Extract the logging and agent rules from Section 17 of PLAN.md and save them verbatim to `AGENT_RULES.md`.
4. Write the `scripts/log.py` script to support the `note` and `ai` logging commands as specified in Section 17.
5. Initialize all the required markdown files in the `notes/` directory as empty or boilerplate files (`LOG.md`, `decisions.md`, `discarded.md`, `tradeoffs.md`, `known_issues.md`, `STATUS.md`, `expected_score.md`, `cost.md`, `extras.md`, `handoff.md`).
6. Save the exact text of this prompt to `prompts/00-setup.md`.

When finished: update notes/STATUS.md, run `python scripts/log.py note "Completed Phase P0 setup"`, execute a git commit, and report back that the P0 gate is met.
