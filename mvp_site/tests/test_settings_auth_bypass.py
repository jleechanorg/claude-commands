#!/usr/bin/env python3
"""
🔴 RED: TDD tests for settings authentication bypass with Flask test client
Layer 1: Unit tests for auth bypass logic

These tests verify auth bypass works with Flask test client (TESTING=True)
"""

import unittest
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import create_app, HEADER_TEST_BYPASS, HEADER_TEST_USER_ID

class TestSettingsAuthBypass(unittest.TestCase):
    """Test settings authentication bypass using Flask test client"""
    
    def setUp(self):
        """Set up Flask test client with TESTING=True"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.test_user_id = "test-user-settings-auth"
        
        # Headers that SHOULD work for auth bypass
        self.bypass_headers = {
            HEADER_TEST_BYPASS: "true", 
            HEADER_TEST_USER_ID: self.test_user_id,
            "Content-Type": "application/json"
        }
    
    def test_settings_page_auth_bypass_works(self):
        """✅ GREEN: Settings page should allow auth bypass"""
        response = self.client.get(
            "/settings", 
            headers=self.bypass_headers
        )
        
        # Auth bypass should work
        self.assertEqual(response.status_code, 200, 
                        f"Settings page should allow auth bypass, got {response.status_code}: {response.get_data(as_text=True)}")
        self.assertIn("Settings", response.get_data(as_text=True), 
                     "Settings page should contain 'Settings' text")
    
    def test_settings_api_get_auth_bypass_works(self):
        """✅ GREEN: Settings API GET should allow auth bypass"""
        response = self.client.get(
            "/api/settings",
            headers=self.bypass_headers
        )
        
        # Auth bypass should work 
        self.assertEqual(response.status_code, 200,
                        f"Settings API GET should allow auth bypass, got {response.status_code}: {response.get_data(as_text=True)}")
        
        data = response.get_json()
        self.assertIsInstance(data, dict, "Should return dict of settings")
    
    def test_settings_api_post_auth_bypass_works(self):
        """✅ GREEN: Settings API POST should allow auth bypass"""
        payload = {"gemini_model": "gemini-2.5-flash"}
        
        response = self.client.post(
            "/api/settings",
            headers=self.bypass_headers,
            json=payload
        )
        
        # Auth bypass should work
        self.assertEqual(response.status_code, 200,
                        f"Settings API POST should allow auth bypass, got {response.status_code}: {response.get_data(as_text=True)}")
        
        data = response.get_json()
        self.assertTrue(data.get('success'), "Should return success=True")
    
    def test_settings_without_auth_bypass_fails(self):
        """✅ GREEN: Settings without auth bypass should fail with 401"""
        # Test without auth bypass headers
        response = self.client.get("/settings")
        
        # Should fail without auth bypass
        self.assertEqual(response.status_code, 401, 
                        "Settings without auth bypass should return 401")


if __name__ == "__main__":
    # Run the failing tests to demonstrate the problem
    unittest.main(verbosity=2)