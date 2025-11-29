# Python Modules: tests

> Auto-generated overview of module docstrings and public APIs. Enhance descriptions as needed.

## `tests/__init__.py`

**Role:** Test package setup.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:** None exported (primarily internal helpers).

---

## `tests/archive_redundant_test_real_api_integration.py`

**Role:** Red/Green Test: Real API Integration for Campaign Creation Tests that React V2 frontend makes real API calls to Flask backend (not mock)

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class RealAPIIntegrationTest` – Test real API integration between React V2 and Flask backend (Status: Keep).
  - `setUp` – Set up test environment (Status: Keep).
  - `test_mock_mode_disabled_red` – 🔴 RED TEST: Verify that mock mode was returning fake data This should FAIL after our fix since mock mode is disabled (Status: Keep).
  - `test_real_api_service_export_green` – 🟢 GREEN TEST: Verify that services/index.ts exports real API service (Status: Keep).
  - `test_api_service_no_test_bypass_green` – 🟢 GREEN TEST: Verify that api.service.ts has test mode disabled (Status: Keep).
  - `test_mock_toggle_removed_green` – 🟢 GREEN TEST: Verify MockModeToggle is removed from UI (Status: Keep).
  - `test_flask_backend_reachable` – 🟢 GREEN TEST: Verify Flask backend is running and reachable (Status: Keep).
  - `test_campaign_creation_api_integration` – 🟢 GREEN TEST: Integration test - Campaign creation makes real API call (Status: Keep).
  - `test_no_mock_service_in_production_path` – 🟢 GREEN TEST: Verify mock service is not in production import path (Status: Keep).
- `run_red_green_test` – Run the red/green test suite and report results (Status: Keep).

---

## `tests/auth/test_auth_resilience.py`

**Role:** Red/Green Test: Authentication Resilience Tests that JWT clock skew errors are automatically handled with retry logic

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class AuthResilienceTest` – Test authentication resilience features (Status: Keep).
  - `setUp` – Set up test environment (Status: Keep).
  - `test_clock_skew_auto_retry_mechanism` – 🔴 RED TEST: Verify that clock skew errors trigger auto-retry This test simulates the JWT "Token used too early" error and verifies that the new resilience logic attempts retry with fresh token (Status: Keep).
  - `test_user_friendly_error_messages` – 🔴 RED TEST: Verify that user gets helpful error messages instead of generic failures (Status: Keep).
  - `test_offline_campaign_caching` – 🔴 RED TEST: Verify that successful campaign data is cached for offline viewing (Status: Keep).
  - `test_connection_status_monitoring` – 🔴 RED TEST: Verify that connection status is monitored for smart UI adaptations (Status: Keep).
  - `test_integrated_resilience_workflow` – 🟢 GREEN TEST: Test the complete resilience workflow end-to-end This verifies that all components work together correctly (Status: Keep).
- `run_red_green_test` – Run the red/green test suite and report results (Status: Keep).

---

## `tests/data/extract_sariel_prompts.py`

**Role:** Extract the first 10 LLM prompts from Sariel campaign for integration testing. This includes the initial campaign setup prompt and player interactions.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class SarielPromptExtractor` – Extract prompts from Sariel campaign data (Status: Keep).
  - `load_campaign_data` – Load campaign data from JSON file (Status: Keep).
  - `extract_initial_prompt` – Extract the initial campaign setup prompt (Status: Keep).
  - `extract_player_prompts` – Extract the first 10 player interaction prompts (Status: Keep).
  - `format_prompts_for_testing` – Format prompts in a way suitable for integration testing (Status: Keep).
  - `save_prompts` – Save extracted prompts to a JSON file (Status: Keep).
  - `display_prompts` – Display the extracted prompts in a readable format (Status: Keep).
- `main` – Main function to extract and display Sariel campaign prompts (Status: Keep).

---

## `tests/data/show_sariel_test_summary.py`

**Role:** Show a summary of what the Sariel campaign integration test validates

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `show_sariel_test_summary` – Display summary of Sariel campaign integration test validation (Status: Keep).

---

## `tests/fake_auth.py`

**Role:** Fake Firebase Auth service for testing. Returns realistic auth responses instead of Mock objects.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class FakeUserRecord` – Fake Firebase User Record. (Status: Keep).
  - `to_dict` – Convert to dictionary representation. (Status: Keep).
- `class FakeDecodedToken` – Fake decoded Firebase token. (Status: Keep).
  - `get` – Get token claim value. (Status: Keep).
- `class FakeAuthError` – Fake Firebase Auth error. (Status: Keep).
- `class FakeFirebaseAuth` – Fake Firebase Auth service. (Status: Keep).
  - `get_user` – Get user by UID. (Status: Keep).
  - `get_user_by_email` – Get user by email. (Status: Keep).
  - `create_user` – Create a new user. (Status: Keep).
  - `update_user` – Update an existing user. (Status: Keep).
  - `delete_user` – Delete a user. (Status: Keep).
  - `verify_id_token` – Verify an ID token. (Status: Keep).
  - `create_custom_token` – Create a custom token. (Status: Keep).
  - `set_custom_user_claims` – Set custom claims for a user. (Status: Keep).
  - `list_users` – List users. (Status: Keep).
- `class FakeListUsersPage` – Fake list users page result. (Status: Keep).
  - `iterate_all` – Iterate over all users. (Status: Keep).
- `create_fake_auth` – Create a fake Firebase Auth service for testing. (Status: Keep).
- `create_test_token` – Create a test token for a specific user. (Status: Keep).

---

## `tests/fake_firestore.py`

**Role:** Fake Firestore implementation for testing. Returns real data structures instead of Mock objects to avoid JSON serialization issues.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class FakeFirestoreDocument` – Fake Firestore document that behaves like the real thing. (Status: Keep).
  - `set` – Simulate setting document data. (Status: Keep).
  - `update` – Simulate updating document data with nested field support. (Status: Keep).
  - `get` – Simulate getting the document. (Status: Keep).
  - `exists` – Document exists after being set. (Status: Keep).
  - `to_dict` – Return the document data. (Status: Keep).
  - `collection` – Get a subcollection. (Status: Keep).
- `class FakeFirestoreCollection` – Fake Firestore collection that behaves like the real thing. (Status: Keep).
  - `document` – Get or create a document reference. (Status: Keep).
  - `stream` – Stream all documents. (Status: Keep).
  - `add` – Add a new document with auto-generated ID. (Status: Keep).
  - `order_by` – Mock order_by for queries. (Status: Keep).
- `class FakeFirestoreClient` – Fake Firestore client that behaves like the real thing. (Status: Keep).
  - `collection` – Get a collection. (Status: Keep).
  - `document` – Get a document by path. (Status: Keep).
- `class FakeGeminiResponse` – Fake Gemini response that behaves like the real thing. (Status: Keep).
  - `get_state_updates` – Return state updates from the fake response. (Status: Keep).
  - `structured_response` – Mock structured response object. (Status: Keep).
- `class FakeTokenCount` – Fake token count response. (Status: Keep).

---

## `tests/fake_gemini.py`

**Role:** Fake Gemini AI service for testing. Returns realistic responses instead of Mock objects to avoid JSON serialization issues.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class FakeGeminiResponse` – Fake Gemini response that behaves like the real thing. (Status: Keep).
- `class FakeGenerationConfig` – Fake generation config object. (Status: Keep).
- `class FakeModelAdapter` – Fake model adapter that generates realistic responses. (Status: Keep).
  - `generate_content` – Generate a fake response based on prompt content. Args: prompt: Either a string prompt or structured JSON input dict generation_config: Generation configuration (optional) (Status: Keep).
- `class FakeGeminiClient` – Fake Gemini client that behaves like google.genai.Client. (Status: Keep).
- `class FakeModelsManager` – Fake models manager for token counting and model access. (Status: Keep).
  - `get` – Get a fake model adapter. (Status: Keep).
  - `generate_content` – Generate content using the default model (for backward compatibility). (Status: Keep).
  - `count_tokens` – Return fake token count. (Status: Keep).
- `class FakeTokenCount` – Fake token count response. (Status: Keep).
- `class FakeGenerativeModel` – Fake GenerativeModel for backward compatibility. (Status: Keep).
  - `generate_content` – Generate content using the adapter. (Status: Keep).
  - `count_tokens` – Count tokens in contents. (Status: Keep).
- `create_fake_gemini_client` – Create a fake Gemini client for testing. (Status: Keep).
- `create_fake_model` – Create a fake GenerativeModel for testing. (Status: Keep).

---

## `tests/fake_services.py`

**Role:** Unified fake services for testing WorldArchitect.AI. Provides a single point to configure all fake services instead of complex mocking. Includes JSON input schema validation support.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class FakeServiceManager` – Manages all fake services for testing. (Status: Keep).
  - `setup_environment` – Set up test environment variables. (Status: Keep).
  - `restore_environment` – Restore original environment variables. (Status: Keep).
  - `start_patches` – Start all service patches. (Status: Keep).
  - `stop_patches` – Stop all service patches. (Status: Keep).
  - `reset` – Reset all services to clean state. (Status: Keep).
  - `create_json_input` – Create structured JSON input for testing. Args: message_type: Type of message (initial_story, story_continuation, user_input, etc.) **kwargs: Additional fields for the JSON input Returns: Dict representing structured JSON input (Status: Keep).
  - `validate_json_input` – Validate JSON input structure. Args: json_input: JSON input to validate Returns: True if valid, False otherwise (Status: Keep).
  - `setup_campaign` – Set up a test campaign with realistic data. (Status: Keep).
  - `setup_user` – Set up a test user. (Status: Keep).
  - `create_test_token` – Create a test authentication token. (Status: Keep).
- `class TestCase` – Base test case with fake services pre-configured. (Status: Keep).
  - `setUp` – Set up fake services for each test. (Status: Keep).
  - `tearDown` – Clean up fake services after each test. (Status: Keep).
- `with_fake_services` – Decorator to automatically set up fake services for a test. (Status: Keep).
- `create_test_app` – Create a test Flask app with fake services configured. (Status: Keep).
- `get_test_headers` – Get test headers for bypassing authentication. (Status: Keep).

---

## `tests/frontend_v2/test_campaign_creation_v2_memory_leaks.py`

**Role:** Test for CampaignCreationV2 memory leak fixes Tests that all timeouts and intervals are properly cleaned up on component unmount

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestCampaignCreationV2MemoryLeaks` – Test memory leak fixes in CampaignCreationV2 component (Status: Keep).
  - `setUp` – No docstring present; review implementation to confirm behavior. (Status: Keep).
  - `test_component_unmount_clears_all_timers` – Test that component unmount properly clears all active timers (Status: Keep).
  - `test_error_handling_clears_timers` – Test that error handling properly clears all timers (Status: Keep).
  - `test_completion_flow_not_interrupted` – Test that completion flow shows 'Campaign ready!' message (Status: Keep).
  - `tearDown` – Clean up browser resources (Status: Keep).

---

## `tests/integration/test_real_browser_settings_game_integration.py`

**Role:** 🌐 REAL BROWSER UI TEST: Settings → Game Integration → Log Verification This test demonstrates the complete end-to-end functionality: 1. Open settings page in real browser 2. Select Gemini Flash 2.5 model 3. Create campaign and make game requests 4. Verify Flash model usage in server logs 5. Switch to Gemini Pro 2.5 model 6. Make more game requests 7. Verify Pro model usage in server logs This proves the settings system works end-to-end with real game functionality.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class RealBrowserSettingsGameTest` – Real browser test for settings → game integration (Status: Keep).
  - `get_current_branch` – Get current git branch name (Status: Keep).
  - `is_ci_environment` – Detect if running in CI environment (Status: Keep).
  - `wait_for_server` – Ensure server is running (Status: Keep).
  - `clear_existing_settings` – Clear any existing settings for clean test (Status: Keep).
  - `set_gemini_model` – Set Gemini model via API (Status: Keep).
  - `verify_model_setting` – Verify model setting persisted (Status: Keep).
  - `create_test_campaign` – Create a test campaign for game requests (Status: Keep).
  - `make_game_request` – Make a game request and verify model usage in logs (Status: Keep).
  - `append_to_log` – Append marker to log file (Status: Keep).
  - `check_logs_for_model` – Check logs for model usage since marker (Status: Keep).
  - `run_browser_simulation_test` – Simulate the browser interactions that we've proven work (Status: Keep).
  - `run_complete_test` – Run the complete test sequence (Status: Keep).
- `class TestRealBrowserSettingsGameIntegration` – Unittest wrapper for integration test (Status: Keep).
  - `setUp` – No docstring present; review implementation to confirm behavior. (Status: Keep).
  - `test_real_browser_settings_game_integration` – Main integration test method (Status: Keep).

---

## `tests/mcp_test_client.py`

**Role:** MCP Test Client for WorldArchitect.AI Provides programmatic testing interface for the MCP server

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class MCPTestClient` – Test client for WorldArchitect.AI MCP server. (Status: Keep).
  - `health_check` – Check server health status. Returns: Health status response Raises: requests.RequestException: If request fails (Status: Keep).
  - `json_rpc_request` – Send JSON-RPC 2.0 request to MCP server. Args: method: JSON-RPC method name params: Method parameters (optional) request_id: Request identifier Returns: JSON-RPC response Raises: requests.RequestException: If request fails (Status: Keep).
  - `list_tools` – List available MCP tools. Returns: List of tool definitions (Status: Keep).
  - `list_resources` – List available MCP resources. Returns: List of resource definitions (Status: Keep).
  - `read_resource` – Read MCP resource content. Args: uri: Resource URI to read Returns: Resource content (Status: Keep).
  - `call_tool` – Call MCP tool. Args: name: Tool name arguments: Tool arguments Returns: Tool execution result (Status: Keep).
  - `create_campaign` – Create a new campaign. Args: user_id: Firebase user ID title: Campaign title **kwargs: Additional campaign parameters Returns: Campaign creation result (Status: Keep).
  - `get_campaign_state` – Get campaign state. Args: user_id: Firebase user ID campaign_id: Campaign identifier Returns: Campaign state data (Status: Keep).
  - `process_action` – Process user action in campaign. Args: user_id: Firebase user ID campaign_id: Campaign identifier user_input: User's action or dialogue mode: Interaction mode (character/narrator) Returns: Action processing result (Status: Keep).
  - `update_campaign` – Update campaign metadata. Args: user_id: Firebase user ID campaign_id: Campaign identifier updates: Fields to update Returns: Update result (Status: Keep).
  - `export_campaign` – Export campaign to document format. Args: user_id: Firebase user ID campaign_id: Campaign identifier format: Export format (pdf/docx/txt) Returns: Export result (Status: Keep).
  - `get_campaigns_list` – Get list of user campaigns. Args: user_id: Firebase user ID Returns: Campaigns list (Status: Keep).
  - `get_user_settings` – Get user settings. Args: user_id: Firebase user ID Returns: User settings (Status: Keep).
  - `update_user_settings` – Update user settings. Args: user_id: Firebase user ID settings: Settings to update Returns: Update result (Status: Keep).
- `class MCPTestSuite` – Test suite for comprehensive MCP server testing. (Status: Keep).
  - `run_test` – Run individual test and record result. Args: test_name: Name of the test test_func: Test function to execute Returns: True if test passed, False otherwise (Status: Keep).
  - `test_health_check` – Test server health endpoint. (Status: Keep).
  - `test_tools_list` – Test tools listing. (Status: Keep).
  - `test_resources_list` – Test resources listing. (Status: Keep).
  - `test_resource_read` – Test resource reading. (Status: Keep).
  - `test_campaign_workflow` – Test complete campaign workflow. (Status: Keep).
  - `test_user_settings` – Test user settings functionality. (Status: Keep).
  - `test_error_handling` – Test error handling scenarios. (Status: Keep).
  - `run_all_tests` – Run all tests in the suite. Returns: Test results summary (Status: Keep).
- `main` – Main test execution function. (Status: Keep).

---

## `tests/mcp_tests/test_mcp_cerebras_integration.py`

**Role:** MCP Cerebras Integration Test - Proof of Working Implementation This test validates that the MCP cerebras tool integration is working correctly after fixing the broken subprocess execution that was introduced by code review fixes. CRITICAL VALIDATION: - Only cerebras tool exposed for security - Tool integration follows expected protocol - Security restrictions properly enforced - MCP contamination filtering works correctly in context extraction === TDD Matrix: MCP Contamination Filtering === ## Test Matrix 1: MCP Pattern Recognition (15 test combinations) | Pattern Type | Content | Filter Mode | Expected Result | |-------------|---------|-------------|-----------------| | Tool Reference | [Used mcp__serena tool] | ON | Removed | | Tool Reference | [Used Bash tool] | ON | Removed | | Tool Reference | [Used mcp__memory__read tool] | ON | Removed | | Inline MCP | mcp__serena__read_file call | ON | Removed | | Meta Pattern | 🔍 Detected slash commands: | ON | Removed | | Mixed Content | Code block + [Used tool] | ON | Code preserved, tool ref removed | | Unicode + MCP | 🎯 Multi-Player Intelligence | ON | Removed | | No Contamination | Pure code/text content | ON | Preserved | | Disabled Filter | [Used tool] content | OFF | Preserved | ## Test Matrix 2: Content Preservation (12 test combinations) | Content Type | MCP Present | Filter Mode | Code Preserved | Text Preserved | |-------------|-------------|-------------|----------------|----------------| | Code Block | Yes | ON | ✅ | ✅ | | Technical Explanation | Yes | ON | ✅ | ✅ | | User Question | No | ON | ✅ | ✅ | | Mixed Code+Tool | Yes | ON | ✅ | ❌ (tool ref) | ## Test Matrix 3: Edge Cases (8 test combinations) | Edge Case | Input | Expected Behavior | |-----------|-------|-------------------| | Empty Content | "" | Returns empty | | Only MCP Refs | "[Used tool1] [Used tool2]" | Returns empty or minimal | | Whitespace Cleanup | "Text [Used tool] More" | "Text More" | | Nested Brackets | "[Used [nested] tool]" | Brackets handled correctly | Total Matrix Coverage: 35 systematic test cases

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestMCPCerebrasIntegration` – Comprehensive test suite proving MCP cerebras integration works correctly. (Status: Keep).
  - `test_tool_availability_and_security` – 🔒 SECURITY TEST: Verify only cerebras tool is exposed. This validates the security-first approach where only cerebras is available to prevent accidental tool exposure. (Status: Keep).
  - `test_slash_command_execution_pattern` – 🔧 RESPONSE TEST: Verify cerebras command responses are well-formed. This test ensures that the MCP tool returns a properly formatted command string rather than falling back to empty or malformed data. (Status: Keep).
  - `test_execution_speed_and_format` – ⚡ PERFORMANCE TEST: Complete integration proof with speed validation. This test runs the complete integration flow and validates: 1. Tool creation works correctly 2. Execution returns expected format 3. Performance is acceptable (sub-millisecond) 4. No timeouts or execution issues 5. Security restrictions in place (Status: Keep).

---

## `tests/mcp_tests/test_mcp_comprehensive.py`

**Role:** Comprehensive MCP Test Suite - Consolidated from 8 redundant test files Tests all MCP server functionality including cerebras tool, JSON-RPC, and red-green-refactor methodology

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestMCPComprehensive` – Comprehensive test suite for MCP server functionality (Status: Keep).
  - `project_root` – Dynamically find project root using CLAUDE.md marker (Status: Keep).
  - `test_tool_discovery` – Test that all slash commands are properly discovered (Status: Keep).
  - `test_cerebras_tool_execution` – Test cerebras tool execution through unified router (Status: Keep).
  - `test_input_validation_basic` – Test basic input validation in handle_tool_call (Status: Keep).
  - `test_invalid_tool_rejection` – Test that invalid tools are rejected (Status: Keep).
  - `test_json_rpc_communication` – Test JSON-RPC communication pattern with MCP server (Status: Keep).
  - `test_server_startup` – Test that the MCP server can start successfully (Status: Keep).
  - `test_red_green_refactor_cycle` – Test red-green-refactor methodology through MCP server (Status: Keep).
  - `test_argument_handling` – Test various argument patterns (Status: Keep).
  - `test_syntax_error_prevention` – Test that indentation and syntax errors are prevented (Status: Keep).
  - `test_consistent_argument_parsing` – Test consistent argument key usage (args vs arguments) (Status: Keep).
  - `test_tool_restriction_logic` – Test that only cerebras tool is allowed as intended (Status: Keep).

---

## `tests/test_age_field_validation.py`

**Role:** Test age field validation in Character classes.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestAgeFieldValidation` – Test age field validation and functionality. (Status: Keep).
  - `setUp` – Set up common test data. (Status: Keep).
  - `test_npc_with_age` – Test NPC creation with age field. (Status: Keep).
  - `test_npc_without_age` – Test NPC creation without age (should be allowed). (Status: Keep).
  - `test_pc_with_age` – Test PlayerCharacter creation with age field. (Status: Keep).
  - `test_pc_without_age` – Test PlayerCharacter creation without age (should be allowed). (Status: Keep).
  - `test_age_validation_negative` – Test that negative ages are rejected. (Status: Keep).
  - `test_age_validation_too_high` – Test that unreasonably high ages are rejected. (Status: Keep).
  - `test_fantasy_ages` – Test that fantasy-appropriate ages work. (Status: Keep).
  - `test_age_type_validation` – Test that non-integer ages are rejected. (Status: Keep).
  - `test_narrative_consistency_helpers` – Test that age enables narrative consistency helpers. (Status: Keep).

---

## `tests/test_ai_content_simple.py`

**Role:** AI Content Personalization Integration Test Tests that AI story generation uses campaign data instead of hardcoded content

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class AIContentPersonalizationTest` – Test that AI content generation uses user's campaign data (Status: Keep).
  - `test_story_continuation_uses_campaign_data` – Test story continuation integrates campaign context from game state (Status: Keep).
  - `test_initial_story_campaign_personalization` – Test initial story generation includes campaign personalization context (Status: Keep).
  - `test_no_hardcoded_character_names` – Test that requests don't contain hardcoded character names like 'Shadowheart' (Status: Keep).

---

## `tests/test_always_json_mode.py`

**Role:** Test that JSON mode is always used for all LLM calls Tests now properly skip when dependencies are unavailable (comprehensive dependency detection).

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestAlwaysJSONMode` – Test suite to ensure JSON mode is always used (Status: Keep).
  - `setUp` – Set up test fixtures (Status: Keep).
  - `test_json_mode_without_entities` – Test that JSON mode is used even when there are no entities (Status: Keep).
  - `test_json_mode_with_entities` – Test that JSON mode is used when entities are present (Status: Keep).
  - `test_generic_json_instruction_format` – Test the generic JSON instruction format (Status: Keep).
  - `test_structured_prompt_injection_without_entities` – Test that structured prompt injection works without entities (Status: Keep).
  - `test_structured_prompt_injection_with_entities` – Test that structured prompt injection works with entities (Status: Keep).

---

## `tests/test_animation_system.py`

**Role:** Animation System Tests - Milestone 3 Tests for CSS animations, JavaScript helpers, and performance

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestAnimationSystem` – Test the animation system components (Status: Keep).
  - `setUp` – Set up test environment (Status: Keep).
  - `test_animation_css_exists_and_valid` – Test that animation CSS file exists and contains expected animations (Status: Keep).
  - `test_animation_js_exists_and_valid` – Test that animation JavaScript file exists and is valid (Status: Keep).
  - `test_index_html_includes_animation_files` – Test that index.html includes animation CSS and JS (Status: Keep).
  - `test_animation_css_syntax_validation` – Test CSS syntax is valid (basic validation) (Status: Keep).
  - `test_animation_performance_properties` – Test that performance-enhancing CSS properties are present (Status: Keep).
  - `test_theme_specific_animations` – Test that theme-specific animations are included (Status: Keep).
  - `test_accessibility_features` – Test that accessibility features are properly implemented (Status: Keep).
  - `test_javascript_error_handling` – Test that JavaScript has proper error handling patterns (Status: Keep).
- `class TestAnimationIntegration` – Integration tests for animation system with existing app (Status: Keep).
  - `setUp` – Set up integration test environment (Status: Keep).
  - `test_animation_system_compatibility` – Test that animation system doesn't conflict with existing app.js (Status: Keep).
  - `test_loading_order_in_html` – Test that scripts are loaded in correct order (Status: Keep).
- `class TestAnimationPerformance` – Performance tests for animation system (Status: Keep).
  - `test_css_file_size` – Test that CSS file size is reasonable (Status: Keep).
  - `test_javascript_file_size` – Test that JavaScript file size is reasonable (Status: Keep).
  - `test_css_selector_efficiency` – Test that CSS selectors are efficient (Status: Keep).
- `class TestAnimationFunctionality` – Functional tests for animation features (Status: Keep).
  - `test_animation_duration_variables` – Test that animation duration variables are properly defined (Status: Keep).
  - `test_keyframe_animations_defined` – Test that essential keyframe animations are defined (Status: Keep).
  - `test_javascript_api_methods` – Test that JavaScript API provides expected methods (Status: Keep).
- `run_animation_tests` – Run all animation system tests (Status: Keep).

---

## `tests/test_api_backward_compatibility.py`

**Role:** Test API Backward Compatibility Ensures that API responses maintain backward compatibility with legacy frontend code. This prevents breaking changes like the one that caused the forEach error.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `has_firebase_credentials` – Check if Firebase credentials are available. (Status: Keep).
- `class TestAPIBackwardCompatibility` – Test that API responses maintain backward compatibility. (Status: Keep).
  - `setUp` – Set up test client. (Status: Keep).
  - `tearDown` – Restore original environment. (Status: Keep).
  - `test_campaigns_api_returns_legacy_array_format` – Test that /api/campaigns returns array directly for backward compatibility. Legacy format: [campaign1, campaign2, ...] NOT: {"campaigns": [...], "success": true} This maintains compatibility with frontend code that does: const { data: campaigns } = await fetchApi('/api/campaigns'); campaigns.forEach(...); // Expects campaigns to be an array (Status: Keep).
  - `test_campaigns_api_supports_foreach` – Test that campaigns response supports JavaScript forEach operation. (Status: Keep).
  - `test_other_apis_maintain_format` – Test that other API endpoints maintain their expected formats. (Status: Keep).
  - `test_response_format_documentation` – Document expected response formats for key endpoints. (Status: Keep).

---

## `tests/test_api_response_format_consistency.py`

**Role:** Test API Response Format Consistency Ensures all API endpoints maintain consistent response formats between: 1. Legacy (main branch) format 2. New MCP format 3. Frontend expectations

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `has_firebase_credentials` – Check if Firebase credentials are available. (Status: Keep).
- `class TestAPIResponseFormatConsistency` – Test that all API responses maintain consistent formats. (Status: Keep).
  - `setUp` – Set up test client. (Status: Keep).
  - `test_campaigns_list_format` – Test GET /api/campaigns returns legacy array format. (Status: Keep).
  - `test_campaign_by_id_format` – Test GET /api/campaigns/<id> returns expected object format. Legacy format: { "campaign": {...}, "story": [...], "game_state": {...} } (Status: Keep).
  - `test_campaign_creation_format` – Test POST /api/campaigns returns expected object format. Expected format: { "success": true, "campaign_id": "..." } (Status: Keep).
  - `test_campaign_update_format` – Test PATCH /api/campaigns/<id> returns expected format. (Status: Keep).
  - `test_interaction_response_format` – Test POST /api/campaigns/<id>/interaction returns expected format. Expected format includes: - narrative or response field - planning_block (optional) - various other fields (Status: Keep).
  - `test_settings_get_format` – Test GET /api/settings returns expected format. (Status: Keep).
  - `test_settings_update_format` – Test POST /api/settings returns expected format. (Status: Keep).
  - `test_export_format` – Test GET /api/campaigns/<id>/export returns expected format. (Status: Keep).
  - `test_frontend_compatibility_summary` – Document all frontend expectations for API responses. (Status: Keep).
  - `tearDown` – Clean up Firebase mocks. (Status: Keep).

---

## `tests/test_api_routes.py`

