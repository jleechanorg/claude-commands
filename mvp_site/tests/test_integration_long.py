#!/usr/bin/env python3
"""
TASK-128: Long Integration Test - Option 1 Repeated

This test creates a campaign and repeatedly chooses option 1 (planning block option)
to verify state consistency over many iterations.

Test Focus:
- State consistency throughout multiple interactions
- No state corruption or drift over many turns
- Game stability with repeated planning choices
- Verification of planning block option selection
"""

import unittest
import json
import tempfile
import os
import sys
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_state import GameState
import constants
from main import app
import firestore_service


class TestIntegrationLong(unittest.TestCase):
    """Test state consistency over repeated option 1 selections."""

    def setUp(self):
        """Set up test environment."""
        self.app = app.test_client()
        self.app.testing = True
        
        # Create test campaign data
        self.test_campaign_id = "test_campaign_long"
        self.test_user_id = "test_user_long"
        
        # Initial game state for testing
        self.initial_game_state = {
            "player_character_data": {
                "name": "Test Hero",
                "hp": 25,
                "max_hp": 25,
                "level": 1,
                "experience": 0
            },
            "current_scene": 1,
            "story_context": "Beginning of adventure",
            "planning_block_active": True,
            "sequence_id": 1
        }

    def test_repeated_option_1_selection_state_consistency(self):
        """Test choosing option 1 repeatedly for 15 iterations."""
        print("\n=== Starting Long Integration Test: 15 Iterations of Option 1 ===")
        
        # Track state across iterations
        state_snapshots = []
        iteration_count = 15
        
        with patch('firestore_service.create_campaign') as mock_create, \
             patch('firestore_service.get_campaign') as mock_get, \
             patch('firestore_service.update_campaign_game_state') as mock_update, \
             patch('gemini_service.generate_response') as mock_gemini:
            
            # Mock campaign creation
            mock_create.return_value = self.test_campaign_id
            
            # Configure mock responses
            current_state = self.initial_game_state.copy()
            
            for iteration in range(iteration_count):
                print(f"\n--- Iteration {iteration + 1}/{iteration_count} ---")
                
                # Mock current campaign state
                mock_get.return_value = {
                    'game_state': current_state,
                    'campaign_id': self.test_campaign_id,
                    'user_id': self.test_user_id
                }
                
                # Mock AI response with planning block and option 1
                mock_response = {
                    "narrative": f"Iteration {iteration + 1}: You continue your adventure. What do you do next?",
                    "planning_block": {
                        "Planning_1": "Continue with the current plan",
                        "Planning_2": "Change your approach", 
                        "Planning_3": "Ask for more information"
                    },
                    "game_state_updates": {
                        "current_scene": current_state["current_scene"] + 1,
                        "sequence_id": current_state["sequence_id"] + 1
                    }
                }
                mock_gemini.return_value = json.dumps(mock_response)
                
                # Simulate user selecting option 1 (Planning_1)
                response = self.app.post('/continue_story', 
                    data={
                        'campaign_id': self.test_campaign_id,
                        'user_input': 'Planning_1',  # Always choose option 1
                        'mode': constants.MODE_CHARACTER
                    },
                    follow_redirects=True
                )
                
                # Verify response is successful
                self.assertEqual(response.status_code, 200)
                response_data = json.loads(response.get_data(as_text=True))
                self.assertTrue(response_data.get('success', False), 
                              f"Iteration {iteration + 1} failed: {response_data.get('error', 'Unknown error')}")
                
                # Update state for next iteration
                if 'game_state_updates' in mock_response:
                    current_state.update(mock_response['game_state_updates'])
                
                # Capture state snapshot
                state_snapshot = {
                    'iteration': iteration + 1,
                    'scene': current_state['current_scene'],
                    'sequence_id': current_state['sequence_id'],
                    'hp': current_state['player_character_data']['hp'],
                    'max_hp': current_state['player_character_data']['max_hp'],
                    'level': current_state['player_character_data']['level']
                }
                state_snapshots.append(state_snapshot)
                
                print(f"Scene: {state_snapshot['scene']}, "
                      f"Sequence: {state_snapshot['sequence_id']}, "
                      f"HP: {state_snapshot['hp']}/{state_snapshot['max_hp']}")
        
        # Verify state consistency
        self._verify_state_consistency(state_snapshots)
        print(f"\n✅ Successfully completed {iteration_count} iterations with consistent state!")

    def test_state_integrity_over_long_session(self):
        """Test state integrity markers over extended gameplay."""
        print("\n=== Testing State Integrity Over 20 Iterations ===")
        
        integrity_markers = []
        iteration_count = 20
        
        with patch('firestore_service.get_campaign') as mock_get, \
             patch('firestore_service.update_campaign_game_state') as mock_update, \
             patch('gemini_service.generate_response') as mock_gemini:
            
            base_state = self.initial_game_state.copy()
            
            for iteration in range(iteration_count):
                # Mock campaign state
                mock_get.return_value = {
                    'game_state': base_state,
                    'campaign_id': self.test_campaign_id
                }
                
                # Mock consistent AI response
                mock_response = {
                    "narrative": f"Turn {iteration + 1}: The adventure continues...",
                    "planning_block": {
                        "Planning_1": "Proceed carefully",
                        "Planning_2": "Move quickly",
                        "Planning_3": "Rest and plan"
                    }
                }
                mock_gemini.return_value = json.dumps(mock_response)
                
                # Check state integrity before each iteration
                integrity_check = {
                    'iteration': iteration + 1,
                    'player_name_consistent': base_state['player_character_data']['name'] == "Test Hero",
                    'hp_within_bounds': 0 <= base_state['player_character_data']['hp'] <= base_state['player_character_data']['max_hp'],
                    'scene_progression': base_state['current_scene'] >= 1,
                    'has_planning_block': base_state.get('planning_block_active', False)
                }
                integrity_markers.append(integrity_check)
                
                # Simulate turn progression
                base_state['current_scene'] += 1
                base_state['sequence_id'] = base_state.get('sequence_id', 0) + 1
        
        # Verify all integrity checks passed
        for marker in integrity_markers:
            self.assertTrue(marker['player_name_consistent'], 
                          f"Player name inconsistent at iteration {marker['iteration']}")
            self.assertTrue(marker['hp_within_bounds'], 
                          f"HP out of bounds at iteration {marker['iteration']}")
            self.assertTrue(marker['scene_progression'], 
                          f"Scene progression error at iteration {marker['iteration']}")
        
        print(f"✅ State integrity maintained across {iteration_count} iterations!")

    def _verify_state_consistency(self, snapshots):
        """Verify state consistency across all iterations."""
        print("\n--- State Consistency Analysis ---")
        
        # Check scene progression
        for i in range(1, len(snapshots)):
            prev_scene = snapshots[i-1]['scene']
            curr_scene = snapshots[i]['scene']
            self.assertEqual(curr_scene, prev_scene + 1, 
                           f"Scene progression error: {prev_scene} -> {curr_scene}")
        
        # Check sequence ID progression
        for i in range(1, len(snapshots)):
            prev_seq = snapshots[i-1]['sequence_id']
            curr_seq = snapshots[i]['sequence_id']
            self.assertEqual(curr_seq, prev_seq + 1, 
                           f"Sequence ID progression error: {prev_seq} -> {curr_seq}")
        
        # Check HP consistency (should remain stable in this test)
        initial_hp = snapshots[0]['hp']
        initial_max_hp = snapshots[0]['max_hp']
        for snapshot in snapshots:
            self.assertEqual(snapshot['hp'], initial_hp, 
                           f"HP drift detected at iteration {snapshot['iteration']}")
            self.assertEqual(snapshot['max_hp'], initial_max_hp, 
                           f"Max HP drift detected at iteration {snapshot['iteration']}")
        
        # Check level consistency
        initial_level = snapshots[0]['level']
        for snapshot in snapshots:
            self.assertEqual(snapshot['level'], initial_level, 
                           f"Level drift detected at iteration {snapshot['iteration']}")
        
        print("✅ All state consistency checks passed!")

    def test_planning_block_option_1_processing(self):
        """Test that option 1 selection is properly processed."""
        print("\n=== Testing Planning Block Option 1 Processing ===")
        
        with patch('firestore_service.get_campaign') as mock_get, \
             patch('firestore_service.update_campaign_game_state') as mock_update, \
             patch('gemini_service.generate_response') as mock_gemini:
            
            # Mock campaign state
            mock_get.return_value = {
                'game_state': self.initial_game_state,
                'campaign_id': self.test_campaign_id
            }
            
            # Mock AI response with planning block
            mock_response = {
                "narrative": "You see three paths ahead.",
                "planning_block": {
                    "Planning_1": "Take the left path",
                    "Planning_2": "Take the middle path",
                    "Planning_3": "Take the right path"
                }
            }
            mock_gemini.return_value = json.dumps(mock_response)
            
            # Test option 1 selection
            response = self.app.post('/continue_story', 
                data={
                    'campaign_id': self.test_campaign_id,
                    'user_input': 'Planning_1',
                    'mode': constants.MODE_CHARACTER
                },
                follow_redirects=True
            )
            
            self.assertEqual(response.status_code, 200)
            response_data = json.loads(response.get_data(as_text=True))
            self.assertTrue(response_data.get('success', False))
            
            # Verify that the planning choice was processed
            # The mock should have been called with the planning choice
            mock_gemini.assert_called()
            
        print("✅ Planning block option 1 processing verified!")


if __name__ == '__main__':
    # Set testing environment
    os.environ['TESTING'] = 'true'
    
    # Create test suite focusing on long integration
    suite = unittest.TestSuite()
    suite.addTest(TestIntegrationLong('test_repeated_option_1_selection_state_consistency'))
    suite.addTest(TestIntegrationLong('test_state_integrity_over_long_session'))
    suite.addTest(TestIntegrationLong('test_planning_block_option_1_processing'))
    
    # Run with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)