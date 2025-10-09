# Python Modules: testing_framework

> Auto-generated overview of module docstrings and public APIs. Enhance descriptions as needed.
> Updated: 2025-10-08
> NOTE: Methods `analyze_entity_presence`, `extract_physical_states`, and `detect_scene_transitions` originated in `NarrativeSyncValidator`; `create_injection_templates` came from `DualPassGenerator` when the framework was consolidated.

## `testing_framework/__init__.py`

**Role:** Testing framework for service provider abstraction. Enables seamless switching between mock and real services for testing.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:** None exported (primarily internal helpers).

---

## `testing_framework/capture.py`

**Role:** Data capture framework for real service interactions. Records API calls and responses for mock validation and analysis.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class CaptureManager` – Manages capture of service interactions for mock validation. (Status: Keep).
  - `capture_interaction` – Context manager for capturing service interactions. (Status: Keep).
  - `record_response` – Record response data for a specific interaction. (Status: Keep).
  - `save_captures` – Save captured interactions to file. (Status: Keep).
  - `get_summary` – Get summary statistics of captured interactions. (Status: Keep).
- `class CaptureFirestoreClient` – Wrapper for Firestore client that captures interactions. (Status: Keep).
  - `collection` – Get collection reference with capture. (Status: Keep).
  - `document` – Get document reference with capture. (Status: Keep).
- `class CaptureCollectionReference` – Wrapper for Firestore collection reference with capture. (Status: Keep).
  - `add` – Add document with capture. (Status: Keep).
  - `document` – Get document reference. (Status: Keep).
  - `stream` – Stream documents with capture. (Status: Keep).
  - `get` – Get all documents with capture. (Status: Keep).
- `class CaptureDocumentReference` – Wrapper for Firestore document reference with capture. (Status: Keep).
  - `set` – Set document with capture. (Status: Keep).
  - `get` – Get document with capture. (Status: Keep).
  - `update` – Update document with capture. (Status: Keep).
  - `delete` – Delete document with capture. (Status: Keep).
- `class CaptureGeminiClient` – Wrapper for Gemini client that captures interactions. (Status: Keep).
  - `generate_content` – Generate content with capture. (Status: Keep).
- `load_capture_data` – Load captured interaction data from file. (Status: Keep).
- `cleanup_old_captures` – Clean up capture files older than specified days. (Status: Keep).

---

## `testing_framework/capture_analysis.py`

**Role:** Analysis tools for captured data and mock validation. Compares captured real service interactions with mock responses.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class CaptureAnalyzer` – Analyzes captured service interactions and compares with mock data. (Status: Keep).
  - `analyze_captures` – Analyze all captures from the last N days. (Status: Keep).
  - `compare_with_mock` – Compare captured real responses with mock responses. (Status: Keep).
  - `generate_report` – Generate a human-readable analysis report. (Status: Keep).
- `create_mock_baseline` – Create a mock response baseline from captured real data. (Status: Keep).

---

## `testing_framework/capture_cli.py`

**Role:** Command-line interface for capture analysis and mock validation.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `analyze_command` – Analyze captured data. (Status: Keep).
- `compare_command` – Compare captured data with mock responses. (Status: Keep).
- `baseline_command` – Create mock baseline from captured data. (Status: Keep).
- `cleanup_command` – Clean up old capture files. (Status: Keep).
- `list_command` – List available capture files. (Status: Keep).
- `main` – Main CLI entry point. (Status: Keep).

---

## `testing_framework/config.py`

