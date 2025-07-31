#!/usr/bin/env python3
"""
RED Phase: Test that Flask app can be imported from main.py
This test should FAIL initially, demonstrating the issue.
"""

import os
import sys
import unittest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestFlaskAppImport(unittest.TestCase):
    """Test that Flask app is properly importable"""

    def test_app_import_from_main(self):
        """Test that we can import app from main module"""
        try:
            from main import app

            self.assertIsNotNone(app, "App should not be None")
            self.assertTrue(hasattr(app, "run"), "App should have run method")
        except ImportError as e:
            self.fail(f"Failed to import app from main: {e}")

    def test_create_app_function_exists(self):
        """Test that create_app function exists and works"""
        from main import create_app

        app = create_app()
        self.assertIsNotNone(app, "create_app should return Flask app")
        self.assertTrue(hasattr(app, "run"), "App should have run method")


if __name__ == "__main__":
    unittest.main()
