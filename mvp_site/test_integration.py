import unittest
import os
import json

import main

class TestInteractionIntegration(unittest.TestCase):

    def setUp(self):
        """
        Set up a test client and create a new campaign for each test.
        """
        self.app = main.create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.user_id = "test-suite-user-123"

        # Create a new campaign before each test runs
        print("\n--- (setUp) Creating a new campaign for the test ---")
        create_response = self.client.post(
            '/api/campaigns',
            headers={
                'Content-Type': 'application/json',
                'X-Test-Bypass-Auth': 'true',
                'X-Test-User-ID': self.user_id
            },
            data=json.dumps({
                'prompt': 'A test campaign for our integration test.',
                'title': 'Integration Test Campaign'
            })
        )
        self.assertEqual(create_response.status_code, 201, "Failed to create campaign in setUp")
        create_data = create_response.get_json()
        self.campaign_id = create_data.get('campaign_id')
        self.assertIsNotNone(self.campaign_id, "Campaign ID not found in setUp response")
        print(f"--- (setUp) Campaign {self.campaign_id} created ---")

    def tearDown(self):
        """
        Clean up any test data. (Placeholder for now)
        """
        print(f"--- (tearDown) Test finished for campaign {self.campaign_id} ---")
        pass

    def test_character_mode_interaction(self):
        """
        Tests a full interaction flow using 'character' mode.
        """
        print("\n--- RUNNING: test_character_mode_interaction ---")
        response = self.client.post(
            f'/api/campaigns/{self.campaign_id}/interaction',
            headers={
                'Content-Type': 'application/json',
                'X-Test-Bypass-Auth': 'true',
                'X-Test-User-ID': self.user_id
            },
            data=json.dumps({
                'input': 'I check the door for traps.',
                'mode': 'character'
            })
        )
        print(f"Character Mode Response: {response.get_data(as_text=True)}")
        self.assertEqual(response.status_code, 200)
        response_data = response.get_json()
        self.assertTrue(response_data.get('success'))

    def test_god_mode_interaction(self):
        """
        Tests a full interaction flow using 'god' mode.
        """
        print("\n--- RUNNING: test_god_mode_interaction ---")
        response = self.client.post(
            f'/api/campaigns/{self.campaign_id}/interaction',
            headers={
                'Content-Type': 'application/json',
                'X-Test-Bypass-Auth': 'true',
                'X-Test-User-ID': self.user_id
            },
            data=json.dumps({
                'input': 'A sudden earthquake shakes the dungeon.',
                'mode': 'god'
            })
        )
        print(f"God Mode Response: {response.get_data(as_text=True)}")
        self.assertEqual(response.status_code, 200)
        response_data = response.get_json()
        self.assertTrue(response_data.get('success'))

if __name__ == '__main__':
    unittest.main()
