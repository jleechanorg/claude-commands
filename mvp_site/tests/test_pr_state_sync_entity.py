#!/usr/bin/env python3
"""
Comprehensive test suite for state_sync_entity PR changes.
Tests entity schema integration, debug mode changes, resource tracking, and manifest cache.
"""

import unittest
import json
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock, call

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_state import GameState
from entity_tracking import create_from_game_state, SceneManifest, EntityStatus, Visibility
import gemini_service
import constants


class TestEntitySchemaIntegration(unittest.TestCase):
    """Test entity schema integration and ID standardization"""
    
    def test_entity_tracking_wrapper_exists(self):
        """Test that entity_tracking.py properly wraps schemas implementation"""
        # Create test game state
        game_state = {
            'player_character_data': {
                'name': 'Test Hero',
                'string_id': 'pc_testhero_001'
            },
            'npc_data': {}
        }
        
        # Test wrapper function
        manifest = create_from_game_state(game_state, session_number=1, turn_number=1)
        self.assertIsInstance(manifest, SceneManifest)
        self.assertEqual(manifest.session_number, 1)
        self.assertEqual(manifest.turn_number, 1)
    
    def test_entity_id_format_standardization(self):
        """Test that entity IDs follow underscore format"""
        game_state = {
            'player_character_data': {
                'name': 'Test Hero'
                # Note: no string_id provided
            },
            'npc_data': {
                'Guard Captain': {
                    'name': 'Guard Captain',
                    'hp_current': 40,
                    'hp_max': 40
                }
            }
        }
        
        manifest = create_from_game_state(game_state, 1, 1)
        
        # Check PC ID format
        self.assertEqual(len(manifest.player_characters), 1)
        pc = manifest.player_characters[0]
        self.assertRegex(pc.entity_id, r'^pc_[a-z_]+_\d{3}$')
        self.assertIn('test_hero', pc.entity_id.lower())
        
        # Check NPC ID format
        self.assertEqual(len(manifest.npcs), 1)
        npc = manifest.npcs[0]
        self.assertRegex(npc.entity_id, r'^npc_[a-z_]+_\d{3}$')
        self.assertIn('guard_captain', npc.entity_id.lower())
    
    def test_entity_schema_loaded_in_gemini_service(self):
        """Test that entity schema instructions are loaded in both story functions"""
        with patch.object(gemini_service, '_load_instruction_file') as mock_load:
            mock_load.return_value = "test instruction content"
            
            # Test get_initial_story
            with patch.object(gemini_service, 'get_client') as mock_get_client:
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.text = "Test story"
                mock_client.models.generate_content.return_value = mock_response
                mock_get_client.return_value = mock_client
                
                gemini_service.get_initial_story("Test prompt", selected_prompts=['narrative'])
                
                # Verify entity schema was loaded
                load_calls = mock_load.call_args_list
                entity_schema_calls = [call for call in load_calls 
                                     if call[0][0] == constants.PROMPT_TYPE_ENTITY_SCHEMA]
                self.assertEqual(len(entity_schema_calls), 1)
            
            mock_load.reset_mock()
            
            # Test continue_story
            with patch.object(gemini_service, 'get_client') as mock_get_client:
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.text = "This is a long enough test response for narrative validation to pass without errors."
                mock_client.models.generate_content.return_value = mock_response
                mock_get_client.return_value = mock_client
                
                test_game_state = GameState()
                gemini_service.continue_story(
                    "Test input", 
                    "character",
                    [], 
                    test_game_state,
                    selected_prompts=['narrative']
                )
                
                # Verify entity schema was loaded
                load_calls = mock_load.call_args_list
                entity_schema_calls = [call for call in load_calls 
                                     if call[0][0] == constants.PROMPT_TYPE_ENTITY_SCHEMA]
                self.assertEqual(len(entity_schema_calls), 1)


class TestDebugModeDefaults(unittest.TestCase):
    """Test debug mode default changes"""
    
    def test_game_state_defaults_to_debug_true(self):
        """Test that GameState now defaults to debug_mode=True"""
        gs = GameState()
        self.assertTrue(gs.debug_mode)
    
    def test_game_state_respects_explicit_debug_false(self):
        """Test that debug_mode can still be set to False explicitly"""
        gs = GameState(debug_mode=False)
        self.assertFalse(gs.debug_mode)
    
    def test_debug_mode_serialization(self):
        """Test that debug_mode is properly serialized"""
        gs = GameState(debug_mode=True)
        data = gs.to_dict()
        self.assertIn('debug_mode', data)
        self.assertTrue(data['debug_mode'])
        
        # Test deserialization
        gs2 = GameState.from_dict(data)
        self.assertTrue(gs2.debug_mode)


