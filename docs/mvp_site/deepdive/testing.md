# Testing & Quality Infrastructure

> **Last updated:** 2025-10-16

The MVP repository includes a rich suite of custom testing utilities plus
hundreds of regression tests spanning unit, integration, UI, and MCP workflows.

## Custom Testing Framework (`testing_framework/`)

| Module | Public API | Purpose | Keep? |
| --- | --- | --- | --- |
| `config.py` | `TestConfig` | Centralizes environment toggles (mock vs real services). | Keep. 【F:mvp_site/testing_framework/config.py†L1-L200】 |
| `factory.py` | `get_service_provider`, `set_service_provider`, `reset_global_provider` | Manages the active service provider (mock vs real). | Keep. 【F:mvp_site/testing_framework/factory.py†L1-L200】 |
| `service_provider.py` | `TestServiceProvider` | Base provider abstraction used by tests. | Keep. 【F:mvp_site/testing_framework/service_provider.py†L1-L160】 |
| `mock_provider.py` | `MockServiceProvider` | Supplies Firestore/Gemini mocks. | Keep. 【F:mvp_site/testing_framework/mock_provider.py†L1-L200】 |
| `real_provider.py` | `RealServiceProvider` | Bridges to production services when permitted. | Keep but guard behind env flags. 【F:mvp_site/testing_framework/real_provider.py†L1-L200】 |
| `fixtures.py` | `service_provider`, `firestore_client`, `gemini_client`, `auth_service`, `test_mode`, `IsolatedTestCase` | Pytest fixtures/base classes for dual-mode testing. | Keep. 【F:mvp_site/testing_framework/fixtures.py†L1-L340】 |
| `integration_utils.py` | `dual_mode_test`, `MockCompatibilityMixin`, `smart_patch`, `validate_test_environment` | Shared helpers for toggling between mock/real integrations. | Keep. 【F:mvp_site/testing_framework/integration_utils.py†L1-L360】 |
| `capture.py` | `CaptureManager`, `CaptureFirestoreClient`, `CaptureGeminiClient`, `load_capture_data`, `cleanup_old_captures` | Records real API traffic for replay testing. | Keep. 【F:mvp_site/testing_framework/capture.py†L1-L360】 |
| `capture_cli.py` | `analyze_command`, `compare_command`, `baseline_command`, `cleanup_command`, `list_command`, `main` | CLI wrapper for capture tooling. | Keep. 【F:mvp_site/testing_framework/capture_cli.py†L1-L260】 |
| `capture_analysis.py` | `CaptureAnalyzer`, `create_mock_baseline` | Analyzes captured sessions. | Keep. 【F:mvp_site/testing_framework/capture_analysis.py†L1-L200】 |
| `pytest_integration.py` | `test_mode`, `service_provider`, `requires_real_services`, etc. | Registers fixtures and markers with pytest. | Keep. 【F:mvp_site/testing_framework/pytest_integration.py†L1-L360】 |
| `simple_mock_provider.py` | `SimpleMockFirestore`, `SimpleMockGemini`, etc. | Lightweight mocks for smoke tests. | Keep. 【F:mvp_site/testing_framework/simple_mock_provider.py†L1-L260】 |
| `migration_examples.py` | `TraditionalCharacterTestBefore`, `ModernCharacterTestAfter`, etc. | Shows before/after patterns for migrating tests. | Keep for documentation. 【F:mvp_site/testing_framework/migration_examples.py†L1-L260】 |

Supporting tests under `testing_framework/tests/` ensure the framework’s own
components behave correctly (factory switching, capture flows, etc.). 【F:mvp_site/testing_framework/tests/test_factory.py†L1-L200】

## Python Unit & Integration Tests (`tests/`)

The `tests/` directory contains themed regression suites. When porting to
TypeScript, treat these as specifications. Highlights by category (each bullet
lists the relevant files):

- **API & Flask integration** – `test_api_routes.py`, `test_settings_api.py`,
  `test_flask_app_import.py`, `test_main_enhancements.py`, `test_mcp_health.py`,
  `test_api_backward_compatibility.py`. Validate HTTP routes, auth guards, and
  MCP plumbing. 【F:mvp_site/tests/test_api_routes.py†L1-L220】【F:mvp_site/tests/test_main_enhancements.py†L1-L320】
