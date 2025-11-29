# Python Modules: root

> Last updated: 2025-10-08  
> Regenerate via: `./scripts/generate_mvp_site_docs.sh root-python`
>
> Auto-generated overview of module docstrings and public APIs. Enhance descriptions as needed.

## `__init__.py`

**Role:** Package initialization for ``mvp_site``.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:** None exported (primarily internal helpers).

---

## `constants.py`

**Role:** Shared constants used across multiple services in the application. This prevents cyclical dependencies and keeps key values consistent.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `get_attributes_for_system` – Get the list of attributes for the given system. (Status: Keep).
- `get_attribute_codes_for_system` – Get the list of attribute codes for the given system. (Status: Keep).
- `uses_charisma` – Check if the given system uses Charisma attribute. (Status: Keep).
- `uses_big_five` – Check if the given system uses Big Five personality traits for social mechanics. (Status: Keep).

---

## `custom_types.py`

**Role:** Shared type definitions for WorldArchitect.AI This module contains common type definitions used across the application, including TypedDicts for Firebase data structures, type aliases, and protocol definitions for better type safety.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class CampaignData` – Type definition for campaign data stored in Firestore. (Status: Keep).
- `class StateUpdate` – Type definition for state update objects. (Status: Keep).
- `class EntityData` – Type definition for entity data in campaigns. (Status: Keep).
- `class MissionData` – Type definition for mission/quest data. (Status: Keep).
- `class ApiResponse` – Standard API response structure. (Status: Keep).
- `class GeminiRequest` – Type definition for Gemini API requests. (Status: Keep).
- `class GeminiResponse` – Type definition for Gemini API responses. (Status: Keep).
- `class DatabaseService` – Protocol for database service implementations. (Status: Keep).
  - `get_campaign` – Retrieve a campaign by ID. (Status: Keep).
  - `update_campaign` – Update a campaign with the provided field changes. (Status: Keep).
  - `delete_campaign` – Delete a campaign. (Status: Keep).
- `class AIService` – Protocol for AI service implementations. (Status: Keep).
  - `generate_response` – Generate an AI response. (Status: Keep).
  - `validate_response` – Validate an AI response. (Status: Keep).

---

## `debug_hybrid_system.py`

**Role:** Hybrid debug content system for backward compatibility. This module provides functions to handle both old campaigns with embedded debug tags and new campaigns with structured debug_info fields.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `contains_json_artifacts` – Check if text contains JSON artifacts that need cleaning. Args: text: Text to check for JSON artifacts Returns: True if text appears to contain JSON that should be cleaned (Status: Keep).
- `convert_json_escape_sequences` – Convert JSON escape sequences to their actual characters. This function properly converts JSON escape sequences like \n, \t, \" to their actual character equivalents, preserving content structure. Args: text: Text containing JSON escape sequences Returns: Text with escape sequences converted to actual characters (Status: Keep).
- `clean_json_artifacts` – Clean JSON artifacts from narrative text using the same logic as parse_structured_response. Args: text: Text that may contain JSON artifacts Returns: Cleaned text with JSON artifacts removed (Status: Keep).
- `contains_debug_tags` – Check if text contains any legacy debug tags. Args: text: Story text to check Returns: True if any debug tags are found (Status: Keep).
- `strip_debug_content` – Strip all debug content from text (for non-debug mode). Args: text: Text with potential debug tags Returns: Text with all debug content removed (Status: Keep).
- `strip_state_updates_only` – Strip only STATE_UPDATES blocks (for debug mode). Args: text: Text with potential state update blocks Returns: Text with STATE_UPDATES blocks removed but other debug content preserved (Status: Keep).
- `process_story_entry_for_display` – Process a single story entry for display, handling debug content and JSON artifacts appropriately. Args: entry: Story entry from database debug_mode: Whether debug mode is enabled Returns: Processed story entry safe for display (Status: Keep).
- `process_story_for_display` – Process a full story (list of entries) for display. Args: story_entries: List of story entries from database debug_mode: Whether debug mode is enabled Returns: Processed story entries safe for display (Status: Keep).
- `get_narrative_for_display` – Get narrative text appropriate for display based on campaign type and debug mode. This is the main function for processing individual narrative texts. Args: story_text: Raw story text from database debug_mode: Whether debug mode is enabled Returns: Processed narrative text (Status: Keep).

---

## `debug_json_response.py`

**Role:** Debug utilities for handling incomplete JSON responses from Gemini API

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `fix_incomplete_json` – Attempts to fix incomplete JSON responses from Gemini. Args: response_text: The potentially incomplete JSON string Returns: tuple: (fixed_json_dict, was_incomplete) (Status: Keep).
- `validate_json_response` – Validates that a JSON response has the expected structure. Args: response_dict: The parsed JSON dictionary Returns: tuple: (is_valid, missing_fields, truncated_fields) (Status: Keep).
- `extract_planning_block` – Extracts the planning block from a narrative, even if JSON was incomplete. Args: narrative_text: The narrative text that may contain a planning block Returns: str: The planning block text or None (Status: Keep).

---

## `debug_mode_parser.py`

**Role:** Debug Mode Command Parser

This module provides robust parsing and validation of debug mode commands from user input. Debug mode allows users to surface DM commentary, dice rolls, resource tracking, and other state changes.

**Key Features:**
- Comprehensive pattern matching for enable/disable commands.
- Conversational command support (for example, "please enable debug mode").
- Negative pattern filtering to avoid false matches.
- State change messaging and validation helpers.
- God mode restriction (debug commands only work in god mode).

**Architecture:**
- Static class methods for stateless parsing.
- Regex-based pattern matching with extensive coverage.
- Normalized input processing for consistent matching.
- Separate enable/disable pattern sets for clarity.

**Usage:**
```python
# Parse debug command
command_type, should_update = DebugModeParser.parse_debug_command(user_input, mode)

# Quick check if input is debug command
is_debug = DebugModeParser.is_debug_toggle_command(user_input, mode)

# Get appropriate system message
message = DebugModeParser.get_state_update_message(command_type, new_state)
```

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class DebugModeParser` – Parser for debug mode commands in god mode. (Status: Keep).
  - `parse_debug_command` – Parse user input for debug mode commands. Args: user_input: Raw user input string current_mode: Current interaction mode ('god' or 'character') Returns: Tuple of (command_type, should_update_state) - command_type: 'enable', 'disable', or None - should_update_state: True if state should be updated before LLM call (Status: Keep).
  - `is_debug_toggle_command` – Quick check if input is likely a debug toggle command. Args: user_input: Raw user input string current_mode: Current interaction mode Returns: True if this appears to be a debug toggle command (Status: Keep).
  - `get_state_update_message` – Get appropriate system message for debug mode state change. Args: command_type: 'enable' or 'disable' new_state: New debug mode state Returns: System message to display to user (Status: Keep).

---

## `decorators.py`

**Role:** Decorators Module This module provides utility decorators for common cross-cutting concerns in the application. Currently focuses on exception logging to provide consistent error handling across services. Key Features: - Exception logging with full context (function name, args, kwargs) - Stack trace preservation for debugging - Consistent error message formatting - Logger integration with emoji-enhanced logging Usage: @log_exceptions def my_function(): # Function logic here pass

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `log_exceptions` – A decorator that wraps a function in a try-except block and logs any exceptions with a full stack trace. Args: func: The function to be decorated. Returns: The wrapper function that includes exception logging. (Status: Keep).

