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
        mock_firestore_service.get_campaign_by_id.return_value = (mock_campaign_data, [])
        
        response = self.client.get('/api/campaigns/test-campaign', headers=self.test_headers)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['campaign'], mock_campaign_data)
        self.assertIn('story', data)
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
    
    def test_export_campaign_unsupported_format(self):
        """Test export with unsupported format."""
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
        
        # Mock Gemini service
        mock_opening_story = 'Your adventure begins...'
        mock_gemini_service.get_initial_story.return_value = mock_opening_story
        
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
            generate_companions=False
        )
        mock_firestore_service.create_campaign.assert_called_once()
    
    @patch('main.firestore_service')
    @patch('main.constants')
    @patch('main.gemini_service')
    @patch('main.GameState')
    def test_create_campaign_missing_prompt(self, mock_game_state_class, mock_gemini_service, mock_constants, mock_firestore_service):
        """Test campaign creation with missing prompt."""
        mock_constants.KEY_TITLE = 'title'
        
        # Mock GameState
        mock_game_state = MagicMock()
        mock_game_state.to_dict.return_value = {'initial': 'state'}
        mock_game_state_class.return_value = mock_game_state
        
        # Mock the gemini service to return a proper response
        mock_gemini_service.get_initial_story.return_value = "Mock story response"
        
        # Mock firestore service
        mock_firestore_service.create_campaign.return_value = "test-campaign-id"
        
        # Test with missing prompt
        campaign_data = {
            'title': 'My Adventure',
            'selected_prompts': ['narrative']
            # Missing 'prompt' field
        }
        
        response = self.client.post(
            '/api/campaigns',
            headers=self.test_headers,
            json=campaign_data
        )
        
        # Should succeed with mocked services, even with None prompt
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('campaign_id', data)
        self.assertTrue(data['success'])


if __name__ == '__main__':
    unittest.main()