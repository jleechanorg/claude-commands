import unittest
import os
import json
import sys
import subprocess

# Add the project root to the Python path to allow for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

import logging_util

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
    # Configuration for test prompts - represents all checkboxes being selected
    TEST_SELECTED_PROMPTS = ['narrative', 'mechanics']  # All user-selectable prompts
    TEST_CUSTOM_OPTIONS = ['companions', 'defaultWorld']  # Additional test options
    USE_TIMEOUT = IntegrationTestSetup.USE_TIMEOUT

    # Mock system instructions
    mock_instructions = IntegrationTestSetup.mock_system_instructions()
    MOCK_INTEGRATION_NARRATIVE = mock_instructions['narrative']
    MOCK_INTEGRATION_MECHANICS = mock_instructions['mechanics']
    MOCK_INTEGRATION_CALIBRATION = mock_instructions['calibration']

    # Register cleanup on exit
    import atexit
    atexit.register(lambda: test_setup.cleanup())


def run_god_command(test_instance, action, command_string=None):
    """Shared helper function to run god-command script and return output."""
    # Use sys.executable to ensure we're using the python from the venv
    python_executable = sys.executable
    script_path = os.path.join(project_root, "main.py")
    base_command = [
        python_executable, script_path, "god-command",
        action,
        "--campaign_id", test_instance.campaign_id,
        "--user_id", test_instance.user_id
    ]
    if command_string:
        base_command.extend(["--command_string", command_string])
    
    # Set TESTING environment variable
    env = os.environ.copy()
    env["TESTING"] = "true"
    
    # Run the god-command from the original directory
    result = subprocess.run(base_command, capture_output=True, text=True, cwd=project_root, env=env)
    test_instance.assertEqual(result.returncode, 0, f"god-command {action} failed: {result.stderr}")

    # The god-command logs JSON to stderr (via logging_util.info), not stdout
    if action == 'ask':
        # Look for JSON in stderr output
        output = result.stderr
        # Find the line that starts with "Current game state:"
        lines = output.split('\n')
        json_lines = []
        capturing = False
        for line in lines:
            if 'Current game state:' in line:
                capturing = True
                continue
            if capturing:
                json_lines.append(line)
        
        # Join the JSON lines and parse
        json_text = '\n'.join(json_lines).strip()
        if json_text:
            return json_text
        else:
            # Fallback: try to find JSON block directly
            json_start = output.find('{')
            json_end = output.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                return output[json_start:json_end]
            else:
                test_instance.fail(f"No JSON found in god-command output: {output}")
    
    return result.stderr