**Role:** Test API routes functionality in MCP architecture. Tests API endpoints through MCP API gateway pattern.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestAPIRoutes` – Test API routes through MCP API gateway. (Status: Keep).
  - `setUp` – Set up test client for MCP architecture. (Status: Keep).
  - `test_mcp_get_campaigns_endpoint` – Test campaigns list endpoint through MCP gateway. (Status: Keep).
  - `test_mcp_get_specific_campaign_endpoint` – Test specific campaign retrieval through MCP gateway. (Status: Keep).
  - `test_mcp_get_campaigns_response` – Test campaigns endpoint response through MCP. (Status: Keep).
  - `test_mcp_get_campaigns_error_handling` – Test campaigns endpoint error handling through MCP. (Status: Keep).
  - `test_mcp_campaign_with_debug_mode` – Test campaign retrieval with debug mode through MCP. (Status: Keep).
  - `test_mcp_get_settings_endpoint` – Test settings endpoint through MCP gateway. (Status: Keep).
  - `test_mcp_post_settings_endpoint` – Test settings update endpoint through MCP gateway. (Status: Keep).
  - `test_mcp_campaign_interaction_endpoint` – Test campaign interaction endpoint through MCP gateway. (Status: Keep).
  - `test_mcp_cors_headers_handling` – Test CORS headers handling through MCP gateway. (Status: Keep).

---

## `tests/test_api_service_enhancements.py`

**Role:** TDD Tests for Flask API Service Enhancements These tests validate REAL Flask application behavior using test_client

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `client` – Flask test client fixture for real app testing (Status: Keep).
- `test_time_endpoint_available` – Test that time endpoint is available and returns proper structure (Status: Keep).
- `test_campaigns_endpoint_requires_auth` – Test that campaigns endpoint requires authentication (Status: Keep).
- `test_campaigns_endpoint_with_test_bypass` – Test campaigns endpoint with test bypass header (Status: Keep).
- `test_settings_endpoint_requires_auth` – Test that settings endpoint requires authentication (Status: Keep).
- `test_settings_endpoint_with_test_bypass` – Test settings endpoint with test bypass header (Status: Keep).
- `test_campaign_creation_requires_auth` – Test that campaign creation requires authentication (Status: Keep).
- `test_campaign_creation_with_test_bypass` – Test campaign creation with test bypass header (Status: Keep).
- `test_invalid_endpoint_returns_404` – Test that invalid API endpoints return 404 (Status: Keep).
- `test_cors_headers_present_on_api_routes` – Test that CORS headers are properly set on API routes (Status: Keep).
- `test_frontend_serving_fallback` – Test that non-API routes serve frontend (Status: Keep).
- `test_static_file_serving` – Test that static files are served from correct paths (Status: Keep).
- `test_campaign_get_with_mocked_mcp` – Test campaign retrieval with mocked MCP client (Status: Keep).
- `test_error_handling_with_invalid_json` – Test error handling with invalid JSON data (Status: Keep).

---

## `tests/test_architectural_boundary_validation.py`

**Role:** 🏗️ RED-GREEN TEST: Architectural Boundary Field Format Validation ================================================================ This test validates field format consistency across all architectural boundaries: 1. Frontend → main.py (API Gateway) 2. main.py → world_logic.py (MCP Protocol) 3. world_logic.py → Response (Business Logic) Tests BOTH the intentional translation patterns AND potential mismatches. CRITICAL ARCHITECTURAL INSIGHTS: - main.py uses "input" for frontend compatibility - world_logic.py uses "user_input" for MCP protocol - Translation layer converts between these formats - Error/Success fields are consistent across boundaries - Story fields must use "text" format for UI display

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestArchitecturalBoundaryValidation` – Comprehensive validation of field formats across architectural boundaries. (Status: Keep).
  - `test_frontend_to_main_field_constants` – RED-GREEN: Validate frontend → main.py field translation constants. (Status: Keep).
  - `test_main_to_mcp_field_constants` – RED-GREEN: Validate main.py → MCP protocol field translation constants. (Status: Keep).
  - `test_mcp_api_field_constants` – RED-GREEN: Validate MCP API layer field consistency. (Status: Keep).
  - `test_cross_boundary_field_consistency` – RED-GREEN: Validate that error/success fields are consistent across ALL boundaries. (Status: Keep).
  - `test_translation_layer_field_conversion` – RED-GREEN: Validate the intentional field translation between layers. This test confirms that the "input" → "user_input" translation is CORRECT and intentional. (Status: Keep).
  - `test_red_phase_field_mismatch_detection` – RED PHASE: Test what happens with WRONG field access patterns. This demonstrates potential bugs if field access patterns were incorrect. (Status: Keep).
  - `test_story_field_format_validation` – RED-GREEN: Validate story entry field format for UI compatibility. This test validates the fix for the original bug where story entries were created with "story" field but UI expected "text" field. (Status: Keep).
  - `test_green_phase_complete_flow_validation` – GREEN PHASE: End-to-end field format validation. This test validates the complete flow works correctly after all fixes. (Status: Keep).

---

## `tests/test_architectural_decisions.py`

**Role:** Architecture Decision Tests (ADTs) These tests verify that our architectural decisions remain valid and are actually implemented as designed. They prevent the "test name vs reality" problem and ensure architectural consistency.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestArchitecturalDecisions` – Tests that validate our architectural decisions (Status: Keep).
  - `test_adt_001_pydantic_validation_is_used` – ADT-001: Entity validation uses Pydantic implementation for robust data validation (Status: Keep).
  - `test_adt_002_only_pydantic_implementation_exists` – ADT-002: Only Pydantic implementation exists (Simple removed) (Status: Keep).
  - `test_adt_003_entity_tracking_imports_pydantic_module` – ADT-003: entity_tracking.py imports from Pydantic module (Status: Keep).
  - `test_adt_004_pydantic_validation_actually_rejects_bad_data` – ADT-004: Pydantic validation actually rejects invalid data (Status: Keep).
  - `test_adt_005_defensive_numeric_conversion_works` – ADT-005: DefensiveNumericConverter handles 'unknown' values gracefully (Status: Keep).
  - `test_adt_006_no_environment_variable_switching` – ADT-006: No environment variable switching - Pydantic is always used (Status: Keep).
- `class TestASTAnalysisEngine` – Unit tests for the AST-based architecture analysis engine (Status: Keep).
  - `setUp` – Set up test fixtures with temporary directory and test files (Status: Keep).
  - `tearDown` – Clean up temporary files (Status: Keep).
  - `test_adt_007_analyze_file_architecture_valid_python` – ADT-007: File analysis correctly analyzes valid Python files (Status: Keep).
  - `test_adt_008_analyze_file_architecture_syntax_error` – ADT-008: File analysis processes syntax error files as text (Status: Keep).
  - `test_adt_009_analyze_file_architecture_missing_file` – ADT-009: AST analysis handles missing files gracefully (Status: Keep).
  - `test_adt_010_analyze_file_architecture_empty_file` – ADT-010: AST analysis handles empty files gracefully (Status: Keep).
  - `test_adt_011_calculate_cyclomatic_complexity_simple` – ADT-011: Cyclomatic complexity calculation for simple code (Status: Keep).
  - `test_adt_012_calculate_cyclomatic_complexity_complex` – ADT-012: Cyclomatic complexity calculation for complex code (Status: Keep).
  - `test_adt_013_extract_functions_with_complexity` – ADT-013: Function extraction with complexity analysis (Status: Keep).
  - `test_adt_014_extract_import_dependencies` – ADT-014: Import dependency extraction (Status: Keep).
  - `test_adt_015_extract_classes_with_methods` – ADT-015: Class and method extraction (Status: Keep).
  - `test_adt_016_find_architectural_issues_high_complexity` – ADT-016: High complexity issue detection (Status: Keep).
  - `test_adt_017_generate_evidence_based_insights` – ADT-017: Evidence-based insights generation (Status: Keep).
  - `test_adt_018_format_analysis_for_arch_command` – ADT-018: Formatted output for /arch command integration (Status: Keep).
  - `test_adt_019_analyze_project_files_multiple_files` – ADT-019: Analysis of multiple files (Status: Keep).
  - `test_adt_020_variance_validation_different_outputs` – ADT-020: Variance validation - different files produce different analysis (Status: Keep).

---

## `tests/test_auth_mock_separation_redgreen.py`

**Role:** RED-GREEN test for AUTH_SKIP_MODE vs MOCK_SERVICES_MODE separation. This test demonstrates that: 1. Current TESTING mode bypasses production code paths (RED) 2. New separation allows testing real services with auth bypass (GREEN)

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestAuthMockSeparation` – Test that demonstrates the need for separating auth skip from mock services. (Status: Keep).
  - `test_current_mock_mode_bypasses_verification` – GREEN: MOCK_SERVICES_MODE=true bypasses verification for unit tests. (Status: Keep).
  - `test_auth_skip_with_real_services` – GREEN: AUTH_SKIP_MODE=true allows testing real services without auth. (Status: Keep).

---

## `tests/test_authenticated_comprehensive.py`

**Role:** Comprehensive Authenticated API Test Suite Tests all campaign functionality using real Firebase authentication

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class AuthenticatedTestSuite` – No class docstring present; review implementation to confirm behavior. (Status: Keep).
  - `test_server_connectivity` – Test basic server connectivity (Status: Keep).
  - `test_campaigns_endpoint` – Test campaigns endpoint without authentication (to see what error we get) (Status: Keep).
  - `test_campaign_creation_without_auth` – Test campaign creation to understand the authentication requirement (Status: Keep).
  - `test_frontend_accessibility` – Test frontend accessibility and basic functionality (Status: Keep).
  - `analyze_authentication_requirements` – Analyze what authentication is required based on API responses (Status: Keep).
  - `run_comprehensive_test_suite` – Run the complete authenticated test suite (Status: Keep).

---

## `tests/test_banned_name_prevention_v2.py`

**Role:** Test to verify that AI character generation instructions prevent banned names. This test checks behavior and structure, not exact content strings.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestBannedNamePreventionBehavior` – Test that instructions prevent AI from suggesting banned names. (Status: Keep).
  - `setUp` – Set up test paths. (Status: Keep).
  - `test_master_directive_has_prevention_behavior` – Test that master directive includes prevention behavior. (Status: Keep).
  - `test_mechanics_instruction_has_prevention_behavior` – Test that mechanics instruction includes prevention for Option 2. (Status: Keep).
  - `test_version_indicates_changes` – Test that version number reflects banned name changes. (Status: Keep).
  - `test_critical_reminders_include_naming` – Test that critical reminders section addresses naming. (Status: Keep).

---

## `tests/test_banned_names_loading.py`

**Role:** Unit tests for banned names loading functionality. Verifies that the real banned_names.md file is loaded correctly.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestBannedNamesLoading` – Test that banned names are loaded correctly from banned_names.md. (Status: Keep).
  - `test_banned_names_file_exists` – Test that the banned_names.md file exists. (Status: Keep).
  - `test_load_banned_names_returns_content` – Test that load_banned_names returns non-empty content. (Status: Keep).
  - `test_banned_names_contains_master_directive` – Test that banned names content contains the MASTER DIRECTIVE. (Status: Keep).
  - `test_banned_names_contains_all_primary_names` – Test that all 10 primary banned names are present. (Status: Keep).
  - `test_banned_names_contains_extended_names` – Test that extended banned names are present in the simplified list. (Status: Keep).
  - `test_banned_names_count_verification` – Test that the file has correct structure and name count. (Status: Keep).
  - `test_banned_names_enforcement_directive` – Test that enforcement directive is present. (Status: Keep).
  - `test_world_content_includes_banned_names` – Test that the full world content includes banned names section. (Status: Keep).

---

## `tests/test_banned_names_visibility_v2.py`

**Role:** Test to verify that the AI can identify where banned names come from. This test checks structure and behavior, not exact content strings.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestBannedNamesVisibilityBehavior` – Test that banned names are properly identified in world content. (Status: Keep).
  - `test_world_content_includes_naming_restrictions` – Test that world content includes identifiable naming restrictions. (Status: Keep).
  - `test_banned_names_loader_returns_content` – Test that the banned names loader returns non-empty content. (Status: Keep).
  - `test_world_content_structure_includes_all_sections` – Test that world content has proper structure with all expected sections. (Status: Keep).

---

## `tests/test_campaign_clicks.py`

**Role:** Tests for campaign list click functionality - TASK-005a

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestCampaignClicks` – Test campaign list click registration and navigation (Status: Keep).
  - `test_campaign_item_has_clickable_attributes` – Test that campaign items have proper data attributes for clicking (Status: Keep).
  - `test_css_classes_present` – Test that required CSS classes are defined (Status: Keep).
  - `test_javascript_click_handler_structure` – Test that JavaScript has proper click handler structure (Status: Keep).
  - `test_index_html_includes_css` – Test that index.html includes the campaign click fix CSS (Status: Keep).

---

## `tests/test_character_extraction_regex_bug.py`

**Role:** Red-Green test for character/NPC extraction regex functionality. Tests the NPC pattern matching that uses re.findall in llm_service.py to ensure the import re statement exists and works properly.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestCharacterExtractionRegex` – Test character/NPC extraction regex functionality (Status: Keep).
  - `test_re_import_exists` – RED: Test that re module is properly imported (Status: Keep).
  - `test_npc_pattern_extraction_from_prompt` – RED: Test NPC pattern extraction using re.findall (Status: Keep).
  - `test_actual_llm_service_npc_extraction` – GREEN: Test that actual llm_service code works with re patterns (Status: Keep).
  - `test_planning_block_character_creation_check` – GREEN: Test the actual re.search usage in planning block logic (Status: Keep).
  - `test_all_re_usage_in_llm_service` – GREEN: Comprehensive test of all regex usage in llm_service (Status: Keep).

---

## `tests/test_ci_firebase_init_redgreen.py`

