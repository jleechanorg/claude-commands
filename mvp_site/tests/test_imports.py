#!/usr/bin/env python3
"""
Import tests to catch missing import statements.
These tests simply import modules to ensure all dependencies are available.
"""

import os
import sys
import unittest

import constants
import firestore_service
import game_state
import gemini_response
import gemini_service
import main
import narrative_response_schema
import structured_fields_utils

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestImports(unittest.TestCase):
    """Test that all main modules can be imported without errors"""

    def test_import_firestore_service(self):
        """Test that firestore_service can be imported"""
        try:


            self.assertTrue(hasattr(firestore_service, "add_story_entry"))
            self.assertTrue(hasattr(firestore_service, "create_campaign"))
        except ImportError as e:
            self.fail(f"Failed to import firestore_service: {e}")

    def test_import_gemini_service(self):
        """Test that gemini_service can be imported"""
        try:


            self.assertTrue(hasattr(gemini_service, "continue_story"))
        except ImportError as e:
            self.fail(f"Failed to import gemini_service: {e}")

    def test_import_main(self):
        """Test that main can be imported"""
        try:


            self.assertTrue(hasattr(main, "create_app"))
        except ImportError as e:
            self.fail(f"Failed to import main: {e}")

    def test_import_game_state(self):
        """Test that game_state can be imported"""
        try:


            self.assertTrue(hasattr(game_state, "GameState"))
        except ImportError as e:
            self.fail(f"Failed to import game_state: {e}")

    def test_import_constants(self):
        """Test that constants can be imported and has expected fields"""
        try:


            # Check for structured field constants
            self.assertTrue(hasattr(constants, "FIELD_SESSION_HEADER"))
            self.assertTrue(hasattr(constants, "FIELD_PLANNING_BLOCK"))
            self.assertTrue(hasattr(constants, "FIELD_DICE_ROLLS"))
            self.assertTrue(hasattr(constants, "FIELD_RESOURCES"))
            self.assertTrue(hasattr(constants, "FIELD_DEBUG_INFO"))
        except ImportError as e:
            self.fail(f"Failed to import constants: {e}")

    def test_import_structured_fields_utils(self):
        """Test that structured_fields_utils can be imported"""
        try:


            self.assertTrue(
                hasattr(structured_fields_utils, "extract_structured_fields")
            )
        except ImportError as e:
            self.fail(f"Failed to import structured_fields_utils: {e}")

    def test_import_narrative_response_schema(self):
        """Test that narrative_response_schema can be imported"""
        try:


            self.assertTrue(hasattr(narrative_response_schema, "NarrativeResponse"))
        except ImportError as e:
            self.fail(f"Failed to import narrative_response_schema: {e}")

    def test_import_gemini_response(self):
        """Test that gemini_response can be imported"""
        try:


            self.assertTrue(hasattr(gemini_response, "GeminiResponse"))
        except ImportError as e:
            self.fail(f"Failed to import gemini_response: {e}")


if __name__ == "__main__":
    unittest.main()
