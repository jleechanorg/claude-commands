# Core Application Code Breakdown

_Last updated: 2025-10-02_

To reproduce the numbers below from the repository root:

```bash
./loc_simple.sh
```

Example output from the current run (captured 2025-10-02):

```text
  Core Application    :  29994 lines (py:22342 js:6347 html:1305)
```

`loc_simple.sh` attributes **29,994 production lines** to the Core Application bucket across `mvp_site/` (22,342 Python, 6,347 JavaScript, 1,305 HTML). The table below reconciles those totals with the major runtime areas inside the package.

> **Note:** The broader `./codebase_loc.sh` script counts every language (TypeScript, docs, generated assets, etc.) and currently reports ~602,581 LOC. That wider scope explains why the project-wide figure is higher than the Core Application total documented here.

## Production LOC composition (Python/JavaScript/HTML only)

| Area | Production LOC | Representative modules | What the code does |
| --- | --- | --- | --- |
| API gateway & MCP bridge | 3,084 | [`main.py`](../mvp_site/main.py), [`mcp_api.py`](../mvp_site/mcp_api.py), [`mcp_client.py`](../mvp_site/mcp_client.py), [`start_flask.py`](../mvp_site/start_flask.py), [`main_parallel_dual_pass.py`](../mvp_site/main_parallel_dual_pass.py), [`unified_api_examples.py`](../mvp_site/unified_api_examples.py), [`inspect_sdk.py`](../mvp_site/inspect_sdk.py) | Flask exposes REST endpoints and forwards everything to the MCP tool server while keeping HTTP responses compatible for both front-ends. |
| Gameplay orchestration | 2,089 | [`world_logic.py`](../mvp_site/world_logic.py), [`document_generator.py`](../mvp_site/document_generator.py), [`prompt_utils.py`](../mvp_site/prompt_utils.py), [`dual_pass_generator.py`](../mvp_site/dual_pass_generator.py), [`world_loader.py`](../mvp_site/world_loader.py) | Central mission flow loads player state, prepares prompts, and renders exports/pitches used by the GM workflow. |
| AI generation pipeline | 3,904 | [`gemini_service.py`](../mvp_site/gemini_service.py), [`gemini_request.py`](../mvp_site/gemini_request.py), [`gemini_response.py`](../mvp_site/gemini_response.py), [`robust_json_parser.py`](../mvp_site/robust_json_parser.py), [`token_utils.py`](../mvp_site/token_utils.py) | Manages Gemini request orchestration, retries, JSON parsing, and token budgeting for story beats and narrator text. |
| Entity & narrative validation | 3,772 | [`entity_validator.py`](../mvp_site/entity_validator.py), [`entity_preloader.py`](../mvp_site/entity_preloader.py), [`entity_instructions.py`](../mvp_site/entity_instructions.py), [`entity_tracking.py`](../mvp_site/entity_tracking.py), [`entity_utils.py`](../mvp_site/entity_utils.py), [`narrative_response_schema.py`](../mvp_site/narrative_response_schema.py), [`narrative_sync_validator.py`](../mvp_site/narrative_sync_validator.py), [`schemas/`](../mvp_site/schemas/), [`structured_fields_utils.py`](../mvp_site/structured_fields_utils.py), [`custom_types.py`](../mvp_site/custom_types.py), [`config/paths.py`](../mvp_site/config/paths.py), [`constants.py`](../mvp_site/constants.py) | Guards campaign state by validating characters, stats, and narrative events before they reach persistence or the UI. |
| Persistence & memory services | 2,938 | [`firestore_service.py`](../mvp_site/firestore_service.py), [`game_state.py`](../mvp_site/game_state.py), [`numeric_field_converter.py`](../mvp_site/numeric_field_converter.py), [`file_cache.py`](../mvp_site/file_cache.py), [`json_utils.py`](../mvp_site/json_utils.py), [`memory_integration.py`](../mvp_site/memory_integration.py), [`memory_mcp_real.py`](../mvp_site/memory_mcp_real.py), [`mcp_memory_real.py`](../mvp_site/mcp_memory_real.py) | Wraps Firestore access, enforces numeric hygiene, and syncs long-lived MCP memory stores used for dual-pass narration. |
| Diagnostics & developer tooling | 1,949 | [`analysis/`](../mvp_site/analysis/), [`debug_hybrid_system.py`](../mvp_site/debug_hybrid_system.py), [`debug_json_response.py`](../mvp_site/debug_json_response.py), [`debug_mode_parser.py`](../mvp_site/debug_mode_parser.py), [`logging_util.py`](../mvp_site/logging_util.py), [`decorators.py`](../mvp_site/decorators.py), [`__init__.py`](../mvp_site/__init__.py) | Capture scripts, logging helpers, and debug parsers that exercise Gemini and MCP flows during development. |
| Mocks & capture harnesses | 1,557 | [`mocks/`](../mvp_site/mocks/) | Drop-in Firestore and Gemini fakes plus fixture packs that power local capture sessions. |
| Testing framework & capture CLI | 3,049 | [`testing_framework/`](../mvp_site/testing_framework/), [`testing_ui/`](../mvp_site/testing_ui/) | Python harnesses that drive MCP capture sessions, validate example migrations, and ship the reusable factories that power integration fixtures. |
| Front-end presentation (.js/.html counted) | 7,652 | [`frontend_v1/`](../mvp_site/frontend_v1/), [`frontend_v2/`](../mvp_site/frontend_v2/), [`templates/`](../mvp_site/templates/), [`static/`](../mvp_site/static/) | Legacy JS client, shared HTML templates, Tailwind configuration, and hosted static fallbacks that ship with the Flask server. |

These categories together sum to the 29,994-line Core Application total (`3,084 + 2,089 + 3,904 + 3,772 + 2,938 + 1,949 + 1,557 + 3,049 + 7,652 = 29,994`).

### Why the script total looks smaller than the full project footprint

`loc_simple.sh` only counts `.py`, `.js`, and `.html` files. The React application under `mvp_site/frontend_v2/src/` is TypeScript-first, contributing another ~16K lines that are **not** part of the Core Application bucket reported by the script but are still required to ship the product UI. Together the shipped clients (legacy JS plus React build artifacts) cover roughly ~27.6K production lines, so the table intentionally focuses on the `.js/.html` subset that `loc_simple.sh` measures while this paragraph calls out the missing TypeScript surface.

## Architectural highlights

- **Thin HTTP layer.** [`main.py`](../mvp_site/main.py) exposes authenticated REST endpoints and defers all gameplay to the MCP server, keeping the Flask tier stateless and easily replaceable.
- **Tool-based gameplay.** [`mcp_api.py`](../mvp_site/mcp_api.py) wraps the orchestrator in MCP tools so automation and front-ends can reuse the same command surface without copying business logic.
- **Defensive data handling.** [`entity_validator.py`](../mvp_site/entity_validator.py) and [`firestore_service.py`](../mvp_site/firestore_service.py) guard against malformed AI output before it reaches persistence or the client.
- **Story generation pipeline.** [`gemini_service.py`](../mvp_site/gemini_service.py) coordinates prompt construction, retries, and response parsing to keep the GM experience consistent.
- **Legacy + modern UIs.** The shipped Flask app still serves the legacy JS interface alongside the newer React build, which is why `.js/.html` files still occupy a sizable share of the counted Core Application LOC.
