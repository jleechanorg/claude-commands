#!/usr/bin/env python3
"""
Run all HTTP simulation tests.
These tests make direct HTTP requests to the Flask server.
"""

import os
import subprocess
import sys
import time
from datetime import datetime

# Test files to run
HTTP_TESTS = [
    "test_continue_campaign.py",
    "test_multiple_turns.py",
    "test_god_mode.py",
    "test_character_creation.py",
    "test_export_download.py",
    "test_settings_theme.py",
    "test_error_cases.py",
    "test_http_browser_simulation.py",
]


def run_http_test(test_file):
    """Run a single HTTP test file."""
    test_path = os.path.join(os.path.dirname(__file__), test_file)

    if not os.path.exists(test_path):
        print(f"⚠️  Test file not found: {test_file}")
        return False

    print(f"\n{'=' * 60}")
    print(f"🔗 Running: {test_file}")
    print(f"{'=' * 60}")

    start_time = time.time()

    # Run the test with TESTING=true
    env = os.environ.copy()
    env["TESTING"] = "true"

    result = subprocess.run(
        [sys.executable, test_path],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    duration = time.time() - start_time

    # Print output
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    # Check result
    if result.returncode == 0:
        print(f"✅ PASSED ({duration:.2f}s)")
        return True
    print(f"❌ FAILED ({duration:.2f}s)")
    return False


def main():
    """Run all HTTP tests."""
    print("🚀 WorldArchitect.AI HTTP Test Suite")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🔗 Testing with HTTP requests (requests library)")
    print("=" * 60)

    # Check if test server is running
    import requests

    try:
        response = requests.get("http://localhost:8086", timeout=2)
        print("✅ Test server is running on port 8086")
    except:
        print("⚠️  WARNING: Test server not responding at http://localhost:8086")
        print("   Tests may use different ports or start their own servers")

    print("\n" + "=" * 60)

    # Run all tests
    passed = 0
    failed = 0
    skipped = 0

    for test_file in HTTP_TESTS:
        if os.path.exists(os.path.join(os.path.dirname(__file__), test_file)):
            if run_http_test(test_file):
                passed += 1
            else:
                failed += 1
        else:
            print(f"\n⚠️  Skipping {test_file} (not found)")
            skipped += 1

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   ⚠️  Skipped: {skipped}")
    print(f"   📋 Total: {len(HTTP_TESTS)}")
    print("=" * 60)

    # Overall result
    if failed == 0 and passed > 0:
        print("\n✅ ALL HTTP TESTS PASSED!")
        return 0
    print(f"\n❌ HTTP TESTS FAILED ({failed} failures)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
