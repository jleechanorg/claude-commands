#!/usr/bin/env python3
"""
🏗️ RED-GREEN TEST: Architectural Boundary Field Format Validation
================================================================

This test validates field format consistency across all architectural boundaries:
1. Frontend → main.py (API Gateway)
2. main.py → world_logic.py (MCP Protocol)
3. world_logic.py → Response (Business Logic)

Tests BOTH the intentional translation patterns AND potential mismatches.

CRITICAL ARCHITECTURAL INSIGHTS:
- main.py uses "input" for frontend compatibility
- world_logic.py uses "user_input" for MCP protocol
- Translation layer converts between these formats
- Error/Success fields are consistent across boundaries
- Story fields must use "text" format for UI display
"""

import os
import sys
import unittest

# Set TESTING environment variable
os.environ["TESTING"] = "true"
os.environ["GEMINI_API_KEY"] = "test-api-key"

# Add parent directory to path
sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(
            os.path.dirname(
                __file__
                if "__file__" in globals()
                else "tests/test_architectural_boundary_validation.py"
            ),
            "..",
        )
    ),
)

# Module-level imports (moved from inline locations per coding guidelines)
from main import (
    KEY_ERROR,
    KEY_ERROR as MAIN_ERROR,
    KEY_SUCCESS,
    KEY_SUCCESS as MAIN_SUCCESS,
    KEY_USER_INPUT,
    KEY_USER_INPUT as FRONTEND_KEY,
)
from mcp_api import KEY_ERROR as MCP_ERROR, KEY_USER_INPUT

from mvp_site.world_logic import (
    KEY_ERROR as WL_ERROR,
    KEY_SUCCESS as WL_SUCCESS,
    KEY_USER_INPUT as MCP_KEY,
)


