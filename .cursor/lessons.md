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