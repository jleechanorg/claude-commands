"""
Comprehensive tests for main.py route handlers.
Tests all major API endpoints with various scenarios including success, failure, and edge cases.
"""

import os
import unittest
from unittest.mock import MagicMock, patch

# Mock firebase_admin before imports
mock_firebase_admin = MagicMock()
mock_firestore = MagicMock()
mock_auth = MagicMock()
mock_firebase_admin.firestore = mock_firestore
mock_firebase_admin.auth = mock_auth

# Firebase DELETE_FIELD sentinel
DELETE_FIELD = object()
mock_firestore.DELETE_FIELD = DELETE_FIELD

# Setup module mocks
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.modules["firebase_admin"] = mock_firebase_admin
sys.modules["firebase_admin.firestore"] = mock_firestore
sys.modules["firebase_admin.auth"] = mock_auth

# Import after mocking
from main import (
    DEFAULT_TEST_USER,
    HEADER_TEST_BYPASS,
    HEADER_TEST_USER_ID,
    KEY_CAMPAIGN,
    KEY_CAMPAIGN_ID,
    KEY_ERROR,
    KEY_MESSAGE,
    KEY_STORY,
    KEY_SUCCESS,
    create_app,
)
from mocks.data_fixtures import SAMPLE_CAMPAIGN, SAMPLE_GAME_STATE, SAMPLE_STORY_CONTEXT


