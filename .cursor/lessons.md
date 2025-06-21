# Lessons Learned & Best Practices

This document is a persistent repository for reusable knowledge, best practices, and crucial insights.

### Git & Repository
- **Lesson:** Before proposing changes, always review the cumulative diff against the merge-base of the target branch (`origin/main`) to verify the changes are accurate and safe.
- **Command:** `git diff $(git merge-base origin/main HEAD) HEAD`

### Python & Virtual Environments
- **Lesson:** Due to PEP 668, `pip install` into a system Python environment marked "externally managed" will be blocked. Python packages must always be installed into an activated virtual environment (`venv`).
- **Lesson:** On some Linux systems, the `python3-venv` package must be installed via the system package manager (e.g., `apt`, `yum`) before Python's `venv` module can be used.
- **Action:** Always verify the `venv` is active before running `pip install` or any Python scripts.

### Backend & Data
- **Lesson (Robust Data Handling):** Application code must be resilient to data variations. This includes handling API limits by truncating data and gracefully managing different data schemas (e.g., "old" vs. "new" documents in Firestore) within the application logic itself.
- **Lesson (Professional Practices):** Use the `logging` module over `print()` for server-side debugging. For Flask, use the Application Factory pattern to structure the app.
- **Lesson (Flask SPA Routing):** For a Flask backend serving a Single Page Application (SPA), a catch-all route must be implemented to serve the main `index.html` for all non-API paths, enabling client-side routing.
- **Action:** Ensure a ` @app.route('/<path:path>')` or similar route exists to serve the SPA's entry point.

### Frontend Development
- **Lesson:** Browsers aggressively cache static assets like CSS and JavaScript. During development, after making changes to these files, it is crucial to restart the development server and perform a hard refresh (e.g., Ctrl+Shift+R or Cmd+Shift+R) to ensure the latest versions are loaded.
- **Action:** After any change in the `static` folder, restart the server and hard refresh the browser.

### Testing
- **Lesson (Test Fidelity):** Unit and integration tests must accurately reflect the real-world conditions of the application. Mocking should be used carefully and must not bypass the exact functionality being tested (e.g., file system access).

### Shell & Automation Scripts
- **Lesson (Robust Scripting):** Workflow scripts (e.g., `fupdate.sh`, `deploy.sh`) must be context-aware (work correctly from any subdirectory) and idempotent. They should handle optional arguments and have sane defaults. Parent directories should always be created with `mkdir -p`.
- **Lesson (Shell Config):** Changes made to shell configuration files (e.g., `.bashrc`, `.zshrc`) are not applied to the current terminal session. The configuration must be reloaded.
- **Action:** After editing a shell config file, run `source ~/.bashrc` (or the equivalent for your shell) or open a new terminal session.

### AI Collaboration
- **Lesson:** Detailed, explicit, and well-structured system prompts and user instructions significantly improve AI performance and consistency. Iterative refinement is key.
- **Action:** Continue to refine `rules.md` and provide clear, specific instructions for tasks.

### Tooling & Environment Notes
- **Lesson (Linter vs. Dynamic Libraries):** Static analysis tools (linters) may fail to correctly parse attributes of dynamic libraries like `firebase-admin`. For example, the linter may incorrectly flag `firestore.Query.DESCENDING` as an `AttributeError`, but it is correct at runtime.
- **Action:** In cases of conflict, trust validated, working code over the linter's warning. The correct, tested usage is `firestore.Query.DESCENDING`.

*   **Root Cause:** Failure to explicitly sanitize data for serialization. The `json` library cannot handle Python `datetime` objects by default.
*   **Lesson:** Always pass data destined for JSON serialization through a handler that can manage common non-serializable types like `datetime`.

*   **Incident:** Multiple failed attempts to call the Gemini API, resulting in "non-text response" errors and linter failures.
*   **Root Cause:** Using outdated patterns from the legacy `google-generativeai` Python SDK instead of the current `google-genai` SDK. The API signature for client initialization and content generation changed significantly.
*   **Lesson:** The project uses the modern `google-genai` SDK. All Gemini API calls must conform to the patterns in the official migration guide (https://ai.google.dev/gemini-api/docs/migrate). Specifically, use `genai.Client()` for initialization and `client.models.generate_content()` for requests, not `genai.GenerativeModel()`.

*   **Incident:** Application crashed with a `404 Not Found` error when checking a new campaign for legacy data.
*   **Root Cause:** A function (`update_campaign_game_state`) used the Firestore `.update()` method, which fails if the target document does not exist. The code path for a "new campaign with no legacy data" tried to update a document that had not yet been created.
*   **Lesson:** Functions that modify database records should be designed to be idempotent or act as an "upsert" (update or insert) when there's a possibility of acting on a non-existent resource. For Firestore, this means preferring `.set(data, merge=True)` over `.update(data)` in such cases. 