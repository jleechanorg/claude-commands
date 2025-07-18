#!/usr/bin/env python3
"""
Test to verify mock services are properly initialized when USE_MOCKS=true.
"""

import os
import sys
import unittest

# Set USE_MOCKS before importing anything
os.environ["USE_MOCKS"] = "true"
os.environ["TESTING"] = "true"

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import create_app


class TestMockServices(unittest.TestCase):
    def setUp(self):
        """Set up test client."""
        self.app = create_app()
        self.client = self.app.test_client()
        self.test_headers = {
            "X-Test-Bypass-Auth": "true",
            "X-Test-User-ID": "test-mock-user",
        }

    def test_app_config_use_mocks(self):
        """Test that USE_MOCKS config is properly set."""
        self.assertTrue(self.app.config.get("USE_MOCKS"), "USE_MOCKS should be True")

    def test_services_are_mocked(self):
        """Test that services are using mock implementations."""
        # Import the services that main.py uses
        import main

        # Check that gemini_service is the mock version
        self.assertEqual(
            main.gemini_service.__name__,
            "mocks.mock_gemini_service_wrapper",
            "gemini_service should be the mock wrapper",
        )

        # Check that firestore_service is the mock version
        self.assertEqual(
            main.firestore_service.__name__,
            "mocks.mock_firestore_service_wrapper",
            "firestore_service should be the mock wrapper",
        )

    def test_api_calls_use_mocks(self):
        """Test that API calls actually use mock services."""
        # Get campaigns - should return mock data
        response = self.client.get("/api/campaigns", headers=self.test_headers)
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertIsInstance(data, list)

        # Check if we got the sample campaign from mock data
        if data:
            # The mock includes a sample campaign
            self.assertTrue(
                any(c.get("title") == "The Dragon Knight's Quest" for c in data),
                "Should return mock campaign data",
            )

    def test_create_campaign_with_mocks(self):
        """Test creating a campaign with mock services."""
        campaign_data = {
            "title": "Mock Test Campaign",
            "genre": "Fantasy",
            "tone": "Epic",
            "characterName": "Mock Hero",
            "characterBackground": "Testing mocks",
            "selectedPrompts": [],
        }

        response = self.client.post(
            "/api/campaigns", json=campaign_data, headers=self.test_headers
        )

        self.assertEqual(response.status_code, 201)  # 201 Created
        data = response.get_json()

        # Should get a campaign ID back
        self.assertIn("campaign_id", data)
        self.assertTrue(data.get("success"), "Campaign creation should succeed")

        # The API returns just success and campaign_id
        # We can verify the mock was used by checking campaign content
        campaign_id = data["campaign_id"]
        self.assertIsNotNone(campaign_id, "Should return a campaign ID")


if __name__ == "__main__":
    unittest.main()
