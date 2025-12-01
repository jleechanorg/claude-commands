# Fallback Behavior Review (mvp_site)

This document inventories fallback logic in `mvp_site/`, explains the rationale for each case, and flags spots where the behavior may hide configuration/setup errors the user wants surfaced.

## Runtime/server code

- **Frontend routing fallback in `main.py`**: The `serve_frontend` route serves `index.html` when the requested path does not match a static asset, which is the standard Single Page App pattern so the client router can handle deep links. The adjacent `/handle_interaction` handler returns a 410 with an explicit refresh instruction for users on stale cached bundles; it intentionally avoids accepting the request to force clients to upgrade. This fallback is justified because it protects existing users from hitting a dead endpoint while still failing the legacy call path.

- **MCP memory client in `mcp_memory_real.py`**: `_get_mcp_function` resolves MCP functions from globals and initialization now fails fast if any required handler is missing. Public methods validate that function pointers are non-None before invocation and raise `MCPMemoryError` if unavailable. The `set_functions()` helper requires all three MCP functions to be provided together for dependency injection; partial injection is rejected to avoid inconsistent states. This strict behavior surfaces configuration errors immediately rather than masking them with fallbacks.

- **Narrative parsing fallbacks in `narrative_response_schema.py`**: Multiple layers of fallback construct a `NarrativeResponse` even when the LLM returns malformed or partially structured JSON—extracting known fields, regex-parsing narrative text, and cleaning JSON-like strings. These are justified because upstream LLM responses are nondeterministic and user-facing flows need to render something readable rather than crash; the fallbacks do not hide configuration errors but handle untrusted model output.

- **Game state reconstruction in `world_logic.py`**: When `GameState.from_dict` unexpectedly returns `None` after applying GOD_MODE updates, the code now logs an error and returns an HTTP 500 error response with message "Unable to reconstruct game state after applying changes." This fail-fast behavior prevents silent data corruption and surfaces deserialization failures immediately.

- **Document ID handling in `firestore_service.py`**: During story writes, if Firestore does not return a document reference with an `id`, the code raises a `FirestoreWriteError`. If document_id is None after a successful write, a `FirestoreWriteError` is raised with message "Document ID was not captured during write. This indicates an unexpected error in the Firestore write operation." This fail-fast approach ensures write anomalies are surfaced rather than masked with fallback values.

## Tests and mocks

- **Testing framework fallbacks (`testing_framework/` tests and README)**: These files include fallback implementations and assertions to ensure the test harness degrades gracefully when integration utilities are unavailable. Because they run only in the test suite and explicitly report when fallbacks are used, they do not affect runtime behavior.

- **LLM/model fallback tests (`llm_service.py` references)**: The test suites and documentation cite fallback model cycling to validate resilience to upstream model errors; the logic under test is about external provider instability, not local configuration.

- **Mock wrappers (`mocks/mock_llm_service_wrapper.py`, `mocks/mock_firestore_service_wrapper.py`)**: These wrappers now use direct imports (`from mvp_site import logging_util`) instead of fallback import chains. Missing dependencies will cause immediate import failures, ensuring test environment configuration errors are surfaced rather than masked.

- **Frontend test fallbacks (`frontend_v2/src/utils/errorHandling.ts` and related tests/components)**: Frontend utility functions accept `fallbackMessage` to render user-friendly errors instead of crashing the UI. These are UX-level fallbacks for runtime errors in the browser, not configuration masking on the server.

## Key takeaways

- User-facing robustness to unpredictable LLM output (narrative parsing) and stale cached frontend bundles is justified.
- Fallbacks that previously hid missing services or imports have been removed in favor of fail-fast behavior with explicit error messages.
- The MCP memory client now uses `MCPMemoryError` for clear error propagation.
- Firestore write operations fail fast with `FirestoreWriteError` if document IDs cannot be captured.
- Game state reconstruction errors now return HTTP 500 instead of silently substituting empty state.
