# AI, Persistence, and Entity Tooling

> **Last updated:** 2025-10-16

These modules encapsulate Gemini prompt/response handling, Firestore
persistence, structured schemas, and entity enforcement utilities that sit
under `world_logic.py`.

## Gemini Integration

| File | Public API | Responsibility | Keep? |
| --- | --- | --- | --- |
| `gemini_request.py` | `GeminiRequest`, `json_default_serializer`, `GeminiRequestError`, `PayloadTooLargeError`, `ValidationError` | Pydantic-style request wrapper that validates payload size and schema before sending prompts to Gemini. | Keep – port validation and error taxonomy to the TypeScript client. 【F:mvp_site/gemini_request.py†L1-L220】 |
| `gemini_response.py` | `GeminiResponse` | Structured wrapper around Gemini responses with helpers to extract state updates and narrative text. | Keep – replicate interface to keep downstream consumers unchanged. 【F:mvp_site/gemini_response.py†L1-L220】 |
| `gemini_service.py` | `PromptBuilder`, `get_initial_story`, `continue_story` | Builds multi-part prompts (system, world, timeline), enforces model selection, validates structured responses, and logs token usage before returning a `GeminiResponse`. | Keep core flow; TypeScript implementation should reuse prompt templates and validation steps. 【F:mvp_site/gemini_service.py†L1-L1180】 |
| `dual_pass_generator.py` | `GenerationPass`, `DualPassResult`, `DualPassGenerator`, `AdaptiveEntityInjector` | Implements two-pass narrative generation (baseline + entity injection) with heuristics for missing entity coverage. | Keep if dual-pass remains a product requirement; otherwise mark optional. 【F:mvp_site/dual_pass_generator.py†L1-L540】 |
| `entity_instructions.py` | `EntityInstruction`, `EntityInstructionGenerator`, `EntityEnforcementChecker` | Generates structured entity directives for Gemini prompts and validates coverage against game state. | Keep – drives structured responses. 【F:mvp_site/entity_instructions.py†L1-L360】 |
| `entity_preloader.py` | `EntityPreloader`, `LocationEntityEnforcer` | Preloads entity metadata from Firestore/story context to inform prompts. | Keep. 【F:mvp_site/entity_preloader.py†L1-L260】 |
| `entity_tracking.py` | `create_from_game_state`, `get_validation_info` | Builds tracking payloads that ensure Gemini outputs contain required entities. | Keep. 【F:mvp_site/entity_tracking.py†L1-L220】 |
| `entity_validator.py` | `EntityPresenceType`, `ValidationResult`, `EntityValidator`, `EntityRetryManager` | Validates and retries Gemini responses when entities are missing or inconsistent. | Keep – essential guardrail. 【F:mvp_site/entity_validator.py†L1-L420】 |
| `narrative_response_schema.py` | `NarrativeResponse`, `EntityTrackingInstruction`, `parse_structured_response`, `create_generic_json_instruction`, `create_structured_prompt_injection`, `validate_entity_coverage` | Defines the canonical structured JSON schema returned by Gemini and helper factories for injection prompts. | Keep. 【F:mvp_site/narrative_response_schema.py†L1-L360】 |
| `narrative_sync_validator.py` | `EntityPresenceType`, `EntityContext`, `ValidationResult`, `NarrativeSyncValidator` | Cross-checks narrative text against tracked entities to prevent desync. | Keep. 【F:mvp_site/narrative_sync_validator.py†L1-L320】 |
| `structured_fields_utils.py` | `extract_structured_fields` | Extracts structured sections from Gemini responses before storage. | Keep. 【F:mvp_site/structured_fields_utils.py†L1-L160】 |
| `prompt_utils.py` | `_build_campaign_prompt_impl` (private) exposed through `world_logic`; no public exports. | Keep internally for prompt templating, but fold into new prompt builder design. 【F:mvp_site/prompt_utils.py†L1-L200】 |
| `numeric_field_converter.py` | `NumericFieldConverter` | Cleans and normalizes numeric fields in state updates. | Keep – ensures data integrity. 【F:mvp_site/numeric_field_converter.py†L1-L200】 |
| `schemas/defensive_numeric_converter.py` | `DefensiveNumericConverter` | Strict conversion utilities for schema validation. | Keep as reference for stricter validation in TypeScript. 【F:mvp_site/schemas/defensive_numeric_converter.py†L1-L200】 |
| `schemas/entities_pydantic.py` | `EntityType`, `Character`, `NPC`, `SceneManifest`, etc. | Canonical entity data models and factory `create_from_game_state`. | Keep – port models to TypeScript interfaces/types. 【F:mvp_site/schemas/entities_pydantic.py†L1-L360】 |

## Firestore Persistence & Mission Handling

| File | Public API | Responsibility | Keep? |
| --- | --- | --- | --- |
| `firestore_service.py` | `MissionHandler`, `update_state_with_changes`, `json_default_serializer`, `get_db`, `get_campaigns_for_user`, `get_campaign_by_id`, `add_story_entry`, `create_campaign`, `get_campaign_game_state`, `update_campaign_game_state`, `update_campaign`, `get_user_settings`, `update_user_settings`, etc. | Encapsulates all Firestore reads/writes, mock-mode shims, mission/story utilities, and JSON serialization fallbacks. | Keep – critical for persistence; TypeScript rewrite must reproduce API contract (campaigns collection layout, mission updates). 【F:mvp_site/firestore_service.py†L1-L680】 |
| `file_cache.py` | `read_file_cached`, `clear_file_cache`, `get_cache_stats`, `invalidate_file` | Simple filesystem cache to avoid re-reading static assets. | Keep optional; a TypeScript implementation could rely on in-memory caches. 【F:mvp_site/file_cache.py†L1-L200】 |
| `memory_integration.py` | (see MCP Bridge table) | Bridges Firestore data with memory MCP. | Keep if memory stays. |

