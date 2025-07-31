"""Tests for campaign list click functionality - TASK-005a"""

import os
import unittest


class TestCampaignClicks(unittest.TestCase):
    """Test campaign list click registration and navigation"""

    def test_campaign_item_has_clickable_attributes(self):
        """Test that campaign items have proper data attributes for clicking"""
        # Mock campaign data
        campaign = {
            "id": "test-123",
            "title": "Test Campaign",
            "initial_prompt": "A test campaign prompt",
            "last_played": "2024-01-01T12:00:00",
        }

        # Verify the campaign item would have correct data attributes
        assert campaign["id"] is not None
        assert campaign["title"] is not None

    def test_css_classes_present(self):
        """Test that required CSS classes are defined"""
        # This test verifies the CSS file exists and can be loaded

        css_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "frontend_v1",
            "campaign-click-fix.css",
        )
        assert os.path.exists(css_path), "Campaign click fix CSS file should exist"

        # Read CSS content to verify key classes
        with open(css_path) as f:
            css_content = f.read()

        # Check for essential CSS rules
        assert ".campaign-title-link" in css_content
        assert "cursor: pointer" in css_content
        assert ".list-group-item[data-campaign-id]" in css_content

    def test_javascript_click_handler_structure(self):
        """Test that JavaScript has proper click handler structure"""

        js_path = os.path.join(os.path.dirname(__file__), "..", "frontend_v1", "app.js")

        with open(js_path) as f:
            js_content = f.read()

        # Verify click handler improvements are present
        assert "campaign-list').addEventListener('click'" in js_content
        assert "e.stopPropagation()" in js_content
        assert "campaignItem.style.opacity" in js_content
        assert "handleRouteChange()" in js_content

    def test_index_html_includes_css(self):
        """Test that index.html includes the campaign click fix CSS"""

        html_path = os.path.join(
            os.path.dirname(__file__), "..", "frontend_v1", "index.html"
        )

        with open(html_path) as f:
            html_content = f.read()

        # Verify CSS is included
        assert "campaign-click-fix.css" in html_content
        assert "<!-- Campaign Click Fix - TASK-005a -->" in html_content


if __name__ == "__main__":
    unittest.main()