class TestCampaignRoutes(unittest.TestCase):
    """Test campaign management routes."""

    def setUp(self):
        """Set up test client and headers."""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.test_headers = {
            HEADER_TEST_BYPASS: "true",
            HEADER_TEST_USER_ID: DEFAULT_TEST_USER,
        }

    @patch("main.firestore_service")
    def test_get_campaigns_success(self, mock_firestore_service):
        """Test successful campaigns retrieval."""
        # Mock campaigns list
        mock_campaigns = [
            {"id": "campaign1", "title": "Adventure 1", "user_id": DEFAULT_TEST_USER},
            {"id": "campaign2", "title": "Adventure 2", "user_id": DEFAULT_TEST_USER},
        ]
        mock_firestore_service.get_campaigns_for_user.return_value = mock_campaigns

        response = self.client.get("/api/campaigns", headers=self.test_headers)

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["title"], "Adventure 1")
        mock_firestore_service.get_campaigns_for_user.assert_called_once_with(
            DEFAULT_TEST_USER
        )

    @patch("main.firestore_service")
    def test_get_campaigns_error(self, mock_firestore_service):
        """Test campaigns retrieval with service error."""
        mock_firestore_service.get_campaigns_for_user.side_effect = Exception(
            "Database error"
        )

        response = self.client.get("/api/campaigns", headers=self.test_headers)

        self.assertEqual(response.status_code, 500)
        data = response.get_json()
        self.assertIn(KEY_ERROR, data)
        self.assertIn("Database error", data[KEY_ERROR])

    @patch('main.get_user_settings')
    @patch("main.firestore_service")
    def test_get_single_campaign_success(self, mock_firestore_service, mock_get_user_settings):
        """Test successful single campaign retrieval."""
        # Mock campaign and story data
        mock_campaign = SAMPLE_CAMPAIGN.copy()
        mock_story = SAMPLE_STORY_CONTEXT.copy()
        mock_game_state = MagicMock()
        mock_game_state.to_dict.return_value = SAMPLE_GAME_STATE

        mock_firestore_service.get_campaign_by_id.return_value = (
            mock_campaign,
            mock_story,
        )
        mock_firestore_service.get_campaign_game_state.return_value = mock_game_state
        # Mock get_user_settings for debug_mode lookup
        mock_get_user_settings.return_value = {'debug_mode': False}

        response = self.client.get(
            "/api/campaigns/test-campaign", headers=self.test_headers
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn(KEY_CAMPAIGN, data)
        self.assertIn(KEY_STORY, data)
        self.assertIn("game_state", data)
        self.assertEqual(data[KEY_CAMPAIGN]["title"], mock_campaign["title"])

    @patch("main.firestore_service")
    def test_get_single_campaign_not_found(self, mock_firestore_service):
        """Test single campaign retrieval when campaign doesn't exist."""
        mock_firestore_service.get_campaign_by_id.return_value = (None, None)

        response = self.client.get(
            "/api/campaigns/nonexistent", headers=self.test_headers
        )

        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertIn(KEY_ERROR, data)
        self.assertIn("not found", data[KEY_ERROR].lower())

    @patch("main.firestore_service")
    def test_get_single_campaign_error(self, mock_firestore_service):
        """Test single campaign retrieval with service error."""
        mock_firestore_service.get_campaign_by_id.side_effect = Exception(
            "Database error"
        )

        response = self.client.get(
            "/api/campaigns/test-campaign", headers=self.test_headers
        )

        self.assertEqual(response.status_code, 500)
        data = response.get_json()
        self.assertIn(KEY_ERROR, data)

    @patch("main.firestore_service")
    @patch("main.gemini_service")
    def test_create_campaign_success(self, mock_gemini_service, mock_firestore_service):
        """Test successful campaign creation."""
        # Mock AI response
        mock_ai_response = MagicMock()
        mock_ai_response.narrative_text = "Welcome to your adventure!"
        mock_gemini_service.get_initial_story.return_value = mock_ai_response

        # Mock campaign creation
        mock_firestore_service.create_campaign.return_value = "new-campaign-id"

        campaign_data = {
            "prompt": "Create a fantasy adventure",
            "title": "My New Adventure",
            "selected_prompts": ["narrative", "combat"],
            "custom_options": ["companions", "defaultWorld"],
        }

        response = self.client.post(
            "/api/campaigns", headers=self.test_headers, json=campaign_data
        )

        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertTrue(data[KEY_SUCCESS])
        self.assertEqual(data[KEY_CAMPAIGN_ID], "new-campaign-id")

        # Verify AI service was called correctly
        mock_gemini_service.get_initial_story.assert_called_once()
        call_args = mock_gemini_service.get_initial_story.call_args
        self.assertEqual(call_args[0][0], campaign_data["prompt"])
        self.assertEqual(
            call_args[1]["selected_prompts"], campaign_data["selected_prompts"]
        )
        self.assertTrue(call_args[1]["generate_companions"])
        self.assertTrue(call_args[1]["use_default_world"])

    @patch("main.firestore_service")
    @patch("main.gemini_service")
    def test_create_campaign_minimal_data(
        self, mock_gemini_service, mock_firestore_service
    ):
        """Test campaign creation with minimal required data."""
        mock_ai_response = MagicMock()
        mock_ai_response.narrative_text = "Basic adventure begins."
        mock_gemini_service.get_initial_story.return_value = mock_ai_response
        mock_firestore_service.create_campaign.return_value = "basic-campaign-id"

        campaign_data = {"prompt": "Simple adventure", "title": "Basic Adventure"}

        response = self.client.post(
            "/api/campaigns", headers=self.test_headers, json=campaign_data
        )

        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertTrue(data[KEY_SUCCESS])

        # Verify defaults were used
        call_args = mock_gemini_service.get_initial_story.call_args
        self.assertEqual(call_args[1]["selected_prompts"], [])
        self.assertFalse(call_args[1]["generate_companions"])
        self.assertFalse(call_args[1]["use_default_world"])

    @patch("main.firestore_service")
    def test_update_campaign_success(self, mock_firestore_service):
        """Test successful campaign title update."""
        update_data = {"title": "Updated Adventure Title"}

        response = self.client.patch(
            "/api/campaigns/test-campaign", headers=self.test_headers, json=update_data
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data[KEY_SUCCESS])
        self.assertIn("updated successfully", data[KEY_MESSAGE])

        mock_firestore_service.update_campaign_title.assert_called_once_with(
            DEFAULT_TEST_USER, "test-campaign", "Updated Adventure Title"
        )

    @patch("main.firestore_service")
    def test_update_campaign_missing_title(self, mock_firestore_service):
        """Test campaign update with missing title."""
        update_data = {}

        response = self.client.patch(
            "/api/campaigns/test-campaign", headers=self.test_headers, json=update_data
        )

        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn(KEY_ERROR, data)
        self.assertIn("required", data[KEY_ERROR].lower())

    @patch("main.firestore_service")
    def test_update_campaign_service_error(self, mock_firestore_service):
        """Test campaign update with service error."""
        mock_firestore_service.update_campaign_title.side_effect = Exception(
            "Update failed"
        )
        update_data = {"title": "New Title"}

        response = self.client.patch(
            "/api/campaigns/test-campaign", headers=self.test_headers, json=update_data
        )

        self.assertEqual(response.status_code, 500)
        data = response.get_json()
        self.assertIn(KEY_ERROR, data)
        self.assertIn("Failed to update", data[KEY_ERROR])

    @patch("main.firestore_service")
    @patch("main.document_generator")
    def test_export_campaign_txt_success(self, mock_doc_gen, mock_firestore_service):
        """Test successful campaign export as TXT."""
        # Mock campaign data
        mock_campaign = {"title": "Test Campaign"}
        mock_story = [
            {"actor": "user", "text": "Player action", "mode": "character"},
            {"actor": "gemini", "text": "AI response", "mode": "character"},
        ]
        mock_firestore_service.get_campaign_by_id.return_value = (
            mock_campaign,
            mock_story,
        )

        # Mock file operations
        temp_file = "/tmp/test_export.txt"
        with (
            patch("os.path.exists", return_value=True),
            patch("tempfile.mkdtemp", return_value="/tmp/exports"),
            patch("os.makedirs"),
            patch("uuid.uuid4", return_value="test-uuid"),
            patch("main.send_file") as mock_send_file,
        ):
            mock_send_file.return_value = MagicMock()

            response = self.client.get(
                "/api/campaigns/test-campaign/export?format=txt",
                headers=self.test_headers,
            )

            mock_doc_gen.generate_txt.assert_called_once()
            mock_send_file.assert_called_once()

    @patch("main.firestore_service")
    def test_export_campaign_not_found(self, mock_firestore_service):
        """Test campaign export when campaign doesn't exist."""
        mock_firestore_service.get_campaign_by_id.return_value = (None, None)

        response = self.client.get(
            "/api/campaigns/nonexistent/export", headers=self.test_headers
        )

        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertIn(KEY_ERROR, data)
        self.assertIn("not found", data[KEY_ERROR].lower())

    @patch("main.firestore_service")
    def test_export_campaign_unsupported_format(self, mock_firestore_service):
        """Test campaign export with unsupported format."""
        mock_campaign = {"title": "Test Campaign"}
        mock_story = []
        mock_firestore_service.get_campaign_by_id.return_value = (
            mock_campaign,
            mock_story,
        )

        response = self.client.get(
            "/api/campaigns/test-campaign/export?format=invalid",
            headers=self.test_headers,
        )

        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn(KEY_ERROR, data)
        self.assertIn("Unsupported format", data[KEY_ERROR])

    @patch("main.firestore_service")
    def test_export_campaign_generation_error(self, mock_firestore_service):
        """Test campaign export with file generation error."""
        mock_campaign = {"title": "Test Campaign"}
        mock_story = []
        mock_firestore_service.get_campaign_by_id.return_value = (
            mock_campaign,
            mock_story,
        )

        with patch("os.path.exists", return_value=False):
            response = self.client.get(
                "/api/campaigns/test-campaign/export?format=txt",
                headers=self.test_headers,
            )

            self.assertEqual(response.status_code, 500)
            data = response.get_json()
            self.assertIn(KEY_ERROR, data)
            self.assertIn("Failed to create", data[KEY_ERROR])


class TestFrontendRoutes(unittest.TestCase):
    """Test frontend serving routes."""

    def setUp(self):
        """Set up test client."""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_serve_root_path(self):
        """Test serving root path returns index.html."""
        with patch("main.send_from_directory") as mock_send:
            mock_send.return_value = "index.html content"

            response = self.client.get("/")

            # Should serve index.html from static folder (explicit path since static_folder=None)
            # Navigate from test file -> tests dir -> mvp_site dir -> static dir
            test_dir = os.path.dirname(os.path.abspath(__file__))
            mvp_site_dir = os.path.dirname(test_dir)
            expected_static_path = os.path.join(mvp_site_dir, 'static')
            mock_send.assert_called_with(expected_static_path, "index.html")

    def test_serve_existing_static_file(self):
        """Test serving existing static file."""
        with (
            patch("os.path.exists", return_value=True),
            patch("main.send_from_directory") as mock_send,
        ):
            mock_send.return_value = "css content"

            response = self.client.get("/styles.css")

            # Should serve the actual file (explicit path since static_folder=None)
            # Navigate from test file -> tests dir -> mvp_site dir -> static dir
            test_dir = os.path.dirname(os.path.abspath(__file__))
            mvp_site_dir = os.path.dirname(test_dir)
            expected_static_path = os.path.join(mvp_site_dir, 'static')
            mock_send.assert_called_with(expected_static_path, "styles.css")

    def test_serve_nonexistent_file_fallback(self):
        """Test serving nonexistent file falls back to index.html."""
        with (
            patch("os.path.exists", return_value=False),
            patch("main.send_from_directory") as mock_send,
        ):
            mock_send.return_value = "index.html content"

            response = self.client.get("/nonexistent/path")

            # Should fallback to index.html (explicit path since static_folder=None)
            # Navigate from test file -> tests dir -> mvp_site dir -> static dir
            test_dir = os.path.dirname(os.path.abspath(__file__))
            mvp_site_dir = os.path.dirname(test_dir)
            expected_static_path = os.path.join(mvp_site_dir, 'static')
            mock_send.assert_called_with(expected_static_path, "index.html")


    # Cache Busting Tests (moved from test_cache_busting_red_green.py)
    def test_static_js_file_normal_caching_green(self):
        """GREEN: Test that JS files have normal caching without special header."""
        response = self.client.get('/static/app.js')
        
        # Should have normal caching (not full no-cache)
        cache_control = response.headers.get('Cache-Control', '')
        self.assertNotEqual(cache_control, 'no-cache, no-store, must-revalidate')
        self.assertNotIn('Pragma', response.headers)
        self.assertNotIn('Expires', response.headers)

    def test_static_js_file_cache_busting_green(self):
        """GREEN: Test that JS files disable caching with X-No-Cache header."""
        response = self.client.get('/static/app.js', headers={'X-No-Cache': 'true'})
        
        # Should have full cache busting
        self.assertEqual(response.headers.get('Cache-Control'), 'no-cache, no-store, must-revalidate')
        self.assertEqual(response.headers.get('Pragma'), 'no-cache')
        self.assertEqual(response.headers.get('Expires'), '0')

    def test_static_css_file_cache_busting_green(self):
        """GREEN: Test that CSS files also support cache busting."""
        response = self.client.get('/static/style.css', headers={'X-No-Cache': 'true'})
        
        # Should have full cache busting for CSS too
        self.assertEqual(response.headers.get('Cache-Control'), 'no-cache, no-store, must-revalidate')
        self.assertEqual(response.headers.get('Pragma'), 'no-cache')
        self.assertEqual(response.headers.get('Expires'), '0')

    def test_non_js_css_files_unaffected_green(self):
        """GREEN: Test that non-JS/CSS files are not affected by cache busting."""
        # Create a mock image file response
        with patch('main.send_from_directory') as mock_send:
            mock_response = MagicMock()
            mock_response.headers = {}
            mock_send.return_value = mock_response
            
            response = self.client.get('/static/image.png', headers={'X-No-Cache': 'true'})
            
            # Should not have cache busting headers for non-JS/CSS files
            self.assertNotIn('Cache-Control', mock_response.headers)
            self.assertNotIn('Pragma', mock_response.headers)
            self.assertNotIn('Expires', mock_response.headers)

    def test_handle_interaction_fallback_green(self):
        """GREEN: Test that /handle_interaction returns helpful fallback message."""
        response = self.client.post('/handle_interaction', 
                                   json={'input': 'test'},
                                   headers={'Content-Type': 'application/json'})
        
        # Should return 410 Gone with helpful message
        self.assertEqual(response.status_code, 410)
        data = response.get_json()
        self.assertIn('error', data)
        self.assertIn('refresh', data['error'].lower())
        self.assertIn('cache', data['redirect_message'].lower())  # Cache is in redirect_message
        self.assertEqual(data['status'], 'cache_issue')


if __name__ == "__main__":
    unittest.main()
