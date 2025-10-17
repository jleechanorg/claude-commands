# Utility Modules Cheat Sheet

> **Last updated:** 2025-10-16

This quick reference lists cross-cutting helpers that appear throughout the
MVP codebase. Full detail lives in [`ai_and_persistence.md`](ai_and_persistence.md),
but this sheet groups them by responsibility so you can quickly locate the
relevant Python file when porting functionality.

## JSON & Error Recovery

- `json_utils.py` – Low-level helpers for counting braces/quotes, unescaping
  strings, and safely parsing partial JSON. 【F:mvp_site/json_utils.py†L1-L220】
- `robust_json_parser.py` – Orchestrates layered fallback strategies when Gemini
  returns malformed JSON. 【F:mvp_site/robust_json_parser.py†L1-L300】
- `debug_json_response.py` – Fixes truncated payloads and extracts planning
  blocks for troubleshooting. 【F:mvp_site/debug_json_response.py†L1-L200】

## Logging & Diagnostics

- `logging_util.py` – Centralized logger setup used by Flask, services, and
  tests. 【F:mvp_site/logging_util.py†L1-L220】
- `decorators.py` – `log_exceptions` decorator for consistent error reporting in
  async/sync contexts. 【F:mvp_site/decorators.py†L1-L80】
- `debug_hybrid_system.py` – Cleans narrative debug tags before display. 【F:mvp_site/debug_hybrid_system.py†L1-L220】
- `token_utils.py` – Token counting utilities to monitor prompt size. 【F:mvp_site/token_utils.py†L1-L160】

## Prompt & Entity Helpers

- `prompt_utils.py` – Shared logic for assembling campaign prompt blocks. 【F:mvp_site/prompt_utils.py†L1-L200】
- `entity_utils.py` – Filtering helpers for unknown entities. 【F:mvp_site/entity_utils.py†L1-L120】
- `numeric_field_converter.py` – Safely coerces numeric state updates. 【F:mvp_site/numeric_field_converter.py†L1-L160】

## Debugging Scripts

- `debug_mode_parser.py` – Parses slash/debug commands for game masters. 【F:mvp_site/debug_mode_parser.py†L1-L200】
- `debug_hybrid_system.py` – Standalone cleaner that strips hybrid-debug tags from captured transcripts before sharing with testers. 【F:mvp_site/debug_hybrid_system.py†L1-L220】
- `inspect_sdk.py` – Minimal helper to load Gemini keys when running CLI tools. 【F:mvp_site/inspect_sdk.py†L1-L80】

Keep these utilities handy: they represent the guardrails (logging, JSON
sanity, prompt sanitation) that must exist in the TypeScript rewrite to achieve
behavioral parity.