---

## `document_generator.py`

**Role:** Document Generation System This module handles the generation of campaign documents in multiple formats (PDF, DOCX, TXT). It processes story logs from campaigns and converts them into formatted, exportable documents suitable for sharing or archiving. Key Features: - Multi-format export (PDF, DOCX, TXT) - Story context processing and formatting - Custom font support for better typography - Actor labeling system (Story, God, Main Character) - Consistent formatting across all export formats Architecture: - Format-specific generation functions - Shared story text processing - Configurable styling constants - Safe file handling with cleanup Usage: # Generate PDF document generate_pdf(story_text, output_path, campaign_title) # Generate DOCX document generate_docx(story_text, output_path, campaign_title) # Generate TXT document generate_txt(story_text, output_path, campaign_title) # Process story log for export story_text = get_story_text_from_context(story_log) Dependencies: - fpdf: PDF generation library - python-docx: DOCX document creation - DejaVu Sans font: Custom font for better Unicode support

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `get_story_text_from_context` – Convert story log entries to formatted text for document export. This function replicates the logic from main.py export_campaign. (Status: Keep).
- `generate_pdf` – Generates a PDF file and saves it to the specified path. (Status: Keep).
- `generate_docx` – Generates a DOCX file and saves it to the specified path. (Status: Keep).
- `generate_txt` – Generates a TXT file and saves it to the specified path. (Status: Keep).

---

## `dual_pass_generator.py`

**Role:** Dual-Pass Generation System (Option 7) First pass generates narrative, second pass verifies and injects missing entities.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class GenerationPass` – Represents a single generation pass (Status: Keep).
- `class DualPassResult` – Result of dual-pass generation (Status: Keep).
- `class DualPassGenerator` – Implements dual-pass generation to improve entity tracking. Pass 1: Generate initial narrative Pass 2: Verify entities and inject missing ones (Status: Keep).
  - `generate_with_dual_pass` – Execute dual-pass generation with entity verification. Args: initial_prompt: The original prompt for narrative generation expected_entities: Entities that should be present location: Current scene location generation_callback: Function to call AI generation (llm_service.continue_story) Returns: DualPassResult with both passes and final narrative (Status: Keep).
  - `create_entity_injection_snippet` – Create a snippet to inject a missing entity (REFACTORED: uses EntityValidator templates) (Status: Keep).
- `class AdaptiveEntityInjector` – Advanced entity injection that adapts based on narrative context. (Status: Keep).
  - `inject_entities_adaptively` – Adaptively inject missing entities based on narrative context (Status: Keep).

---

## `entity_instructions.py`

**Role:** Enhanced Explicit Entity Instructions (Option 5 Enhanced) Generates specific AI instructions requiring entity mentions and presence.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class EntityInstruction` – Represents an instruction for handling a specific entity (Status: Keep).
- `class EntityInstructionGenerator` – Generates explicit instructions for AI to ensure entity presence. Creates targeted instructions based on entity types and context. (Status: Keep).
  - `generate_entity_instructions` – Generate comprehensive entity instructions for AI prompts. Args: entities: List of all entities that should be present player_references: Entities specifically referenced by player input location: Current scene location story_context: Additional story context (Status: Keep).
  - `create_location_specific_instructions` – Create location-specific entity instructions (Status: Keep).
- `class EntityEnforcementChecker` – Validates that entity instructions are being followed in AI responses. (Status: Keep).
  - `check_instruction_compliance` – Check if narrative complies with entity instructions (Status: Keep).

---

## `entity_preloader.py`

**Role:** Entity Pre-Loading System (Option 3) Includes full entity manifest in every AI prompt to ensure entity presence.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class EntityPreloader` – Handles entity pre-loading for AI prompts to prevent entity disappearing. Implements Option 3: Entity Pre-Loading in Prompts. (Status: Keep).
  - `generate_entity_manifest` – Generate or retrieve cached entity manifest (Status: Keep).
  - `create_entity_preload_text` – Create entity pre-loading text to inject into AI prompts. This ensures all active entities are explicitly mentioned before generation. (Status: Keep).
  - `get_entity_count` – Get count of entities for logging/validation (Status: Keep).
  - `clear_cache` – Clear the manifest cache (useful for testing) (Status: Keep).
- `class LocationEntityEnforcer` – Implements location-based entity enforcement. Ensures location-appropriate NPCs are included in scenes. (Status: Keep).
  - `get_required_entities_for_location` – Get entities that should be present in a specific location (Status: Keep).
  - `validate_location_entities` – Validate that required entities are present for a location (Status: Keep).
  - `generate_location_enforcement_text` – Generate text to enforce location-appropriate entities (Status: Keep).

---

## `entity_tracking.py`

**Role:** Entity Tracking System This module provides entity tracking capabilities for narrative generation, ensuring that characters, NPCs, and other entities are properly tracked and validated during story generation. The system uses Pydantic validation for robust schema enforcement and data integrity. Key Features: - Scene manifest creation from game state - Entity status tracking (active, inactive, mentioned) - Visibility management (visible, hidden, off-screen) - Pydantic-based validation for data integrity - Integration with AI narrative generation Architecture: - Wrapper around Pydantic schemas for entity validation - Game state integration for entity discovery - Scene-based entity tracking with turn/session context - Enumerated status and visibility states Usage: # Create scene manifest from game state manifest = create_from_game_state(game_state, session_number, turn_number) # Get validation information info = get_validation_info() # Access entity data entities = manifest.get_expected_entities() Note: This module acts as a bridge between the core application and the Pydantic-based entity schemas, providing a stable API while delegating validation to the schemas module.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `create_from_game_state` – Create a SceneManifest from game state using Pydantic validation. (Status: Keep).
- `get_validation_info` – Get information about the current validation approach (Status: Keep).

---

## `entity_utils.py`

**Role:** Utility functions for entity handling and validation.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `filter_unknown_entities` – Filter out 'Unknown' entities from a list. 'Unknown' is used as a default location name when location is not found in world_data and should not be treated as a real entity for validation. Args: entities: List of entity names to filter Returns: List of entities with 'Unknown' entries removed (Status: Keep).
- `is_unknown_entity` – Check if an entity is the 'Unknown' placeholder. Args: entity: Entity name to check Returns: True if entity is 'Unknown' (case-insensitive), False otherwise (Status: Keep).

---

## `entity_validator.py`

**Role:** Enhanced Post-Generation Validation with Retry (Option 2 Enhanced) Validates AI output for missing entities and implements retry logic.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class EntityPresenceType` – Types of entity presence in narrative (Status: Keep).
- `class ValidationResult` – Result of entity validation - unified format for all validators (Status: Keep).
- `class EntityValidator` – Enhanced post-generation validator that checks for missing entities and provides retry logic for improved entity tracking. (Status: Keep).
  - `analyze_entity_presence` – Determine if an entity is physically present or just mentioned (consolidated from NarrativeSyncValidator) (Status: Keep).
  - `extract_physical_states` – Extract physical state descriptions from narrative (consolidated from NarrativeSyncValidator) (Status: Keep).
  - `detect_scene_transitions` – Detect location transitions in the narrative (consolidated from NarrativeSyncValidator) (Status: Keep).
  - `create_injection_templates` – Create entity injection templates (consolidated from DualPassGenerator) (Status: Keep).
  - `validate_entity_presence` – Validate that expected entities are present in the narrative. Returns detailed validation result with retry suggestions. (Status: Keep).
  - `create_retry_prompt` – Create an enhanced prompt for retry when entities are missing (Status: Keep).
  - `validate` – Comprehensive validation method that supports both EntityValidator and NarrativeSyncValidator interfaces. This method consolidates all validation logic in one place. (Status: Keep).
