# WorldArchitect.AI MVP Site Deep Dive

> **Last updated:** 2025-10-16

This documentation set maps the current Python/Flask MVP codebase so it can be
reimplemented in a modern TypeScript stack with functional parity. Start here
for a top-level understanding, then follow the linked deep-dive guides for
detailed module inventories and API responsibilities.

## System Overview

The MVP application is a Flask API gateway that authenticates users with
Firebase, proxies gameplay requests to a Model Context Protocol (MCP) server,
and serves the legacy front-end bundles. Game logic and content generation live
in `world_logic.py` (MCP server shim) and Gemini integrations. The system is
tightly coupled to Google Firestore for campaign persistence and to Gemini for
AI narrative generation. 【F:mvp_site/main.py†L3-L520】【F:mvp_site/world_logic.py†L1-L420】

Primary runtime flow:

1. **HTTP ingress (`main.py`)** – Flask routes authenticate with Firebase,
   assemble request payloads, and invoke MCP tools via `MCPClient`. Static
   assets are served from `frontend_v1` with fallbacks for historical paths.
2. **MCP client (`mcp_client.py`)** – Translates HTTP payloads to MCP tool
   calls. In local mode it bypasses HTTP and calls `world_logic` functions
   directly; otherwise it issues JSON-RPC HTTP calls to an MCP server.
3. **World logic (`world_logic.py`)** – Implements gameplay workflows such as
   campaign creation, state updates, structured response formatting, and
   setting management. It orchestrates Gemini prompts, Firestore storage, and
   debugging utilities.
4. **AI integrations** – `llm_service.py` builds prompts, selects models,
   validates structured responses, and emits timeline entries. Memory and
   instruction helpers coordinate the narrative context across passes.
5. **Persistence** – `firestore_service.py` encapsulates Firestore access with
   mock-friendly abstractions and mission/story helpers. Game state and user
   settings flow through `GameState` models, numeric converters, and entity
   validators.
6. **Front-end** – Legacy `frontend_v1` static assets and modern `frontend_v2`
   Vite/React TypeScript code consume the same JSON API. Front-end tests ensure
   parity between versions.

## How to Use These Notes

The remaining documents provide file-by-file breakdowns, including public APIs,
responsibilities, and keep/remove recommendations.

- [`backend_core.md`](backend_core.md) – Flask entrypoints, MCP plumbing, world
  logic, and document generation.
- [`ai_and_persistence.md`](ai_and_persistence.md) – Gemini services,
  Firestore access, memory integrations, schemas, and entity tooling.
- [`utilities.md`](utilities.md) – Cross-cutting helpers (JSON parsing,
  logging, tokens, debugging, prompts, numeric converters).
- [`frontends_and_assets.md`](frontends_and_assets.md) – Legacy and modern
  front-end bundles, static assets, templates, and exported docs.
- [`testing.md`](testing.md) – Custom testing framework, mock providers,
  regression suites, and UI/end-to-end coverage.
- [`operations_and_docs.md`](operations_and_docs.md) – Supporting docs,
  scripts, configuration files, and project metadata inside `mvp_site/`.

Each guide lists every file within its scope, summarizes public-facing
functions/classes, and flags obsolete artifacts. Together they describe the
system interfaces needed to rebuild the application in TypeScript (e.g., API
routes, request/response formats, data models, and long-running processes).
> Last updated: 2025-10-08

This deep dive documents every asset in `mvp_site/` so a new engineer can rebuild the product (for example in TypeScript) without
opening the existing source. Use this index to jump to the detailed write-ups that were generated for every file and public API.

## How to Read These Notes

1. Start with the [Directory Overview](directories_overview.md) to understand which sub-systems live where and which folders are
   disposable (for example vendored `node_modules/` trees and virtual environments).
2. Explore the auto-generated module references (`*_python.md`) for the Python backend. Every file lists its module-level
   responsibility, public functions/classes, and the recommendation on whether it should be kept.
3. Review the frontend inventories ([frontend_v1_overview.md](frontend_v1_overview.md) and
   [frontend_v2_src.md](frontend_v2_src.md)) to see which screens, hooks, and utility modules currently exist.
