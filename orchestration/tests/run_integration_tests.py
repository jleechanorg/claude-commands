#!/usr/bin/env python3
"""
Orchestration Integration Test Runner

Runs the integration tests that specifically target the stale task queue bug
and related orchestration reliability issues.

Usage:
    python3 run_integration_tests.py                  # All integration tests
    python3 run_integration_tests.py --stale-only     # Only stale task prevention tests
    python3 run_integration_tests.py --lifecycle-only # Only lifecycle tests
    python3 run_integration_tests.py --verbose        # Verbose output
"""

import sys
import unittest
import argparse
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import test modules
import test_stale_task_prevention
import test_prompt_file_lifecycle
import test_task_execution_verification
import test_tmux_session_lifecycle


def create_test_suite(test_type='all'):
    """Create test suite based on requested test type."""
    suite = unittest.TestSuite()

    if test_type in ['all', 'stale']:
        # Add stale task prevention tests
        suite.addTest(unittest.makeSuite(test_stale_task_prevention.TestStaleTaskPrevention))
        suite.addTest(unittest.makeSuite(test_stale_task_prevention.TestTaskDispatcherCleanup))

    if test_type in ['all', 'lifecycle']:
        # Add lifecycle management tests
        suite.addTest(unittest.makeSuite(test_prompt_file_lifecycle.TestPromptFileLifecycle))
        suite.addTest(unittest.makeSuite(test_prompt_file_lifecycle.TestPromptFileIntegration))
        suite.addTest(unittest.makeSuite(test_tmux_session_lifecycle.TestTmuxSessionLifecycle))

    if test_type in ['all', 'verification']:
        # Add task execution verification tests
        suite.addTest(unittest.makeSuite(test_task_execution_verification.TestTaskExecutionVerification))
        suite.addTest(unittest.makeSuite(test_task_execution_verification.TestTaskTraceability))

    return suite


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description='Run orchestration integration tests')
    parser.add_argument('--stale-only', action='store_true',
                      help='Run only stale task prevention tests')
    parser.add_argument('--lifecycle-only', action='store_true',
                      help='Run only lifecycle management tests')
    parser.add_argument('--verification-only', action='store_true',
                      help='Run only task execution verification tests')
    parser.add_argument('--verbose', '-v', action='store_true',
                      help='Verbose output')
    parser.add_argument('--list', action='store_true',
                      help='List available test categories')

    args = parser.parse_args()

    if args.list:
        print("Available test categories:")
        print("  all           - All integration tests (default)")
        print("  stale         - Stale task prevention tests")
        print("  lifecycle     - Lifecycle management tests (prompt files, tmux sessions)")
        print("  verification  - Task execution verification tests")
        print("\nUsage examples:")
        print("  python3 run_integration_tests.py")
        print("  python3 run_integration_tests.py --stale-only")
        print("  python3 run_integration_tests.py --lifecycle-only --verbose")
        return 0

    # Determine test type
    test_type = 'all'
    if args.stale_only:
        test_type = 'stale'
    elif args.lifecycle_only:
        test_type = 'lifecycle'
    elif args.verification_only:
        test_type = 'verification'

    # Create and run test suite
    suite = create_test_suite(test_type)

    verbosity = 2 if args.verbose else 1
    runner = unittest.TextTestRunner(verbosity=verbosity)

    print(f"\n🧪 Running {test_type} integration tests...")
    print("=" * 60)

    result = runner.run(suite)

    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("✅ All integration tests passed!")
        print(f"Ran {result.testsRun} tests successfully")
    else:
        print(f"❌ {len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
        print(f"Ran {result.testsRun} tests total")

        if result.failures:
            print("\nFailures:")
            for test, trace in result.failures:
                print(f"  - {test}: {trace.split(chr(10))[0]}")

        if result.errors:
            print("\nErrors:")
            for test, trace in result.errors:
                print(f"  - {test}: {trace.split(chr(10))[0]}")

    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())
