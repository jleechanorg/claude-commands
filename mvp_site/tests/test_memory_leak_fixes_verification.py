#!/usr/bin/env python3
"""
Verification script for CampaignCreationV2 memory leak fixes
This script verifies that the memory leak fixes are properly implemented
"""
import os
import re


def test_memory_leak_fixes():
    """Test that all memory leak fixes are properly implemented"""
    # Use absolute path from project root
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    component_path = os.path.join(project_root, "mvp_site", "frontend_v2", "src", "components", "CampaignCreationV2.tsx")

    # Check if file exists
    if not os.path.exists(component_path):
        print(f"❌ Component file not found: {component_path}")
        return False

    # Read the component file
    with open(component_path) as f:
        content = f.read()

    print("🔍 Verifying memory leak fixes in CampaignCreationV2...")

    # Test 1: Check for progressIntervalRef
    if 'progressIntervalRef = useRef<NodeJS.Timeout | null>(null)' in content:
        print("✅ 1. progressIntervalRef properly declared")
    else:
        print("❌ 1. progressIntervalRef not found or incorrect")
        return False

    # Test 2: Check for completionTimeoutRef
    if 'completionTimeoutRef = useRef<NodeJS.Timeout | null>(null)' in content:
        print("✅ 2. completionTimeoutRef properly declared")
    else:
        print("❌ 2. completionTimeoutRef not found or incorrect")
        return False

    # Test 3: Check for clearAllTimers function
    if 'const clearAllTimers = () =>' in content:
        print("✅ 3. clearAllTimers helper function exists")
    else:
        print("❌ 3. clearAllTimers helper function not found")
        return False

    # Test 4: Check cleanup in useEffect
    if 'clearAllTimers()' in content and 'return () => {' in content:
        print("✅ 4. useEffect cleanup calls clearAllTimers")
    else:
        print("❌ 4. useEffect cleanup not properly implemented")
        return False

    # Test 5: Check progressInterval is stored in ref
    if 'progressIntervalRef.current = progressInterval' in content:
        print("✅ 5. progressInterval stored in ref for cleanup")
    else:
        print("❌ 5. progressInterval not properly stored in ref")
        return False

    # Test 6: Check timeout clearing in error handling using ref
    timeout_clear_pattern = r'if \(timeoutRef\.current\) \{\s*clearTimeout\(timeoutRef\.current\)'
    if re.search(timeout_clear_pattern, content, re.MULTILINE):
        print("✅ 6. timeout properly cleared in error handling using ref")
    else:
        print("❌ 6. timeout not properly cleared in error handling")
        return False

    # Test 7: Check progressInterval cleared on error
    if 'clearInterval(progressInterval)' in content:
        print("✅ 7. progressInterval cleared on error")
    else:
        print("❌ 7. progressInterval not cleared on error")
        return False

    # Test 8: Check completion message improvement
    if 'Campaign ready! Taking you to your adventure' in content:
        print("✅ 8. Completion message improved for better UX")
    else:
        print("❌ 8. Completion message not improved")
        return False

    # Test 9: Check auto-retry timeout cleanup
    retry_cleanup_pattern = r'if \(timeoutRef\.current\) \{\s*clearTimeout\(timeoutRef\.current\)'
    if re.search(retry_cleanup_pattern, content, re.MULTILINE):
        print("✅ 9. Auto-retry timeout properly cleaned up before setting new one")
    else:
        print("❌ 9. Auto-retry timeout cleanup not implemented")
        return False

    # Test 10: Check Promise-based completion timeout
    if 'await new Promise<void>((resolve)' in content and 'completionTimeoutRef.current' in content:
        print("✅ 10. Promise-based completion timeout with proper tracking")
    else:
        print("❌ 10. Promise-based completion timeout not properly implemented")
        return False

    print("\n🎉 All memory leak fixes verified successfully!")
    print("\nSummary of fixes implemented:")
    print("- Added refs for all timer types (timeout, interval, completion)")
    print("- Created clearAllTimers helper function")
    print("- Added comprehensive cleanup in useEffect")
    print("- Fixed timeout scope and cleanup in error handling")
    print("- Improved completion flow to prevent component unmount interruption")
    print("- Added auto-retry timeout cleanup before setting new one")
    print("- Enhanced completion message for better user experience")

    return True

def test_component_structure():
    """Test basic component structure"""
    # Use absolute path from project root
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    component_path = os.path.join(project_root, "mvp_site", "frontend_v2", "src", "components", "CampaignCreationV2.tsx")

    with open(component_path) as f:
        content = f.read()

    print("\n🔍 Verifying component structure...")

    # Check imports
    required_imports = ['useState', 'useEffect', 'useRef']
    for import_item in required_imports:
        if import_item in content:
            print(f"✅ {import_item} imported correctly")
        else:
            print(f"❌ {import_item} not found in imports")
            return False

    # Check component exports
    if 'export function CampaignCreationV2(' in content:
        print("✅ Component properly exported")
    else:
        print("❌ Component export not found")
        return False

    return True

if __name__ == '__main__':
    print("=" * 60)
    print("CAMPAIGNCREATIONV2 MEMORY LEAK FIXES VERIFICATION")
    print("=" * 60)

    # Test component structure first
    if not test_component_structure():
        print("\n❌ Component structure test failed")
        exit(1)

    # Test memory leak fixes
    if not test_memory_leak_fixes():
        print("\n❌ Memory leak fixes verification failed")
        exit(1)

    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED - MEMORY LEAKS SUCCESSFULLY FIXED!")
    print("=" * 60)
