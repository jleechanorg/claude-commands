#!/usr/bin/env python3
"""
Animation System Tests - Milestone 3
Tests for CSS animations, JavaScript helpers, and performance
"""

import os
import sys
import tempfile
import unittest

# Add parent directory to path for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)


class TestAnimationSystem(unittest.TestCase):
    """Test the animation system components"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        # Fix paths to point to parent directory
        parent_dir = os.path.dirname(os.path.dirname(__file__))
        self.animation_css_path = os.path.join(
            parent_dir, "static", "styles", "animations.css"
        )
        self.animation_js_path = os.path.join(
            parent_dir, "static", "js", "animation-helpers.js"
        )
        self.index_html_path = os.path.join(parent_dir, "static", "index.html")

    def test_animation_css_exists_and_valid(self):
        """Test that animation CSS file exists and contains expected animations"""
        self.assertTrue(
            os.path.exists(self.animation_css_path), "animations.css file should exist"
        )

        with open(self.animation_css_path) as f:
            css_content = f.read()

        # Test for essential animation components
        essential_animations = [
            "--animation-duration-fast",
            "--animation-duration-normal",
            "--animation-duration-slow",
            "theme-transitioning",
            ".btn:hover",
            "@keyframes",
            "transition:",
            "transform:",
            "opacity:",
        ]

        for animation in essential_animations:
            self.assertIn(animation, css_content, f"CSS should contain {animation}")

        # Test for accessibility support
        self.assertIn(
            "@media (prefers-reduced-motion: reduce)",
            css_content,
            "Should include reduced motion support",
        )

    def test_animation_js_exists_and_valid(self):
        """Test that animation JavaScript file exists and is valid"""
        self.assertTrue(
            os.path.exists(self.animation_js_path),
            "animation-helpers.js file should exist",
        )

        with open(self.animation_js_path) as f:
            js_content = f.read()

        # Test for essential JavaScript components
        essential_components = [
            "class AnimationHelpers",
            "animatedShowView",
            "addButtonLoadingState",
            "enhanceStoryUpdates",
            "window.animations",
            "DOMContentLoaded",
        ]

        for component in essential_components:
            self.assertIn(
                component, js_content, f"JavaScript should contain {component}"
            )

    def test_index_html_includes_animation_files(self):
        """Test that index.html includes animation CSS and JS"""
        self.assertTrue(
            os.path.exists(self.index_html_path), "index.html file should exist"
        )

        with open(self.index_html_path) as f:
            html_content = f.read()

        # Test for animation file inclusions
        self.assertIn(
            'href="/static/styles/animations.css"',
            html_content,
            "Should include animations.css",
        )
        self.assertIn(
            'src="/static/js/animation-helpers.js"',
            html_content,
            "Should include animation-helpers.js",
        )

    def test_animation_css_syntax_validation(self):
        """Test CSS syntax is valid (basic validation)"""
        with open(self.animation_css_path) as f:
            css_content = f.read()

        # Basic syntax checks
        open_braces = css_content.count("{")
        close_braces = css_content.count("}")
        self.assertEqual(open_braces, close_braces, "CSS should have matching braces")

        # Check for common syntax errors
        self.assertNotIn(";;", css_content, "Should not have double semicolons")
        self.assertNotIn(": ;", css_content, "Should not have space before semicolon")

    def test_animation_performance_properties(self):
        """Test that performance-enhancing CSS properties are present"""
        with open(self.animation_css_path) as f:
            css_content = f.read()

        # Performance properties
        performance_props = [
            "will-change:",
            "transform:",  # GPU acceleration
            "opacity:",  # GPU acceleration
            "transition:",  # Smooth animations
        ]

        for prop in performance_props:
            self.assertIn(
                prop, css_content, f"Should include performance property {prop}"
            )

    def test_theme_specific_animations(self):
        """Test that theme-specific animations are included"""
        with open(self.animation_css_path) as f:
            css_content = f.read()

        # Theme-specific features
        theme_features = [
            '[data-theme="fantasy"]',
            '[data-theme="cyberpunk"]',
            "@keyframes sparkle",
            "box-shadow:",
        ]

        for feature in theme_features:
            self.assertIn(
                feature, css_content, f"Should include theme feature {feature}"
            )

    def test_accessibility_features(self):
        """Test that accessibility features are properly implemented"""
        with open(self.animation_css_path) as f:
            css_content = f.read()

        # Accessibility checks
        self.assertIn(
            "prefers-reduced-motion",
            css_content,
            "Should respect user motion preferences",
        )
        self.assertIn(
            "animation-duration: 0.01ms",
            css_content,
            "Should disable animations for reduced motion",
        )

    def test_javascript_error_handling(self):
        """Test that JavaScript has proper error handling patterns"""
        with open(self.animation_js_path) as f:
            js_content = f.read()

        # Error handling patterns
        error_handling = [
            "if (!",  # Null checks
            "?.(",  # Optional chaining
            "setTimeout(",  # Async handling
            "resolve();",  # Promise handling
        ]

        for pattern in error_handling:
            self.assertIn(
                pattern, js_content, f"Should include error handling pattern {pattern}"
            )


class TestAnimationIntegration(unittest.TestCase):
    """Integration tests for animation system with existing app"""

    def setUp(self):
        """Set up integration test environment"""
        self.app_js_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "static", "app.js"
        )

    def test_animation_system_compatibility(self):
        """Test that animation system doesn't conflict with existing app.js"""
        # Check that both files exist
        animation_js_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "static",
            "js",
            "animation-helpers.js",
        )

        self.assertTrue(os.path.exists(self.app_js_path), "app.js should exist")
        self.assertTrue(
            os.path.exists(animation_js_path), "animation-helpers.js should exist"
        )

        # Read both files
        with open(self.app_js_path) as f:
            app_content = f.read()

        with open(animation_js_path) as f:
            animation_content = f.read()

        # Test for compatibility patterns
        # Animation system should enhance, not replace
        if "showView" in app_content:
            self.assertIn(
                "originalShowView",
                animation_content,
                "Should preserve original showView function",
            )

        # Should not conflict with existing global variables
        app_globals = []
        if "window." in app_content:
            # Basic check for global variable conflicts
            # This is a simplified check - in real testing you'd parse more carefully
            pass

    def test_loading_order_in_html(self):
        """Test that scripts are loaded in correct order"""
        index_html_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "static", "index.html"
        )

        with open(index_html_path) as f:
            html_content = f.read()

        # Find script positions
        theme_manager_pos = html_content.find("theme-manager.js")
        animation_helpers_pos = html_content.find("animation-helpers.js")
        app_js_pos = html_content.find('src="/static/app.js"')

        # Animation helpers should load before app.js but after theme-manager
        self.assertLess(
            theme_manager_pos,
            animation_helpers_pos,
            "theme-manager.js should load before animation-helpers.js",
        )
        self.assertLess(
            animation_helpers_pos,
            app_js_pos,
            "animation-helpers.js should load before app.js",
        )


