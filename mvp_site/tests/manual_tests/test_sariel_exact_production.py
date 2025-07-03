#!/usr/bin/env python3
"""
Test using exact production campaign example from user
Always picks choice 1 after running out of provided prompts
"""
import unittest
import os
import json
import sys
import re
from typing import Dict, List, Any

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from main import create_app
from test_integration.integration_test_lib import IntegrationTestSetup
import gemini_service
from game_state import GameState

class TestSarielExactProduction(unittest.TestCase):
    """Test with exact production campaign prompts"""
    
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()
        
        # Load exact campaign prompts
        prompts_path = os.path.join(os.path.dirname(__file__), 'data', 'sariel_campaign_exact.json')
        with open(prompts_path, 'r') as f:
            cls.campaign_data = json.load(f)
    
    def extract_choice_options(self, narrative: str) -> List[str]:
        """Extract choice options from narrative planning block"""
        # Look for numbered choices like "1. **[Option_1]:**"
        pattern = r'\d+\.\s+\*\*\[([^\]]+)\]:\*\*'
        matches = re.findall(pattern, narrative)
        return matches
    
    def count_entity_fields(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """Count all fields for each entity type"""
        if not game_state:
            return {
                'player_character': {'total_entities': 0, 'total_fields': 0, 'entities': {}},
                'npcs': {'total_entities': 0, 'total_fields': 0, 'entities': {}},
                'world_data': {'total_fields': 0, 'fields': []},
                'combat_state': {'total_fields': 0, 'fields': []},
                'total_all': 0
            }
        
        field_counts = {
            'player_character': {'total_entities': 0, 'total_fields': 0, 'entities': {}},
            'npcs': {'total_entities': 0, 'total_fields': 0, 'entities': {}},
            'world_data': {'total_fields': 0, 'fields': []},
            'combat_state': {'total_fields': 0, 'fields': []},
            'total_all': 0
        }
        
        # Player character
        pc_data = game_state.get('player_character_data', {})
        if isinstance(pc_data, dict) and pc_data:
            pc_name = pc_data.get('name', 'Unknown')
            field_counts['player_character']['total_entities'] = 1
            field_counts['player_character']['total_fields'] = self._count_fields_recursive(pc_data)
            field_counts['player_character']['entities'][pc_name] = {
                'field_count': field_counts['player_character']['total_fields'],
                'has_state_updates': bool(pc_data)
            }
        
        # NPCs
        npc_data = game_state.get('npc_data', {})
        for npc_id, npc_info in npc_data.items():
            if isinstance(npc_info, dict):
                npc_name = npc_info.get('name', npc_id)
                field_count = self._count_fields_recursive(npc_info)
                field_counts['npcs']['total_entities'] += 1
                field_counts['npcs']['total_fields'] += field_count
                field_counts['npcs']['entities'][npc_name] = {
                    'field_count': field_count,
                    'has_state_updates': bool(npc_info)
                }
        
        # World data
        world_data = game_state.get('world_data', {})
        if isinstance(world_data, dict):
            field_counts['world_data']['total_fields'] = self._count_fields_recursive(world_data)
            field_counts['world_data']['fields'] = list(world_data.keys())
        
        # Combat state
        combat_state = game_state.get('combat_state', {})
        if isinstance(combat_state, dict):
            field_counts['combat_state']['total_fields'] = self._count_fields_recursive(combat_state)
            field_counts['combat_state']['fields'] = list(combat_state.keys())
        
        # Total
        field_counts['total_all'] = (
            field_counts['player_character']['total_fields'] +
            field_counts['npcs']['total_fields'] +
            field_counts['world_data']['total_fields'] +
            field_counts['combat_state']['total_fields']
        )
        
        return field_counts
    
    def _count_fields_recursive(self, obj: Any, depth: int = 0) -> int:
        """Recursively count all fields in a nested structure"""
        if depth > 10:  # Prevent infinite recursion
            return 0
            
        if isinstance(obj, dict):
            count = len(obj)
            for value in obj.values():
                if isinstance(value, (dict, list)):
                    count += self._count_fields_recursive(value, depth + 1)
            return count
        elif isinstance(obj, list):
            count = 0
            for item in obj:
                if isinstance(item, (dict, list)):
                    count += self._count_fields_recursive(item, depth + 1)
            return count
        else:
            return 0
    
    def test_exact_production_campaign(self):
        """Test with exact production campaign flow"""
        print("\n" + "="*80)
        print("SARIEL EXACT PRODUCTION CAMPAIGN TEST")
        print("="*80)
        
        user_id = 'test-exact-production'
        
        # Get initial prompt
        initial_prompt = next(p for p in self.campaign_data['prompts'] if p['prompt_id'] == 'initial_setup')
        
        # Create campaign with exact production settings
        campaign_data = {
            'prompt': initial_prompt['input'],
            'title': 'Sariel Exact Production Test',
            'selected_prompts': ['narrative', 'mechanics', 'calibration'],
            'custom_options': ['companions', 'defaultWorld', 'destinySystem']
        }
        
        print(f"\nCreating campaign with prompt: {initial_prompt['input']}")
        
        response = self.client.post(
            '/api/campaigns',
            headers=IntegrationTestSetup.create_test_headers(user_id),
            data=json.dumps(campaign_data),
            content_type='application/json'
        )
        
        print(f"Campaign creation response status: {response.status_code}")
        self.assertEqual(response.status_code, 201)
        campaign_id = response.get_json()['campaign_id']
        print(f"Campaign ID: {campaign_id}")
        
        # Check initial game state
        state_response = self.client.get(
            f'/api/campaigns/{campaign_id}/state',
            headers=IntegrationTestSetup.create_test_headers(user_id)
        )
        
        if state_response.status_code == 200:
            initial_state = state_response.get_json()
            print("\n=== INITIAL GAME STATE ===")
            initial_counts = self.count_entity_fields(initial_state)
            print(f"Total fields: {initial_counts['total_all']}")
            print(f"Player character: {initial_counts['player_character']['total_entities']} entities")
            print(f"NPCs: {initial_counts['npcs']['total_entities']} entities")
        
        # Run provided interactions
        provided_prompts = [p for p in self.campaign_data['prompts'] if p['prompt_id'] != 'initial_setup']
        
        for i, prompt_data in enumerate(provided_prompts):
            print(f"\n{'='*80}")
            print(f"INTERACTION {i+1}: {prompt_data['input']}")
            
            interaction_data = {
                'input': prompt_data['input'],
                'mode': prompt_data['mode']
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
                
                # Debug: print first 500 chars of narrative
                print(f"\nNarrative preview: {narrative[:500]}...")
                
                # Check if STATE_UPDATES_PROPOSED was generated
                has_state_updates = '[STATE_UPDATES_PROPOSED]' in narrative or '🔧 STATE UPDATES PROPOSED:' in narrative
                print(f"STATE_UPDATES_PROPOSED generated: {has_state_updates}")
                
                # Extract available choices for next interaction
                choices = self.extract_choice_options(narrative)
                if choices:
                    print(f"Available choices: {choices}")
            
            # Get updated game state
            state_response = self.client.get(
                f'/api/campaigns/{campaign_id}/state',
                headers=IntegrationTestSetup.create_test_headers(user_id)
            )
            
            if state_response.status_code == 200:
                game_state = state_response.get_json()
                field_counts = self.count_entity_fields(game_state)
                print(f"\nGame state after interaction {i+1}:")
                print(f"- Total fields: {field_counts['total_all']}")
                print(f"- Player character fields: {field_counts['player_character']['total_fields']}")
                print(f"- NPC count: {field_counts['npcs']['total_entities']}")
                print(f"- NPC total fields: {field_counts['npcs']['total_fields']}")
        
        # Continue with choice 1 for additional interactions
        print(f"\n{'='*80}")
        print("CONTINUING WITH CHOICE 1 STRATEGY")
        print("="*80)
        
        for i in range(5):  # Do 5 more interactions
            # Always pick first choice from the last narrative
            if choices and len(choices) > 0:
                next_input = choices[0]
            else:
                next_input = "1"  # Fallback to "1" if no choices found
            
            print(f"\n{'='*80}")
            print(f"AUTO-INTERACTION {len(provided_prompts) + i + 1}: {next_input}")
            
            interaction_data = {
                'input': next_input,
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
                
                # Debug: print first 500 chars of narrative
                print(f"\nNarrative preview: {narrative[:500]}...")
                
                # Check state updates
                has_state_updates = '[STATE_UPDATES_PROPOSED]' in narrative or '🔧 STATE UPDATES PROPOSED:' in narrative
                print(f"STATE_UPDATES_PROPOSED generated: {has_state_updates}")
                
                # Extract next choices
                choices = self.extract_choice_options(narrative)
                if choices:
                    print(f"Available choices: {choices}")
            
            # Check final state
            state_response = self.client.get(
                f'/api/campaigns/{campaign_id}/state',
                headers=IntegrationTestSetup.create_test_headers(user_id)
            )
            
            if state_response.status_code == 200:
                game_state = state_response.get_json()
                field_counts = self.count_entity_fields(game_state)
                print(f"\nGame state after auto-interaction {len(provided_prompts) + i + 1}:")
                print(f"- Total fields: {field_counts['total_all']}")
                print(f"- Success: {'YES' if field_counts['total_all'] > 0 else 'NO'}")

if __name__ == '__main__':
    unittest.main()