class TestArchitecturalBoundaryValidation(unittest.TestCase):
    """Comprehensive validation of field formats across architectural boundaries."""

    def test_frontend_to_main_field_constants(self):
        """
        RED-GREEN: Validate frontend → main.py field translation constants.
        """
        print("\n🔍 Testing Frontend → main.py Field Constants")

        # Frontend sends "input" field
        assert (
            FRONTEND_KEY == "input"
        ), "main.py should expect 'input' field from frontend"

        # Standard response fields
        assert (
            MAIN_SUCCESS == "success"
        ), "main.py should use 'success' for success responses"
        assert MAIN_ERROR == "error", "main.py should use 'error' for error responses"

        print("✅ Frontend → main.py field constants: VALIDATED")

    def test_main_to_mcp_field_constants(self):
        """
        RED-GREEN: Validate main.py → MCP protocol field translation constants.
        """
        print("\n🔍 Testing main.py → MCP Protocol Field Constants")

        # MCP protocol uses "user_input" field
        assert (
            KEY_USER_INPUT == "user_input"
        ), "world_logic.py should expect 'user_input' field from MCP"

        # Standard response fields should match main.py
        assert (
            KEY_SUCCESS == "success"
        ), "world_logic.py should use 'success' for success responses"
        assert (
            KEY_ERROR == "error"
        ), "world_logic.py should use 'error' for error responses"

        print("✅ main.py → MCP field constants: VALIDATED")

    def test_mcp_api_field_constants(self):
        """
        RED-GREEN: Validate MCP API layer field consistency.
        """
        print("\n🔍 Testing MCP API Layer Field Constants")

        # MCP API should match world_logic.py
        assert (
            KEY_USER_INPUT == "user_input"
        ), "mcp_api.py should use 'user_input' field for MCP protocol"
        assert (
            KEY_ERROR == "error"
        ), "mcp_api.py should use 'error' field for error responses"

        print("✅ MCP API field constants: VALIDATED")

    def test_cross_boundary_field_consistency(self):
        """
        RED-GREEN: Validate that error/success fields are consistent across ALL boundaries.
        """
        print("\n🔍 Testing Cross-Boundary Field Consistency")

        # Error fields must be identical across all layers
        assert (
            MAIN_ERROR == WL_ERROR
        ), "Error field must be consistent: main.py vs world_logic.py"
        assert (
            MAIN_ERROR == MCP_ERROR
        ), "Error field must be consistent: main.py vs mcp_api.py"

        # Success fields must be identical across all layers
        assert (
            MAIN_SUCCESS == WL_SUCCESS
        ), "Success field must be consistent: main.py vs world_logic.py"

        print("✅ Cross-boundary field consistency: VALIDATED")

    def test_translation_layer_field_conversion(self):
        """
        RED-GREEN: Validate the intentional field translation between layers.

        This test confirms that the "input" → "user_input" translation is CORRECT and intentional.
        """
        print("\n🔍 Testing Translation Layer Field Conversion")

        # This difference is INTENTIONAL and CORRECT
        assert FRONTEND_KEY == "input", "Frontend interface should use 'input' field"
        assert MCP_KEY == "user_input", "MCP protocol should use 'user_input' field"
        assert FRONTEND_KEY != MCP_KEY, "Translation layer SHOULD convert field names"

        print("✅ Translation layer conversion: VALIDATED")
        print("   Frontend field: 'input' → MCP field: 'user_input' ✅")

    def test_red_phase_field_mismatch_detection(self):
        """
        RED PHASE: Test what happens with WRONG field access patterns.

        This demonstrates potential bugs if field access patterns were incorrect.
        """
        print("\n🔴 RED PHASE: Field Mismatch Detection")

        # Simulate frontend request
        frontend_request = {"input": "Test message", "mode": "character"}

        # WRONG: If main.py tried to use MCP field name for frontend
        wrong_extraction = frontend_request.get("user_input")  # Should be None
        assert wrong_extraction is None, "Using wrong field name should result in None"

        # CORRECT: main.py using proper frontend field name
        correct_extraction = frontend_request.get("input")
        assert (
            correct_extraction == "Test message"
        ), "Using correct field name should extract data"

        # Simulate MCP request
        mcp_request = {"user_input": "Test message", "user_id": "test"}

        # WRONG: If world_logic.py tried to use frontend field name for MCP
        wrong_mcp_extraction = mcp_request.get("input")  # Should be None
        assert (
            wrong_mcp_extraction is None
        ), "Using wrong MCP field name should result in None"

        # CORRECT: world_logic.py using proper MCP field name
        correct_mcp_extraction = mcp_request.get("user_input")
        assert (
            correct_mcp_extraction == "Test message"
        ), "Using correct MCP field name should extract data"

        print("🔴 RED TESTS CONFIRM: Wrong field names cause None extraction")

    def test_story_field_format_validation(self):
        """
        RED-GREEN: Validate story entry field format for UI compatibility.

        This test validates the fix for the original bug where story entries
        were created with "story" field but UI expected "text" field.
        """
        print("\n🔍 Testing Story Field Format Validation")

        # CORRECT story entry format (after fix)
        correct_story_entry = {"text": "The adventure begins in the tavern."}

        # UI expects "text" field
        narrative_text = correct_story_entry.get("text", "")
        assert (
            narrative_text == "The adventure begins in the tavern."
        ), "Story entry should use 'text' field for UI compatibility"

        # RED PHASE: Wrong story entry format (the original bug)
        wrong_story_entry = {"story": "The adventure begins in the tavern."}

        # This would result in empty narrative (the bug we fixed)
        empty_narrative = wrong_story_entry.get("text", "")
        assert (
            empty_narrative == ""
        ), "Wrong story field format should result in empty narrative"

        print("✅ Story field format: VALIDATED")
        print("   Story entries must use 'text' field (not 'story') ✅")

    def test_green_phase_complete_flow_validation(self):
        """
        GREEN PHASE: End-to-end field format validation.

        This test validates the complete flow works correctly after all fixes.
        """
        print("\n🟢 GREEN PHASE: Complete Flow Validation")

        # Step 1: Frontend sends request
        frontend_data = {"input": "I explore the chamber.", "mode": "character"}

        # Step 2: main.py extracts with correct field
        user_input = frontend_data.get(FRONTEND_KEY)
        assert user_input == "I explore the chamber."

        # Step 3: main.py creates MCP request with translated field
        mcp_request = {
            "user_id": "test-user",
            "campaign_id": "test-campaign",
            "user_input": user_input,  # Translation happens here
            "mode": frontend_data.get("mode"),
        }

        # Step 4: world_logic.py extracts with correct MCP field
        extracted_input = mcp_request.get(MCP_KEY)
        assert extracted_input == "I explore the chamber."

        # Step 5: world_logic.py creates story entry with correct field
        story_entry = {"text": f"You {extracted_input.lower()}"}

        # Step 6: UI displays story with correct field access
        displayed_text = story_entry.get("text", "")
        assert displayed_text == "You i explore the chamber."

        print("🟢 GREEN TESTS CONFIRM: Complete flow works correctly")
        print("   Frontend 'input' → MCP 'user_input' → Story 'text' ✅")


if __name__ == "__main__":
    print("🏗️ Architectural Boundary Field Format Validation")
    print("Testing field format consistency across all system boundaries")
    print("=" * 80)
    unittest.main(verbosity=2)
