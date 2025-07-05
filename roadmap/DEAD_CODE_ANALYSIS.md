# Dead Code Analysis Report

Generated on: 2025-07-03

## Summary

This report identifies potentially dead code in the Python codebase, excluding test files, prototype files, and analysis scripts.

## 1. Potentially Unused Functions

These functions appear to have no calls in the codebase:

### Core Application Files

1. **game_state.py**
   - `get_initial_game_state()` (line 276) - May be dead code or an unused utility function

2. **main.py**
   - `_prepare_game_state()` (line 131) - Private function that appears unused

3. **gemini_service.py**
   - `json_datetime_serializer()` (line 35) - Utility function that may be obsolete

4. **firestore_service.py**
   - `_truncate_log_json()` (line 14) - Private utility function appears unused

5. **world_loader.py**
   - `load_world_content_for_system_instruction()` (line 19) - Appears to be dead code

### Entity and Schema Files

6. **entity_tracking.py**
   - `create_from_game_state()` (line 41) - Factory method appears unused

7. **schemas/entities_simple.py**
   - `create_from_game_state()` (line 260) - Factory method appears unused

8. **schemas/entities_pydantic.py**
   - `create_from_game_state()` (line 300) - Factory method appears unused

### Utility and Helper Files

9. **constants.py**
   - `is_valid_attribute_system()` (line 79) - Validation function appears unused

10. **document_generator.py**
    - `get_story_text_from_context()` (line 6) - Text extraction function appears unused

11. **narrative_response_schema.py**
    - `parse_structured_response()` (line 93) - Parser function appears unused

### Mock and Test Support Files

12. **mocks/mock_gemini_service.py**
    - `get_mock_client()` (line 165) - Mock factory appears unused

13. **mocks/mock_firestore_service.py**
    - `get_mock_firestore_client()` (line 238) - Mock factory appears unused

14. **test_integration/integration_test_lib.py**
    - `timeout_handler()` (line 24) - Signal handler appears unused

15. **debug_test.py**
    - `run_single_test()` (line 16) - Test runner function appears unused

## 2. Potentially Unused Classes

These classes appear to have no instantiation or usage:

1. **schemas/entities_simple.py** - `class EntityType` (line 12)
2. **schemas/entities_pydantic.py** - `class EntityType` (line 12)
3. **functional_validation_runner.py** - `class FunctionalValidationRunner` (line 12)
4. **entity_preloader.py** - `class EntityPreloader` (line 13)
5. **entity_preloader_original.py** - `class EntityPreloader` (line 13)
6. **narrative_response_schema.py** - `class NarrativeResponse` (line 9)
7. **debug_mode_parser.py** - `class DebugModeParser` (line 9)
8. **firestore_service.py** - `class MissionHandler` (line 51)
9. **main.py** - `class StateHelper` (line 54)
10. **ai_token_discovery.py** - `class AITokenDiscovery` (line 17)
11. **entity_instructions.py** - `class EntityInstruction` (line 14)
12. **entity_instructions_original.py** - `class EntityInstruction` (line 14)
13. **narrative_sync_validator.py** - `class EntityPresenceType` (line 13)
14. **gemini_service.py** - `class PromptBuilder` (line 186)
15. **entity_validator.py** - `class ValidationResult` (line 15)
16. **dual_pass_generator.py** - `class GenerationPass` (line 15)
17. **game_state.py** - `class MigrationStatus` (line 10)

## 3. Potentially Unused Imports

### gemini_service.py
- `entity_tracking.SceneManifest` - Imported but not used

### game_state.py
- `typing.Optional` - Imported but not used

### entity_tracking.py
- `typing.List` - Imported but not used

## 4. Files That May Be Entirely Dead

Based on the analysis, these files contain only unused code:

1. **entity_preloader_original.py** - Appears to be a backup/old version
2. **entity_instructions_original.py** - Appears to be a backup/old version
3. **ai_token_discovery.py** - Contains only an unused class
4. **functional_validation_runner.py** - Contains only an unused class
5. **debug_mode_parser.py** - Contains only an unused class
6. **narrative_sync_validator.py** - Contains only an unused class
7. **dual_pass_generator.py** - Contains only an unused class

## 5. False Positives Identified

During analysis, these were initially flagged but are actually used:

- `log_exceptions` in decorators.py - Used as a decorator with `@log_exceptions`
- Test functions and main() functions - Entry points that don't need to be called

## Recommendations

1. **Immediate Actions:**
   - Remove or archive the `*_original.py` files if they're no longer needed
   - Remove unused utility functions in core files (game_state, main, gemini_service)
   - Clean up unused imports

2. **Investigation Needed:**
   - Verify if the unused classes are part of a planned feature or can be removed
   - Check if factory methods like `create_from_game_state()` are part of an interface that needs to be maintained

3. **Code Organization:**
   - Consider consolidating entity-related classes that appear unused
   - Review if mock factories are needed for future tests

## Note

This analysis excludes:
- Test files (tests/*, test_*.py)
- Prototype files (prototype/*)
- Analysis scripts (analysis/*)
- Virtual environment files (venv/*)
- Special methods (__init__, __str__, etc.)

Some code may appear dead but could be:
- Used dynamically (via getattr, importlib, etc.)
- Part of a public API
- Kept for backwards compatibility
- Part of incomplete features