**Role:** Configuration management for real service testing. Handles environment variables and validation for test isolation.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestConfig` – Configuration for real service testing. (Status: Keep).
  - `get_real_service_config` – Get configuration for real services. (Status: Keep).
  - `validate_real_service_config` – Validate that required configuration is present. (Status: Keep).
  - `get_test_collection_name` – Get test-specific collection name with prefix. (Status: Keep).

---

## `testing_framework/examples/capture_example.py`

**Role:** Example demonstrating the capture framework for real service interactions. Shows how to use capture mode to record API calls and analyze the data.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `demo_capture_mode` – Demonstrate capture mode functionality. (Status: Keep).
- `demo_mock_capture` – Demonstrate capture analysis with mock data. (Status: Keep).
- `demo_cli_tools` – Demonstrate the CLI analysis tools. (Status: Keep).
- `main` – Main demo function. (Status: Keep).

---

## `testing_framework/factory.py`

**Role:** Service provider factory for creating appropriate providers based on configuration. Manages global provider state for tests.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `get_service_provider` – Create appropriate service provider based on TEST_MODE. (Status: Keep).
- `set_service_provider` – Set the global service provider for tests. (Status: Keep).
- `get_current_provider` – Get the current service provider, creating default if needed. (Status: Keep).
- `reset_global_provider` – Reset the global provider (useful for test cleanup). (Status: Keep).

---

## `testing_framework/fixtures.py`

**Role:** Test fixtures for pytest and unittest integration with the Real-Mode Testing Framework. Provides seamless switching between mock and real services based on TEST_MODE.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `service_provider` – Provide appropriate service provider based on TEST_MODE. Usage in pytest: def test_something(service_provider): firestore = service_provider.get_firestore() # Test logic works with mock or real services (Status: Keep).
- `firestore_client` – Provide Firestore client (mock or real) based on TEST_MODE. (Status: Keep).
- `gemini_client` – Provide Gemini client (mock or real) based on TEST_MODE. (Status: Keep).
- `auth_service` – Provide auth service (mock or real) based on TEST_MODE. (Status: Keep).
- `test_mode` – Get current test mode from environment. (Status: Keep).
- `is_real_service` – Check if using real services. (Status: Keep).
- `class BaseTestCase` – Base test case with service provider integration. Usage: class TestMyFeature(BaseTestCase): def test_something(self): result = self.firestore.get_document('test/doc') # Works with mock or real services (Status: Keep).
  - `setUp` – Set up test with appropriate service provider. (Status: Keep).
  - `tearDown` – Clean up after test. (Status: Keep).
- `class IsolatedTestCase` – Test case with isolated test environment. Each test gets a fresh service provider to ensure complete isolation. Use when tests might interfere with each other. (Status: Keep).
  - `setUp` – Set up with fresh provider and reset global state. (Status: Keep).
  - `tearDown` – Clean up and reset global state. (Status: Keep).
- `setup_test_services` – Manually set up test services for non-fixture usage. Args: test_mode: Override TEST_MODE environment variable Returns: Service provider instance Usage: provider = setup_test_services('mock') try: firestore = provider.get_firestore() # Use services finally: provider.cleanup() (Status: Keep).
- `cleanup_test_services` – Manually clean up test services. (Status: Keep).
- `get_test_client_for_mode` – Get appropriate test client based on mode. Helper for gradually migrating existing tests. (Status: Keep).
- `class MockCompatibilityMixin` – Mixin to help existing tests work with new framework. Provides mock-like attributes that delegate to service provider. (Status: Keep).
  - `mock_firestore` – Compatibility property for tests expecting mock_firestore. (Status: Keep).
  - `mock_gemini` – Compatibility property for tests expecting mock_gemini. (Status: Keep).
  - `mock_auth` – Compatibility property for tests expecting mock_auth. (Status: Keep).

---

## `testing_framework/integration_utils.py`

**Role:** Integration utilities for updating existing tests to support the Real-Mode Testing Framework. Provides helpers for gradual migration and backwards compatibility.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `dual_mode_test` – Decorator to make existing test functions work in dual mode. Usage: @dual_mode_test def test_something(self): # Existing test code works unchanged (Status: Keep).
- `skip_in_real_mode` – Decorator to skip tests in real mode. Usage: @skip_in_real_mode("Uses hardcoded test data") def test_something(self): # This test only runs in mock mode (Status: Keep).
- `real_mode_only` – Decorator for tests that only work with real services. Usage: @real_mode_only("Tests actual API integration") def test_something(self): # This test only runs in real mode (Status: Keep).
- `class DualModeTestMixin` – Mixin to add dual-mode support to existing test classes. Usage: class MyExistingTest(DualModeTestMixin, unittest.TestCase): # Existing test methods work unchanged (Status: Keep).
  - `setUp` – Setup dual-mode support. (Status: Keep).
  - `tearDown` – Cleanup dual-mode resources. (Status: Keep).
- `class MockCompatibilityMixin` – Mixin for tests that expect specific mock attributes. Provides backward compatibility for tests that reference mock objects directly. (Status: Keep).
  - `setUp` – Setup mock compatibility layer. (Status: Keep).
- `class SmartPatcher` – Context manager that patches services only when needed (mock mode). (Status: Keep).
- `smart_patch` – Smart patching that only applies in mock mode. Usage: with smart_patch(gemini_service=None, firestore_service=None): # Code works in both mock and real mode # In mock mode: services are patched with framework mocks # In real mode: no patching, uses real services (Status: Keep).
- `convert_test_class` – Convert existing test class to dual-mode. Args: test_class: The test class to convert add_mixins: Whether to add dual-mode mixins Returns: Modified test class (Status: Keep).
- `update_test_imports` – Update test module to import testing framework. Call this at the top of existing test files: update_test_imports(__name__) Args: _test_module: The module name (typically __name__) (Status: Keep).
- `class TestResourceManager` – Manages test resources and prevents resource leaks in real mode. (Status: Keep).
  - `create_test_collection` – Create a test-specific collection name. (Status: Keep).
  - `cleanup` – Clean up created resources. (Status: Keep).
- `validate_test_environment` – Validate that the test environment is properly configured. (Status: Keep).
- `get_test_mode_info` – Get information about current test mode. (Status: Keep).

---

## `testing_framework/migration_examples.py`

**Role:** Migration examples showing how to update existing tests to support dual modes. Demonstrates before/after patterns for common test scenarios.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TraditionalCharacterTestBefore` – Example of old-style test that only works with mocks. (Status: Keep).
  - `setup_method` – Setup test client (Status: Keep).
  - `test_api_accepts_character_setting_params_old_way` – Test that /api/campaigns accepts character and setting parameters - OLD WAY (Status: Keep).