## Custom Types & Shared Contracts

| File | Public API | Responsibility | Keep? |
| --- | --- | --- | --- |
| `custom_types.py` | `CampaignData`, `StateUpdate`, `EntityData`, `MissionData`, `ApiResponse`, `GeminiRequest`, `GeminiResponse`, `DatabaseService`, `AIService` | Typed dictionaries/protocols defining how services communicate. | Keep – convert to TypeScript type aliases/interfaces. 【F:mvp_site/custom_types.py†L1-L220】 |
| `constants.py` | `get_attributes_for_system`, `get_attribute_codes_for_system`, `uses_charisma`, `uses_big_five` plus numerous constant values. | Defines prompt constants, actor identifiers, system metadata. | Keep – port all constants to ensure identical gameplay semantics. 【F:mvp_site/constants.py†L1-L360】 |
| `entity_utils.py` | `filter_unknown_entities`, `is_unknown_entity` | Helper filters for entity lists. | Keep. 【F:mvp_site/entity_utils.py†L1-L120】 |
| `token_utils.py` | `estimate_tokens`, `log_with_tokens`, `format_token_count` | Token estimation/logging helpers to monitor prompt size. | Keep (or replace with API-specific estimator). 【F:mvp_site/token_utils.py†L1-L200】 |
| `debug_hybrid_system.py` | `process_story_for_display`, `get_narrative_for_display`, etc. | Cleans debug artefacts from story entries. | Keep if debug mode remains; otherwise simplify. 【F:mvp_site/debug_hybrid_system.py†L1-L260】 |
| `debug_json_response.py` | `fix_incomplete_json`, `validate_json_response`, `extract_planning_block` | Recovery helpers for malformed Gemini JSON. | Keep as safety net until Gemini outputs are 100% reliable. 【F:mvp_site/debug_json_response.py†L1-L200】 |
| `json_utils.py` | `try_parse_json`, `complete_truncated_json`, etc. | Defensive JSON parsing utilities used across the stack. | Keep. 【F:mvp_site/json_utils.py†L1-L260】 |
| `robust_json_parser.py` | `RobustJSONParser`, `parse_llm_json_response` | Higher-level parser orchestrating fallback strategies when Gemini responses break schema. | Keep – essential guardrail. 【F:mvp_site/robust_json_parser.py†L1-L300】 |
| `logging_util.py` | `LoggingUtil`, `info`, `error`, etc. | Central logging configuration wrapper used by both Flask and tooling. | Keep – port to Node logger abstraction. 【F:mvp_site/logging_util.py†L1-L260】 |
| `decorators.py` | `log_exceptions` | Decorator used across tests/services to add consistent logging. | Keep. 【F:mvp_site/decorators.py†L1-L120】 |

## Memory & MCP Support Data

| File | Public API | Responsibility | Keep? |
| --- | --- | --- | --- |
| `memory_integration.py` | `MemoryIntegration`, `MemoryMetrics`, `enhance_slash_command` | Adds slash-command enhancements and metrics around memory usage. | Keep if memory remains. 【F:mvp_site/memory_integration.py†L1-L260】 |
| `memory_mcp_real.py` | See MCP Bridge table. | | |
| `mcp_memory_real.py` | See MCP Bridge table. | | |

## Validation Helpers

| File | Public API | Responsibility | Keep? |
| --- | --- | --- | --- |
| `narrative_sync_validator.py` | (see above) | | |
| `narrative_response_schema.py` | (see above) | | |

## Data & Fixtures

- `world/` – JSON/world data assets loaded by `world_loader`. Keep, port to a
  data directory consumable by the TypeScript build.
- `ai_token_discovery_results.json` – Captured benchmark data; optional archive.
- `docs/` under `mvp_site/` – Background writeups (generalized caching,
  frontend comparisons). Keep as historical references.

## Gemini/Firestore Mocks

| File | Public API | Responsibility | Keep? |
| --- | --- | --- | --- |
| `mocks/mock_gemini_service.py` | `MockGeminiClient`, `get_mock_client`, `parse_state_updates_from_response` | Provides deterministic Gemini responses for tests. | Keep to support regression suites. 【F:mvp_site/mocks/mock_gemini_service.py†L1-L200】 |
| `mocks/mock_gemini_service_wrapper.py` | `get_client`, `generate_content`, `get_initial_story`, `continue_story` | Wrapper exposing the mock Gemini client with the same interface as real service. | Keep. 【F:mvp_site/mocks/mock_gemini_service_wrapper.py†L1-L200】 |
| `mocks/mock_firestore_service.py` | `MockFirestoreClient`, `get_mock_firestore_client`, etc. | In-memory Firestore substitute for tests. | Keep. 【F:mvp_site/mocks/mock_firestore_service.py†L1-L260】 |
| `mocks/mock_firestore_service_wrapper.py` | `get_client`, `get_campaigns_for_user`, etc. | Ensures mocks share API surface with production Firestore service. | Keep. 【F:mvp_site/mocks/mock_firestore_service_wrapper.py†L1-L260】 |
| `mocks/data_fixtures.py`, `mocks/structured_fields_fixtures.py` | Prebuilt test fixtures. | Keep. 【F:mvp_site/mocks/data_fixtures.py†L1-L200】 |

These modules underpin the persistence and AI layers that any TypeScript
rewrite must faithfully port. They define the data contracts consumed by
`world_logic` and the HTTP handlers described in `backend_core.md`.
