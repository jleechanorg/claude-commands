# Operational Assets, Documentation, and Configuration

> **Last updated:** 2025-10-16

This section inventories non-runtime assets inside `mvp_site/` that support
deployment, documentation, and developer workflows.

## Project Docs & Guides

| File | Purpose | Keep? |
| --- | --- | --- |
| `README.md`, `README_FOR_AI.md`, `PROMPTS_README.md`, `UNIFIED_API_IMPLEMENTATION.md`, `TYPING_GUIDE.md`, `CODE_REVIEW_SUMMARY.md` | Assorted human-facing docs explaining system goals, prompt strategy, API integration plans, and typing standards. | Keep as onboarding reference; migrate content to new docs site once rewrite lands. 【F:mvp_site/README.md†L1-L200】 |
| `CLAUDE.md` | Instructions for Claude-based agents working on this repo. | Keep only if AI-agent workflows remain relevant. |
| `roadmap/` | Feature plans and milestone tracking. | Keep as product history. |
| `docs/` | Deep dives such as `generalized_file_caching.md` and V1 vs V2 comparisons. | Keep for historical context when planning the rewrite. 【F:mvp_site/docs/generalized_file_caching.md†L1-L200】 |
| `analysis/` scripts | Capture and replay tools (`capture_llm_responses.py`, `run_sariel_replays.py`, etc.) used for real-world data gathering. | Keep if you still need to baseline Gemini behavior; otherwise port essential scripts to Node. 【F:mvp_site/analysis/run_sariel_replays.py†L1-L200】 |

## Configuration & Build Files

| File | Purpose | Keep? |
| --- | --- | --- |
| `Dockerfile` | Builds the Flask app with MCP tooling; serves as CI deployment artifact. | Replace with Node/TypeScript Dockerfile after rewrite, but keep until parity achieved. 【F:mvp_site/Dockerfile†L1-L200】 |
| `requirements.txt` | Python dependencies for the MVP backend. | Keep for reproducibility until the rewrite ships. |
| `package.json` / `package-lock.json` | Legacy Node dependencies (testing/UI). | Replace with new package manifest once TypeScript implementation exists. |
| `mypy.ini`, `pytest.ini` | Static typing and test configuration. | Keep until new stack defines equivalents. |
| `config/paths.py` | Centralizes filesystem paths used by scripts/tests. | Keep or port to TS config. 【F:mvp_site/config/paths.py†L1-L160】 |
| `monitor_doc_sizes.sh` | Utility script to monitor documentation footprint. | Optional; keep if doc-size enforcement remains. 【F:mvp_site/monitor_doc_sizes.sh†L1-L120】 |
| `run_integration_tests.sh` | Shell helper to execute integration suites. | Keep until new CI pipeline ready. |
| `start_flask.py` | Alternate Flask launcher referenced by UI tests. | Covered in backend docs; keep until migration completes. |

## Prompt Assets & Static Data

| File/Dir | Purpose | Keep? |
| --- | --- | --- |
| `prompts/*.md` | Prompt templates used by `llm_service`. Recreate verbatim in the new prompt system. 【F:mvp_site/prompts/master_directive.md†L1-L200】 |
| `world/` | JSON assets representing world content consumed by `world_loader`. | Keep; convert to JSON/TS modules. |
| `assets/DejaVuSans.ttf` | Font used for PDF exports. | Keep or replace with equivalent font in Node export pipeline. |
| `static/` | Contains V2 compiled assets (mirrors frontend_v2 build). | Keep until front-end pipeline is replaced. |
| `templates/base.html`, `templates/settings.html` | Flask-rendered templates for legacy pages. | Keep as reference when re-creating HTML shells. 【F:mvp_site/templates/base.html†L1-L160】 |
| `node_modules/`, `venv/` | Checked-in dependency directories (legacy artifact). | Remove from source control; rely on package managers instead. |

## Tooling & Licensing

| File | Purpose | Keep? |
| --- | --- | --- |
| `bin/LICENSE.chromedriver` | Bundled license for ChromeDriver used in UI tests. | Keep to satisfy licensing requirements. |
| `services/CLAUDE.md`, `config/CLAUDE.md` | Agent guidance for service modules. | Optional depending on future AI-agent workflows. |
| `test_documentation_performance.py` | Script ensuring documentation generation remains performant. | Keep as regression guard while docs evolve. 【F:mvp_site/test_documentation_performance.py†L1-L200】 |

These assets round out the operational knowledge necessary to port the MVP
to a new stack while maintaining deployment, documentation, and testing
capabilities.