- `class ModernCharacterTestAfter` – Example of modernized test that works with both mock and real services. (Status: Keep).
  - `setUp` – Setup test client and services (Status: Keep).
  - `test_api_accepts_character_setting_params_new_way` – Test that /api/campaigns accepts character and setting parameters - NEW WAY (Status: Keep).
- `test_character_creation_pytest_old` – BEFORE: Pytest test with manual mocking. (Status: Keep).
- `test_character_creation_pytest_new` – AFTER: Pytest test with service provider fixture. (Status: Keep).
- `class GradualMigrationExample` – Shows how to gradually migrate existing tests. (Status: Keep).
  - `setup_method` – Original setup method - unchanged. (Status: Keep).
  - `test_legacy_with_compatibility_helper` – Existing test with minimal changes using compatibility helper. (Status: Keep).
- `class BackwardsCompatibleTest` – Shows how to make existing tests work with minimal changes. (Status: Keep).
  - `setup_method` – Setup with backwards compatibility. (Status: Keep).
  - `teardown_method` – Cleanup resources. (Status: Keep).
  - `test_existing_code_unchanged` – Existing test code works without modification. (Status: Keep).
- `class RealModeSafetyExample` – Examples of safety patterns for real mode tests. (Status: Keep).
  - `test_with_resource_limits` – Test that respects resource limits in real mode. (Status: Keep).
  - `test_with_isolation` – Test with proper isolation for real services. (Status: Keep).

---

## `testing_framework/mock_provider.py`