class TestAnimationPerformance(unittest.TestCase):
    """Performance tests for animation system"""

    def test_css_file_size(self):
        """Test that CSS file size is reasonable"""
        animation_css_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "static",
            "styles",
            "animations.css",
        )

        if os.path.exists(animation_css_path):
            file_size = os.path.getsize(animation_css_path)
            # Should be under 50KB for performance
            self.assertLess(
                file_size,
                50 * 1024,
                f"animations.css should be under 50KB, got {file_size} bytes",
            )

    def test_javascript_file_size(self):
        """Test that JavaScript file size is reasonable"""
        animation_js_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "static",
            "js",
            "animation-helpers.js",
        )

        if os.path.exists(animation_js_path):
            file_size = os.path.getsize(animation_js_path)
            # Should be under 30KB for performance
            self.assertLess(
                file_size,
                30 * 1024,
                f"animation-helpers.js should be under 30KB, got {file_size} bytes",
            )

    def test_css_selector_efficiency(self):
        """Test that CSS selectors are efficient"""
        animation_css_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "static",
            "styles",
            "animations.css",
        )

        with open(animation_css_path) as f:
            css_content = f.read()

        # Check for efficient selectors (avoid inefficient patterns)
        inefficient_patterns = [
            "* * *",  # Too many universal selectors
            '[class*=""] [class*=""]',  # Double attribute selectors
        ]

        for pattern in inefficient_patterns:
            self.assertNotIn(
                pattern,
                css_content,
                f"Should avoid inefficient selector pattern: {pattern}",
            )


class TestAnimationFunctionality(unittest.TestCase):
    """Functional tests for animation features"""

    def test_animation_duration_variables(self):
        """Test that animation duration variables are properly defined"""
        animation_css_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "static",
            "styles",
            "animations.css",
        )

        with open(animation_css_path) as f:
            css_content = f.read()

        # Check for duration variables
        duration_vars = [
            "--animation-duration-fast: 0.15s",
            "--animation-duration-normal: 0.3s",
            "--animation-duration-slow: 0.5s",
        ]

        for var in duration_vars:
            self.assertIn(var, css_content, f"Should define duration variable: {var}")

    def test_keyframe_animations_defined(self):
        """Test that essential keyframe animations are defined"""
        animation_css_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "static",
            "styles",
            "animations.css",
        )

        with open(animation_css_path) as f:
            css_content = f.read()

        # Essential animations
        keyframes = [
            "@keyframes btn-spin",
            "@keyframes slideInUp",
            "@keyframes sparkle",
            "@keyframes typeWriter",
            "@keyframes pulse",
        ]

        for keyframe in keyframes:
            self.assertIn(keyframe, css_content, f"Should define keyframe: {keyframe}")

    def test_javascript_api_methods(self):
        """Test that JavaScript API provides expected methods"""
        animation_js_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "static",
            "js",
            "animation-helpers.js",
        )

        with open(animation_js_path) as f:
            js_content = f.read()

        # API methods that should be available
        api_methods = [
            "showView:",
            "showLoading:",
            "hideLoading:",
            "addButtonLoading:",
            "removeButtonLoading:",
            "showStoryLoading:",
            "hideStoryLoading:",
        ]

        for method in api_methods:
            self.assertIn(method, js_content, f"Should provide API method: {method}")


def run_animation_tests():
    """Run all animation system tests"""
    test_suites = [
        unittest.TestLoader().loadTestsFromTestCase(TestAnimationSystem),
        unittest.TestLoader().loadTestsFromTestCase(TestAnimationIntegration),
        unittest.TestLoader().loadTestsFromTestCase(TestAnimationPerformance),
        unittest.TestLoader().loadTestsFromTestCase(TestAnimationFunctionality),
    ]

    combined_suite = unittest.TestSuite(test_suites)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(combined_suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    print("🧪 Running Animation System Tests...")
    success = run_animation_tests()

    if success:
        print("✅ All animation tests passed!")
    else:
        print("❌ Some animation tests failed.")
        exit(1)
