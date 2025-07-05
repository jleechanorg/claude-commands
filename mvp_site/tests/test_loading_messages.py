"""Tests for loading spinner messages - TASK-005b"""

import unittest
import os


class TestLoadingMessages(unittest.TestCase):
    """Test loading spinner with contextual messages"""
    
    def test_loading_messages_css_exists(self):
        """Test that loading messages CSS file exists"""
        css_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'loading-messages.css')
        self.assertTrue(os.path.exists(css_path), "Loading messages CSS file should exist")
        
        # Verify CSS content
        with open(css_path, 'r') as f:
            css_content = f.read()
            
        # Check for essential CSS rules
        self.assertIn('.loading-message', css_content)
        self.assertIn('.loading-content', css_content)
        self.assertIn('opacity', css_content)
        self.assertIn('transition', css_content)
        
    def test_loading_messages_js_exists(self):
        """Test that loading messages JavaScript module exists"""
        js_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'js', 'loading-messages.js')
        self.assertTrue(os.path.exists(js_path), "Loading messages JS file should exist")
        
        # Verify JS content
        with open(js_path, 'r') as f:
            js_content = f.read()
            
        # Check for LoadingMessages class
        self.assertIn('class LoadingMessages', js_content)
        self.assertIn('newCampaign:', js_content)
        self.assertIn('interaction:', js_content)
        self.assertIn('loading:', js_content)
        self.assertIn('saving:', js_content)
        
    def test_index_html_includes_resources(self):
        """Test that index.html includes loading messages resources"""
        html_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'index.html')
        
        with open(html_path, 'r') as f:
            html_content = f.read()
            
        # Verify resources are included
        self.assertIn('loading-messages.css', html_content)
        self.assertIn('loading-messages.js', html_content)
        self.assertIn('<!-- Loading Messages - TASK-005b -->', html_content)
        
        # Verify HTML structure updates
        self.assertIn('loading-content', html_content)
        self.assertIn('<div class="loading-message"></div>', html_content)
        
    def test_app_js_integration(self):
        """Test that app.js integrates with loading messages"""
        js_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'app.js')
        
        with open(js_path, 'r') as f:
            js_content = f.read()
            
        # Check for loading message integration
        self.assertIn('window.loadingMessages', js_content)
        self.assertIn("showSpinner('newCampaign')", js_content)
        self.assertIn("showSpinner('loading')", js_content)
        self.assertIn("showSpinner('saving')", js_content)
        self.assertIn("loadingMessages.start('interaction'", js_content)
        self.assertIn('loadingMessages.stop()', js_content)
        
    def test_message_content_variety(self):
        """Test that various contextual messages exist"""
        js_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'js', 'loading-messages.js')
        
        with open(js_path, 'r') as f:
            js_content = f.read()
            
        # Check for various message types
        expected_messages = [
            '🎲 Rolling for initiative',
            '🏰 Building your world',
            '🤔 The DM is thinking',
            '💾 Saving your progress',
            '📚 Loading your adventure'
        ]
        
        for message in expected_messages:
            self.assertIn(message, js_content, f"Expected message '{message}' not found")


if __name__ == '__main__':
    unittest.main()