**Role:** Mock service provider implementation. Uses existing mock services for testing without external dependencies.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class MockServiceProvider` – Provider that uses existing mock services. (Status: Keep).
  - `get_firestore` – Return mock Firestore client. (Status: Keep).
  - `get_gemini` – Return mock Gemini client. (Status: Keep).
  - `get_auth` – Return mock auth service. (Status: Keep).
  - `cleanup` – Clean up mock services (reset to initial state). (Status: Keep).
  - `is_real_service` – Return False since using mock services. (Status: Keep).

---

## `testing_framework/pytest_integration.py`

**Role:** Pytest integration for the Real-Mode Testing Framework. Provides pytest-specific fixtures, markers, and utilities.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `test_mode` – Get current test mode from environment. (Status: Keep).
- `service_provider` – Provide appropriate service provider based on TEST_MODE. This is the main fixture that most tests should use. (Status: Keep).
- `isolated_service_provider` – Provide isolated service provider with fresh state. Use when test isolation is critical. (Status: Keep).
- `firestore_client` – Provide Firestore client (mock or real) based on TEST_MODE. (Status: Keep).
- `gemini_client` – Provide Gemini client (mock or real) based on TEST_MODE. (Status: Keep).
- `auth_service` – Provide auth service (mock or real) based on TEST_MODE. (Status: Keep).
- `is_real_service` – Check if using real services. (Status: Keep).
- `test_services` – Provide all services as a dictionary for convenience. (Status: Keep).
- `pytest_configure` – Configure pytest with custom markers. (Status: Keep).
- `pytest_runtest_setup` – Setup hook to skip tests based on mode and markers. (Status: Keep).
- `all_modes_service_provider` – Parametrized fixture that runs tests in both mock and real modes. Usage: def test_works_in_both_modes(all_modes_service_provider): firestore = all_modes_service_provider.get_firestore() # Test runs twice: once with mock, once with real (Status: Keep).
- `skip_if_real_mode` – Pytest marker function to skip tests in real mode. (Status: Keep).
- `skip_if_mock_mode` – Pytest marker function to skip tests in mock mode. (Status: Keep).
- `requires_real_services` – Decorator that marks test as requiring real services. (Status: Keep).
- `mock_only` – Decorator that marks test as mock-only. (Status: Keep).
- `expensive_test` – Decorator that marks test as expensive (for real mode filtering). (Status: Keep).
- `test_mode_info` – Auto-use fixture that prints test mode information. (Status: Keep).
- `validate_test_environment` – Validate test environment at session start. (Status: Keep).
- `configure_pytest_ini` – Generate pytest.ini configuration for the framework. Call this to create a pytest.ini file with appropriate settings. (Status: Keep).
- `example_test_functions` – Example test functions showing different patterns. (Status: Keep).

---

## `testing_framework/real_provider.py`

**Role:** Real service provider implementation. Uses actual services with test isolation and cleanup.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class RealServiceProvider` – Provider that uses real services with test isolation. (Status: Keep).
  - `get_firestore` – Return real Firestore client with test isolation. (Status: Keep).
  - `get_gemini` – Return real Gemini client. (Status: Keep).
  - `get_auth` – Return test auth service. (Status: Keep).
  - `cleanup` – Delete test data created during test run. (Status: Keep).
  - `track_test_collection` – Track a collection for cleanup after testing. (Status: Keep).
  - `is_real_service` – Return True since using real services. (Status: Keep).
  - `get_capture_summary` – Get summary of captured interactions. (Status: Keep).
  - `save_capture_data` – Manually save capture data to file. (Status: Keep).

---

## `testing_framework/service_provider.py`

**Role:** Abstract base class for test service providers. Defines the interface for switching between mock and real services.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestServiceProvider` – Abstract base class for test service providers. (Status: Keep).
  - `get_firestore` – Return Firestore client (mock or real). (Status: Keep).
  - `get_gemini` – Return Gemini client (mock or real). (Status: Keep).
  - `get_auth` – Return auth service (mock or real). (Status: Keep).
  - `cleanup` – Clean up resources after test execution. (Status: Keep).
  - `is_real_service` – Return True if using real services. (Status: Keep).

---

## `testing_framework/simple_mock_provider.py`

**Role:** Simplified mock service provider implementation. Avoids dependency issues while providing the same interface.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class SimpleMockDocument` – Mock Firestore document. (Status: Keep).
  - `set` – No docstring present; review implementation to confirm behavior. (Status: Keep).
  - `get` – No docstring present; review implementation to confirm behavior. (Status: Keep).
  - `to_dict` – No docstring present; review implementation to confirm behavior. (Status: Keep).
  - `reference` – No docstring present; review implementation to confirm behavior. (Status: Keep).
- `class SimpleMockCollection` – Mock Firestore collection. (Status: Keep).
  - `document` – No docstring present; review implementation to confirm behavior. (Status: Keep).
  - `stream` – No docstring present; review implementation to confirm behavior. (Status: Keep).
