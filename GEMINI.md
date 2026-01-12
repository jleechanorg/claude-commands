# Gemini Agent Protocol

## Output Location Rules
- **PR Descriptions:** When generating `PR_DESCRIPTION.md` or similar documentation, ALWAYS place it in the project's temporary directory (e.g., `.gemini/tmp/` or `/tmp/`) or a dedicated `tmp/` subdirectory within the project. NEVER place it in the project root to avoid accidental commits.

## GitHub CLI (gh) - Protocol

- **Mandatory Tool**: Use `gh` for **ALL** GitHub tasks (PRs, issues, checks, releases). Do not rely on git alone.
- **Strict Verification**: **NEVER** guess branch names. Always verify `headRefName` via `gh pr view <number> --json headRefName` before checkout.
- **Formatting**: Always use **HEREDOCs** (e.g., `$(cat <<'EOF' ... EOF)`) when passing multi-line bodies to `gh pr create` to ensure correct formatting.
- **Fallback**: If `gh` is missing in restricted environments (e.g., containers), download the precompiled binary from GitHub releases to `/tmp` to bypass package manager restrictions.
