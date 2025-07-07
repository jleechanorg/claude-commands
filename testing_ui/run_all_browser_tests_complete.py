#!/usr/bin/env python3
"""
Complete browser test runner for WorldArchitect.AI
Runs all browser tests and provides comprehensive reporting.
"""

import os
import sys
import subprocess
import time
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test modules
BROWSER_TESTS = [
    ("God Mode Test", "test_god_mode_browser.py"),
    # ("Campaign Creation Test", "test_campaign_creation_browser_v2.py"),  # Not in this PR 
    # ("Campaign Continuation Test", "test_continue_campaign_browser_v2.py"),  # Not in this PR
    ("Campaign Deletion Test", "test_campaign_deletion_browser.py"),
    ("Character/NPC Management Test", "test_character_npc_browser.py"),
    ("Combat System Test", "test_combat_system_browser.py"),
    ("Multi-Campaign Management Test", "test_multi_campaign_browser.py"),
    ("Error Handling Test", "test_error_handling_browser.py"),
    ("Settings Management Test", "test_settings_browser.py"),
    ("Search Functionality Test", "test_search_browser.py"),
    ("Performance Test", "test_performance_browser.py")
]

# Test categories
HIGH_PRIORITY = [0, 1, 2, 3, 4, 5, 6, 7]  # Indices of high priority tests
MEDIUM_PRIORITY = [8, 9, 10]  # Indices of medium priority tests

def run_test(test_name, test_file):
    """Run a single browser test and return results."""
    print(f"\n{'='*60}")
    print(f"🧪 Running: {test_name}")
    print(f"📄 File: {test_file}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        # Set up environment
        env = os.environ.copy()
        env['TESTING'] = 'true'
        
        # Run the test
        result = subprocess.run(
            ['python', f'testing_ui/{test_file}'],
            env=env,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout per test
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        success = result.returncode == 0
        
        return {
            'name': test_name,
            'file': test_file,
            'success': success,
            'duration': duration,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
        
    except subprocess.TimeoutExpired:
        end_time = time.time()
        duration = end_time - start_time
        
        return {
            'name': test_name,
            'file': test_file,
            'success': False,
            'duration': duration,
            'stdout': '',
            'stderr': 'Test timed out after 5 minutes',
            'returncode': -1
        }
        
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        
        return {
            'name': test_name,
            'file': test_file,
            'success': False,
            'duration': duration,
            'stdout': '',
            'stderr': f'Test execution failed: {str(e)}',
            'returncode': -2
        }

def print_summary(results):
    """Print a comprehensive test summary."""
    print(f"\n{'='*80}")
    print("🏁 BROWSER TEST SUITE SUMMARY")
    print(f"{'='*80}")
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r['success'])
    failed_tests = total_tests - passed_tests
    total_duration = sum(r['duration'] for r in results)
    
    print(f"📊 Total Tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"⏱️  Total Duration: {total_duration:.2f} seconds ({total_duration/60:.1f} minutes)")
    print(f"📅 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test results by category
    print(f"\n{'='*50}")
    print("📋 DETAILED RESULTS")
    print(f"{'='*50}")
    
    for i, result in enumerate(results):
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        category = "HIGH" if i in HIGH_PRIORITY else "MEDIUM" if i in MEDIUM_PRIORITY else "LOW"
        
        print(f"{status} [{category:6}] {result['name']:<35} ({result['duration']:.1f}s)")
        
        if not result['success']:
            print(f"    💥 Error: {result['stderr'][:100]}...")
    
    # Failed test details
    failed_results = [r for r in results if not r['success']]
    if failed_results:
        print(f"\n{'='*50}")
        print("❌ FAILED TEST DETAILS")
        print(f"{'='*50}")
        
        for result in failed_results:
            print(f"\n🔍 {result['name']}")
            print(f"   File: {result['file']}")
            print(f"   Duration: {result['duration']:.2f}s")
            print(f"   Return Code: {result['returncode']}")
            
            if result['stderr']:
                print(f"   Error Output:")
                print(f"   {result['stderr'][:500]}...")
            
            if result['stdout']:
                print(f"   Standard Output:")
                print(f"   {result['stdout'][-500:]}...")  # Last 500 chars
    
    # Success rate by category
    print(f"\n{'='*50}")
    print("📈 SUCCESS RATES BY CATEGORY")
    print(f"{'='*50}")
    
    categories = {
        'HIGH': HIGH_PRIORITY,
        'MEDIUM': MEDIUM_PRIORITY
    }
    
    for cat_name, indices in categories.items():
        cat_results = [results[i] for i in indices if i < len(results)]
        cat_total = len(cat_results)
        cat_passed = sum(1 for r in cat_results if r['success'])
        cat_rate = (cat_passed / cat_total * 100) if cat_total > 0 else 0
        
        print(f"{cat_name:8}: {cat_passed}/{cat_total} ({cat_rate:.1f}%)")
    
    print(f"\n📸 Screenshots saved to: /tmp/worldarchitectai/browser/")
    
    return passed_tests == total_tests

def main():
    """Main test runner function."""
    print("🚀 WorldArchitect.AI Complete Browser Test Suite")
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🧪 Total Tests: {len(BROWSER_TESTS)}")
    
    # Ensure screenshot directory exists
    screenshot_dir = "/tmp/worldarchitectai/browser"
    os.makedirs(screenshot_dir, exist_ok=True)
    
    # Run all tests
    results = []
    
    for i, (test_name, test_file) in enumerate(BROWSER_TESTS):
        result = run_test(test_name, test_file)
        results.append(result)
        
        # Print quick status
        status = "✅" if result['success'] else "❌"
        print(f"\n{status} {test_name} - {result['duration']:.1f}s")
        
        if not result['success']:
            print(f"   💥 {result['stderr'][:100]}...")
    
    # Print comprehensive summary
    all_passed = print_summary(results)
    
    # Exit with appropriate code
    if all_passed:
        print(f"\n🎉 ALL BROWSER TESTS PASSED! 🎉")
        sys.exit(0)
    else:
        print(f"\n💥 SOME BROWSER TESTS FAILED 💥")
        sys.exit(1)

if __name__ == "__main__":
    main()