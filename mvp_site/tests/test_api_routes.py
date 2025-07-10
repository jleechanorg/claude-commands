import unittest
import json
import tempfile
import os
from unittest.mock import patch, MagicMock, mock_open
from io import BytesIO

# Mock firebase_admin before it's used in main
mock_firebase_admin = MagicMock()
mock_firestore = MagicMock()
mock_auth = MagicMock()
mock_firebase_admin.firestore = mock_firestore
mock_firebase_admin.auth = mock_auth

# Apply the mock
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

sys.modules['firebase_admin'] = mock_firebase_admin
sys.modules['firebase_admin.firestore'] = mock_firestore
sys.modules['firebase_admin.auth'] = mock_auth

from main import create_app, DEFAULT_TEST_USER, HEADER_TEST_BYPASS, HEADER_TEST_USER_ID
import main


class TestAPIRoutes(unittest.TestCase):
    """Test API routes with comprehensive coverage."""
    
    def setUp(self):
        """Set up test client and mock environment."""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.test_headers = {
            HEADER_TEST_BYPASS: 'true',
            HEADER_TEST_USER_ID: DEFAULT_TEST_USER
        }
        
        # Reset mocks for each test
        mock_firebase_admin.auth.verify_id_token.reset_mock()
        mock_firestore.reset_mock()
    
    @patch('main.firestore_service')
    def test_get_campaigns_success(self, mock_firestore_service):
        """Test successful retrieval of campaigns."""
        # Mock firestore response
        mock_campaigns = {
            'campaigns': [
                {'id': 'campaign1', 'title': 'Adventure 1', 'created_at': '2024-01-01'},
                {'id': 'campaign2', 'title': 'Adventure 2', 'created_at': '2024-01-02'}
            ]
        }
        mock_firestore_service.get_campaigns_for_user.return_value = mock_campaigns
        
        response = self.client.get('/api/campaigns', headers=self.test_headers)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data, mock_campaigns)
        mock_firestore_service.get_campaigns_for_user.assert_called_once_with(DEFAULT_TEST_USER)
    
    @patch('main.firestore_service')
    def test_get_campaigns_empty_list(self, mock_firestore_service):
        """Test retrieval when user has no campaigns."""
        mock_campaigns = {'campaigns': []}
        mock_firestore_service.get_campaigns_for_user.return_value = mock_campaigns
        
        response = self.client.get('/api/campaigns', headers=self.test_headers)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data, mock_campaigns)
    
    @patch('main.firestore_service')
    def test_get_campaigns_firestore_exception(self, mock_firestore_service):
        """Test handling of Firestore exceptions in get_campaigns."""
        mock_firestore_service.get_campaigns_for_user.side_effect = Exception('Firestore error')
        
        response = self.client.get('/api/campaigns', headers=self.test_headers)
        
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    @patch('main.firestore_service')
    def test_get_campaign_success(self, mock_firestore_service):
        """Test successful retrieval of a specific campaign."""
        mock_campaign_data = {
            'id': 'test-campaign',
            'title': 'Test Adventure',
            'player': {'name': 'Hero', 'level': 5}
        }
        # Mock game state
        from game_state import GameState
        mock_game_state = GameState()  # Will default to debug_mode=True
        
        mock_firestore_service.get_campaign_by_id.return_value = (mock_campaign_data, [])
        mock_firestore_service.get_campaign_game_state.return_value = mock_game_state
        
        response = self.client.get('/api/campaigns/test-campaign', headers=self.test_headers)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['campaign'], mock_campaign_data)
        self.assertIn('story', data)
        self.assertIn('game_state', data)
        self.assertTrue(data['game_state'].get('debug_mode', False))  # Should be True by default
        mock_firestore_service.get_campaign_by_id.assert_called_once_with(DEFAULT_TEST_USER, 'test-campaign')
    
    @patch('main.firestore_service')
    def test_get_campaign_not_found(self, mock_firestore_service):
        """Test handling when campaign is not found."""
        mock_firestore_service.get_campaign_by_id.return_value = (None, None)
        
        response = self.client.get('/api/campaigns/nonexistent', headers=self.test_headers)
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('not found', data['error'].lower())
    
    @patch('main.firestore_service')
    def test_get_campaign_firestore_exception(self, mock_firestore_service):
        """Test handling of Firestore exceptions in get_campaign."""
        mock_firestore_service.get_campaign_by_id.side_effect = Exception('Database error')
        
        response = self.client.get('/api/campaigns/test-campaign', headers=self.test_headers)
        
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    @patch('main.firestore_service')
    @patch('main.constants')
    def test_update_campaign_success(self, mock_constants, mock_firestore_service):
        """Test successful campaign title update."""
        # Mock the constants
        mock_constants.KEY_TITLE = 'title'
        
        new_title = 'Updated Adventure Title'
        mock_firestore_service.update_campaign_title.return_value = None  # Method doesn't return anything on success
        
        response = self.client.patch(
            '/api/campaigns/test-campaign',
            headers=self.test_headers,
            json={'title': new_title}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        mock_firestore_service.update_campaign_title.assert_called_once_with(
            DEFAULT_TEST_USER, 'test-campaign', new_title
        )
    
    @patch('main.constants')
    def test_update_campaign_missing_title(self, mock_constants):
        """Test campaign update with missing title."""
        mock_constants.KEY_TITLE = 'title'
        
        response = self.client.patch(
            '/api/campaigns/test-campaign',
            headers=self.test_headers,
            json={}  # Missing title
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('title', data['error'].lower())
    
    @patch('main.firestore_service')
    @patch('main.constants')
    def test_update_campaign_firestore_exception(self, mock_constants, mock_firestore_service):
        """Test handling of Firestore exceptions in update_campaign."""
        mock_constants.KEY_TITLE = 'title'
        mock_firestore_service.update_campaign_title.side_effect = Exception('Update error')
        
        response = self.client.patch(
            '/api/campaigns/test-campaign',
            headers=self.test_headers,
            json={'title': 'New Title'}
        )
        
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertIn('error', data)


class TestExportRoutes(unittest.TestCase):
    """Test campaign export functionality."""
    
    def setUp(self):
        """Set up test client."""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.test_headers = {
            HEADER_TEST_BYPASS: 'true',
            HEADER_TEST_USER_ID: DEFAULT_TEST_USER
        }
    
    @patch('main.document_generator')
    @patch('main.firestore_service')
    @patch('main.os.path.exists')
    @patch('main.send_file')
    def test_export_campaign_pdf_success(self, mock_send_file, mock_exists, mock_firestore_service, mock_doc_generator):
        """Test successful PDF export."""
        # Mock campaign data
        mock_campaign = {
            'title': 'Test Campaign',
            'story': [{'content': 'Adventure begins...'}]
        }
        mock_story = [{'actor': 'user', 'text': 'Hello', 'mode': 'character'}]
        mock_firestore_service.get_campaign_by_id.return_value = (mock_campaign, mock_story)
        
        # Mock file system
        mock_exists.return_value = True
        mock_response = MagicMock()
        mock_response.call_on_close = lambda f: None
        mock_send_file.return_value = mock_response
        
        with patch('main.constants') as mock_constants:
            mock_constants.KEY_ACTOR = 'actor'
            mock_constants.KEY_TEXT = 'text' 
            mock_constants.KEY_MODE = 'mode'
            mock_constants.ACTOR_GEMINI = 'gemini'
            mock_constants.MODE_GOD = 'god'
            
            response = self.client.get(
                '/api/campaigns/test-campaign/export?format=pdf',
                headers=self.test_headers
            )
            
            # Check that the response is successful (Flask wraps the send_file response)
            self.assertEqual(response.status_code, 200)
            mock_doc_generator.generate_pdf.assert_called_once()
            mock_send_file.assert_called_once()
    
    @patch('main.firestore_service')
    def test_export_campaign_not_found(self, mock_firestore_service):
        """Test export when campaign doesn't exist."""
        mock_firestore_service.get_campaign_by_id.return_value = (None, None)
        
        response = self.client.get(
            '/api/campaigns/nonexistent/export?format=pdf',
            headers=self.test_headers
        )
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('not found', data['error'].lower())
    
    @patch('main.firestore_service')
    def test_export_campaign_unsupported_format(self, mock_firestore_service):
        """Test export with unsupported format."""
        # Mock the campaign data
        mock_firestore_service.get_campaign_by_id.return_value = (
            {'title': 'Test Campaign'},
            [{'actor': 'user', 'text': 'Test story'}]
        )
        
        response = self.client.get(
            '/api/campaigns/test-campaign/export?format=xml',
            headers=self.test_headers
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('unsupported', data['error'].lower())


class TestCreateCampaignRoute(unittest.TestCase):
    """Test campaign creation route."""
    
    def setUp(self):
        """Set up test client."""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.test_headers = {
            HEADER_TEST_BYPASS: 'true',
            HEADER_TEST_USER_ID: DEFAULT_TEST_USER
        }
    
    @patch('main.firestore_service')
    @patch('main.gemini_service')
    @patch('main.constants')
    @patch('main.GameState')
    def test_create_campaign_success(self, mock_game_state_class, mock_constants, mock_gemini_service, mock_firestore_service):
        """Test successful campaign creation."""
        # Mock constants
        mock_constants.KEY_TITLE = 'title'
        
        # Mock GameState
        mock_game_state = MagicMock()
        mock_game_state.to_dict.return_value = {'initial': 'state'}
        mock_game_state_class.return_value = mock_game_state
        
        # Mock Gemini service - create mock GeminiResponse
        mock_opening_story = 'Your adventure begins...'
        mock_gemini_response = MagicMock()
        mock_gemini_response.narrative_text = mock_opening_story
        mock_gemini_response.structured_response = None
        mock_gemini_service.get_initial_story.return_value = mock_gemini_response
        
        # Mock Firestore response
        campaign_id = 'new-campaign-123'
        mock_firestore_service.create_campaign.return_value = campaign_id
        
        campaign_data = {
            'prompt': 'Create a fantasy adventure',
            'title': 'My Adventure',
            'selected_prompts': ['narrative', 'mechanics'],
            'custom_options': []
        }
        
        response = self.client.post(
            '/api/campaigns',
            headers=self.test_headers,
            json=campaign_data
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('campaign_id', data)
        self.assertEqual(data['campaign_id'], campaign_id)
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        
        # Verify service calls
        mock_gemini_service.get_initial_story.assert_called_once_with(
            'Create a fantasy adventure',
            selected_prompts=['narrative', 'mechanics'],
            generate_companions=False,
            use_default_world=False
        )
        mock_firestore_service.create_campaign.assert_called_once()
    
    @patch('main.firestore_service')
    @patch('main.constants')
    @patch('main.gemini_service')
    @patch('main.GameState')
    def test_create_campaign_missing_prompt(self, mock_game_state_class, mock_gemini_service, mock_constants, mock_firestore_service):
        """Test campaign creation with missing prompt - should generate random content."""
        mock_constants.KEY_TITLE = 'title'
        
        # Mock GameState
        mock_game_state = MagicMock()
        mock_game_state.to_dict.return_value = {'initial': 'state'}
        mock_game_state_class.return_value = mock_game_state
        
        # Mock the gemini service to return a proper response
        mock_gemini_response = MagicMock()
        mock_gemini_response.narrative_text = "Mock story response"
        mock_gemini_response.structured_response = None
        mock_gemini_service.get_initial_story.return_value = mock_gemini_response
        
        # Mock firestore service
        mock_firestore_service.create_campaign.return_value = "test-campaign-id"
        
        # Test with missing prompt - should succeed and generate random content
        campaign_data = {
            'title': 'My Adventure',
            'selected_prompts': ['narrative']
            # Missing 'prompt', 'character', 'setting', and 'description' fields
        }
        
        response = self.client.post(
            '/api/campaigns',
            headers=self.test_headers,
            json=campaign_data
        )
        
        # Should succeed with 201 because _build_campaign_prompt generates random content
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('campaign_id', data)
        self.assertEqual(data['campaign_id'], "test-campaign-id")
        
        # Verify that gemini_service.get_initial_story was called with a generated prompt
        mock_gemini_service.get_initial_story.assert_called_once()
        call_args = mock_gemini_service.get_initial_story.call_args[0]
        generated_prompt = call_args[0]  # First argument should be the prompt
        
        # Verify the generated prompt contains random character and setting
        self.assertIn("Character:", generated_prompt)
        self.assertIn("Setting:", generated_prompt)
        # Should not contain literal "random character" anymore
        self.assertNotIn("random character", generated_prompt)

    @patch('main.firestore_service')
    @patch('main.constants')
    @patch('main.gemini_service')
    @patch('main.GameState')
    def test_create_campaign_character_setting_format(self, mock_game_state_class, mock_gemini_service, mock_constants, mock_firestore_service):
        """Test campaign creation with new character/setting/description format."""
        # Mock constants
        mock_constants.KEY_TITLE = 'title'
        mock_constants.ATTRIBUTE_SYSTEM_DND = 'D&D'
        
        # Mock GameState
        mock_game_state = MagicMock()
        mock_game_state.to_dict.return_value = {'initial': 'state'}
        mock_game_state_class.return_value = mock_game_state
        
        # Mock Gemini service
        mock_gemini_response = MagicMock()
        mock_gemini_response.narrative_text = 'Your character begins their journey...'
        mock_gemini_response.structured_response = None
        mock_gemini_service.get_initial_story.return_value = mock_gemini_response
        
        # Mock Firestore
        mock_firestore_service.create_campaign.return_value = 'test-campaign-char-setting'
        
        campaign_data = {
            'title': 'Character Setting Adventure',
            'character': 'Astarion',
            'setting': "Baldur's Gate",
            'description': 'Post-ascension vampire lord story',
            'campaign_type': 'custom',
            'selected_prompts': ['narrative', 'mechanics'],
            'custom_options': []
        }
        
        response = self.client.post(
            '/api/campaigns',
            headers=self.test_headers,
            json=campaign_data
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('campaign_id', data)
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        
        # Verify that gemini_service was called with the constructed prompt
        mock_gemini_service.get_initial_story.assert_called_once()
        call_args = mock_gemini_service.get_initial_story.call_args
        prompt_arg = call_args[0][0]  # First positional argument is the prompt
        
        # Verify the prompt was constructed correctly from the 3 fields
        self.assertIn('Character: Astarion', prompt_arg)
        self.assertIn("Setting: Baldur's Gate", prompt_arg)
        self.assertIn('Campaign Description: Post-ascension vampire lord story', prompt_arg)

    @patch('main.firestore_service')
    @patch('main.constants')
    @patch('main.gemini_service')
    @patch('main.GameState')
    def test_create_campaign_dragon_knight_type(self, mock_game_state_class, mock_gemini_service, mock_constants, mock_firestore_service):
        """Test campaign creation with dragon-knight campaign type."""
        # Mock constants
        mock_constants.KEY_TITLE = 'title'
        mock_constants.ATTRIBUTE_SYSTEM_DND = 'D&D'
        
        # Mock GameState
        mock_game_state = MagicMock()
        mock_game_state.to_dict.return_value = {'initial': 'state'}
        mock_game_state_class.return_value = mock_game_state
        
        # Mock Gemini service
        mock_gemini_response = MagicMock()
        mock_gemini_response.narrative_text = 'You are Ser Arion...'
        mock_gemini_response.structured_response = None
        mock_gemini_service.get_initial_story.return_value = mock_gemini_response
        
        # Mock Firestore
        mock_firestore_service.create_campaign.return_value = 'test-dragon-knight-campaign'
        
        campaign_data = {
            'title': 'Dragon Knight Adventure',
            'character': 'Ser Arion',
            'setting': 'World of Assiah',
            'description': '',  # Empty for Dragon Knight (uses built-in)
            'campaign_type': 'dragon-knight',
            'selected_prompts': ['narrative', 'mechanics'],
            'custom_options': ['defaultWorld']
        }
        
        response = self.client.post(
            '/api/campaigns',
            headers=self.test_headers,
            json=campaign_data
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('campaign_id', data)
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        
        # Verify that gemini_service was called with the Dragon Knight narrative
        mock_gemini_service.get_initial_story.assert_called_once()
        call_args = mock_gemini_service.get_initial_story.call_args
        prompt_arg = call_args[0][0]  # First positional argument is the prompt
        
        # Verify the Dragon Knight narrative was used
        self.assertIn('Celestial Imperium', prompt_arg)
        self.assertIn('Empress Sariel', prompt_arg)
        self.assertIn('Dragon Knights', prompt_arg)

    @patch('main.firestore_service')
    @patch('main.constants')
    @patch('main.gemini_service')
    @patch('main.GameState')
    def test_create_campaign_destiny_system_checkbox_checked(self, mock_game_state_class, mock_gemini_service, mock_constants, mock_firestore_service):
        """Test campaign creation with Destiny system checkbox checked (default)."""
        # Import constants for comparison
        import constants
        
        # Mock constants
        mock_constants.KEY_TITLE = 'title'
        mock_constants.ATTRIBUTE_SYSTEM_DND = constants.ATTRIBUTE_SYSTEM_DND
        
        # Mock GameState to capture the attribute_system
        mock_game_state = MagicMock()
        mock_game_state.to_dict.return_value = {'initial': 'state'}
        mock_game_state_class.return_value = mock_game_state
        
        # Mock Gemini service
        mock_gemini_response = MagicMock(); mock_gemini_response.narrative_text = 'Adventure begins...'; mock_gemini_response.structured_response = None; mock_gemini_service.get_initial_story.return_value = mock_gemini_response
        
        # Mock Firestore
        mock_firestore_service.create_campaign.return_value = 'test-campaign-123'
        
        campaign_data = {
            'prompt': 'Create a fantasy adventure',
            'title': 'Destiny System Campaign',
            'selected_prompts': ['narrative'],
            'custom_options': ['destinySystem']  # Destiny checkbox checked
        }
        
        response = self.client.post(
            '/api/campaigns',
            headers=self.test_headers,
            json=campaign_data
        )
        
        # Verify successful creation
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        # Verify GameState was created with D&D system (always uses D&D now)
        mock_game_state_class.assert_called_once()
        call_args = mock_game_state_class.call_args
        custom_campaign_state = call_args[1]['custom_campaign_state']
        self.assertEqual(custom_campaign_state['attribute_system'], constants.ATTRIBUTE_SYSTEM_DND)

    @patch('main.firestore_service')
    @patch('main.constants')
    @patch('main.gemini_service')
    @patch('main.GameState')
    def test_create_campaign_destiny_system_checkbox_unchecked(self, mock_game_state_class, mock_gemini_service, mock_constants, mock_firestore_service):
        """Test campaign creation with Destiny system checkbox unchecked (uses D&D)."""
        # Import constants for comparison
        import constants
        
        # Mock constants
        mock_constants.KEY_TITLE = 'title'
        mock_constants.ATTRIBUTE_SYSTEM_DND = constants.ATTRIBUTE_SYSTEM_DND
        
        # Mock GameState to capture the attribute_system
        mock_game_state = MagicMock()
        mock_game_state.to_dict.return_value = {'initial': 'state'}
        mock_game_state_class.return_value = mock_game_state
        
        # Mock Gemini service
        mock_gemini_response = MagicMock(); mock_gemini_response.narrative_text = 'Adventure begins...'; mock_gemini_response.structured_response = None; mock_gemini_service.get_initial_story.return_value = mock_gemini_response
        
        # Mock Firestore
        mock_firestore_service.create_campaign.return_value = 'test-campaign-456'
        
        campaign_data = {
            'prompt': 'Create a fantasy adventure',
            'title': 'D&D System Campaign',
            'selected_prompts': ['narrative'],
            'custom_options': []  # Destiny checkbox NOT checked = D&D system
        }
        
        response = self.client.post(
            '/api/campaigns',
            headers=self.test_headers,
            json=campaign_data
        )
        
        # Verify successful creation
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        # Verify GameState was created with D&D system
        mock_game_state_class.assert_called_once()
        call_args = mock_game_state_class.call_args
        custom_campaign_state = call_args[1]['custom_campaign_state']
        self.assertEqual(custom_campaign_state['attribute_system'], constants.ATTRIBUTE_SYSTEM_DND)

    @patch('main.firestore_service')
    @patch('main.constants')
    @patch('main.gemini_service')
    @patch('main.GameState')
    def test_create_campaign_multiple_custom_options(self, mock_game_state_class, mock_gemini_service, mock_constants, mock_firestore_service):
        """Test campaign creation with multiple custom options including destinySystem."""
        # Import constants for comparison
        import constants
        
        # Mock constants
        mock_constants.KEY_TITLE = 'title'
        mock_constants.ATTRIBUTE_SYSTEM_DND = constants.ATTRIBUTE_SYSTEM_DND
        
        # Mock GameState to capture the attribute_system
        mock_game_state = MagicMock()
        mock_game_state.to_dict.return_value = {'initial': 'state'}
        mock_game_state_class.return_value = mock_game_state
        
        # Mock Gemini service
        mock_gemini_response = MagicMock(); mock_gemini_response.narrative_text = 'Adventure begins...'; mock_gemini_response.structured_response = None; mock_gemini_service.get_initial_story.return_value = mock_gemini_response
        
        # Mock Firestore
        mock_firestore_service.create_campaign.return_value = 'test-campaign-789'
        
        campaign_data = {
            'prompt': 'Create a fantasy adventure',
            'title': 'Multi-Option Campaign',
            'selected_prompts': ['narrative', 'mechanics'],
            'custom_options': ['destinySystem', 'companions', 'defaultWorld']  # Multiple options
        }
        
        response = self.client.post(
            '/api/campaigns',
            headers=self.test_headers,
            json=campaign_data
        )
        
        # Verify successful creation
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        # Verify GameState was created with D&D system (always uses D&D now)
        mock_game_state_class.assert_called_once()
        call_args = mock_game_state_class.call_args
        custom_campaign_state = call_args[1]['custom_campaign_state']
        self.assertEqual(custom_campaign_state['attribute_system'], constants.ATTRIBUTE_SYSTEM_DND)


if __name__ == '__main__':
    unittest.main()