# Repository Guidelines

## Project Structure & Module Organization
- `mvp_site/`: Python 3.11 backend (Flask, MCP tooling), tests, templates, and static assets. Frontends live in `mvp_site/frontend_v1/` and `mvp_site/frontend_v2/`.
- `mvp_site/tests/` and `mvp_site/test_integration/`: Unit and integration tests. Additional top‑level tests exist in `tests/`.
- `scripts/` and top‑level `run_*.sh`: Development, CI, and utility commands.
- `.claude/` and related folders: Agent orchestration commands and docs.
- `docs/`, `roadmap/`, `world/`: Documentation, plans, and content assets.

## Build, Test, and Development Commands
- `./vpython mvp_site/main.py serve`: Run the API locally (auto‑starts MCP in typical workflows). Alt: `./run_local_server.sh`.
- `./run_tests.sh [--full|--integration|--coverage]`: Run Python tests (intelligent selection by default). Use `--integration` for external‑dep tests.
- `./run_tests_with_coverage.sh`: Generate coverage; HTML output under `/tmp/worldarchitectai/coverage/`.
- `./run_ui_tests.sh`: Execute UI/browser tests where applicable.
- `./run_lint.sh` or `pre-commit run -a`: Lint/format (Ruff, isort, Prettier, ESLint). First‑time: `pre-commit install`.

## Coding Style & Naming Conventions
- Python: 4‑space indent, 88‑char lines, double quotes. Lint/format via Ruff; imports via isort; typing with mypy; security scan via bandit (configured in `pyproject.toml`).
- JavaScript/CSS in `mvp_site/static/`: Prettier (2‑space tabs, single quotes) and ESLint.
- Naming: `snake_case` for files/functions, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants. Tests named `test_*.py`.

## Testing Guidelines
- Frameworks: Standard unittest/pytest‑style tests run through `run_tests.sh` (parallel by default). Integration tests live in `mvp_site/test_integration/` and are opt‑in (`--integration`).
- Environment: Default `TEST_MODE=mock`; real integrations may require credentials.
- Conventions: Place feature tests near code in `mvp_site/tests/`; prefer small, deterministic tests. Use `--coverage` before merging substantive changes.

## Commit & Pull Request Guidelines
- Commits: Imperative mood with optional scope, e.g., `Context Optimization: Reduce token usage` (see `git log`).
- PRs: Clear description, linked issues, screenshots for UI changes, and a test plan (e.g., commands run: `./run_tests.sh --full --coverage`). Ensure CI passes and lint is clean.

## Security & Configuration Tips
- Never commit secrets. Copy `.env.example` to `.env` and populate locally.
- Firebase `serviceAccountKey.json` and `GEMINI_API_KEY` must be set as documented in `README.md`.
- Prefer local mocks for tests; guard credentials with environment variables.

## Agent‑Specific Notes
- Prefer edits under `mvp_site/` and existing scripts. Follow formatting via `pre-commit` before proposing changes. See `.claude/`, `CLAUDE.md`, and `QWEN.md` for orchestration conventions.
