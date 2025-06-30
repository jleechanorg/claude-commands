#!/usr/bin/env python3
"""
Runner for full integration test suite.
"""

import sys
import os

# Run the integration test module
result = os.system(f"{sys.executable} -m prototype.run_integration_tests")

sys.exit(result >> 8)  # Extract exit code from os.system result