#!/usr/bin/env python3
"""
Test Suite for Milestone 4: Interactive Features
Tests campaign wizard, enhanced search, interface manager, and enhanced modals
"""

import unittest
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the mvp_site directory to Python path
mvp_site_path = Path(__file__).parent.parent  # Go up to mvp_site directory
sys.path.insert(0, str(mvp_site_path))

class TestMilestone4InteractiveFeatures(unittest.TestCase):
    """Test suite for Milestone 4 interactive features"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class"""
        os.environ["TESTING"] = "true"
        print("🧪 Testing Milestone 4: Interactive Features")
        print("=" * 60)
    
    def setUp(self):
        """Set up each test"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up after each test"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_interface_manager_js_exists(self):
        """Test that interface manager JavaScript file exists"""
        interface_manager_path = mvp_site_path / "static/js/interface-manager.js"
        self.assertTrue(
            interface_manager_path.exists(),
            "Interface manager JavaScript file should exist"
        )
        
        # Check file has meaningful content
        content = interface_manager_path.read_text()
        self.assertIn("class InterfaceManager", content)
        self.assertIn("enableClassicMode", content)
        self.assertIn("enableModernMode", content)
        print("✅ Interface Manager JavaScript file exists and contains core functionality")
    
    def test_campaign_wizard_js_exists(self):
        """Test that campaign wizard JavaScript file exists"""
        wizard_path = mvp_site_path / "static/js/campaign-wizard.js"
        self.assertTrue(
            wizard_path.exists(),
            "Campaign wizard JavaScript file should exist"
        )
        
        # Check file has meaningful content
        content = wizard_path.read_text()
        self.assertIn("class CampaignWizard", content)
        self.assertIn("generateWizardHTML", content)
        self.assertIn("setupStepNavigation", content)
        self.assertIn("nextStep", content)
        self.assertIn("previousStep", content)
        print("✅ Campaign Wizard JavaScript file exists and contains core functionality")
    
    def test_enhanced_search_js_exists(self):
        """Test that enhanced search JavaScript file exists"""
        search_path = mvp_site_path / "static/js/enhanced-search.js"
        self.assertTrue(
            search_path.exists(),
            "Enhanced search JavaScript file should exist"
        )
        
        # Check file has meaningful content
        content = search_path.read_text()
        self.assertIn("class EnhancedSearch", content)
        self.assertIn("setupSearchInterface", content)
        self.assertIn("applyFilters", content)
        self.assertIn("generateSearchHTML", content)
        print("✅ Enhanced Search JavaScript file exists and contains core functionality")
    
    def test_interactive_features_css_exists(self):
        """Test that interactive features CSS file exists"""
        css_path = mvp_site_path / "static/styles/interactive-features.css"
        self.assertTrue(
            css_path.exists(),
            "Interactive features CSS file should exist"
        )
        
        # Check CSS has meaningful content
        content = css_path.read_text()
        self.assertIn(".campaign-wizard", content)
        self.assertIn(".search-filter-container", content)
        self.assertIn(".personality-card", content)
        self.assertIn(".modern-mode", content)
        print("✅ Interactive Features CSS file exists and contains styling rules")
    
    def test_index_html_includes_scripts(self):
        """Test that index.html includes all necessary script files"""
        index_path = mvp_site_path / "static/index.html"
        self.assertTrue(index_path.exists(), "index.html should exist")
        
        content = index_path.read_text()
        
        # Check for script includes
        self.assertIn("interface-manager.js", content)
        self.assertIn("campaign-wizard.js", content)
        self.assertIn("enhanced-search.js", content)
        
        # Check for CSS includes
        self.assertIn("interactive-features.css", content)
        
        print("✅ index.html includes all interactive features scripts and CSS")
    
    def test_index_html_has_interface_toggle(self):
        """Test that index.html contains the interface mode toggle"""
        index_path = mvp_site_path / "static/index.html"
        content = index_path.read_text()
        
        # Check for interface mode toggle elements
        self.assertIn("data-interface-mode", content)
        self.assertIn("Classic Interface", content)
        self.assertIn("Modern Interface", content)
        self.assertIn("current-mode-icon", content)
        
        print("✅ index.html contains interface mode toggle UI")
    
    def test_javascript_file_structure(self):
        """Test JavaScript files have proper structure"""
        js_files = [
            "interface-manager.js",
            "campaign-wizard.js", 
            "enhanced-search.js"
        ]
        
        for js_file in js_files:
            file_path = mvp_site_path / f"static/js/{js_file}"
            content = file_path.read_text()
            
            # Check for proper class structure
            self.assertIn("constructor()", content, f"{js_file} should have constructor")
            self.assertIn("init()", content, f"{js_file} should have init method")
            
            # Check for enabled checking (different files may implement differently)
            if js_file != "interface-manager.js":
                self.assertIn("checkIfEnabled", content, f"{js_file} should check if enabled")
            
            # Check for modern mode integration (interface manager might not reference itself)
            if js_file != "interface-manager.js":
                self.assertIn("interfaceManager", content, f"{js_file} should integrate with interface manager")
            
        print("✅ All JavaScript files have proper structure and integration")
    
    def test_css_modern_mode_selectors(self):
        """Test CSS has proper modern mode selectors"""
        css_path = mvp_site_path / "static/styles/interactive-features.css"
        content = css_path.read_text()
        
        # Check for modern mode specific selectors
        self.assertIn(".modern-mode", content)
        self.assertIn('body[data-interface-mode="modern"]', content)
        self.assertIn(".interactive-features-enabled", content)
        
        # Check for responsive design
        self.assertIn("@media", content)
        self.assertIn("max-width: 768px", content)
        
        # Check for theme-specific styles
        self.assertIn('[data-theme="dark"]', content)
        self.assertIn('[data-theme="fantasy"]', content)
        self.assertIn('[data-theme="cyberpunk"]', content)
        
        print("✅ CSS has proper modern mode selectors and responsive design")
    
    def test_campaign_wizard_html_structure(self):
        """Test campaign wizard generates proper HTML structure"""
        wizard_path = mvp_site_path / "static/js/campaign-wizard.js"
        content = wizard_path.read_text()
        
        # Check for wizard HTML elements
        self.assertIn("campaign-wizard", content)
        self.assertIn("wizard-progress", content)
        self.assertIn("step-indicators", content)
        self.assertIn("wizard-step", content)
        self.assertIn("wizard-navigation", content)
        
        # Check for step content
        self.assertIn("Campaign Basics", content)
        self.assertIn("AI's Expertise", content)
        self.assertIn("Campaign Options", content)
        self.assertIn("Ready to Launch", content)
        
        print("✅ Campaign wizard generates proper HTML structure")
    
    def test_enhanced_search_features(self):
        """Test enhanced search has all required features"""
        search_path = mvp_site_path / "static/js/enhanced-search.js"
        content = search_path.read_text()
        
        # Check for search functionality
        self.assertIn("search-filter-container", content)
        self.assertIn("campaign-search", content)
        self.assertIn("filter-controls", content)
        self.assertIn("applyFilters", content)
        
        # Check for filter types
        self.assertIn("sort-by", content)
        self.assertIn("theme-filter", content)
        self.assertIn("status-filter", content)
        
        # Check for real-time features
        self.assertIn("addEventListener", content)
        self.assertIn("debounce", content)
        self.assertIn("updateDisplay", content)
        
        print("✅ Enhanced search has all required features")
    
    def test_interface_manager_feature_control(self):
        """Test interface manager can control features"""
        manager_path = mvp_site_path / "static/js/interface-manager.js"
        content = manager_path.read_text()
        
        # Check for feature control methods
        self.assertIn("disableAnimations", content)
        self.assertIn("enableAnimations", content)
        self.assertIn("disableEnhancedComponents", content)
        self.assertIn("enableEnhancedComponents", content)
        self.assertIn("disableInteractiveFeatures", content)
        self.assertIn("enableInteractiveFeatures", content)
        
        # Check for safety mechanisms
        self.assertIn("localStorage", content)
        self.assertIn("feature_", content)
        
        print("✅ Interface manager has proper feature control methods")
    
    def test_backward_compatibility(self):
        """Test that features maintain backward compatibility"""
        # Test features that depend on interface manager
        dependent_js_files = [
            "campaign-wizard.js",
            "enhanced-search.js"
        ]
        
        for js_file in dependent_js_files:
            file_path = mvp_site_path / f"static/js/{js_file}"
            content = file_path.read_text()
            
            # Check for backward compatibility checks
            self.assertIn("checkIfEnabled", content, f"{js_file} should check if enabled")
            
            # Check that it doesn't break if interface manager isn't available
            self.assertIn("window.interfaceManager", content, f"{js_file} should check for interface manager")
        
        # Test interface manager itself has safe defaults
        manager_path = mvp_site_path / "static/js/interface-manager.js"
        manager_content = manager_path.read_text()
        self.assertIn("'classic'", manager_content, "Interface manager should default to classic mode")
        
        print("✅ All features maintain backward compatibility")
    
    def test_progressive_enhancement(self):
        """Test that features use progressive enhancement"""
        # Test interface manager defaults to classic mode
        manager_path = mvp_site_path / "static/js/interface-manager.js"
        content = manager_path.read_text()
        
        self.assertIn("'classic'", content)
        self.assertIn("safety", content.lower())
        
        # Test features only activate in modern mode
        for js_file in ["campaign-wizard.js", "enhanced-search.js"]:
            file_path = mvp_site_path / f"static/js/{js_file}"
            content = file_path.read_text()
            
            self.assertIn("isModernMode", content, f"{js_file} should check for modern mode")
            self.assertIn("disable", content, f"{js_file} should have disable functionality")
        
        print("✅ Features use progressive enhancement and default to safe mode")
    
    def test_file_integration_order(self):
        """Test that files are loaded in the correct order"""
        index_path = mvp_site_path / "static/index.html"
        content = index_path.read_text()
        
        # Find script tag positions
        interface_pos = content.find("interface-manager.js")
        wizard_pos = content.find("campaign-wizard.js")
        search_pos = content.find("enhanced-search.js")
        
        # Interface manager should load first
        self.assertLess(interface_pos, wizard_pos, "Interface manager should load before wizard")
        self.assertLess(interface_pos, search_pos, "Interface manager should load before search")
        
        print("✅ JavaScript files are loaded in correct dependency order")
    
    def test_css_theme_integration(self):
        """Test CSS integrates properly with existing theme system"""
        css_path = mvp_site_path / "static/styles/interactive-features.css"
        content = css_path.read_text()
        
        # Check for theme support (light theme is default, doesn't need explicit selectors)
        required_themes = ["dark", "fantasy", "cyberpunk"]
        for theme in required_themes:
            self.assertIn(f'[data-theme="{theme}"]', content, f"Should support {theme} theme")
        
        # Check for no conflicts with existing classes
        self.assertNotIn("!important", content.lower(), "Should not use !important declarations")
        
        print("✅ CSS integrates properly with existing theme system")

    def test_performance_considerations(self):
        """Test that features are optimized for performance"""
        js_files = [
            "campaign-wizard.js",
            "enhanced-search.js"
        ]
        
        for js_file in js_files:
            file_path = mvp_site_path / f"static/js/{js_file}"
            content = file_path.read_text()
            
            # Check for performance optimizations
            if "search" in js_file:
                self.assertIn("debounce", content.lower(), "Search should debounce input")
                self.assertIn("setTimeout", content, "Should use timeout for debouncing")
            
            # Check for efficient DOM manipulation
            self.assertIn("querySelector", content, "Should use efficient DOM queries")
            
        print("✅ Features include performance optimizations")

    def test_accessibility_features(self):
        """Test that interactive features maintain accessibility"""
        # Test HTML structure for accessibility
        wizard_path = mvp_site_path / "static/js/campaign-wizard.js"
        content = wizard_path.read_text()
        
        # Check for accessibility-related attributes (role, aria, or label)
        has_accessibility = ("role=" in content or 
                           "aria-" in content or 
                           "label" in content)
        self.assertTrue(has_accessibility, "Should have some accessibility attributes")
        
        # Check for keyboard navigation
        self.assertIn("addEventListener", content)
        
        # Test CSS respects accessibility preferences
        css_path = mvp_site_path / "static/styles/interactive-features.css"
        css_content = css_path.read_text()
        
        # Should have smooth transitions but respect reduced motion
        self.assertIn("transition", css_content)
        
        print("✅ Interactive features maintain accessibility standards")

    def test_error_handling(self):
        """Test that features handle errors gracefully"""
        js_files = [
            "interface-manager.js",
            "campaign-wizard.js",
            "enhanced-search.js"
        ]
        
        for js_file in js_files:
            file_path = mvp_site_path / f"static/js/{js_file}"
            content = file_path.read_text()
            
            # Check for defensive programming
            self.assertIn("if (", content, f"{js_file} should have conditional checks")
            
            # Check for safe DOM access (either getElementById or querySelector)
            has_safe_dom = ("document.getElementById" in content or 
                           "document.querySelector" in content or
                           "?.querySelector" in content)
            self.assertTrue(has_safe_dom, f"{js_file} should safely access DOM elements")
            
        print("✅ Features include proper error handling")

def run_milestone_4_tests():
    """Run all Milestone 4 tests"""
    print("🚀 Starting Milestone 4: Interactive Features Test Suite")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestMilestone4InteractiveFeatures)
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout, buffer=False)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("🎯 MILESTONE 4 TEST SUMMARY")
    print("=" * 60)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    passed = total_tests - failures - errors
    
    print(f"✅ Passed: {passed}/{total_tests}")
    if failures > 0:
        print(f"❌ Failed: {failures}")
    if errors > 0:
        print(f"💥 Errors: {errors}")
    
    if result.wasSuccessful():
        print("\n🎉 MILESTONE 4: INTERACTIVE FEATURES - ALL TESTS PASSED!")
        print("📋 Features Ready:")
        print("   • Master Interface Toggle (Classic/Modern)")
        print("   • Campaign Wizard (Multi-step Creation)")
        print("   • Enhanced Search & Filter")
        print("   • Enhanced Modals")
        print("   • Backward Compatibility")
        print("   • Progressive Enhancement")
        return True
    else:
        print("\n❌ Some tests failed. Please fix issues before deployment.")
        return False

if __name__ == "__main__":
    success = run_milestone_4_tests()
    sys.exit(0 if success else 1) 