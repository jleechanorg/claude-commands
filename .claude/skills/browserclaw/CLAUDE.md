# CLAUDE.md

## Repo intent

`browserclaw` captures browser traffic with Playwright and turns that traffic into developer-facing artifacts. Keep the tool honest:

- Manual auth only
- No stealth, evasion, or auth bypass features
- Prefer deterministic generation over fragile scraping heuristics
- Keep generated outputs reviewable by humans

## Development rules

- Run `PYTHONPATH=src pytest -q` before pushing
- Keep generated code templates simple and auditable
- If a provider integration cannot be validated locally, document that clearly in the PR