- `class SimpleMockFirestore` – Simplified mock Firestore for testing the framework. (Status: Keep).
  - `reset` – No docstring present; review implementation to confirm behavior. (Status: Keep).
  - `collection` – No docstring present; review implementation to confirm behavior. (Status: Keep).
  - `get_campaigns_for_user` – No docstring present; review implementation to confirm behavior. (Status: Keep).
- `class SimpleMockGemini` – Simplified mock Gemini for testing the framework. (Status: Keep).
  - `generate_content` – No docstring present; review implementation to confirm behavior. (Status: Keep).
  - `reset` – No docstring present; review implementation to confirm behavior. (Status: Keep).
- `class SimpleMockAuth` – Simplified mock auth service. (Status: Keep).
  - `verify_id_token` – No docstring present; review implementation to confirm behavior. (Status: Keep).
  - `reset` – No docstring present; review implementation to confirm behavior. (Status: Keep).
- `class SimpleMockServiceProvider` – Simplified provider that uses basic mocks without complex dependencies. (Status: Keep).
  - `get_firestore` – Return simplified mock Firestore client. (Status: Keep).
  - `get_gemini` – Return simplified mock Gemini client. (Status: Keep).
  - `get_auth` – Return mock auth service. (Status: Keep).
  - `cleanup` – Clean up mock services (reset to initial state). (Status: Keep).
  - `is_real_service` – Return False since using mock services. (Status: Keep).

---

## `testing_framework/test_basic_validation.py`

**Role:** Basic validation test for the Real-Mode Testing Framework integration. Tests core functionality without external dependencies.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestBasicFramework` – Test basic framework functionality. (Status: Keep).
  - `setUp` – Setup for each test. (Status: Keep).
  - `test_service_provider_creation` – Test that service providers can be created. (Status: Keep).
  - `test_mode_switching` – Test switching between mock and real modes. (Status: Keep).
  - `test_global_provider_management` – Test global provider management. (Status: Keep).
- `class TestBackwardCompatibility` – Test backward compatibility features. (Status: Keep).
  - `setUp` – Setup for each test. (Status: Keep).
  - `test_get_test_client_helper` – Test the backward compatibility helper. (Status: Keep).
  - `test_integration_utils_import` – Test that integration utilities can be imported. (Status: Keep).
- `class TestServiceOperations` – Test basic service operations. (Status: Keep).
  - `setUp` – Setup for each test. (Status: Keep).
  - `tearDown` – Cleanup after each test. (Status: Keep).
  - `test_firestore_mock_operations` – Test that mock Firestore operations work. (Status: Keep).
  - `test_gemini_mock_operations` – Test that mock Gemini operations work. (Status: Keep).
  - `test_auth_mock_operations` – Test that mock auth operations work. (Status: Keep).
- `run_validation` – Run all validation tests. (Status: Keep).

---

## `testing_framework/test_framework_validation.py`

**Role:** Framework validation script to demonstrate all components working together. Run this to verify the TestServiceProvider framework is functioning correctly.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `validate_component` – Run a test component and return results. (Status: Keep).
- `validate_mock_provider` – Test MockServiceProvider functionality. (Status: Keep).
- `validate_real_provider_validation` – Test RealServiceProvider configuration validation. (Status: Keep).
- `validate_factory_switching` – Test service provider factory mode switching. (Status: Keep).
- `validate_global_provider_management` – Test global provider state management. (Status: Keep).
- `validate_configuration` – Test configuration management. (Status: Keep).
- `validate_interface_compliance` – Test that all providers implement the same interface. (Status: Keep).
- `main` – Run all validation tests and report results. (Status: Keep).

---

## `testing_framework/test_integration_validation.py`

**Role:** Validation tests for the Real-Mode Testing Framework integration. Ensures that the integration works correctly and existing tests remain compatible.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestFrameworkIntegration` – Test that the framework integration works correctly. (Status: Keep).
  - `test_service_provider_access` – Test that services are accessible through the framework. (Status: Keep).
  - `test_firestore_operations` – Test basic Firestore operations work in both modes. (Status: Keep).
  - `test_gemini_operations` – Test basic Gemini operations work in both modes. (Status: Keep).
