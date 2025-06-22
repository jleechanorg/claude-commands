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

*   **Incident:** Application crashed with `ModuleNotFoundError: No module named 'mvp_site'`.
*   **Root Cause:** Using an absolute import (`from mvp_site import constants`) in a script that was being run directly from within the `mvp_site` subdirectory. This execution context prevents Python from recognizing `mvp_site` as a package in its search path.
*   **Lesson:** When a Python script is intended to be run directly (e.g., `python my_script.py`), any imports of other modules within the same directory must be relative (e.g., `import my_module`), not absolute from a parent directory that isn't a recognized package in the current execution context.
*   **Action:** When working on scripts inside a subdirectory of the project, use relative imports for local modules.

*   **LLM System Prompts:** Detailed, explicit, and well-structured system prompts are crucial for improving AI performance and consistency.
*   **Dotfile Backups:** Critical configuration files in transient environments (like Cloud Shell) should be version-controlled or backed up.
*   **Safe File Edits:** To avoid accidental deletions or unwanted changes, I must treat file edits like a formal code review. I will first determine the exact `diff` I intend to create. After using my tools to generate the change, I will compare the actual result to my intended `diff`. If they do not match perfectly, I will stop, report the discrepancy, and re-plan the edit instead of proceeding with a faulty change. This ensures that I am always performing surgical and additive changes, never destructive ones.

## VII. 5 Whys Analysis Log

*This section will be used to document the root cause analysis of any significant failures.*

*   **Root Cause:** Failure to explicitly sanitize data for serialization. The `json` library cannot handle Python `datetime` objects by default.
*   **Lesson:** Always pass data destined for JSON serialization through a handler that can manage common non-serializable types like `datetime`.

