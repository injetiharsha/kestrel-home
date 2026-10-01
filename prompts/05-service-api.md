# Prompt 05 — Phase P5: Service API and Highly Polished Web Screen

Read PLAN.md and AGENT_RULES.md first.

Your task is Phase P5: Service API and Highly Polished Web Screen.
1. If focusing on a more sophisticated UI design requires extra time or alters your step-by-step approach, add a brief entry to the Change Log in Section 0 of PLAN.md first.
2. Build a FastAPI application in `service/` with `POST /predict`, `GET /health`, and `GET /` (serving a single static HTML page).
3. **Frontend Design (Highly Polished):** Create a professional-grade, beautiful user interface using strictly vanilla JS, HTML, and custom CSS. **Do NOT use external CDNs or libraries (no external Tailwind, Bootstrap, or Google Fonts)**. Achieve a polished, modern look by implementing:
    *   **Typography & Layout:** Use the `system-ui` font stack for a crisp, modern feel. Use CSS Flexbox/Grid to center the application and align form fields beautifully.
    *   **Form UI:** Design elegant form controls (dropdowns for all order fields as specified in Section 11) with soft borders, rounded corners, subtle box-shadows, and clear active/focus states.
    *   **UX/Interactivity:** Implement a loading state (e.g., CSS spinner or button state change) while the `/predict` endpoint is being called.
    *   **Results Dashboard:** Render the API response in a visually distinct results card. Use color-coded visual indicators for the risk band (e.g., Green for low risk, Yellow for medium, Red for high risk) and clean formatting for the "recommended action" and "top 3 reasons". 
    *   **Error Handling:** Ensure polite, well-styled UI error messages if bad input is submitted (handling 422 errors gracefully).
4. The `/predict` endpoint must take a JSON order, return a score (0 to 1), risk band, recommended action, and top 3 reasons in plain text.
5. Implement the reasons engine using model-agnostic feature perturbation as specified in Section 7.
6. Ensure the service uses no API keys, and can be started cleanly from `requirements.txt` on a fresh machine.
7. Add tests in `tests/` to verify the endpoint works.
8. Save the exact text of this prompt to `prompts/05-service-api.md`.

When finished: update notes/STATUS.md, run `python scripts/log.py note "Completed Phase P5 service API with highly polished frontend"`, execute a git commit, and report back that the P5 gate is met.