- `class TestBackwardsCompatibility` – Test that existing test patterns still work with the framework. (Status: Keep).
  - `setUp` – Setup test environment. (Status: Keep).
  - `test_mock_compatibility_attributes` – Test that mock compatibility attributes work. (Status: Keep).
  - `test_decorator_compatibility` – Test that dual_mode_test decorator works. (Status: Keep).
  - `test_smart_patch_usage` – Test that smart_patch works correctly. (Status: Keep).
- `class TestGradualMigration` – Test gradual migration patterns for existing tests. (Status: Keep).
  - `setUp` – Setup with gradual migration pattern. (Status: Keep).
  - `tearDown` – Cleanup resources. (Status: Keep).
  - `test_gradual_adoption` – Test that tests can adopt framework features gradually. (Status: Keep).
- `class TestResourceManagement` – Test that resource management works correctly. (Status: Keep).
  - `test_cleanup_called` – Test that cleanup is called automatically. (Status: Keep).
  - `test_isolation_between_tests` – Test that tests are properly isolated. (Status: Keep).
- `class TestModeSkipping` – Test that mode-specific skipping works. (Status: Keep).
  - `test_mock_only_test` – This test should only run in mock mode. (Status: Keep).
  - `test_real_only_test` – This test should only run in real mode. (Status: Keep).
- `class TestFrameworkValidation` – Test framework validation functions. (Status: Keep).
  - `test_environment_validation` – Test that validate_test_environment works. (Status: Keep).
  - `test_mode_detection` – Test that test mode is detected correctly. (Status: Keep).

---

## `testing_framework/tests/__init__.py`

**Role:** Unit tests for testing framework components.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:** None exported (primarily internal helpers).

---

## `testing_framework/tests/test_capture.py`

**Role:** Tests for the capture framework.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestCaptureManager` – Test the CaptureManager class. (Status: Keep).
  - `setUp` – Set up test environment. (Status: Keep).
  - `tearDown` – Clean up test environment. (Status: Keep).
  - `test_initialization` – Test capture manager initialization. (Status: Keep).
  - `test_capture_interaction_success` – Test successful interaction capture. (Status: Keep).
  - `test_capture_interaction_error` – Test error handling in interaction capture. (Status: Keep).
  - `test_save_captures` – Test saving captures to file. (Status: Keep).
  - `test_sanitize_data` – Test data sanitization for sensitive fields. (Status: Keep).
  - `test_get_summary` – Test getting summary statistics. (Status: Keep).
- `class TestCaptureFirestoreClient` – Test the Firestore capture wrapper. (Status: Keep).
  - `setUp` – Set up test environment. (Status: Keep).
  - `tearDown` – Clean up test environment. (Status: Keep).
  - `test_collection_add` – Test collection add with capture. (Status: Keep).
  - `test_document_get` – Test document get with capture. (Status: Keep).
- `class TestCaptureGeminiClient` – Test the Gemini capture wrapper. (Status: Keep).
  - `setUp` – Set up test environment. (Status: Keep).
  - `tearDown` – Clean up test environment. (Status: Keep).
  - `test_generate_content` – Test content generation with capture. (Status: Keep).
- `class TestCaptureAnalyzer` – Test the capture analysis tools. (Status: Keep).
  - `setUp` – Set up test environment. (Status: Keep).
  - `tearDown` – Clean up test environment. (Status: Keep).
  - `test_analyze_interactions` – Test interaction analysis. (Status: Keep).
  - `test_compare_with_mock` – Test comparison with mock responses. (Status: Keep).
  - `test_generate_report` – Test report generation. (Status: Keep).
- `class TestUtilityFunctions` – Test utility functions. (Status: Keep).
  - `setUp` – Set up test environment. (Status: Keep).
  - `tearDown` – Clean up test environment. (Status: Keep).
  - `test_cleanup_old_captures` – Test cleanup of old capture files. (Status: Keep).
  - `test_create_mock_baseline` – Test creating mock baseline from capture data. (Status: Keep).

---

## `testing_framework/tests/test_factory.py`

**Role:** Unit tests for service provider factory.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestFactory` – Test service provider factory functions. (Status: Keep).
  - `setUp` – Set up test fixtures. (Status: Keep).
  - `tearDown` – Clean up test fixtures. (Status: Keep).
  - `test_get_service_provider_default_mock` – Test that get_service_provider returns MockServiceProvider by default. (Status: Keep).
  - `test_get_service_provider_explicit_mock` – Test that get_service_provider returns MockServiceProvider for 'mock' mode. (Status: Keep).
  - `test_get_service_provider_real_mode` – Test that get_service_provider returns RealServiceProvider for 'real' mode. (Status: Keep).
  - `test_get_service_provider_capture_mode` – Test that get_service_provider returns RealServiceProvider with capture mode. (Status: Keep).
  - `test_get_service_provider_invalid_mode` – Test that get_service_provider raises ValueError for invalid mode. (Status: Keep).
  - `test_get_service_provider_from_env` – Test that get_service_provider reads from TEST_MODE environment variable. (Status: Keep).
  - `test_set_and_get_current_provider` – Test setting and getting the current provider. (Status: Keep).
  - `test_get_current_provider_creates_default` – Test that get_current_provider creates default if none set. (Status: Keep).
  - `test_get_current_provider_consistent` – Test that get_current_provider returns same instance on multiple calls. (Status: Keep).
  - `test_reset_global_provider` – Test that reset_global_provider clears the global state. (Status: Keep).

