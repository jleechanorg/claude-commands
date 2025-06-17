import unittest
import os
import json
from unittest.mock import patch, MagicMock

# We still need the dummy key for the import-time initialization check
os.environ["GEMINI_API_KEY"] = "DUMMY_KEY_FOR_INTEGRATION_TESTING"

import main

class TestInteractionIntegration(unittest.TestCase):

    def setUp(self):
        """
        Set up a test client and create a new campaign for each test.
        """
        # --- THIS IS THE FIX ---
        # 1. Create a patcher for the get_client function.
        self.patcher = patch('gemini_service.get_client')
        
        # 2. Start the patcher and get the mock object.
        mock_get_client = self.patcher.start()
        
        # 3. Configure the mock client that all tests in this class will use.
        self.mock_client = MagicMock()
        mock_get_client.return_value = self.mock_client
        
        # Configure the mock for the 'create campaign' call in this setUp method
        self.mock_client.models.generate_content.return_value.text = "This is a test opening story."
        
        # Standard setup
        self.app = main.create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.user_id = "test-suite-user-123"

        print("\n--- (setUp) Creating a new campaign for the test ---")
        create_response = self.client.post(
            '/api/campaigns',
            headers={'Content-Type': 'application/json', 'X-Test-Bypass-Auth': 'true', 'X-Test-User-ID': self.user_id},
            data=json.dumps({'prompt': 'A test campaign', 'title': 'Integration Test'})
        )
        self.assertEqual(create_response.status_code, 201, "Failed to create campaign in setUp")
        create_data = create_response.get_json()
        self.campaign_id = create_data.get('campaign_id')
        self.assertIsNotNone(self.campaign_id, "Campaign ID not found in setUp response")
        print(f"--- (setUp) Campaign {self.campaign_id} created ---")

    def tearDown(self):
        """
        Clean up any test data and stop the patcher.
        """
        # --- THIS IS THE FIX ---
        # 4. Stop the patcher to clean up the environment after each test.
        self.patcher.stop()
        print(f"--- (tearDown) Test finished for campaign {self.campaign_id} ---")
        pass

    def test_character_mode_interaction(self):
        """
        Tests a full interaction flow using 'character' mode.
        """
        self.mock_client.models.generate_content.return_value.text = "The character sees a door."
        
        print("\n--- RUNNING: test_character_mode_interaction ---")
        response = self.client.post(
            f'/api/campaigns/{self.campaign_id}/interaction',
            headers={'Content-Type': 'application/json', 'X-Test-Bypass-Auth': 'true', 'X-Test-User-ID': self.user_id},
            data=json.dumps({'input': 'I check the door for traps.', 'mode': 'character'})
        )
        print(f"Character Mode Response: {response.get_data(as_text=True)}")
        self.assertEqual(response.status_code, 200)
        response_data = response.get_json()
        self.assertEqual(response_data.get('response'), "The character sees a door.")

    def test_god_mode_interaction(self):
        """
        Tests a full interaction flow using 'god' mode.
        """
        self.mock_client.models.generate_content.return_value.text = "An earthquake shakes the room."

        print("\n--- RUNNING: test_god_mode_interaction ---")
        response = self.client.post(
            f'/api/campaigns/{self.campaign_id}/interaction',
            headers={'Content-Type': 'application/json', 'X-Test-Bypass-Auth': 'true', 'X-Test-User-ID': self.user_id},
            data=json.dumps({'input': 'A sudden earthquake shakes the dungeon.', 'mode': 'god'})
        )
        print(f"God Mode Response: {response.get_data(as_text=True)}")
        self.assertEqual(response.status_code, 200)
        response_data = response.get_json()
        self.assertEqual(response_data.get('response'), "An earthquake shakes the room.")

if __name__ == '__main__':
    unittest.main()