class TestResourceTracking(unittest.TestCase):
    """Test resource tracking in debug output"""
    
    def test_debug_resources_format_in_instructions(self):
        """Test that debug instructions include resource tracking format"""
        # Load actual debug instructions from continue_story
        with patch.object(gemini_service, 'get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "This is a long enough test response for narrative validation to pass without errors."
            mock_client.models.generate_content.return_value = mock_response
            mock_get_client.return_value = mock_client
            
            # Capture the actual prompt sent
            test_game_state = GameState()
            gemini_service.continue_story(
                "Test input",
                "character",
                [],
                test_game_state,
                selected_prompts=['narrative']
            )
            
            # Get the system instruction from the call (where debug instructions are)
            call_args = mock_client.models.generate_content.call_args
            system_instruction = call_args[1]['config'].system_instruction.text
            
            # Verify resource tracking instructions are present
            self.assertIn('DEBUG_RESOURCES_START', system_instruction)
            self.assertIn('DEBUG_RESOURCES_END', system_instruction)
            self.assertIn('EP used', system_instruction)
            self.assertIn('spell slots', system_instruction)
            self.assertIn('short rests', system_instruction)
    
    def test_resource_examples_in_debug_instructions(self):
        """Test that debug instructions include proper resource examples"""
        with patch.object(gemini_service, '_load_instruction_file') as mock_load:
            mock_load.return_value = "test content"
            with patch.object(gemini_service, 'get_client') as mock_get_client:
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.text = "This is a long enough test response for narrative validation to pass without errors."
                mock_client.models.generate_content.return_value = mock_response
                mock_get_client.return_value = mock_client
                
                # Call continue_story to get the actual prompt
                test_game_state = GameState()
                gemini_service.continue_story(
                    "Test input",
                    "character",
                    [],
                    test_game_state,
                    selected_prompts=['narrative']
                )
                
                # Get the system instruction from the call (where debug instructions are)
                call_args = mock_client.models.generate_content.call_args
                # System instruction is in config.system_instruction.text
                system_instruction = call_args[1]['config'].system_instruction.text
                debug_text = str(system_instruction)
                
                # Look for resource example patterns
                self.assertIn('Resources: 2 EP used (6/8 remaining)', debug_text)
                self.assertIn('DEBUG_RESOURCES_START', debug_text)
                self.assertIn('DEBUG_RESOURCES_END', debug_text)


class TestManifestCacheExclusion(unittest.TestCase):
    """Test that manifest cache is excluded from serialization"""
    
    def test_underscore_attributes_excluded_from_serialization(self):
        """Test that attributes starting with _ are excluded from to_dict()"""
        gs = GameState()
        
        # Add some underscore attributes
        gs._test_cache = "should not serialize"
        gs._another_cache = {"data": "private"}
        
        # Serialize
        data = gs.to_dict()
        
        # Verify underscore attributes are excluded
        self.assertNotIn('_test_cache', data)
        self.assertNotIn('_another_cache', data)
        
        # Verify normal attributes are included
        self.assertIn('game_state_version', data)
        self.assertIn('player_character_data', data)
    
    def test_manifest_cache_exclusion(self):
        """Test specific manifest cache exclusion"""
        gs = GameState()
        
        # Simulate adding a manifest cache
        gs._manifest_cache = MagicMock()
        gs._manifest_cache.to_dict.return_value = {"should": "not appear"}
        
        # Serialize
        data = gs.to_dict()
        
        # Verify manifest cache is excluded
        self.assertNotIn('_manifest_cache', data)
        self.assertNotIn('manifest_cache', data)
        
        # Verify serialization doesn't error
        json_str = json.dumps(data, default=str)
        self.assertIsInstance(json_str, str)


class TestEntityStringIdPreservation(unittest.TestCase):
    """Test that existing string_ids are preserved"""
    
    def test_existing_string_ids_preserved(self):
        """Test that schemas respect existing string_ids from game state"""
        game_state = {
            'player_character_data': {
                'name': 'Hero',
                'string_id': 'pc_custom_id_999'  # Non-standard ID
            },
            'npc_data': {
                'Villain': {
                    'name': 'Villain',
                    'string_id': 'npc_special_villain_042'  # Custom ID
                }
            }
        }
        
        manifest = create_from_game_state(game_state, 1, 1)
        
        # Verify IDs are preserved
        self.assertEqual(manifest.player_characters[0].entity_id, 'pc_custom_id_999')
        self.assertEqual(manifest.npcs[0].entity_id, 'npc_special_villain_042')


class TestEntitySchemaPathConstant(unittest.TestCase):
    """Test that PROMPT_TYPE_ENTITY_SCHEMA constant exists and is used"""
    
    def test_entity_schema_constant_exists(self):
        """Test that the entity schema constant is defined"""
        self.assertTrue(hasattr(constants, 'PROMPT_TYPE_ENTITY_SCHEMA'))
        self.assertIsInstance(constants.PROMPT_TYPE_ENTITY_SCHEMA, str)
    
    def test_entity_schema_path_exists_in_path_map(self):
        """Test that entity schema path is properly mapped"""
        self.assertIn(constants.PROMPT_TYPE_ENTITY_SCHEMA, gemini_service.PATH_MAP)
        
        # Verify the file exists
        path = gemini_service.PATH_MAP[constants.PROMPT_TYPE_ENTITY_SCHEMA]
        full_path = os.path.join(os.path.dirname(gemini_service.__file__), path)
        self.assertTrue(os.path.exists(full_path), 
                       f"Entity schema file not found at {full_path}")


if __name__ == '__main__':
    unittest.main()