---

## `testing_framework/tests/test_integration_example.py`

**Role:** Integration example showing how existing tests can use the framework. This demonstrates backwards compatibility and easy migration.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestIntegrationExample` – Example showing how tests can use the service provider framework. (Status: Keep).
  - `setUp` – Set up test fixtures - use mock mode for safety. (Status: Keep).
  - `tearDown` – Clean up after tests. (Status: Keep).
  - `test_existing_test_pattern` – Test that simulates how existing tests would be updated. (Status: Keep).
  - `test_seamless_mode_switching` – Test that mode switching works without changing test code. (Status: Keep).

---

## `testing_framework/tests/test_mock_provider.py`

**Role:** Unit tests for MockServiceProvider.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestMockProvider` – Test MockServiceProvider implementation. (Status: Keep).
  - `setUp` – Set up test fixtures. (Status: Keep).
  - `test_implements_interface` – Test that MockServiceProvider implements TestServiceProvider interface. (Status: Keep).
  - `test_get_firestore_returns_mock` – Test that get_firestore returns MockFirestoreClient. (Status: Keep).
  - `test_get_gemini_returns_mock` – Test that get_gemini returns MockGeminiClient. (Status: Keep).
  - `test_get_auth_returns_mock` – Test that get_auth returns mock auth (currently None). (Status: Keep).
  - `test_is_real_service_false` – Test that is_real_service returns False for mock provider. (Status: Keep).
  - `test_cleanup_resets_services` – Test that cleanup resets mock services. (Status: Keep).
  - `test_consistent_instances` – Test that multiple calls return the same instances. (Status: Keep).

---

## `testing_framework/tests/test_real_provider.py`

**Role:** Unit tests for RealServiceProvider.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestRealProvider` – Test RealServiceProvider implementation. (Status: Keep).
  - `setUp` – Set up test fixtures. (Status: Keep).
  - `tearDown` – Clean up test fixtures. (Status: Keep).
  - `test_implements_interface` – Test that RealServiceProvider implements TestServiceProvider interface. (Status: Keep).
  - `test_is_real_service_true` – Test that is_real_service returns True for real provider. (Status: Keep).
  - `test_capture_mode_initialization` – Test that capture mode is properly initialized. (Status: Keep).
  - `test_get_firestore_creates_client` – Test that get_firestore attempts to create real Firestore client. (Status: Keep).
  - `test_get_gemini_creates_client` – Test that get_gemini attempts to create real Gemini client. (Status: Keep).
  - `test_get_auth_creates_test_auth` – Test that get_auth creates test auth object. (Status: Keep).
  - `test_track_test_collection` – Test that track_test_collection adds to cleanup list. (Status: Keep).
  - `test_cleanup_calls_collection_cleanup` – Test that cleanup processes tracked collections. (Status: Keep).
  - `test_missing_api_key_raises_error` – Test that missing API key raises ValueError. (Status: Keep).

---

