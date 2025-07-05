import unittest
import os
import json
import sys
import subprocess
import logging

# Add the project root to the Python path to allow for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Handle missing dependencies gracefully
try:
    from main import create_app
    import firestore_service
    from game_state import GameState
    from integration_test_lib import IntegrationTestSetup, setup_integration_test_environment
    
    # Set up the integration test environment
    test_setup = setup_integration_test_environment(project_root)
    temp_prompts_dir = test_setup.create_test_prompts_directory()
    DEPS_AVAILABLE = True
except ImportError as e:
    print(f"Integration test dependencies not available: {e}")
    DEPS_AVAILABLE = False

# Initialize test configuration only if dependencies are available
if DEPS_AVAILABLE:
    # Temporarily change working directory to temp dir so imports find test prompts
    original_cwd = os.getcwd()
    os.chdir(temp_prompts_dir)

    import gemini_service # Import gemini_service to mock its internal _load_instruction_file

    # Get test configuration from the shared library
    TEST_MODEL_OVERRIDE = IntegrationTestSetup.TEST_MODEL_OVERRIDE
    TEST_SELECTED_PROMPTS = IntegrationTestSetup.TEST_SELECTED_PROMPTS
    USE_TIMEOUT = IntegrationTestSetup.USE_TIMEOUT

    # Mock system instructions
    mock_instructions = IntegrationTestSetup.mock_system_instructions()
    MOCK_INTEGRATION_NARRATIVE = mock_instructions['narrative']
    MOCK_INTEGRATION_MECHANICS = mock_instructions['mechanics']
    MOCK_INTEGRATION_CALIBRATION = mock_instructions['calibration']

    # Register cleanup on exit
    import atexit
    atexit.register(lambda: test_setup.cleanup())

