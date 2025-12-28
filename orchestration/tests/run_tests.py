#!/usr/bin/env python3
"""Test runner for orchestration system tests."""

import argparse
import os
import sys
import unittest
from unittest import TextTestRunner

# Add project root directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def run_specific_test(test_name):
    """Run a specific test module."""
    try:
        module = __import__(f"test_{test_name}")
        suite = unittest.TestLoader().loadTestsFromModule(module)
        runner = TextTestRunner(verbosity=2)
        result = runner.run(suite)
        return result.wasSuccessful()
    except ImportError:
        print(f"Test module 'test_{test_name}' not found")
        return False


def run_all_tests():
    """Run all orchestration tests."""
    # Discover and run all tests in the tests directory
    test_dir = os.path.dirname(__file__)
    loader = unittest.TestLoader()

    # Load all test modules
    suite = loader.discover(test_dir, pattern="test_*.py")

    # Run tests with detailed output
    runner = TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Run orchestration system tests")
    parser.add_argument(
        "test",
        nargs="?",
        help='Specific test to run (e.g., "unified" for test_orchestrate_unified.py)',
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--list", "-l", action="store_true", help="List available tests")

    args = parser.parse_args()

    if args.list:
        print("Available tests:")
        test_files = [f for f in os.listdir(".") if f.startswith("test_") and f.endswith(".py")]
        for test_file in test_files:
            test_name = test_file[5:-3]  # Remove 'test_' prefix and '.py' suffix
            print(f"  {test_name}")
        return

    print("🤖 Orchestration System Test Suite")
    print("=" * 50)

    if args.test:
        print(f"Running specific test: {args.test}")
        success = run_specific_test(args.test)
    else:
        print("Running all tests...")
        success = run_all_tests()

    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
