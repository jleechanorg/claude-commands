#!/usr/bin/env python3
"""
🔴 RED: TDD tests for settings authentication bypass with real test server
Layer 1: Unit tests for auth bypass logic

These tests SHOULD FAIL initially to demonstrate the problem
"""

import unittest
import requests
import os
import time

class TestSettingsAuthBypass(unittest.TestCase):
    """Test settings authentication bypass for real test server"""
    
    def setUp(self):
        """Set up test client for real server"""
        self.base_url = "http://localhost:8081"
        self.test_user_id = "test-user-settings-auth"
        
        # Headers that SHOULD work for auth bypass
        self.bypass_headers = {
            "X-Test-Bypass-Auth": "true", 
            "X-Test-User-ID": self.test_user_id,
            "Content-Type": "application/json"
        }
        
        # Wait for server to be ready
        self.wait_for_server()
    
    def wait_for_server(self, max_retries=10):
        """Wait for test server to be available"""
        for i in range(max_retries):
            try:
                response = requests.get(f"{self.base_url}/", timeout=2)
                if response.status_code == 200:
                    return
            except:
                pass
            time.sleep(1)
        raise Exception("Test server not available")
    
    def test_settings_page_auth_bypass_fails(self):
        """🔴 RED: Settings page should allow auth bypass but currently fails"""
        # This test should FAIL initially, showing the problem
        response = requests.get(
            f"{self.base_url}/settings", 
            headers=self.bypass_headers
        )
        
        # What we EXPECT (but will fail initially)
        self.assertEqual(response.status_code, 200, 
                        f"Settings page should allow auth bypass, got {response.status_code}: {response.text}")
        self.assertIn("Settings", response.text, 
                     "Settings page should contain 'Settings' text")
    
    def test_settings_api_get_auth_bypass_fails(self):
        """🔴 RED: Settings API GET should allow auth bypass but currently fails"""
        response = requests.get(
            f"{self.base_url}/api/settings",
            headers=self.bypass_headers
        )
        
        # What we EXPECT (but will fail initially)  
        self.assertEqual(response.status_code, 200,
                        f"Settings API GET should allow auth bypass, got {response.status_code}: {response.text}")
        
        data = response.json()
        self.assertIsInstance(data, dict, "Should return dict of settings")
    
    def test_settings_api_post_auth_bypass_fails(self):
        """🔴 RED: Settings API POST should allow auth bypass but currently fails"""
        payload = {"gemini_model": "flash-2.5"}
        
        response = requests.post(
            f"{self.base_url}/api/settings",
            headers=self.bypass_headers,
            json=payload
        )
        
        # What we EXPECT (but will fail initially)
        self.assertEqual(response.status_code, 200,
                        f"Settings API POST should allow auth bypass, got {response.status_code}: {response.text}")
        
        data = response.json()
        self.assertTrue(data.get('success'), "Should return success=True")
    
    def test_current_auth_bypass_behavior(self):
        """🔴 RED: Document current failing behavior"""
        # Test what actually happens now (should be 401)
        response = requests.get(
            f"{self.base_url}/settings",
            headers=self.bypass_headers
        )
        
        # Document the current failing state
        print(f"\n🔴 CURRENT FAILING STATE:")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        print(f"Headers sent: {self.bypass_headers}")
        
        # This will pass initially (documenting the broken state)
        self.assertEqual(response.status_code, 401, 
                        "Currently failing with 401 - this documents the problem")


if __name__ == "__main__":
    # Run the failing tests to demonstrate the problem
    unittest.main(verbosity=2)