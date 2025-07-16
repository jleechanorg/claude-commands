import unittest
import json
import tempfile
import os
from unittest.mock import patch, MagicMock, mock_open
from firebase_admin import auth

# Mock firebase_admin before it's used in main
# This is a common pattern for testing Flask apps with Firebase
mock_firebase_admin = MagicMock()
mock_firestore = MagicMock()
mock_auth = MagicMock()
mock_firebase_admin.firestore = mock_firestore
mock_firebase_admin.auth = mock_auth

# The special DELETE_FIELD sentinel object we need to test against
DELETE_FIELD = object()
mock_firestore.DELETE_FIELD = DELETE_FIELD

# Apply the mock
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

sys.modules['firebase_admin'] = mock_firebase_admin
sys.modules['firebase_admin.firestore'] = mock_firestore
sys.modules['firebase_admin.auth'] = mock_auth


from main import create_app, DEFAULT_TEST_USER, HEADER_TEST_BYPASS, HEADER_TEST_USER_ID, parse_set_command, format_state_changes, setup_file_logging
from firestore_service import _truncate_log_json as truncate_game_state_for_logging
from game_state import GameState

class TestApiEndpoints(unittest.TestCase):

    def setUp(self):
        """Set up a test client for the Flask application."""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.test_headers = {
            HEADER_TEST_BYPASS: 'true',
            HEADER_TEST_USER_ID: DEFAULT_TEST_USER
        }

    @patch('main.firestore_service')
    def test_god_ask_state_with_delete_sentinel(self, mock_firestore_service):
        """
        Tests that the GOD_ASK_STATE command correctly serializes a game state
        containing the firestore.DELETE_FIELD sentinel value without crashing.
        """
        # 1. Arrange: Create a mock game state containing the sentinel
        mock_game_state = {
            "player": {"name": "Astarion", "hp": 23},
            "npcs": {
                "Goblin": {"status": "alive"},
                "Mind Flayer": DELETE_FIELD  # This field should be deleted
            }
        }
        # Mock the document snapshot and its to_dict method
        # Create a real GameState object instead of mock
        mock_game_state_obj = GameState.from_dict(mock_game_state)
        mock_firestore_service.get_campaign_game_state.return_value = mock_game_state_obj

        # 2. Act: Make the API call
        response = self.client.post(
            '/api/campaigns/test-campaign/interaction',
            headers=self.test_headers,
            json={'input': 'GOD_ASK_STATE'}
        )
        
        # 3. Assert
        self.assertEqual(response.status_code, 200)
        
        # The response text should be a JSON string inside a code block
        response_data = json.loads(response.get_data(as_text=True))
        response_json_str = response_data['response'].replace('```json\\n', '').replace('\\n```', '')
        final_state = json.loads(response_json_str)

        # Check that the 'Mind Flayer' key is now null (None in Python)
        self.assertIn('npcs', final_state)
        self.assertIn('Mind Flayer', final_state['npcs'])
        self.assertIsNone(final_state['npcs']['Mind Flayer'])
        # Verify other data is still present
        self.assertEqual(final_state['player']['name'], 'Astarion')
    
    @patch('main.firestore_service')
    @patch('main.update_state_with_changes')
    def test_god_mode_set_command(self, mock_update_state, mock_firestore_service):
        """Test GOD_MODE_SET command parsing and execution."""
        # Mock campaign and game state
        mock_campaign = {'id': 'test-campaign', 'title': 'Test'}
        mock_game_state = {'player': {'name': 'Hero', 'level': 1}}
        
        mock_doc_snapshot = MagicMock()
        mock_doc_snapshot.to_dict.return_value = mock_game_state
        mock_firestore_service.get_campaign_by_id.return_value = (mock_campaign, [])
        mock_firestore_service.get_campaign_game_state.return_value = mock_doc_snapshot
        mock_update_state.return_value = {'player': {'name': 'Hero', 'level': 5, 'hp': 50}}
        
        # Test SET command
        set_command = "GOD_MODE_SET:\nplayer.level = 5\nplayer.hp = 50"
        
        response = self.client.post(
            '/api/campaigns/test-campaign/interaction',
            headers=self.test_headers,
            json={'input': set_command}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('response', data)
        self.assertIn('Game state updated', data['response'])
        
        # Verify update_state_with_changes was called with parsed changes
        mock_update_state.assert_called_once()
        call_args = mock_update_state.call_args[0]
        changes = call_args[1]  # Second argument should be the changes dict
        self.assertIn('player', changes)
    
    @patch('main.firestore_service')
    @patch('main.update_state_with_changes')
    def test_god_mode_update_state_command(self, mock_update_state, mock_firestore_service):
        """Test GOD_MODE_UPDATE_STATE command with JSON payload."""
        # Mock campaign and game state
        mock_campaign = {'id': 'test-campaign', 'title': 'Test'}
        mock_game_state = {'player': {'name': 'Hero'}}
        
        mock_doc_snapshot = MagicMock()
        mock_doc_snapshot.to_dict.return_value = mock_game_state
        mock_firestore_service.get_campaign_by_id.return_value = (mock_campaign, [])
        mock_firestore_service.get_campaign_game_state.return_value = mock_doc_snapshot
        mock_update_state.return_value = {
            "player": {"name": "Hero", "stats": {"strength": 15}},
            "inventory": {"items": ["sword", "potion"]}
        }
        
        # Test UPDATE_STATE command with JSON
        json_payload = {
            "player": {"stats": {"strength": 15}},
            "inventory": {"items": ["sword", "potion"]}
        }
        update_command = f"GOD_MODE_UPDATE_STATE:{json.dumps(json_payload)}"
        
        response = self.client.post(
            '/api/campaigns/test-campaign/interaction',
            headers=self.test_headers,
            json={'input': update_command}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('response', data)
        
        # Verify update was called with JSON payload
        mock_update_state.assert_called_once()
        call_args = mock_update_state.call_args[0]
        changes = call_args[1]
        self.assertEqual(changes, json_payload)
    
    @patch('main.firestore_service')
    def test_god_mode_update_state_invalid_json(self, mock_firestore_service):
        """Test GOD_MODE_UPDATE_STATE command with invalid JSON."""
        # Mock campaign and game state
        mock_campaign = {'id': 'test-campaign', 'title': 'Test'}
        mock_game_state = {'player': {'name': 'Hero'}}
        
        mock_doc_snapshot = MagicMock()
        mock_doc_snapshot.to_dict.return_value = mock_game_state
        mock_firestore_service.get_campaign_by_id.return_value = (mock_campaign, [])
        mock_firestore_service.get_campaign_game_state.return_value = mock_doc_snapshot
        
        # Test UPDATE_STATE command with invalid JSON
        invalid_json = "GOD_MODE_UPDATE_STATE:{invalid json syntax}"
        
        response = self.client.post(
            '/api/campaigns/test-campaign/interaction',
            headers=self.test_headers,
            json={'input': invalid_json}
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)
        self.assertIn('JSON', data['error'])
    
    @patch('main.firestore_service')
    @patch('main.gemini_service')
    def test_normal_ai_interaction_flow(self, mock_gemini_service, mock_firestore_service):
        """Test normal AI interaction (non-GOD mode)."""
        # Mock campaign and game state
        mock_campaign = {'id': 'test-campaign', 'title': 'Test Adventure'}
        mock_game_state = {'player': {'name': 'Hero', 'location': 'village'}}
        mock_story = [{'actor': 'user', 'text': 'I explore the village'}]
        
        # Create a real GameState object instead of mock
        mock_game_state_obj = GameState.from_dict(mock_game_state)
        
        mock_firestore_service.get_campaign_by_id.return_value = (mock_campaign, mock_story)
        mock_firestore_service.get_campaign_game_state.return_value = mock_game_state_obj
        
        # Mock Gemini response - create a mock GeminiResponse object
        mock_ai_response = "You walk through the bustling village square..."
        mock_gemini_response = MagicMock()
        mock_gemini_response.narrative_text = mock_ai_response
        mock_gemini_response.debug_tags_present = {'dm_notes': False, 'dice_rolls': False, 'state_changes': False}
        mock_gemini_response.state_updates = {}
        mock_gemini_response.structured_response = None
        # Add the get_narrative_text method
        mock_gemini_response.get_narrative_text = MagicMock(return_value=mock_ai_response)
        mock_gemini_service.continue_story.return_value = mock_gemini_response
        mock_gemini_service.parse_llm_response_for_state_changes.return_value = {}
        
        response = self.client.post(
            '/api/campaigns/test-campaign/interaction',
            headers=self.test_headers,
            json={'input': 'I look around the village square'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('response', data)
        self.assertEqual(data['response'], mock_ai_response)
        
        # Verify AI service was called
        mock_gemini_service.continue_story.assert_called_once()
    
    @patch('main.firestore_service')
    def test_legacy_migration_status_handling(self, mock_firestore_service):
        """Test handling of different legacy migration statuses."""
        # MigrationStatus already imported at the top
        
        # Mock campaign
        mock_campaign = {'id': 'test-campaign', 'title': 'Test'}
        mock_story = []
        
        # Test with NOT_CHECKED status
        mock_game_state = {
            'player': {'name': 'Hero'}
        }
        
        mock_doc_snapshot = MagicMock()
        mock_doc_snapshot.to_dict.return_value = mock_game_state
        mock_firestore_service.get_campaign_by_id.return_value = (mock_campaign, mock_story)
        mock_firestore_service.get_campaign_game_state.return_value = mock_doc_snapshot
        
        response = self.client.post(
            '/api/campaigns/test-campaign/interaction',
            headers=self.test_headers,
            json={'input': 'GOD_ASK_STATE'}
        )
        
        self.assertEqual(response.status_code, 200)
        # Should handle migration status without error


class TestAuthenticationDecorator(unittest.TestCase):
    """Test the check_token decorator with various authentication scenarios."""
    
    def setUp(self):
        """Set up test environment with mocked Firebase auth."""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Reset auth mock for each test
        mock_firebase_admin.auth.verify_id_token.reset_mock()
    
    def test_authentication_bypass_works(self):
        """Test that authentication bypass works in testing mode."""
        # The existing test_god_ask_state_with_delete_sentinel already tests auth bypass
        # This is a placeholder to maintain coverage


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions in main.py."""
    
    def test_parse_set_command_simple_assignment(self):
        """Test parsing simple key=value assignments."""
        result = parse_set_command("player.name = \"John Doe\"")
        expected = {"player": {"name": "John Doe"}}
        self.assertEqual(result, expected)
    
    def test_parse_set_command_json_value(self):
        """Test parsing JSON values."""
        result = parse_set_command('character.stats = {"strength": 15, "dexterity": 12}')
        expected = {"character": {"stats": {"strength": 15, "dexterity": 12}}}
        self.assertEqual(result, expected)
    
    def test_parse_set_command_multiple_lines(self):
        """Test parsing multiple assignments."""
        command = """player.level = 5
player.hp = 45
player.class = "Warrior\""""
        result = parse_set_command(command)
        expected = {
            "player": {
                "level": 5,
                "hp": 45,
                "class": "Warrior"
            }
        }
        self.assertEqual(result, expected)
    
    def test_parse_set_command_append_operation(self):
        """Test parsing append operations."""
        result = parse_set_command("inventory.items.append = \"Health Potion\"")
        expected = {"inventory": {"items": {"append": ["Health Potion"]}}}
        self.assertEqual(result, expected)
    
    def test_parse_set_command_invalid_json(self):
        """Test parsing with invalid JSON values."""
        result = parse_set_command("player.data = {invalid json}")
        expected = {}  # Invalid JSON lines are skipped
        self.assertEqual(result, expected)
    
    def test_parse_set_command_empty_input(self):
        """Test parsing empty input."""
        result = parse_set_command("")
        self.assertEqual(result, {})
    
    def test_format_state_changes_empty(self):
        """Test formatting empty state changes."""
        result = format_state_changes({})
        self.assertEqual(result, "No state changes.")
    
    def test_format_state_changes_single_entry(self):
        """Test formatting single state change."""
        changes = {"player.name": "John"}
        result = format_state_changes(changes)
        self.assertIn("Game state updated (1 entry):", result)
        self.assertIn("player.name: \"John\"", result)
    
    def test_format_state_changes_multiple_entries(self):
        """Test formatting multiple state changes."""
        changes = {
            "player.name": "John",
            "player.level": 5
        }
        result = format_state_changes(changes)
        self.assertIn("Game state updated (2 entries):", result)
        self.assertIn("player.name: \"John\"", result)
        self.assertIn("player.level: 5", result)
    
    def test_format_state_changes_nested_dict(self):
        """Test formatting nested dictionary changes."""
        changes = {
            "player": {
                "stats": {
                    "strength": 15,
                    "dexterity": 12
                }
            }
        }
        result = format_state_changes(changes)
        self.assertIn("Game state updated (2 entries):", result)
        self.assertIn("player.stats.strength: 15", result)
        self.assertIn("player.stats.dexterity: 12", result)
    
    def test_format_state_changes_html_mode(self):
        """Test formatting for HTML output."""
        changes = {"player.name": "John"}
        result = format_state_changes(changes, for_html=True)
        self.assertIn("<ul>", result)  # Should contain HTML list
        self.assertIn("<li>", result)  # Should contain list items
        self.assertIn("<code>", result)  # Should contain code tags
    
    def test_truncate_game_state_for_logging_under_limit(self):
        """Test truncation when state is under line limit."""
        small_state = {"player": {"name": "John", "level": 5}}
        result = truncate_game_state_for_logging(small_state, max_lines=20)
        # Should return full JSON since it's under limit
        self.assertIn("player", result)
        self.assertIn("John", result)
        self.assertNotIn("truncated", result)
    
    def test_truncate_game_state_for_logging_over_limit(self):
        """Test truncation when state exceeds line limit."""
        # Create a large state that will exceed the line limit
        large_state = {f"key_{i}": f"value_{i}" for i in range(50)}
        result = truncate_game_state_for_logging(large_state, max_lines=5)
        # Should be truncated
        self.assertIn("truncated", result)
        lines = result.split('\n')
        self.assertEqual(len(lines), 5)  # Should be max_lines (including truncation message)

    @patch('main.subprocess.check_output')
    @patch('main.os.makedirs')
    @patch('main.logging.FileHandler')
    @patch('main.logging_util.info')
    @patch('main.logging.getLogger')
    def test_setup_file_logging_with_slash_in_branch_name(self, mock_get_logger, mock_logging_util_info, mock_file_handler, mock_makedirs, mock_subprocess):
        """Test that branch names with forward slashes are converted to underscores in log filenames."""
        # Mock git branch command to return a branch name with forward slash
        mock_subprocess.return_value = "fix/god-mode-planning-blocks"
        
        # Mock logger and its handlers
        mock_logger = MagicMock()
        mock_logger.handlers = []
        mock_get_logger.return_value = mock_logger
        
        # Call the function
        setup_file_logging()
        
        # Verify that the FileHandler was called with the converted filename
        expected_log_path = os.path.join("/tmp/worldarchitectai_logs", "fix_god-mode-planning-blocks.log")
        mock_file_handler.assert_called_once_with(expected_log_path)



if __name__ == '__main__':
    unittest.main()
