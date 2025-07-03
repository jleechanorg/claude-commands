#!/usr/bin/env python3
"""
Test that entity tracking works in get_initial_story
"""
import unittest
import os
import json
import sys

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from main import create_app
from test_integration.integration_test_lib import IntegrationTestSetup

class TestInitialEntityTracking(unittest.TestCase):
    """Test entity tracking in initial story creation"""
    
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()
    
    def test_sariel_initial_tracking(self):
        """Test that Sariel is tracked from the beginning"""
        print("\n" + "="*80)
        print("TESTING INITIAL ENTITY TRACKING FOR SARIEL")
        print("="*80)
        
        user_id = 'test-initial-tracking'
        
        # Create campaign with Sariel
        campaign_data = {
            'prompt': '''Create a new D&D campaign with the following setup:
            
Player Character: Sariel, a member of House Arcanus
Setting: A medieval fantasy world with political intrigue
Starting Location: The throne room of a grand castle

Initialize the campaign with:
- Player character data for Sariel
- Initial NPCs including advisors and court members
- The immediate scenario where Sariel must make important decisions

Begin the narrative with Sariel arriving at court for an important meeting.''',
            'title': 'Initial Entity Tracking Test',
            'selected_prompts': ['narrative', 'mechanics']
        }
        
        print("\nCreating campaign...")
        response = self.client.post(
            '/api/campaigns',
            headers=IntegrationTestSetup.create_test_headers(user_id),
            data=json.dumps(campaign_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201, f"Campaign creation failed: {response.status_code}")
        
        response_json = response.get_json()
        campaign_id = response_json['campaign_id']
        
        # Debug: print response keys
        print(f"\nResponse keys: {list(response_json.keys())}")
        
        # Get campaign data to check the story
        campaign_response = self.client.get(
            f'/api/campaigns/{campaign_id}',
            headers=IntegrationTestSetup.create_test_headers(user_id)
        )
        
        if campaign_response.status_code == 200:
            campaign_data = campaign_response.get_json()
            print(f"\nCampaign data keys: {list(campaign_data.keys())}")
            
            # Look for story in different possible locations
            story_data = campaign_data.get('story', [])
            print(f"Story data type: {type(story_data)}")
            
            if isinstance(story_data, list) and len(story_data) > 0:
                print(f"Story list length: {len(story_data)}")
                # Look for the AI's response, not the user prompt
                narrative = ''
                for i, entry in enumerate(story_data):
                    print(f"Entry {i}: actor={entry.get('actor', 'unknown')}, length={len(entry.get('text', ''))}")
                    if entry.get('actor') == 'assistant' or entry.get('actor') == 'gemini':
                        narrative = entry.get('text', '')
                        break
            elif isinstance(story_data, str):
                narrative = story_data
            else:
                narrative = ''
        else:
            narrative = ''
            print(f"Failed to get campaign data: {campaign_response.status_code}")
            
        print(f"\nNARRATIVE LENGTH: {len(narrative)} characters")
        
        # Debug: print the actual narrative to see what we got
        print(f"\nACTUAL NARRATIVE:")
        print("-" * 40)
        print(narrative[:1000] + "..." if len(narrative) > 1000 else narrative)
        print("-" * 40)
        
        # Check for Sariel in narrative
        sariel_count = narrative.lower().count('sariel')
        print(f"\nSARIEL MENTIONS IN NARRATIVE: {sariel_count}")
        
        if sariel_count > 0:
            print("✓ SUCCESS: Sariel is mentioned in the initial narrative!")
            # Show some context
            lines = narrative.split('\n')
            for i, line in enumerate(lines):
                if 'sariel' in line.lower():
                    print(f"  Line {i}: {line.strip()}")
        else:
            print("✗ FAILURE: Sariel is NOT mentioned in the initial narrative!")
            print("\nFirst 500 characters of narrative:")
            print(narrative[:500])
        
        # Check game state
        print("\n\nCHECKING GAME STATE...")
        if 'game_state' in response_json:
            game_state = response_json['game_state']
            pc_data = game_state.get('player_character_data', {})
            print(f"Player character data: {pc_data}")
            
            if pc_data.get('name') == 'Sariel':
                print("✓ SUCCESS: Sariel is properly set in game state!")
            else:
                print(f"✗ FAILURE: Expected Sariel, got {pc_data.get('name', 'NO NAME')}")
        
        self.assertGreater(sariel_count, 0, "Sariel should be mentioned in initial narrative")

if __name__ == '__main__':
    unittest.main()