**Role:** RED-GREEN test to reproduce CI Firebase initialization failure. This test reproduces the exact CI environment where: - MOCK_SERVICES_MODE=true (what CI sets) - TESTING is NOT set (CI doesn't set this in env vars) - world_logic.py tries to initialize Firebase and fails

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestCIFirebaseInitialization` – Test Firebase initialization behavior in CI environment. (Status: Keep).
  - `setUp` – Set up CI-like environment. (Status: Keep).
  - `test_ci_environment_firebase_initialization_failure` – RED: Reproduce the CI Firebase initialization failure. In CI: - MOCK_SERVICES_MODE=true is set - TESTING is not set in environment (only in command) - world_logic.py only checks TESTING, not MOCK_SERVICES_MODE - This causes Firebase initialization to be attempted and fail (Status: Keep).
  - `tearDown` – Restore original environment. (Status: Keep).

---

## `tests/test_claude_settings_validation.py`

**Role:** Unit tests for .claude/settings.json hook configuration validation. This test enforces the robust hook pattern to prevent system lockouts caused by environment variable dependencies. Author: Claude Code (Genesis Coder, Prime Mover) Created: 2025-08-22 Issue: Fix for PR #1410 hook environment robustness

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestClaudeSettingsValidation` – Validate .claude/settings.json hook configurations for robustness. (Status: Keep).
  - `setUp` – Set up test fixtures. (Status: Keep).
  - `test_settings_file_exists` – Test that .claude/settings.json exists. (Status: Keep).
  - `test_settings_file_valid_json` – Test that settings.json is valid JSON. (Status: Keep).
  - `test_hook_robustness_patterns` – Test that all hooks use robust patterns to prevent system lockouts. (Status: Keep).
  - `test_no_shell_injection_vulnerabilities` – Test that hook commands are not vulnerable to shell injection. (Status: Keep).
  - `test_hook_files_exist` – Test that all referenced hook files actually exist. (Status: Keep).
  - `test_consistent_pattern_usage` – Test that all hooks use consistent robust patterns. (Status: Keep).
- `class TestRobustPatternExamples` – Test robust pattern validation with specific examples. (Status: Keep).
  - `setUp` – Set up validator for testing. (Status: Keep).
  - `test_fragile_pattern_detection` – Test that fragile patterns are correctly detected. (Status: Keep).
  - `test_robust_pattern_acceptance` – Test that robust patterns are correctly accepted. (Status: Keep).

---

## `tests/test_combat_bug_green.py`

**Role:** GREEN TEST: Verify the combat AttributeError bug is fixed This test MUST PASS to confirm the bug is resolved

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestCombatBugGreen` – Test to verify the AttributeError fix works correctly (Status: Keep).
  - `test_cleanup_defeated_enemies_handles_list_combatants` – GREEN TEST: This should PASS without errors Verifies that cleanup_defeated_enemies now handles list format (Status: Keep).
  - `test_cleanup_defeated_enemies_preserves_dict_combatants` – Verify that dict format still works correctly (regression test) (Status: Keep).
  - `test_cleanup_with_complex_list_structure` – Test with more complex list structure that AI might generate (Status: Keep).

---

## `tests/test_combat_cleanup_comprehensive.py`

**Role:** Comprehensive Combat Cleanup Tests This test file contains comprehensive tests for the automatic cleanup system, including edge cases and realistic combat scenarios.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestCombatCleanupComprehensive` – Comprehensive tests for combat cleanup functionality. Tests cover various scenarios including edge cases and realistic workflows. (Status: Keep).
  - `test_automatic_cleanup_via_state_updates_hp_defeat` – Test: Enemy defeated via AI HP update should be automatically cleaned up. This test verifies the fix is working correctly. (Status: Keep).
  - `test_combat_end_with_pre_defeated_enemies` – Test: When combat ends and there are already defeated enemies, they should be cleaned up. This tests the edge case where: 1. Enemy is defeated in an earlier turn but not cleaned up 2. AI ends combat without explicitly cleaning defeated enemies 3. The automatic cleanup should catch and remove them (Status: Keep).
  - `test_multiple_enemies_defeated_same_turn` – Test: Multiple enemies defeated in the same AI response should all be cleaned up. This tests area-effect damage scenarios where multiple enemies die simultaneously. (Status: Keep).
  - `test_cleanup_without_explicit_combat_state_changes` – Test: Cleanup should trigger even when combat_state isn't explicitly in proposed_changes. This tests whether the cleanup is robust enough to detect defeated enemies even when the AI makes other types of updates (like updating turn order). (Status: Keep).

---

## `tests/test_common.py`

**Role:** Common test utilities shared across test files.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `has_firebase_credentials` – Check if Firebase credentials are available. Note: End2end tests use complete mocking and don't require real credentials. This function returns False to ensure tests use mocked services. (Status: Keep).

---

## `tests/test_complete_combined_approach.py`

**Role:** Test the complete Combined approach (Structured Generation + Validation) Demonstrates the full implementation of Milestone 1

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestCompleteCombinedApproach` – Test the complete Combined approach implementation (Status: Keep).
  - `setUp` – Set up test scenario (Status: Keep).
  - `test_step1_structured_generation_prompt_creation` – Step 1: Create structured generation prompt with entity manifest (Status: Keep).
  - `test_step2_structured_response_parsing` – Step 2: Parse structured JSON response from LLM (Status: Keep).
  - `test_step3_schema_validation` – Step 3: Validate structured response against expected schema (Status: Keep).
  - `test_step4_narrative_sync_validation` – Step 4: Additional validation with NarrativeSyncValidator (Status: Keep).
  - `test_complete_combined_approach_integration` – Test complete Combined approach integration flow (Status: Keep).
  - `test_failure_case_handling` – Test how the system handles failure cases (Status: Keep).

---

## `tests/test_constants.py`

**Role:** No module docstring; review code to confirm responsibilities.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestConstants` – Test constants module values and structure. (Status: Keep).
  - `test_actor_constants` – Test actor constants are properly defined. (Status: Keep).
  - `test_interaction_mode_constants` – Test interaction mode constants. (Status: Keep).
  - `test_dictionary_key_constants` – Test dictionary key constants. (Status: Keep).
  - `test_export_format_constants` – Test export format constants. (Status: Keep).
  - `test_prompt_filename_constants` – Test prompt filename constants. (Status: Keep).
  - `test_prompt_type_constants` – Test prompt type constants. (Status: Keep).
  - `test_prompt_path_constants` – Test prompt path constants are properly constructed. (Status: Keep).
  - `test_constants_are_strings` – Test that all constants are strings (no accidental None values). (Status: Keep).
  - `test_constants_immutability_pattern` – Test that constants follow immutability patterns (uppercase naming). (Status: Keep).
  - `test_attribute_system_constants` – Test that attribute system constants are defined correctly. (Status: Keep).
  - `test_attribute_lists` – Test that attribute lists are defined correctly. (Status: Keep).
  - `test_helper_functions` – Test the attribute system helper functions. (Status: Keep).
  - `test_character_creation_constants` – Test character creation constants. (Status: Keep).
  - `test_mode_switching_constants` – Test mode switching detection constants. (Status: Keep).
  - `test_user_selectable_prompts` – Test user selectable prompts list. (Status: Keep).

---

## `tests/test_context_truncation.py`

**Role:** No module docstring; review code to confirm responsibilities.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestContextTruncation` – No class docstring present; review implementation to confirm behavior. (Status: Keep).
  - `setUp` – This method runs before each test. We can override the constants for predictable testing. (Status: Keep).
  - `test_no_truncation_when_under_char_limit` – Verify that if the context is UNDER the character limit, no truncation occurs (new behavior). (Status: Keep).
  - `test_truncates_when_few_turns_over_char_limit` – Verify that when there are few turns but still over char limit, it takes the most recent turns that fit the turn limits. (Status: Keep).
  - `test_does_not_truncate_if_within_all_limits` – Verify that no truncation happens if the context is within all limits. (Status: Keep).

---

## `tests/test_data_integrity.py`

**Role:** Data Integrity Test Suite Tests to catch data corruption bugs like NPCs being converted to strings, state inconsistencies, and other data structure violations.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `update_state_with_changes_test` – Test version of update_state_with_changes without Firebase dependencies. (Status: Keep).
- `class TestDataIntegrity` – Test suite for data integrity validation. (Status: Keep).
  - `setUp` – Set up test fixtures. (Status: Keep).
  - `test_npc_data_integrity_validation` – Test that NPC data validation catches corruption. (Status: Keep).
  - `test_state_update_preserves_npc_structure` – Test that state updates don't corrupt NPC data structure. (Status: Keep).
  - `test_delete_token_processing` – Test that __DELETE__ tokens work without corrupting other data. (Status: Keep).
  - `test_mission_processing_doesnt_corrupt_npcs` – Test that mission processing safely handles different data types. (Status: Keep).
  - `test_combat_cleanup_preserves_data_types` – Test that combat cleanup doesn't corrupt NPC data types. (Status: Keep).
  - `test_mixed_mission_data_handling` – Test handling of missions that might contain mixed data types. (Status: Keep).
  - `test_state_consistency_after_multiple_updates` – Test that multiple state updates maintain data integrity. (Status: Keep).
  - `test_npc_string_update_preservation` – Test the specific bug where updating an NPC with a string value corrupts the entire NPC dictionary structure. This test ensures that string updates to NPCs are handled intelligently by preserving the dictionary structure and treating strings as status updates. (Status: Keep).
  - `test_multiple_npc_string_updates_isolation` – Test that string updates to one NPC don't corrupt other NPCs. (Status: Keep).
  - `test_string_overwrite_on_npc_dict_is_converted` – CRITICAL: Ensures that a string update to an NPC is converted to status field. This tests the smart conversion that preserves NPC data while updating status. (Status: Keep).
  - `test_list_overwrite_on_missions_is_converted` – CRITICAL: Ensures that dictionary updates to active_missions are converted to list appends. This tests the safeguard that prevents AI from corrupting the mission list. (Status: Keep).

---

## `tests/test_decorators.py`

**Role:** No module docstring; review code to confirm responsibilities.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestLogExceptionsDecorator` – Test the log_exceptions decorator. (Status: Keep).
  - `setUp` – Set up test logging environment. (Status: Keep).
  - `tearDown` – Clean up test logging environment. (Status: Keep).
  - `test_decorator_preserves_function_metadata` – Test that decorator preserves original function metadata. (Status: Keep).
  - `test_decorator_successful_execution` – Test decorator with successful function execution. (Status: Keep).
  - `test_decorator_logs_exception_and_reraises` – Test that decorator logs exceptions and re-raises them. (Status: Keep).
  - `test_decorator_logs_function_arguments` – Test that decorator logs function arguments in error messages. (Status: Keep).
  - `test_decorator_with_different_exception_types` – Test decorator behavior with different exception types. (Status: Keep).
  - `test_decorator_preserves_return_values` – Test that decorator preserves various return value types. (Status: Keep).
  - `test_decorator_with_complex_arguments` – Test decorator with complex argument types. (Status: Keep).
  - `test_decorator_uses_module_logger` – Test that decorator uses logging_util.error for exception logging. (Status: Keep).
  - `test_nested_decorated_functions` – Test behavior when decorated functions call other decorated functions. (Status: Keep).

---

## `tests/test_defensive_numeric_converter.py`

**Role:** Test cases for DefensiveNumericConverter

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestDefensiveNumericConverter` – Test DefensiveNumericConverter functionality (Status: Keep).
  - `test_hp_unknown_values` – Test HP fields with unknown values (Status: Keep).
  - `test_stats_unknown_values` – Test ability score fields with unknown values (Status: Keep).
  - `test_level_unknown_values` – Test level field with unknown values (Status: Keep).
  - `test_non_hp_defaults` – Test non-HP field defaults (gold, initiative, etc.) (Status: Keep).
  - `test_numeric_string_conversion` – Test valid numeric strings get converted properly (Status: Keep).
  - `test_range_validation` – Test range validation for different field types (Status: Keep).
  - `test_non_numeric_fields_unchanged` – Test that non-numeric fields are not converted (Status: Keep).
  - `test_dict_conversion` – Test dictionary conversion functionality (Status: Keep).
- `class TestEntitiesWithDefensiveConverter` – Test entity classes using DefensiveNumericConverter (Status: Keep).
  - `test_health_status_with_unknown_values` – Test HealthStatus with various unknown values (Status: Keep).
  - `test_stats_with_unknown_values` – Test Stats with various unknown values (Status: Keep).
  - `test_character_with_unknown_level` – Test Character with unknown level (Status: Keep).
  - `test_hp_validation_after_conversion` – Test that HP validation works after defensive conversion (Status: Keep).

---

## `tests/test_delete_fix.py`

**Role:** Simple test to verify __DELETE__ token processing works correctly.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `update_state_with_changes_simplified` – Simplified version of the function for testing. (Status: Keep).
- `test_delete_token_processing` – Test that __DELETE__ tokens work correctly. (Status: Keep).

---

## `tests/test_delete_token_comprehensive.py`

**Role:** Comprehensive test for __DELETE__ token processing in firestore_service. Tests the actual implementation, not a simplified version.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestDeleteTokenProcessing` – Test DELETE token handling in the actual update_state_with_changes function. (Status: Keep).
  - `setUp` – Set up test data. (Status: Keep).
  - `tearDown` – Clean up. (Status: Keep).
  - `test_nested_npc_deletion` – Test deleting NPCs from nested npc_data structure (most common case). (Status: Keep).
  - `test_top_level_deletion` – Test deleting top-level keys. (Status: Keep).
  - `test_delete_non_dict_value` – Test deleting keys that have non-dict values (strings, numbers, etc). (Status: Keep).
  - `test_deeply_nested_deletion` – Test deletion in deeply nested structures. (Status: Keep).
  - `test_mixed_updates_and_deletions` – Test mixing regular updates with deletions in same operation. (Status: Keep).

---

## `tests/test_deployment_build.py`

**Role:** Test to verify world files are accessible in deployment context. This simulates the Docker build environment to catch deployment issues early.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestDeploymentBuild` – Test deployment build context and file accessibility. (Status: Keep).
  - `setUp` – Create a temporary directory structure mimicking deployment. (Status: Keep).
  - `tearDown` – Clean up temporary directory. (Status: Keep).
  - `test_world_files_not_accessible_without_copy` – Test that world files are NOT accessible without copying (reproduces the bug). (Status: Keep).
  - `test_world_files_accessible_after_copy` – Test that world files ARE accessible after copying (verifies the fix). (Status: Keep).
  - `test_deploy_script_simulation` – Simulate the deploy.sh script behavior. (Status: Keep).

---

## `tests/test_documentation_performance.py`

**Role:** Test documentation file sizes and performance to prevent API timeouts.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `get_project_root` – Get the project root directory. (Status: Keep).
- `check_file_size` – Check if a file is within acceptable size limits. (Status: Keep).
- `test_file_sizes` – Test that all documentation files are within acceptable size limits. (Status: Keep).
- `check_read_performance` – Check how long it takes to read a file. (Status: Keep).
- `test_read_performance` – Test that all documentation files can be read within acceptable time. (Status: Keep).
- `simulate_api_read` – Simulate API-style chunked reading. Args: filepath: Path to the file to read chunk_lines: Number of lines per chunk (default: 2000) Returns: List of chunk information dictionaries (Status: Keep).
- `main` – Run all documentation performance tests. (Status: Keep).

---

## `tests/test_dual_pass_generator.py`

**Role:** Unit tests for Dual-Pass Generation System (Option 7) Tests dual-pass narrative generation with entity verification.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestDualPassGenerator` – No class docstring present; review implementation to confirm behavior. (Status: Keep).
  - `setUp` – No docstring present; review implementation to confirm behavior. (Status: Keep).
  - `test_build_injection_templates` – Test that injection templates are properly built via EntityValidator (Status: Keep).
  - `test_generate_with_dual_pass_success_first_pass` – Test dual-pass generation when first pass succeeds (Status: Keep).
  - `test_generate_with_dual_pass_requires_second_pass` – Test dual-pass generation when second pass is needed (Status: Keep).
  - `test_create_injection_prompt` – Test injection prompt creation for second pass (Status: Keep).
  - `test_combine_narratives_complete_rewrite` – Test narrative combination when second pass is complete rewrite (Status: Keep).
  - `test_combine_narratives_append_enhancement` – Test narrative combination when second pass is enhancement (Status: Keep).
  - `test_create_entity_injection_snippet_cassian` – Test entity injection snippet creation for specific entities (Status: Keep).
  - `test_create_entity_injection_snippet_generic` – Test entity injection snippet creation for generic entities (Status: Keep).
- `class TestAdaptiveEntityInjector` – No class docstring present; review implementation to confirm behavior. (Status: Keep).
  - `setUp` – No docstring present; review implementation to confirm behavior. (Status: Keep).
  - `test_choose_injection_strategy_dialogue` – Test strategy selection for dialogue-heavy narratives (Status: Keep).
  - `test_choose_injection_strategy_action` – Test strategy selection for action-heavy narratives (Status: Keep).
  - `test_choose_injection_strategy_emotional` – Test strategy selection for emotional narratives (Status: Keep).
  - `test_choose_injection_strategy_default` – Test default strategy selection (Status: Keep).
  - `test_inject_via_dialogue` – Test dialogue-based entity injection (Status: Keep).
  - `test_inject_via_action` – Test action-based entity injection (Status: Keep).
  - `test_inject_via_presence` – Test presence-based entity injection (Status: Keep).
  - `test_inject_via_reaction` – Test reaction-based entity injection (Status: Keep).
  - `test_inject_entities_adaptively` – Test full adaptive injection process (Status: Keep).
- `class TestDataClasses` – No class docstring present; review implementation to confirm behavior. (Status: Keep).
  - `test_generation_pass_creation` – Test GenerationPass dataclass creation (Status: Keep).
  - `test_dual_pass_result_creation` – Test DualPassResult dataclass creation (Status: Keep).
- `class TestGlobalInstances` – No class docstring present; review implementation to confirm behavior. (Status: Keep).
  - `test_global_dual_pass_generator_exists` – Test that global dual pass generator instance exists (Status: Keep).
  - `test_global_adaptive_injector_exists` – Test that global adaptive injector instance exists (Status: Keep).

---

## `tests/test_end2end/run_end2end_tests.py`

**Role:** Runner script for end-to-end integration tests. Run this from the project root with the virtual environment activated. Usage: python mvp_site/tests/run_end2end_tests.py

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `run_tests` – Run all end-to-end integration tests. (Status: Keep).

---

## `tests/test_end2end/test_continue_story_end2end.py`

**Role:** End-to-end integration test for continuing a story. Only mocks external services (Gemini API and Firestore DB) at the lowest level. Tests the full flow from API endpoint through all service layers.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestContinueStoryEnd2End` – Test continuing a story through the full application stack. (Status: Keep).
  - `setUp` – Set up test client. (Status: Keep).
  - `test_continue_story_success` – Test successful story continuation using fake services. (Status: Keep).
  - `test_continue_story_campaign_not_found` – Test continuing story with non-existent campaign. (Status: Keep).

---

## `tests/test_end2end/test_create_campaign_end2end.py`

**Role:** End-to-end integration test for creating a campaign. Only mocks external services (Gemini API and Firestore DB) at the lowest level. Tests the full flow from API endpoint through all service layers.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestCreateCampaignEnd2End` – Test creating a campaign through the full application stack. (Status: Keep).
  - `setUp` – Set up test client. (Status: Keep).
  - `test_create_campaign_success` – Test successful campaign creation using fake services. (Status: Keep).
  - `test_create_campaign_gemini_error` – Test campaign creation with Gemini service error. (Status: Keep).

---

## `tests/test_end2end/test_debug_mode_end2end.py`

**Role:** End-to-end integration test for debug mode functionality. Tests the full flow from settings API to UI state consistency. Only mocks external services (Gemini API and Firestore DB) at the lowest level.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestDebugModeEnd2End` – Test debug mode functionality through the full application stack. (Status: Keep).
  - `setUp` – Set up test client and test data. (Status: Keep).
  - `test_turn_on_debug_mode` – Test Case 1: Turn on debug mode via settings API. (Status: Keep).
  - `test_turn_off_debug_mode` – Test Case 2: Turn off debug mode via settings API. (Status: Keep).
  - `test_ui_state_debug_mode_on` – Test Case 3: UI receives correct state when debug mode is ON. (Status: Keep).
  - `test_ui_state_debug_mode_off` – Test Case 4: UI receives correct state when debug mode is OFF. (Status: Keep).
  - `test_interaction_respects_debug_mode_setting` – Test that game interactions respect the user's debug mode setting. (Status: Keep).
  - `test_debug_mode_persistence_across_requests` – Test that debug mode setting persists across multiple requests. (Status: Keep).
  - `test_json_input_validation_in_debug_context` – Test JSON input validation in debug mode context. (Status: Keep).
  - `test_json_input_validation_debug_mode_toggling` – Test JSON input validation when debug mode is toggled. (Status: Keep).
  - `test_backend_strips_game_state_fields_when_debug_off` – Test that backend strips game state fields (entities, state_updates, debug_info) when debug mode is OFF. (Status: Keep).
  - `test_debug_mode_filtering_unit_integration` – Restored from test_debug_filtering_unit.py - integration test for debug filtering (Status: Keep).
  - `test_state_updates_sequence_id_debug_filtering_integration` – Restored from test_debug_filtering_unit.py - character mode sequence ID filtering test (Status: Keep).
  - `test_pr1150_debug_mode_standard_behavior` – Test for PR #1150: Standard debug mode behavior where debug_mode=True shows MORE information This test validates that debug mode follows standard behavior where debug_mode=True provides additional debugging information including state_updates. (Status: Keep).
  - `test_pr1150_character_mode_sequence_tracking_debug_respect` – Test for PR #1150: Character mode sequence tracking with standard debug behavior This validates the second location in world_logic.py where state_updates is conditionally added for character mode sequence tracking in debug mode. (Status: Keep).
  - `test_character_mode_preserves_original_state_changes_during_sequence_merge` – Test that would have caught the character mode state merge bug. Verifies that original Gemini state changes are preserved when merged with story sequence tracking update in character mode. This test ensures that changing the data source from unified_response to response doesn't break the merge functionality. (Status: Keep).

---

## `tests/test_end2end/test_mcp_error_handling_end2end.py`

**Role:** End-to-end integration test for MCP error handling and translation. Tests error propagation from world_logic → MCPClient → Flask HTTP responses. Only mocks external services (Firestore DB and Gemini API) at the lowest level.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `has_firebase_credentials` – Check if Firebase credentials are available. Note: End2end tests use complete mocking and don't require real credentials. This function returns False to ensure tests use mocked services. (Status: Keep).
- `class TestMCPErrorHandlingEnd2End` – Test MCP error handling and translation through the full application stack. (Status: Keep).
  - `setUp` – Set up test client and test data. (Status: Keep).
  - `test_mcp_campaign_not_found_error` – Test MCP error handling for non-existent campaign. (Status: Keep).
  - `test_mcp_missing_user_id_error` – Test MCP error handling for missing authentication. (Status: Keep).
  - `test_mcp_invalid_request_format_error` – Test MCP error handling for invalid request format. (Status: Keep).
  - `test_mcp_interaction_missing_campaign_error` – Test MCP error handling for interaction with non-existent campaign. (Status: Keep).
  - `test_mcp_interaction_invalid_mode_error` – Test MCP error handling for invalid interaction mode. (Status: Keep).
  - `test_mcp_update_campaign_not_found_error` – Test MCP error handling for updating non-existent campaign. (Status: Keep).
  - `test_mcp_export_campaign_not_found_error` – Test MCP error handling for exporting non-existent campaign. (Status: Keep).
  - `test_mcp_export_invalid_format_error` – Test MCP error handling for invalid export format. (Status: Keep).
  - `test_mcp_http_method_not_allowed_error` – Test MCP error handling for unsupported HTTP methods. (Status: Keep).
  - `test_mcp_firestore_connection_error_simulation` – Test MCP error handling when Firestore connection fails. (Status: Keep).
  - `test_mcp_missing_content_type_error` – Test MCP error handling for missing Content-Type header. (Status: Keep).
  - `test_mcp_unauthorized_campaign_access_error` – Test MCP error handling for accessing another user's campaign. (Status: Keep).
  - `test_mcp_error_response_format_consistency` – Test that all MCP error responses have consistent format. (Status: Keep).

---

## `tests/test_end2end/test_mcp_integration_comprehensive.py`

**Role:** Comprehensive MCP Integration End-to-End Tests Tests the complete MCP architecture workflow: Flask App → MCPClient → MCP Server → World Logic → Response Chain This supplements the existing Flask-only end2end tests with true MCP server integration.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestMCPIntegrationComprehensive` – Comprehensive end-to-end tests for MCP architecture integration. (Status: Keep).
  - `setUpClass` – Set up MCP server for all tests. (Status: Keep).
  - `tearDownClass` – Clean up MCP server after all tests. (Status: Keep).
  - `setUp` – Set up test client and data. (Status: Keep).
  - `test_mcp_flask_integration_complete_workflow` – Test complete workflow: Flask → MCP → World Logic → Response. (Status: Keep).
  - `test_mcp_direct_server_communication` – Test direct MCP server communication if available. (Status: Keep).
  - `test_mcp_error_handling_and_fallback` – Test MCP error handling and fallback behaviors. (Status: Keep).
  - `test_mcp_interaction_workflow` – Test user interaction workflow through MCP. (Status: Keep).
  - `test_mcp_concurrent_requests` – Test MCP handling of concurrent requests. (Status: Keep).
  - `test_mcp_event_loop_performance_bug` – Test that MCP does NOT create new event loops per request (RED test - should fail initially). (Status: Keep).
  - `test_mcp_production_traceback_security_bug` – Test that MCP does NOT expose tracebacks in production mode (RED test - should fail initially). (Status: Keep).
  - `test_mcp_authentication_integration` – Test authentication handling through MCP architecture. (Status: Keep).
  - `test_mcp_settings_integration` – Test settings management through MCP. (Status: Keep).
  - `test_mcp_export_functionality` – Test campaign export through MCP. (Status: Keep).
  - `test_mcp_god_mode_commands` – Test God Mode commands through MCP architecture. (Status: Keep).
  - `test_mcp_campaign_update_patch_endpoint` – Test campaign updates via PATCH endpoint through MCP. (Status: Keep).

---

## `tests/test_end2end/test_mcp_protocol_end2end.py`

**Role:** End-to-end integration test for MCP JSON-RPC protocol communication. Tests the complete MCP protocol flow: Flask → MCPClient → world_logic → response. Only mocks external services (Firestore DB and Gemini API) at the lowest level.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestMCPProtocolEnd2End` – Test MCP JSON-RPC protocol communication through the full application stack. (Status: Keep).
  - `setUp` – Set up test client and mocks. (Status: Keep).
  - `test_mcp_get_campaigns_list_protocol` – Test MCP protocol for get_campaigns_list_unified tool. (Status: Keep).
  - `test_mcp_create_campaign_protocol` – Test MCP protocol for create_campaign_unified tool. (Status: Keep).
  - `test_mcp_process_action_protocol` – Test MCP protocol for process_action_unified tool. (Status: Keep).
  - `test_mcp_get_campaign_state_protocol` – Test MCP protocol for get_campaign_state_unified tool. (Status: Keep).
  - `test_mcp_update_campaign_protocol` – Test MCP protocol for update_campaign_unified tool. (Status: Keep).
  - `test_mcp_export_campaign_protocol` – Test MCP protocol for export_campaign_unified tool. (Status: Keep).
  - `test_mcp_user_settings_protocol` – Test MCP protocol for user settings get/update tools. (Status: Keep).
  - `test_mcp_protocol_error_handling` – Test MCP protocol error handling for invalid requests. (Status: Keep).
  - `test_mcp_protocol_authentication_flow` – Test MCP protocol with authentication scenarios. (Status: Keep).

---

## `tests/test_end2end/test_visit_campaign_end2end.py`

**Role:** End-to-end integration test for visiting an existing campaign - FIXED VERSION. Only mocks external services (Firestore DB). Tests the full flow from API endpoint through all service layers.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `has_firebase_credentials` – Check if Firebase credentials are available. Note: End2end tests use complete mocking and don't require real credentials. This function returns False to ensure tests use mocked services. (Status: Keep).
- `class TestVisitCampaignEnd2End` – Test visiting/reading an existing campaign through the full application stack. (Status: Keep).
  - `setUp` – Set up test client and mocks. (Status: Keep).
  - `test_visit_campaign_success` – Test successfully visiting an existing campaign. (Status: Keep).
  - `test_visit_campaign_not_found` – Test visiting a non-existent campaign. (Status: Keep).
  - `test_visit_campaign_unauthorized` – Test visiting a campaign owned by another user. (Status: Keep).
  - `test_json_input_validation_in_campaign_context` – Test JSON input validation in campaign visit context. (Status: Keep).
  - `test_json_input_validation_error_handling` – Test JSON input validation error handling in end2end context. (Status: Keep).

---

## `tests/test_entities_pydantic_integration.py`

**Role:** Test enhanced Pydantic entities with integrated fields from entities_simple.py and game_state_instruction.md

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestPydanticEntityIntegration` – Test comprehensive Pydantic entity integration (Status: Keep).
  - `setUp` – Set up common test data (Status: Keep).
  - `test_npc_gender_validation_mandatory` – Test that gender is mandatory for NPCs (critical for narrative consistency) (Status: Keep).
  - `test_npc_gender_validation_valid` – Test valid gender values for NPCs (Status: Keep).
  - `test_npc_creative_gender_accepted` – Test that creative gender values are accepted (updated for permissive validation) (Status: Keep).
  - `test_pc_gender_optional` – Test that gender is optional for PCs (Status: Keep).
  - `test_age_validation_fantasy_ranges` – Test age validation with fantasy-appropriate ranges (Status: Keep).
  - `test_age_validation_invalid_ranges` – Test age validation rejects invalid ranges (Status: Keep).
  - `test_mbti_validation` – Test MBTI personality type validation (Status: Keep).
  - `test_alignment_validation` – Test D&D alignment validation (Status: Keep).
  - `test_dnd_fundamentals_integration` – Test D&D fundamental fields integration (Status: Keep).
  - `test_defensive_numeric_conversion_stats` – Test defensive numeric conversion for stats (Status: Keep).
  - `test_defensive_numeric_conversion_health` – Test defensive numeric conversion for health values (Status: Keep).
  - `test_npc_creative_gender_values` – Test that creative gender values are now accepted (Status: Keep).
  - `test_npc_invalid_gender_types_still_fail` – Test that non-string gender values still fail validation (Status: Keep).
  - `test_creative_alignment_values` – Test that creative alignment values are accepted (Status: Keep).
  - `test_creative_mbti_values` – Test that creative personality descriptions are accepted (Status: Keep).
  - `test_comprehensive_npc_creation` – Test creating a comprehensive NPC with all enhanced fields (Status: Keep).
  - `test_backward_compatibility` – Test that existing NPC creation still works (backward compatibility) (Status: Keep).

---

## `tests/test_entity_classes.py`

**Role:** Unit tests for entity schema classes

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestPydanticValidation` – Test Pydantic validation functionality (Status: Keep).
  - `test_entity_id_validation` – Test entity ID validation in Pydantic models (Status: Keep).
  - `test_pydantic_field_validation` – Test Pydantic field validation with defensive conversion (Status: Keep).
- `class TestStats` – Test Stats class functionality (Status: Keep).
  - `test_stats_default_values` – Test Stats with default values (Status: Keep).
  - `test_stats_custom_values` – Test Stats with custom values (Status: Keep).
  - `test_stats_with_string_values` – Test Stats with string numeric values (Status: Keep).
  - `test_stats_with_unknown_values` – Test Stats handles unknown values gracefully (Status: Keep).
  - `test_stats_range_clamping` – Test Stats clamps values to valid range (Status: Keep).
- `class TestHealthStatus` – Test HealthStatus class functionality (Status: Keep).
  - `test_health_status_basic` – Test basic HealthStatus creation (Status: Keep).
  - `test_health_status_with_conditions` – Test HealthStatus with conditions (Status: Keep).
  - `test_health_status_hp_validation` – Test HP validation - should reject hp > hp_max (Status: Keep).
  - `test_health_status_with_unknown_values` – Test HealthStatus with unknown values (Status: Keep).
  - `test_health_status_negative_temp_hp` – Test negative temp_hp gets converted to 0 (Status: Keep).
- `class TestLocation` – Test Location class functionality (Status: Keep).
  - `test_location_basic` – Test basic Location creation (Status: Keep).
  - `test_location_with_all_fields` – Test Location with all optional fields (Status: Keep).
  - `test_location_invalid_id` – Test Location with invalid entity ID (Status: Keep).
- `class TestCharacter` – Test Character class functionality (Status: Keep).
  - `setUp` – Set up test data (Status: Keep).
  - `test_character_basic_pc` – Test basic Player Character creation (Status: Keep).
  - `test_character_basic_npc` – Test basic NPC creation (Status: Keep).
  - `test_character_with_all_fields` – Test Character with all optional fields (Status: Keep).
  - `test_character_invalid_entity_id` – Test Character with invalid entity ID (Status: Keep).
  - `test_character_invalid_location_id` – Test Character with invalid location ID (Status: Keep).
  - `test_character_with_unknown_level` – Test Character handles unknown level gracefully (Status: Keep).
  - `test_character_default_stats` – Test Character creates default Stats when none provided (Status: Keep).

---

## `tests/test_entity_id_special_chars.py`

**Role:** Test entity ID validation with special characters - verifies fix for apostrophe bug

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestEntityIDSpecialCharacters` – Test that entity IDs handle special characters properly (Status: Keep).
  - `test_sanitize_entity_name_for_id` – Test the sanitization function handles all special characters (Status: Keep).
  - `test_npc_with_apostrophe_name` – Test creating NPC with apostrophe in name (the original bug case) (Status: Keep).
  - `test_entity_id_validation_patterns` – Test that entity ID patterns reject invalid IDs (Status: Keep).
  - `test_create_from_game_state_with_special_chars` – Test the full pipeline with create_from_game_state (Status: Keep).
  - `test_edge_cases` – Test edge cases for entity ID generation (Status: Keep).

---

## `tests/test_entity_instructions.py`

**Role:** Unit tests for Enhanced Explicit Entity Instructions (Option 5 Enhanced) Tests entity instruction generation and enforcement checking.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestEntityInstructionGenerator` – No class docstring present; review implementation to confirm behavior. (Status: Keep).
  - `setUp` – No docstring present; review implementation to confirm behavior. (Status: Keep).
  - `test_build_instruction_templates` – Test that instruction templates are properly built (Status: Keep).
  - `test_build_entity_priorities` – Test that entity priorities are properly configured (Status: Keep).
  - `test_generate_entity_instructions_empty_entities` – Test instruction generation with empty entity list (Status: Keep).
  - `test_generate_entity_instructions_basic` – Test basic entity instruction generation (Status: Keep).
  - `test_generate_entity_instructions_with_location` – Test entity instruction generation with location (Status: Keep).
  - `test_create_entity_instruction_player_character` – Test entity instruction creation for player characters (Status: Keep).
  - `test_create_entity_instruction_npc_referenced` – Test entity instruction creation for referenced NPCs (Status: Keep).
  - `test_create_entity_instruction_location_owner` – Test entity instruction creation for location owners (Status: Keep).
  - `test_create_entity_instruction_background` – Test entity instruction creation for background entities (Status: Keep).
  - `test_create_entity_instruction_cassian_emotional` – Test special Cassian emotional handling (Status: Keep).
  - `test_is_player_character` – Test player character detection (Status: Keep).
  - `test_is_location_owner_valerius` – Test location owner detection for Valerius (Status: Keep).
  - `test_is_location_owner_cressida` – Test location owner detection for Lady Cressida (Status: Keep).
  - `test_create_location_specific_instructions` – Test location-specific instruction generation (Status: Keep).
  - `test_create_location_specific_instructions_valerius_study` – Test location-specific instructions for Valerius's study (Status: Keep).
- `class TestEntityEnforcementChecker` – No class docstring present; review implementation to confirm behavior. (Status: Keep).
  - `setUp` – No docstring present; review implementation to confirm behavior. (Status: Keep).
  - `test_build_compliance_patterns` – Test that compliance patterns are properly built (Status: Keep).
  - `test_check_instruction_compliance_success` – Test successful instruction compliance checking (Status: Keep).
  - `test_check_instruction_compliance_failure` – Test failed instruction compliance checking (Status: Keep).
  - `test_check_entity_compliance_present_with_dialogue` – Test entity compliance detection with dialogue (Status: Keep).
  - `test_check_entity_compliance_present_with_action` – Test entity compliance detection with action (Status: Keep).
  - `test_check_entity_compliance_not_present` – Test entity compliance when entity is not present (Status: Keep).
  - `test_check_entity_compliance_multiple_mentions` – Test entity compliance with multiple mentions (Status: Keep).
- `class TestEntityInstructionDataClass` – No class docstring present; review implementation to confirm behavior. (Status: Keep).
  - `test_entity_instruction_creation` – Test EntityInstruction dataclass creation (Status: Keep).
- `class TestGlobalInstances` – No class docstring present; review implementation to confirm behavior. (Status: Keep).
  - `test_global_entity_instruction_generator_exists` – Test that global entity instruction generator instance exists (Status: Keep).
  - `test_global_entity_enforcement_checker_exists` – Test that global entity enforcement checker instance exists (Status: Keep).

---

## `tests/test_entity_preloader.py`

**Role:** Unit tests for Entity Pre-Loading System (Option 3) Tests entity manifest generation and preload text creation.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestEntityPreloader` – No class docstring present; review implementation to confirm behavior. (Status: Keep).
  - `setUp` – No docstring present; review implementation to confirm behavior. (Status: Keep).
  - `test_generate_entity_manifest_caching` – Test that entity manifest generation uses caching properly (Status: Keep).
  - `test_create_entity_preload_text_basic` – Test basic entity preload text generation (Status: Keep).
  - `test_create_entity_preload_text_with_location` – Test entity preload text with location-specific entities (Status: Keep).
  - `test_get_entity_count` – Test entity counting functionality (Status: Keep).
  - `test_get_location_entities_throne_room` – Test location entity detection for throne room (Status: Keep).
  - `test_clear_cache` – Test cache clearing functionality (Status: Keep).
- `class TestLocationEntityEnforcer` – No class docstring present; review implementation to confirm behavior. (Status: Keep).
  - `setUp` – No docstring present; review implementation to confirm behavior. (Status: Keep).
  - `test_get_required_entities_valerius_study` – Test location rules for Valerius's study (Status: Keep).
  - `test_get_required_entities_cressida_chambers` – Test location rules for Lady Cressida's chambers (Status: Keep).
  - `test_validate_location_entities_success` – Test successful location entity validation (Status: Keep).
  - `test_validate_location_entities_failure` – Test location entity validation with no rules (Status: Keep).
  - `test_generate_location_enforcement_text` – Test location enforcement text generation (Status: Keep).
- `class TestGlobalInstances` – No class docstring present; review implementation to confirm behavior. (Status: Keep).
  - `test_global_entity_preloader_exists` – Test that global entity preloader instance exists (Status: Keep).
  - `test_global_location_enforcer_exists` – Test that global location enforcer instance exists (Status: Keep).

---

## `tests/test_entity_tracking.py`

**Role:** Test script for entity tracking production implementation

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestEntityTracking` – Test entity tracking components (Status: Keep).
  - `test_entity_id_format_standardization` – Test that entity IDs follow underscore format like 'pc_name_001' (Status: Keep).
  - `test_existing_string_ids_preserved` – Test that existing string_ids from game state are preserved (Status: Keep).
  - `setUp` – Set up test data (Status: Keep).
  - `test_scene_manifest_creation` – Test SceneManifest creation from game state (Status: Keep).
  - `test_expected_entities_filtering` – Test that expected entities correctly filters visible, conscious entities (Status: Keep).
  - `test_manifest_prompt_format` – Test manifest to prompt format conversion (Status: Keep).
  - `test_narrative_sync_validator` – Test NarrativeSyncValidator functionality (Status: Keep).
  - `test_validator_presence_detection` – Test validator's presence detection logic (REFACTORED: uses EntityValidator) (Status: Keep).
  - `test_integration_flow` – Test the complete entity tracking flow (Status: Keep).
  - `test_get_validation_info` – Test get_validation_info function returns correct information. (Status: Keep).
  - `test_unknown_entity_filtering_comprehensive` – Test comprehensive Unknown entity filtering across all validators (Status: Keep).
  - `test_entity_validator_comprehensive_validation` – Test EntityValidator's comprehensive validation method (Status: Keep).
  - `test_entity_presence_type_detection` – Test EntityPresenceType detection in EntityValidator (Status: Keep).
  - `test_physical_state_extraction` – Test physical state extraction from EntityValidator (Status: Keep).
  - `test_scene_transition_detection` – Test scene transition detection from EntityValidator (Status: Keep).
  - `test_injection_template_creation` – Test entity injection template creation (Status: Keep).
  - `test_narrative_sync_validator_delegation` – Test that NarrativeSyncValidator properly delegates to EntityValidator (Status: Keep).
  - `test_dual_pass_generator_integration` – Test DualPassGenerator uses EntityValidator properly (Status: Keep).
  - `test_validation_result_compatibility` – Test ValidationResult supports both old and new interfaces (Status: Keep).
  - `test_multiple_unknown_entities` – Test filtering multiple Unknown entities and variations (Status: Keep).
  - `test_edge_cases_and_robustness` – Test edge cases for robustness (Status: Keep).
  - `test_end_to_end_missing_entity_red_green_workflow` – End-to-end RED-GREEN test: Demonstrates missing entity detection and handling RED Phase: Show system correctly identifies missing entities GREEN Phase: Show system properly handles/filters missing entities (Status: Keep).

---

## `tests/test_entity_tracking_generic.py`

**Role:** Tests to ensure entity tracking works for ANY campaign, not just Sariel. Tests that the system is truly generic and doesn't have hardcoded campaign data.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestEntityTrackingGeneric` – Test that entity tracking is generic and not campaign-specific (Status: Keep).
  - `test_entity_instructions_not_hardcoded_sariel` – Test that entity instructions don't have hardcoded Sariel references (Status: Keep).
  - `test_player_character_detection_is_generic` – Test that PC detection isn't hardcoded to Sariel (Status: Keep).
  - `test_location_enforcer_not_hardcoded` – Test that location enforcer doesn't have hardcoded locations (Status: Keep).
  - `test_location_mappings_are_generic` – Test that location owner mappings are disabled (returns False for all) (Status: Keep).
  - `test_entity_specific_instruction_is_generic` – Test that entity-specific methods are generic (Status: Keep).
  - `test_entity_tracking_with_different_campaign` – Test full entity tracking with a non-Sariel campaign (Status: Keep).
  - `test_hardcoded_location_instructions` – Test that location instructions are hardcoded (Status: Keep).
- `class TestEntityTrackingGenericFixes` – Test proposed fixes for making entity tracking generic (Status: Keep).
  - `test_proposed_generic_player_character_detection` – Test how PC detection should work generically (Status: Keep).
  - `test_proposed_dynamic_location_rules` – Test how location rules should work dynamically (Status: Keep).
  - `test_proposed_no_character_specific_methods` – Test that generic system shouldn't have character-specific methods (Status: Keep).

---

## `tests/test_entity_utils.py`

**Role:** Tests for entity utility functions.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestEntityUtils` – Test entity utility functions (Status: Keep).
  - `test_filter_unknown_entities_removes_unknown` – Test that 'Unknown' entities are filtered out (Status: Keep).
  - `test_filter_unknown_entities_case_insensitive` – Test that filtering is case-insensitive (Status: Keep).
  - `test_filter_unknown_entities_empty_list` – Test filtering empty list (Status: Keep).
  - `test_filter_unknown_entities_only_unknown` – Test filtering list with only 'Unknown' entities (Status: Keep).
  - `test_filter_unknown_entities_no_unknown` – Test filtering list with no 'Unknown' entities (Status: Keep).
  - `test_is_unknown_entity_true_cases` – Test is_unknown_entity returns True for unknown entities (Status: Keep).
  - `test_is_unknown_entity_false_cases` – Test is_unknown_entity returns False for known entities (Status: Keep).
  - `test_filter_unknown_entities_preserves_order` – Test that filtering preserves the original order (Status: Keep).

---

## `tests/test_entity_validator.py`

**Role:** Unit tests for Enhanced Post-Generation Validation with Retry (Option 2 Enhanced) Tests entity validation and retry logic functionality.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestEntityValidator` – No class docstring present; review implementation to confirm behavior. (Status: Keep).
  - `setUp` – No docstring present; review implementation to confirm behavior. (Status: Keep).
  - `test_validate_entity_presence_success` – Test successful entity validation (Status: Keep).
  - `test_validate_entity_presence_missing_entities` – Test validation with missing entities (Status: Keep).
  - `test_calculate_entity_presence_score_direct_mention` – Test scoring for direct entity mentions (Status: Keep).
  - `test_calculate_entity_presence_score_action_attribution` – Test scoring for action attribution patterns (Status: Keep).
  - `test_calculate_entity_presence_score_partial_match` – Test scoring for partial name matches (Status: Keep).
  - `test_generate_retry_suggestions_cassian` – Test retry suggestions for Cassian specifically (Status: Keep).
  - `test_generate_retry_suggestions_location_specific` – Test location-specific retry suggestions (Status: Keep).
  - `test_create_retry_prompt` – Test retry prompt creation (Status: Keep).
  - `test_create_retry_prompt_no_retry_needed` – Test retry prompt when no retry is needed (Status: Keep).
- `class TestEntityRetryManager` – No class docstring present; review implementation to confirm behavior. (Status: Keep).
  - `setUp` – No docstring present; review implementation to confirm behavior. (Status: Keep).
  - `test_validate_with_retry_success_first_try` – Test successful validation on first try (Status: Keep).
  - `test_validate_with_retry_success_after_retry` – Test successful validation after retry (Status: Keep).
  - `test_validate_with_retry_max_retries_exceeded` – Test behavior when max retries exceeded (Status: Keep).
  - `test_validate_with_retry_no_callback` – Test validation without retry callback (Status: Keep).
  - `test_get_retry_statistics` – Test retry statistics retrieval (Status: Keep).
- `class TestValidationResultDataClass` – No class docstring present; review implementation to confirm behavior. (Status: Keep).
  - `test_validation_result_creation` – Test ValidationResult dataclass creation (Status: Keep).
- `class TestGlobalInstances` – No class docstring present; review implementation to confirm behavior. (Status: Keep).
  - `test_global_entity_validator_exists` – Test that global entity validator instance exists (Status: Keep).
  - `test_global_entity_retry_manager_exists` – Test that global entity retry manager instance exists (Status: Keep).

---

## `tests/test_extra_json_fields.py`

**Role:** Test handling of extra JSON fields from Gemini

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestExtraJSONFields` – Test that we handle extra fields Gemini might include (Status: Keep).
  - `test_parse_json_with_extra_fields` – Test parsing JSON that includes fields not in NarrativeResponse schema (Status: Keep).
  - `test_narrative_response_with_debug_info` – Test that NarrativeResponse properly handles debug_info field (Status: Keep).

---

## `tests/test_fake_services_simple.py`

**Role:** Simple test of fake services without external dependencies. Verifies that fakes work correctly in isolation.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestFakeServicesSimple` – Test fake services in isolation. (Status: Keep).
  - `test_fake_firestore_basic_operations` – Test that fake Firestore behaves like the real thing. (Status: Keep).
  - `test_fake_gemini_response_generation` – Test that fake Gemini generates realistic responses. (Status: Keep).
  - `test_fake_auth_user_management` – Test that fake Auth manages users realistically. (Status: Keep).
  - `test_fake_services_integration` – Test that all fake services work together. (Status: Keep).

---

## `tests/test_field_format_validation.py`

**Role:** Red-Green Test for Field Format Validation ========================================== This test validates that the field format between world_logic.py and main.py translation layer is consistent and working correctly. RED: Temporarily break the field format to ensure test catches it GREEN: Fix the field format and ensure test passes

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestFieldFormatValidation` – Test field format consistency between world_logic and main translation layer. (Status: Keep).
  - `setUp` – Set up test with mock dependencies. (Status: Keep).
  - `test_field_format_consistency_red_green` – RED-GREEN TEST: Field format consistency between world_logic and main.py This test ensures that story entries created by world_logic.py use the correct field format that main.py translation layer expects. (Status: Keep).
  - `test_red_phase_field_format_mismatch_detection` – RED PHASE: Temporarily test what happens with wrong field format This demonstrates what would happen if world_logic used 'story' field instead of 'text' field - the translation layer would fail to extract content. (Status: Keep).

---

## `tests/test_file_cache.py`

**Role:** Unit tests for file_cache.py module. Tests the generalized file caching functionality using cachetools.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestFileCache` – Test cases for file_cache module. (Status: Keep).
  - `setUp` – Set up test fixtures before each test method. (Status: Keep).
  - `tearDown` – Clean up after each test method. (Status: Keep).
  - `test_basic_file_read` – Test basic file reading functionality. (Status: Keep).
  - `test_cache_hit_behavior` – Test that subsequent reads use cache (cache hits). (Status: Keep).
  - `test_cache_miss_behavior` – Test cache miss statistics. (Status: Keep).
  - `test_file_not_found_error` – Test error handling for non-existent files. (Status: Keep).
  - `test_cache_clear_functionality` – Test that cache clearing works correctly. (Status: Keep).
  - `test_cache_statistics_tracking` – Test that cache statistics are properly tracked. (Status: Keep).
  - `test_thread_safety` – Test that cache is thread-safe. (Status: Keep).
  - `test_performance_improvement` – Test that cached reads are faster than file I/O. (Status: Keep).
  - `test_ttl_expiration_simulation` – Test TTL expiration behavior (simulated since 1 hour is too long). (Status: Keep).
  - `test_cache_invalidation_functionality` – Test cache invalidation functionality. (Status: Keep).
- `class TestFileCacheIntegration` – Integration tests for file cache with real world usage. (Status: Keep).
  - `setUp` – Set up integration test fixtures. (Status: Keep).
  - `tearDown` – Clean up integration test fixtures. (Status: Keep).
  - `test_multiple_files_caching` – Test caching behavior with multiple different files. (Status: Keep).

---

## `tests/test_firebase_mock_mode.py`

**Role:** Test that Firebase initialization is skipped when MOCK_SERVICES_MODE is set. This is a simplified test that verifies both main.py and world_logic.py properly check for MOCK_SERVICES_MODE environment variable.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestFirebaseMockMode` – Test Firebase initialization with MOCK_SERVICES_MODE. (Status: Keep).
  - `test_main_initializes_firebase_regardless_of_mock_mode` – Test that main.py initializes Firebase regardless of MOCK_SERVICES_MODE (testing mode removed). (Status: Keep).
  - `test_world_logic_initializes_firebase_regardless_of_mock_mode` – Test that world_logic.py initializes Firebase regardless of MOCK_SERVICES_MODE (testing mode removed). (Status: Keep).

---

## `tests/test_firestore_database_errors.py`

**Role:** Unit tests for firestore_service.py database error handling. Tests connection failures, transaction errors, query problems, and document-level error scenarios to improve coverage.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestFirestoreDatabaseErrors` – Test database error scenarios in firestore_service.py (Status: Keep).
  - `setUp` – Set up test environment (Status: Keep).
  - `test_connection_timeout_recovery` – Test recovery from database connection timeouts (Status: Keep).
  - `test_connection_refused_handling` – Test handling of network connection failures (Status: Keep).
  - `test_auth_token_expiry_refresh` – Test handling of expired authentication tokens (Status: Keep).
  - `test_transaction_conflict_resolution` – Test handling of concurrent transaction conflicts (Status: Keep).
  - `test_transaction_rollback_on_failure` – Test transaction rollback when operations fail (Status: Keep).
  - `test_deadlock_detection_recovery` – Test recovery from transaction deadlocks (Status: Keep).
  - `test_invalid_query_syntax_handling` – Test handling of malformed database queries (Status: Keep).
  - `test_query_timeout_with_retry` – Test handling of slow queries that timeout (Status: Keep).
  - `test_query_size_limit_exceeded` – Test handling when query results are too large (Status: Keep).
  - `test_collection_not_found_error` – Test handling when collections don't exist (Status: Keep).
  - `test_document_not_found_graceful` – Test graceful handling of missing documents (Status: Keep).
  - `test_document_size_limit_handling` – Test handling of oversized documents (>1MB) (Status: Keep).
  - `test_invalid_document_id_format` – Test handling of malformed document IDs (Status: Keep).
  - `test_document_permission_denied` – Test handling of access control failures (Status: Keep).
  - `test_batch_operation_partial_failure` – Test handling when some batch operations succeed, others fail (Status: Keep).

---

## `tests/test_firestore_empty_narrative_bug_redgreen.py`

**Role:** RED-GREEN TEST: Firestore Empty Narrative Persistence Bug This test demonstrates the bug described in roadmap/scratchpad_planb_rates.md: - Think commands with empty narrative weren't being saved to Firestore - Bug: chunks=0 logic prevented database writes for empty narratives - Impact: AI responses disappeared on page reload RED: Test fails when empty narrative + structured fields aren't saved GREEN: Test passes after fix handles empty narrative correctly

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestFirestoreEmptyNarrativeBug` – RED-GREEN demonstration of the Firestore empty narrative persistence bug. The Bug Scenario: 1. AI generates response with empty narrative but valid structured fields 2. Original code: chunks=0 → no database write → data lost 3. Fixed code: handles empty narrative + structured fields correctly (Status: Keep).
  - `setUp` – Set up test environment with fake Firestore client. (Status: Keep).
  - `test_empty_narrative_with_structured_fields_persists` – RED-GREEN TEST: Empty narrative + structured fields should be saved. This tests the specific bug from planb_rates scratchpad: - Think commands generate empty narrative but valid structured fields - Original bug: chunks=0 prevented any database write - Fix: empty narrative with structured fields should still save (Status: Keep).
  - `test_bug_reproduction_scenario` – Reproduce the exact bug scenario from the scratchpad: 1. Think command generates response with empty narrative 2. Response has valid structured fields (planning block, state changes) 3. Original bug: chunks=0 → no save → response disappears on reload (Status: Keep).

---

## `tests/test_firestore_helper_functions_fixed.py`

**Role:** Phase 4: Helper function tests for firestore_service.py (fixed version) Test _truncate_log_json and _perform_append functions

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestFirestoreHelperFunctions` – Test helper functions in firestore_service.py (Status: Keep).
  - `test_truncate_log_json_small_data` – Test _truncate_log_json with data smaller than max_lines (Status: Keep).
  - `test_truncate_log_json_large_data` – Test _truncate_log_json with data exceeding max_lines (Status: Keep).
  - `test_truncate_log_json_exact_boundary` – Test _truncate_log_json with exactly max_lines (Status: Keep).
  - `test_truncate_log_json_invalid_json` – Test _truncate_log_json exception handling with non-serializable data (Status: Keep).
  - `test_truncate_log_json_circular_reference` – Test _truncate_log_json with circular reference (Status: Keep).
  - `test_truncate_log_json_empty_data` – Test _truncate_log_json with empty data (Status: Keep).
  - `test_truncate_log_json_none_data` – Test _truncate_log_json with None (Status: Keep).
  - `test_perform_append_single_item` – Test _perform_append with single item (not a list) (Status: Keep).
  - `test_perform_append_list_items` – Test _perform_append with list of items (Status: Keep).
  - `test_perform_append_empty_list` – Test _perform_append with empty items list (Status: Keep).
  - `test_perform_append_deduplicate_true` – Test _perform_append with deduplication enabled (Status: Keep).
  - `test_perform_append_deduplicate_false` – Test _perform_append with deduplication disabled (Status: Keep).
  - `test_perform_append_none_item` – Test _perform_append with None as single item (Status: Keep).
  - `test_perform_append_complex_objects` – Test _perform_append with complex objects (Status: Keep).
  - `test_perform_append_deduplicate_complex_objects` – Test _perform_append deduplication with complex objects (Status: Keep).
  - `test_truncate_log_json_max_lines_parameter` – Test _truncate_log_json respects max_lines parameter (Status: Keep).
  - `test_perform_append_all_duplicates` – Test _perform_append when all items are duplicates (Status: Keep).

---

## `tests/test_firestore_mission_handler.py`

**Role:** Phase 4: MissionHandler tests for firestore_service.py Target coverage: 61% → 70% Focus: MissionHandler class static methods

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestMissionHandler` – Test MissionHandler static methods (Status: Keep).
  - `test_initialize_missions_list_missing_key` – Test initialize_missions_list when key doesn't exist (Status: Keep).
  - `test_initialize_missions_list_non_list_value` – Test initialize_missions_list when key exists but isn't a list (Status: Keep).
  - `test_initialize_missions_list_already_list` – Test initialize_missions_list when key already has a list (Status: Keep).
  - `test_initialize_missions_list_none_value` – Test initialize_missions_list when key has None value (Status: Keep).
  - `test_find_existing_mission_index_found` – Test find_existing_mission_index when mission exists (Status: Keep).
  - `test_find_existing_mission_index_not_found` – Test find_existing_mission_index when mission doesn't exist (Status: Keep).
  - `test_find_existing_mission_index_empty_list` – Test find_existing_mission_index with empty list (Status: Keep).
  - `test_find_existing_mission_index_invalid_mission_objects` – Test find_existing_mission_index with non-dict items in list (Status: Keep).
  - `test_find_existing_mission_index_missing_mission_id` – Test find_existing_mission_index when dicts lack mission_id (Status: Keep).
  - `test_process_mission_data_new_mission` – Test process_mission_data adding a new mission (Status: Keep).
  - `test_process_mission_data_update_existing` – Test process_mission_data updating an existing mission (Status: Keep).
  - `test_process_mission_data_adds_missing_id` – Test process_mission_data adds mission_id if missing (Status: Keep).
  - `test_handle_missions_dict_conversion` – Test handle_missions_dict_conversion with dict of missions (Status: Keep).
  - `test_handle_active_missions_conversion_dict` – Test handle_active_missions_conversion with dict value (Status: Keep).
  - `test_handle_active_missions_conversion_invalid_type` – Test handle_active_missions_conversion with non-dict, non-list value (Status: Keep).
  - `test_handle_missions_dict_conversion_empty` – Test handle_missions_dict_conversion with empty dict (Status: Keep).
  - `test_handle_missions_dict_conversion_mixed_types` – Test handle_missions_dict_conversion with various invalid types (Status: Keep).

---

## `tests/test_firestore_mock.py`

**Role:** Test demonstrating proper mocking of Firestore client in tests.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestFirestoreMocking` – Demonstrate proper mocking of Firestore operations. (Status: Keep).
  - `test_firestore_operations_with_mock` – Test that Firestore operations can be properly mocked. (Status: Keep).
  - `test_mock_at_firestore_client_level` – Test that get_db() can be properly mocked for testing. (Status: Keep).
  - `test_mock_with_context_manager` – Test using mock as a context manager for isolated tests. (Status: Keep).

---

## `tests/test_firestore_state_helpers.py`

**Role:** Phase 5: State helper function tests for firestore_service.py Test _handle_append_syntax, _handle_core_memories_safeguard, _handle_dict_merge, _handle_delete_token, _handle_string_to_dict_update

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestFirestoreStateHelpers` – Test state helper functions in firestore_service.py (Status: Keep).
  - `test_handle_append_syntax_valid` – Test _handle_append_syntax with valid append syntax (Status: Keep).
  - `test_handle_append_syntax_not_dict` – Test _handle_append_syntax with non-dict value (Status: Keep).
  - `test_handle_append_syntax_no_append_key` – Test _handle_append_syntax with dict missing 'append' key (Status: Keep).
  - `test_handle_append_syntax_creates_list` – Test _handle_append_syntax creates list if missing (Status: Keep).
  - `test_handle_append_syntax_core_memories_dedup` – Test _handle_append_syntax with core_memories uses deduplication (Status: Keep).
  - `test_handle_core_memories_safeguard_triggered` – Test _handle_core_memories_safeguard prevents overwrite (Status: Keep).
  - `test_handle_core_memories_safeguard_other_key` – Test _handle_core_memories_safeguard ignores other keys (Status: Keep).
  - `test_handle_core_memories_safeguard_creates_list` – Test _handle_core_memories_safeguard creates list if missing (Status: Keep).
  - `test_handle_dict_merge_non_dict_value` – Test _handle_dict_merge with non-dict value (Status: Keep).
  - `test_handle_dict_merge_existing_dict` – Test _handle_dict_merge merges with existing dict (Status: Keep).
  - `test_handle_dict_merge_new_dict` – Test _handle_dict_merge creates new dict when key missing (Status: Keep).
  - `test_handle_dict_merge_overwrite_non_dict` – Test _handle_dict_merge overwrites non-dict existing value (Status: Keep).
  - `test_handle_delete_token_deletes_existing` – Test _handle_delete_token removes existing key (Status: Keep).
  - `test_handle_delete_token_missing_key` – Test _handle_delete_token with non-existent key (Status: Keep).
  - `test_handle_delete_token_wrong_value` – Test _handle_delete_token with value not DELETE_TOKEN (Status: Keep).
  - `test_handle_string_to_dict_update_preserves_dict` – Test _handle_string_to_dict_update preserves dict structure (Status: Keep).
  - `test_handle_string_to_dict_update_non_dict_existing` – Test _handle_string_to_dict_update with non-dict existing value (Status: Keep).
  - `test_handle_string_to_dict_update_missing_key` – Test _handle_string_to_dict_update with missing key (Status: Keep).
  - `test_handle_string_to_dict_update_overwrites_status` – Test _handle_string_to_dict_update overwrites existing status (Status: Keep).
  - `test_update_state_with_changes_integration` – Test update_state_with_changes with various scenarios (Status: Keep).
  - `test_matrix_delete_token_comprehensive` – Matrix 1: DELETE_TOKEN handling - All combinations [1,1-3] (Status: Keep).
  - `test_matrix_append_syntax_comprehensive` – Matrix 2: Append syntax handling - All combinations [2,1-3] (Status: Keep).
  - `test_matrix_core_memories_safeguard_comprehensive` – Matrix 3: Core memories safeguard - All combinations [3,1-3] (Status: Keep).
  - `test_matrix_integration_state_updates_red_phase` – Matrix 5: Integration testing - RED phase with expected failures [5,1-4] (Status: Keep).
  - `test_matrix_value_type_validation_red_phase` – Matrix 6: Value type validation - RED phase [6,1-7] (Status: Keep).
  - `test_matrix_edge_cases_refactor` – Matrix 7: Edge cases and refactoring validation [7,1-5] (Status: Keep).
  - `test_matrix_performance_characteristics` – Matrix 8: Performance and scalability testing [8,1-4] (Status: Keep).

---

## `tests/test_firestore_structured_fields.py`

**Role:** Unit tests for firestore_service structured fields handling. Tests that structured fields are properly stored in Firestore.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestFirestoreStructuredFields` – Test structured fields handling in firestore_service (Status: Keep).
  - `setUp` – Set up test environment (Status: Keep).
  - `tearDown` – Clean up test environment (Status: Keep).
  - `test_add_story_entry_with_structured_fields` – Test add_story_entry properly stores structured fields (Status: Keep).
  - `test_add_story_entry_without_structured_fields` – Test add_story_entry works without structured fields (Status: Keep).
  - `test_add_story_entry_with_partial_structured_fields` – Test add_story_entry with only some structured fields (Status: Keep).
  - `test_add_story_entry_with_empty_structured_fields` – Test add_story_entry with empty structured fields dict (Status: Keep).
  - `test_add_story_entry_with_none_values_in_structured_fields` – Test add_story_entry handles None values in structured fields (Status: Keep).

---

## `tests/test_flask_app_import.py`

**Role:** RED Phase: Test that Flask app can be imported from main.py This test should FAIL initially, demonstrating the issue.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestFlaskAppImport` – Test that Flask app is properly importable (Status: Keep).
  - `test_app_import_from_main` – Test that we can import app from main module (Status: Keep).
  - `test_create_app_function_exists` – Test that create_app function exists and works (Status: Keep).

---

## `tests/test_game_state.py`

**Role:** Unit tests for game_state.py module. Tests the GameState class and related functions. Comprehensive mocking implemented to handle CI environments that lack Firebase dependencies.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestGameState` – Test cases for the GameState class. (Status: Keep).
  - `test_validate_checkpoint_consistency_dict_location_bug` – Test that validate_checkpoint_consistency handles dict location objects correctly. (Status: Keep).
  - `test_debug_mode_default_true` – Test that debug_mode defaults to True per updated DEFAULT_DEBUG_MODE. (Status: Keep).
  - `test_debug_mode_can_be_set_false` – Test that debug_mode can be explicitly set to False. (Status: Keep).
  - `test_debug_mode_from_dict` – Test that debug_mode is properly loaded from dict. (Status: Keep).
  - `test_default_initialization` – Test GameState initialization with default values. (Status: Keep).
  - `test_initialization_with_kwargs` – Test GameState initialization with provided values. (Status: Keep).
  - `test_to_dict` – Test serialization to dictionary. (Status: Keep).
  - `test_from_dict_with_valid_data` – Test deserialization from dictionary. (Status: Keep).
  - `test_from_dict_with_none` – Test from_dict returns None when source is None. (Status: Keep).
  - `test_from_dict_with_empty_dict` – Test from_dict returns None when source is empty dict. (Status: Keep).
  - `test_dynamic_attribute_setting` – Test that dynamic attributes are set correctly. (Status: Keep).
  - `test_attribute_precedence` – Test that existing attributes are not overwritten by dynamic setting. (Status: Keep).
  - `test_three_layer_nesting_all_types` – Test GameState with 3 layers of nesting and all valid Python data types. (Status: Keep).
  - `test_to_dict_three_layer_nesting_all_types` – Test serialization of GameState with 3 layers of nesting and all data types. (Status: Keep).
  - `test_from_dict_three_layer_nesting_all_types` – Test deserialization from dict with 3 layers of nesting and all data types. (Status: Keep).
  - `test_manifest_cache_not_serialized` – Test that internal cache attributes like _manifest_cache are excluded from serialization. (Status: Keep).
- `class TestUpdateStateWithChanges` – Test cases for the update_state_with_changes function. (Status: Keep).
  - `test_simple_overwrite` – Test simple value overwriting. (Status: Keep).
  - `test_nested_dict_merge` – Test recursive merging of nested dictionaries. (Status: Keep).
  - `test_explicit_append_syntax` – Test explicit append using {'append': ...} syntax. (Status: Keep).
  - `test_explicit_append_to_nonexistent_key` – Test append to a key that doesn't exist yet. (Status: Keep).
  - `test_explicit_append_to_non_list` – Test append to a key that exists but isn't a list. (Status: Keep).
  - `test_core_memories_safeguard` – Test that core_memories is protected from direct overwrite. (Status: Keep).
  - `test_core_memories_deduplication` – Test that core_memories deduplicates when appending. (Status: Keep).
  - `test_core_memories_to_nonexistent_key` – Test core_memories safeguard when key doesn't exist. (Status: Keep).
  - `test_mixed_operations` – Test a complex scenario with multiple operation types. (Status: Keep).
  - `test_deep_nesting` – Test very deep nested dictionary merging. (Status: Keep).
  - `test_three_layer_nesting_all_data_types` – Test update_state_with_changes with 3 layers of nesting and all Python data types. (Status: Keep).
  - `test_three_layer_nesting_edge_cases` – Test edge cases with 3-layer nesting including empty structures and type conflicts. (Status: Keep).
- `class TestPerformAppend` – Test cases for the _perform_append helper function. (Status: Keep).
  - `test_append_single_item` – Test appending a single item. (Status: Keep).
  - `test_append_multiple_items` – Test appending multiple items. (Status: Keep).
  - `test_append_with_deduplication` – Test appending with deduplication enabled. (Status: Keep).
  - `test_append_without_deduplication` – Test appending without deduplication (default). (Status: Keep).
  - `test_append_all_duplicates` – Test appending when all items are duplicates. (Status: Keep).
  - `test_append_all_data_types` – Test appending various data types to a list. (Status: Keep).
- `class TestGameStateValidation` – Test cases for the GameState validation methods. (Status: Keep).
  - `test_validate_checkpoint_consistency_hp_mismatch_fails_without_implementation` – RED TEST: This should fail without the validate_checkpoint_consistency implementation. (Status: Keep).
  - `test_validate_checkpoint_consistency_location_mismatch_fails_without_implementation` – RED TEST: This should fail without the validate_checkpoint_consistency implementation. (Status: Keep).
  - `test_validate_checkpoint_consistency_mission_completion_fails_without_implementation` – RED TEST: This should fail without the validate_checkpoint_consistency implementation. (Status: Keep).
- `class TestMainStateFunctions` – Test cases for state-related functions in main.py. (Status: Keep).
  - `test_cleanup_legacy_state_with_dot_keys` – Test cleanup of legacy keys with dots. (Status: Keep).
  - `test_cleanup_legacy_state_with_world_time` – Test cleanup of legacy world_time key. (Status: Keep).
  - `test_cleanup_legacy_state_no_changes` – Test cleanup when no legacy keys are present. (Status: Keep).
  - `test_cleanup_legacy_state_empty_dict` – Test cleanup with empty dictionary. (Status: Keep).
  - `test_format_game_state_updates_simple` – Test formatting simple state changes. (Status: Keep).
  - `test_format_game_state_updates_nested` – Test formatting nested state changes. (Status: Keep).
  - `test_format_game_state_updates_html` – Test formatting state changes for HTML output. (Status: Keep).
  - `test_format_game_state_updates_empty` – Test formatting empty state changes. (Status: Keep).
  - `test_parse_set_command_simple` – Test parsing simple set commands. (Status: Keep).
  - `test_parse_set_command_nested` – Test parsing nested dot notation. (Status: Keep).
  - `test_parse_set_command_append` – Test parsing append operations. (Status: Keep).
  - `test_parse_set_command_invalid_json` – Test parsing with invalid JSON values. (Status: Keep).
  - `test_parse_set_command_empty_lines` – Test parsing with empty lines and no equals signs. (Status: Keep).
  - `test_parse_set_command_three_layer_nesting_all_types` – Test parsing set commands with 3 layers of nesting and all data types. (Status: Keep).
  - `test_debug_mode_command_applies_multiline_god_mode_set` – Ensure GOD_MODE_SET blocks with nested paths are applied through the debug handler. (Status: Keep).
  - `test_debug_mode_command_returns_structured_state_for_ask` – GOD_ASK_STATE should return the raw game_state alongside the formatted response. (Status: Keep).

---

## `tests/test_game_state_division_by_zero.py`

**Role:** Test for the division by zero fix in GameState.validate_checkpoint_consistency

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestGameStateDivisionByZero` – Test cases for division by zero error fix in validate_checkpoint_consistency. (Status: Keep).
  - `test_validate_with_zero_hp_max_during_character_creation` – Test that validation handles hp_max=0 during character creation without crashing. (Status: Keep).
  - `test_validate_with_zero_hp_max_outside_character_creation` – Test that validation detects invalid hp_max=0 outside character creation. (Status: Keep).
  - `test_validate_with_none_hp_values` – Test that validation handles None HP values gracefully. (Status: Keep).
  - `test_validate_with_normal_hp_values` – Test that validation works correctly with normal HP values. (Status: Keep).
  - `test_validate_detects_hp_narrative_mismatch` – Test that validation correctly detects HP/narrative mismatches. (Status: Keep).
  - `test_validate_with_partial_character_data` – Test validation with incomplete character data (only hp_current). (Status: Keep).
  - `test_validate_character_creation_scenario` – Test the exact scenario from the error: character creation with hp_max=0. (Status: Keep).

---

## `tests/test_llm_entity_sanitization.py`

**Role:** Test entity name sanitization in llm_service.py

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestLLMEntitySanitization` – Test entity name sanitization function in llm_service (Status: Keep).
  - `test_sanitize_entity_name_for_id_basic` – Test basic sanitization cases (Status: Keep).
  - `test_multiple_apostrophes_and_quotes` – Test handling of multiple apostrophes and quotes (Status: Keep).
  - `test_special_characters` – Test various special characters (Status: Keep).
  - `test_unicode_and_accents` – Test unicode characters and accented letters (Status: Keep).
  - `test_whitespace_handling` – Test various whitespace scenarios (Status: Keep).
  - `test_consecutive_special_chars` – Test multiple consecutive special characters (Status: Keep).
  - `test_edge_cases` – Test edge cases (Status: Keep).
  - `test_real_world_npc_names` – Test with actual NPC names that might appear in games (Status: Keep).
  - `test_integration_with_entity_id_format` – Test that sanitized names work with the entity ID format (Status: Keep).

---

## `tests/test_gemini_request_tdd.py`

**Role:** Test-Driven Development for GeminiRequest Class This test defines the proper structured JSON that should be sent directly to Gemini API instead of being converted back to concatenated string blobs. The tests will initially FAIL until we implement the GeminiRequest class properly. RED -> GREEN -> REFACTOR approach: 1. RED: Tests fail because current implementation converts JSON back to strings 2. GREEN: Implement GeminiRequest class that sends actual JSON to Gemini 3. REFACTOR: Remove old json_input_schema approach

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestGeminiRequestTDD` – TDD tests for GeminiRequest class that sends actual JSON to Gemini API. These tests define the EXPECTED behavior: structured JSON fields should be sent directly to Gemini API, not converted to concatenated strings. (Status: Keep).
  - `setUp` – Set up test fixtures. (Status: Keep).
  - `test_continue_story_sends_structured_json_to_gemini` – FAILING TEST: Verify continue_story sends structured JSON directly to Gemini API. This test will FAIL initially because the current implementation converts JSON back to concatenated strings via to_gemini_format(). Expected: Direct JSON fields sent to Gemini API Current: JSON converted back to string blob (Status: Keep).
  - `test_get_initial_story_sends_structured_json_to_gemini` – TEST: Verify get_initial_story works with built-in mock mode. This test uses the built-in MOCK_SERVICES_MODE to avoid complex mocking. It verifies that the function returns a valid response structure. (Status: Keep).
  - `test_gemini_request_class_exists` – FAILING TEST: Verify GeminiRequest class exists and has expected methods. This test will FAIL until we create the GeminiRequest class. (Status: Keep).

---

## `tests/test_gemini_request_validation.py`

**Role:** Test validation behavior of GeminiRequest class Tests for the new validation features added to ensure proper type safety, field validation, and error handling.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestGeminiRequestValidation` – Test validation behavior of GeminiRequest class. (Status: Keep).
  - `test_empty_user_id_raises_validation_error` – Test that empty user_id raises ValidationError. (Status: Keep).
  - `test_whitespace_user_id_raises_validation_error` – Test that whitespace-only user_id raises ValidationError. (Status: Keep).
  - `test_empty_game_mode_raises_validation_error` – Test that empty game_mode raises ValidationError. (Status: Keep).
  - `test_wrong_game_state_type_raises_validation_error` – Test that non-dict game_state raises ValidationError. (Status: Keep).
  - `test_wrong_story_history_type_raises_validation_error` – Test that non-list story_history raises ValidationError. (Status: Keep).
  - `test_wrong_core_memories_type_raises_validation_error` – Test that non-list core_memories raises ValidationError. (Status: Keep).
  - `test_wrong_core_memories_item_type_raises_validation_error` – Test that non-string items in core_memories raise ValidationError. (Status: Keep).
  - `test_too_long_user_action_raises_validation_error` – Test that overly long user_action raises ValidationError. (Status: Keep).
  - `test_too_long_checkpoint_block_raises_validation_error` – Test that overly long checkpoint_block raises ValidationError. (Status: Keep).
  - `test_large_payload_raises_payload_too_large_error` – Test that oversized JSON payload raises PayloadTooLargeError. (Status: Keep).
  - `test_valid_request_passes_validation` – Test that valid GeminiRequest passes all validation. (Status: Keep).
  - `test_build_story_continuation_validates_parameters` – Test that build_story_continuation validates input parameters. (Status: Keep).
  - `test_build_initial_story_validates_parameters` – Test that build_initial_story validates input parameters. (Status: Keep).
  - `test_json_serialization_error_handling` – Test that JSON serialization errors are properly handled. (Status: Keep).

---

## `tests/test_gemini_response.py`

**Role:** Test-Driven Development: Tests for GeminiResponse object These tests define the expected behavior for the GeminiResponse object that will clean up the architecture between llm_service and main.py. Updated for new API where GeminiResponse.create() takes raw response text.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestGeminiResponse` – Test cases for GeminiResponse object. (Status: Keep).
  - `setUp` – Set up test fixtures. (Status: Keep).
  - `test_gemini_response_creation` – Test creating a GeminiResponse object. (Status: Keep).
  - `test_debug_tags_detection_with_content` – Test debug tags are properly detected when content exists. (Status: Keep).
  - `test_debug_tags_detection_no_content` – Test debug tags detection when no debug content exists. (Status: Keep).
  - `test_state_updates_property` – Test state_updates property returns correct data. (Status: Keep).
  - `test_entities_mentioned_property` – Test entities_mentioned property returns correct data. (Status: Keep).
  - `test_location_confirmed_property` – Test location_confirmed property returns correct data. (Status: Keep).
  - `test_debug_info_property` – Test debug_info property returns correct data. (Status: Keep).
  - `test_none_structured_response_handling` – Test GeminiResponse handles plain text gracefully. (Status: Keep).
  - `test_get_initial_story_returns_gemini_response` – Test that get_initial_story returns a GeminiResponse object. (Status: Keep).
  - `test_continue_story_returns_gemini_response` – Test that continue_story returns a GeminiResponse object. (Status: Keep).
  - `test_main_py_handles_gemini_response_object` – Test that main.py properly handles GeminiResponse objects. (Status: Keep).
  - `test_legacy_create_method` – Test that the legacy create method still works for backwards compatibility. (Status: Keep).

---

## `tests/test_gemini_response_structured_fields.py`

**Role:** Unit tests for GeminiResponse handling of structured fields. Tests parsing of raw JSON responses containing structured fields.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestGeminiResponseStructuredFields` – Test GeminiResponse parsing of structured fields from raw JSON (Status: Keep).
  - `setUp` – Set up test fixtures (Status: Keep).
  - `test_parse_all_structured_fields_present` – Test parsing when all structured fields are present (Status: Keep).
  - `test_parse_missing_structured_fields` – Test parsing when some structured fields are missing (Status: Keep).
  - `test_parse_empty_structured_fields` – Test parsing when structured fields are present but empty (Status: Keep).
  - `test_parse_null_structured_fields` – Test parsing when structured fields are null (Status: Keep).
  - `test_parse_malformed_dice_rolls` – Test parsing when dice_rolls is not a list (Status: Keep).
  - `test_parse_complex_debug_info` – Test parsing complex nested debug_info (Status: Keep).
  - `test_parse_special_characters_in_fields` – Test parsing fields with special characters (Status: Keep).
  - `test_parse_very_long_fields` – Test parsing fields with very long content (Status: Keep).

---

## `tests/test_gemini_response_validation.py`

**Role:** Tests for LLM response validation and parsing in llm_service.py. Focus on JSON parsing, schema validation, and field validation.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestGeminiResponseValidation` – Test suite for LLM API response validation and parsing. (Status: Keep).
  - `setUp` – Set up test fixtures. (Status: Keep).
  - `test_valid_json_parsing` – Test that valid JSON responses are parsed correctly. (Status: Keep).
  - `test_invalid_json_recovery` – Test that malformed JSON triggers proper error handling. (Status: Keep).
  - `test_partial_json_handling` – Test handling of truncated JSON responses. (Status: Keep).
  - `test_missing_content_field` – Test response parsing when 'narrative' content field is missing. (Status: Keep).
  - `test_missing_role_field` – Test response parsing when role-related fields are missing. (Status: Keep).
  - `test_missing_parts_field` – Test response parsing when complex structure fields are missing. (Status: Keep).
  - `test_invalid_content_type` – Test response parsing when content is wrong type (number not string). (Status: Keep).
  - `test_invalid_parts_structure` – Test response parsing when parts/list fields have wrong structure. (Status: Keep).
  - `test_null_values_handling` – Test response parsing with null values in required fields. (Status: Keep).
  - `test_oversized_response` – Test handling of very large responses (simulating 10MB). (Status: Keep).
  - `test_empty_content_handling` – Test handling of empty content fields. (Status: Keep).
  - `test_whitespace_only_content` – Test handling of whitespace-only content. (Status: Keep).

---

## `tests/test_gemini_token_management.py`

**Role:** Test Suite for Gemini Service Token Management Tests token constants and basic functionality without complex dependencies. This test is designed to work in both local and CI environments.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestGeminiTokenManagement` – Test cases for token management constants and functions. (Status: Keep).
  - `test_token_constants_updated` – Test that token constants reflect correct Gemini 2.5 Flash limits. (Status: Keep).
  - `test_token_estimation_basic` – Test basic token estimation function works. (Status: Keep).
  - `test_token_estimation_empty` – Test token estimation with empty text. (Status: Keep).
  - `test_token_estimation_unicode` – Test token estimation with Unicode characters. (Status: Keep).
  - `test_token_constants_in_real_service` – Test that token constants are properly set in real service. (Status: Keep).

---

## `tests/test_generator_isolated.py`

**Role:** No module docstring; review code to confirm responsibilities.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `export_endpoint` – No docstring present; review implementation to confirm behavior. (Status: Keep).
- `class TestPdfGeneration` – No class docstring present; review implementation to confirm behavior. (Status: Keep).
  - `setUp` – No docstring present; review implementation to confirm behavior. (Status: Keep).
  - `test_pdf_generation_and_export` – Tests if a PDF can be generated and returned from the test Flask route. This test WILL FAIL if 'assets/DejaVuSans.ttf' is missing. (Status: Keep).

---

## `tests/test_god_mode_json_display_red_green.py`

**Role:** Red-Green test to reproduce and fix god mode raw JSON display issue.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestGodModeJsonDisplayRedGreen` – Red-Green test for god mode JSON display issue. (Status: Keep).
  - `test_original_bug_raw_json_without_narrative` – RED TEST: Reproduce the original bug - god mode returns JSON without narrative field. (Status: Keep).
  - `test_original_bug_partial_json` – RED TEST: God mode returns incomplete/malformed JSON. (Status: Keep).
  - `test_green_solution_with_god_mode_response_field` – GREEN TEST: Proper solution using god_mode_response field. (Status: Keep).
  - `test_all_code_paths_coverage` – Ensure all new code paths are tested. (Status: Keep).
  - `test_edge_cases` – Test edge cases for complete coverage. (Status: Keep).
  - `test_hasattr_safety` – Test the hasattr checks work correctly. (Status: Keep).
  - `test_code_coverage_branches` – Ensure we hit all conditional branches in the code. (Status: Keep).

---

## `tests/test_god_mode_planning_blocks.py`

**Role:** Test that God mode responses include planning blocks when offering choices.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestGodModePlanningBlocks` – Test God mode planning block requirements. (Status: Keep).
  - `test_god_mode_with_planning_block` – Test that God mode responses can include planning blocks. (Status: Keep).
  - `test_god_mode_choices_all_have_prefix` – Test that all God mode choices use the god: prefix. (Status: Keep).
  - `test_god_mode_without_planning_block` – Test that God mode responses without choices don't require planning blocks. (Status: Keep).
  - `test_missing_return_story_choice` – Test detection of missing god:return_story choice. (Status: Keep).
  - `test_planning_block_structure` – Test that God mode planning blocks follow the correct structure. (Status: Keep).

---

## `tests/test_god_mode_response_field.py`

**Role:** Test that god mode responses use the god_mode_response field correctly.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestGodModeResponseField` – Test god_mode_response field handling. (Status: Keep).
  - `setUp` – Set up test environment (Status: Keep).
  - `tearDown` – Clean up test environment (Status: Keep).
  - `test_god_mode_response_field_used` – Test that god_mode_response field is used when present. (Status: Keep).
  - `test_normal_response_without_god_mode` – Test that normal responses work without god_mode_response field. (Status: Keep).
  - `test_god_mode_with_state_updates` – Test god mode response with complex state updates. (Status: Keep).
  - `test_god_mode_empty_response` – Test god mode with empty god_mode_response field. (Status: Keep).
  - `test_malformed_god_mode_response` – Test handling of malformed JSON with god_mode_response. (Status: Keep).
  - `test_backward_compatibility` – Test that old god mode responses without god_mode_response field still work. (Status: Keep).
  - `test_god_mode_with_empty_narrative` – Test god mode response when narrative is empty string. (Status: Keep).
  - `test_combined_god_mode_and_narrative` – Test that only narrative is returned when both god_mode_response and narrative are present. (Status: Keep).
  - `test_god_mode_response_saved_to_firestore` – Test that god_mode_response is saved to Firestore via add_story_entry. (Status: Keep).
- `class TestGodModeResponseIntegration` – No class docstring present; review implementation to confirm behavior. (Status: Keep).
  - `setUp` – Set up test environment (Status: Keep).
  - `tearDown` – Clean up test environment (Status: Keep).
  - `test_all_structured_fields_are_saved_in_firestore` – No docstring present; review implementation to confirm behavior. (Status: Keep).

---

## `tests/test_granular_mock_control.py`

**Role:** Test MCP environment configuration for different testing scenarios. In MCP architecture, environment variables control behavior at the MCP server level.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestMCPEnvironmentControl` – No class docstring present; review implementation to confirm behavior. (Status: Keep).
  - `setUp` – Save original environment. (Status: Keep).
  - `tearDown` – Restore original environment. (Status: Keep).
  - `test_mcp_testing_environment_configured` – Test that MCP testing environment is properly configured. (Status: Keep).
  - `test_mcp_production_environment_configured` – Test that MCP production environment can be configured. (Status: Keep).
  - `test_mcp_client_handles_environment_gracefully` – Test that MCP client handles different environments gracefully. (Status: Keep).
  - `test_mcp_environment_variables_respected` – Test that MCP architecture respects environment variables. (Status: Keep).

---

## `tests/test_hp_unknown_values.py`

**Role:** Test cases for HP unknown value handling in HealthStatus

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestHPUnknownValues` – Test HealthStatus handling of unknown/invalid HP values (Status: Keep).
  - `test_hp_unknown_string` – Test HP='unknown' gets converted to 1 (Status: Keep).
  - `test_hp_max_unknown_string` – Test HP_MAX='unknown' gets converted to 1, hp must be valid (Status: Keep).
  - `test_both_unknown_strings` – Test both HP and HP_MAX='unknown' (Status: Keep).
  - `test_hp_none_value` – Test HP=None gets converted to 1 (Status: Keep).
  - `test_hp_max_none_value` – Test HP_MAX=None gets converted to 1, hp must be valid (Status: Keep).
  - `test_hp_invalid_string` – Test HP with invalid string gets converted to 1 (Status: Keep).
  - `test_hp_empty_string` – Test HP with empty string gets converted to 1 (Status: Keep).
  - `test_hp_max_invalid_string` – Test HP_MAX with invalid string gets converted to 1, hp must be valid (Status: Keep).
  - `test_hp_numeric_string` – Test HP as numeric string gets converted properly (Status: Keep).
  - `test_hp_zero_string` – Test HP='0' gets converted properly (Status: Keep).
  - `test_normal_numeric_values` – Test normal numeric values still work (Status: Keep).
  - `test_hp_exceeds_max_after_conversion` – Test validation still works after conversion (Status: Keep).
  - `test_negative_hp_values` – Test negative HP and HP_MAX values get converted by DefensiveNumericConverter (Status: Keep).

---

## `tests/test_imports.py`

**Role:** Import tests to catch missing import statements. These tests simply import modules to ensure all dependencies are available. NOTE: This file is intentionally exempt from the inline import rule. It may contain imports within test methods to test specific import scenarios and verify that modules can be imported correctly under various conditions. This is the ONLY file in the codebase allowed to have inline imports.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestImports` – Test that all main modules can be imported without errors (Status: Keep).
  - `test_import_firestore_service` – Test that firestore_service can be imported (Status: Keep).
  - `test_import_llm_service` – Test that llm_service can be imported (Status: Keep).
  - `test_import_main` – Test that main can be imported (Status: Keep).
  - `test_import_game_state` – Test that game_state can be imported (Status: Keep).
  - `test_import_constants` – Test that constants can be imported and has expected fields (Status: Keep).
  - `test_import_structured_fields_utils` – Test that structured_fields_utils can be imported (Status: Keep).
  - `test_import_narrative_response_schema` – Test that narrative_response_schema can be imported (Status: Keep).
  - `test_import_gemini_response` – Test that gemini_response can be imported (Status: Keep).

---

## `tests/test_infrastructure.py`

**Role:** Infrastructure tests for /testserver command functionality. Tests server start/stop/status commands, port allocation, and process management.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestServerInfrastructure` – Test /testserver command infrastructure functionality. (Status: Keep).
  - `setUp` – Set up test fixtures. (Status: Keep).
  - `test_testserver_help_command` – Test that /testserver help displays usage information. (Status: Keep).
  - `test_testserver_unknown_action` – Test /testserver with unknown action shows error and usage. (Status: Keep).
  - `test_testserver_manager_delegation` – Test that testserver.sh properly delegates to test_server_manager.sh. (Status: Keep).
  - `test_port_allocation_range` – Test that port allocation works within expected range (8081-8090). (Status: Keep).
  - `test_branch_specific_logging` – Test that branch-specific logging directory structure works. (Status: Keep).
  - `test_status_command_current_branch` – Test /testserver status shows current branch information. (Status: Keep).
  - `test_integration_with_push_commands` – Test that testserver integrates with /push and /integrate commands. (Status: Keep).
  - `test_conflict_detection_and_resolution` – Test that testserver handles port conflicts and process management. (Status: Keep).
  - `test_error_handling_missing_manager` – Test error handling when test_server_manager.sh is missing. (Status: Keep).
- `class TestServerProcessManagement` – Test server process management and monitoring functionality. (Status: Keep).
  - `test_process_identification` – Test that server processes can be identified by branch. (Status: Keep).
  - `test_port_range_validation` – Test that port allocation stays within valid range. (Status: Keep).
  - `test_log_file_structure` – Test branch-specific log file naming structure. (Status: Keep).

---

## `tests/test_input_field_validation.py`

**Role:** Red-Green Test for Input Field Translation Validation ===================================================== This test validates that the input field translation between frontend → main.py → world_logic.py works correctly across the architectural boundaries. Frontend sends: {"input": "..."} main.py receives: data.get("input") with KEY_USER_INPUT = "input" main.py sends to MCP: {"user_input": "..."} world_logic.py receives: request_data.get("user_input") with KEY_USER_INPUT = "user_input"

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestInputFieldTranslation` – Test input field translation across architectural boundaries. (Status: Keep).
  - `test_frontend_to_main_input_field` – Test that main.py correctly extracts 'input' field from frontend requests. (Status: Keep).
  - `test_main_to_mcp_field_translation` – Test that main.py correctly creates 'user_input' field for MCP protocol. (Status: Keep).
  - `test_mcp_world_logic_input_field` – Test that world_logic.py correctly expects 'user_input' field from MCP. (Status: Keep).
  - `test_end_to_end_input_field_flow` – RED-GREEN TEST: End-to-end input field translation flow. This test validates the complete flow: Frontend {"input": "..."} → main.py → MCP {"user_input": "..."} → world_logic.py (Status: Keep).
  - `test_red_phase_input_field_mismatch_detection` – RED PHASE: Test what would happen with wrong field names. This demonstrates potential bugs if the translation layer was broken. (Status: Keep).

---

## `tests/test_json_cleanup_safety.py`

**Role:** Tests for safer JSON cleanup approach Ensures narrative text containing JSON-like patterns isn't corrupted

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestJSONCleanupSafety` – Test cases for safer JSON cleanup implementation (Status: Keep).
  - `test_narrative_with_json_like_content_preserved` – Test that narrative containing JSON-like syntax is preserved (Status: Keep).
  - `test_malformed_json_cleanup_only_when_needed` – Test that cleanup only applies to clearly malformed JSON (Status: Keep).
  - `test_partial_json_with_narrative_extraction` – Test extraction of narrative from partial JSON (Status: Keep).
  - `test_json_without_quotes_cleanup` – Test cleanup of JSON-like text without proper quotes (Status: Keep).
  - `test_nested_json_in_narrative` – Test that valid JSON with nested structures in narrative works (Status: Keep).
  - `test_aggressive_cleanup_last_resort` – Test that aggressive cleanup only happens as last resort (Status: Keep).
  - `test_minimal_cleanup_for_json_without_narrative` – Test minimal cleanup when JSON-like but no narrative field (Status: Keep).
  - `test_json_artifact_detection` – Test that JSON artifacts are properly detected. (Status: Keep).
  - `test_dragon_knight_description_cleaning` – Test cleaning of the Dragon Knight campaign description with JSON escapes. (Status: Keep).
  - `test_json_structure_cleaning` – Test cleaning of JSON structure from campaign description. (Status: Keep).
  - `test_god_mode_response_extraction` – Test extraction of god_mode_response from JSON. (Status: Keep).
  - `test_normal_description_preservation` – Test that normal descriptions are preserved. (Status: Keep).
  - `test_story_entry_json_cleaning` – Test that story entries are properly processed to remove JSON artifacts. (Status: Keep).
  - `test_escaped_json_content_cleaning` – Test cleaning of escaped JSON content without structure. (Status: Keep).

---

## `tests/test_json_mode_constants.py`

**Role:** Test that constants have been updated for JSON mode

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestJSONModeConstants` – Test suite for JSON mode constant updates (Status: Keep).
  - `test_character_creation_reminder_no_state_updates` – Test that CHARACTER_DESIGN_REMINDER doesn't instruct to include STATE_UPDATES_PROPOSED (Status: Keep).
  - `test_character_creation_reminder_maintains_other_instructions` – Test that other important instructions are still present (Status: Keep).

---

## `tests/test_json_mode_preference.py`

**Role:** No module docstring; review code to confirm responsibilities.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestJSONModePreference` – Test that JSON mode is always preferred over regex parsing when available (Status: Keep).
  - `setUp` – Set up test fixtures (Status: Keep).
  - `test_json_mode_preferred_over_markdown_blocks` – Test that when both JSON and markdown blocks exist, JSON is used (Status: Keep).
  - `test_no_fallback_parsing_exists` – Test that parse_llm_response_for_state_changes no longer exists (Status: Keep).
  - `test_no_state_updates_when_no_json` – Test that no state updates are available when no JSON response (Status: Keep).
  - `test_strip_debug_content_preserves_json_state_updates` – Test that strip_debug_content doesn't interfere with JSON state updates (Status: Keep).
  - `test_json_extraction_from_code_blocks` – Test JSON extraction from markdown code blocks (Status: Keep).
  - `test_no_double_parsing` – Test that state updates aren't parsed twice (Status: Keep).

---

## `tests/test_json_mode_state_updates.py`

**Role:** Test that state updates work properly in JSON response mode.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestJsonModeStateUpdates` – Test that state updates are properly extracted from JSON responses. (Status: Keep).
  - `setUp` – Set up test environment. (Status: Keep).
  - `test_json_response_with_state_updates` – Test that state updates from JSON response are appended to response text. (Status: Keep).
  - `test_json_response_without_state_updates` – Test that responses without state updates work correctly. (Status: Keep).
  - `test_json_response_with_empty_state_updates` – Test that empty state updates are handled correctly. (Status: Keep).

---

## `tests/test_json_only_comprehensive.py`

**Role:** No module docstring; review code to confirm responsibilities.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestJSONOnlyComprehensive` – Comprehensive test suite to verify JSON mode is the ONLY mode (Status: Keep).
  - `test_no_fallback_in_main_py` – Test that main.py no longer has fallback parsing logic (Status: Keep).
  - `test_gemini_response_logs_error_without_structured` – Test that GeminiResponse logs error when no structured response (Status: Keep).
  - `test_json_mode_always_enabled` – Test that all API calls use JSON mode (Status: Keep).
  - `test_parse_function_removed` – Test that parse_llm_response_for_state_changes is removed (Status: Keep).
  - `test_clean_markdown_helper_removed` – Test that _clean_markdown_from_json helper is removed (Status: Keep).
  - `test_state_updates_only_from_json` – Test that state updates come ONLY from JSON response (Status: Keep).
  - `test_no_state_updates_without_json` – Test that no state updates are available without JSON response (Status: Keep).
  - `test_strip_functions_only_for_display` – Test that strip functions don't affect state parsing (Status: Keep).

---

## `tests/test_json_only_mode.py`

**Role:** No module docstring; review code to confirm responsibilities.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestJSONOnlyMode` – Test that JSON mode is the ONLY mode - no fallbacks to regex parsing (Status: Keep).
  - `test_parse_llm_response_for_state_changes_should_not_exist` – Test that the regex parsing function should not exist (Status: Keep).
  - `test_all_gemini_calls_must_use_json_mode` – Test that all Gemini API calls enforce JSON mode (Status: Keep).
  - `test_main_py_no_fallback_parsing` – Test that main.py doesn't have fallback regex parsing (Status: Keep).
  - `test_no_regex_state_update_extraction` – Test that STATE_UPDATES_PROPOSED regex extraction is removed (Status: Keep).
  - `test_always_structured_response_required` – Test that a structured response is always required (Status: Keep).
  - `test_generation_config_always_includes_json` – Test that generation config always includes JSON response format (Status: Keep).
  - `test_robust_json_parser_is_only_fallback` – Test that robust JSON parser is the only fallback for malformed JSON (Status: Keep).
  - `test_strip_functions_dont_affect_state_parsing` – Test that strip functions are only for display, not state extraction (Status: Keep).
  - `test_error_on_missing_structured_response` – Test that system logs error when structured response is missing (Status: Keep).

---

## `tests/test_json_utils.py`

**Role:** Comprehensive test suite for json_utils.py Tests JSON parsing utilities for handling incomplete or malformed JSON responses

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestCountUnmatchedQuotes` – Test count_unmatched_quotes function (Status: Keep).
  - `test_no_quotes` – Test with text containing no quotes (Status: Keep).
  - `test_matched_quotes` – Test with properly matched quotes (Status: Keep).
  - `test_unmatched_quotes` – Test with unmatched quotes (Status: Keep).
  - `test_escaped_quotes` – Test with escaped quotes (Status: Keep).
  - `test_escaped_backslashes` – Test with escaped backslashes before quotes (Status: Keep).
  - `test_mixed_escape_sequences` – Test with various escape sequences (Status: Keep).
  - `test_complex_json_strings` – Test with complex JSON-like strings (Status: Keep).
- `class TestCountUnmatchedBraces` – Test count_unmatched_braces function (Status: Keep).
  - `test_no_braces` – Test with text containing no braces or brackets (Status: Keep).
  - `test_matched_braces` – Test with properly matched braces (Status: Keep).
  - `test_matched_brackets` – Test with properly matched brackets (Status: Keep).
  - `test_unmatched_braces` – Test with unmatched braces (Status: Keep).
  - `test_unmatched_brackets` – Test with unmatched brackets (Status: Keep).
  - `test_mixed_braces_brackets` – Test with mixed braces and brackets (Status: Keep).
  - `test_braces_in_strings` – Test that braces inside strings are ignored (Status: Keep).
  - `test_escaped_quotes_in_strings` – Test with escaped quotes in strings (Status: Keep).
- `class TestUnescapeJsonString` – Test unescape_json_string function (Status: Keep).
  - `test_no_escape_sequences` – Test with strings containing no escape sequences (Status: Keep).
  - `test_newline_escapes` – Test unescaping newline characters (Status: Keep).
  - `test_tab_escapes` – Test unescaping tab characters (Status: Keep).
  - `test_quote_escapes` – Test unescaping quote characters (Status: Keep).
  - `test_backslash_escapes` – Test unescaping backslash characters (Status: Keep).
  - `test_other_escapes` – Test unescaping other special characters (Status: Keep).
  - `test_multiple_escapes` – Test unescaping multiple different escape sequences (Status: Keep).
  - `test_unicode_preserved` – Test that Unicode characters are preserved (Status: Keep).
- `class TestTryParseJson` – Test try_parse_json function (Status: Keep).
  - `test_valid_json` – Test parsing valid JSON (Status: Keep).
  - `test_invalid_json` – Test parsing invalid JSON (Status: Keep).
  - `test_empty_string` – Test parsing empty string (Status: Keep).
  - `test_null_values` – Test parsing JSON with null values (Status: Keep).
  - `test_numeric_values` – Test parsing JSON with numeric values (Status: Keep).
  - `test_boolean_values` – Test parsing JSON with boolean values (Status: Keep).
- `class TestExtractJsonBoundaries` – Test extract_json_boundaries function (Status: Keep).
  - `test_no_json_markers` – Test with text containing no JSON markers (Status: Keep).
  - `test_simple_json_object` – Test extracting simple JSON objects (Status: Keep).
  - `test_simple_json_array` – Test extracting simple JSON arrays (Status: Keep).
  - `test_nested_json_object` – Test extracting nested JSON objects (Status: Keep).
  - `test_json_with_strings_containing_braces` – Test extracting JSON with strings containing braces (Status: Keep).
  - `test_incomplete_json` – Test with incomplete JSON (Status: Keep).
  - `test_multiple_json_objects` – Test with multiple JSON objects (should extract first) (Status: Keep).
  - `test_escaped_quotes_in_strings` – Test JSON with escaped quotes in strings (Status: Keep).
- `class TestCompleteTruncatedJson` – Test complete_truncated_json function (Status: Keep).
  - `test_empty_string` – Test with empty string (Status: Keep).
  - `test_already_complete_json` – Test with already complete JSON (Status: Keep).
  - `test_missing_closing_brace` – Test completing JSON missing closing braces (Status: Keep).
  - `test_missing_closing_bracket` – Test completing JSON missing closing brackets (Status: Keep).
  - `test_unclosed_string` – Test completing JSON with unclosed strings (Status: Keep).
  - `test_unclosed_string_with_closing_brace` – Test special case of unclosed string with closing brace (Status: Keep).
  - `test_mixed_brackets_and_braces` – Test completing JSON with mixed brackets and braces (Status: Keep).
  - `test_non_json_text` – Test with non-JSON text (Status: Keep).
- `class TestExtractFieldValue` – Test extract_field_value function (Status: Keep).
  - `test_extract_simple_string_field` – Test extracting simple string fields (Status: Keep).
  - `test_extract_nonexistent_field` – Test extracting nonexistent fields (Status: Keep).
  - `test_extract_from_empty_string` – Test extracting from empty string (Status: Keep).
  - `test_extract_field_with_escaped_quotes` – Test extracting fields containing escaped quotes (Status: Keep).
  - `test_extract_field_with_newlines` – Test extracting fields containing newlines (Status: Keep).
  - `test_extract_narrative_field` – Test extracting narrative field (special handling) (Status: Keep).
  - `test_extract_from_malformed_json` – Test extracting from malformed JSON (Status: Keep).
  - `test_extract_nested_field` – Test that nested fields are not extracted (only top-level) (Status: Keep).
  - `test_extract_field_with_special_characters` – Test extracting fields with special characters (Status: Keep).
  - `test_extract_empty_string_value` – Test extracting empty string values (Status: Keep).
  - `test_extract_with_trailing_backslash` – Test extracting incomplete string with trailing backslash (Status: Keep).

---

## `tests/test_loading_messages.py`

**Role:** Tests for loading spinner messages - TASK-005b

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestLoadingMessages` – Test loading spinner with contextual messages (Status: Keep).
  - `test_loading_messages_css_exists` – Test that loading messages CSS file exists (Status: Keep).
  - `test_loading_messages_js_exists` – Test that loading messages JavaScript module exists (Status: Keep).
  - `test_index_html_includes_resources` – Test that index.html includes loading messages resources (Status: Keep).
  - `test_app_js_integration` – Test that app.js integrates with loading messages (Status: Keep).
  - `test_message_content_variety` – Test that various contextual messages exist (Status: Keep).

---

## `tests/test_luke_campaign_jedi_master_gender_fix.py`

**Role:** Test to ensure Luke campaign Jedi Master gender consistency issue is fixed.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestLukeCampaignJediMasterGenderFix` – Test specific to Luke campaign Jedi Master gender issue. (Status: Keep).
  - `test_jedi_master_female_consistency` – Test that Jedi Master gender is enforced and prevents inconsistency. (Status: Keep).
  - `test_prevent_luke_campaign_bug_scenario` – Test that the specific Luke campaign bug scenario is prevented. (Status: Keep).
  - `test_creative_gender_acceptance` – Test that creative gender values are accepted for LLM flexibility. (Status: Keep).

---

## `tests/test_main_enhancements.py`

**Role:** No module docstring; review code to confirm responsibilities.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `client` – Flask test client fixture with proper error handling (Status: Keep).
- `test_flask_app_import` – Test that the Flask app can be imported successfully (Status: Keep).
- `test_flask_app_is_flask_instance` – Test that imported app is a Flask instance (Status: Keep).
- `test_time_endpoint_exists` – Test that the /api/time endpoint exists and works (Status: Keep).
- `test_campaigns_endpoint_requires_auth` – Test that campaigns endpoint requires authentication (Status: Keep).
- `test_campaigns_endpoint_with_test_headers` – Test campaigns endpoint with test bypass headers (Status: Keep).
- `test_settings_endpoint_requires_auth` – Test that settings endpoint requires authentication (Status: Keep).
- `test_settings_endpoint_with_test_headers` – Test settings endpoint with test bypass headers (Status: Keep).
- `test_create_campaign_requires_auth` – Test that campaign creation requires authentication (Status: Keep).
- `test_create_campaign_with_test_headers` – Test campaign creation with test bypass headers (Status: Keep).
- `test_mcp_client_integration` – Test MCP client integration with mocked client (Status: Keep).
- `test_cors_enabled_for_api_routes` – Test that CORS is enabled for API routes (Status: Keep).
- `test_frontend_serving` – Test that frontend is served from root path (Status: Keep).
- `test_invalid_json_handling` – Test proper handling of invalid JSON in requests (Status: Keep).
- `test_nonexistent_campaign_handling` – Test handling of requests for non-existent campaigns (Status: Keep).
- `test_future_annotations_import` – Test that __future__ annotations are properly imported for forward compatibility (Status: Keep).
- `test_import_organization` – Test that imports are properly organized and accessible (Status: Keep).
- `test_mcp_http_flag_default_behavior` – Test MCP HTTP flag default behavior (should default to True - HTTP mode) (Status: Keep).
- `test_mcp_http_flag_explicit_enable` – Test MCP HTTP flag when explicitly enabled (Status: Keep).
- `test_mcp_http_boolean_logic_matrix` – Comprehensive test matrix for MCP HTTP boolean logic (Status: Keep).
- `test_app_configuration_with_mcp_settings` – Test that app configuration includes MCP settings correctly (Status: Keep).
- `test_import_error_handling` – Test that import errors are handled gracefully (Status: Keep).
- `test_async_safety_improvements` – Test that async safety improvements are in place (Status: Keep).
- `test_cli_argument_parsing_safety` – Test that CLI argument parsing handles edge cases safely (Status: Keep).
- `test_threading_safety_with_mcp` – Test threading safety improvements with MCP integration (Status: Keep).

---

## `tests/test_main_error_handling_final.py`

**Role:** Phase 3: Error handling tests for main.py parse_set_command Target: Improve coverage by testing error paths

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestParseSetCommandErrorHandling` – Test error handling in parse_set_command function (Status: Keep).
  - `test_json_decode_errors` – Test handling of invalid JSON values (Status: Keep).
  - `test_empty_values_and_whitespace` – Test handling of empty values and whitespace (Status: Keep).
  - `test_lines_without_equals` – Test lines that don't contain equals sign are ignored (Status: Keep).
  - `test_special_characters_in_values` – Test values containing special characters (Status: Keep).
  - `test_numeric_boolean_null_values` – Test various value types (Status: Keep).
  - `test_arrays_and_objects` – Test complex JSON structures (Status: Keep).
  - `test_edge_cases` – Test various edge cases (Status: Keep).
  - `test_unicode_and_emoji` – Test unicode characters and emoji (Status: Keep).
  - `test_very_long_values` – Test handling of very long values (Status: Keep).
  - `test_escaped_characters` – Test escaped characters in JSON strings (Status: Keep).

---

## `tests/test_main_interaction_structured_fields.py`

**Role:** Tests for structured fields in interaction endpoint through MCP architecture. Tests that structured field handling works through MCP API gateway.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestMCPInteractionStructuredFields` – Test structured fields through MCP interaction endpoint. (Status: Keep).
  - `setUp` – Set up test fixtures for MCP testing. (Status: Keep).
  - `test_mcp_interaction_basic_request` – Test basic interaction request through MCP. (Status: Keep).
  - `test_mcp_interaction_with_structured_response` – Test interaction expecting structured response through MCP. (Status: Keep).
  - `test_mcp_interaction_combat_scenario` – Test combat interaction through MCP. (Status: Keep).
  - `test_mcp_interaction_data_types` – Test interaction response data types through MCP. (Status: Keep).
  - `test_mcp_interaction_error_handling` – Test interaction error handling through MCP. (Status: Keep).
  - `test_mcp_interaction_different_modes` – Test different interaction modes through MCP. (Status: Keep).
  - `test_mcp_interaction_concurrent_requests` – Test concurrent interaction requests through MCP. (Status: Keep).

---

## `tests/test_main_security_validation.py`

**Role:** Tests for main.py security and validation features. Phase 8 - Milestone 8.3

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestSQLInjectionPrevention` – Test SQL injection prevention measures. (Status: Keep).
  - `setUp` – Set up test client and mocks. (Status: Keep).
  - `test_sql_injection_in_campaign_name` – Test that SQL injection attempts in campaign names are sanitized. (Status: Keep).
  - `test_sql_injection_in_user_input` – Test SQL injection attempts in various user inputs. (Status: Keep).
  - `test_nosql_injection_prevention` – Test NoSQL injection prevention in Firestore queries. (Status: Keep).
  - `test_parameterized_query_usage` – Test that queries use parameterized/safe patterns. (Status: Keep).
- `class TestXSSPrevention` – Test XSS (Cross-Site Scripting) prevention measures. (Status: Keep).
  - `setUp` – Set up test environment. (Status: Keep).
  - `test_xss_in_campaign_description` – Test XSS prevention in campaign descriptions. (Status: Keep).
  - `test_script_tag_sanitization` – Test that script tags are properly handled. (Status: Keep).
  - `test_event_handler_removal` – Test that event handlers are neutralized. (Status: Keep).
  - `test_xss_in_json_responses` – Test XSS prevention in JSON API responses. (Status: Keep).
- `class TestRequestSizeLimits` – Test request size limit enforcement. (Status: Keep).
  - `setUp` – Set up test environment. (Status: Keep).
  - `test_request_body_size_limit` – Test that oversized request bodies are rejected. (Status: Keep).
  - `test_header_size_limit` – Test that oversized headers are handled. (Status: Keep).
  - `test_url_length_limit` – Test URL length limits. (Status: Keep).
  - `test_array_size_limits` – Test limits on array/list sizes in requests. (Status: Keep).
- `class TestRateLimitingEnforcement` – Test rate limiting enforcement. (Status: Keep).
  - `setUp` – Set up test environment. (Status: Keep).
  - `test_api_rate_limiting` – Test API rate limiting enforcement. (Status: Keep).
  - `test_rate_limit_headers` – Test rate limit headers are properly set. (Status: Keep).
  - `test_distributed_rate_limiting` – Test distributed rate limiting across multiple instances. (Status: Keep).
  - `test_rate_limit_by_endpoint` – Test different rate limits for different endpoints. (Status: Keep).
- `class TestInputSanitization` – Test input sanitization measures. (Status: Keep).
  - `setUp` – Set up test environment. (Status: Keep).
  - `test_html_entity_encoding` – Test HTML entity encoding for special characters. (Status: Keep).
  - `test_unicode_normalization` – Test Unicode normalization to prevent homograph attacks. (Status: Keep).
  - `test_control_character_removal` – Test removal of control characters. (Status: Keep).
  - `test_nested_encoding_prevention` – Test prevention of nested/double encoding attacks. (Status: Keep).
- `class TestCSRFProtection` – Test CSRF (Cross-Site Request Forgery) protection. (Status: Keep).
  - `setUp` – Set up test environment. (Status: Keep).
  - `test_csrf_token_validation` – Test CSRF token validation on state-changing operations. (Status: Keep).
  - `test_double_submit_cookie` – Test double-submit cookie pattern for CSRF protection. (Status: Keep).
  - `test_origin_header_validation` – Test Origin header validation for CSRF protection. (Status: Keep).
  - `test_safe_methods_exempt` – Test that safe methods don't require CSRF protection. (Status: Keep).
- `class TestPathTraversalAndPayloadAttacks` – Test path traversal and payload attack prevention. (Status: Keep).
  - `setUp` – Set up test environment. (Status: Keep).
  - `test_path_traversal_prevention` – Test prevention of path traversal attacks. (Status: Keep).
  - `test_json_bomb_protection` – Test protection against JSON bomb/billion laughs attacks. (Status: Keep).
  - `test_zip_bomb_prevention` – Test prevention of zip bomb attacks. (Status: Keep).
  - `test_xml_entity_expansion_prevention` – Test prevention of XML entity expansion attacks (XXE). (Status: Keep).

---

## `tests/test_main_state_helper.py`

**Role:** Comprehensive tests for StateHelper class and utility functions in main.py. Focuses on debug content stripping and state management utilities.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class StateHelper` – Test wrapper for state helper functions. (Status: Keep).
  - `strip_debug_content` – Strip debug content from text. (Status: Keep).
  - `strip_state_updates_only` – Strip only state updates from text. (Status: Keep).
  - `strip_other_debug_content` – Strip all debug content except STATE_UPDATES_PROPOSED blocks. (Status: Keep).
- `class TestStateHelper` – Test StateHelper class methods. (Status: Keep).
  - `test_strip_debug_content_basic` – Test basic debug content stripping. (Status: Keep).
  - `test_strip_state_updates_only_basic` – Test stripping only state updates. (Status: Keep).
  - `test_strip_other_debug_content_basic` – Test stripping debug content except state updates. (Status: Keep).
  - `test_apply_automatic_combat_cleanup_basic` – Test automatic combat cleanup. (Status: Keep).
- `class TestUtilityFunctions` – Test utility functions in main.py. (Status: Keep).
  - `test_format_game_state_updates_for_html` – Test format_game_state_updates with HTML formatting. (Status: Keep).
  - `test_format_game_state_updates_for_text` – Test format_game_state_updates with text formatting. (Status: Keep).
  - `test_format_game_state_updates_empty_dict` – Test format_game_state_updates with empty changes. (Status: Keep).
  - `test_format_game_state_updates_complex_nested` – Test format_game_state_updates with complex nested data. (Status: Keep).
- `class TestApplicationConfiguration` – Test application configuration and setup. (Status: Keep).
  - `test_create_app_basic_configuration` – Test basic app creation and configuration. (Status: Keep).
  - `test_create_app_testing_mode` – Test app creation in testing mode. (Status: Keep).
  - `test_cors_configuration` – Test CORS configuration is applied. (Status: Keep).
  - `test_app_route_registration` – Test that routes are properly registered. (Status: Keep).
  - `test_error_handler_registration` – Test that error handlers are registered if they exist. (Status: Keep).
- `class TestConstants` – Test constants and configuration values. (Status: Keep).
  - `test_header_constants` – Test that header constants are properly defined. (Status: Keep).
  - `test_key_constants` – Test that response key constants are properly defined. (Status: Keep).
  - `test_default_test_user` – Test default test user constant. (Status: Keep).
  - `test_cors_resources_configuration` – Test CORS resources configuration. (Status: Keep).

---

## `tests/test_main_structured_response_building.py`

**Role:** Unit tests for main.py structured response building. Tests that the /api/campaigns/{id}/interaction endpoint returns the correct structure.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestMainStructuredResponseBuilding` – Test that main.py builds responses matching the schema (Status: Keep).
  - `setUp` – Set up test data (Status: Keep).
  - `test_response_includes_all_required_fields` – Test that API response includes all fields from structured response (Status: Keep).
  - `test_response_handles_missing_fields_gracefully` – Test that response handles missing optional fields (Status: Keep).
  - `test_debug_info_only_in_debug_mode` – Test that debug_info is included based on debug mode (Status: Keep).
  - `test_nested_field_extraction` – Test extraction of fields from nested structure (Status: Keep).
  - `test_backend_debug_field_filtering_red_green` – RED-GREEN: Test backend debug field filtering based on debug_mode (Status: Keep).
  - `test_comprehensive_debug_response_building_logic` – Restored from test_debug_response_building.py - comprehensive response building test (Status: Keep).
  - `test_character_mode_sequence_id_debug_filtering` – Restored from test_debug_response_building.py - character mode sequence ID test (Status: Keep).

---

## `tests/test_mcp_health.py`

**Role:** Test MCP server health checks to ensure all servers are properly configured. Uses red-green methodology - write failing tests first, then make them pass.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestMCPServerHealth` – Test that all MCP servers are healthy and properly configured. (Status: Keep).
  - `setUp` – Set up test environment. (Status: Keep).
  - `test_react_mcp_server_exists` – Test that react-mcp server is properly installed and configured. (Status: Keep).
  - `test_worldarchitect_game_server_running` – Test that worldarchitect-game server is running on port 7000. (Status: Keep).
  - `test_mcp_config_has_all_servers` – Test that MCP config contains all required servers. (Status: Keep).
  - `test_claude_mcp_script_success` – Test that claude_mcp.sh script runs successfully. (Status: Keep).
  - `test_react_mcp_dependencies_installed` – Test that react-mcp has all dependencies installed. (Status: Keep).
  - `test_worldarchitect_game_service_file` – Test that worldarchitect-game has proper service configuration. (Status: Keep).

---

## `tests/test_memory_integration.py`

**Role:** Test suite for memory integration

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestMemoryIntegration` – No class docstring present; review implementation to confirm behavior. (Status: Keep).
  - `setUp` – No docstring present; review implementation to confirm behavior. (Status: Keep).
  - `test_extract_query_terms` – Test query term extraction (Status: Keep).
  - `test_relevance_scoring` – Test relevance score calculation (Status: Keep).
  - `test_search_with_caching` – Test search with cache behavior (Status: Keep).
  - `test_context_enhancement` – Test context enhancement with memories (Status: Keep).
  - `test_slash_command_enhancement` – Test slash command enhancement (Status: Keep).
  - `test_error_handling` – Test graceful error handling (Status: Keep).
  - `test_metrics_tracking` – Test performance metrics (Status: Keep).

---

## `tests/test_memory_leak_fixes_verification.py`

**Role:** Verification script for CampaignCreationV2 memory leak fixes This script verifies that the memory leak fixes are properly implemented

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `test_memory_leak_fixes` – Test that all memory leak fixes are properly implemented (Status: Keep).
- `test_component_structure` – Test basic component structure (Status: Keep).

---

## `tests/test_milestone_4_interactive_features.py`

**Role:** Test Suite for Milestone 4: Interactive Features Tests campaign wizard, enhanced search, interface manager, and enhanced modals

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestMilestone4InteractiveFeatures` – Test suite for Milestone 4 interactive features (Status: Keep).
  - `setUpClass` – Set up test class (Status: Keep).
  - `setUp` – Set up each test (Status: Keep).
  - `tearDown` – Clean up after each test (Status: Keep).
  - `test_interface_manager_js_exists` – Test that interface manager JavaScript file exists (Status: Keep).
  - `test_campaign_wizard_js_exists` – Test that campaign wizard JavaScript file exists (Status: Keep).
  - `test_enhanced_search_js_exists` – Test that enhanced search JavaScript file exists (Status: Keep).
  - `test_interactive_features_css_exists` – Test that interactive features CSS file exists (Status: Keep).
  - `test_index_html_includes_scripts` – Test that index.html includes all necessary script files (Status: Keep).
  - `test_index_html_has_modern_interface` – Test that index.html supports modern interface system (Status: Keep).
  - `test_javascript_file_structure` – Test JavaScript files have proper structure (Status: Keep).
  - `test_css_modern_mode_selectors` – Test CSS has proper modern mode selectors (Status: Keep).
  - `test_campaign_wizard_html_structure` – Test campaign wizard generates proper HTML structure (Status: Keep).
  - `test_enhanced_search_features` – Test enhanced search has all required features (Status: Keep).
  - `test_interface_manager_feature_control` – Test interface manager can control features (Status: Keep).
  - `test_backward_compatibility` – Test that features maintain backward compatibility (Status: Keep).
  - `test_progressive_enhancement` – Test that features use progressive enhancement (Status: Keep).
  - `test_file_integration_order` – Test that files are loaded in the correct order (Status: Keep).
  - `test_css_theme_integration` – Test CSS integrates properly with existing theme system (Status: Keep).
  - `test_performance_considerations` – Test that features are optimized for performance (Status: Keep).
  - `test_accessibility_features` – Test that interactive features maintain accessibility (Status: Keep).
  - `test_error_handling` – Test that features handle errors gracefully (Status: Keep).
- `run_milestone_4_tests` – Run all Milestone 4 tests (Status: Keep).

---

## `tests/test_mission_conversion_helpers.py`

**Role:** No module docstring; review code to confirm responsibilities.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestMissionConversionHelpers` – Test all branches of the mission conversion logic with comprehensive coverage. (Status: Keep).
  - `setUp` – Set up logging to capture conversion messages. (Status: Keep).
  - `tearDown` – Clean up logging handler. (Status: Keep).
  - `test_missions_dict_with_valid_mission_data` – Test converting dict with valid mission objects. (Status: Keep).
  - `test_missions_dict_with_existing_mission_update` – Test updating existing mission when mission_id matches. (Status: Keep).
  - `test_missions_dict_with_invalid_mission_data` – Test handling invalid mission data (non-dict values). (Status: Keep).
  - `test_missions_dict_with_existing_mission_id_in_data` – Test that existing mission_id in data is preserved. (Status: Keep).
  - `test_missions_non_dict_non_list_value` – Test handling non-dict, non-list values for active_missions. (Status: Keep).
  - `test_missions_initialization_when_missing` – Test that active_missions is initialized when missing. (Status: Keep).
  - `test_missions_initialization_when_wrong_type` – Test that active_missions is reinitialized when wrong type. (Status: Keep).
  - `test_mixed_valid_and_invalid_missions` – Test handling mix of valid and invalid mission data. (Status: Keep).
  - `test_update_mission_preserves_other_fields` – Test that updating mission preserves fields not in the update. (Status: Keep).

---

## `tests/test_mission_handling.py`

**Role:** No module docstring; review code to confirm responsibilities.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestMissionHandling` – Test that the smart conversion for active_missions works correctly. (Status: Keep).
  - `test_ai_dict_format_converts_to_list_append` – Test that AI's dictionary format for missions gets converted to list append. (Status: Keep).
  - `test_updating_existing_mission_by_id` – Test that providing a mission with existing ID updates rather than duplicates. (Status: Keep).
  - `test_ai_provides_list_format_works_normally` – Test that if AI provides correct list format, it works without conversion. (Status: Keep).

---

## `tests/test_narrative_cutoff_bug.py`

**Role:** No module docstring; review code to confirm responsibilities.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestNarrativeCutoffBug` – Test the narrative cutoff bug fix using red/green methodology. (Status: Keep).
  - `setUp` – Set up test data with narratives that would trigger the bug. (Status: Keep).
  - `test_narrative_extraction_with_quotes_RED_phase` – RED PHASE: Demonstrate that a naive regex approach would fail. This test shows how the old approach would cut off the narrative at an embedded quote within the content. (Status: Keep).
  - `test_narrative_extraction_with_quotes_GREEN_phase` – GREEN PHASE: Demonstrate that the fixed implementation works correctly. The new implementation in json_utils.extract_field_value properly handles escaped quotes and extracts the complete narrative. (Status: Keep).
  - `test_complex_nested_quotes` – Test extraction with complex nested quotes and escape sequences. (Status: Keep).
  - `test_incomplete_json_narrative` – Test that incomplete JSON (cut off mid-narrative) still extracts what's available. (Status: Keep).
  - `test_narrative_with_json_special_chars` – Test narratives containing JSON special characters. (Status: Keep).
  - `test_extraction_performance` – Test that the fix handles very long narratives efficiently. (Status: Keep).

---

## `tests/test_narrative_field_clean.py`

**Role:** Test to ensure narrative field never contains debug content. Part of the clean debug/narrative separation initiative.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestNarrativeFieldClean` – Test that narrative fields are clean of debug content. (Status: Keep).
  - `test_narrative_field_with_debug_tags_should_fail` – Test that we can detect debug tags in narrative field. (Status: Keep).
  - `test_clean_narrative_passes` – Test that clean narrative passes validation. (Status: Keep).
  - `test_state_updates_in_correct_field` – Test that state updates are in state_updates field, not narrative. (Status: Keep).

---

## `tests/test_narrative_response_error_handling.py`

**Role:** Tests for narrative response error handling and type conversion

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestNarrativeResponseErrorHandling` – Test coverage for error handling paths in narrative_response_schema.py (Status: Keep).
  - `setUp` – Set up test fixtures (Status: Keep).
  - `test_validate_string_field_with_none` – Test _validate_string_field handles None values (Status: Keep).
  - `test_validate_string_field_with_integer` – Test _validate_string_field converts integers (Status: Keep).
  - `test_validate_string_field_with_float` – Test _validate_string_field converts floats (Status: Keep).
  - `test_validate_string_field_with_boolean` – Test _validate_string_field converts booleans (Status: Keep).
  - `test_validate_string_field_with_dict` – Test _validate_string_field converts dictionaries (Status: Keep).
  - `test_validate_string_field_with_list` – Test _validate_string_field converts lists (Status: Keep).
  - `test_validate_string_field_conversion_error` – Test _validate_string_field handles conversion errors (Status: Keep).
  - `test_validate_list_field_with_none` – Test _validate_list_field handles None values (Status: Keep).
  - `test_validate_list_field_with_non_list` – Test _validate_list_field handles non-list values (Status: Keep).
  - `test_god_mode_fallback_on_narrative_response_error` – Test fallback when NarrativeResponse creation fails but god_mode_response exists (Status: Keep).
  - `test_combine_god_mode_and_narrative_with_none` – Test _combine_god_mode_and_narrative handles None narrative (Status: Keep).
  - `test_combine_god_mode_and_narrative_with_empty` – Test _combine_god_mode_and_narrative handles empty narrative (Status: Keep).
  - `test_malformed_json_with_narrative_field` – Test extraction from malformed JSON with narrative field (Status: Keep).
  - `test_deeply_nested_malformed_json` – Test extraction from deeply nested malformed JSON (Status: Keep).
  - `test_json_with_escaped_characters` – Test handling of JSON with escaped characters (Status: Keep).
  - `test_type_validation_in_structured_fields` – Test type validation in structured fields (Status: Keep).

---

## `tests/test_narrative_response_extraction.py`

**Role:** Unit tests for NarrativeResponse extraction from GeminiResponse. Tests the mapping and validation of structured fields.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestNarrativeResponseExtraction` – Test extraction and mapping of structured fields in NarrativeResponse (Status: Keep).
  - `test_narrative_response_initialization_all_fields` – Test NarrativeResponse initialization with all structured fields (Status: Keep).
  - `test_narrative_response_defaults` – Test NarrativeResponse with minimal required fields (Status: Keep).
  - `test_narrative_response_none_handling` – Test NarrativeResponse handles None values correctly (Status: Keep).
  - `test_type_validation_dice_rolls` – Test dice_rolls type validation (Status: Keep).
  - `test_type_validation_debug_info` – Test debug_info type validation (Status: Keep).
  - `test_string_field_stripping` – Test that string fields are properly stripped of whitespace (Status: Keep).
  - `test_extra_fields_handling` – Test handling of unexpected extra fields (Status: Keep).
  - `test_to_dict_method` – Test conversion to dictionary if method exists (Status: Keep).
  - `test_gemini_response_to_narrative_response_mapping` – Test that GeminiResponse correctly maps to NarrativeResponse fields (Status: Keep).
  - `test_empty_narrative_validation` – Test that empty narrative is handled appropriately (Status: Keep).
  - `test_complex_planning_block_formatting` – Test complex formatting in planning_block field (Status: Keep).

---

## `tests/test_narrative_response_legacy_fallback.py`

**Role:** Tests for legacy JSON cleanup and fallback code in narrative_response_schema.py

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestNarrativeResponseLegacyFallback` – Test coverage for legacy JSON cleanup code (lines 500-557) (Status: Keep).
  - `test_malformed_json_aggressive_cleanup` – Test aggressive cleanup for severely malformed JSON (Status: Keep).
  - `test_json_artifacts_in_text` – Test cleanup of JSON artifacts in narrative text (Status: Keep).
  - `test_nested_json_string_escapes` – Test handling of nested JSON string escapes (Status: Keep).
  - `test_json_with_no_narrative_field` – Test fallback when JSON has no narrative field (Status: Keep).
  - `test_multiple_narrative_patterns` – Test extraction with multiple narrative patterns in text (Status: Keep).
  - `test_json_comma_separator_cleanup` – Test JSON comma separator replacement (Status: Keep).
  - `test_whitespace_normalization` – Test whitespace pattern normalization (Status: Keep).
  - `test_final_json_artifact_check` – Test the final JSON artifact check and cleanup (Status: Keep).
  - `test_deeply_broken_json_with_narrative_hint` – Test extraction from deeply broken JSON with narrative hint (Status: Keep).
  - `test_mixed_valid_and_invalid_json` – Test handling of mixed valid and invalid JSON (Status: Keep).
  - `test_escaped_quotes_in_narrative` – Test handling of escaped quotes in narrative (Status: Keep).
  - `test_partial_json_at_end_of_response` – Test handling when JSON is cut off at the end (Status: Keep).
  - `test_json_with_unicode_characters` – Test handling of Unicode characters in JSON (Status: Keep).
  - `test_completely_non_json_response` – Test handling of completely non-JSON response (Status: Keep).

---

## `tests/test_npc_data_handling.py`

**Role:** No module docstring; review code to confirm responsibilities.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestNPCDataHandling` – Test that the smart handling for npc_data prevents string corruption. (Status: Keep).
  - `test_ai_string_update_converts_to_status_field` – Test that AI's string updates to NPCs get converted to status field updates. (Status: Keep).
  - `test_ai_updates_specific_npc_fields` – Test that AI can update specific fields of an NPC normally. (Status: Keep).
  - `test_ai_delete_npc_with_delete_token` – Test that AI can properly delete an NPC using __DELETE__ token. (Status: Keep).
  - `test_ai_creates_new_npc_correctly` – Test that AI can create a new NPC with proper dictionary structure. (Status: Keep).
  - `test_mixed_updates_in_single_change` – Test handling mixed updates - some NPCs get strings, others get dicts. (Status: Keep).

---

## `tests/test_npc_gender_consistency_red_green.py`

**Role:** Red-Green test for NPC gender consistency issue.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestNPCGenderConsistencyRedGreen` – Red-Green test for NPC gender consistency. (Status: Keep).
  - `test_red_npc_missing_gender_field` – RED TEST: NPC creation should fail without mandatory gender field. (Status: Keep).
  - `test_green_npc_with_mandatory_gender_field` – GREEN TEST: NPC class should have mandatory gender field. (Status: Keep).
  - `test_green_npc_gender_validation` – GREEN TEST: Gender field should be validated. (Status: Keep).
  - `test_green_npc_gender_prevents_inconsistency` – GREEN TEST: Gender field should prevent narrative inconsistency. (Status: Keep).
  - `test_edge_cases_gender_field` – Test edge cases for gender field. (Status: Keep).

---

## `tests/test_null_narrative_bug_fix.py`

**Role:** Test for the null narrative bug fix.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestNullNarrativeBugFix` – Test the fix for the null narrative raw JSON display bug. (Status: Keep).
  - `test_null_narrative_field_no_raw_json` – Test that null narrative field doesn't show raw JSON. (Status: Keep).
  - `test_missing_narrative_field_no_raw_json` – Test that missing narrative field doesn't show raw JSON. (Status: Keep).
  - `test_empty_string_narrative_works` – Test that empty string narrative works correctly. (Status: Keep).
  - `test_normal_narrative_still_works` – Test that normal narrative processing still works. (Status: Keep).
  - `test_god_mode_response_with_null_narrative` – Test god mode response handling with null narrative. (Status: Keep).

---

## `tests/test_numeric_field_converter.py`

**Role:** Test cases for refactored NumericFieldConverter

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestNumericFieldConverter` – Test refactored NumericFieldConverter functionality (Status: Keep).
  - `test_try_convert_to_int_success` – Test successful string to int conversion (Status: Keep).
  - `test_try_convert_to_int_failure` – Test failed conversion returns original value (Status: Keep).
  - `test_try_convert_to_int_non_string` – Test non-string values are returned unchanged (Status: Keep).
  - `test_convert_dict_with_fields` – Test dictionary conversion with specified numeric fields (Status: Keep).
  - `test_convert_dict_with_fields_nested` – Test nested dictionary conversion (Status: Keep).
  - `test_convert_dict_with_fields_list` – Test list processing in dictionary conversion (Status: Keep).
  - `test_convert_all_possible_ints` – Test converting all possible integer strings (Status: Keep).
  - `test_convert_all_possible_ints_nested` – Test convert_all_possible_ints with nested structures (Status: Keep).
  - `test_legacy_convert_value` – Test legacy convert_value method for backward compatibility (Status: Keep).
  - `test_legacy_convert_dict` – Test legacy convert_dict method for backward compatibility (Status: Keep).
  - `test_invalid_data_handling` – Test handling of invalid data types (Status: Keep).

---

## `tests/test_performance_config.py`

**Role:** Global test performance configuration for fast test execution. This module provides aggressive mocking of expensive operations to speed up tests. Import this module in tests that need fast execution with minimal overhead.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `setup_fast_mode_mocks` – Set up aggressive mocking for fast test execution. (Status: Keep).
- `cleanup_fast_mode_mocks` – Clean up fast mode mocks. (Status: Keep).
- `setup_ci_fast_mode` – Set up fast mode for CI environment. (Status: Keep).
- `print_performance_config` – Print current performance configuration. (Status: Keep).

---

## `tests/test_planning_block_analysis.py`

**Role:** Tests for planning block analysis field handling and Deep Think mode

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestPlanningBlockAnalysis` – Test coverage for Deep Think planning blocks with analysis fields (Status: Keep).
  - `setUp` – Set up test fixtures (Status: Keep).
  - `test_planning_block_with_analysis_pros_cons` – Test planning block with pros/cons analysis structure (Status: Keep).
  - `test_analysis_field_with_xss_attempts` – Test that analysis fields are properly sanitized against XSS (Status: Keep).
  - `test_analysis_with_nested_structures` – Test analysis field with deeply nested data structures (Status: Keep).
  - `test_analysis_field_type_variations` – Test analysis field with various data types (Status: Keep).
  - `test_missing_analysis_field` – Test planning blocks without analysis field work correctly (Status: Keep).

---

## `tests/test_planning_block_robustness.py`

**Role:** Test planning block robustness and edge case handling. Tests validation of null, empty, and malformed planning blocks. Now tests JSON-only planning block format.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestPlanningBlockRobustness` – Test edge cases and robustness for JSON planning blocks (Status: Keep).
  - `test_null_planning_block` – Test handling of null planning block (Status: Keep).
  - `test_empty_string_planning_block` – Test handling of empty string planning block (Status: Keep).
  - `test_whitespace_only_planning_block` – Test handling of whitespace-only planning block (Status: Keep).
  - `test_non_string_planning_block` – Test handling of non-string/dict planning block values (Status: Keep).
  - `test_json_like_planning_block` – Test detection of JSON-like string planning blocks (Status: Keep).
  - `test_extremely_long_planning_block` – Test handling of very long planning blocks (Status: Keep).
  - `test_null_bytes_in_planning_block` – Test handling of null bytes in planning block (Status: Keep).
  - `test_other_structured_fields_validation` – Test validation of other structured fields (Status: Keep).
  - `test_to_dict_with_edge_cases` – Test to_dict method with edge case values (Status: Keep).
  - `test_special_characters_in_planning_block` – Test handling of special characters (Status: Keep).
  - `test_valid_planning_block_structure` – Test valid JSON planning block structure (Status: Keep).

---

## `tests/test_planning_block_validation_integration.py`

**Role:** Integration tests for planning block validation and logging. Tests the complete flow of _validate_and_enforce_planning_block with all logging paths.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestPlanningBlockValidationIntegration` – Integration tests for planning block validation with comprehensive logging coverage. (Status: Keep).
  - `setUp` – Set up test fixtures. (Status: Keep).
  - `test_character_creation_detection_case_insensitive` – Test character creation detection with case insensitivity. (Status: Keep).
  - `test_planning_block_regeneration_logging` – Test planning block regeneration with all logging paths. (Status: Keep).
  - `test_planning_block_early_return_when_already_set` – Test early return when planning_block is already set. (Status: Keep).
  - `test_planning_block_validation_success_logging` – Test planning block validation success logging. (Status: Keep).
  - `test_planning_block_validation_failure_logging` – Test planning block validation failure logging. (Status: Keep).
  - `test_planning_block_exception_logging` – Test planning block exception logging with traceback. (Status: Keep).
  - `test_planning_block_source_logging` – Test planning block source logging (structured vs raw). (Status: Keep).
  - `test_planning_block_parsing_logging` – Test planning block parsing step logging. (Status: Keep).
  - `test_fallback_logging` – Test fallback logging when exceptions occur. (Status: Keep).
  - `test_crash_safety_with_malformed_inputs` – Test that the function doesn't crash with malformed inputs. (Status: Keep).
  - `test_unicode_handling_in_logging` – Test that logging handles unicode characters safely. (Status: Keep).

---

## `tests/test_planning_blocks_ui.py`

**Role:** Test script for planning block UI buttons functionality. This tests the parsing and rendering of planning blocks as clickable buttons.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestPlanningBlocksUI` – Test cases for planning block button rendering (Status: Keep).
  - `test_standard_planning_block_format` – Test standard planning block with three choices (Status: Keep).
  - `test_deep_think_block_format` – Test deep think block with pros and cons (Status: Keep).
  - `test_choice_text_extraction` – Test that the full choice text is properly extracted (Status: Keep).
  - `test_special_characters_preserved` – Test that normal special characters are preserved (not HTML escaped) (Status: Keep).

---

## `tests/test_pr_changes_runner.py`

**Role:** Simple test runner for PR changes that avoids import issues

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `run_pr_change_tests` – Run all PR change validation tests (Status: Keep).

---

## `tests/test_production_parity.py`

**Role:** Production Parity Tests - Test production environment configurations Tests that catch differences between test and production environments, specifically response format compatibility issues.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `has_firebase_credentials` – Check if Firebase credentials are available. (Status: Keep).
- `class TestProductionParity` – Test production-like configurations to catch parity issues. (Status: Keep).
  - `setUp` – Set up test client for production parity testing. (Status: Keep).
  - `tearDown` – Restore original environment. (Status: Keep).
  - `test_campaigns_list_response_format_compatibility` – Test that campaigns list response format is frontend-compatible. This test verifies that: 1. The response has the expected structure 2. The 'campaigns' field contains an array 3. Frontend destructuring { data: campaigns } will work correctly (Status: Keep).
  - `test_direct_calls_mode_response_format` – Test response format when using direct calls mode (default). This tests the production configuration where world_logic.py functions are called directly without HTTP overhead. (Status: Keep).

---

## `tests/test_prompts.py`

**Role:** No module docstring; review code to confirm responsibilities.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestPromptLoading` – No class docstring present; review implementation to confirm behavior. (Status: Keep).
  - `setUp` – Clear the instruction cache before each test to ensure isolation. (Status: Keep).
  - `test_all_prompts_are_loadable_via_service` – Ensures that all referenced prompt files can be loaded successfully by calling the actual _load_instruction_file function. (Status: Keep).
  - `test_loading_unknown_prompt_raises_error` – Ensures that calling _load_instruction_file with an unknown type correctly raises a ValueError, following the strict loading policy. (Status: Keep).
  - `test_all_prompt_files_are_registered_in_service` – Ensures that every .md file in the prompts directory is registered in the llm_service.PATH_MAP, and vice-versa. This prevents un-loaded or orphaned prompt files. (Status: Keep).
  - `test_all_registered_prompts_are_actually_used` – Ensures that every prompt registered in PATH_MAP is actually used somewhere in the codebase. This prevents dead/unused prompts. (Status: Keep).

---

## `tests/test_qwen_matrix.py`

**Role:** Matrix-Enhanced TDD Tests for Cerebras/Qwen Command Integration Following comprehensive test matrix approach from /tdd command

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class QwenCommandMatrixTests` – Matrix-driven tests covering all qwen command scenarios (Status: Keep).
  - `setUp` – Set up test environment for each matrix test (Status: Keep).
  - `tearDown` – Restore environment after each test (Status: Keep).
  - `test_matrix_1_1_cerebras_valid_key` – [1,1] Cerebras with valid CEREBRAS_API_KEY → Fast generation + timing (Status: Keep).
  - `test_matrix_1_2_cerebras_fallback_key` – [1,2] Cerebras with OPENAI_API_KEY fallback → Fallback auth working (Status: Keep).
  - `test_matrix_1_3_cerebras_missing_keys` – [1,3] Cerebras with missing keys → Clear error message (Status: Keep).
  - `test_matrix_3_1_simple_code_request` – [3,1] Simple code request with project context → Code generation (Status: Keep).
  - `test_matrix_3_4_empty_prompt` – [3,4] Empty prompt → Usage error (Status: Keep).
  - `test_matrix_3_5_special_characters` – [3,5] Special characters in prompt → Proper escaping (Status: Keep).
  - `test_matrix_4_1_cerebras_timing_display` – [4,1] Cerebras timing display format → Rocket emojis and ms (Status: Keep).
  - `test_matrix_5_1_concise_output` – [5,1] System prompt 'Be concise, direct' → No verbose explanations (Status: Keep).
  - `test_matrix_5_2_no_comments_unless_asked` – [5,2] System prompt 'NEVER add comments' → Code without comments (Status: Keep).

---

## `tests/test_react_v2_tdd_critical_issues.py`

**Role:** TDD Test Suite for React V2 Critical Issues This test suite follows Red-Green-Refactor methodology to drive fixes for critical issues identified in the React V2 audit: 1. Hardcoded "Ser Arion" character names 2. "intermediate • fantasy" text clutter 3. Broken URL routing for /campaign/:id 4. Missing settings functionality Each test will initially FAIL (RED), driving implementation of fixes (GREEN).

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class ReactV2CriticalIssuesTDD` – TDD test suite for React V2 critical issues (Status: Keep).
  - `setUp` – Set up test environment (Status: Keep).
  - `test_hardcoded_ser_arion_removed_from_tsx_red` – 🔴 RED TEST: CampaignCreationV2.tsx should not contain hardcoded "Ser Arion" This will FAIL because audit found hardcoded character names (Status: Keep).
  - `test_intermediate_fantasy_text_removed_red` – 🔴 RED TEST: Campaign cards should not show "intermediate • fantasy" clutter This will FAIL because audit found unwanted text display (Status: Keep).
  - `test_campaign_id_routing_implemented_red` – 🔴 RED TEST: /campaign/:id URLs should route properly This will FAIL because routing is not implemented (Status: Keep).
  - `test_settings_button_exists_red` – 🔴 RED TEST: Settings button should exist beside "Create Campaign" This will FAIL because settings functionality is missing (Status: Keep).
  - `test_sign_out_functionality_exists_red` – 🔴 RED TEST: Sign out functionality should be accessible This will FAIL because sign-out feature is missing (Status: Keep).
  - `test_campaign_creation_uses_user_input_green` – 🟢 GREEN TEST: Campaign creation should use actual user input, not hardcoded values This will pass after we fix hardcoded names (Status: Keep).
  - `test_clean_campaign_card_display_green` – 🟢 GREEN TEST: Campaign cards should display clean, user-friendly information This will pass after we remove text clutter (Status: Keep).
  - `test_gameplay_view_no_infinite_renders_red` – 🔴 RED TEST: GamePlayView component should not cause infinite re-render loops This will FAIL because of useEffect dependency issue causing "Too many re-renders" React error (Status: Keep).
  - `test_gameplay_view_stable_useeffect_green` – 🟢 GREEN TEST: GamePlayView useEffect should have stable dependencies This will pass after we fix the infinite render dependency issue (Status: Keep).
  - `test_full_campaign_creation_workflow_integration` – 🟢 INTEGRATION: Complete campaign creation workflow without hardcoded interference This validates the entire flow after all fixes are implemented (Status: Keep).
- `run_tdd_test_suite` – Run the TDD test suite and report RED/GREEN status (Status: Keep).

---

## `tests/test_real_json_bug_reproduction.py`

**Role:** Test to reproduce the exact JSON bug from user's campaign.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestRealJsonBugReproduction` – Test to reproduce the exact JSON bug the user is experiencing. (Status: Keep).
  - `test_user_exact_scene_2_json` – Test the exact JSON structure from user's Scene #2. (Status: Keep).
  - `test_user_simplified_version` – Test a simplified version to isolate the issue. (Status: Keep).

---

## `tests/test_red_green_json_fix.py`

**Role:** Red/Green Testing for JSON Display Bug Fix This test demonstrates the bug by first showing failing tests (red state) and then showing passing tests with the fix (green state).

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestRedGreenJSONFix` – Red/Green test suite for JSON display bug (Status: Keep).
  - `setUp` – Set up test cases that reproduce the actual bug (Status: Keep).
  - `test_red_state_raw_json_displayed` – RED TEST: Demonstrates the bug where raw JSON is shown to users This test would FAIL without the fix because parse_structured_response would return the raw JSON string when parsing fails. (Status: Keep).
  - `test_red_state_markdown_wrapped_json` – RED TEST: AI returns JSON wrapped in markdown code blocks Without the fix, this returns the markdown-wrapped JSON string. (Status: Keep).
  - `test_red_state_partial_json_fallback` – RED TEST: Partial JSON that can't be parsed Without fallback extraction, users see broken JSON. (Status: Keep).
  - `test_red_state_escaped_characters` – RED TEST: JSON with escaped characters like \n and \" Without proper unescaping, users see escape sequences. (Status: Keep).
  - `test_green_state_comprehensive_fix` – GREEN TEST: Demonstrates the complete fix working This shows all the fix components working together. (Status: Keep).
  - `test_simulate_red_state` – SIMULATION: What the bug looked like before the fix This simulates the red state by showing what would happen without our parsing improvements. (Status: Keep).
- `run_red_green_tests` – Run the red/green test suite with detailed output (Status: Keep).

---

## `tests/test_robust_json_parser.py`

**Role:** Comprehensive test suite for robust_json_parser.py Tests the RobustJSONParser class and parse_llm_json_response function

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestRobustJSONParser` – Test the RobustJSONParser class (Status: Keep).
  - `setUp` – Set up test fixtures (Status: Keep).
  - `test_parse_valid_json` – Test parsing valid JSON returns correct result (Status: Keep).
  - `test_parse_empty_string` – Test parsing empty string returns None (Status: Keep).
  - `test_parse_incomplete_json_missing_brace` – Test parsing JSON missing closing brace (Status: Keep).
  - `test_parse_incomplete_json_unclosed_string` – Test parsing JSON with unclosed string (Status: Keep).
  - `test_parse_json_with_extra_text` – Test parsing JSON with surrounding text (Status: Keep).
  - `test_parse_malformed_json_unquoted_keys` – Test parsing JSON with unquoted keys (Status: Keep).
  - `test_parse_deeply_nested_incomplete` – Test parsing deeply nested incomplete JSON (Status: Keep).
  - `test_logging_on_successful_fix` – Test that successful fixes are logged (Status: Keep).
  - `test_extract_fields_from_severely_malformed` – Test field extraction from severely malformed JSON (Status: Keep).
- `class TestParseSpecificFields` – Test parsing of specific fields (Status: Keep).
  - `test_extract_narrative_field` – Test extraction of narrative field specifically (Status: Keep).
  - `test_extract_entities_mentioned` – Test extraction of entities_mentioned array (Status: Keep).
  - `test_extract_location_confirmed` – Test extraction of location_confirmed field (Status: Keep).
- `class TestParseLLMJsonResponse` – Test the parse_llm_json_response function (Status: Keep).
  - `test_parse_complete_response` – Test parsing complete LLM response (Status: Keep).
  - `test_parse_incomplete_response` – Test parsing incomplete LLM response (Status: Keep).
  - `test_parse_non_json_response` – Test parsing non-JSON response falls back to treating as narrative (Status: Keep).
  - `test_parse_missing_required_fields` – Test that missing required fields are added with defaults (Status: Keep).
  - `test_parse_partial_fields` – Test parsing response with only some fields (Status: Keep).
  - `test_logging_when_no_json_found` – Test that appropriate logging occurs when no JSON is found (Status: Keep).
- `class TestRealWorldScenarios` – Test with real-world LLM response scenarios (Status: Keep).
  - `test_parse_truncated_narrative` – Test the example from the module (Status: Keep).
  - `test_parse_json_with_unicode` – Test parsing JSON containing unicode characters (Status: Keep).
  - `test_parse_json_with_newlines` – Test parsing JSON with embedded newlines (Status: Keep).

---

## `tests/test_scene_numbering.py`

**Role:** No module docstring; review code to confirm responsibilities.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestSceneNumbering` – Test that user-facing scene numbers only increment for AI responses. (Status: Keep).
  - `test_user_scene_numbering` – Test that user_scene_number only increments for gemini responses. (Status: Keep).

---

## `tests/test_settings_api.py`

**Role:** Tests for settings page API endpoints in MCP architecture. These tests verify that the API gateway properly handles settings requests.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestSettingsAPI` – Tests for settings API endpoints in MCP architecture. (Status: Keep).
  - `setUp` – Set up test client and authentication headers. (Status: Keep).
  - `test_settings_page_route_works` – Test that settings page route works in MCP architecture. (Status: Keep).
  - `test_settings_api_endpoint_works` – Test that settings API endpoint works in MCP architecture. (Status: Keep).
  - `test_update_settings_api_works` – Test that settings update API works in MCP architecture. (Status: Keep).
  - `test_settings_endpoints_auth_behavior` – Test that settings endpoints handle authentication in MCP architecture. (Status: Keep).

---

## `tests/test_squash_merge_detection.py`

**Role:** Unit tests for squash-merge detection functionality in integrate.sh Tests the critical bug fixes for false positive detection.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestSquashMergeDetection` – Test squash-merge detection functionality and bug fixes. (Status: Keep).
  - `setUp` – Set up test fixtures. (Status: Keep).
  - `test_integrate_script_syntax` – Test that integrate.sh has valid bash syntax. (Status: Keep).
  - `test_detect_function_exists` – Test that detect_squash_merged_commits function exists. (Status: Keep).
  - `test_regex_bug_fix` – Test that the sed regex requires at least one digit. (Status: Keep).
  - `test_empty_string_check` – Test that empty string check is present to prevent false positives. (Status: Keep).
  - `test_fixed_strings_flag` – Test that --fixed-strings flag is used with git log --grep. (Status: Keep).
  - `test_sed_regex_behavior` – Test the actual sed regex behavior with various inputs. (Status: Keep).
  - `test_critical_false_positive_cases` – Test specific cases that would cause false positives. (Status: Keep).
  - `test_function_integration_points` – Test that the function is called at the right place in integrate.sh. (Status: Keep).
  - `test_error_handling_and_safety` – Test that the function has proper error handling. (Status: Keep).
- `class TestSquashMergeRegexEdgeCases` – Additional edge case tests for the regex patterns. (Status: Keep).
  - `test_regex_anchoring` – Test that regex is properly anchored to end of string. (Status: Keep).
  - `test_whitespace_handling` – Test proper whitespace handling in regex. (Status: Keep).

---

## `tests/test_state_update_integration.py`

**Role:** Integration tests for state update flow in the JSON response system. This test suite specifically targets Bug 1: LLM Not Respecting Character Actions by testing the complete flow from AI response to state application.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestStateUpdateIntegration` – Test the complete state update flow from AI response to game state (Status: Keep).
  - `setUp` – Set up test fixtures and mock objects (Status: Keep).
  - `tearDown` – Clean up test fixtures (Status: Keep).
  - `test_state_updates_extracted_from_json_response` – Test that state updates are properly extracted from JSON response (Status: Keep).
  - `test_state_updates_separated_from_narrative` – Test that state updates don't leak into narrative text (Status: Keep).
  - `test_response_without_state_updates` – Test handling of responses without state updates (Status: Keep).
  - `test_malformed_state_updates_handling` – Test graceful handling of malformed state updates (Status: Keep).
  - `test_llm_service_state_update_processing` – Test that Gemini service properly processes state updates (Status: Keep).
  - `test_state_update_application_simulation` – Test simulation of state update application to game state (Status: Keep).
  - `test_consecutive_state_updates` – Test that consecutive actions properly update state (Status: Keep).
  - `test_state_update_field_completeness` – Test that all expected state update fields are present (Status: Keep).
  - `test_state_update_data_types` – Test that state update fields have correct data types (Status: Keep).
  - `test_empty_state_updates_handling` – Test handling of empty state updates (Status: Keep).
- `class TestStateUpdatePersistence` – Test that state updates are properly persisted and don't get lost (Status: Keep).
  - `test_state_update_debug_logging` – Test that state updates are logged for debugging (Status: Keep).

---

## `tests/test_state_updates_json_parsing.py`

**Role:** No module docstring; review code to confirm responsibilities.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestStateUpdatesJSONParsing` – Test that state updates are properly extracted from JSON responses, not markdown blocks (Status: Keep).
  - `setUp` – Set up test fixtures (Status: Keep).
  - `test_state_updates_extracted_from_json_response` – Test that state updates are properly extracted from GeminiResponse object (Status: Keep).
  - `test_main_py_uses_json_state_updates_not_markdown_blocks` – Test that main.py correctly uses state_updates from structured response (Status: Keep).
  - `test_no_state_updates_proposed_blocks_in_json_mode` – Test that system doesn't look for [STATE_UPDATES_PROPOSED] blocks in JSON mode (Status: Keep).
  - `test_empty_state_updates_handled_gracefully` – Test that empty or None state updates are handled properly (Status: Keep).
  - `test_state_updates_with_complex_nested_structures` – Test that complex nested state updates are preserved correctly (Status: Keep).

---

## `tests/test_structured_fields_storage.py`

**Role:** Test to verify that structured fields are properly stored and retrieved.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `test_structured_fields_storage` – Test that structured fields are stored and retrieved correctly. (Status: Keep).

---

## `tests/test_structured_fields_utils.py`

**Role:** Unit tests for `structured_fields_utils.extract_structured_fields`.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestStructuredFieldsUtils` – Test cases for structured_fields_utils.extract_structured_fields function. (Status: Keep).
  - `setUp` – Set up test fixtures for each test. (Status: Keep).
  - `test_extract_structured_fields_with_full_data` – Test extraction with complete structured response data. (Status: Keep).
  - `test_extract_structured_fields_with_empty_fields` – Test extraction with empty structured response fields. (Status: Keep).
  - `test_extract_structured_fields_with_missing_attributes` – Test extraction when structured response lacks some attributes. (Status: Keep).
  - `test_extract_structured_fields_with_no_structured_response` – Test extraction when GeminiResponse has no structured_response. (Status: Keep).
  - `test_extract_structured_fields_with_none_values` – Test extraction when structured response has None values. (Status: Keep).
  - `test_extract_structured_fields_constants_mapping` – Test that function uses correct constants for field names. (Status: Keep).
  - `test_extract_structured_fields_with_complex_debug_info` – Test extraction with complex debug info structure. (Status: Keep).
  - `test_extract_structured_fields_with_long_text_fields` – Test extraction with longer text content. (Status: Keep).

---

## `tests/test_structured_generation.py`

**Role:** Test structured generation implementation

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestStructuredGeneration` – Test structured generation components (Status: Keep).
  - `setUp` – Set up test data (Status: Keep).
  - `test_narrative_response_schema` – Test NarrativeResponse model (Status: Keep).
  - `test_entity_tracking_instruction` – Test EntityTrackingInstruction creation (Status: Keep).
  - `test_structured_prompt_injection` – Test prompt injection creation (Status: Keep).
  - `test_parse_structured_response_valid_json` – Test parsing valid JSON response (Status: Keep).
  - `test_parse_structured_response_with_extra_text` – Test parsing JSON with extra text around it (Status: Keep).
  - `test_parse_structured_response_fallback` – Test fallback for invalid JSON (Status: Keep).
  - `test_validate_entity_coverage_perfect` – Test entity coverage validation with perfect coverage (Status: Keep).
  - `test_validate_entity_coverage_missing` – Test entity coverage validation with missing entities (Status: Keep).
  - `test_integration_with_entity_tracking` – Test integration with existing entity tracking system (Status: Keep).

---

## `tests/test_structured_response_extraction.py`

**Role:** Unit tests for structured response field extraction and processing. Tests the correct handling of the schema from game_state_instruction.md

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestStructuredResponseExtraction` – Test extraction and processing of structured response fields (Status: Keep).
  - `setUp` – Set up test data matching the schema (Status: Keep).
  - `test_structured_response_has_correct_fields` – Test that response has all required fields from schema (Status: Keep).
  - `test_debug_info_structure` – Test that debug_info contains dice_rolls and resources (Status: Keep).
  - `test_narrative_contains_structured_content` – Test that narrative contains session header and planning block (Status: Keep).
  - `test_state_updates_structure` – Test state_updates field structure (Status: Keep).
  - `test_god_mode_response_handling` – Test god_mode_response field handling (Status: Keep).
  - `test_entities_and_location_fields` – Test entities_mentioned and location_confirmed fields (Status: Keep).
  - `test_narrative_response_object_mapping` – Test that NarrativeResponse object maps fields correctly (Status: Keep).
  - `test_empty_state_updates_handling` – Test that empty state_updates is handled correctly (Status: Keep).

---

## `tests/test_subprocess_security.py`

**Role:** Test subprocess security vulnerabilities in copilot utils. Tests the security fix for shell=True usage in check_merge_tree function. Following TDD approach: test the vulnerability, then verify the fix.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestSubprocessSecurity` – Test subprocess security in GitCommands. (Status: Keep).
  - `test_check_merge_tree_no_shell_injection` – Test that check_merge_tree is not vulnerable to shell injection. (Status: Keep).
  - `test_check_merge_tree_injection_attempt` – Test that malicious input cannot be injected through shell. (Status: Keep).
  - `test_all_git_commands_secure_subprocess` – Test that all GitCommands methods use secure subprocess calls. (Status: Keep).
  - `test_original_vulnerability_pattern` – Test that the original vulnerable pattern would fail this test. This test documents what the vulnerability looked like before the fix. If this test passes, it means the vulnerability has been fixed. (Status: Keep).
  - `test_merge_tree_uses_remote_tracking_refs` – Test that merge_tree uses origin/branch for CI/shallow clone reliability. RED PHASE: This test will fail until we fix the branch reference issue. (Status: Keep).

---

## `tests/test_syntax.py`

**Role:** No module docstring; review code to confirm responsibilities.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestModuleSyntax` – No class docstring present; review implementation to confirm behavior. (Status: Keep).
  - `test_all_python_files_syntax` – Test that all Python files have valid syntax - would catch f-string errors. (Status: Keep).
  - `test_llm_service_import` – Tests if the llm_service.py module can be imported. A failure here indicates a syntax error in the file. (Status: Keep).

---

## `tests/test_syntax_comprehensive.py`

**Role:** No module docstring; review code to confirm responsibilities.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestComprehensiveSyntax` – Comprehensive syntax and import testing that would catch the f-string error. This test ensures all Python files can be parsed and core modules imported. (Status: Keep).
  - `test_all_python_files_syntax` – Test that all Python files in the project have valid syntax using AST parsing. (Status: Keep).
  - `test_game_state_syntax_and_import` – Specifically test game_state.py syntax and import. (Status: Keep).
  - `test_main_module_syntax` – Test that main.py has valid syntax and can load its dependencies. (Status: Keep).
  - `test_basic_game_state_instantiation` – Test basic GameState instantiation without combat-specific features. (Status: Keep).

---

## `tests/test_think_block_protocol.py`

**Role:** Unit tests for Think Block State Management Protocol Tests the critical think block behavior to ensure: 1. Think blocks generate only internal thoughts + options 2. AI waits for player selection after think blocks 3. Invalid inputs get proper error responses 4. Valid selections continue narrative 5. No narrative progression without explicit choice This addresses the bug where LLM continued taking actions after think blocks instead of waiting for player input.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestThinkBlockProtocol` – Test cases for Think Block State Management Protocol (Status: Keep).
  - `setUp` – Set up test environment (Status: Keep).
  - `test_think_block_protocol_exists_in_prompt` – Test that think block protocol is present in the prompt file (Status: Keep).
  - `test_think_keywords_detection` – Test that all think block keywords are properly defined (Status: Keep).
  - `test_forbidden_actions_defined` – Test that forbidden actions are clearly defined (Status: Keep).
  - `test_valid_input_definitions` – Test that valid post-think-block inputs are defined (Status: Keep).
  - `test_invalid_input_definitions` – Test that invalid post-think-block inputs are defined (Status: Keep).
  - `test_error_response_format_defined` – Test that error response format is specified (Status: Keep).
  - `test_state_validation_checkpoints` – Test that state validation checkpoints are defined (Status: Keep).
  - `test_protocol_presence` – Test that think block protocol is present somewhere in the file (Status: Keep).
  - `test_protocol_overrides_other_instructions` – Test that protocol explicitly states it overrides other instructions (Status: Keep).
- `class TestThinkBlockScenarios` – Test specific think block scenarios and expected behaviors (Status: Keep).
  - `setUp` – Set up test scenarios (Status: Keep).
  - `test_simple_think_scenario` – Test simple think command scenario (Status: Keep).
  - `test_complex_planning_scenario` – Test complex planning scenario (Status: Keep).
  - `test_invalid_continuation_scenario` – Test invalid continuation after think block (Status: Keep).
  - `test_valid_selection_scenario` – Test valid option selection after think block (Status: Keep).
- `class TestPromptFileIntegrity` – Test that prompt file changes don't break existing functionality (Status: Keep).
  - `setUp` – Set up file integrity tests (Status: Keep).
  - `test_prompt_file_exists` – Test that the prompt file exists (Status: Keep).
  - `test_prompt_file_readable` – Test that the prompt file is readable (Status: Keep).
  - `test_backup_file_exists` – Test that backup file was created (Status: Keep).
  - `test_essential_protocols_preserved` – Test that essential game protocols are preserved (Status: Keep).
- `class TestThinkBlockStateManagement` – Test state management aspects of think block protocol (Status: Keep).
  - `test_waiting_state_definition` – Test that planning block state is defined (Status: Keep).
  - `test_state_transition_rules` – Test that state transition rules are clearly defined (Status: Keep).
- `run_think_block_tests` – Run all think block protocol tests (Status: Keep).

---

## `tests/test_time_consolidation.py`

**Role:** Unit tests for time consolidation functionality in GameState. Tests the migration of separate time_of_day fields into unified world_time objects.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestTimeConsolidation` – Test cases for time tracking consolidation. (Status: Keep).
  - `test_legacy_time_migration` – Test migration of legacy separate time_of_day field. (Status: Keep).
  - `test_time_of_day_calculation` – Test automatic calculation of time_of_day from hour. (Status: Keep).
  - `test_already_consolidated_data` – Test that already consolidated data is not modified. (Status: Keep).
  - `test_hour_to_time_of_day_mappings` – Test all hour-to-description mappings. (Status: Keep).
  - `test_missing_world_data` – Test handling of missing world_data. (Status: Keep).
  - `test_no_time_data_unchanged` – Test that world_data without any time fields remains unchanged. (Status: Keep).
  - `test_invalid_world_time_format` – Test handling of invalid world_time format. (Status: Keep).
  - `test_edge_case_hours` – Test edge cases for hour values. (Status: Keep).
  - `test_time_of_day_without_world_time` – Test migration of time_of_day when world_time doesn't exist. (Status: Keep).

---

## `tests/test_time_pressure.py`

**Role:** No module docstring; review code to confirm responsibilities.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestTimePressure` – No class docstring present; review implementation to confirm behavior. (Status: Keep).
  - `setUp` – Set up test fixtures (Status: Keep).
  - `tearDown` – Clean up test fixtures (Status: Keep).
  - `test_time_sensitive_events_tracked` – Test that events with deadlines are properly tracked in game state (Status: Keep).
  - `test_npc_agenda_progression` – Test that NPCs have agendas that progress over time (Status: Keep).
  - `test_deadline_consequences` – Test that missing a deadline triggers consequences (Status: Keep).
  - `test_warning_generation` – Test warning generation at different urgency levels (Status: Keep).
  - `test_world_resource_depletion` – Test that world resources deplete at specified rates (Status: Keep).
  - `test_time_advancement` – Test that different actions advance time appropriately (Status: Keep).
  - `test_initial_game_state_has_time_pressure_structures` – Test that new game states are created with time pressure structures (Status: Keep).

---

## `tests/test_token_utils.py`

**Role:** Test suite for token_utils.py Tests token counting and logging utilities for accurate token estimation and consistent logging across the application.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestTokenUtils` – Test suite for token utility functions. (Status: Keep).
  - `test_estimate_tokens_with_string` – Test token estimation with string input. (Status: Keep).
  - `test_estimate_tokens_with_list` – Test token estimation with list input. (Status: Keep).
  - `test_estimate_tokens_with_none` – Test token estimation with None input. (Status: Keep).
  - `test_estimate_tokens_edge_cases` – Test edge cases for token estimation. (Status: Keep).
  - `test_log_with_tokens_default_logger` – Test log_with_tokens with default logger. (Status: Keep).
  - `test_log_with_tokens_custom_logger` – Test log_with_tokens with custom logger. (Status: Keep).
  - `test_log_with_tokens_empty_text` – Test log_with_tokens with empty text. (Status: Keep).
  - `test_log_with_tokens_none_text` – Test log_with_tokens with None text. (Status: Keep).
  - `test_format_token_count` – Test format_token_count function. (Status: Keep).
  - `test_token_estimation_consistency` – Test that token estimation is consistent across functions. (Status: Keep).
  - `test_log_with_tokens_integration` – Integration test for log_with_tokens with various inputs. (Status: Keep).
- `class TestFileCache` – Comprehensive test suite for file_cache.py functionality. (Status: Keep).
  - `setUp` – Set up test environment before each test. (Status: Keep).
  - `tearDown` – Clean up after each test. (Status: Keep).
  - `test_basic_read_file_cached_functionality` – Test basic read_file_cached functionality. (Status: Keep).
  - `test_cache_hit_and_miss_behavior` – Test cache hit and miss statistics tracking. (Status: Keep).
  - `test_thread_safety_concurrent_access` – Test thread safety with concurrent file access. (Status: Keep).
  - `test_ttl_expiration_testing` – Test TTL expiration functionality (mocked for speed). (Status: Keep).
  - `test_cache_statistics_tracking` – Test comprehensive cache statistics tracking. (Status: Keep).
  - `test_error_handling_missing_files` – Test error handling for missing files. (Status: Keep).
  - `test_cache_invalidation_functionality` – Test cache invalidation functionality. (Status: Keep).
  - `test_performance_comparison_vs_direct_reads` – Test performance comparison between cached and direct file reads. (Status: Keep).
  - `test_path_normalization` – Test that different path representations for the same file use the same cache entry. (Status: Keep).
  - `test_encoding_parameter` – Test different file encodings. (Status: Keep).
- `mock_open_read` – Helper function to create mock for file reading. (Status: Keep).

---

## `tests/test_type_safety_foundation.py`

**Role:** Type Safety Foundation Tests Tests the specific changes made in the type safety foundation PR: 1. Fixed syntax error in main.py logging statement 2. Enhanced type safety in TypeScript (tested via HTTP validation)

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestTypeSafetyFoundation` – Tests for type safety foundation changes. (Status: Keep).
  - `test_logging_syntax_fix` – Test that the logging statement syntax fix works correctly. (Status: Keep).
  - `test_data_structure_validation` – Test that data validation patterns work correctly. (Status: Keep).
  - `test_error_handling_patterns` – Test enhanced error handling patterns introduced in the foundation changes. (Status: Keep).
  - `test_null_safety_patterns` – Test null safety patterns that would be enforced by TypeScript improvements. (Status: Keep).
  - `test_foundation_documentation` – Document the foundation changes and their purpose. (Status: Keep).

---

## `tests/test_unknown_entity_filtering.py`

**Role:** Test that 'Unknown' is properly filtered from entity validation

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestUnknownEntityFiltering` – No class docstring present; review implementation to confirm behavior. (Status: Keep).
  - `setUp` – No docstring present; review implementation to confirm behavior. (Status: Keep).
  - `test_unknown_filtered_from_validation` – Test that 'Unknown' entity is filtered out during validation (Status: Keep).
  - `test_dual_pass_filters_unknown` – Test that dual pass generation filters Unknown from expected entities (Status: Keep).
  - `test_empty_expected_entities_after_filtering` – Test behavior when only Unknown is in expected entities (Status: Keep).

---

## `tests/test_unknown_entity_fix_summary.py`

**Role:** Summary test demonstrating the Unknown entity fix

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestUnknownEntityFixSummary` – Summary test showing: 1. The problem: Unknown was treated as a missing entity 2. The fix: Filter Unknown from validation 3. The result: No unnecessary dual-pass generation (Status: Keep).
  - `test_complete_fix_demonstration` – Complete demonstration of the fix (Status: Keep).
  - `test_real_entities_still_validated` – Ensure real entities are still properly validated (Status: Keep).

---

## `tests/test_user_scenario_fix_validation.py`

**Role:** Test to validate the main user scenario fix - no more raw JSON in god mode.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestUserScenarioFixValidation` – Validate that the main user scenario is fixed. (Status: Keep).
  - `test_luke_scenario_scene_116_type_issue` – Test the exact type of malformed JSON that caused Luke's issue. (Status: Keep).
  - `test_various_malformation_scenarios` – Test different types of JSON malformation that could occur. (Status: Keep).
  - `test_normal_god_mode_still_works` – Ensure normal god mode responses still work correctly. (Status: Keep).
  - `test_edge_case_empty_god_mode_response` – Test edge case where god_mode_response exists but is empty. (Status: Keep).

---

## `tests/test_v1_vs_v2_campaign_comparison.py`

**Role:** 🔬 SYSTEMATIC V1 vs V2 CAMPAIGN CREATION COMPARISON TEST This test follows TDD methodology and mandatory QA protocol requirements to systematically compare V1 (Flask) vs V2 (React) campaign creation workflows. 📋 TEST MATRIX COVERAGE: - Campaign Types: Dragon Knight (default), Custom with "Lady Elara", Full Custom - System Versions: V1 (http://localhost:8081) vs V2 (http://localhost:3002) - Testing Phases: RED (failure verification) → GREEN (success verification) - Evidence Collection: Screenshots, API timing, console logs, error states 🚨 MANDATORY QA PROTOCOL COMPLIANCE: ✅ Test Matrix Creation - Document ALL user paths before testing ✅ Evidence Documentation - Screenshots for EACH test matrix cell ✅ Red Team Questions - Adversarial testing to break fixes ✅ Path Coverage Report - Visual showing tested vs untested combinations ✅ Testing Debt Documentation - Related patterns verified after discovery 📁 EVIDENCE STORAGE: All evidence saved to /tmp/v1_vs_v2_test_evidence_{BRANCH}/

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `get_branch_name` – Get current git branch name for temp directory isolation (Status: Keep).
- `class TestMatrix` – 📋 MANDATORY TEST MATRIX - All combinations must be tested Campaign Types × System Versions × Test Scenarios = Coverage Matrix (Status: Keep).
  - `get_test_matrix` – Generate complete test matrix for systematic coverage (Status: Keep).
- `class EvidenceCollector` – 📸 SYSTEMATIC EVIDENCE COLLECTION Handles screenshot capture, API timing, console logs, and error documentation following mandatory QA protocol requirements. (Status: Keep).
  - `setup_evidence_directories` – Create organized directory structure for evidence (Status: Keep).
  - `capture_screenshot` – 📸 MANDATORY SCREENSHOT EVIDENCE Format: "✅ [Claim] [Evidence: screenshot1.png, screenshot2.png]" Path Label Format: "Screenshot: Custom Campaign → Step 1 → Character Field" (Status: Keep).
  - `capture_api_timing` – 📊 API Performance Measurement (Status: Keep).
  - `capture_console_logs` – 📝 Console Log Collection (Status: Keep).
  - `document_error_state` – 🚨 ERROR STATE DOCUMENTATION (Status: Keep).
- `class BrowserTestHelper` – 🌐 BROWSER AUTOMATION HELPER Provides standardized browser operations for both V1 and V2 systems with systematic evidence collection at each step. (Status: Keep).
  - `navigate_with_test_auth` – 🔐 Navigate with authentication bypass (Status: Keep).
  - `create_dragon_knight_campaign` – 🐉 DRAGON KNIGHT DEFAULT CAMPAIGN CREATION (Status: Keep).
  - `create_custom_lady_elara_campaign` – 👩‍⚔️ CUSTOM CAMPAIGN - LADY ELARA CHARACTER (Status: Keep).
  - `create_full_custom_campaign` – ⚙️ FULL CUSTOMIZATION CAMPAIGN (Status: Keep).
  - `test_planning_block_functionality` – 📋 V2 PLANNING BLOCK FUNCTIONALITY TEST (Status: Keep).
  - `measure_api_performance` – 📊 API PERFORMANCE MEASUREMENT (Status: Keep).
- `class V1VsV2CampaignComparisonTest` – 🔬 SYSTEMATIC V1 vs V2 COMPARISON TEST Implements TDD methodology with RED/GREEN phases and mandatory QA protocol. Tests all campaign types across both systems with comprehensive evidence collection. (Status: Keep).
  - `setUpClass` – Initialize test environment and evidence collection (Status: Keep).
  - `setUp` – Initialize browser for each test (Status: Keep).
  - `tearDown` – Clean up browser resources (Status: Keep).
  - `test_red_phase_dragon_knight_comparison` – 🔴 RED PHASE: Dragon Knight Campaign Creation Failure Verification Tests that our comparison methodology can detect real differences between V1 and V2 implementations before fixes are applied. (Status: Keep).
  - `test_green_phase_dragon_knight_comparison` – 🟢 GREEN PHASE: Dragon Knight Campaign Creation Success Verification Tests that both V1 and V2 systems can successfully create Dragon Knight campaigns after any necessary fixes have been applied. (Status: Keep).
  - `test_red_phase_custom_elara_comparison` – 🔴 RED PHASE: Custom Lady Elara Campaign Creation Failure Verification Tests custom character creation and data flow validation. Verifies that "Lady Elara" appears in the final game content. (Status: Keep).
  - `test_green_phase_custom_elara_comparison` – 🟢 GREEN PHASE: Custom Lady Elara Campaign Creation Success Verification Validates end-to-end data flow: Input "Lady Elara" → API → Database → UI Display (Status: Keep).
  - `test_v2_planning_block_functionality` – 📋 V2-SPECIFIC: Planning Block Functionality Verification Tests V2's unique planning block features that don't exist in V1. (Status: Keep).
  - `test_api_performance_comparison` – 📊 API PERFORMANCE COMPARISON Measures and compares API response times between V1 and V2 systems. (Status: Keep).
  - `test_error_handling_comparison` – 🚨 ERROR HANDLING COMPARISON Tests how V1 and V2 systems handle error conditions and edge cases. (Status: Keep).
  - `tearDownClass` – 📊 GENERATE COMPREHENSIVE TEST REPORT Creates systematic evidence report following mandatory QA protocol. (Status: Keep).

---

## `tests/test_v2_dashboard_authenticated_user.py`

**Role:** Test: V2 Dashboard should show campaigns for authenticated users, not welcome page This test verifies the critical issue found in V1 vs V2 comparison: - V2 console logs show 18 campaigns fetched successfully - But V2 UI shows welcome page "Create Your First Campaign" - This should only show for users with 0 campaigns RED-GREEN Test: First confirm this test FAILS, then fix the issue.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `test_dashboard_shows_campaigns_not_welcome_for_authenticated_user` – RED: This test should FAIL initially Dashboard component should show campaigns list when: - User is authenticated - API fetched campaigns array (length > 0) Dashboard should NOT show welcome page when campaigns exist. (Status: Keep).
- `test_dashboard_welcome_page_only_for_no_campaigns` – Test that welcome page ONLY shows when campaigns.length === 0 (Status: Keep).

---

## `tests/test_v2_frontend_red_green.py`

**Role:** RED-GREEN Test: V2 React Frontend Environment Variables and Rendering This test implements red-green methodology to fix the V2 frontend "nothing loads" issue. RED Phase: Tests that should FAIL due to missing environment variables in production build GREEN Phase: Tests that should PASS after environment variables are properly configured

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestV2FrontendRedGreen` – Red-Green tests for V2 React frontend environment configuration. (Status: Keep).
  - `setUp` – Set up test environment. (Status: Keep).
  - `test_red_phase_missing_environment_variables` – RED TEST: This should FAIL because environment variables are not set for production build The React app loads assets but shows blank screen because Firebase can't initialize without proper environment variables. (Status: Keep).
  - `check_build_environment_variables` – Check if the built JavaScript files contain the environment variables. (Status: Keep).
  - `test_red_phase_build_without_env_vars` – RED TEST: Build should fail or produce non-functional app without environment variables TEST GATED: Requires RUN_V2_BUILD_TESTS=1 and ENABLE_BUILD_TESTS=1 environment flags (Status: Keep).
  - `check_build_functionality` – Check if the build is functional by examining the output. (Status: Keep).
  - `test_green_phase_build_with_env_vars` – GREEN TEST: Build should succeed and be functional with proper environment variables TEST GATED: Requires RUN_V2_BUILD_TESTS=1 and ENABLE_BUILD_TESTS=1 environment flags (Status: Keep).
  - `verify_build_contains_env_vars` – Verify that the build contains the required environment variables. (Status: Keep).
  - `test_environment_setup_documentation` – Document what environment setup is required for GREEN tests to pass. (Status: Keep).

---

## `tests/test_v2_frontend_verification.py`

**Role:** V2 Frontend Verification Test This test verifies that the V2 React frontend is properly configured and loading after the red-green fix that rebuilt the app with environment variables. ENHANCED: Added comprehensive security token testing with TDD matrix coverage for the getCompensatedToken clock skew compensation security fix.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestV2FrontendVerification` – Verification tests for V2 React frontend after red-green fix. (Status: Keep).
  - `setUp` – Set up test environment. (Status: Keep).
  - `test_v2_frontend_html_loads` – Test that the V2 frontend HTML loads correctly. (Status: Keep).
  - `test_v2_frontend_assets_load` – Test that V2 frontend assets (JS, CSS) load correctly. (Status: Keep).
  - `test_v2_frontend_has_firebase_config` – Test that the V2 frontend JavaScript contains Firebase configuration. (Status: Keep).
  - `test_v2_api_endpoint_accessible` – Test that the API endpoint is accessible from V2 frontend context. (Status: Keep).
  - `test_build_structure_complete` – Test that the build directory has the expected structure. (Status: Keep).
  - `test_red_green_fix_summary` – Document the red-green fix that resolved the 'nothing loads' issue. (Status: Keep).
- `class TestSecurityTokenMatrix` – TDD Matrix Testing for getCompensatedToken Security Fix Comprehensive test matrix covering all clock skew compensation scenarios following the security fix in api.service.ts line 882. RED PHASE: All tests should FAIL initially since we're testing the logic that should be implemented in the TypeScript frontend. (Status: Keep).
  - `setUp` – Set up mock environment for security token testing. (Status: Keep).
  - `test_matrix_1_clock_skew_no_detection` – Matrix [1,1]: No skew detected → Direct token fetch (Status: Keep).
  - `test_matrix_1_clock_skew_client_behind_2000ms` – Matrix [1,2]: Client behind 2000ms → Wait 2500ms before token (Status: Keep).
  - `test_matrix_1_clock_skew_client_behind_5000ms` – Matrix [1,3]: Client behind 5000ms → Wait 5500ms before token (Status: Keep).
  - `test_matrix_1_clock_skew_client_ahead` – Matrix [1,4]: Client ahead → Direct token fetch (no wait) (Status: Keep).
  - `test_matrix_2_force_refresh_combinations` – Matrix [2,1-6]: Test all force refresh combinations (Status: Keep).
  - `test_matrix_3_token_validation_valid_jwt` – Matrix [3,1]: Valid JWT → Return token (Status: Keep).
  - `test_matrix_3_token_validation_null_token` – Matrix [3,2]: Null token → Throw auth error (Status: Keep).
  - `test_matrix_3_token_validation_empty_token` – Matrix [3,3]: Empty token → Throw auth error (Status: Keep).
  - `test_matrix_3_token_validation_non_string` – Matrix [3,4]: Non-string token → Throw validation error (Status: Keep).
  - `test_matrix_3_token_validation_malformed_jwt` – Matrix [3,5]: Malformed JWT → Throw JWT error (Status: Keep).
  - `test_matrix_3_token_validation_empty_jwt_part` – Matrix [3,6]: Empty JWT part → Throw structure error (Status: Keep).
  - `test_matrix_4_auth_state_authenticated_success` – Matrix [4,1]: Authenticated + No skew → Success with token (Status: Keep).
  - `test_matrix_4_auth_state_not_authenticated` – Matrix [4,4]: Not authenticated → Throw 'User not authenticated' (Status: Keep).

---

## `tests/test_validation_comparison.py`

**Role:** Test Pydantic validation functionality and performance.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestPydanticValidation` – Test Pydantic validation functionality and performance (Status: Keep).
  - `setUp` – Setup test data (Status: Keep).
  - `test_pydantic_validation_performance` – Test Pydantic validation performance (Status: Keep).
  - `test_validation_info` – Test that validation info returns correct Pydantic settings (Status: Keep).
  - `test_entity_creation_with_validation` – Test that entities are created with proper validation (Status: Keep).
  - `test_invalid_data_handling` – Test that Pydantic validation handles invalid data gracefully (Status: Keep).

---

## `tests/test_world_loader.py`

**Role:** Unit tests for world_loader.py path handling logic and file caching integration. Tests both development and production scenarios with comprehensive end-to-end coverage.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestWorldLoader` – Test world_loader.py path handling in different environments. (Status: Keep).
  - `setUp` – Set up test environment. (Status: Keep).
  - `tearDown` – Clean up test environment. (Status: Keep).
  - `test_development_scenario_parent_world` – Test legacy path logic (simplified since new cache tests cover functionality). (Status: Keep).
  - `test_production_scenario_local_world` – Test current world_loader path resolution. (Status: Keep).
  - `test_path_construction_logic` – Test the path construction logic for both scenarios. (Status: Keep).
  - `test_missing_world_files_error_handling` – Test error handling when world files are missing. (Status: Keep).
- `class TestWorldLoaderEnd2EndCache` – End-to-end tests for world_loader.py with file caching integration. (Status: Keep).
  - `setUp` – Set up test environment with real world files and cache. (Status: Keep).
  - `tearDown` – Clean up test environment. (Status: Keep).
  - `test_world_content_loading_with_cache_integration` – Test full world content loading with cache integration - PASSING TEST. (Status: Keep).
  - `test_banned_names_loading_and_caching_behavior` – Test banned names loading and caching behavior - PASSING TEST. (Status: Keep).
  - `test_cache_hit_miss_scenarios_for_system_instructions` – Test cache hit/miss scenarios for world content system instructions - PASSING TEST. (Status: Keep).
  - `test_performance_improvement_verification` – Test cache functionality verification - focuses on behavior not timing. (Status: Keep).
  - `test_cache_statistics_tracking_during_world_loading` – Test cache statistics tracking during world loading - PASSING TEST. (Status: Keep).
  - `test_error_handling_with_missing_world_files` – Test error handling with missing world files - PASSING TEST. (Status: Keep).
  - `test_integration_with_existing_world_loader_scenarios` – Test integration with existing world_loader scenarios - PASSING TEST. (Status: Keep).
  - `test_memory_efficiency_validation` – Test memory efficiency validation - PASSING TEST. (Status: Keep).

---

## `tests/test_world_loader_e2e.py`

**Role:** End-to-end tests for world_loader.py with file caching. Tests the integration of world_loader with the file_cache system.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestWorldLoaderE2E` – End-to-end tests for world_loader with caching. (Status: Keep).
  - `setUp` – Set up test fixtures before each test method. (Status: Keep).
  - `tearDown` – Clean up after each test method. (Status: Keep).
  - `test_world_content_loading_uses_cache` – Test that load_world_content uses the file cache. (Status: Keep).
  - `test_banned_names_loading_uses_cache` – Test that load_banned_names uses the file cache. (Status: Keep).
  - `test_world_loader_performance_with_cache` – Test that repeated world loader calls show performance improvement. (Status: Keep).
  - `test_world_loader_cache_persistence_across_calls` – Test that cache persists across multiple function calls. (Status: Keep).
  - `test_world_loader_handles_missing_files_gracefully` – Test that world_loader handles missing files without breaking cache. (Status: Keep).
  - `test_world_content_format_and_structure` – Test that world content maintains expected format through caching. (Status: Keep).
- `class TestWorldLoaderCacheIntegration` – Integration tests for world_loader cache behavior. (Status: Keep).
  - `setUp` – Set up integration test fixtures. (Status: Keep).
  - `tearDown` – Clean up integration test fixtures. (Status: Keep).
  - `test_mixed_world_loader_calls_cache_efficiency` – Test cache efficiency with mixed world_loader function calls. (Status: Keep).

---

## `tests/test_world_logic.py`

**Role:** Test file to verify world_logic.py structure and basic functionality. This test doesn't require external dependencies.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestUnifiedAPIStructure` – Test the structure and basic logic of world_logic.py (Status: Keep).
  - `setUp` – Set up test environment and mock all external dependencies (Status: Keep).
  - `tearDown` – Clean up mocks (Status: Keep).
  - `test_import_world_logic` – Test that world_logic can be imported with mocked dependencies (Status: Keep).
  - `test_build_campaign_prompt` – Test the campaign prompt building logic (Status: Keep).
  - `test_cleanup_legacy_state` – Test legacy state cleanup logic (Status: Keep).
  - `test_error_response_format` – Test standardized error response format (Status: Keep).
  - `test_success_response_format` – Test standardized success response format (Status: Keep).
  - `test_create_campaign_unified_validation_sync` – Test campaign creation validation (sync version) (Status: Keep).
  - `test_process_action_unified_validation_sync` – Test action processing validation (sync version) (Status: Keep).
- `class TestMCPMigrationRedGreen` – Red-Green TDD tests for critical MCP migration bug fixes. (Status: Keep).
  - `setUp` – Set up test fixtures. (Status: Keep).
  - `test_sequence_id_calculation_bug_red_phase` – 🔴 RED PHASE: Test that would FAIL before sequence_id fix This test verifies that AI responses get the correct sequence_id calculation: - User input should get: len(story_context) + 1 = 5 - AI response should get: len(story_context) + 2 = 6 Before the fix, both would get len(story_context) + 1 = 5 (WRONG!) (Status: Keep).
  - `test_user_scene_number_field_red_phase` – 🔴 RED PHASE: Test that would FAIL before user_scene_number field addition This test verifies that the user_scene_number field is present in API responses. Before the fix, this field was missing and would break frontend compatibility. (Status: Keep).
  - `test_enhanced_logging_json_serialization_red_phase` – 🔴 RED PHASE: Test that would FAIL before enhanced logging fix This test verifies that the enhanced logging with JSON serialization works correctly with complex objects that have custom serializers. (Status: Keep).
- `class TestJSONEscapeConversion` – Test JSON escape sequence conversion functionality. (Status: Keep).
  - `test_convert_json_escape_sequences_basic` – Test core conversion function with various escape sequences. (Status: Keep).
  - `test_unicode_escape_sequences_and_idempotence` – Ensure \uXXXX and surrogate pairs are handled and conversion is idempotent. (Status: Keep).
  - `test_dragon_knight_description_conversion` – Test conversion of the actual Dragon Knight description that caused the original issue. (Status: Keep).
- `class TestConvertAndFormatField` – Test the helper function that eliminates code duplication. (Status: Keep).
  - `test_convert_and_format_field_basic` – Test helper function with various inputs. (Status: Keep).
- `class TestBuildCampaignPromptConversion` – Test campaign prompt building with conversion integration. (Status: Keep).
  - `test_build_campaign_prompt_converts_all_fields` – Test that all fields get conversion applied. (Status: Keep).
  - `test_build_campaign_prompt_dragon_knight_case` – Test the exact Dragon Knight case that prompted the original fix. (Status: Keep).
  - `test_build_campaign_prompt_old_prompt_priority` – Test that old_prompt takes priority and bypasses conversion. (Status: Keep).
  - `test_build_campaign_prompt_empty_fields` – Test behavior with empty or whitespace-only fields. (Status: Keep).
  - `test_build_campaign_prompt_all_empty_triggers_random` – Test that all empty fields triggers random generation. (Status: Keep).
- `class TestMarkdownStructurePreservation` – Test that conversion preserves markdown formatting. (Status: Keep).
  - `test_markdown_structure_preservation` – Test that conversion preserves markdown formatting. (Status: Keep).
- `class TestCodeHealthChecks` – Test for code health issues like unused constants and dead code. (Status: Keep).
  - `test_no_unused_random_constants_in_world_logic` – Test that RANDOM_CHARACTERS and RANDOM_SETTINGS are not duplicated/unused in world_logic.py (Status: Keep).

---

## `tests/wizard/test_campaign_wizard_reset_reproduction.py`

**Role:** Campaign Wizard Reset Issue Reproduction Test This test reproduces the exact user workflow that leads to the persistent spinner issue: 1. Create first campaign 2. Navigate back to dashboard 3. Click "Start Campaign" again 4. Verify wizard appears clean (not spinner)

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class CampaignWizardResetReproductionTest` – Automated reproduction of the campaign wizard reset issue PERFORMANCE GATED: Requires ENABLE_BROWSER_TESTS=1 (expensive 30+ second test) (Status: Keep).
  - `setUpClass` – No docstring present; review implementation to confirm behavior. (Status: Keep).
  - `start_test_server` – Start local server serving the application (Status: Keep).
  - `setup_browser` – Set up Chrome browser for testing (Status: Keep).
  - `tearDownClass` – No docstring present; review implementation to confirm behavior. (Status: Keep).
  - `setUp` – No docstring present; review implementation to confirm behavior. (Status: Keep).
  - `test_campaign_wizard_reset_issue_reproduction` – Reproduce the complete user workflow that leads to persistent spinner (Status: Keep).

---