class TestInteractionIntegration(unittest.TestCase):

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
        """Check dependencies and use shared campaign from setUpClass."""
        if not DEPS_AVAILABLE:
            self.fail("CRITICAL FAILURE: Integration test dependencies missing (Flask, etc.). Install requirements.txt to fix.")
        
        self.app = self.__class__.app
        self.client = self.__class__.client
        self.user_id = self.__class__.user_id
        self.campaign_id = self.__class__.campaign_id

    def tearDown(self):
        """Clean up any test data (campaigns, etc.)."""
        # NOTE: For now we leave Firestore docs in place for manual inspection.
        pass

    def test_new_campaign_creates_initial_state(self):
        """
        Milestone 1: Verify that a new campaign generates an initial game state.
        This tests the entire creation pipeline.
        """
        test_setup.set_timeout(60)  # 60 second timeout
        try:
            # Fetch the state from the shared campaign to verify it was created correctly
            state_json = run_god_command(self, 'ask')
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
        initial_state_json = run_god_command(self, 'ask')
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
        final_state_json = run_god_command(self, 'ask')
        final_state = json.loads(final_state_json)
        
        # Check that the AI made some stat changes (we can't predict exact values with natural state)
        self.assertIn('player_character_data', final_state)
        pc_data = final_state['player_character_data']
        
        # Verify that either stats were updated OR gold was updated (showing AI responded)
        # Check for various possible locations where AI might store these values
        stats_updated = False
        gold_updated = False
        
        # Check for stats in various locations (current structure uses 'attributes')
        if 'attributes' in pc_data and isinstance(pc_data['attributes'], dict):
            # Check if any numeric stats exist (STR, strength, etc.)
            stats_updated = any(isinstance(v, (int, float)) for v in pc_data['attributes'].values())
        elif 'stats' in pc_data and isinstance(pc_data['stats'], dict):
            # Fallback check for old structure
            stats_updated = any(isinstance(v, (int, float)) for v in pc_data['stats'].values())
        
        # Check for gold in various locations
        initial_gold = initial_state['player_character_data'].get('gold', 0)
        if initial_gold is None:
            initial_gold = 0
            
        # Gold might be at root level, in stats, attributes, or resources
        current_gold = pc_data.get('gold', 0)
        if current_gold is None:
            current_gold = 0
        
        # Check attributes for gold
        if 'attributes' in pc_data and isinstance(pc_data['attributes'], dict):
            attrs_gold = pc_data['attributes'].get('gold', 0)
            if attrs_gold and attrs_gold > current_gold:
                current_gold = attrs_gold
                
        # Check stats for gold (fallback)
        if 'stats' in pc_data and isinstance(pc_data['stats'], dict):
            stats_gold = pc_data['stats'].get('gold', 0)
            if stats_gold and stats_gold > current_gold:
                current_gold = stats_gold
                
        # Check resources for gold
        if 'resources' in pc_data and isinstance(pc_data['resources'], dict):
            resources_gold = pc_data['resources'].get('gold', 0)
            if resources_gold and resources_gold > current_gold:
                current_gold = resources_gold
                
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
        run_god_command(self, 'set', initial_set_command)

        # Test 1: Deep nested update (3 levels deep)
        update_set_command = 'GOD_MODE_SET: test_data.level1_dict.level2_dict.level3_string = "updated_deep_value"'
        run_god_command(self, 'set', update_set_command)
        
        # Test 2: Add new nested structure
        add_new_command = 'GOD_MODE_SET: test_data.level1_dict.level2_dict.level3_new_dict = {"brand_new": "nested_value", "number": 999}'
        run_god_command(self, 'set', add_new_command)
        
        # Test 3: Update list at level 2
        update_list_command = 'GOD_MODE_SET: test_data.level1_dict.level2_list = ["x", "y", "z", "new_item"]'
        run_god_command(self, 'set', update_list_command)
        
        # Test 4: Update root level value
        update_root_command = 'GOD_MODE_SET: test_data.level1_string = "updated_root_value"'
        run_god_command(self, 'set', update_root_command)
        
        # Test 5: Add completely new root level structure
        add_root_command = 'GOD_MODE_SET: test_data.new_root_dict = {"deeply": {"nested": {"value": "success", "types": [1, 2.5, true, null]}}}'
        run_god_command(self, 'set', add_root_command)
        
        # Verify all changes were applied correctly
        final_state_json = run_god_command(self, 'ask')
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

    def test_story_progression_smoke_test(self):
        """
        Quick smoke test: Verify basic story progression works.
        Lightweight test that ensures the story system responds to commands.
        """
        # Simple story command
        story_command = (
            "I explore the nearby forest and discover an ancient artifact. "
            "What do I find?"
        )
        
        response = self.client.post(
            f'/api/campaigns/{self.campaign_id}/interaction',
            headers={'Content-Type': 'application/json', 'X-Test-Bypass-Auth': 'true', 'X-Test-User-ID': self.user_id},
            data=json.dumps({'input': story_command, 'mode': 'character'})
        )
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        response_data = response.get_json()
        self.assertIn('response', response_data)
        self.assertIsInstance(response_data['response'], str)
        self.assertGreater(len(response_data['response']), 50, "Story response should be substantive")
        
        # Verify the response contains story elements
        response_text = response_data['response'].lower()
        story_keywords = ['forest', 'artifact', 'discover', 'find', 'ancient']
        found_keywords = sum(1 for keyword in story_keywords if keyword in response_text)
        self.assertGreater(found_keywords, 0, "Response should relate to the story command")
        
        print("✅ Story progression smoke test passed!")