- `class EntityRetryManager` – Manages retry logic for entity validation failures. Implements smart retry strategies to improve entity tracking. (Status: Keep).
  - `validate_with_retry` – Validate entity presence with automatic retry logic. Args: narrative_text: The AI-generated narrative expected_entities: List of entities that should be present location: Current scene location retry_callback: Function to call for regeneration (narrative_generator) Returns: Tuple of (final_validation_result, retry_attempts_used) (Status: Keep).
  - `get_retry_statistics` – Get statistics about retry performance (Status: Keep).

---

## `file_cache.py`

**Role:** Generalized file caching module using cachetools. This module provides thread-safe file caching for any file read operation, replacing custom cache implementations with a battle-tested library.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `read_file_cached` – Read file with automatic caching. Thread-safe with TTL expiration. Args: filepath: Path to file to read encoding: File encoding (default: utf-8) Returns: File content as string Raises: FileNotFoundError: If file doesn't exist IOError: If file can't be read (Status: Keep).
- `clear_file_cache` – Clear all cached files. Useful for testing and development. (Status: Keep).
- `get_cache_stats` – Get cache performance statistics. Returns: Dictionary with cache performance metrics (Status: Keep).
- `invalidate_file` – Remove specific file from cache (useful when file is modified). Args: filepath: Path to file to remove from cache Returns: True if file was in cache and removed, False otherwise (Status: Keep).

---

## `firestore_service.py`

**Role:** Firestore Service - Database Operations and Game State Management This module provides comprehensive database operations for WorldArchitect.AI, including campaign management, game state synchronization, and robust data handling. Key Responsibilities: - Campaign CRUD operations (Create, Read, Update, Delete) - Game state serialization and persistence - Complex state update processing with merge logic - Mission management and data conversion - Defensive programming patterns for data integrity - JSON serialization utilities for Firestore compatibility Architecture: - Uses Firebase Firestore for data persistence - Implements robust state update mechanisms - Provides mission handling with smart conversion - Includes comprehensive error handling and logging - Supports legacy data cleanup and migration Dependencies: - Firebase Admin SDK for Firestore operations - Custom GameState class for state management - NumericFieldConverter for data type handling - Logging utilities for comprehensive debugging

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class FirestoreWriteError` – Raised when Firestore write operations return unexpected responses. (Status: Keep).
- `class MissionHandler` – Handles mission-related operations for game state management. Consolidates mission processing, conversion, and updates. (Status: Keep).
  - `initialize_missions_list` – Initialize active_missions as empty list if it doesn't exist or is wrong type. (Status: Keep).
  - `find_existing_mission_index` – Find the index of an existing mission by mission_id. Returns -1 if not found. (Status: Keep).
  - `process_mission_data` – Process a single mission, either updating existing or adding new. (Status: Keep).
  - `handle_missions_dict_conversion` – Convert dictionary format missions to list append format. (Status: Keep).
  - `handle_active_missions_conversion` – Handle smart conversion of active_missions from various formats to list. (Status: Keep).
- `update_state_with_changes` – Recursively updates a state dictionary with a changes dictionary using intelligent merge logic. This is the core function for applying AI-generated state updates to the game state. It implements sophisticated handling for different data types and update patterns. Key Features: - Explicit append syntax: {'append': [items]} for safe list operations - Core memories safeguard: Prevents accidental overwrite of important game history - Recursive dictionary merging: Deep merge for nested objects - DELETE_TOKEN support: Allows removal of specific fields - Mission smart conversion: Handles various mission data formats - Numeric field conversion: Ensures proper data types - Defensive programming: Validates data structures before operations Update Patterns Handled: 1. DELETE_TOKEN - Removes fields marked for deletion 2. Explicit append - Safe list operations with deduplication 3. Core memories safeguard - Protects critical game history 4. Mission conversion - Handles dict-to-list conversion for missions 5. Dictionary merging - Recursive merge for nested structures 6. String-to-dict preservation - Maintains existing dict structures 7. Simple overwrite - Default behavior for primitive values Args: state_to_update (dict): The current game state to modify changes (dict): Changes to apply (typically from AI response) Returns: dict: Updated state dictionary with changes applied Example Usage: current_state = {"health": 100, "items": ["sword"]} changes = {"health": 80, "items": {"append": ["potion"]}} result = update_state_with_changes(current_state, changes) # Result: {"health": 80, "items": ["sword", "potion"]} (Status: Keep).
- `json_serial` – JSON serializer for objects not serializable by default json code (Status: Keep).
- `json_default_serializer` – Handles serialization of data types json doesn't know, like datetimes. (Status: Keep).
- `get_db` – Return an initialized Firestore client or fail fast. Tests should patch this helper rather than relying on in-module mocks so that production code paths always exercise the real Firestore SDK. (Status: Keep).
- `get_campaigns_for_user` – Retrieves campaigns for a given user with optional pagination and sorting. Args: user_id: Firebase user ID limit: Optional maximum number of campaigns to return sort_by: Sort field ('created_at' or 'last_played'), defaults to 'last_played' Returns: List of campaign dictionaries (Status: Keep).
- `get_campaign_by_id` – Retrieves a single campaign and its full story using a robust, single query and in-memory sort to handle all data types. (Status: Keep).
- `add_story_entry` – Add a story entry to Firestore with write-then-read pattern for data integrity. This function implements the write-then-read pattern: 1. Write data to Firestore 2. Read it back immediately to verify persistence 3. Only return success if read confirms write succeeded This prevents data loss from failed writes that appear successful to users. Args: user_id: User ID campaign_id: Campaign ID actor: Actor type ('user' or 'gemini') text: Story text content mode: Optional mode (e.g., 'god', 'character') structured_fields: Required dict for AI responses containing structured response fields (Status: Keep).
- `verify_document_by_id` – Verify a story entry was written by directly reading the document by ID Args: user_id: User ID campaign_id: Campaign ID document_id: Document ID to verify expected_actor: Expected actor type for validation Returns: bool: True if document exists and has correct actor (Status: Keep).
- `verify_latest_entry` – Efficiently verify a story entry was written by reading only the latest entries Args: user_id: User ID campaign_id: Campaign ID actor: Expected actor type text: Expected text content limit: Number of latest entries to check (default 10) Returns: bool: True if matching entry found in latest entries (Status: Keep).
- `create_campaign` – No docstring present; review implementation to confirm behavior. (Status: Keep).
- `get_campaign_game_state` – Fetches the current game state for a given campaign. (Status: Keep).
- `update_campaign_game_state` – Updates the game state for a campaign, overwriting with the provided dict. (Status: Keep).
- `update_campaign_title` – Updates the title of a specific campaign. (Status: Keep).
- `update_campaign` – Updates a campaign with arbitrary updates. (Status: Keep).
- `get_user_settings` – Get user settings from Firestore. Args: user_id: User ID to get settings for Returns: Dict containing user settings, empty dict if user exists but no settings, or None if user doesn't exist or database error (Status: Keep).
- `update_user_settings` – Update user settings in Firestore. Uses nested field updates to prevent clobbering sibling settings fields. Args: user_id: User ID to update settings for settings: Dictionary of settings to update Returns: bool: True if update succeeded, False otherwise (Status: Keep).

---

## `game_state.py`

**Role:** Defines the GameState class, which represents the complete state of a campaign.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class GameState` – A class to hold and manage game state data, behaving like a flexible dictionary. (Status: Keep).
  - `to_dict` – Serializes the GameState object to a dictionary for Firestore. (Status: Keep).
  - `from_dict` – Creates a GameState object from a dictionary (e.g., from Firestore). (Status: Keep).
  - `validate_checkpoint_consistency` – Validates that critical checkpoint data in the state matches references in the narrative. Returns a list of discrepancies found. Args: narrative_text: The latest narrative content from the AI Returns: List of discrepancy descriptions, empty if no issues found (Status: Keep).
  - `start_combat` – Initialize combat state with given combatants. Args: combatants_data: List of dicts with keys: name, initiative, type, hp_current, hp_max (Status: Keep).
  - `end_combat` – End combat and reset combat state. (Status: Keep).
  - `cleanup_defeated_enemies` – Identifies and removes defeated enemies from both combat_state and npc_data. Returns a list of defeated enemy names for logging. CRITICAL: This function works regardless of in_combat status to handle cleanup during combat end transitions. (Status: Keep).

