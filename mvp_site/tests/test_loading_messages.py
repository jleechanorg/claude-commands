"""Tests for loading spinner messages - TASK-005b"""

import os
import unittest


class TestLoadingMessages(unittest.TestCase):
    """Test loading spinner with contextual messages"""

    def test_loading_messages_css_exists(self):
        """Test that loading messages CSS file exists"""
        css_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "frontend_v1",
            "loading-messages.css",
        )
        assert os.path.exists(css_path), "Loading messages CSS file should exist"

        # Verify CSS content
        with open(css_path) as f:
            css_content = f.read()

        # Check for essential CSS rules
        assert ".loading-message" in css_content
        assert ".loading-content" in css_content
        assert "opacity" in css_content
        assert "transition" in css_content

    def test_loading_messages_js_exists(self):
        """Test that loading messages JavaScript module exists"""
        js_path = os.path.join(
            os.path.dirname(__file__), "..", "frontend_v1", "js", "loading-messages.js"
        )
        assert os.path.exists(js_path), "Loading messages JS file should exist"

        # Verify JS content
        with open(js_path) as f:
            js_content = f.read()

        # Check for LoadingMessages class
        assert "class LoadingMessages" in js_content
        assert "newCampaign:" in js_content
        assert "interaction:" in js_content
        assert "loading:" in js_content
        assert "saving:" in js_content

    def test_index_html_includes_resources(self):
        """Test that index.html includes loading messages resources"""
        html_path = os.path.join(
            os.path.dirname(__file__), "..", "frontend_v1", "index.html"
        )

        with open(html_path) as f:
            html_content = f.read()

        # Verify resources are included
        assert "loading-messages.css" in html_content
        assert "loading-messages.js" in html_content
        assert "<!-- Loading Messages - TASK-005b -->" in html_content

        # Verify HTML structure updates
        assert "loading-content" in html_content
        assert '<div class="loading-message"></div>' in html_content

    def test_app_js_integration(self):
        """Test that app.js integrates with loading messages"""
        js_path = os.path.join(os.path.dirname(__file__), "..", "frontend_v1", "app.js")

        with open(js_path) as f:
            js_content = f.read()

        # Check for loading message integration
        assert "window.loadingMessages" in js_content
        assert "showSpinner('newCampaign')" in js_content
        assert "showSpinner('loading')" in js_content
        assert "showSpinner('saving')" in js_content
        assert "loadingMessages.start('interaction'" in js_content
        assert "loadingMessages.stop()" in js_content

    def test_message_content_variety(self):
        """Test that various contextual messages exist"""
        js_path = os.path.join(
            os.path.dirname(__file__), "..", "frontend_v1", "js", "loading-messages.js"
        )

        with open(js_path) as f:
            js_content = f.read()

        # Check for various message types
        expected_messages = [
            "🎲 Rolling for initiative",
            "🏰 Building your world",
            "🤔 The DM is thinking",
            "💾 Saving your progress",
            "📚 Loading your adventure",
        ]

        for message in expected_messages:
            assert message in js_content, f"Expected message '{message}' not found"


if __name__ == "__main__":
    unittest.main()
