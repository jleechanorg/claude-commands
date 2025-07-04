#!/usr/bin/env python3
"""
Test that STATE_UPDATES_PROPOSED are being generated properly
"""
import unittest
import os
import json
import sys
import re

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from main import create_app
from integration_test_lib import IntegrationTestSetup

class TestStateUpdatesGeneration(unittest.TestCase):
    """Test that state updates are generated in responses"""
    
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()
    
    def test_initial_campaign_generates_state(self):
        """Test that creating a campaign generates initial state"""
        user_id = 'test-state-generation'
        
        # Create campaign with Sariel prompt
        campaign_data = {
            'prompt': 'Start as Sariel. We are in the throne room the day after her mother\'s death.',
            'title': 'State Generation Test',
            'selected_prompts': ['narrative', 'mechanics', 'calibration'],
            'custom_options': ['companions', 'defaultWorld', 'destinySystem']
        }
        
        print("\n=== CREATING CAMPAIGN ===")
        
        response = self.client.post(
            '/api/campaigns',
            headers=IntegrationTestSetup.create_test_headers(user_id),
            data=json.dumps(campaign_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        result = response.get_json()
        print(f"\nCampaign creation response keys: {list(result.keys())}")
        campaign_id = result['campaign_id']
        initial_story = result.get('opening_story', '')
        
        # Check if maybe the story is under a different key
        for key in ['story', 'narrative', 'initial_narrative', 'content']:
            if key in result and result[key]:
                print(f"Found content under key '{key}': {len(result[key])} chars")
        
        # Show the initial story length
        print(f"\nInitial story length: {len(initial_story)} chars")
        
        # Check if STATE_UPDATES_PROPOSED is in the initial story
        has_state_block = '[STATE_UPDATES_PROPOSED]' in initial_story
        print(f"\nInitial story contains STATE_UPDATES_PROPOSED: {has_state_block}")
        
        # Show first 2000 chars to see what we got
        print(f"\nFirst 2000 chars of initial story:\n{initial_story[:2000]}")
        
        if has_state_block:
            # Extract the state block
            match = re.search(r'\[STATE_UPDATES_PROPOSED\](.*?)\[END_STATE_UPDATES_PROPOSED\]', 
                            initial_story, re.DOTALL)
            if match:
                state_json_str = match.group(1).strip()
                print(f"\nExtracted state block:\n{state_json_str[:500]}...")
        
        # Check the actual game state via the campaign endpoint
        state_response = self.client.get(
            f'/api/campaigns/{campaign_id}',
            headers=IntegrationTestSetup.create_test_headers(user_id)
        )
        
        print(f"\nState response status: {state_response.status_code}")
        if state_response.status_code != 200:
            print(f"State response error: {state_response.get_data(as_text=True)}")
            self.assertEqual(state_response.status_code, 200)
        
        campaign_data = state_response.get_json()
        if campaign_data is None:
            print("ERROR: campaign_data is None!")
            self.assertIsNotNone(campaign_data, "Campaign response returned None")
        
        print(f"\nCampaign data keys: {list(campaign_data.keys())}")
        
        # Get the game_state from the campaign response
        game_state = campaign_data.get('game_state', {})
        story_content = campaign_data.get('story', '')
        
        print(f"\nStory content length: {len(story_content)} chars")
        print(f"\nFirst 1000 chars of story:\n{story_content[:1000]}")
        
        # Check if state has data
        has_pc_data = bool(game_state.get('player_character_data', {}))
        has_npc_data = bool(game_state.get('npc_data', {}))
        has_world_data = bool(game_state.get('world_data', {}))
        
        print(f"\nGame state status:")
        print(f"- Has player character data: {has_pc_data}")
        print(f"- Has NPC data: {has_npc_data}")
        print(f"- Has world data: {has_world_data}")
        
        # At least one should have data for a successful state generation
        self.assertTrue(has_pc_data or has_npc_data or has_world_data,
                       "No entity data was generated in the initial campaign state")
    
    def test_character_interaction_generates_state(self):
        """Test that character interactions can generate state updates"""
        user_id = 'test-interaction-state'
        
        # Create a simple campaign
        campaign_data = {
            'prompt': 'I am a knight named Sir Galahad in a medieval kingdom.',
            'title': 'Interaction State Test',
            'selected_prompts': ['narrative'],
            'custom_options': []
        }
        
        response = self.client.post(
            '/api/campaigns',
            headers=IntegrationTestSetup.create_test_headers(user_id),
            data=json.dumps(campaign_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        campaign_id = response.get_json()['campaign_id']
        
        # Send an interaction that should trigger state updates
        interaction_data = {
            'input': 'I draw my sword and prepare for battle.',
            'mode': 'character'
        }
        
        print("\n=== SENDING INTERACTION ===")
        
        response = self.client.post(
            f'/api/campaigns/{campaign_id}/interaction',
            headers=IntegrationTestSetup.create_test_headers(user_id),
            data=json.dumps(interaction_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.get_json()
        narrative = result.get('narrative', '')
        
        # Check for state updates
        has_state_block = '[STATE_UPDATES_PROPOSED]' in narrative
        print(f"\nInteraction response contains STATE_UPDATES_PROPOSED: {has_state_block}")
        
        # Show first part of narrative for debugging
        print(f"\nNarrative preview:\n{narrative[:1000]}...")

if __name__ == '__main__':
    unittest.main()