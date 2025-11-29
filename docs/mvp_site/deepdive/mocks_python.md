# Python Modules: mocks

> Auto-generated overview of module docstrings and public APIs. Enhance descriptions as needed.
> Updated: 2025-10-08

## `mocks/__init__.py`

**Role:** Mock libraries for function testing. Provides realistic mocks for external dependencies like Gemini API and Firestore.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:** None exported (primarily internal helpers).

---

## `mocks/data_fixtures.py`

**Role:** Data fixtures for testing. Provides realistic sample data for campaigns, game states, and AI responses. Note: This is a data fixtures file, not a test file. It provides sample data for other tests to use.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:** None exported (primarily internal helpers).

---

## `mocks/mock_firestore_service.py`

**Role:** Mock Firestore service for function testing. Provides in-memory database simulation without making actual Firestore calls.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class MockFirestoreDocument` – Mock Firestore document that behaves like the real DocumentSnapshot. (Status: Keep).
  - `to_dict` – Return the document data as a dictionary. (Status: Keep).
  - `get` – Get a specific field from the document. (Status: Keep).
  - `exists` – Check if the document exists. (Status: Keep).
  - `id` – Get the document ID. (Status: Keep).
- `class MockFirestoreClient` – Mock Firestore client that simulates database operations in memory. Designed to behave like the real Firestore client for testing purposes. (Status: Keep).
  - `get_campaigns_for_user` – Get all campaigns for a user. (Status: Keep).
  - `get_campaign_by_id` – Get campaign and story context by ID. (Status: Keep).
  - `get_campaign_game_state` – Get the game state for a campaign. (Status: Keep).
  - `update_campaign_game_state` – Update the game state for a campaign. (Status: Keep).
  - `create_campaign` – Create a new campaign. (Status: Keep).
  - `add_story_entry` – Add a story entry to the campaign log. (Status: Keep).
  - `update_campaign_title` – Update a campaign's title. (Status: Keep).
  - `update_campaign` – Update a campaign with arbitrary updates. (Status: Keep).
  - `delete_campaign` – Delete a campaign and all associated data. (Status: Keep).
  - `get_game_state` – Get current game state as a dictionary. (Status: Keep).
  - `update_game_state` – Update the game state. (Status: Keep).
  - `get_story_context` – Get story context for a campaign. (Status: Keep).
  - `reset` – Reset the mock to initial state. (Status: Keep).
  - `get_operation_stats` – Get statistics about mock operations. (Status: Keep).
  - `set_campaign_data` – Set specific campaign data for testing. (Status: Keep).
  - `set_game_state_data` – Set specific game state data for testing. (Status: Keep).
  - `set_story_context` – Set specific story context for testing. (Status: Keep).
- `get_mock_firestore_client` – Get the global mock Firestore client instance. (Status: Keep).
- `add_story_entry` – Add a story entry to the campaign log. (Status: Keep).
- `get_campaign_by_id` – Get a campaign by ID. (Status: Keep).

---

## `mocks/mock_firestore_service_wrapper.py`

**Role:** Mock Firestore Service wrapper that provides the same interface as the real firestore_service module.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `get_client` – Get the mock Firestore client instance. (Status: Keep).
- `get_campaigns_for_user` – Get all campaigns for a user. (Status: Keep).
- `get_campaign_by_id` – Get campaign and story context by ID. (Status: Keep).
- `create_campaign` – Create a new campaign with all parameters. (Status: Keep).
- `update_campaign` – Update an existing campaign. (Status: Keep).
- `delete_campaign` – Delete a campaign. (Status: Keep).
- `get_game_state` – Get current game state. (Status: Keep).
- `update_game_state` – Update game state. (Status: Keep).
- `update_state_with_changes` – Update game state with partial changes. (Status: Keep).
- `get_campaign_game_state` – Get the current game state for a campaign (compatibility with real service). (Status: Keep).
- `update_campaign_game_state` – Update the current game state for a campaign (compatibility with real service). (Status: Keep).
- `add_story_entry` – Add a story entry to the log. Supports both legacy and new calling patterns. (Status: Keep).
- `get_story_context` – Get story context for a campaign. (Status: Keep).
- `json_default_serializer` – JSON serializer for objects not serializable by default json code. (Status: Keep).

---

## `mocks/mock_llm_service.py`

**Role:** Mock Gemini API service for function testing. Provides realistic AI responses without making actual API calls.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class MockGeminiResponse` – Mock response object that mimics the real Gemini API response. (Status: Keep).
- `class MockGeminiClient` – Mock Gemini client that simulates AI responses based on prompt patterns. Designed to behave like the real Gemini API for testing purposes. (Status: Keep).
  - `generate_content` – Generate content based on prompt patterns. Args: prompt_parts: List of prompt strings or single prompt string model: Model name (ignored in mock) Returns: MockGeminiResponse with appropriate text (Status: Keep).
  - `set_response_mode` – Set the response mode to trigger specific scenarios. (Status: Keep).
  - `reset` – Reset the mock to initial state. (Status: Keep).
- `get_mock_client` – Get the global mock client instance. (Status: Keep).
- `parse_state_updates_from_response` – Parse state updates from a mock AI response. Mimics the legacy state parsing function (now deprecated). (Status: Keep).

---

## `mocks/mock_llm_service_wrapper.py`

**Role:** Mock Gemini Service wrapper that provides the same interface as the real llm_service module.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `get_client` – Get the mock Gemini client instance. (Status: Keep).
- `generate_content` – Mock generate_content function that mimics the real service interface. Note: Parameters temperature, max_output_tokens, top_p, top_k, response_mime_type, and response_schema are accepted for API compatibility but not used in mock. (Status: Keep).
- `get_initial_story` – Mock get_initial_story function that returns predefined content. (Status: Keep).
- `continue_story` – Mock continue_story function that returns predefined content. (Status: Keep).

---

## `mocks/structured_fields_fixtures.py`

**Role:** Structured field fixtures for UI testing. Provides proper JSON responses with all 10 fields from game_state_instruction.md.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:** None exported (primarily internal helpers).

---

