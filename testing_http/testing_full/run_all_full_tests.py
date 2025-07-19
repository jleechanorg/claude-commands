#!/usr/bin/env python3
"""
Run all FULL API browser tests (using real Firebase and Gemini).

WARNING: These tests cost money and use real API quotas!
"""

import os
import subprocess
import sys
import time
from datetime import datetime

from test_config_full import validate_config

# Test files in order of complexity/cost
TEST_FILES = [
    "test_continue_campaign_full.py",
    "test_god_mode_full.py",
    # Add more as we create them:
    # "test_multiple_turns_full.py",
    # "test_character_creation_full.py",
    # "test_export_download_full.py",
    # "test_error_cases_full.py",
    # "test_settings_theme_full.py",
]


def run_test(test_file, log_file):
    """Run a single test file."""
    output = f"\n{'=' * 70}\n"
    output += f"🏃 Running {test_file}\n"
    output += f"{'=' * 70}\n"
    print(output, end="")
    log_file.write(output)
    log_file.flush()

    result = subprocess.run(
        [sys.executable, test_file],
        check=False,
        capture_output=True,
        text=True,
        input="y\n",  # Auto-confirm for batch runs
    )

    print(result.stdout)
    log_file.write(result.stdout + "\n")
    if result.stderr:
        error_output = f"STDERR: {result.stderr}\n"
        print(error_output)
        log_file.write(error_output)
    log_file.flush()

    # Check for actual test success/failure in output
    if "TEST PASSED" in result.stdout:
        return True
    if "TEST FAILED" in result.stdout:
        return False
    # Fallback to return code if no clear indicator
    print("⚠️  WARNING: Could not determine test result from output, using exit code")
    return result.returncode == 0


def main():
    """Run all full API tests with safety checks."""
    # Create temp log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"/tmp/worldarchitect_full_api_tests_{timestamp}.log"

    with open(log_filename, "w") as log_file:

        def tee_print(msg=""):
            """Print to both stdout and log file."""
            print(msg)
            log_file.write(msg + "\n")
            log_file.flush()

        tee_print("🌐 WorldArchitect.AI FULL API Test Suite")
        tee_print("⚠️  WARNING: These tests use REAL APIs!")
        tee_print("=" * 40)
        tee_print(f"\n📝 Logging to: {log_filename}")

        # Validate configuration first
        if not validate_config():
            tee_print("\n❌ Please fix configuration errors before running tests.")
            return 1

        tee_print("\n💰 Cost Estimates:")
        tee_print("  - Per test: ~$0.001-0.002")
        tee_print(
            f"  - Total ({len(TEST_FILES)} tests): ~${len(TEST_FILES) * 0.0015:.3f}"
        )

        # Safety confirmation
        tee_print("\n⚠️  These tests will:")
        tee_print("  1. Make real Gemini API calls")
        tee_print("  2. Create real Firebase data")
        tee_print("  3. Cost actual money")

        response = input("\nProceed with ALL tests? (y/n): ")
        tee_print(f"\nProceed with ALL tests? (y/n): {response}")
        if response.lower() != "y":
            tee_print("Tests cancelled.")
            return 0

        # Change to test directory
        test_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(test_dir)

        # Track results
        results = {}
        start_time = time.time()
        total_cost_estimate = 0

        # Run each test
        for test_file in TEST_FILES:
            if os.path.exists(test_file):
                success = run_test(test_file, log_file)
                results[test_file] = success

                # Rough cost estimate
                total_cost_estimate += 0.0015

                # Stop if cost gets too high
                if total_cost_estimate > 0.10:
                    tee_print("\n💸 Cost limit approaching, stopping tests")
                    break

                time.sleep(2)  # Pause between tests
            else:
                tee_print(f"⚠️ Test file not found: {test_file}")
                results[test_file] = False

        # Summary
        elapsed = time.time() - start_time
        passed = sum(1 for v in results.values() if v)
        total = len(results)

        tee_print(f"\n{'=' * 70}")
        tee_print("📊 FULL API TEST SUMMARY")
        tee_print(f"{'=' * 70}")

        for test, success in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            tee_print(f"{status} {test}")

        tee_print(f"\nTotal: {passed}/{total} passed ({passed / total * 100:.1f}%)")
        tee_print(f"Time: {elapsed:.2f} seconds")
        tee_print(f"Estimated cost: ~${total_cost_estimate:.3f}")

        # Overall result
        if passed == total:
            tee_print("\n🎉 ALL TESTS PASSED!")
            result_code = 0
        else:
            tee_print(f"\n❌ {total - passed} tests failed")
            result_code = 1

        tee_print(f"\n📄 Full test log saved to: {log_filename}")
        tee_print("=" * 70)

        # Print summary at the end
        print("\n🗂️  TEST RUN COMPLETE")
        print(f"📄 Log file: {log_filename}")
        print(f"📊 Result: {passed}/{total} tests passed")
        print(f"💰 Estimated cost: ~${total_cost_estimate:.3f}")

        return result_code


if __name__ == "__main__":
    sys.exit(main())