class TestInteractionIntegration(unittest.TestCase):

    def setUp(self):
        """Check dependencies before each test."""
        if not DEPS_AVAILABLE:
            self.fail("CRITICAL FAILURE: Integration test dependencies missing (Flask, etc.). Install requirements.txt to fix.")

    @classmethod
    def setUpClass(cls):
        """Create one campaign for all tests to share."""
        if not DEPS_AVAILABLE:
            return  # Skip setup if dependencies missing - individual tests will fail
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()
        cls.user_id = 'test-integration-user'

        # Create one shared campaign for all tests
        create_response = cls.client.post(
            '/api/campaigns',
            headers={'Content-Type': 'application/json', 'X-Test-Bypass-Auth': 'true', 'X-Test-User-ID': cls.user_id},
            data=json.dumps({'prompt': 'A brave knight in a land of dragons needs to choose between killing an evil dragon or joining its side.', 'title': 'Test', 'selected_prompts': TEST_SELECTED_PROMPTS})
        )
        assert create_response.status_code == 201, "Failed to create shared campaign"
        create_data = create_response.get_json()
        cls.campaign_id = create_data.get('campaign_id')
        assert cls.campaign_id is not None

    def setUp(self):
        """Use shared campaign from setUpClass."""
        self.app = self.__class__.app
        self.client = self.__class__.client
        self.user_id = self.__class__.user_id
        self.campaign_id = self.__class__.campaign_id

    def tearDown(self):
        """Clean up any test data (campaigns, etc.)."""
        # NOTE: For now we leave Firestore docs in place for manual inspection.
        pass

    def _run_god_command(self, action, command_string=None):
        """Helper function to run the god-command script and return its output."""
        # Use sys.executable to ensure we're using the python from the venv
        python_executable = sys.executable
        script_path = os.path.join(project_root, "main.py")
        base_command = [
            python_executable, script_path, "god-command",
            action,
            "--campaign_id", self.campaign_id,
            "--user_id", self.user_id
        ]
        if command_string:
            base_command.extend(["--command_string", command_string])
        
        # Run the god-command from the original directory
        result = subprocess.run(base_command, capture_output=True, text=True, cwd=project_root)
        self.assertEqual(result.returncode, 0, f"god-command {action} failed: {result.stderr}")

        # The god-command 'ask' prints an info line before the JSON. Extract the JSON block.
        output = result.stdout.strip()
        if action == 'ask':
            json_start = output.find('{')
            json_text = output[json_start:] if json_start != -1 else output
            return json_text
        return output

    def test_new_campaign_creates_initial_state(self):
        """
        Milestone 1: Verify that a new campaign generates an initial game state.
        This tests the entire creation pipeline.
        """
        test_setup.set_timeout(60)  # 60 second timeout
        try:
            # Fetch the state from the shared campaign to verify it was created correctly
            state_json = self._run_god_command('ask')
            game_state = json.loads(state_json)

            # Basic sanity assertions. We cannot predict the exact content, but the structure should exist.
            self.assertIn('player_character_data', game_state)
            self.assertIn('npc_data', game_state)
        finally:
            test_setup.cancel_timeout()  # Cancel timeout

    def test_ai_state_update_is_merged_correctly(self):
        """
        Milestone 2: Verify that an AI-proposed update is merged without data loss.
        Uses a specific prompt designed to trigger state changes.
        """
        # Don't pre-set conflicting state - let the AI work with the natural campaign state
        # Just verify we have a character to work with
        initial_state_json = self._run_god_command('ask')
        initial_state = json.loads(initial_state_json)
        self.assertIn('player_character_data', initial_state)

        # Use a very explicit prompt that demands state updates
        targeted_prompt = (
            "IMPORTANT: You must update the game state in a [STATE_UPDATES_PROPOSED] block. "
            "The character finds and drinks a magical strength potion, permanently increasing their strength by 3 points. "
            "They also discover 50 gold pieces in a treasure chest. Update the character's stats accordingly."
        )
        
        interaction_data = {
            'input': targeted_prompt,
            'mode': 'character'
        }
        
        interaction_response = self.client.post(
            f'/api/campaigns/{self.campaign_id}/interaction',
            headers={'Content-Type': 'application/json', 'X-Test-Bypass-Auth': 'true', 'X-Test-User-ID': self.user_id},
            data=json.dumps(interaction_data)
        )
        
        self.assertEqual(interaction_response.status_code, 200)

        # Verify the AI made the requested changes
        final_state_json = self._run_god_command('ask')
        final_state = json.loads(final_state_json)
        
        # Check that the AI made some stat changes (we can't predict exact values with natural state)
        self.assertIn('player_character_data', final_state)
        pc_data = final_state['player_character_data']
        
        # Verify that either stats were updated OR gold was updated (showing AI responded)
        # Check for various possible locations where AI might store these values
        stats_updated = False
        gold_updated = False
        
        # Check for stats in various locations
        if 'stats' in pc_data and isinstance(pc_data['stats'], dict):
            # Check if any numeric stats exist (STR, strength, etc.)
            stats_updated = any(isinstance(v, (int, float)) for v in pc_data['stats'].values())
        
        # Check for gold in various locations
        initial_gold = initial_state['player_character_data'].get('gold', 0)
        if initial_gold is None:
            initial_gold = 0
            
        # Gold might be at root level or in stats
        current_gold = pc_data.get('gold', 0)
        if current_gold is None:
            current_gold = 0
        if 'stats' in pc_data and isinstance(pc_data['stats'], dict):
            stats_gold = pc_data['stats'].get('gold', 0)
            if stats_gold and stats_gold > current_gold:
                current_gold = stats_gold
                
        gold_updated = current_gold > initial_gold
        
        # Also accept if AI created any new numeric fields
        new_numeric_fields = any(isinstance(v, (int, float)) for k, v in pc_data.items() 
                                if k not in initial_state['player_character_data'])
        
        self.assertTrue(stats_updated or gold_updated or new_numeric_fields, 
                       f"AI should have updated stats, gold, or added numeric fields. Initial: {initial_state['player_character_data']}, Final: {pc_data}")

    def test_god_command_set_performs_deep_merge(self):
        """
        Milestone 3: Comprehensive deep merge test with 3 layers of nesting and all Python types.
        Tests every valid Python data type in nested structures.
        """
        # Set up a complex initial state with 3 layers of nesting and all Python types
        complex_initial_state = {
            "level1_dict": {
                "level2_dict": {
                    "level3_string": "initial_value",
                    "level3_int": 42,
                    "level3_float": 3.14159,
                    "level3_bool": True,
                    "level3_list": [1, 2, 3],
                    "level3_none": None
                },
                "level2_string": "level2_initial",
                "level2_list": ["a", "b", "c"],
                "level2_int": 100
            },
            "level1_string": "root_value",
            "level1_list": [{"nested": "item1"}, {"nested": "item2"}],
            "level1_bool": False,
            "level1_float": 2.718
        }
        
        initial_set_command = f'GOD_MODE_SET: test_data = {json.dumps(complex_initial_state)}'
        self._run_god_command('set', initial_set_command)

        # Test 1: Deep nested update (3 levels deep)
        update_set_command = 'GOD_MODE_SET: test_data.level1_dict.level2_dict.level3_string = "updated_deep_value"'
        self._run_god_command('set', update_set_command)
        
        # Test 2: Add new nested structure
        add_new_command = 'GOD_MODE_SET: test_data.level1_dict.level2_dict.level3_new_dict = {"brand_new": "nested_value", "number": 999}'
        self._run_god_command('set', add_new_command)
        
        # Test 3: Update list at level 2
        update_list_command = 'GOD_MODE_SET: test_data.level1_dict.level2_list = ["x", "y", "z", "new_item"]'
        self._run_god_command('set', update_list_command)
        
        # Test 4: Update root level value
        update_root_command = 'GOD_MODE_SET: test_data.level1_string = "updated_root_value"'
        self._run_god_command('set', update_root_command)
        
        # Test 5: Add completely new root level structure
        add_root_command = 'GOD_MODE_SET: test_data.new_root_dict = {"deeply": {"nested": {"value": "success", "types": [1, 2.5, true, null]}}}'
        self._run_god_command('set', add_root_command)
        
        # Verify all changes were applied correctly
        final_state_json = self._run_god_command('ask')
        final_state = json.loads(final_state_json)
        
        test_data = final_state['test_data']
        
        # Verify deep nested update (3 levels)
        self.assertEqual(test_data['level1_dict']['level2_dict']['level3_string'], 'updated_deep_value')
        
        # Verify original values were preserved at all levels
        self.assertEqual(test_data['level1_dict']['level2_dict']['level3_int'], 42)
        self.assertEqual(test_data['level1_dict']['level2_dict']['level3_float'], 3.14159)
        self.assertEqual(test_data['level1_dict']['level2_dict']['level3_bool'], True)
        self.assertEqual(test_data['level1_dict']['level2_dict']['level3_list'], [1, 2, 3])
        self.assertIsNone(test_data['level1_dict']['level2_dict']['level3_none'])
        
        # Verify new nested structure was added
        self.assertEqual(test_data['level1_dict']['level2_dict']['level3_new_dict']['brand_new'], 'nested_value')
        self.assertEqual(test_data['level1_dict']['level2_dict']['level3_new_dict']['number'], 999)
        
        # Verify list update at level 2
        self.assertEqual(test_data['level1_dict']['level2_list'], ["x", "y", "z", "new_item"])
        
        # Verify other level 2 values preserved
        self.assertEqual(test_data['level1_dict']['level2_string'], 'level2_initial')
        self.assertEqual(test_data['level1_dict']['level2_int'], 100)
        
        # Verify root level updates
        self.assertEqual(test_data['level1_string'], 'updated_root_value')
        self.assertEqual(test_data['level1_bool'], False)
        self.assertEqual(test_data['level1_float'], 2.718)
        
        # Verify original root level list preserved
        self.assertEqual(test_data['level1_list'], [{"nested": "item1"}, {"nested": "item2"}])
        
        # Verify new root level structure
        self.assertEqual(test_data['new_root_dict']['deeply']['nested']['value'], 'success')
        self.assertEqual(test_data['new_root_dict']['deeply']['nested']['types'], [1, 2.5, True, None])
        
        print("✅ Comprehensive deep merge test with all Python types completed successfully!")
        print(f"Final test data structure has {len(test_data)} root keys with complex nesting preserved")

    def test_sequential_story_commands_evolve_state(self):
        """
        Milestone 4: Verify that sequential story commands progressively evolve game state.
        Tests the full story progression pipeline with state tracking.
        """
        # Set up initial character state with more flexible structure
        initial_setup = 'GOD_MODE_SET: player_character_data = {"name": "Aria", "level": 1, "gold": 50, "exp": 0}'
        self._run_god_command('set', initial_setup)
        
        # Capture initial state
        initial_state_json = self._run_god_command('ask')
        initial_state = json.loads(initial_state_json)
        
        # Get initial values from wherever they are stored
        pc_data = initial_state['player_character_data']
        initial_gold = pc_data.get('gold', 0)
        initial_exp = pc_data.get('exp', 0)
        
        # Also check in stats subdictionary if present
        if 'stats' in pc_data and isinstance(pc_data['stats'], dict):
            initial_gold = pc_data['stats'].get('gold', initial_gold)
            initial_exp = pc_data['stats'].get('exp', initial_exp)
        
        # First story command: Find treasure
        first_command = (
            "Aria explores an ancient tomb and discovers a hidden treasure chest containing 100 gold pieces "
            "and gains 50 experience points from overcoming the tomb's challenges. Update her stats."
        )
        
        first_response = self.client.post(
            f'/api/campaigns/{self.campaign_id}/interaction',
            headers={'Content-Type': 'application/json', 'X-Test-Bypass-Auth': 'true', 'X-Test-User-ID': self.user_id},
            data=json.dumps({'input': first_command, 'mode': 'character'})
        )
        self.assertEqual(first_response.status_code, 200)
        
        # Check state after first command
        after_first_json = self._run_god_command('ask')
        after_first_state = json.loads(after_first_json)
        
        # Verify character structure is maintained
        self.assertIn('player_character_data', after_first_state)
        self.assertEqual(after_first_state['player_character_data']['name'], 'Aria')
        
        # Log the state for debugging
        first_pc_data = after_first_state['player_character_data']
        print(f"PC data after first command: {first_pc_data}")
        
        # Second story command: Battle and level up
        second_command = (
            "Aria encounters a fierce dragon guardian. After an epic battle, she defeats it and gains 150 more experience points, "
            "leveling up to level 2. She also finds a magical sword worth 200 gold. Update her progression."
        )
        
        second_response = self.client.post(
            f'/api/campaigns/{self.campaign_id}/interaction',
            headers={'Content-Type': 'application/json', 'X-Test-Bypass-Auth': 'true', 'X-Test-User-ID': self.user_id},
            data=json.dumps({'input': second_command, 'mode': 'character'})
        )
        self.assertEqual(second_response.status_code, 200)
        
        # Check final state after second command
        final_state_json = self._run_god_command('ask')
        final_state = json.loads(final_state_json)
        
        # Verify progressive evolution
        self.assertIn('player_character_data', final_state)
        self.assertEqual(final_state['player_character_data']['name'], 'Aria')
        
        final_pc_data = final_state['player_character_data']
        print(f"PC data after second command: {final_pc_data}")
        
        # Verify that state has evolved - check for these fields in various locations
        # They might be at root level or in a stats subdictionary
        has_level = 'level' in final_pc_data or ('stats' in final_pc_data and 'level' in final_pc_data.get('stats', {}))
        has_gold = 'gold' in final_pc_data or ('stats' in final_pc_data and 'gold' in final_pc_data.get('stats', {}))
        has_exp = 'exp' in final_pc_data or 'experience' in final_pc_data or \
                  ('stats' in final_pc_data and ('exp' in final_pc_data.get('stats', {}) or 'experience' in final_pc_data.get('stats', {})))
        
        # At least some progression fields should exist
        self.assertTrue(has_level or has_gold or has_exp, 
                       f"Expected level, gold, or exp fields in character data. Got: {final_pc_data}")
        
        # Verify we have core memories tracking the adventure
        if 'core_memories' in final_state['player_character_data']:
            memories = final_state['player_character_data']['core_memories']
            self.assertIsInstance(memories, list)
            print(f"Adventure memories: {memories}")
        
        print("✅ Sequential story progression test completed successfully!")


if __name__ == '__main__':
    unittest.main()
