#!/usr/bin/env python3
"""
Run all REAL browser automation tests using Playwright.
These tests launch actual browsers and interact with the UI.
"""

import os
import sys
import subprocess
import time
from datetime import datetime

# Test files to run (only real browser tests)
BROWSER_TESTS = [
    "test_campaign_creation_browser.py",
    "test_campaign_creation_browser_v2.py",
    "test_continue_campaign_browser.py",
    "test_continue_campaign_browser_v2.py",
    "test_god_mode_browser.py",
    "test_real_browser.py",
    "test_playwright_sample.py",
    "test_playwright_mock.py"
]

def check_playwright_installed():
    """Check if Playwright is installed and set up."""
    try:
        import playwright
        return True
    except ImportError:
        print("❌ Playwright not installed!")
        print("Run: pip install playwright")
        print("Then: playwright install chromium")
        return False

def run_browser_test(test_file):
    """Run a single browser test file."""
    test_path = os.path.join(os.path.dirname(__file__), test_file)
    
    if not os.path.exists(test_path):
        print(f"⚠️  Test file not found: {test_file}")
        return False
    
    print(f"\n{'='*60}")
    print(f"🌐 Running: {test_file}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    # Run the test
    result = subprocess.run(
        [sys.executable, test_path],
        capture_output=True,
        text=True
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
    else:
        print(f"❌ FAILED ({duration:.2f}s)")
        return False

def main():
    """Run all browser tests."""
    # Check if we're using real APIs
    use_real_apis = os.environ.get('REAL_APIS', '').lower() in ['true', '1', 'yes']
    
    print("🚀 WorldArchitect.AI Browser Test Suite")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🌐 Testing with REAL browser automation (Playwright)")
    
    if use_real_apis:
        print("💰 Using REAL Firebase and Gemini APIs (costs money!)")
    else:
        print("🎭 Using MOCK APIs (free)")
    
    print("="*60)
    
    # Check prerequisites
    if not check_playwright_installed():
        sys.exit(1)
    
    # Check if test server is running
    import requests
    try:
        response = requests.get("http://localhost:6006", timeout=2)
        print("✅ Test server is running")
    except:
        print("⚠️  WARNING: Test server not responding at http://localhost:6006")
        print("   Start the test server with: TESTING=true python3 mvp_site/main.py")
        print("   Continuing anyway...")
    
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
    print("📊 Test Summary:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   ⚠️  Skipped: {skipped}")
    print(f"   📋 Total: {len(BROWSER_TESTS)}")
    print("="*60)
    
    # Overall result
    if failed == 0 and passed > 0:
        print("\n✅ ALL BROWSER TESTS PASSED!")
        return 0
    else:
        print(f"\n❌ BROWSER TESTS FAILED ({failed} failures)")
        return 1

if __name__ == "__main__":
    sys.exit(main())