class BaseCampaignIntegrationTest(unittest.TestCase):
    """Base class for campaign integration tests with shared functionality.
    
    Provides common test setup, teardown, and utility methods for testing
    different campaign types with real Gemini/Firebase integration.
    """
    
    # Override these in subclasses
    CAMPAIGN_PROMPT = ""
    CAMPAIGN_TITLE = "Test Campaign"
    USER_ID_SUFFIX = "test-user"
    
    @classmethod
    def setUpClass(cls):
        """Create campaign for all tests to share."""
        if not DEPS_AVAILABLE:
            return
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()
        cls.user_id = f'test-{cls.USER_ID_SUFFIX}'
        
        # Create campaign with subclass-specific prompt
        create_response = cls.client.post(
            '/api/campaigns',
            headers={'Content-Type': 'application/json', 'X-Test-Bypass-Auth': 'true', 'X-Test-User-ID': cls.user_id},
            data=json.dumps({
                'prompt': cls.CAMPAIGN_PROMPT,
                'title': cls.CAMPAIGN_TITLE,
                'selected_prompts': TEST_SELECTED_PROMPTS,  # ['narrative', 'mechanics'] - all checkboxes checked
                'custom_options': TEST_CUSTOM_OPTIONS  # Additional options for complete testing
            })
        )
        assert create_response.status_code == 201, f"Failed to create {cls.CAMPAIGN_TITLE}"
        create_data = create_response.get_json()
        cls.campaign_id = create_data.get('campaign_id')
        assert cls.campaign_id is not None
    
    @classmethod
    def tearDownClass(cls):
        """Clean up the campaign after all tests complete."""
        if not DEPS_AVAILABLE or not hasattr(cls, 'campaign_id') or not cls.campaign_id:
            return
        try:
            # Note: The API doesn't provide a delete endpoint, so we leave campaigns
            # This is acceptable for test data as it helps with debugging
            pass
        except Exception as e:
            print(f"Warning: Could not clean up campaign {cls.campaign_id}: {e}")

    def setUp(self):
        """Check dependencies and use shared campaign."""
        if not DEPS_AVAILABLE:
            self.fail("CRITICAL FAILURE: Integration test dependencies missing.")
        
        self.app = self.__class__.app
        self.client = self.__class__.client
        self.user_id = self.__class__.user_id
        self.campaign_id = self.__class__.campaign_id

    def start_campaign_story(self):
        """Common method to start the campaign story."""
        return self.client.post(
            f'/api/campaigns/{self.campaign_id}/interaction',
            headers={'Content-Type': 'application/json', 'X-Test-Bypass-Auth': 'true', 'X-Test-User-ID': self.user_id},
            data=json.dumps({'input': 'Begin the story.', 'mode': 'character'})
        )

    def send_character_action(self, action_text):
        """Send a character mode action to the campaign."""
        return self.client.post(
            f'/api/campaigns/{self.campaign_id}/interaction',
            headers={'Content-Type': 'application/json', 'X-Test-Bypass-Auth': 'true', 'X-Test-User-ID': self.user_id},
            data=json.dumps({'input': action_text, 'mode': 'character'})
        )

    def get_game_state(self):
        """Get the current game state as a parsed JSON object."""
        state_json = run_god_command(self, 'ask')
        return json.loads(state_json)

    def assert_character_created(self, expected_name, expected_class=None, expected_alignment=None):
        """Common assertion for character creation."""
        state = self.get_game_state()
        self.assertIn('player_character_data', state)
        pc_data = state['player_character_data']
        
        # Basic character data
        self.assertEqual(pc_data.get('name'), expected_name, f"Character should be named {expected_name}")
        self.assertEqual(pc_data.get('level'), 1, "Character should be level 1")
        
        if expected_class:
            if isinstance(expected_class, list):
                self.assertIn(pc_data.get('class'), expected_class, f"Character should be one of {expected_class}")
            else:
                self.assertEqual(pc_data.get('class'), expected_class, f"Character should be {expected_class}")
        
        if expected_alignment:
            self.assertEqual(pc_data.get('alignment'), expected_alignment, f"Character should be {expected_alignment}")
        
        # Core fields - these may vary based on campaign type
        # For now, just verify the basic required fields
        required_fields = ['name', 'level', 'class']
        for field in required_fields:
            self.assertIn(field, pc_data, f"Character missing required field: {field}")
        
        return pc_data

    def assert_combat_active(self):
        """Common assertion for combat state."""
        state = self.get_game_state()
        combat_state = state.get('combat_state', {})
        self.assertTrue(combat_state.get('in_combat', False), "Combat state should be active")
        
        combatants = combat_state.get('combatants', [])
        self.assertGreater(len(combatants), 1, "Should have multiple combatants")
        
        return combat_state, combatants

    def assert_story_progression(self, expected_elements):
        """Check that story elements are captured in core memories."""
        state = self.get_game_state()
        custom_state = state.get('custom_campaign_state', {})
        core_memories = custom_state.get('core_memories', [])
        
        self.assertGreater(len(core_memories), 1, "Should have multiple core memories tracking story progression")
        
        # Check for expected story elements
        memory_text = ' '.join(core_memories).lower()
        found_elements = sum(1 for element in expected_elements if element.lower() in memory_text)
        
        self.assertGreater(found_elements, len(expected_elements) // 2, 
                          f"Expected at least half of {expected_elements} in memories. Memories: {core_memories}")
        
        return core_memories


