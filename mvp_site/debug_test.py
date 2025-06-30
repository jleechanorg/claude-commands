#!/usr/bin/env python3
"""
Debug test runner for Milestone 4
"""

import sys
import traceback
from pathlib import Path

# Add the mvp_site directory to Python path
mvp_site_path = Path(__file__).parent
sys.path.insert(0, str(mvp_site_path))

from test_milestone_4_interactive_features import TestMilestone4InteractiveFeatures

def run_single_test(test_name):
    """Run a single test and capture any errors"""
    test_instance = TestMilestone4InteractiveFeatures()
    test_instance.setUp()
    
    try:
        test_method = getattr(test_instance, test_name)
        test_method()
        print(f"✅ {test_name} PASSED")
        return True
    except Exception as e:
        print(f"❌ {test_name} FAILED:")
        print(f"   Error: {e}")
        print(f"   Traceback: {traceback.format_exc()}")
        return False
    finally:
        test_instance.tearDown()

def main():
    """Run all tests individually to identify failures"""
    print("🔍 Debug Test Runner for Milestone 4")
    print("=" * 50)
    
    # Get all test methods
    test_methods = [method for method in dir(TestMilestone4InteractiveFeatures) 
                   if method.startswith('test_')]
    
    passed = 0
    failed = 0
    
    for test_method in test_methods:
        if run_single_test(test_method):
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 SUMMARY: {passed} passed, {failed} failed")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 