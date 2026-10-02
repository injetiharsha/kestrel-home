# Phase P5b Prompt — Service UI Polish

Read PLAN.md and AGENT_RULES.md first.

Phase P5 revision: fix clean-machine bugs in the service, then rebuild the web screen to a much higher polish.
Do NOT overwrite prompts/05-service-api.md (keep history). Save this prompt to prompts/05b-service-ui-polish.md.

STEP 0 - PLAN.md first (rule 10)
Add a Change Log entry in Section 0: "P5 revision: (a) service no longer reads data/ at runtime; product catalog and state list shipped as service/catalog.json; (b) UI rebuilt; (c) tests that need data skip cleanly; (d) test-client dependency added to requirements." Also add to Section 14: "K16 service/catalog.json contains 21 product rows (sku, family, list price, warranty, launch date) copied from products.csv; judged low sensitivity (public catalog); customers.csv is NOT shipped." Update Section 11 (service spec) to mention the state field, catalog.json and CSP header.

PART A - clean-machine fixes
1. Create scripts/build_catalog.py. It reads data/products.csv and the fitted model's state categories (from the OneHotEncoder inside outputs/model_lr.joblib), writes service/catalog.json containing: products array (sku, family, list_price_inr, warranty_months, launch_date), states array, and all categorical categories the model expects.
2. Rewrite service/app.py so it never reads data/ at runtime. It loads outputs/model_lr.joblib and service/catalog.json only. Unknown SKU returns 422 (not silent fallback). CSP middleware added. GET /catalog endpoint added.
3. Rewrite tests/test_service.py: add test_catalog_endpoint, test_csp_header_present, test_predict_unknown_sku_422 (expects 422). Remove data-dependent customer_id tests.
4. Add httpx>=0.27.0 to requirements.txt (FastAPI TestClient dependency).

PART B - UI rebuild
1. Single-file service/static/index.html. Vanilla HTML + CSS + JS, no CDN. system-ui font stack.
2. Dark + light theme toggle (localStorage persistence, prefers-color-scheme default).
3. API-driven dropdowns from GET /catalog (SKU grouped by family, states from model).
4. SVG semicircle gauge with animated fill, color-coded by risk band.
5. Glassmorphism card surfaces, sticky header, responsive grid.
6. WCAG AA: all interactive elements keyboard-accessible, sufficient contrast ratios.

PART C - Tests and verification
Run pytest. All 26 tests (blacklist + service) must pass.
Verify uvicorn starts and serves the UI.

When finished: update notes/STATUS.md, run `python scripts/log.py note "Completed Phase P5b service revision"`, execute a git commit, and report back.
