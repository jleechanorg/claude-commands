# Backend Core Modules

> **Last updated:** 2025-10-16

This guide covers the primary runtime modules that accept HTTP requests,
translate them to MCP calls, apply world-logic orchestration, and emit
front-end compatible responses.

## `main.py`

| Public API | Responsibility | Keep? | Notes |
| --- | --- | --- | --- |
| `setup_file_logging()` | Configures branch-specific console/file logging via `logging_util`. | Keep | Required for consistent log routing and CI diagnostics. 【F:mvp_site/main.py†L130-L164】 |
| `safe_jsonify(data)` | Serializes payloads with the Firestore-aware JSON serializer before returning a Flask response. | Keep | Needed to sanitize Firestore sentinels and custom objects across all routes. 【F:mvp_site/main.py†L166-L178】 |
| `generic_error_response(operation, status_code)` | Returns a standardized JSON error tuple. | Keep | Used for fallback error handling in route wrappers. 【F:mvp_site/main.py†L181-L196】 |
| `create_app()` | Builds the Flask app, configures CORS/rate limits/auth middleware, initializes Firebase, lazily wires the MCP client, and registers every `/api/*` endpoint plus SPA asset fallbacks. | Keep | Central entrypoint; rewrite must reproduce auth flow, MCP calls, and route semantics. 【F:mvp_site/main.py†L199-L969】 |
| `run_test_command(command)` | Helper invoked from CLI to launch UI/HTTP smoke-test runners. | Keep (port to tooling script) | Provides developer ergonomics; convert to npm/yarn scripts in the TypeScript rewrite. 【F:mvp_site/main.py†L972-L1039】 |

*Route handlers inside `create_app()` remain the canonical contract for the TypeScript rewrite (campaign CRUD, interactions, settings, exports). Recreate these HTTP shapes exactly.*

## `start_flask.py`

Thin wrapper that imports `app` from `main.py` and exposes a CLI entry for
test harnesses. Keep until the new stack owns server startup. 【F:mvp_site/start_flask.py†L1-L18】

## `main_parallel_dual_pass.py`

Adds legacy experimental routes for a “parallel dual-pass” entity enhancement
flow. Public factory `add_parallel_dual_pass_routes(app, get_campaign_info)`
registers `/enhance-entities` and `/check-enhancement` endpoints that call
Gemini through `dual_pass_generator` utilities. The feature predates the MCP
refactor and is now deprecated—remove or re-implement only if dual-pass is in
scope for the rewrite. 【F:mvp_site/main_parallel_dual_pass.py†L1-L76】

## MCP Bridge

| File | Public API | Responsibility | Keep? |
| --- | --- | --- | --- |
| `mcp_client.py` | `MCPClient`, `MCPClientError`, `http_to_mcp_request`, `mcp_to_http_response`, `handle_mcp_errors`, `create_mcp_client`, `example_usage` | Handles JSON-RPC transport to the MCP server or direct calls into `world_logic` when `skip_http` is enabled. Provides HTTP↔MCP translation helpers and rich error mapping. Essential for mirroring request flows in the new stack. | Keep core client; port translation logic to TypeScript service layer. 【F:mvp_site/mcp_client.py†L1-L420】 |
| `mcp_api.py` | `handle_list_tools`, `handle_call_tool`, `_create_*` tool factories, `handle_list_resources`, `handle_read_resource`, `setup_mcp_logging`, `run_server` | Exposes `world_logic` as an MCP-compatible server (tool registration, resource handlers). Only needed if you continue running a Python MCP sidecar; otherwise migrate semantics into the TypeScript backend. | Keep during transition; reassess once TypeScript service replaces MCP bridge. 【F:mvp_site/mcp_api.py†L1-L420】 |
| `memory_mcp_real.py` | `MemoryMCPInterface`, `search_nodes`, `create_entities` | Real MCP integration for long-term memory graph operations. Wraps asynchronous MCP calls with structured responses. | Keep if long-term memory stays external; otherwise stub in TypeScript. 【F:mvp_site/memory_mcp_real.py†L1-L200】 |
| `mcp_memory_real.py` | `MCPMemoryClient`, `search_nodes`, `open_nodes`, `read_graph`, `initialize_mcp_functions`, `set_mcp_functions` | Legacy direct MCP Graph API integration used by experiments. Consider migrating functionality into the new stack or deprecating if not in use. 【F:mvp_site/mcp_memory_real.py†L1-L220】 |
| `memory_integration.py` | `MemoryIntegration`, `MemoryMetrics`, `enhance_slash_command` | Higher-level orchestration of narrative memory injection combining MCP and Gemini responses. | Keep if narrative memory is a product requirement; otherwise archive. 【F:mvp_site/memory_integration.py†L1-L260】 |

## World Logic & Game Flow

| File | Public API | Responsibility | Keep? |
| --- | --- | --- | --- |
| `world_logic.py` | `create_campaign_unified`, `process_action_unified`, `get_campaign_state_unified`, `update_campaign_unified`, `export_campaign_unified`, `get_campaigns_for_user_list`, `get_campaigns_list_unified`, `create_error_response`, `create_success_response`, `apply_automatic_combat_cleanup`, `format_game_state_updates`, `parse_set_command` + debug helpers | Central orchestration layer implementing campaign CRUD, action processing, export formatting, structured-field handling, and debug commands. Coordinates Firestore persistence, Gemini prompts, and narrative sanitization. | Keep – this is the business brain. Port logic carefully or split between TypeScript services and dedicated AI workers. 【F:mvp_site/world_logic.py†L235-L940】【F:mvp_site/world_logic.py†L851-L1310】 |
| `world_loader.py` | `load_banned_names`, `load_world_content_for_system_instruction` | Loads static content assets (banned names, world templates) for prompt construction. | Keep; convert to TypeScript data-loading utilities. 【F:mvp_site/world_loader.py†L1-L200】 |
| `game_state.py` | `GameState` dataclass | Canonical campaign state structure with serialization helpers; feeds prompt construction and persistence. | Keep; replicate shape in TypeScript models. 【F:mvp_site/game_state.py†L1-L200】 |
| `document_generator.py` | `get_story_text_from_context`, `generate_pdf`, `generate_docx`, `generate_txt` | Export routines that stitch story entries and render PDF/DOCX/TXT downloads. | Keep functionality; re-implement using Node tooling (e.g., pdf-lib/docx). 【F:mvp_site/document_generator.py†L1-L220】 |
| `debug_mode_parser.py` | `DebugModeParser` | Parses and applies debug console commands for power users. | Keep if debug console remains; otherwise drop. 【F:mvp_site/debug_mode_parser.py†L1-L200】 |

## Legacy/Support Modules

| File | Public API | Responsibility | Keep? |
| --- | --- | --- | --- |
| `inspect_sdk.py` | `_load_api_key()` | Utility for loading Gemini API keys in CLI tooling. | Optional; replace with Node environment manager. 【F:mvp_site/inspect_sdk.py†L1-L80】 |
| `unified_api_examples.py` | *(no public functions)* | Example payloads kept for documentation. | Archive inside docs; not needed in runtime. |
| `__init__.py` | Package marker | Keeps `mvp_site` importable as a package. | Keep until repository restructuring. |
| `start_flask.py` | CLI entrypoint for Flask server | Already covered above. | Keep until new server exists. |

> See [`ai_and_persistence.md`](ai_and_persistence.md) for Gemini, Firestore,
> entity, and schema modules that underpin the world logic functions referenced
> here.
