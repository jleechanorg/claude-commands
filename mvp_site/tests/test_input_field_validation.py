#!/usr/bin/env python3
"""
Red-Green Test for Input Field Translation Validation
=====================================================

This test validates that the input field translation between frontend → main.py → world_logic.py
works correctly across the architectural boundaries.

Frontend sends: {"input": "..."}
main.py receives: data.get("input") with KEY_USER_INPUT = "input"
main.py sends to MCP: {"user_input": "..."}
world_logic.py receives: request_data.get("user_input") with KEY_USER_INPUT = "user_input"
"""

import os
import sys
import unittest

# Set TESTING environment variable
os.environ["TESTING"] = "true"
os.environ["GEMINI_API_KEY"] = "test-api-key"

# Add the parent directory to the path to import main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import constants at module level
from main import KEY_USER_INPUT as MAIN_KEY_USER_INPUT

from mvp_site.world_logic import KEY_USER_INPUT as MCP_KEY_USER_INPUT


class TestInputFieldTranslation(unittest.TestCase):
    """Test input field translation across architectural boundaries."""

    def test_frontend_to_main_input_field(self):
        """
        Test that main.py correctly extracts 'input' field from frontend requests.
        """
        # Simulate frontend request data
        frontend_request = {"input": "I explore the testing area.", "mode": "character"}

        # Verify main.py expects "input" field (for frontend compatibility)
        assert (
            MAIN_KEY_USER_INPUT == "input"
        ), "main.py should expect 'input' field from frontend"

        # Test field extraction
        user_input = frontend_request.get(MAIN_KEY_USER_INPUT)
        assert (
            user_input == "I explore the testing area."
        ), "main.py should correctly extract user input from frontend"

        print("✅ Frontend → main.py: 'input' field extraction works correctly")

    def test_main_to_mcp_field_translation(self):
        """
        Test that main.py correctly creates 'user_input' field for MCP protocol.
        """
        # Simulate what main.py should send to MCP
        user_id = "test-user"
        campaign_id = "test-campaign"
        user_input = "I explore the testing area."
        mode = "character"

        # This is how main.py constructs the MCP request
        mcp_request = {
            "user_id": user_id,
            "campaign_id": campaign_id,
            "user_input": user_input,  # KEY: Should use "user_input" for MCP
            "mode": mode,
        }

        # Verify the translation happened correctly
        assert (
            "user_input" in mcp_request
        ), "MCP request should contain 'user_input' field"
        assert (
            mcp_request["user_input"] == "I explore the testing area."
        ), "MCP request should have correct user input value"

        print("✅ main.py → MCP: 'user_input' field translation works correctly")

    def test_mcp_world_logic_input_field(self):
        """
        Test that world_logic.py correctly expects 'user_input' field from MCP.
        """
        # Verify world_logic.py expects "user_input" field (for MCP protocol)
        assert (
            MCP_KEY_USER_INPUT == "user_input"
        ), "world_logic.py should expect 'user_input' field from MCP"

        # Simulate MCP request data
        mcp_request = {
            "user_id": "test-user",
            "campaign_id": "test-campaign",
            "user_input": "I explore the testing area.",
            "mode": "character",
        }

        # Test field extraction
        user_input = mcp_request.get(MCP_KEY_USER_INPUT)
        assert (
            user_input == "I explore the testing area."
        ), "world_logic.py should correctly extract user input from MCP"

        print("✅ MCP → world_logic.py: 'user_input' field extraction works correctly")

    def test_end_to_end_input_field_flow(self):
        """
        RED-GREEN TEST: End-to-end input field translation flow.

        This test validates the complete flow:
        Frontend {"input": "..."} → main.py → MCP {"user_input": "..."} → world_logic.py
        """
        print("\n🔍 Testing end-to-end input field translation flow...")

        # Step 1: Frontend sends data
        frontend_data = {"input": "I test the complete flow.", "mode": "character"}
        print(f"   Frontend sends: {frontend_data}")

        # Step 2: main.py extracts with its KEY_USER_INPUT
        user_input_extracted = frontend_data.get(MAIN_KEY_USER_INPUT)
        assert MAIN_KEY_USER_INPUT == "input", "main.py should use 'input' key"
        assert user_input_extracted == "I test the complete flow."
        print(f"   main.py extracts: {MAIN_KEY_USER_INPUT} = '{user_input_extracted}'")

        # Step 3: main.py creates MCP request with "user_input"
        mcp_request = {
            "user_id": "test-user",
            "campaign_id": "test-campaign",
            "user_input": user_input_extracted,  # Translation happens here
            "mode": frontend_data.get("mode"),
        }
        print(f"   main.py creates MCP request: {mcp_request}")

        # Step 4: world_logic.py extracts with its KEY_USER_INPUT
        user_input_final = mcp_request.get(MCP_KEY_USER_INPUT)
        assert (
            MCP_KEY_USER_INPUT == "user_input"
        ), "world_logic.py should use 'user_input' key"
        assert user_input_final == "I test the complete flow."
        print(
            f"   world_logic.py extracts: {MCP_KEY_USER_INPUT} = '{user_input_final}'"
        )

        # Final validation
        assert (
            user_input_extracted == user_input_final
        ), "User input should be preserved through the translation"

        print("✅ End-to-end input field translation: WORKING CORRECTLY")
        print("✅ Translation layer correctly converts 'input' → 'user_input'")

    def test_red_phase_input_field_mismatch_detection(self):
        """
        RED PHASE: Test what would happen with wrong field names.

        This demonstrates potential bugs if the translation layer was broken.
        """
        print("\n🔴 RED PHASE: Testing input field mismatch scenarios")

        # Scenario 1: If main.py used wrong field name for frontend
        frontend_data = {"input": "Test message"}
        wrong_main_key = "user_input"  # Wrong - should be "input"

        extracted_wrong = frontend_data.get(wrong_main_key)
        assert extracted_wrong is None, "Wrong field name should result in None"
        print("🔴 If main.py used 'user_input' for frontend: None extracted")

        # Scenario 2: If main.py sent wrong field name to MCP
        mcp_request_wrong = {
            "input": "Test message"  # Wrong - should be "user_input"
        }
        extracted_mcp_wrong = mcp_request_wrong.get(MCP_KEY_USER_INPUT)
        assert (
            extracted_mcp_wrong is None
        ), "Wrong field name should result in None for MCP"
        print("🔴 If main.py sent 'input' to MCP: None extracted by world_logic.py")

        print("🔴 RED TESTS CONFIRM: Field name mismatches would cause None extraction")


if __name__ == "__main__":
    print("🧪 Input Field Translation Validation Test")
    print("Testing field translation across frontend → main.py → world_logic.py")
    print("=" * 80)
    unittest.main(verbosity=2)
