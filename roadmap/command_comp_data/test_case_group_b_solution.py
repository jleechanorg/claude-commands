#!/usr/bin/env python3
"""
Simple debugging task for A/B testing - FIXED - roadmap test case
"""

import os
import sys

# Add paths for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
mvp_site_path = os.path.join(project_root, 'mvp_site')

sys.path.insert(0, current_dir)
sys.path.insert(0, mvp_site_path)
sys.path.insert(0, project_root)

# Set testing mode
os.environ["TESTING"] = "true"
os.environ["MOCK_SERVICES_MODE"] = "true"


def process_data(items):
    """Process list of numbers with group B solution."""
    results = []
    for item in items:
        if item > 0:
            results.append(item * 2)
        else:
            results.append(item * -1)  # Fixed: multiply by -1 instead of dividing by 0
    return results


def test_process_data():
    """Test the process_data function with group B solution."""
    test_data = [1, 2, -1, 3, 0, 4]
    expected = [2, 4, 1, 6, 0, 8]  # Note: -1 becomes 1, 0 becomes 0
    result = process_data(test_data)
    
    print("Processing:", test_data)
    print("Result:", result)
    print("Expected:", expected)
    
    assert result == expected, f"Expected {expected}, got {result}"
    print("✅ Test passed")


if __name__ == "__main__":
    test_process_data()
