#!/usr/bin/env python3
"""
Run browser tests with REAL Firebase and Gemini APIs.
This costs money! Use with caution.
"""

import os
import sys
import subprocess
from datetime import datetime

# Import the regular browser test runner
from run_all_browser_tests import BROWSER_TESTS, check_playwright_installed, run_browser_test

def main():
    """Run browser tests with real APIs."""
    print("🚀 WorldArchitect.AI Browser Test Suite (REAL APIs)")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🌐 Testing with REAL browser automation (Playwright)")
    print("💰 WARNING: Using REAL Firebase and Gemini APIs - This costs money!")
    print("="*60)
    
    # Confirm with user
    response = input("\n⚠️  Do you want to continue with REAL API tests? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Aborted by user")
        return 1
    
    # Set environment variables for real APIs
    os.environ['REAL_APIS'] = 'true'
    os.environ['TESTING'] = 'true'
    
    # Check prerequisites
    if not check_playwright_installed():
        sys.exit(1)
    
    print("\n" + "="*60)
    
    # Run all tests
    passed = 0
    failed = 0
    skipped = 0
    
    for test_file in BROWSER_TESTS:
        if os.path.exists(os.path.join(os.path.dirname(__file__), test_file)):
            if run_browser_test(test_file):
                passed += 1
            else:
                failed += 1
        else:
            print(f"\n⚠️  Skipping {test_file} (not found)")
            skipped += 1
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary (REAL APIs):")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   ⚠️  Skipped: {skipped}")
    print(f"   📋 Total: {len(BROWSER_TESTS)}")
    print("="*60)
    
    # Overall result
    if failed == 0 and passed > 0:
        print("\n✅ ALL BROWSER TESTS PASSED (with REAL APIs)!")
        return 0
    else:
        print(f"\n❌ BROWSER TESTS FAILED ({failed} failures)")
        return 1

if __name__ == "__main__":
    sys.exit(main())