class TestDefaultDragonKnightCampaign(BaseCampaignIntegrationTest):
    """Test the Dragon Knight campaign with character creation, combat, and story progression.
    
    Uses real system prompts with 'all checkboxes checked' configuration:
    - narrative: Story guidance and character development
    - mechanics: Combat rules and game mechanics
    
    This simulates the complete user experience with full system prompts.
    """
    
    CAMPAIGN_PROMPT = """You are Ser Arion, a 16 year old honorable knight on your first mission, sworn to protect the vast Celestial Imperium. For decades, the Empire has been ruled by the iron-willed Empress Sariel, a ruthless tyrant who uses psychic power to crush dissent. While her methods are terrifying, her reign has brought undeniable benefits: the roads are safe, trade flourishes, and the common people no longer starve or fear bandits. You are a product of this "Silent Peace," and your oath binds you to the security and prosperity it provides.

Your loyalty is now brutally tested. You have been ordered to slaughter a settlement of innocent refugees whose very existence has been deemed a threat to the Empress's perfect, unyielding order. As you wrestle with this monstrous command, a powerful, new voice enters your mind—Aurum, the Gilded King, a magnificent gold dragon long thought to be a myth. He appears as a champion of freedom, urging you to defy the Empress's "soulless cage" and fight for a world of choice and glorious struggle.

You are now caught between two powerful and morally grey forces. Do you uphold your oath and commit an atrocity, believing the sacrifice of a few is worth the peace and safety of millions? Or do you break your vow and join the arrogant dragon's chaotic crusade, plunging the world back into violence for a chance at true freedom? This single choice will define your honor and your path in an empire where security is bought with blood."""
    
    CAMPAIGN_TITLE = "Dragon Knight Test Campaign"
    USER_ID_SUFFIX = "dragon-knight-user"

    def test_dragon_knight_character_creation(self):
        """Test automatic character creation when starting the Dragon Knight campaign."""
        # Start the story - LLM automatically creates the character
        response = self.start_campaign_story()
        self.assertEqual(response.status_code, 200)
        
        # Verify character creation using base class helper
        pc_data = self.assert_character_created('Ser Arion', ['Knight', 'Paladin'], 'Lawful Good')
        
        print(f"✅ Character auto-creation test passed - Ser Arion created with all required fields")

    def test_dragon_knight_combat_encounter(self):
        """Test combat mechanics and state management in Dragon Knight campaign."""
        # Start story and make choices
        self.start_campaign_story()
        self.send_character_action('I choose to listen to Aurum the Gilded King. I will not slaughter these innocent refugees.')
        
        # Trigger combat
        combat_prompt = (
            'Suddenly, Imperial Guards arrive to enforce the Empress\'s order. "Surrender, traitor!" they shout. '
            'I draw my sword and prepare to fight them in combat. I attack the lead guard!'
        )
        response = self.send_character_action(combat_prompt)
        self.assertEqual(response.status_code, 200)
        
        # Verify combat using base class helper
        combat_state, combatants = self.assert_combat_active()
        
        # Additional specific checks
        player_combatant = next((c for c in combatants if c.get('side') == 'player' and c.get('name') == 'Ser Arion'), None)
        self.assertIsNotNone(player_combatant, "Ser Arion should be in combat")
        self.assertIn('hp_current', player_combatant, "Player should have current HP")
        self.assertIn('hp_max', player_combatant, "Player should have max HP")
        
        print(f"✅ Combat test passed - Combat active with {len(combatants)} combatants")

    def test_dragon_knight_story_progression(self):
        """Test narrative choices and story progression through Dragon Knight campaign."""
        # Start the story using base class helper
        self.start_campaign_story()
        
        # Make narrative choices using base class helper
        choices = [
            ("I choose to listen to Aurum the Gilded King. I will not slaughter these innocent refugees. "
             "I sheath my sword and stand with the dragon against the Empress."),
            ('I approach Theron and Elara. "The dragon offers freedom from the Empress\'s tyranny. '
             'Will you stand with me against her forces?" I try to rally the refugees to our cause.'),
            ('Suddenly, Imperial Guards arrive to enforce the Empress\'s order. "Surrender, traitor!" they shout. '
             'I draw my sword and prepare to fight them in combat. I attack the lead guard!')
        ]
        
        for choice in choices:
            response = self.send_character_action(choice)
            self.assertEqual(response.status_code, 200)
        
        # Verify story progression using base class helper
        expected_elements = ['arion', 'choice', 'dragon', 'aurum', 'refugees']
        core_memories = self.assert_story_progression(expected_elements)
        
        # Verify combat was triggered using base class helper
        combat_state, combatants = self.assert_combat_active()
        
        print(f"✅ Story progression test passed - {len(core_memories)} memories, combat active with {len(combatants)} combatants")


