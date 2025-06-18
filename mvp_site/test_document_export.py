import unittest
import os
import json
from unittest.mock import patch, MagicMock

# Set a dummy API key to prevent gemini_service from failing on import
os.environ["GEMINI_API_KEY"] = "DUMMY_KEY_FOR_EXPORT_TESTING"

# Mock firebase_admin before it's used by the app
# This is the key fix: we patch the library itself before our app code runs
mock_firebase_app = MagicMock()
patcher = patch('firebase_admin.initialize_app', return_value=mock_firebase_app)
patcher.start()

# Now it's safe to import 'main' because the above patch will catch the initialize_app call
import main

class TestExportEndpoint(unittest.TestCase):

    def setUp(self):
        """Set up a test client for the Flask application for each test."""
        # We patch gemini_service here to prevent it from initializing its client
        # during the creation of the app, as it's not needed for this test.
        with patch('main.gemini_service'):
            self.app = main.create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.user_id = "test-export-user-123"
        self.campaign_id = "test-campaign-id-456"

    # We patch the specific functions our endpoint uses
    @patch('main.firestore_service.get_campaign_by_id')
    @patch('main.document_generator.generate_pdf')
    def test_export_pdf_success(self, mock_generate_pdf, mock_get_campaign_by_id):
        """
        Tests the GET /export?format=pdf endpoint for a successful scenario.
        """
        print("\\n--- Running Test: test_export_pdf_success ---")

        # 1. Configure Mocks
        mock_get_campaign_by_id.return_value = (
            {'title': 'My Test Campaign'}, 
            [{'actor': 'gemini', 'text': 'A story starts.'}]
        )
        
        dummy_pdf_path = "test_output.pdf"
        with open(dummy_pdf_path, "w") as f:
            f.write("dummy pdf content")
        mock_generate_pdf.return_value = dummy_pdf_path

        # 2. Make the API Call
        response = self.client.get(
            f'/api/campaigns/{self.campaign_id}/export?format=pdf',
            headers={'X-Test-Bypass-Auth': 'true', 'X-Test-User-ID': self.user_id}
        )

        # 3. Assert Results
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'application/pdf')
        mock_get_campaign_by_id.assert_called_once_with(self.user_id, self.campaign_id)
        mock_generate_pdf.assert_called_once()
        
        # Clean up the dummy file
        os.remove(dummy_pdf_path)
        print("--- Test Finished Successfully ---")


    @patch('main.firestore_service.get_campaign_by_id')
    def test_export_campaign_not_found(self, mock_get_campaign_by_id):
        """
        Tests that the endpoint returns a 404 error if the campaign doesn't exist.
        """
        print("\\n--- Running Test: test_export_campaign_not_found ---")
        
        mock_get_campaign_by_id.return_value = (None, None)

        response = self.client.get(
            f'/api/campaigns/{self.campaign_id}/export?format=pdf',
            headers={'X-Test-Bypass-Auth': 'true', 'X-Test-User-ID': self.user_id}
        )
        
        self.assertEqual(response.status_code, 404)
        response_data = response.get_json()
        self.assertEqual(response_data['error'], 'Campaign not found')
        print("--- Test Finished Successfully ---")

    def tearDown(self):
        """Stop any class-wide patches."""
        # It's good practice to stop patchers you started, although for this test
        # it's less critical as it runs once at import time.
        patcher.stop()

if __name__ == '__main__':
    unittest.main()