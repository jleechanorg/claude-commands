#!/usr/bin/env python3
"""
Debug test to understand why Sariel is missing from narratives
"""
import unittest
import os
import json
import sys
import logging

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from main import create_app
from integration_test_lib import IntegrationTestSetup
import gemini_service

# Configure very verbose logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Capture prompts
captured_prompts = []

# Monkey patch to capture prompts
original_call = gemini_service._call_gemini_api

def capture_prompt(prompt_parts, model_name, **kwargs):
    if prompt_parts:
        prompt = prompt_parts[0] if isinstance(prompt_parts[0], str) else str(prompt_parts[0])
        print("\n" + "="*80)
        print("CHECKING PROMPT FOR SARIEL MENTIONS:")
        print("="*80)
        
        # Check for entity preloading
        if "=== ENTITY MANIFEST ===" in prompt:
            print("✓ Entity manifest found in prompt")
            manifest_start = prompt.find("=== ENTITY MANIFEST ===")
            manifest_end = prompt.find("=== END ENTITY MANIFEST ===")
            if manifest_start != -1 and manifest_end != -1:
                manifest = prompt[manifest_start:manifest_end]
                print("Entity manifest content:")
                print(manifest[:500] + "..." if len(manifest) > 500 else manifest)
        else:
            print("✗ No entity manifest found in prompt!")
        
        # Check for Sariel in prompt
        sariel_count = prompt.lower().count('sariel')
        print(f"\nSariel mentioned {sariel_count} times in prompt")
        
        # Show entity-related sections
        lines = prompt.split('\n')
        for i, line in enumerate(lines):
            if 'PLAYER CHARACTER' in line or 'Sariel' in line or 'ENTITIES' in line:
                print(f"Line {i}: {line}")
        
        captured_prompts.append(prompt)
    
    return original_call(prompt_parts, model_name, **kwargs)

gemini_service._call_gemini_api = capture_prompt

class TestSarielEntityDebug(unittest.TestCase):
    """Debug why Sariel is missing"""
    
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()
        
        # Load Sariel campaign prompts
        prompts_path = os.path.join(os.path.dirname(__file__), 'data', 'sariel_campaign_prompts.json')
        with open(prompts_path, 'r') as f:
            cls.sariel_data = json.load(f)
    
    def test_debug_sariel_missing(self):
        """Debug first interaction to see why Sariel is missing"""
        print("\n" + "="*80)
        print("DEBUGGING SARIEL ENTITY TRACKING")
        print("="*80)
        
        user_id = 'test-debug-sariel'
        
        # Create campaign
        initial_prompt = self.sariel_data['prompts'][0]
        print(f"\nCreating campaign with initial prompt...")
        
        campaign_data = {
            'prompt': initial_prompt['input'],
            'title': 'Debug Sariel Test',
            'selected_prompts': ['narrative', 'mechanics']
        }
        
        response = self.client.post(
            '/api/campaigns',
            headers=IntegrationTestSetup.create_test_headers(user_id),
            data=json.dumps(campaign_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        campaign_id = response.get_json()['campaign_id']
        
        # Get initial game state
        print(f"\nChecking initial game state...")
        state_response = self.client.get(
            f'/api/campaigns/{campaign_id}/state',
            headers=IntegrationTestSetup.create_test_headers(user_id)
        )
        
        if state_response.status_code == 200:
            game_state = state_response.get_json()
            print(f"Player character data: {game_state.get('player_character_data', {})}")
            print(f"NPCs: {list(game_state.get('npc_data', {}).keys())}")
        else:
            print(f"Failed to get game state: {state_response.status_code}")
            print(f"Response: {state_response.get_data(as_text=True)}")
            game_state = {}
        
        # Run first interaction
        print(f"\n\nRunning first interaction...")
        first_prompt = self.sariel_data['prompts'][1]
        print(f"Input: {first_prompt['input']}")
        print(f"Expected entities: {first_prompt['context'].get('expected_entities', [])}")
        
        interaction_data = {
            'input': first_prompt['input'],
            'mode': 'character'
        }
        
        response = self.client.post(
            f'/api/campaigns/{campaign_id}/interaction',
            headers=IntegrationTestSetup.create_test_headers(user_id),
            data=json.dumps(interaction_data),
            content_type='application/json'
        )
        
        if response.status_code == 200:
            result = response.get_json()
            narrative = result.get('narrative', '')
            
            print(f"\n\nNARRATIVE RESPONSE:")
            print(narrative)
            
            # Check for Sariel
            if 'sariel' in narrative.lower():
                print(f"\n✓ Sariel IS mentioned in narrative!")
            else:
                print(f"\n✗ Sariel is MISSING from narrative!")
                
            # Check game state after
            state_response = self.client.get(
                f'/api/campaigns/{campaign_id}/state',
                headers=IntegrationTestSetup.create_test_headers(user_id)
            )
            
            if state_response.status_code == 200:
                game_state = state_response.get_json()
                print(f"\nGame state after interaction:")
                print(f"Player character data: {game_state.get('player_character_data', {})}")

if __name__ == '__main__':
    unittest.main()