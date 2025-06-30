#!/usr/bin/env python3
"""
Run integration tests for the validation prototype.
"""

import sys
import os
import unittest

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import test module
from tests import test_integration

if __name__ == "__main__":
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(test_integration)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with error code if tests failed
    sys.exit(0 if result.wasSuccessful() else 1)