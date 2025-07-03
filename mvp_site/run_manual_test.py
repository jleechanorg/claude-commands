#!/usr/bin/env python3
"""
Runner script for manual tests that ensures proper Python path setup.

Usage:
    python run_manual_test.py tests/manual_tests/test_sariel_exact_production.py
"""
import sys
import os
import importlib.util
import argparse

def run_manual_test(test_path):
    """Run a manual test with proper path setup."""
    # Ensure mvp_site is in Python path
    mvp_site_dir = os.path.dirname(os.path.abspath(__file__))
    if mvp_site_dir not in sys.path:
        sys.path.insert(0, mvp_site_dir)
    
    # Get absolute path to test file
    test_file = os.path.abspath(test_path)
    if not os.path.exists(test_file):
        print(f"Error: Test file not found: {test_file}")
        sys.exit(1)
    
    # Extract module name from file path
    module_name = os.path.splitext(os.path.basename(test_file))[0]
    
    # Load and execute the test module
    spec = importlib.util.spec_from_file_location(module_name, test_file)
    module = importlib.util.module_from_spec(spec)
    
    # Add the module's directory to sys.path for any relative imports
    test_dir = os.path.dirname(test_file)
    if test_dir not in sys.path:
        sys.path.insert(0, test_dir)
    
    # Execute the module
    print(f"Running manual test: {test_path}")
    print("="*60)
    spec.loader.exec_module(module)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run manual tests with proper path setup')
    parser.add_argument('test_file', help='Path to the test file to run')
    args = parser.parse_args()
    
    run_manual_test(args.test_file)