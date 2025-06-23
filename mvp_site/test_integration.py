import unittest
import os
import json
import sys
import subprocess
import logging

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

# Create dummy prompts directory and files for integration tests to prevent FileNotFoundError during import
if not os.path.exists('./prompts'):
    os.makedirs('./prompts')
with open('./prompts/narrative_system_instruction.md', 'w') as f:
    f.write("Integration test narrative instruction.")
with open('./prompts/mechanics_system_instruction.md', 'w') as f:
    f.write("Integration test mechanics instruction.")
with open('./prompts/calibration_instruction.md', 'w') as f:
    f.write("Integration test calibration instruction.")


import gemini_service # Import gemini_service to mock its internal _load_instruction_file

# Define mock system instruction content for consistent integration testing
MOCK_INTEGRATION_NARRATIVE = "Integration narrative."
MOCK_INTEGRATION_MECHANICS = "Integration mechanics."
MOCK_INTEGRATION_CALIBRATION = "Integration calibration."

# Speed up tests by using faster model and minimal prompts
TEST_MODEL_OVERRIDE = 'gemini-1.5-flash'  # Much faster than gemini-2.5-pro
TEST_SELECTED_PROMPTS = ['narrative']  # Use only one prompt type instead of multiple

class TestInteractionIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Create one campaign for all tests to share."""
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()
        cls.user_id = 'test-integration-user'
        
        # Ensure the real Gemini API key is set; fall back to local file if possible.
        if not os.environ.get("GEMINI_API_KEY") and os.path.exists(os.path.join(project_root, "mvp_site", "local_api_key.txt")):
            with open(os.path.join(project_root, "mvp_site", "local_api_key.txt"), "r") as key_file:
                os.environ["GEMINI_API_KEY"] = key_file.read().strip()

        # Create one shared campaign for all tests
        create_response = cls.client.post(
            '/api/campaigns',
            headers={'Content-Type': 'application/json', 'X-Test-Bypass-Auth': 'true', 'X-Test-User-ID': cls.user_id},
            data=json.dumps({'prompt': 'Start adventure', 'title': 'Test', 'selected_prompts': TEST_SELECTED_PROMPTS})
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
        script_path = os.path.join(project_root, "mvp_site", "main.py")
        base_command = [
            python_executable, script_path, "god-command",
            action,
            "--campaign_id", self.campaign_id,
            "--user_id", self.user_id
        ]
        if command_string:
            base_command.extend(["--command_string", command_string])
        
        result = subprocess.run(base_command, capture_output=True, text=True)
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

    @unittest.skip("Requires predictable AI output; skipped when using live Gemini API.")
    def test_ai_state_update_is_merged_correctly(self):
        pass

    @unittest.skip("GOD_MODE deep-merge verified elsewhere; skipping to shorten live API run time.")
    def test_god_command_set_performs_deep_merge(self):
        pass


if __name__ == '__main__':
    unittest.main()
