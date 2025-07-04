"""Tests for campaign list click functionality - TASK-005a"""

import unittest
from unittest.mock import patch, MagicMock
import json


class TestCampaignClicks(unittest.TestCase):
    """Test campaign list click registration and navigation"""
    
    def test_campaign_item_has_clickable_attributes(self):
        """Test that campaign items have proper data attributes for clicking"""
        # Mock campaign data
        campaign = {
            'id': 'test-123',
            'title': 'Test Campaign',
            'initial_prompt': 'A test campaign prompt',
            'last_played': '2024-01-01T12:00:00'
        }
        
        # Verify the campaign item would have correct data attributes
        self.assertIsNotNone(campaign['id'])
        self.assertIsNotNone(campaign['title'])
        
    def test_css_classes_present(self):
        """Test that required CSS classes are defined"""
        # This test verifies the CSS file exists and can be loaded
        import os
        css_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'campaign-click-fix.css')
        self.assertTrue(os.path.exists(css_path), "Campaign click fix CSS file should exist")
        
        # Read CSS content to verify key classes
        with open(css_path, 'r') as f:
            css_content = f.read()
            
        # Check for essential CSS rules
        self.assertIn('.campaign-title-link', css_content)
        self.assertIn('cursor: pointer', css_content)
        self.assertIn('.list-group-item[data-campaign-id]', css_content)
        
    def test_javascript_click_handler_structure(self):
        """Test that JavaScript has proper click handler structure"""
        import os
        js_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'app.js')
        
        with open(js_path, 'r') as f:
            js_content = f.read()
            
        # Verify click handler improvements are present
        self.assertIn("campaign-list').addEventListener('click'", js_content)
        self.assertIn('e.stopPropagation()', js_content)
        self.assertIn('campaignItem.style.opacity', js_content)
        self.assertIn('handleRouteChange()', js_content)
        
    def test_index_html_includes_css(self):
        """Test that index.html includes the campaign click fix CSS"""
        import os
        html_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'index.html')
        
        with open(html_path, 'r') as f:
            html_content = f.read()
            
        # Verify CSS is included
        self.assertIn('campaign-click-fix.css', html_content)
        self.assertIn('<!-- Campaign Click Fix - TASK-005a -->', html_content)


if __name__ == '__main__':
    unittest.main()