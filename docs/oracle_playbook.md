# Oracle CLI Playbook

Use these helpers after sourcing `scripts/oracle_helpers.sh`:

- `oracle_arch_preview` – dry-run bundle preview for architecture reviews.
- `oracle_arch` – architecture review with browser engine defaults.
- `oracle_ai_debug [note.md]` – AI pipeline bug triage; optional note path.
- `oracle_diff_review` – review current git diff.
- `oracle_ui_debug [note.md]` – frontend triage with optional note path.

Tips:
- Ensure `oracle` CLI is installed and on PATH.
- Set `ORACLE_ENGINE`, `ORACLE_DEFAULT_GLOBS`, and `ORACLE_DEFAULT_EXCLUDES` to control scope.
- Use `--dry-run summary` to inspect bundles before sending.