---

## `gemini_request.py`

**Role:** GeminiRequest Class for Structured JSON Input to Gemini API This class replaces the flawed json_input_schema approach that converted JSON back to concatenated strings. Instead, it provides structured JSON that is sent directly to the Gemini API without string conversion. Key principles: 1. Flat JSON structure (no nested "context") 2. Preserves structured data types (dict, list) 3. Sends actual JSON to Gemini, not concatenated strings 4. Similar pattern to GeminiResponse class

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class GeminiRequestError` – Custom exception for GeminiRequest validation and serialization errors. (Status: Keep).
- `class PayloadTooLargeError` – Raised when JSON payload exceeds size limits. (Status: Keep).
- `class ValidationError` – Raised when GeminiRequest fields fail validation. (Status: Keep).
- `class GeminiRequest` – Structured request object for Gemini API calls. Provides a clean, typed interface for building JSON requests that are sent directly to Gemini API without string concatenation. (Status: Keep).
  - `to_json` – Convert to flat JSON structure for direct Gemini API consumption. Returns a flat dictionary with all fields at the top level. No nested "context" wrapper - just the raw structured data. Raises: PayloadTooLargeError: If JSON payload exceeds size limits GeminiRequestError: If JSON serialization fails (Status: Keep).
  - `build_story_continuation` – Build a GeminiRequest for story continuation. Args: user_action: The user's input/action user_id: User identifier game_mode: Game interaction mode (e.g., 'character', 'story') game_state: Current game state as structured dict story_history: Previous story entries as structured list checkpoint_block: Checkpoint summary text core_memories: Important story memories sequence_ids: Story sequence identifiers entity_tracking: Entity tracking data selected_prompts: Selected prompt types use_default_world: Whether to use default world content Returns: GeminiRequest configured for story continuation (Status: Keep).
  - `build_initial_story` – Build a GeminiRequest for initial story generation. Args: character_prompt: The character/story prompt from user user_id: User identifier selected_prompts: List of selected prompt types generate_companions: Whether to generate companion characters use_default_world: Whether to use default world content world_data: Custom world data if applicable Returns: GeminiRequest configured for initial story generation (Status: Keep).
- `json_default_serializer` – JSON serializer for objects that aren't serializable by default. Handles datetime objects and other non-JSON-serializable types with improved error handling and type safety. Args: obj: Object to serialize Returns: JSON-serializable representation of the object Raises: GeminiRequestError: If object cannot be serialized (Status: Keep).

---

## `gemini_response.py`

**Role:** Gemini Response objects for clean architecture between AI service and main application.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class GeminiResponse` – Gemini Response wrapper for clean architecture between AI service and main application. Provides structured response handling with backward compatibility. (Status: Keep).
  - `state_updates` – Backwards compatibility property for state_updates. (Status: Keep).
  - `entities_mentioned` – Backwards compatibility property for entities_mentioned. (Status: Keep).
  - `location_confirmed` – Backwards compatibility property for location_confirmed. (Status: Keep).
  - `debug_info` – Backwards compatibility property for debug_info. (Status: Keep).
  - `session_header` – Get session header from structured response. (Status: Keep).
  - `planning_block` – Get planning block from structured response. (Status: Keep).
  - `dice_rolls` – Get dice rolls from structured response. (Status: Keep).
  - `resources` – Get resources from structured response. (Status: Keep).
  - `get_narrative_text` – Get the narrative text with debug content handled based on debug mode. For new structured responses, the narrative is already clean. For legacy responses, this method provides backward compatibility. Args: debug_mode: If True, include debug content. If False, strip debug content. Returns: Clean narrative text (debug content is now in separate fields) (Status: Keep).
  - `has_debug_content` – Check if response has any debug content. (Status: Keep).
  - `get_state_updates` – Get state updates from structured response. (Status: Keep).
  - `get_entities_mentioned` – Get entities mentioned from structured response. (Status: Keep).
  - `get_location_confirmed` – Get confirmed location from structured response. (Status: Keep).
  - `get_debug_info` – Get debug info from structured response. (Status: Keep).
  - `create` – Create a GeminiResponse from raw Gemini API response. Handles all JSON parsing internally. Args: raw_response_text: Raw text response from Gemini API model: Model name used for generation Returns: GeminiResponse with parsed narrative and structured data (Status: Keep).
  - `create_from_structured_response` – Create GeminiResponse from structured JSON response. This is the new preferred way to create responses that properly separates narrative from debug content. Args: structured_response: Parsed NarrativeResponse object model: Model name used for generation combined_narrative_text: The combined narrative text (including god_mode_response if present) Returns: GeminiResponse with clean narrative and structured data (Status: Keep).
  - `create_legacy` – Create GeminiResponse from plain text (legacy support). This handles old-style responses that embed debug content in the narrative. Args: narrative_text: Raw narrative text (may contain debug tags) model: Model name used for generation structured_response: Optional structured response object Returns: GeminiResponse with debug content stripped from narrative (Status: Keep).

---

## `llm_service.py`

