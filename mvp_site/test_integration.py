import unittest
import os
import json
import sys
import subprocess
import logging
import tempfile
import shutil

# Add the project root to the Python path to allow for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from mvp_site.main import create_app
from mvp_site import firestore_service
from mvp_site.game_state import GameState

# Suppress noisy logging from underlying libraries for cleaner test output
logging.basicConfig(level=logging.WARNING)

# We still need the dummy key for the import-time initialization check
os.environ["GEMINI_API_KEY"] = "AIzaSyAfngmuVONpJPEbXpEZ1LwJnpDi2Vrdwb8" # DO NOT SUBMIT
os.environ["TESTING"] = "true"  # Enable fast model for tests

# Create temporary prompts directory for tests
temp_prompts_dir = tempfile.mkdtemp(prefix='test_prompts_')
os.makedirs(os.path.join(temp_prompts_dir, 'prompts'), exist_ok=True)

# Create minimal test prompt files
test_prompt_files = {
    'narrative_system_instruction.md': "Test narrative instruction.",
    'mechanics_system_instruction.md': "Test mechanics instruction.", 
    'calibration_instruction.md': "Test calibration instruction.",
    'destiny_ruleset.md': "Test destiny rules.",
    'game_state_instruction.md': "Test game state instruction.",
    'character_template.md': "Test character template.",
    'character_sheet_template.md': "Test character sheet.",
    '5e_SRD_All.md': "Test SRD content."
}

for filename, content in test_prompt_files.items():
    with open(os.path.join(temp_prompts_dir, 'prompts', filename), 'w') as f:
        f.write(content)

# Temporarily change working directory to temp dir so imports find test prompts
original_cwd = os.getcwd()
os.chdir(temp_prompts_dir)

import gemini_service # Import gemini_service to mock its internal _load_instruction_file

# Define mock system instruction content for consistent integration testing
MOCK_INTEGRATION_NARRATIVE = "Integration narrative."
MOCK_INTEGRATION_MECHANICS = "Integration mechanics."
MOCK_INTEGRATION_CALIBRATION = "Integration calibration."

# Speed up tests by using faster model and minimal prompts
TEST_MODEL_OVERRIDE = 'gemini-1.5-flash'  # Much faster than gemini-2.5-pro
TEST_SELECTED_PROMPTS = ['narrative']  # Use only one prompt type instead of multiple

# Cleanup function to restore original state
def cleanup_test_environment():
    os.chdir(original_cwd)
    shutil.rmtree(temp_prompts_dir, ignore_errors=True)

# Register cleanup
import atexit
atexit.register(cleanup_test_environment)

class TestInteractionIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Create one campaign for all tests to share."""
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()
        cls.user_id = 'test-integration-user'
        
        # Ensure the real Gemini API key is set; fall back to local file if possible.
        local_key_path = os.path.join(original_cwd, "mvp_site", "local_api_key.txt")
        if not os.environ.get("GEMINI_API_KEY") and os.path.exists(local_key_path):
            with open(local_key_path, "r") as key_file:
                os.environ["GEMINI_API_KEY"] = key_file.read().strip()

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
        script_path = "/home/jleechan/projects/worldarchitect.ai/mvp_site/main.py"
        base_command = [
            python_executable, script_path, "god-command",
            action,
            "--campaign_id", self.campaign_id,
            "--user_id", self.user_id
        ]
        if command_string:
            base_command.extend(["--command_string", command_string])
        
        # Run the god-command from the original directory
        result = subprocess.run(base_command, capture_output=True, text=True, cwd="/home/jleechan/projects/worldarchitect.ai/mvp_site")
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
        # Fetch the state from the shared campaign to verify it was created correctly
        state_json = self._run_god_command('ask')
        game_state = json.loads(state_json)

        # Basic sanity assertions. We cannot predict the exact content, but the structure should exist.
        self.assertIn('player_character_data', game_state)
        self.assertIn('npc_data', game_state)

    def test_ai_state_update_is_merged_correctly(self):
        """
        Milestone 2: Verify that an AI-proposed update is merged without data loss.
        Uses a specific prompt designed to trigger state changes.
        """
        # First, set a known initial state
        initial_set_command = 'GOD_MODE_SET: player_character_data = {"name": "Sir Kaelen", "stats": {"str": 10, "hp": 100}}'
        self._run_god_command('set', initial_set_command)

        # Use a very specific prompt that should trigger state changes
        targeted_prompt = (
            "Sir Kaelen finds a magical strength potion and drinks it, permanently increasing his strength by 5 points. "
            "He also takes 20 damage from a trap. Update his stats accordingly."
        )
        
        # Simulate the interaction with this targeted prompt
        interaction_response = self.client.post(
            f'/api/campaigns/{self.campaign_id}/interaction',
            headers={'Content-Type': 'application/json', 'X-Test-Bypass-Auth': 'true', 'X-Test-User-ID': self.user_id},
            data=json.dumps({'input': targeted_prompt, 'mode': 'character'})
        )
        self.assertEqual(interaction_response.status_code, 200)

        # Verify the state was updated (we can't predict exact values, but we can check structure)
        final_state_json = self._run_god_command('ask')
        final_state = json.loads(final_state_json)
        
        # Basic assertions - the AI should have maintained the character structure
        self.assertIn('player_character_data', final_state)
        self.assertIn('name', final_state['player_character_data'])
        self.assertEqual(final_state['player_character_data']['name'], 'Sir Kaelen')
        
        # The AI should have updated stats in some way (we can't predict exact values)
        self.assertIn('stats', final_state['player_character_data'])
        pc_stats = final_state['player_character_data']['stats']
        
        # At minimum, these keys should still exist (testing merge didn't lose data)
        self.assertIn('str', pc_stats)
        self.assertIn('hp', pc_stats)
        
        # Optional: Print the actual changes for manual verification during development
        print(f"Final stats after AI update: {pc_stats}")

    def test_god_command_set_performs_deep_merge(self):
        """
        Milestone 3: Verify the god-command itself performs a deep merge.
        This test doesn't require AI calls, just tests the merge logic.
        """
        # Set an initial state with a nested object
        initial_set_command = 'GOD_MODE_SET: player_character_data.stats = {"str": 12, "dex": 12}'
        self._run_god_command('set', initial_set_command)

        # Use another god command to update just one part of the nested object
        update_set_command = 'GOD_MODE_SET: player_character_data.stats.dex = 18'
        self._run_god_command('set', update_set_command)
        
        # Verify the deep merge
        final_state_json = self._run_god_command('ask')
        final_state = json.loads(final_state_json)
        
        pc_stats = final_state['player_character_data']['stats']
        self.assertEqual(pc_stats['dex'], 18)
        self.assertEqual(pc_stats['str'], 12)


if __name__ == '__main__':
    unittest.main()
