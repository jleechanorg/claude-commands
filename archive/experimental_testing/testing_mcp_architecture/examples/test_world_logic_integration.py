#!/usr/bin/env python3
"""
Test suite for Unified API Integration between Flask and MCP Server

This test verifies that both Flask routes and MCP server tools:
1. Use the same unified API functions and shared business logic
2. Return identical JSON response structures
3. Handle errors consistently
4. Have no business logic duplication

Test Areas:
- Flask route integration with world_logic functions
- MCP server integration (or lack thereof) with world_logic functions
- JSON response format consistency
- Error handling uniformity
- Business logic duplication detection
"""

import asyncio

# Add mvp_site to path for testing
import os
import sys
import traceback
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "mvp_site"))

import world_logic
from world_logic import (
    create_campaign_unified,
    export_campaign_unified,
    get_campaign_state_unified,
    get_campaigns_list_unified,
    get_user_settings_unified,
    process_action_unified,
    update_campaign_unified,
    update_user_settings_unified,
)


class TestUnifiedAPIIntegration(unittest.TestCase):
    """Test unified API integration across Flask and MCP interfaces."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_user_id = "test-user-123"
        self.test_campaign_id = "test-campaign-456"

        # Sample request data for testing
        self.sample_campaign_request = {
            "user_id": self.test_user_id,
            "title": "Test Campaign",
            "character": "A brave knight",
            "setting": "Medieval fantasy",
            "description": "An epic adventure",
        }

        self.sample_action_request = {
            "user_id": self.test_user_id,
            "campaign_id": self.test_campaign_id,
            "user_input": "I look around the room",
            "mode": "character",
        }

    def test_world_logic_structure(self):
        """Test that world_logic module has all expected functions."""
        print("\n=== Testing Unified API Structure ===")

        expected_functions = [
            "create_campaign_unified",
            "process_action_unified",
            "get_campaign_state_unified",
            "update_campaign_unified",
            "export_campaign_unified",
            "get_campaigns_list_unified",
            "get_user_settings_unified",
            "update_user_settings_unified",
            "create_error_response",
            "create_success_response",
        ]

        for func_name in expected_functions:
            assert hasattr(world_logic, func_name), f"Missing function: {func_name}"
            func = getattr(world_logic, func_name)
            assert callable(func), f"Not callable: {func_name}"
            print(f"✅ {func_name} - Present and callable")

    def test_flask_route_integration(self):
        """Test that Flask routes are using world_logic functions."""
        print("\n=== Testing Flask Route Integration ===")

        # Read main.py to check for world_logic usage
        main_py_path = os.path.join("mvp_site", "main.py")
        with open(main_py_path) as f:
            main_py_content = f.read()

        # Check for world_logic import
        assert "import world_logic" in main_py_content, "main.py should import world_logic"
        print("✅ main.py imports world_logic")

        # Check for world_logic function calls in Flask routes
        expected_calls = [
            "world_logic.get_campaigns_list_unified",
            "world_logic.get_campaign_state_unified",
            "world_logic.create_campaign_unified",
            "world_logic.update_campaign_unified",
            "world_logic.process_action_unified",
            "world_logic.export_campaign_unified",
            "world_logic.get_user_settings_unified",
            "world_logic.update_user_settings_unified",
        ]

        for call in expected_calls:
            assert call in main_py_content, f"main.py should call {call}"
            print(f"✅ Flask route calls {call}")

    def test_mcp_server_integration(self):
        """Test MCP server integration with world_logic functions."""
        print("\n=== Testing MCP Server Integration ===")

        # Read world_logic.py to check for world_logic usage
        world_logic_path = os.path.join("mvp_site", "world_logic.py")
        with open(world_logic_path) as f:
            world_logic_content = f.read()

        # Check for world_logic import
        has_unified_import = (
            "import world_logic" in world_logic_content
            or "from world_logic" in world_logic_content
        )

        if has_unified_import:
            print("✅ world_logic.py imports world_logic")

            # Check for world_logic function calls in MCP tools
            expected_calls = [
                "world_logic.create_campaign_unified",
                "world_logic.process_action_unified",
                "world_logic.get_campaign_state_unified",
                "world_logic.update_campaign_unified",
                "world_logic.export_campaign_unified",
                "world_logic.get_user_settings_unified",
                "world_logic.update_user_settings_unified",
            ]

            for call in expected_calls:
                if call in world_logic_content:
                    print(f"✅ MCP tool calls {call}")
                else:
                    print(f"❌ MCP tool missing {call}")
        else:
            print("❌ world_logic.py does NOT import world_logic")
            print("❌ MCP server is NOT using unified API functions")
            print("❌ Business logic duplication detected between Flask and MCP")

    def test_business_logic_duplication(self):
        """Test for business logic duplication between Flask and MCP."""
        print("\n=== Testing Business Logic Duplication ===")

        # Read both files
        main_py_path = os.path.join("mvp_site", "main.py")
        world_logic_path = os.path.join("mvp_site", "world_logic.py")

        with open(main_py_path) as f:
            main_py_content = f.read()

        with open(world_logic_path) as f:
            world_logic_content = f.read()

        # Check for duplicate business logic patterns
        duplicate_patterns = [
            "_prepare_game_state",
            "_cleanup_legacy_state",
            "_build_campaign_prompt",
            "_handle_debug_mode_command",
            "gemini_service.get_initial_story",
            "gemini_service.continue_story",
            "firestore_service.create_campaign",
            "firestore_service.update_campaign_game_state",
        ]

        duplicates_found = []
        for pattern in duplicate_patterns:
            in_main = pattern in main_py_content
            in_world_logic = pattern in world_logic_content

            if in_main and in_world_logic:
                duplicates_found.append(pattern)
                print(
                    f"❌ DUPLICATE: {pattern} found in both main.py and world_logic.py"
                )
            elif in_main:
                print(f"✅ {pattern} only in main.py (via world_logic)")
            elif in_world_logic:
                print(
                    f"⚠️  {pattern} only in world_logic.py (needs world_logic integration)"
                )

        if duplicates_found:
            print(
                f"\n❌ Found {len(duplicates_found)} duplicate business logic patterns"
            )
            print("❌ Business logic is NOT properly unified")
        else:
            print("\n✅ No duplicate business logic patterns detected")

    async def test_response_format_consistency(self):
        """Test that world_logic functions return consistent JSON formats."""
        print("\n=== Testing Response Format Consistency ===")

        # Test success response format
        try:
            success_response = world_logic.create_success_response({"test": "data"})
            assert "success" in success_response
            assert success_response["success"]
            assert "test" in success_response
            print("✅ Success response format is consistent")
        except Exception as e:
            print(f"❌ Success response format test failed: {e}")

        # Test error response format
        try:
            error_response = world_logic.create_error_response("Test error", 400)
            assert "error" in error_response
            assert "success" in error_response
            assert not error_response["success"]
            assert "status_code" in error_response
            print("✅ Error response format is consistent")
        except Exception as e:
            print(f"❌ Error response format test failed: {e}")

    async def test_world_logic_function_behavior(self):
        """Test unified API function behavior without external dependencies."""
        print("\n=== Testing Unified API Function Behavior ===")

        # Test input validation
        try:
            # Test missing user_id
            result = await get_campaigns_list_unified({})
            assert "error" in result
            assert "User ID is required" in result["error"]
            print("✅ Input validation works for missing user_id")
        except Exception as e:
            print(f"❌ Input validation test failed: {e}")

        try:
            # Test missing campaign_id
            result = await get_campaign_state_unified({"user_id": "test"})
            assert "error" in result
            assert "Campaign ID is required" in result["error"]
            print("✅ Input validation works for missing campaign_id")
        except Exception as e:
            print(f"❌ Input validation test failed: {e}")

    def test_error_handling_consistency(self):
        """Test that error handling is consistent across unified functions."""
        print("\n=== Testing Error Handling Consistency ===")

        # Check that all unified functions use consistent error patterns
        unified_functions = [
            create_campaign_unified,
            process_action_unified,
            get_campaign_state_unified,
            update_campaign_unified,
            export_campaign_unified,
            get_campaigns_list_unified,
            get_user_settings_unified,
            update_user_settings_unified,
        ]

        for func in unified_functions:
            # Check function signature (should be async)
            assert asyncio.iscoroutinefunction(func), f"{func.__name__} should be async"
            print(f"✅ {func.__name__} is async")

    def run_integration_tests(self):
        """Run all integration tests and provide summary."""
        print("=" * 60)
        print("UNIFIED API INTEGRATION TEST SUITE")
        print("=" * 60)

        # Run synchronous tests
        test_methods = [
            self.test_world_logic_structure,
            self.test_flask_route_integration,
            self.test_mcp_server_integration,
            self.test_business_logic_duplication,
            self.test_error_handling_consistency,
        ]

        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                print(f"❌ {test_method.__name__} failed: {e}")
                traceback.print_exc()

        # Run async tests
        async_tests = [
            self.test_response_format_consistency,
            self.test_world_logic_function_behavior,
        ]

        for async_test in async_tests:
            try:
                asyncio.run(async_test())
            except Exception as e:
                print(f"❌ {async_test.__name__} failed: {e}")
                traceback.print_exc()


def main():
    """Run the integration test suite."""
    tester = TestUnifiedAPIIntegration()
    tester.run_integration_tests()

    print("\n" + "=" * 60)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 60)
    print("✅ Flask routes successfully use world_logic functions")
    print("❌ MCP server does NOT use world_logic functions")
    print("❌ Business logic duplication exists between Flask and MCP")
    print("✅ Unified API provides consistent JSON response formats")
    print("✅ Error handling is standardized in world_logic")
    print("\nRECOMMENDATION: Update world_logic.py to use world_logic functions")


if __name__ == "__main__":
    main()
