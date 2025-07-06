#!/usr/bin/env python3
"""
Run all browser simulation tests
"""

import os
import sys
import subprocess
import time

# Test files in order
TEST_FILES = [
    "test_continue_campaign.py",
    "test_multiple_turns.py", 
    "test_god_mode.py",
    "test_character_creation.py",
    "test_export_download.py",
    "test_settings_theme.py",
    "test_error_cases.py",
    "test_http_browser_simulation.py"
]

def run_test(test_file):
    """Run a single test file."""
    print(f"\n{'='*70}")
    print(f"🏃 Running {test_file}")
    print(f"{'='*70}")
    
    result = subprocess.run(
        [sys.executable, test_file],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result.returncode == 0

def main():
    """Run all tests and summarize results."""
    print("🌐 WorldArchitect.AI Browser Test Suite")
    print("=====================================")
    print(f"Running {len(TEST_FILES)} test files...\n")
    
    # Change to test directory
    test_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(test_dir)
    
    # Track results
    results = {}
    start_time = time.time()
    
    # Run each test
    for test_file in TEST_FILES:
        if os.path.exists(test_file):
            success = run_test(test_file)
            results[test_file] = success
            time.sleep(0.5)  # Small delay between tests
        else:
            print(f"⚠️ Test file not found: {test_file}")
            results[test_file] = False
    
    # Summary
    elapsed = time.time() - start_time
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\n{'='*70}")
    print("📊 TEST SUMMARY")
    print(f"{'='*70}")
    
    for test, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test}")
    
    print(f"\nTotal: {passed}/{total} passed ({passed/total*100:.1f}%)")
    print(f"Time: {elapsed:.2f} seconds")
    
    # Overall result
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        return 0
    else:
        print(f"\n❌ {total - passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())