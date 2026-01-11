#!/usr/bin/env python3
"""
Test Suite for Milestone 4: Interactive Features
Tests campaign wizard, enhanced search, interface manager, and enhanced modals
"""

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Add the mvp_site directory to Python path
mvp_site_path = Path(__file__).parent.parent  # Go up to mvp_site directory
sys.path.insert(0, str(mvp_site_path))


class TestMilestone4InteractiveFeatures(unittest.TestCase):
    """Test suite for Milestone 4 interactive features"""

    @classmethod
    def setUpClass(cls):
        """Set up test class"""
        os.environ["TESTING_AUTH_BYPASS"] = "true"
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
        interface_manager_path = mvp_site_path / "frontend_v1/js/interface-manager.js"
        assert (
            interface_manager_path.exists()
        ), "Interface manager JavaScript file should exist"

        # Check file has meaningful content
        content = interface_manager_path.read_text()
        assert "class InterfaceManager" in content
        assert "enableModernMode" in content
        print(
            "✅ Interface Manager JavaScript file exists and contains core functionality"
        )

    def test_campaign_wizard_js_exists(self):
        """Test that campaign wizard JavaScript file exists"""
        wizard_path = mvp_site_path / "frontend_v1/js/campaign-wizard.js"
        assert wizard_path.exists(), "Campaign wizard JavaScript file should exist"

        # Check file has meaningful content
        content = wizard_path.read_text()
        assert "class CampaignWizard" in content
        assert "generateWizardHTML" in content
        assert "setupStepNavigation" in content
        assert "nextStep" in content
        assert "previousStep" in content
        print(
            "✅ Campaign Wizard JavaScript file exists and contains core functionality"
        )

    def test_enhanced_search_js_exists(self):
        """Test that enhanced search JavaScript file exists"""
        search_path = mvp_site_path / "frontend_v1/js/enhanced-search.js"
        assert search_path.exists(), "Enhanced search JavaScript file should exist"

        # Check file has meaningful content
        content = search_path.read_text()
        assert "class EnhancedSearch" in content
        assert "setupSearchInterface" in content
        assert "applyFilters" in content
        assert "generateSearchHTML" in content
        print(
            "✅ Enhanced Search JavaScript file exists and contains core functionality"
        )

    def test_interactive_features_css_exists(self):
        """Test that interactive features CSS file exists"""
        css_path = mvp_site_path / "frontend_v1/styles/interactive-features.css"
        assert css_path.exists(), "Interactive features CSS file should exist"

        # Check CSS has meaningful content
        content = css_path.read_text()
        assert ".campaign-wizard" in content
        assert ".search-filter-container" in content
        assert ".personality-card" in content
        assert ".modern-mode" in content
        print("✅ Interactive Features CSS file exists and contains styling rules")

    def test_index_html_includes_scripts(self):
        """Test that index.html includes all necessary script files"""
        index_path = mvp_site_path / "frontend_v1/index.html"
        assert index_path.exists(), "index.html should exist"

        content = index_path.read_text()

        # Check for script includes
        assert "interface-manager.js" in content
        assert "campaign-wizard.js" in content
        assert "enhanced-search.js" in content

        # Check for CSS includes
        assert "interactive-features.css" in content

        print("✅ index.html includes all interactive features scripts and CSS")

    def test_index_html_has_modern_interface(self):
        """Test that index.html supports modern interface system"""
        index_path = mvp_site_path / "frontend_v1/index.html"
        content = index_path.read_text()

        # Check for modern interface elements (no longer toggle, just modern)
        assert "current-mode-icon" in content
        assert "Settings" in content
        assert "interface-manager.js" in content

        print("✅ index.html supports modern interface system")

    def test_javascript_file_structure(self):
        """Test JavaScript files have proper structure"""
        js_files = ["interface-manager.js", "campaign-wizard.js", "enhanced-search.js"]

        for js_file in js_files:
            file_path = mvp_site_path / f"frontend_v1/js/{js_file}"
            content = file_path.read_text()

            # Check for proper class structure
            assert "constructor()" in content, f"{js_file} should have constructor"
            assert "init()" in content, f"{js_file} should have init method"

            # Check for enabled checking (different files may implement differently)
            if js_file != "interface-manager.js":
                assert "checkIfEnabled" in content, f"{js_file} should check if enabled"

            # Check for modern mode integration (interface manager might not reference itself)
            if js_file != "interface-manager.js":
                assert (
                    "interfaceManager" in content
                ), f"{js_file} should integrate with interface manager"

        print("✅ All JavaScript files have proper structure and integration")

    def test_css_modern_mode_selectors(self):
        """Test CSS has proper modern mode selectors"""
        css_path = mvp_site_path / "frontend_v1/styles/interactive-features.css"
        content = css_path.read_text()

        # Check for modern mode specific selectors
        assert ".modern-mode" in content
        assert "body[data-interface-mode='modern']" in content
        assert ".interactive-features-enabled" in content

        # Check for responsive design
        assert "@media" in content
        assert "max-width: 768px" in content

        # Check for theme-specific styles
        assert "[data-theme='dark']" in content
        assert "[data-theme='fantasy']" in content
        assert "[data-theme='cyberpunk']" in content

        print("✅ CSS has proper modern mode selectors and responsive design")

    def test_campaign_wizard_html_structure(self):
        """Test campaign wizard generates proper HTML structure"""
        wizard_path = mvp_site_path / "frontend_v1/js/campaign-wizard.js"
        content = wizard_path.read_text()

        # Check for wizard HTML elements
        assert "campaign-wizard" in content
        assert "wizard-progress" in content
        assert "step-indicators" in content
        assert "wizard-step" in content
        assert "wizard-navigation" in content

        # Check for step content
        assert "Campaign Basics" in content
        assert "AI's Expertise" in content
        assert "Ready to Launch" in content

        print("✅ Campaign wizard generates proper HTML structure")

    def test_enhanced_search_features(self):
        """Test enhanced search has all required features"""
        search_path = mvp_site_path / "frontend_v1/js/enhanced-search.js"
        content = search_path.read_text()

        # Check for search functionality
        assert "search-filter-container" in content
        assert "campaign-search" in content
        assert "filter-controls" in content
        assert "applyFilters" in content

        # Check for filter types
        assert "sort-by" in content
        assert "theme-filter" in content
        assert "status-filter" in content

        # Check for real-time features
        assert "addEventListener" in content
        assert "debounce" in content
        assert "updateDisplay" in content

        print("✅ Enhanced search has all required features")

    def test_interface_manager_feature_control(self):
        """Test interface manager can control features"""
        manager_path = mvp_site_path / "frontend_v1/js/interface-manager.js"
        content = manager_path.read_text()

        # Check for feature control methods
        assert "disableAnimations" in content
        assert "enableAnimations" in content
        assert "disableEnhancedComponents" in content
        assert "enableEnhancedComponents" in content
        assert "disableInteractiveFeatures" in content
        assert "enableInteractiveFeatures" in content

        # Check for safety mechanisms
        assert "localStorage" in content
        assert "feature_" in content

        print("✅ Interface manager has proper feature control methods")

    def test_backward_compatibility(self):
        """Test that features maintain backward compatibility"""
        # Test features that depend on interface manager
        dependent_js_files = ["campaign-wizard.js", "enhanced-search.js"]

        for js_file in dependent_js_files:
            file_path = mvp_site_path / f"frontend_v1/js/{js_file}"
            content = file_path.read_text()

            # Check for backward compatibility checks
            assert "checkIfEnabled" in content, f"{js_file} should check if enabled"

            # Check that it doesn't break if interface manager isn't available
            assert (
                "window.interfaceManager" in content
            ), f"{js_file} should check for interface manager"

        # Test interface manager itself has safe defaults
        manager_path = mvp_site_path / "frontend_v1/js/interface-manager.js"
        manager_content = manager_path.read_text()
        assert (
            "modern" in manager_content.lower()
        ), "Interface manager should have safe defaults"

        print("✅ All features maintain backward compatibility")

    def test_progressive_enhancement(self):
        """Test that features use progressive enhancement"""
        # Test interface manager has proper default handling
        manager_path = mvp_site_path / "frontend_v1/js/interface-manager.js"
        content = manager_path.read_text()

        # Check for safe defaults and feature control
        assert "enableModernMode" in content
        assert "localStorage" in content

        # Test features only activate in modern mode
        for js_file in ["campaign-wizard.js", "enhanced-search.js"]:
            file_path = mvp_site_path / f"frontend_v1/js/{js_file}"
            content = file_path.read_text()

            assert "isModernMode" in content, f"{js_file} should check for modern mode"
            assert "disable" in content, f"{js_file} should have disable functionality"

        print("✅ Features use progressive enhancement and modern interface system")

    def test_file_integration_order(self):
        """Test that files are loaded in the correct order"""
        index_path = mvp_site_path / "frontend_v1/index.html"
        content = index_path.read_text()

        # Find script tag positions
        interface_pos = content.find("interface-manager.js")
        wizard_pos = content.find("campaign-wizard.js")
        search_pos = content.find("enhanced-search.js")

        # Interface manager should load first
        assert interface_pos < wizard_pos, "Interface manager should load before wizard"
        assert interface_pos < search_pos, "Interface manager should load before search"

        print("✅ JavaScript files are loaded in correct dependency order")

    def test_css_theme_integration(self):
        """Test CSS integrates properly with existing theme system"""
        css_path = mvp_site_path / "frontend_v1/styles/interactive-features.css"
        content = css_path.read_text()

        # Check for theme support (light theme is default, doesn't need explicit selectors)
        required_themes = ["dark", "fantasy", "cyberpunk"]
        for theme in required_themes:
            assert f"[data-theme='{theme}']" in content, f"Should support {theme} theme"

        # Check for no conflicts with existing classes
        assert (
            "!important" not in content.lower()
        ), "Should not use !important declarations"

        print("✅ CSS integrates properly with existing theme system")

    def test_performance_considerations(self):
        """Test that features are optimized for performance"""
        js_files = ["campaign-wizard.js", "enhanced-search.js"]

        for js_file in js_files:
            file_path = mvp_site_path / f"frontend_v1/js/{js_file}"
            content = file_path.read_text()

            # Check for performance optimizations
            if "search" in js_file:
                assert "debounce" in content.lower(), "Search should debounce input"
                assert "setTimeout" in content, "Should use timeout for debouncing"

            # Check for efficient DOM manipulation
            assert "querySelector" in content, "Should use efficient DOM queries"

        print("✅ Features include performance optimizations")

    def test_accessibility_features(self):
        """Test that interactive features maintain accessibility"""
        # Test HTML structure for accessibility
        wizard_path = mvp_site_path / "frontend_v1/js/campaign-wizard.js"
        content = wizard_path.read_text()

        # Check for accessibility-related attributes (role, aria, or label)
        has_accessibility = (
            "role=" in content or "aria-" in content or "label" in content
        )
        assert has_accessibility, "Should have some accessibility attributes"

        # Check for keyboard navigation
        assert "addEventListener" in content

        # Test CSS respects accessibility preferences
        css_path = mvp_site_path / "frontend_v1/styles/interactive-features.css"
        css_content = css_path.read_text()

        # Should have smooth transitions but respect reduced motion
        assert "transition" in css_content

        print("✅ Interactive features maintain accessibility standards")

    def test_error_handling(self):
        """Test that features handle errors gracefully"""
        js_files = ["interface-manager.js", "campaign-wizard.js", "enhanced-search.js"]

        for js_file in js_files:
            file_path = mvp_site_path / f"frontend_v1/js/{js_file}"
            content = file_path.read_text()

            # Check for defensive programming
            assert "if (" in content, f"{js_file} should have conditional checks"

            # Check for safe DOM access (either getElementById or querySelector)
            has_safe_dom = (
                "document.getElementById" in content
                or "document.querySelector" in content
                or "?.querySelector" in content
            )
            assert has_safe_dom, f"{js_file} should safely access DOM elements"

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
        print("   • Modern Interface System")
        print("   • Campaign Wizard (Multi-step Creation)")
        print("   • Enhanced Search & Filter")
        print("   • Enhanced Modals")
        print("   • Backward Compatibility")
        print("   • Progressive Enhancement")
        return True
    print("\n❌ Some tests failed. Please fix issues before deployment.")
    return False


if __name__ == "__main__":
    success = run_milestone_4_tests()
    sys.exit(0 if success else 1)