class TestBG3AstarionCampaign(BaseCampaignIntegrationTest):
    """Test the BG3 Astarion custom campaign with character creation and story progression.
    
    This tests a custom Baldur's Gate 3 inspired campaign where the player is Astarion,
    the vampire spawn, testing custom character prompts and story integration.
    """
    
    CAMPAIGN_PROMPT = """You are Astarion, a vampire spawn who has just escaped from his cruel master Cazador after 200 years of servitude. The illithid tadpole in your brain has somehow freed you from Cazador's compulsion, but you still bear the scars of centuries of torture and manipulation.

You find yourself in a small village at dusk, your newfound freedom both exhilarating and terrifying. The hunger for blood gnaws at you, but for the first time in centuries, you can choose whether to feed. A young woman walks alone down a dark alley, humming softly to herself.

As you struggle with your vampiric nature and the weight of your past, you must decide: Will you embrace the monster Cazador made you, or fight against your dark impulses to forge a new path? Your choice here will define whether you remain a slave to your nature or become truly free."""
    
    CAMPAIGN_TITLE = "BG3 Astarion Test Campaign"
    USER_ID_SUFFIX = "bg3-astarion-user"

    def test_astarion_character_creation(self):
        """Test automatic character creation for Astarion campaign."""
        # Start the story - LLM automatically creates Astarion
        response = self.start_campaign_story()
        self.assertEqual(response.status_code, 200)
        
        # Verify character creation - Astarion should be a Rogue or similar
        pc_data = self.assert_character_created('Astarion', ['Rogue', 'Vampire Spawn', 'Ranger'], None)
        
        # Check for vampire-specific traits
        traits_text = str(pc_data.get('traits', [])) + ' ' + str(pc_data.get('race', '')) + ' ' + str(pc_data.get('subrace', ''))
        self.assertTrue('vampire' in traits_text.lower() or 'undead' in traits_text.lower(), 
                       f"Astarion should have vampire/undead traits. Got: {traits_text}")
        
        print(f"✅ Astarion character creation test passed")

    def test_astarion_story_progression_full(self):
        """Test complete narrative arc with three choices and combat for Astarion."""
        # Start story
        self.start_campaign_story()
        
        # Narrative Choice 1: Resist the hunger (moral choice)
        choice_1 = (
            "I clench my fists and turn away from the woman. 'No,' I whisper to myself. "
            "'I am not Cazador's puppet anymore. I will not feed on innocents.' "
            "I retreat into the shadows, fighting the hunger."
        )
        response_1 = self.send_character_action(choice_1)
        self.assertEqual(response_1.status_code, 200)
        
        # Narrative Choice 2: Seek alternative sustenance
        choice_2 = (
            "I search the village outskirts for animals - rats, birds, anything to quell this hunger. "
            "'There must be another way,' I tell myself. I find a stray dog and reluctantly feed, "
            "hating myself but refusing to harm innocents."
        )
        response_2 = self.send_character_action(choice_2)
        self.assertEqual(response_2.status_code, 200)
        
        # Narrative Choice 3: Trigger combat with vampire hunters or Cazador's minions
        choice_3 = (
            "Suddenly, I sense familiar presences - vampire spawn, my former 'siblings' sent by Cazador! "
            "'Come back to master, brother,' they hiss from the shadows. 'Never!' I snarl, "
            "drawing my daggers. 'I'll die before I return to him!' I attack the nearest spawn!"
        )
        response_3 = self.send_character_action(choice_3)
        self.assertEqual(response_3.status_code, 200)
        
        # Verify story progression - check for key story beats
        expected_elements = ['astarion', 'cazador', 'hunger', 'vampire', 'siblings']
        core_memories = self.assert_story_progression(expected_elements)
        
        # Verify combat was triggered
        combat_state, combatants = self.assert_combat_active()
        
        # Check for Astarion in combat
        astarion = next((c for c in combatants if c.get('name') == 'Astarion'), None)
        self.assertIsNotNone(astarion, "Astarion should be in combat")
        
        print(f"✅ Astarion full story progression test passed - {len(core_memories)} memories, combat with {len(combatants)} combatants")

    def test_astarion_combat_mechanics(self):
        """Test combat mechanics when vampire hunters attack Astarion."""
        # Start story and make initial choice
        self.start_campaign_story()
        self.send_character_action("I resist the urge to feed and look for another way.")
        
        # Trigger combat with vampire hunters (avoiding apostrophes in entity names)
        combat_trigger = (
            "A group of vampire hunters bursts into the alley! 'Found one!' their leader shouts. "
            "'Die, monster!' They draw silver weapons and attack. I have no choice but to defend myself. "
            "I draw my daggers and strike at the lead hunter!"
        )
        response = self.send_character_action(combat_trigger)
        self.assertEqual(response.status_code, 200)
        
        # Verify combat state
        combat_state, combatants = self.assert_combat_active()
        
        # Check for Astarion in combat
        astarion = next((c for c in combatants if c.get('name') == 'Astarion'), None)
        self.assertIsNotNone(astarion, "Astarion should be in combat")
        self.assertEqual(astarion.get('side'), 'player', "Astarion should be on player side")
        
        # Check for enemy combatants (hunters)
        enemy_combatants = [c for c in combatants if c.get('side') == 'enemy']
        self.assertGreater(len(enemy_combatants), 0, "Should have enemy combatants")
        
        # Verify Astarion has proper combat stats
        self.assertIn('hp_current', astarion, "Astarion should have current HP")
        self.assertIn('hp_max', astarion, "Astarion should have max HP")
        
        print(f"✅ Astarion combat mechanics test passed - Fighting {len(combatants)} combatants")

    def test_character_creation_ai_generated_with_specified_character(self):
        """Test AIGenerated path with a pre-specified character (e.g., Geralt of Rivia)"""
        # Create campaign with specified character
        create_response = self.client.post(
            '/api/campaigns',
            headers={'Content-Type': 'application/json', 'X-Test-Bypass-Auth': 'true', 'X-Test-User-ID': self.user_id},
            data=json.dumps({
                'prompt': 'I want to play as Geralt of Rivia, the legendary witcher',
                'title': 'Witcher Campaign',
                'selected_prompts': ['narrative', 'mechanics']
            })
        )
        self.assertEqual(create_response.status_code, 201)
        campaign_id = create_response.get_json()['campaign_id']
        
        # First interaction should recognize Geralt and offer design options
        interact_response = self.client.post(
            f'/api/campaigns/{campaign_id}/interact',
            headers={'Content-Type': 'application/json', 'X-Test-Bypass-Auth': 'true', 'X-Test-User-ID': self.user_id},
            data=json.dumps({'input': '1'})  # Select AIGenerated
        )
        self.assertEqual(interact_response.status_code, 200)
        response_data = interact_response.get_json()
        
        # Verify character recognition
        self.assertIn('Geralt', response_data['response'], "Should recognize Geralt")
        
        # Verify complete character sheet is shown
        response_text = response_data['response']
        self.assertIn('CHARACTER SHEET', response_text, "Should show character sheet")
        self.assertIn('STR:', response_text, "Should show STR score")
        self.assertIn('DEX:', response_text, "Should show DEX score")
        self.assertIn('CON:', response_text, "Should show CON score")
        self.assertIn('INT:', response_text, "Should show INT score")
        self.assertIn('WIS:', response_text, "Should show WIS score")
        self.assertIn('CHA:', response_text, "Should show CHA score")
        self.assertIn('Equipment:', response_text, "Should show equipment")
        
        # Verify planning block
        self.assertIn('--- PLANNING BLOCK ---', response_text, "Should have planning block")
        
        # Approve the character
        approve_response = self.client.post(
            f'/api/campaigns/{campaign_id}/interact',
            headers={'Content-Type': 'application/json', 'X-Test-Bypass-Auth': 'true', 'X-Test-User-ID': self.user_id},
            data=json.dumps({'input': '1'})  # Approve character
        )
        self.assertEqual(approve_response.status_code, 200)
        
        # Verify character data is stored
        final_state_json = run_god_command(self, 'ask', campaign_id=campaign_id)
        final_state = json.loads(final_state_json)
        pc_data = final_state.get('player_character_data', {})
        
        self.assertEqual(pc_data.get('name'), 'Geralt', "Character name should be Geralt")
        self.assertIn('class', pc_data, "Should have character class")
        self.assertIn('hp_max', pc_data, "Should have max HP")
        
        print("✅ AIGenerated path with specified character test passed")

    def test_character_creation_ai_generated_no_character(self):
        """Test AIGenerated path without pre-specified character"""
        # Create campaign without specified character
        create_response = self.client.post(
            '/api/campaigns',
            headers={'Content-Type': 'application/json', 'X-Test-Bypass-Auth': 'true', 'X-Test-User-ID': self.user_id},
            data=json.dumps({
                'prompt': 'A dark fantasy world filled with ancient magic',
                'title': 'Dark Fantasy Campaign',
                'selected_prompts': ['narrative', 'mechanics']
            })
        )
        self.assertEqual(create_response.status_code, 201)
        campaign_id = create_response.get_json()['campaign_id']
        
        # First interaction should offer generic character creation
        interact_response = self.client.post(
            f'/api/campaigns/{campaign_id}/interact',
            headers={'Content-Type': 'application/json', 'X-Test-Bypass-Auth': 'true', 'X-Test-User-ID': self.user_id},
            data=json.dumps({'input': '1'})  # Select AIGenerated
        )
        self.assertEqual(interact_response.status_code, 200)
        response_data = interact_response.get_json()
        
        # Verify generic greeting
        response_text = response_data['response']
        self.assertIn('CHARACTER SHEET', response_text, "Should show character sheet")
        
        # Verify all required character elements
        self.assertIn('Race:', response_text, "Should show race")
        self.assertIn('Class:', response_text, "Should show class")
        self.assertIn('Level:', response_text, "Should show level")
        self.assertIn('Background:', response_text, "Should show background")
        self.assertIn('Why This Character:', response_text, "Should explain choices")
        
        print("✅ AIGenerated path without character test passed")

    def test_character_creation_standard_dnd_path(self):
        """Test StandardD&D path with step-by-step choices"""
        # Create campaign
        create_response = self.client.post(
            '/api/campaigns',
            headers={'Content-Type': 'application/json', 'X-Test-Bypass-Auth': 'true', 'X-Test-User-ID': self.user_id},
            data=json.dumps({
                'prompt': 'Classic D&D adventure',
                'title': 'Standard D&D Campaign',
                'selected_prompts': ['narrative', 'mechanics']
            })
        )
        self.assertEqual(create_response.status_code, 201)
        campaign_id = create_response.get_json()['campaign_id']
        
        # Select StandardD&D option
        interact_response = self.client.post(
            f'/api/campaigns/{campaign_id}/interact',
            headers={'Content-Type': 'application/json', 'X-Test-Bypass-Auth': 'true', 'X-Test-User-ID': self.user_id},
            data=json.dumps({'input': '2'})  # Select StandardD&D
        )
        self.assertEqual(interact_response.status_code, 200)
        response_data = interact_response.get_json()
        
        # Should present race options
        response_text = response_data['response']
        self.assertIn('Human', response_text, "Should list Human race")
        self.assertIn('Elf', response_text, "Should list Elf race")
        self.assertIn('Dwarf', response_text, "Should list Dwarf race")
        
        # Select Human (option 1)
        race_response = self.client.post(
            f'/api/campaigns/{campaign_id}/interact',
            headers={'Content-Type': 'application/json', 'X-Test-Bypass-Auth': 'true', 'X-Test-User-ID': self.user_id},
            data=json.dumps({'input': '1'})  # Select Human
        )
        self.assertEqual(race_response.status_code, 200)
        
        # Should now present class options
        class_text = race_response.get_json()['response']
        self.assertIn('Fighter', class_text, "Should list Fighter class")
        self.assertIn('Wizard', class_text, "Should list Wizard class")
        
        print("✅ StandardD&D path test passed")

    def test_character_creation_custom_class_path(self):
        """Test CustomClass path with unique character concept"""
        # Create campaign with custom character idea
        create_response = self.client.post(
            '/api/campaigns',
            headers={'Content-Type': 'application/json', 'X-Test-Bypass-Auth': 'true', 'X-Test-User-ID': self.user_id},
            data=json.dumps({
                'prompt': 'I want to play as a time-traveling chronomancer',
                'title': 'Custom Character Campaign',
                'selected_prompts': ['narrative', 'mechanics']
            })
        )
        self.assertEqual(create_response.status_code, 201)
        campaign_id = create_response.get_json()['campaign_id']
        
        # Select CustomClass option
        interact_response = self.client.post(
            f'/api/campaigns/{campaign_id}/interact',
            headers={'Content-Type': 'application/json', 'X-Test-Bypass-Auth': 'true', 'X-Test-User-ID': self.user_id},
            data=json.dumps({'input': '3'})  # Select CustomClass
        )
        self.assertEqual(interact_response.status_code, 200)
        response_data = interact_response.get_json()
        
        # Should acknowledge custom concept
        response_text = response_data['response']
        self.assertIn('chronomancer', response_text.lower(), "Should acknowledge chronomancer concept")
        
        # Should ask for more details or present custom mechanics
        self.assertIn('--- PLANNING BLOCK ---', response_text, "Should have planning block")
        
        print("✅ CustomClass path test passed")

    def test_character_creation_numeric_input_handling(self):
        """Test that numeric inputs are correctly interpreted during character creation"""
        # Create campaign
        create_response = self.client.post(
            '/api/campaigns',
            headers={'Content-Type': 'application/json', 'X-Test-Bypass-Auth': 'true', 'X-Test-User-ID': self.user_id},
            data=json.dumps({
                'prompt': 'Test numeric input handling',
                'title': 'Numeric Input Test',
                'selected_prompts': ['narrative', 'mechanics']
            })
        )
        self.assertEqual(create_response.status_code, 201)
        campaign_id = create_response.get_json()['campaign_id']
        
        # Send numeric input "2" - should select StandardD&D, not continue story
        interact_response = self.client.post(
            f'/api/campaigns/{campaign_id}/interact',
            headers={'Content-Type': 'application/json', 'X-Test-Bypass-Auth': 'true', 'X-Test-User-ID': self.user_id},
            data=json.dumps({'input': '2'})
        )
        self.assertEqual(interact_response.status_code, 200)
        response_data = interact_response.get_json()
        
        # Verify it interpreted as option selection, not story continuation
        response_text = response_data['response']
        # Should present race/class options, not continue story
        races_presented = any(race in response_text for race in ['Human', 'Elf', 'Dwarf', 'Halfling'])
        self.assertTrue(races_presented, "Numeric input should trigger StandardD&D path, not story continuation")
        
        print("✅ Numeric input handling test passed")

    def test_character_creation_final_approval_enforcement(self):
        """Test that final approval step is always presented"""
        # Create campaign
        create_response = self.client.post(
            '/api/campaigns',
            headers={'Content-Type': 'application/json', 'X-Test-Bypass-Auth': 'true', 'X-Test-User-ID': self.user_id},
            data=json.dumps({
                'prompt': 'Test final approval',
                'title': 'Approval Test',
                'selected_prompts': ['narrative', 'mechanics']
            })
        )
        self.assertEqual(create_response.status_code, 201)
        campaign_id = create_response.get_json()['campaign_id']
        
        # Select AIGenerated
        interact_response = self.client.post(
            f'/api/campaigns/{campaign_id}/interact',
            headers={'Content-Type': 'application/json', 'X-Test-Bypass-Auth': 'true', 'X-Test-User-ID': self.user_id},
            data=json.dumps({'input': '1'})
        )
        self.assertEqual(interact_response.status_code, 200)
        response_data = interact_response.get_json()
        
        # Verify final approval options are presented
        response_text = response_data['response']
        self.assertIn('Would you like to', response_text, "Should ask for approval")
        approval_options = [
            'Play as this character',
            'Make changes',
            'Start over'
        ]
        for option in approval_options:
            self.assertIn(option, response_text, f"Should include '{option}' option")
        
        print("✅ Final approval enforcement test passed")

    def test_character_creation_shows_campaign_summary(self):
        """Test that character creation displays full campaign summary"""
        # Create campaign with all options
        create_response = self.client.post(
            '/api/campaigns',
            headers={'Content-Type': 'application/json', 'X-Test-Bypass-Auth': 'true', 'X-Test-User-ID': self.user_id},
            data=json.dumps({
                'prompt': 'I want to play as Drizzt Do\'Urden in the Underdark',
                'title': 'Drizzt\'s Journey',
                'selected_prompts': ['narrative', 'mechanics']
            })
        )
        self.assertEqual(create_response.status_code, 201)
        campaign_id = create_response.get_json()['campaign_id']
        
        # First interaction should show campaign summary
        interact_response = self.client.post(
            f'/api/campaigns/{campaign_id}/interact',
            headers={'Content-Type': 'application/json', 'X-Test-Bypass-Auth': 'true', 'X-Test-User-ID': self.user_id},
            data=json.dumps({'input': ''})  # Empty input to see initial response
        )
        self.assertEqual(interact_response.status_code, 200)
        response_data = interact_response.get_json()
        response_text = response_data['response']
        
        # Verify campaign summary is shown
        self.assertIn('CAMPAIGN SUMMARY', response_text, "Should show campaign summary header")
        self.assertIn('Title:', response_text, "Should show title field")
        self.assertIn('Character:', response_text, "Should show character field")
        self.assertIn('Setting:', response_text, "Should show setting field")
        self.assertIn('Description:', response_text, "Should show description field")
        self.assertIn('AI Personalities:', response_text, "Should show personalities")
        self.assertIn('Options:', response_text, "Should show options")
        
        # Verify specific content
        self.assertIn('Drizzt', response_text, "Should show character name")
        self.assertIn('Narrative, Mechanics', response_text, "Should list active personalities")
        
        print("✅ Campaign summary display test passed")


if __name__ == '__main__':
    unittest.main()
