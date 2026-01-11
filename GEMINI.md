# Gemini Agent Protocol

## Output Location Rules
- **PR Descriptions:** When generating `PR_DESCRIPTION.md` or similar documentation, ALWAYS place it in the project's temporary directory (e.g., `.gemini/tmp/` or `/tmp/`) or a dedicated `tmp/` subdirectory within the project. NEVER place it in the project root to avoid accidental commits.