**Role:** Gemini Service - AI Integration and Response Processing This module provides comprehensive AI service integration for WorldArchitect.AI, handling all aspects of story generation, prompt construction, and response processing. Key Responsibilities: - Gemini AI client management and model selection - System instruction building and prompt construction - Entity tracking and narrative validation - JSON response parsing and structured data handling - Model fallback and error handling - Planning block enforcement and debug content management - Token counting and context management - **FIXED: Token limit management to prevent backstory cutoffs** Architecture: - Uses Google Generative AI (Gemini) for story generation - Implements robust prompt building with PromptBuilder class - Provides entity tracking with multiple mitigation strategies - Includes comprehensive error handling and model cycling - Supports both initial story generation and continuation - Manages complex state interactions and validation Key Classes: - PromptBuilder: Constructs system instructions and prompts - GeminiResponse: Custom response object with parsed data - EntityPreloader: Pre-loads entity context for tracking - EntityInstructionGenerator: Creates entity-specific instructions - DualPassGenerator: Retry mechanism for entity tracking Dependencies: - Google Generative AI SDK for Gemini API calls - Custom entity tracking and validation modules - Game state management for context - Token utilities for cost management

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `get_client` – Initializes and returns a singleton Gemini client. (Status: Keep).
- `class PromptBuilder` – Encapsulates prompt building logic for the Gemini service. This class is responsible for constructing comprehensive system instructions that guide the AI's behavior as a digital D&D Game Master. It manages the complex hierarchy of instructions and ensures proper ordering and integration. Key Responsibilities: - Build core system instructions in proper precedence order - Add character-related instructions conditionally - Include selected prompt types (narrative, mechanics) - Add system reference instructions (D&D SRD) - Generate companion and background summary instructions - Manage world content integration - Ensure debug instructions are properly included Instruction Hierarchy (in order of loading): 1. Master directive (establishes authority) 2. Game state instructions (data structure compliance) 3. Debug instructions (technical functionality) 4. Character template (conditional) 5. Selected prompts (narrative/mechanics) 6. System references (D&D SRD) 7. World content (conditional) The class ensures that instructions are loaded in the correct order to prevent "instruction fatigue" and maintain proper AI behavior hierarchy. (Status: Keep).
  - `build_core_system_instructions` – Build the core system instructions that are always loaded first. Returns a list of instruction parts. (Status: Keep).
  - `add_character_instructions` – Conditionally add character-related instructions based on selected prompts. (Status: Keep).
  - `add_selected_prompt_instructions` – Add instructions for selected prompt types in consistent order. (Status: Keep).
  - `add_system_reference_instructions` – Add system reference instructions that are always included. (Status: Keep).
  - `build_companion_instruction` – Build companion instruction text. (Status: Keep).
  - `build_background_summary_instruction` – Build background summary instruction text. (Status: Keep).
  - `build_continuation_reminder` – Build reminders for story continuation, especially planning blocks. (Status: Keep).
  - `finalize_instructions` – Finalize the system instructions by adding world instructions. Returns the complete system instruction string. (Status: Keep).
- `get_initial_story` – Generates the initial story part, including character, narrative, and mechanics instructions. Returns: GeminiResponse: Custom response object containing: - narrative_text: Clean text for display (guaranteed to be clean narrative) - structured_response: Parsed JSON with state updates, entities, etc. (Status: Keep).
- `continue_story` – Continues the story by calling the Gemini API with the current context and game state. Args: user_input: The user's input text mode: The interaction mode (e.g., 'character', 'story') story_context: List of previous story entries current_game_state: Current GameState object selected_prompts: List of selected prompt types use_default_world: Whether to include world content in system instructions Returns: GeminiResponse: Custom response object containing: - narrative_text: Clean text for display (guaranteed to be clean narrative) - structured_response: Parsed JSON with state updates, entities, etc. (Status: Keep).

---

## `inspect_sdk.py`

**Role:** No module docstring; review code to confirm responsibilities.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:** None exported (primarily internal helpers).

---

## `json_utils.py`

