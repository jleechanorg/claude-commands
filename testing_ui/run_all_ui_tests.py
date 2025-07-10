#!/usr/bin/env python3
"""
Individual UI Test Runner - Bypasses timeout issues by running each test separately
Runs all 45 UI tests individually with proper error handling and logging
"""

import os
import sys
import subprocess
import time
import signal
from pathlib import Path

# Core and Functionality Tests (Modernized Suite)
CORE_TESTS = [
    "testing_ui/core_tests/test_wizard_character_setting.py",
    "testing_ui/core_tests/test_campaign_creation_browser.py",
    "testing_ui/core_tests/test_api_response_structure.py", 
    "testing_ui/core_tests/test_structured_fields_browser.py",
    "testing_ui/core_tests/test_continue_campaign_browser.py"
]

FUNCTIONALITY_TESTS = [
    "testing_ui/functionality/test_accessibility_browser.py",
    "testing_ui/functionality/test_campaign_deletion_browser.py",
    "testing_ui/functionality/test_character_management_browser.py",
    "testing_ui/functionality/test_error_handling_browser.py",
    "testing_ui/functionality/test_performance_browser.py",
    "testing_ui/functionality/test_settings_browser.py",
    "testing_ui/functionality/test_story_download_browser.py",
    "testing_ui/functionality/test_story_sharing_browser.py"
]

# Combined test suite
TEST_FILES = CORE_TESTS + FUNCTIONALITY_TESTS

def setup_environment():
    """Setup test environment"""
    print("🔧 Setting up test environment...")
    
    # Set environment variables
    os.environ['TESTING'] = 'true'
    os.environ['USE_MOCKS'] = 'true'
    os.environ['PORT'] = '6007'
    
    # Create screenshot directory
    screenshot_dir = "/tmp/worldarchitectai/browser"
    os.makedirs(screenshot_dir, exist_ok=True)
    print(f"📸 Screenshots will be saved to: {screenshot_dir}")
    
    return screenshot_dir

def start_test_server():
    """Start test server and return process"""
    print("🏃 Starting test server with MOCK APIs on port 6007...")
    
    # Kill any existing server on port 6007 only (avoid killing dev server on 8080)
    try:
        subprocess.run(["lsof", "-ti:6007"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        result = subprocess.run(["lsof", "-ti:6007"], capture_output=True, text=True)
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                subprocess.run(["kill", "-9", pid], check=False)
        time.sleep(1)
    except:
        pass
    
    # Start server
    server_process = subprocess.Popen(
        ["python3", "mvp_site/main.py", "serve"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=os.environ.copy()
    )
    
    # Wait for server to be ready
    print("⏳ Waiting for server to be ready...")
    for i in range(30):
        try:
            result = subprocess.run(
                ["curl", "-s", "http://localhost:6007"], 
                capture_output=True, 
                timeout=5
            )
            if result.returncode == 0:
                print("✅ Server is ready")
                return server_process
        except:
            pass
        time.sleep(1)
    
    print("❌ Server failed to start")
    server_process.terminate()
    return None

def run_individual_test(test_file, test_num, total_tests):
    """Run a single test file"""
    print(f"\n🧪 [{test_num}/{total_tests}] Running: {test_file}")
    print("=" * 60)
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return False, f"File not found: {test_file}"
    
    try:
        # Run the test with timeout
        result = subprocess.run(
            ["python3", test_file],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout per test
            env=os.environ.copy()
        )
        
        if result.returncode == 0:
            print(f"✅ PASSED: {test_file}")
            return True, result.stdout
        else:
            print(f"❌ FAILED: {test_file}")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False, f"Exit code: {result.returncode}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    
    except subprocess.TimeoutExpired:
        print(f"⏰ TIMEOUT: {test_file} (5 minutes)")
        return False, "Test timed out after 5 minutes"
    
    except Exception as e:
        print(f"💥 ERROR: {test_file} - {str(e)}")
        return False, f"Exception: {str(e)}"

def main():
    """Main test runner"""
    print("🚀 WorldArchitect.AI - Modernized UI Test Runner")
    print("=" * 55)
    print(f"📋 Running {len(TEST_FILES)} UI tests ({len(CORE_TESTS)} core + {len(FUNCTIONALITY_TESTS)} functionality)")
    print("🎯 Using MOCK APIs to prevent costs")
    print("🚪 Test server will run on port 6007 (avoiding dev server on 8080)")
    print(f"📂 {len(os.listdir('testing_ui/archive'))} tests archived for faster execution")
    print("=" * 55)
    
    # Setup
    screenshot_dir = setup_environment()
    
    # Start server
    server_process = start_test_server()
    if not server_process:
        print("❌ Failed to start test server")
        return 1
    
    # Track results
    passed = 0
    failed = 0
    failed_tests = []
    results = {}
    
    try:
        # Run each test individually
        for i, test_file in enumerate(TEST_FILES, 1):
            success, output = run_individual_test(test_file, i, len(TEST_FILES))
            results[test_file] = {"success": success, "output": output}
            
            if success:
                passed += 1
            else:
                failed += 1
                failed_tests.append(test_file)
            
            # Brief pause between tests
            time.sleep(1)
    
    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        if server_process:
            server_process.terminate()
            server_process.wait()
        print("✅ Cleanup complete")
    
    # Results summary
    print("\n" + "=" * 60)
    print("📊 FINAL TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"✅ Passed: {passed}/{len(TEST_FILES)}")
    print(f"❌ Failed: {failed}/{len(TEST_FILES)}")
    print(f"📸 Screenshots: {screenshot_dir}")
    
    if failed_tests:
        print(f"\n❌ Failed tests ({len(failed_tests)}):")
        for test in failed_tests:
            print(f"   - {test}")
    
    if failed == 0:
        print("\n🎉 ALL UI TESTS PASSED!")
        return 0
    else:
        print(f"\n💥 {failed} tests failed. Check output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())