- **World logic & game state** – `test_world_logic.py`, `test_world_loader.py`,
  `test_world_loader_e2e.py`, `test_game_state.py`, `test_main_state_helper.py`,
  `test_apply_automatic_combat_cleanup` (via `test_combat_cleanup_comprehensive.py`).
  Ensure campaign prompts, exports, and combat cleanup behave. 【F:mvp_site/tests/test_world_logic.py†L1-L360】
- **Structured fields & JSON safety** – `test_structured_fields_utils.py`,
  `test_structured_response_extraction.py`, `test_json_utils.py`,
  `test_debug_json_response.py`, `test_robust_json_parser.py`,
  `test_json_cleanup_safety.py`, `test_extra_json_fields.py`,
  `test_json_only_comprehensive.py`. Provide reference for JSON post-processing.
  【F:mvp_site/tests/test_structured_fields_utils.py†L1-L200】
- **Gemini interaction** – `test_gemini_request_validation.py`,
  `test_gemini_response.py`, `test_gemini_response_structured_fields.py`,
  `test_gemini_token_management.py`, `test_generator_isolated.py`,
  `test_dual_pass_generator.py`, `test_planning_block_validation_integration.py`.
  Document prompt validation and dual-pass heuristics. 【F:mvp_site/tests/test_dual_pass_generator.py†L1-L320】
- **Entity tooling** – `test_entity_validator.py`, `test_entity_instructions.py`,
  `test_entity_tracking.py`, `test_entity_preloader.py`, `test_entity_utils.py`,
  `test_unknown_entity_filtering.py`. Cover enforcement logic for entity coverage.
  【F:mvp_site/tests/test_entity_validator.py†L1-L360】
- **Firestore & persistence** – `test_firestore_structured_fields.py`,
  `test_firestore_mission_handler.py`, `test_firestore_empty_narrative_bug_redgreen.py`,
  `test_firestore_database_errors.py`, `test_fake_firestore.py`,
  `test_fake_services.py`, `test_fake_services_simple.py`. Validate Firestore
  adapters and mission handling. 【F:mvp_site/tests/test_firestore_mission_handler.py†L1-L220】
- **Narrative & gameplay regressions** – `test_narrative_cutoff_bug.py`,
  `test_null_narrative_bug_fix.py`, `test_npc_gender_consistency_red_green.py`,
  `test_character_extraction_regex_bug.py`, `test_time_pressure.py`,
  `test_animation_system.py`. Provide guardrails for previously fixed bugs.
  【F:mvp_site/tests/test_narrative_cutoff_bug.py†L1-L160】
- **End-to-end flows** – `test_end2end/` suite (campaign creation, continue
  story, MCP protocol error handling) plus `tests/frontend_v2/` and
  `tests/wizard/` targeted flows. 【F:mvp_site/tests/test_end2end/test_create_campaign_end2end.py†L1-L200】
- **Auth & security** – `tests/auth/test_auth_resilience.py`,
  `test_subprocess_security.py`, `test_architectural_boundary_validation.py`. Ensure
  sandboxing and credential boundaries remain intact. 【F:mvp_site/tests/auth/test_auth_resilience.py†L1-L200】
- **Performance & docs** – `test_documentation_performance.py`,
  `test_performance_config.py`, `test_memory_leak_fixes_verification.py`.
  Guard against regressions in documentation and runtime performance.

Consult the remaining `test_*.py` files for niche edge cases (banned names,
mission conversions, JSON mode toggles, etc.); each title reflects the scenario
it locks down. All should remain until equivalent TypeScript tests replace
them.

## UI & Browser Tests (`testing_ui/`)

Playwright/Selenium-style scripts exercise the React UI against mock or real
APIs (`test_mobile_responsive.py`, `test_ui_with_api_campaign.py`,
`test_v2_campaign_display_logic.py`, etc.). They rely on `testing_ui/run_all_browser_tests.py`
invoked through `main.run_test_command`. Keep until the new front-end test suite
is established. 【F:mvp_site/testing_ui/test_ui_with_api_campaign.py†L1-L200】

## MCP & Integration Suites

- `tests/mcp_tests/` validates MCP interoperability with Cerebras and the local
  server. 【F:mvp_site/tests/mcp_tests/test_mcp_comprehensive.py†L1-L200】
- `tests/integration/` includes browser-based settings/game integrations that hit
  real services when credentials are present. 【F:mvp_site/tests/integration/test_real_browser_settings_game_integration.py†L1-L200】

By treating these tests as executable documentation, the TypeScript rewrite can
match every behavior guaranteed by the Python suite.
