#!/usr/bin/env python3
"""
Run all tests in the prototype package.
"""

import os
import sys
import unittest

# Get the directory containing this script
repo_root = os.path.dirname(os.path.abspath(__file__))

# Discover and run tests
loader = unittest.TestLoader()
start_dir = os.path.join(repo_root, "prototype", "tests")
suite = loader.discover(start_dir, pattern="test_*.py", top_level_dir=repo_root)

# Run the tests
runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)

# Exit with proper code
sys.exit(0 if result.wasSuccessful() else 1)