*   **Incident:** Multiple failed attempts to call the Gemini API, resulting in "non-text response" errors and linter failures.
*   **Root Cause:** Using outdated patterns from the legacy `google-generativeai` Python SDK instead of the current `google-genai` SDK. The API signature for client initialization and content generation changed significantly.
*   **Lesson:** The project uses the modern `google-genai` SDK. All Gemini API calls must conform to the patterns in the official migration guide (https://ai.google.dev/gemini-api/docs/migrate). Specifically, use `genai.Client()` for initialization and `client.models.generate_content()` for requests, not `genai.GenerativeModel()`.

*   **Incident:** Application crashed with a `404 Not Found` error when checking a new campaign for legacy data.
*   **Root Cause:** A function (`update_campaign_game_state`) used the Firestore `.update()` method, which fails if the target document does not exist. The code path for a "new campaign with no legacy data" tried to update a document that had not yet been created.
*   **Lesson:** Functions that modify database records should be designed to be idempotent or act as an "upsert" (update or insert) when there's a possibility of acting on a non-existent resource. For Firestore, this means preferring `.set(data, merge=True)` over `.update(data)` in such cases.

*   **Incident:** Application crashed with `ModuleNotFoundError: No module named 'mvp_site'`.
*   **Root Cause:** Using an absolute import (`from mvp_site import constants`) in a script that was being run directly from within the `mvp_site` subdirectory. This execution context prevents Python from recognizing `mvp_site` as a package in its search path.
*   **Lesson:** When a Python script is intended to be run directly (e.g., `python my_script.py`), any imports of other modules within the same directory must be relative (e.g., `import my_module`), not absolute from a parent directory that isn't a recognized package in the current execution context.
*   **Action:** When working on scripts inside a subdirectory of the project, use relative imports for local modules.

*   **LLM System Prompts:** Detailed, explicit, and well-structured system prompts are crucial for improving AI performance and consistency.
*   **Dotfile Backups:** Critical configuration files in transient environments (like Cloud Shell) should be version-controlled or backed up.
*   **Workspace-Specific Rules:** Always check for a `.cursor/rules.md` file at the start of any interaction. If it exists, its contents supersede any general operating instructions. This file is the definitive source of truth for project-specific protocols.

---
## State Management & Data Integrity (June 2025)

### Lesson: State updates require a deep, recursive merge.
*   **Problem:** The initial state update logic used a shallow merge (`dict.update()`), which caused nested objects and lists (like `core_memories`) to be completely overwritten instead of updated.
*   **Solution:** Implement a recursive `deep_merge` function (renamed to `update_state_with_changes`) that traverses the entire state dictionary, merging nested objects and intelligently handling list appends.

### Lesson: Code must be resilient to schema evolution.
*   **Problem:** The application crashed when loading older campaign documents that were missing newer fields like `created_at`.
*   **Solution:** Both the Python backend and the JavaScript frontend must use defensive data access patterns.
    *   **Backend (Python):** Use the `dict.get('key', default_value)` method to safely access keys that may not exist.
    *   **Frontend (JavaScript):** Use ternary operators (`campaign.last_played ? ... : 'N/A'`) or optional chaining (`campaign?.last_played`) to handle potentially `undefined` properties.

### Lesson: The data source path is the ultimate source of truth.
*   **Problem:** The most elusive bug was that state changes were not persisting. The root cause was that the application was reading the game state from one Firestore document (`.../game_states/current_state`) but writing updates to a different one (`.../campaigns/{id}`).
*   **Solution:** When debugging persistence issues, the first step is to log and verify that the read path and write path for a given resource are identical.

## AI Interaction & Prompt Engineering (June 2025)

### Lesson: AI instructions must be clear, consistent, and unambiguous.
*   **Problem:** The AI began generating malformed JSON for state updates.
*   **Solution:** An audit of the `game_state_instruction.md` prompt file revealed conflicting examples—one section encouraged dot-notation while another mandated nested objects. The solution was to enforce a single, clear standard (nested objects) and remove all contradictory instructions and examples.

### Lesson: Enforce critical logic with code-level safeguards, not just prompts.
*   **Problem:** Despite prompt improvements, the AI would occasionally attempt to overwrite the `core_memories` list, which would risk data loss.
*   **Solution:** Instead of endlessly refining the prompt, a "smart safeguard" was added to the `update_state_with_changes` function. This code intercepts any direct assignment to `core_memories`, intelligently extracts the new items, and safely appends them, making the system resilient to AI errors by default.

## Lesson: Architecting Robust File Downloads

**Problem:** A file download feature was failing in multiple, confusing ways: truncated filenames, mangled Unicode characters, and failed requests. The root cause was a combination of backend header issues and incomplete frontend logic.

**Solution:** A robust file download requires a clear separation of concerns between the backend and frontend.

### Backend Responsibilities (e.g., Flask)

1.  **Decouple Filesystem Name from Download Name:** The filename on the server's disk should be temporary and safe. A UUID is ideal (`uuid.uuid4().ext`). The user-facing filename should be derived from the data's title and sent separately.
2.  **Use `send_file` Correctly:** The standard `send_file(path, download_name="user_facing_name.ext", as_attachment=True)` is the correct tool. It handles setting the `Content-Disposition` header.
3.  **Clean Up Temporary Files:** The backend is responsible for generating the temporary file and must clean it up. Using Flask's `@response.call_on_close` decorator is a reliable way to remove the file after the download stream is finished.

### Frontend Responsibilities (e.g., JavaScript `fetch`)

1.  **Initiate Download and Expect a Header:** The frontend code initiates the `fetch` request to the download endpoint.
2.  **Read `Content-Disposition`:** It is not enough to just get the file data (the "blob"). The JavaScript **must** read the `Content-Disposition` header from the response.
3.  **Extract the Filename:** The script must parse the `Content-Disposition` header to extract the `filename=` value. This is the source of truth for the downloaded file's name.
4.  **Assemble the Download Link:** The script creates a blob URL from the response data (`URL.createObjectURL(blob)`), creates a temporary `<a>` element, sets its `href` to the blob URL, and critically, sets its `download` attribute to the filename extracted from the header.
5.  **Include Authentication:** If the backend endpoint is protected, the frontend `fetch` call must include the necessary authorization token in its headers.

By strictly adhering to this pattern, the backend has full control over the final filename, and the frontend correctly respects it, preventing truncation and other errors. 