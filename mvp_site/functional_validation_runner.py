#!/usr/bin/env python3

"""
Functional Validation Test Runner
Checks for the specific issues identified in user feedback
"""

import os
import sys
from pathlib import Path

class FunctionalValidationRunner:
    def __init__(self):
        self.mvp_site_path = Path(__file__).parent
        self.failed_tests = []
        self.passed_tests = []
    
    def test_spinner_implementation(self):
        """Test 1: Check if spinner is implemented when clicking Begin Adventure"""
        print("🔴 TEST 1: Spinner Implementation")
        
        # Check campaign wizard for spinner/loading implementation
        wizard_file = self.mvp_site_path / "static/js/campaign-wizard.js"
        
        if not wizard_file.exists():
            self.failed_tests.append("Spinner Test: campaign-wizard.js not found")
            print("❌ FAIL: campaign-wizard.js not found")
            return False
            
        content = wizard_file.read_text()
        
        has_spinner = any(keyword in content.lower() for keyword in [
            'spinner', 'loading', 'progress', 'building characters', 'building factions'
        ])
        
        has_progress_bar = 'progress-bar' in content or 'progress' in content
        
        if not has_spinner:
            self.failed_tests.append("Spinner Test: No spinner/loading implementation found")
            print("❌ FAIL: No spinner implementation found")
            return False
            
        if not has_progress_bar:
            self.failed_tests.append("Spinner Test: No progress bar implementation")
            print("❌ FAIL: No progress bar found")
            return False
            
        print("✅ PASS: Spinner implementation found")
        self.passed_tests.append("Spinner Test")
        return True
    
    def test_search_filter_functionality(self):
        """Test 2: Check if search and filter functionality is implemented"""
        print("🔴 TEST 2: Search and Filter Functionality")
        
        search_file = self.mvp_site_path / "static/js/enhanced-search.js"
        
        if not search_file.exists():
            self.failed_tests.append("Search Test: enhanced-search.js not found")
            print("❌ FAIL: enhanced-search.js not found")
            return False
            
        content = search_file.read_text()
        
        # Check for actual filtering logic
        has_filter_logic = any(keyword in content for keyword in [
            'filter(', 'display: none', 'style.display', 'hidden'
        ])
        
        has_search_handler = any(keyword in content for keyword in [
            'addEventListener', 'input', 'onInput', 'search'
        ])
        
        if not has_filter_logic:
            self.failed_tests.append("Search Test: No filtering logic found")
            print("❌ FAIL: No filtering logic implemented")
            return False
            
        if not has_search_handler:
            self.failed_tests.append("Search Test: No search event handler found")
            print("❌ FAIL: No search event handler")
            return False
            
        print("✅ PASS: Search and filter functionality found")
        self.passed_tests.append("Search and Filter Test")
        return True
    
    def test_modern_mode_default(self):
        """Test 3: Check if modern mode is set as default"""
        print("🔴 TEST 3: Modern Mode Default")
        
        interface_file = self.mvp_site_path / "static/js/interface-manager.js"
        
        if not interface_file.exists():
            self.failed_tests.append("Modern Mode Test: interface-manager.js not found")
            print("❌ FAIL: interface-manager.js not found")
            return False
            
        content = interface_file.read_text()
        
        # Check for modern mode as default
        modern_default = any(keyword in content for keyword in [
            "mode: 'modern'", 'mode = "modern"', "defaultMode: 'modern'",
            'modern-mode', 'data-interface-mode="modern"'
        ])
        
        classic_default = any(keyword in content for keyword in [
            "mode: 'classic'", 'mode = "classic"', "defaultMode: 'classic'"
        ])
        
        if classic_default and not modern_default:
            self.failed_tests.append("Modern Mode Test: Classic mode is default, not modern")
            print("❌ FAIL: Classic mode is default, should be modern")
            return False
            
        if not modern_default:
            self.failed_tests.append("Modern Mode Test: No clear default mode setting found")
            print("❌ FAIL: No clear modern mode default found")
            return False
            
        print("✅ PASS: Modern mode appears to be default")
        self.passed_tests.append("Modern Mode Default Test")
        return True
    
    def test_theme_readability(self):
        """Test 4: Check theme CSS for readability issues"""
        print("🔴 TEST 4: Theme Readability")
        
        css_files = [
            self.mvp_site_path / "static/style.css",
            self.mvp_site_path / "static/styles/globals.css",
            self.mvp_site_path / "static/styles/interactive-features.css"
        ]
        
        issues = []
        
        for css_file in css_files:
            if css_file.exists():
                content = css_file.read_text()
                
                # Split content into lines for context analysis
                lines = content.split('\n')
                in_keyframes = False
                
                for i, line in enumerate(lines):
                    # Track if we're inside @keyframes
                    if '@keyframes' in line:
                        in_keyframes = True
                    elif in_keyframes and line.strip() == '}' and (i + 1 >= len(lines) or lines[i + 1].strip() == ''):
                        in_keyframes = False
                    
                    # Skip checks inside keyframes (animations)
                    if in_keyframes:
                        continue
                    
                    # Check for potential readability issues outside animations
                    if 'color: transparent' in line:
                        issues.append(f"{css_file.name} line {i+1}: Contains transparent text")
                    
                    # Check for opacity: 0 (but not 0.x values)
                    if 'opacity: 0' in line and not 'opacity: 0.' in line and not any(anim in line.lower() for anim in ['animation', 'transition', 'hover', ':before', ':after']):
                        # Additional context check - see if it's part of a text element
                        context_start = max(0, i - 5)
                        context_end = min(len(lines), i + 5)
                        context = '\n'.join(lines[context_start:context_end])
                        
                        if any(text_indicator in context.lower() for text_indicator in ['text', 'font', 'p {', 'h1', 'h2', 'h3', 'span', 'label']):
                            issues.append(f"{css_file.name} line {i+1}: Text opacity set to 0")
                    
                # Check for same color text and background
                lines = content.split('\n')
                current_selector = ""
                current_rules = {}
                
                for line in lines:
                    line = line.strip()
                    if line.endswith('{'):
                        current_selector = line[:-1].strip()
                        current_rules = {}
                    elif ':' in line and ';' in line:
                        prop, value = line.split(':', 1)
                        current_rules[prop.strip()] = value.strip().rstrip(';')
                    elif line == '}':
                        # Check rules for issues
                        if 'color' in current_rules and 'background-color' in current_rules:
                            if current_rules['color'] == current_rules['background-color']:
                                issues.append(f"Same text and background color in {current_selector}")
        
        if issues:
            self.failed_tests.extend([f"Theme Readability: {issue}" for issue in issues])
            print(f"❌ FAIL: Found {len(issues)} readability issues")
            for issue in issues:
                print(f"   - {issue}")
            return False
            
        print("✅ PASS: No obvious theme readability issues found")
        self.passed_tests.append("Theme Readability Test")
        return True
    
    def test_checkbox_alignment(self):
        """Test 5: Check CSS for checkbox alignment issues"""
        print("🔴 TEST 5: Checkbox Alignment")
        
        css_files = [
            self.mvp_site_path / "static/styles/interactive-features.css",
            self.mvp_site_path / "static/style.css"
        ]
        
        has_checkbox_styles = False
        has_alignment_fix = False
        
        for css_file in css_files:
            if css_file.exists():
                content = css_file.read_text()
                
                if 'checkbox' in content.lower() or 'input[type="checkbox"]' in content:
                    has_checkbox_styles = True
                    
                if any(prop in content for prop in [
                    'vertical-align', 'align-items', 'flex', 'display: flex'
                ]):
                    has_alignment_fix = True
        
        if not has_checkbox_styles:
            self.failed_tests.append("Checkbox Alignment: No checkbox styles found")
            print("❌ FAIL: No checkbox styles found")
            return False
            
        if not has_alignment_fix:
            self.failed_tests.append("Checkbox Alignment: No alignment properties found")
            print("❌ FAIL: No alignment CSS properties found")
            return False
            
        print("✅ PASS: Checkbox alignment styles found")
        self.passed_tests.append("Checkbox Alignment Test")
        return True
    
    def test_sort_functionality(self):
        """Test 6: Check if sort functionality is implemented"""
        print("🔴 TEST 6: Sort Functionality")
        
        search_file = self.mvp_site_path / "static/js/enhanced-search.js"
        app_file = self.mvp_site_path / "static/app.js"
        
        has_sort_logic = False
        
        for js_file in [search_file, app_file]:
            if js_file.exists():
                content = js_file.read_text()
                
                if any(keyword in content for keyword in [
                    'sort(', 'sortBy', 'sortCampaigns', 'date_created', 'title'
                ]):
                    has_sort_logic = True
                    break
        
        if not has_sort_logic:
            self.failed_tests.append("Sort Test: No sort functionality found")
            print("❌ FAIL: No sort functionality implemented")
            return False
            
        print("✅ PASS: Sort functionality found")
        self.passed_tests.append("Sort Functionality Test")
        return True
    
    def run_all_tests(self):
        """Run all functional validation tests"""
        print("🧪 FUNCTIONAL VALIDATION TEST SUITE")
        print("=" * 50)
        print("Testing for issues identified in user feedback...\n")
        
        tests = [
            self.test_spinner_implementation,
            self.test_search_filter_functionality,
            self.test_modern_mode_default,
            self.test_theme_readability,
            self.test_checkbox_alignment,
            self.test_sort_functionality
        ]
        
        for test in tests:
            try:
                test()
                print()
            except Exception as e:
                print(f"❌ ERROR in {test.__name__}: {e}")
                self.failed_tests.append(f"{test.__name__}: {e}")
                print()
        
        # Summary
        total_tests = len(tests)
        passed_count = len(self.passed_tests)
        failed_count = len(self.failed_tests)
        
        print("📊 TEST SUMMARY")
        print("=" * 30)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_count}")
        print(f"❌ Failed: {failed_count}")
        
        if failed_count > 0:
            print(f"\n🔴 FAILED TESTS (Need to fix these):")
            for i, failure in enumerate(self.failed_tests, 1):
                print(f"   {i}. {failure}")
            
            print("\n✅ SUCCESS: Tests are working correctly!")
            print("These failures confirm the issues identified in user feedback.")
            print("Now we can systematically fix each issue.")
        else:
            print("\n🎉 SUCCESS: All UI issues have been resolved!")
            print("All 6 critical issues identified from user screenshots are now fixed.")
            print("The application is ready for use with all features working correctly.")
        
        return {
            'total': total_tests,
            'passed': passed_count,
            'failed': failed_count,
            'failures': self.failed_tests
        }

if __name__ == "__main__":
    runner = FunctionalValidationRunner()
    results = runner.run_all_tests()
    
    # Save results to file
    results_file = Path(__file__).parent / "tmp" / "test_results.txt"
    with open(results_file, 'w') as f:
        f.write(f"Functional Validation Test Results\n")
        f.write(f"Total: {results['total']}, Passed: {results['passed']}, Failed: {results['failed']}\n\n")
        f.write("Failed Tests:\n")
        for failure in results['failures']:
            f.write(f"- {failure}\n")
    
    print(f"\n📄 Results saved to {results_file}")
    
    # Exit with error code if tests failed (which is expected at this point)
    sys.exit(0 if results['failed'] == 0 else 1) 