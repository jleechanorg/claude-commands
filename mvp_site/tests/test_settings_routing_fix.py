#!/usr/bin/env python3
"""
🔴 TDD RED PHASE: Failing tests that expose the real Flask routing issues

These tests SHOULD FAIL initially, documenting exactly what's broken:
1. /settings route serving wrong template
2. /api/settings POST method not allowed
3. Settings template not rendering AI model selection

This follows TDD methodology: Write failing tests → Fix code → Tests pass
"""

import unittest
import requests
import os


class TestSettingsRoutingFix(unittest.TestCase):
    """TDD tests to expose and fix Flask routing issues"""
    
    def setUp(self):
        """Set up test environment"""
        self.base_url = "http://localhost:8081"
        self.test_user_id = "tdd-routing-test"
        
        self.headers = {
            "X-Test-Bypass-Auth": "true",
            "X-Test-User-ID": self.test_user_id,
            "Content-Type": "application/json"
        }
        
        # Ensure server is ready
        self.wait_for_server()
    
    def wait_for_server(self, max_retries=3):
        """Wait for server availability"""
        for i in range(max_retries):
            try:
                response = requests.get(f"{self.base_url}/", timeout=2)
                if response.status_code == 200:
                    return
            except:
                pass
        raise Exception("Server not available for TDD testing")
    
    def test_settings_route_serves_correct_template(self):
        """🔴 RED: /settings route should serve settings.html template, not homepage"""
        print("\n🔴 TDD RED: Testing /settings route template")
        
        response = requests.get(f"{self.base_url}/settings", headers=self.headers)
        
        # What we EXPECT (will fail initially)
        self.assertEqual(response.status_code, 200, "Settings route should return 200")
        
        html = response.text
        
        # These should be present in settings.html template
        self.assertIn("<title>Settings - WorldArchitect.AI</title>", html, 
                     "Settings page should have correct title")
        self.assertIn("AI Model Selection", html, 
                     "Settings page should contain AI Model Selection section")
        self.assertIn('id="modelPro"', html, 
                     "Settings page should contain Gemini Pro radio button")
        self.assertIn('id="modelFlash"', html, 
                     "Settings page should contain Gemini Flash radio button")
        self.assertIn("settings.js", html, 
                     "Settings page should include settings.js script")
        
        # These should NOT be present (these are from homepage)
        self.assertNotIn("Start New Campaign", html, 
                        "Settings page should NOT contain campaign creation content")
        self.assertNotIn("Campaign Type", html, 
                        "Settings page should NOT contain campaign type selection")
        self.assertNotIn('id="new-campaign-form"', html, 
                        "Settings page should NOT contain new campaign form")
    
    def test_settings_api_get_works(self):
        """🔴 RED: GET /api/settings should return user settings JSON"""
        print("\n🔴 TDD RED: Testing GET /api/settings")
        
        response = requests.get(f"{self.base_url}/api/settings", headers=self.headers)
        
        # Should return 200 with JSON response
        self.assertEqual(response.status_code, 200, 
                        "GET /api/settings should return 200")
        
        # Should return valid JSON
        try:
            data = response.json()
            self.assertIsInstance(data, dict, "API should return JSON dict")
        except ValueError:
            self.fail("API should return valid JSON, not HTML")
    
    def test_settings_api_post_allows_model_selection(self):
        """🔴 RED: POST /api/settings should accept model selection"""
        print("\n🔴 TDD RED: Testing POST /api/settings")
        
        payload = {"gemini_model": "flash-2.5"}
        
        response = requests.post(
            f"{self.base_url}/api/settings",
            headers=self.headers,
            json=payload
        )
        
        # Should NOT return 405 Method Not Allowed
        self.assertNotEqual(response.status_code, 405, 
                           "POST /api/settings should be allowed, not 405")
        
        # Should return success
        self.assertEqual(response.status_code, 200, 
                        "POST /api/settings should return 200")
        
        # Should return success JSON
        try:
            data = response.json()
            self.assertTrue(data.get('success'), 
                           f"Should return success=True, got: {data}")
        except ValueError:
            self.fail("API should return JSON response, not HTML")
    
    def test_settings_api_post_validates_model(self):
        """🔴 RED: POST /api/settings should validate model selection"""
        print("\n🔴 TDD RED: Testing POST /api/settings validation")
        
        # Valid model should succeed
        valid_payload = {"gemini_model": "pro-2.5"}
        response = requests.post(
            f"{self.base_url}/api/settings",
            headers=self.headers,
            json=valid_payload
        )
        self.assertEqual(response.status_code, 200, "Valid model should be accepted")
        
        # Invalid model should fail with 400
        invalid_payload = {"gemini_model": "invalid-model"}
        response = requests.post(
            f"{self.base_url}/api/settings",
            headers=self.headers,
            json=invalid_payload
        )
        self.assertEqual(response.status_code, 400, "Invalid model should return 400")
        
        # Missing model should fail with 400
        empty_payload = {}
        response = requests.post(
            f"{self.base_url}/api/settings",
            headers=self.headers,
            json=empty_payload
        )
        self.assertEqual(response.status_code, 400, "Missing model should return 400")
    
    def test_settings_persistence_round_trip(self):
        """🔴 RED: Settings should persist in database"""
        print("\n🔴 TDD RED: Testing settings persistence")
        
        # Set flash model
        flash_payload = {"gemini_model": "flash-2.5"}
        response = requests.post(
            f"{self.base_url}/api/settings",
            headers=self.headers,
            json=flash_payload
        )
        self.assertEqual(response.status_code, 200, "Should save flash model")
        
        # Verify it persisted
        response = requests.get(f"{self.base_url}/api/settings", headers=self.headers)
        self.assertEqual(response.status_code, 200, "Should retrieve settings")
        
        data = response.json()
        self.assertEqual(data.get('gemini_model'), 'flash-2.5', 
                        "Flash model should persist")
        
        # Change to pro model
        pro_payload = {"gemini_model": "pro-2.5"}
        response = requests.post(
            f"{self.base_url}/api/settings",
            headers=self.headers,
            json=pro_payload
        )
        self.assertEqual(response.status_code, 200, "Should save pro model")
        
        # Verify change persisted
        response = requests.get(f"{self.base_url}/api/settings", headers=self.headers)
        data = response.json()
        self.assertEqual(data.get('gemini_model'), 'pro-2.5', 
                        "Pro model should persist")


if __name__ == "__main__":
    print("🔴 TDD RED PHASE: Running failing tests to expose routing issues")
    print("These tests SHOULD FAIL initially - that's the point of TDD!")
    print("=" * 60)
    
    unittest.main(verbosity=2)