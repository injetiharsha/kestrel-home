# Prompt 02 — Phase P2: Cleaning, Features, and Blacklist Testing

Read PLAN.md and AGENT_RULES.md first.

Your task is Phase P2: Cleaning, features, and blacklist testing.
1. Implement data cleaning in the `src/` folder: Deduplicate by `order_id` (keeping `source == crm`), divide Oct 2025 values > 5x expected by 100, and read `pincode` as a string (flagging 000000 as `no_address`).
2. Implement feature engineering based strictly on Section 8 of PLAN.md.
3. Write a pytest in the `tests/` folder to strictly enforce the blacklist rule: ensure `returned`, `last_service_event_type`, `pickup_scheduled_at`, `source`, `order_id`, `customer_id`, `signup_date`, order month/year, and raw `delivery_note` text are never used as features.
4. Run the test, ensure it passes, and save the resulting clean dataframe to a gitignored path (e.g., `.scratch/clean_train.parquet`).
5. Save the exact text of this prompt to `prompts/02-cleaning-features.md`.

When finished: update notes/STATUS.md, run `python scripts/log.py note "Completed Phase P2 cleaning and features"`, execute a git commit, and report back that the P2 gate is met.
