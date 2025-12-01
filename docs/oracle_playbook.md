# Oracle CLI Playbook (WorldArchitect.AI)

Quick guide to use `@steipete/oracle` for this repo.

## Setup
- Install: `npm install -g @steipete/oracle` (or `npx -y @steipete/oracle --help`).
- Keys (API mode recommended): set `OPENAI_API_KEY` (optional `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`).
- Optional defaults: `~/.oracle/config.json`:
  ```json5
  { model: "gpt-5.1-pro", engine: "api", filesReport: true }
  ```

## Bundles (globs)
- Docs: `README.md,CLAUDE.md,CODE_REVIEW_SUMMARY.md`
- Backend: `mvp_site/*.py,mvp_site/schemas/**/*.py`
- AI hot path: `mvp_site/gemini_service.py,mvp_site/gemini_response.py,mvp_site/dual_pass_generator.py,mvp_site/robust_json_parser.py,mvp_site/game_state.py,mvp_site/entity_validator.py,mvp_site/narrative_response_schema.py,mvp_site/world_logic.py`
- MCP/API boundary: `mvp_site/main.py,mvp_site/world_logic.py,mvp_site/mcp_api.py,mvp_site/mcp_client.py`
- Frontend: `mvp_site/frontend_v1/**/*.js,mvp_site/frontend_v1/**/*.css,mvp_site/frontend_v1/**/*.html`
- Tests: `tests/**/*.py,test_integration/**/*.py`

## Common workflows
- Architecture review: include README + backend + frontend; preview with `--dry-run summary`.
- AI pipeline debug: prompt with the bug + `$MCP,$AI_CORE,$TESTS` (optionally `tmp/bug-report.md`).
- MCP/API contract check: attach gateway + schemas/templates.
- Frontend issues: attach campaign wizard JS/CSS/HTML + any UI notes.
- Test coverage gaps: compare `game_state.py`, `entity_validator.py` vs tests and ask for missing cases.
- Diff review: `git diff > /tmp/wa.patch` then `oracle --wait --write-output wa-review.md -p "Review this diff..." --file "$WA_DOCS,/tmp/wa.patch"`.
- Multi-model cross-check: `--models gpt-5.1-pro,claude-4.5-sonnet,gemini-3-pro` for security/consistency reviews.

## Operational tips
- Keep runs focused; always include `README.md` for high-level questions.
- Use `--files-report` to see token spend; `--wait` for long runs.
- Reuse sessions: `oracle status`, `oracle session <id> --render`.
- Keep `tmp/notes.md` and include it in `--file` for iterative debugging.

## Helpers
Source `scripts/oracle_helpers.sh` for ready-made bundles and commands:
```bash
source scripts/oracle_helpers.sh
oracle_arch_preview   # dry-run architecture review
oracle_arch           # architecture review (API/browser depending on config)
oracle_ai_debug       # AI pipeline debug (optional bug file path)
oracle_diff_review    # review current git diff -> wa-review.md
oracle_ui_debug       # frontend bug triage (optional note file)
```