**Role:** Shared JSON parsing utilities for handling incomplete or malformed JSON responses

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `count_unmatched_quotes` – Count unmatched quotes in text, accounting for escape sequences. Returns: Number of unmatched quotes (odd number indicates we're in a string) (Status: Keep).
- `count_unmatched_braces` – Count unmatched braces and brackets, accounting for strings. Returns: tuple: (unmatched_braces, unmatched_brackets) (Status: Keep).
- `unescape_json_string` – Unescape common JSON escape sequences. (Status: Keep).
- `try_parse_json` – Try to parse JSON text, returning (result, success). (Status: Keep).
- `extract_json_boundaries` – Extract JSON content between first { and its matching } or [ and its matching ]. Returns: Extracted JSON string if valid boundaries found, original text if incomplete, or None if no JSON start marker ({ or [) is found (Status: Keep).
- `complete_truncated_json` – Attempt to complete truncated JSON by adding missing quotes and braces. (Status: Keep).
- `extract_field_value` – Extract a specific field value from potentially malformed JSON. Args: text: The JSON-like text field_name: The field to extract Returns: The extracted value or None (Status: Keep).

---

## `logging_util.py`

**Role:** Centralized logging utility with emoji-enhanced messages. Provides consistent error and warning logging across the application. Supports both module-level convenience functions and logger-aware functions that preserve logger context.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class LoggingUtil` – Centralized logging utility with emoji-enhanced messages. (Status: Keep).
  - `get_log_directory` – Get the standardized log directory path with branch isolation. Returns: str: Path to the log directory in format /tmp/worldarchitect.ai/{branch_name} (Status: Keep).
  - `get_log_file` – Get the standardized log file path for a specific service. Args: service_name: Name of the service (e.g., 'flask-server', 'mcp-server', 'test-server') Returns: str: Full path to the log file (Status: Keep).
  - `error` – Log an error message with fire and red dot emojis. Args: message: The error message to log *args: Additional positional arguments for logging logger: Optional logger instance to preserve context. If None, uses root logger. **kwargs: Additional keyword arguments for logging (Status: Keep).
  - `warning` – Log a warning message with warning emoji. Args: message: The warning message to log *args: Additional positional arguments for logging logger: Optional logger instance to preserve context. If None, uses root logger. **kwargs: Additional keyword arguments for logging (Status: Keep).
  - `get_error_prefix` – Get the error emoji prefix for manual use. (Status: Keep).
  - `get_warning_prefix` – Get the warning emoji prefix for manual use. (Status: Keep).
  - `info` – Log an info message (no emoji modification). Args: message: The info message to log *args: Additional positional arguments for logging **kwargs: Additional keyword arguments for logging (Status: Keep).
  - `debug` – Log a debug message (no emoji modification). Args: message: The debug message to log *args: Additional positional arguments for logging **kwargs: Additional keyword arguments for logging (Status: Keep).
  - `critical` – Log a critical message with double fire emoji. Args: message: The critical message to log *args: Additional positional arguments for logging **kwargs: Additional keyword arguments for logging (Status: Keep).
  - `exception` – Log an exception message with traceback. Args: message: The exception message to log *args: Additional positional arguments for logging **kwargs: Additional keyword arguments for logging (Status: Keep).
  - `basicConfig` – Configure basic logging settings. Args: **kwargs: Arguments to pass to logging.basicConfig (Status: Keep).
  - `getLogger` – Get a logger instance. Args: name: Logger name (optional) Returns: Logger instance (Status: Keep).
- `error` – Log an error message with fire and red dot emojis. Args: message: The error message to log *args: Additional positional arguments for logging **kwargs: Additional keyword arguments for logging. Use logger=my_logger to preserve logger context. (Status: Keep).
- `warning` – Log a warning message with warning emoji. Args: message: The warning message to log *args: Additional positional arguments for logging **kwargs: Additional keyword arguments for logging. Use logger=my_logger to preserve logger context. (Status: Keep).
- `info` – Log an info message (no emoji modification). (Status: Keep).
- `debug` – Log a debug message (no emoji modification). (Status: Keep).
- `critical` – Log a critical message with double fire emoji. (Status: Keep).
- `exception` – Log an exception message with traceback. (Status: Keep).
- `basicConfig` – Configure basic logging settings. (Status: Keep).
- `getLogger` – Get a logger instance. (Status: Keep).

---

## `main.py`

**Role:** No module docstring; review code to confirm responsibilities.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `setup_file_logging` – Configure file logging for current git branch using centralized logging_util. Creates branch-specific log files in /tmp/worldarchitect.ai/{branch}/flask-server.log and configures logging_util to write to both console and file. (Status: Keep).
- `safe_jsonify` – Safely serialize data to JSON, handling Firestore Sentinels and other special objects. This function processes the data through json_default_serializer to handle Firestore SERVER_TIMESTAMP and DELETE_FIELD sentinels before calling Flask's jsonify. (Status: Keep).
- `generic_error_response` – Return a generic error response without exposing internal details. Args: operation: Brief description of what failed (e.g., "create campaign", "authentication") status_code: HTTP status code to return Returns: Tuple of JSON response and status code (Status: Keep).
- `create_app` – Create and configure the Flask application. This function initializes the Flask application with all necessary configuration, middleware, and route handlers. It sets up CORS, authentication, and all API endpoints. Key Configuration: - Frontend asset serving from 'frontend_v1' folder (with /static/ redirect compatibility) - CORS enabled for all /api/* routes - Testing mode configuration from environment - Firebase Admin SDK initialization - Authentication decorator for protected routes - File logging to /tmp/worldarchitect.ai/{branch}/flask-server.log Routes Configured: - GET /api/campaigns - List user's campaigns - GET /api/campaigns/<id> - Get specific campaign - POST /api/campaigns - Create new campaign - PATCH /api/campaigns/<id> - Update campaign - POST /api/campaigns/<id>/interaction - Handle user interactions - GET /api/campaigns/<id>/export - Export campaign documents - /* - Frontend SPA fallback Returns: Configured Flask application instance (Status: Keep).
- `run_test_command` – Run a test command. Args: command: The test command to run ('testui', 'testuif', 'testhttp', 'testhttpf') (Status: Keep).

---

## `main_parallel_dual_pass.py`

**Role:** Parallel Dual-Pass Implementation - New endpoints for TASK-019 This module adds the new endpoints needed for parallel dual-pass processing. To be integrated into main.py

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `add_parallel_dual_pass_routes` – Add routes for parallel dual-pass optimization (Status: Keep).

---

## `mcp_api.py`

**Role:** World Logic MCP Server - D&D Game Mechanics This MCP server exposes WorldArchitect.AI's D&D 5e game mechanics as tools and resources. Extracted from the monolithic main.py to provide clean API boundaries via MCP protocol. Tests verified passing locally on mcp_redesign branch. Architecture: - MCP server exposing D&D game logic as tools - Clean separation from HTTP handling (translation layer) - Maintains all existing functionality through MCP tools - Supports real-time gaming with stateful sessions Key MCP Tools: - create_campaign: Initialize new D&D campaigns - create_character: Generate player/NPC characters - process_action: Handle game actions and story progression - get_campaign_state: Retrieve current game state - update_campaign: Modify campaign data - export_campaign: Generate campaign documents

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `handle_list_tools` – List available MCP tools for D&D game mechanics. (Status: Keep).
- `handle_call_tool` – Handle MCP tool calls for D&D game mechanics. (Status: Keep).
- `handle_list_resources` – List available MCP resources for D&D content. (Status: Keep).
- `handle_read_resource` – Read MCP resources for D&D content. (Status: Keep).
- `setup_mcp_logging` – Configure centralized logging for MCP server. (Status: Keep).
- `run_server` – Run the World Logic MCP server. (Status: Keep).

---

## `mcp_client.py`

**Role:** MCP Client Library for WorldArchitect.AI This module provides a simple MCP (Model Context Protocol) client for main.py to communicate with the world_logic.py MCP server. It handles JSON-RPC communication and provides translation functions between Flask HTTP requests/responses and MCP protocol. Architecture: - MCPClient class for JSON-RPC communication with MCP server - Translation functions to convert between HTTP and MCP formats - Error handling and mapping between MCP and HTTP status codes - Async-compatible design for future async Flask integration Usage: from mvp_site.mcp_client import MCPClient, http_to_mcp_request, mcp_to_http_response client = MCPClient("http://localhost:8000") result = await client.call_tool("create_campaign", {"name": "Test Campaign"})

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class MCPErrorCode` – MCP error codes from JSON-RPC 2.0 specification (Status: Keep).
- `class MCPError` – MCP error structure (Status: Keep).
- `class MCPClientError` – Exception raised by MCP client operations (Status: Keep).
- `class MCPClient` – MCP client for communicating with world_logic.py MCP server Provides methods to call MCP tools and retrieve resources via JSON-RPC 2.0 over HTTP. Handles connection failures and MCP protocol errors. Can be used as a context manager for automatic resource cleanup: with MCPClient("http://localhost:8000") as client: result = await client.call_tool("test_tool", {}) (Status: Keep).
  - `call_tool` – Call an MCP tool on the server Args: tool_name: Name of the tool to call arguments: Tool arguments Returns: Tool result data Raises: MCPClientError: On communication or MCP errors (Status: Keep).
  - `get_resource` – Get an MCP resource from the server Args: uri: Resource URI Returns: Resource content Raises: MCPClientError: On communication or MCP errors (Status: Keep).
  - `call_tool_sync` – Synchronous wrapper for call_tool - uses singleton event loop for performance Args: tool_name: Name of the tool to call arguments: Tool arguments Returns: Tool result data (Status: Keep).
  - `get_resource_sync` – Synchronous wrapper for get_resource - uses singleton event loop for performance Args: uri: Resource URI Returns: Resource content (Status: Keep).
  - `close` – Close the HTTP session (Status: Keep).
- `http_to_mcp_request` – Convert Flask request to MCP tool call format Args: flask_request: Flask Request object tool_name: Name of MCP tool to call Returns: Dictionary with MCP tool arguments (Status: Keep).
- `mcp_to_http_response` – Convert MCP tool result to Flask Response Args: mcp_result: Result from MCP tool call status_code: HTTP status code Returns: Flask Response object (Status: Keep).
- `handle_mcp_errors` – Map MCP errors to appropriate HTTP status codes and responses Args: error: MCP client error or generic exception Returns: Flask Response with appropriate error information (Status: Keep).
- `create_mcp_client` – Create and return a configured MCP client instance Returns: Configured MCPClient instance (Status: Keep).
- `example_usage` – Example of how main.py would use this client (Status: Keep).

---

## `mcp_memory_real.py`

**Role:** Real Memory MCP Integration This module provides the actual MCP integration for production use. Replace mcp_memory_stub.py imports with this module when ready.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class MCPMemoryClient` – MCP Memory client with dependency injection support (Status: Keep).
  - `initialize` – Initialize MCP function references (called once at startup) (Status: Keep).
  - `set_functions` – Dependency injection for testing (allows mock functions) (Status: Keep).
  - `search_nodes` – Call real Memory MCP search_nodes function (Status: Keep).
  - `open_nodes` – Call real Memory MCP open_nodes function (Status: Keep).
  - `read_graph` – Call real Memory MCP read_graph function (Status: Keep).
- `search_nodes` – Call real Memory MCP search_nodes function (Status: Keep).
- `open_nodes` – Call real Memory MCP open_nodes function (Status: Keep).
- `read_graph` – Call real Memory MCP read_graph function (Status: Keep).
- `initialize_mcp_functions` – Initialize MCP function references (called once at startup) (Status: Keep).
- `set_mcp_functions` – Dependency injection for testing (allows mock functions) (Status: Keep).

---

## `memory_integration.py`

**Role:** Memory MCP Integration Module Automatically enhances LLM responses with relevant memory context.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class MemoryIntegration` – Core memory integration for automatic context enhancement (Status: Keep).
  - `extract_query_terms` – Extracts key terms from the user input for use in memory searches. This method identifies and extracts various types of terms from the input string: - Entity names: Capitalized words or phrases (e.g., "John Doe"). - Technical terms: Words not in a predefined list of stop words. - PR references: Strings matching the pattern "PR #<number>". Args: user_input (str): The raw input string provided by the user. Returns: List[str]: A list of up to 5 unique terms extracted from the input, including entities, technical terms, and PR references. (Status: Keep).
  - `calculate_relevance_score` – Calculate the relevance score of an entity to a given query context. The scoring algorithm considers the following factors: - Name match: If the entity's name matches or contains terms from the query context, it contributes 0.4 to the score. - Type match: If the entity's type contains specific keywords (e.g., 'pattern', 'learning', 'issue'), it contributes 0.2 to the score. - Observation relevance: Matches between query terms and the entity's observations contribute 0.05 per match, up to a maximum of 0.3. The final score is capped at 1.0. Args: entity (Dict[str, Any]): The entity to evaluate. Expected keys include 'name', 'entityType', and 'observations' (a list of strings). query_context (str): The query context to compare against the entity. Returns: float: A relevance score between 0.0 and 1.0, where higher scores indicate greater relevance. (Status: Keep).
  - `search_relevant_memory` – Search and retrieve relevant memories. This method searches for memories relevant to the provided terms. It first checks the `hot_cache` for cached results. If no valid cache entry is found, it performs a search (implementation details omitted for brevity). Caching Behavior: - Results are cached in `hot_cache` with a time-to-live (TTL) of 5 minutes. - Cache keys are generated by concatenating the sorted search terms with colons. Error Handling: - If an exception occurs during the search, it is logged, and an empty list is returned. - The method also records metrics about the query's success or failure. Args: terms (List[str]): A list of search terms extracted from user input. Returns: List[Dict[str, Any]]: A list of memory entities relevant to the search terms. (Status: Keep).
  - `enhance_context` – Inject memory context into prompt (Status: Keep).
  - `get_enhanced_response_context` – Main entry point for memory enhancement (Status: Keep).
- `class MemoryMetrics` – Track memory system performance (Status: Keep).
  - `record_query` – No docstring present; review implementation to confirm behavior. (Status: Keep).
  - `cache_hit_rate` – No docstring present; review implementation to confirm behavior. (Status: Keep).
  - `avg_latency` – No docstring present; review implementation to confirm behavior. (Status: Keep).
- `enhance_slash_command` – Enhance slash command with memory context (Status: Keep).

---

## `memory_mcp_real.py`

**Role:** Memory MCP Integration - Architectural Limitation Documentation IMPORTANT: This module demonstrates why Python cannot directly integrate with Claude Code's MCP tools. The fundamental issue: - MCP tools (like mcp__memory-server__search_nodes) exist in Claude's execution environment - These are NOT Python modules and cannot be imported or called from Python code - They are only accessible to the Claude AI assistant, not to the Python runtime This module serves as documentation of this architectural limitation.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class MemoryMCPInterface` – Interface demonstrating the architectural limitation of MCP integration. MCP tools are not accessible from Python runtime. The correct approach is to implement memory enhancement as a behavioral protocol in CLAUDE.md, allowing the LLM to handle memory searches directly. (Status: Keep).
  - `search_nodes` – This method cannot actually call MCP tools from Python. The architectural limitation: - mcp__memory-server__search_nodes exists in Claude's environment - It is NOT a Python function that can be imported or called - Only the Claude AI can access these tools directly Returns: Empty list - Python cannot access MCP tools (Status: Keep).
  - `create_entities` – This method cannot actually call MCP tools from Python. See search_nodes docstring for architectural limitations. Returns: False - Python cannot access MCP tools (Status: Keep).
- `search_nodes` – See MemoryMCPInterface.search_nodes - returns empty list (Status: Keep).
- `create_entities` – See MemoryMCPInterface.create_entities - returns False (Status: Keep).

---

## `narrative_response_schema.py`

**Role:** Simplified structured narrative generation schemas Based on Milestone 0.4 Combined approach implementation (without pydantic dependency)

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class NarrativeResponse` – Schema for structured narrative generation response (Status: Keep).
  - `to_dict` – Convert to dictionary (Status: Keep).
- `class EntityTrackingInstruction` – Schema for entity tracking instructions to be injected into prompts (Status: Keep).
  - `create_from_manifest` – Create entity tracking instruction from manifest (Status: Keep).
  - `to_prompt_injection` – Convert to prompt injection format (Status: Keep).
- `parse_structured_response` – Parse structured response and check for JSON bug issues. (Status: Keep).
- `create_generic_json_instruction` – Create generic JSON response format instruction when no entity tracking is needed (e.g., during character creation, campaign initialization, or scenes without entities) (Status: Keep).
- `create_structured_prompt_injection` – Create structured prompt injection for JSON response format Args: manifest_text: Formatted scene manifest (can be empty) expected_entities: List of entities that must be mentioned (can be empty) Returns: Formatted prompt injection string (Status: Keep).
- `validate_entity_coverage` – Validate that the structured response covers all expected entities Returns: Dict with validation results (Status: Keep).

---

## `narrative_sync_validator.py`

**Role:** Narrative Synchronization Validator for Production Entity Tracking Adapted from Milestone 0.4 prototype for production use in llm_service.py REFACTORED: Now delegates to EntityValidator for all entity presence logic.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class EntityPresenceType` – Types of entity presence in narrative (Status: Keep).
- `class EntityContext` – Context information for an entity in the narrative (Status: Keep).
- `class ValidationResult` – Result of narrative validation (Status: Keep).
- `class NarrativeSyncValidator` – Advanced validator specifically designed for preventing narrative desynchronization. Delegates entity presence logic to EntityValidator while adding narrative-specific features. (Status: Keep).
  - `validate` – Validate narrative synchronization with advanced presence detection. REFACTORED: Now delegates all entity logic to EntityValidator. Args: narrative_text: The generated narrative expected_entities: List of entities that should appear location: Current scene location previous_states: Previous entity states for continuity checking (Status: Keep).

---

## `numeric_field_converter.py`

**Role:** Numeric field converter utilities for converting string values to integers. Used primarily for data layer operations (e.g., Firestore) where simple conversion is needed without smart defaults. For robust entity conversion with fallbacks, use DefensiveNumericConverter instead.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class NumericFieldConverter` – Simple utilities for converting string values to integers (Status: Keep).
  - `try_convert_to_int` – Try to convert a value to integer, return original if conversion fails. Args: value: The value to potentially convert Returns: The value converted to int if possible, otherwise unchanged (Status: Keep).
  - `convert_dict_with_fields` – Recursively convert specified numeric fields in a dictionary. Args: data: Dictionary to process numeric_fields: Set of field names that should be converted to integers Returns: Dictionary with specified numeric fields converted to integers (Status: Keep).
  - `convert_all_possible_ints` – Try to convert all string values that look like integers. This is useful for general-purpose conversion where you don't know field names. Args: data: Dictionary to process Returns: Dictionary with all convertible string integers converted (Status: Keep).
  - `convert_value` – Legacy method - just tries to convert the value regardless of key (Status: Keep).
  - `convert_dict` – Legacy method - tries to convert all possible integers (Status: Keep).

---

## `prompt_utils.py`

**Role:** Pure utility functions for campaign prompt building and JSON escape sequence conversion. This module contains helper functions that are shared between world_logic.py and tests. Extracted to avoid import-unsafe dependencies and code duplication.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:** None exported (primarily internal helpers).

---

## `robust_json_parser.py`

**Role:** Robust JSON parser for handling various forms of incomplete or malformed JSON from LLMs

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class RobustJSONParser` – A robust parser that can handle various forms of incomplete JSON responses. Designed specifically for LLM outputs that might be truncated or malformed. (Status: Keep).
  - `parse` – Attempts to parse JSON text with multiple fallback strategies. Args: text: The potentially incomplete JSON string Returns: tuple: (parsed_dict or None, was_incomplete) (Status: Keep).
- `parse_llm_json_response` – Parse potentially incomplete JSON response from LLM. Args: response_text: Raw response from LLM that should be JSON Returns: tuple: (parsed_dict, was_incomplete) (Status: Keep).

---

## `start_flask.py`

**Role:** Standalone Flask app starter for run_ui_tests.sh This resolves import path issues when running in subshells.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:** None exported (primarily internal helpers).

---

## `structured_fields_utils.py`

**Role:** Utility helpers for extracting structured Gemini response fields.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `extract_structured_fields` – Extract structured fields from a GeminiResponse-like object. (Status: Keep).

---

## `test_documentation_performance.py`

**Role:** Documentation Performance Test Tests documentation file sizes to prevent API timeouts This script checks documentation files against size thresholds and provides detailed reporting for files that may cause performance issues. Usage: python3 mvp_site/test_documentation_performance.py

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `get_file_size_info` – Get detailed size information for a file (Status: Keep).
- `check_documentation_files` – Check all documentation files for size issues (Status: Keep).
- `main` – Main execution function (Status: Keep).

---

## `token_utils.py`

**Role:** Token counting utilities for consistent logging across the application.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `estimate_tokens` – Estimate token count for text. Uses the rough approximation of 1 token per 4 characters for Gemini models. This is a simple estimation - for exact counts, use the Gemini API's count_tokens method. Args: text: String or list of strings to count tokens for Returns: Estimated token count (Status: Keep).
- `log_with_tokens` – Log a message with both character and token counts. Args: message: Base message to log text: Text to count logger: Logger instance (uses logging if not provided) (Status: Keep).
- `format_token_count` – Format character count with estimated tokens. Args: char_count: Number of characters Returns: Formatted string like "1000 characters (~250 tokens)" (Status: Keep).

---

## `unified_api_examples.py`

**Role:** Examples showing how to use unified_api.py from both Flask and MCP contexts. This file demonstrates the integration patterns for using the unified API layer to provide consistent functionality across different interfaces.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:** None exported (primarily internal helpers).

---

## `world_loader.py`

**Role:** World content loader for WorldArchitect.AI Loads world files and creates combined instruction content for AI system.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `load_banned_names` – Load the banned names from the dedicated banned_names.md file Returns: str: Banned names content or empty string if not found. (Status: Keep).
- `load_world_content_for_system_instruction` – Load world file and create system instruction. Returns: str: Combined world content formatted for system instruction (Status: Keep).

---

## `world_logic.py`

**Role:** Unified API Layer for WorldArchitect.AI This module provides consistent JSON interfaces for both Flask and MCP server usage, extracting shared business logic and standardizing input/output formats. Architecture: - Unified functions handle the core game logic - Consistent JSON input/output structures - Centralized error handling and response formatting - Support for both user_id extraction (Flask auth) and explicit parameters (MCP)

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `json_default_serializer` – Default JSON serializer for objects that are not naturally JSON serializable. Handles specific known types with targeted exception handling. (Status: Keep).
- `truncate_game_state_for_logging` – Truncates a game state dictionary for logging to improve readability. Uses the enhanced _truncate_log_json function from firestore_service. (Status: Keep).
- `create_campaign_unified` – Unified campaign creation logic for both Flask and MCP. Args: request_data: Dictionary containing: - user_id: User ID - title: Campaign title - character: Character description (optional) - setting: Setting description (optional) - description: Campaign description (optional) - prompt: Legacy prompt format (optional) - selected_prompts: List of selected prompts (optional) - custom_options: List of custom options (optional) Returns: Dictionary with success/error status and campaign data (Status: Keep).
- `process_action_unified` – Unified story processing logic for both Flask and MCP. Args: request_data: Dictionary containing: - user_id: User ID - campaign_id: Campaign ID - user_input: User action/input - mode: Interaction mode (optional, defaults to 'character') Returns: Dictionary with success/error status and story response (Status: Keep).
- `get_campaign_state_unified` – Unified campaign state retrieval logic for both Flask and MCP. Args: request_data: Dictionary containing: - user_id: User ID - campaign_id: Campaign ID - include_story: Whether to include processed story (optional, default False) Returns: Dictionary with success/error status and campaign state (Status: Keep).
- `update_campaign_unified` – Unified campaign update logic for both Flask and MCP. Args: request_data: Dictionary containing: - user_id: User ID - campaign_id: Campaign ID - updates: Dictionary of updates to apply Returns: Dictionary with success/error status (Status: Keep).
- `export_campaign_unified` – Unified campaign export logic for both Flask and MCP. Args: request_data: Dictionary containing: - user_id: User ID - campaign_id: Campaign ID - format: Export format ('pdf', 'docx', 'txt') - filename: Optional filename Returns: Dictionary with success/error status and export info (Status: Keep).
- `get_campaigns_for_user_list` – Get campaigns list for a user - synchronous version for tests. (Status: Keep).
- `get_campaigns_list_unified` – Unified campaigns list retrieval logic for both Flask and MCP. Args: request_data: Dictionary containing: - user_id: User ID - limit: Optional maximum number of campaigns to return - sort_by: Optional sort field ('created_at' or 'last_played') Returns: Dictionary with success/error status and campaigns list (Status: Keep).
- `create_error_response` – Create standardized error response. Args: message: Error message status_code: HTTP status code (for Flask compatibility) Returns: Standardized error response dictionary (Status: Keep).
- `create_success_response` – Create standardized success response. Args: data: Response data Returns: Standardized success response dictionary (Status: Keep).
- `get_user_settings_unified` – Unified user settings retrieval for both Flask and MCP. Args: request_data: Dictionary containing: - user_id: User ID Returns: Dictionary with user settings or default settings (Status: Keep).
- `update_user_settings_unified` – Unified user settings update for both Flask and MCP. Args: request_data: Dictionary containing: - user_id: User ID - settings: Dictionary of settings to update Returns: Dictionary with success status and updated settings (Status: Keep).
- `apply_automatic_combat_cleanup` – Automatically cleans up defeated enemies from combat state when combat updates are applied. This function should be called after any state update that modifies combat_state. It identifies defeated enemies (HP <= 0) and removes them from both combat_state and npc_data to maintain consistency. Args: updated_state_dict: The state dictionary after applying proposed changes proposed_changes: The original changes dict to check if combat_state was modified Returns: Updated state dictionary with defeated enemies cleaned up (Status: Keep).
- `format_game_state_updates` – Formats a dictionary of game state updates into a readable string, counting the number of leaf-node changes. (Status: Keep).
- `parse_set_command` – Parses a multi-line string of `key.path = value` into a nested dictionary of proposed changes. Handles multiple .append operations correctly. (Status: Keep).

---