4. Inspect supporting assets:
   - [templates_overview.md](templates_overview.md) for Flask Jinja templates
   - [static_overview.md](static_overview.md) for statically served frontend bundles
   - [prompts_overview.md](prompts_overview.md) and [world_assets.md](world_assets.md) for content consumed by the AI layer
5. For non-Python root files (Dockerfile, READMEs, integration docs, etc.) use
   [root_non_python.md](root_non_python.md).

## System Architecture Summary

WorldArchitect.AI uses a **thin Flask API gateway** (`main.py`) that authenticates with Firebase, applies rate limiting, serves
static assets, and proxies every meaningful game operation to the internal **MCP tool server** (`world_logic.py`).

- **MCP Client & Error Handling**: `mcp_client.py`, `mcp_api.py`, and decorators orchestrate requests to the world logic server,
  applying standardized retry/error handling (`handle_mcp_errors`).
- **Business Logic**: `world_logic.py` implements the unified campaign API used by both Flask and MCP servers. Supporting modules
  (`entity_*`, `narrative_*`, `memory_*`, `prompt_utils`, `dual_pass_generator`, etc.) assemble prompts, validate data, and
  transform AI output.
- **Content & Configuration**: `prompts/` contains structured instructions, `world/` holds world bible content, and
  `schemas/` defines Pydantic models guaranteeing shape consistency.
- **Frontends**: `frontend_v1/` is the legacy static bundle, while `frontend_v2/` is a modern React + Vite codebase (with
  committed build outputs under `static/v2`). Both depend on the Flask routes for data.
- **Testing & Tooling**: `tests/`, `testing_framework/`, and `testing_ui/` provide API, regression, UI, and architectural
  validation suites.

## Key Data Flows

1. **Campaign lifecycle**: Frontend calls `/api/campaigns*` → Flask authenticates & forwards to `world_logic` via `MCPClient` →
   `world_logic` orchestrates prompt generation, Gemini interactions, entity validation, and Firestore persistence.
2. **Memory & Entity tracking**: Campaign state updates flow through `entity_tracking`, `entity_validator`, and memory modules to
   guarantee consistent world state.
3. **Narrative generation**: `dual_pass_generator` and `narrative_sync_validator` construct Gemini prompts, parse structured
   responses, and ensure narrative + mechanics coherence.
4. **World content loading**: `world_loader` composes world bible files and banned-name lists, with `file_cache` providing reuse.
5. **Testing harness**: `testing_framework` gives scenario scaffolding, while `tests/` enforces architectural contracts and
   regression coverage across API, prompts, and frontend builds.

## Guidance for a TypeScript Rebuild

- Mirror the Flask HTTP surface exactly; consult `main.py` and `world_logic.py` to replicate request/response schemas. The
  docstrings in [root_python.md](root_python.md) and [tests_python.md](tests_python.md) enumerate every route and contract.
- Re-implement backend integrations (Firebase auth, MCP client, Gemini prompts) using the module responsibilities documented in
  `*_python.md`. Each function bullet explains why it exists, what it expects, and whether it must be preserved.
- Port content verbatim: prompts, world assets, and structured schemas should be treated as canonical data files.
- Replicate UI behavior by tracing components/hooks listed in the frontend inventories. Pay special attention to how `frontend_v2`
  stores state (Zustand stores under `src/stores`) and how API calls are shaped (`src/services`).
- Keep the testing strategy: reproduce key tests highlighted in [tests_python.md](tests_python.md) and UI automation under
  `testing_ui/` to confirm parity in the TypeScript rewrite.

## Removal Candidates

- Vendored dependencies under `mvp_site/node_modules/` and `mvp_site/frontend_v2/node_modules/` should be deleted and restored
  via package managers. The deep dive flags these directories as removable.
- The committed Python `venv/` should also be removed.

## Next Steps

1. Walk through each linked markdown for deeper per-file detail.
2. Extract data models and API shapes into a TypeScript interface catalog.
3. Implement the new TypeScript service/frontend, leaning on these docs to maintain feature parity.

