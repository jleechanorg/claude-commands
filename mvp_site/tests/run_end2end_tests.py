#!/usr/bin/env python3
"""
Runner script for end-to-end integration tests.
Run this from the project root with the virtual environment activated.

Usage:
    python mvp_site/tests/run_end2end_tests.py
"""

import unittest
import sys
import os

# Add the mvp_site directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import all test modules
from tests import test_create_campaign_end2end
from tests import test_continue_story_end2end
from tests import test_visit_campaign_end2end

def run_tests():
    """Run all end-to-end integration tests."""
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromModule(test_create_campaign_end2end))
    suite.addTests(loader.loadTestsFromModule(test_continue_story_end2end))
    suite.addTests(loader.loadTestsFromModule(test_visit_campaign_end2end))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code based on test results
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    print("Running End-to-End Integration Tests")
    print("=" * 60)
    print("These tests mock only external services (Firestore & Gemini)")
    print("and test the full application flow through all layers.")
    print("=" * 60)
    
    exit_code = run_tests()
    
    if exit_code == 0:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed.")
    
    sys.exit(exit_code)