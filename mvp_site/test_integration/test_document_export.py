import os
import shutil
import sys
import unittest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tempfile
from unittest.mock import MagicMock, patch

# Set a dummy API key to prevent gemini_service from failing on import
os.environ["GEMINI_API_KEY"] = "DUMMY_KEY_FOR_EXPORT_TESTING"

# Mock firebase_admin before it's used by the app
# This is the key fix: we patch the library itself before our app code runs
mock_firebase_app = MagicMock()
patcher = patch("firebase_admin.initialize_app", return_value=mock_firebase_app)
patcher.start()

# Now it's safe to import 'main' because the above patch will catch the initialize_app call
import main


class TestExportEndpoint(unittest.TestCase):
    def setUp(self):
        """Set up a test client for the Flask application for each test."""
        # We patch MCPClient to prevent it from initializing actual client
        # during the creation of the app, as it's not needed for this test.
        with patch("main.MCPClient"):
            self.app = main.create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.user_id = "test-export-user-123"
        self.campaign_id = "test-campaign-id-456"

    # We patch the specific functions our endpoint uses
    @patch("main.MCPClient")
    def test_export_pdf_success(self, mock_mcp_client_class):
        """
        Tests the GET /export?format=pdf endpoint for a successful scenario.
        """

        # Create a temporary file for testing first
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".pdf", delete=False
        ) as temp_file:
            temp_file.write("dummy pdf content")
            dummy_pdf_path = temp_file.name
        
        # 1. Configure MCP Mock
        mock_mcp_client = MagicMock()
        mock_mcp_client_class.return_value = mock_mcp_client
        
        # Mock multiple MCP calls: get_campaign_by_id and export_campaign
        async def mock_mcp_side_effect(tool_name, arguments):
            if tool_name == "export_campaign":
                # For export_campaign, the MCP server creates the file and returns the path
                # Let's create a temporary export file to simulate what the MCP server would do
                fd, export_temp_path = tempfile.mkstemp(
                    suffix=f".{arguments.get('format', 'pdf')}"
                )
                os.close(fd)
                shutil.copy2(dummy_pdf_path, export_temp_path)
                
                return {
                    "success": True,
                    "export_path": export_temp_path,
                    "campaign_title": "My Test Campaign"
                }
            return None
        
        mock_mcp_client.call_tool.side_effect = mock_mcp_side_effect

        try:
            # PDF generation is now handled in mock_mcp_side_effect above

            # 2. Make the API Call
            response = self.client.get(
                f"/api/campaigns/{self.campaign_id}/export?format=pdf",
                headers={"X-Test-Bypass-Auth": "true", "X-Test-User-ID": self.user_id},
            )

            # 3. Assert Results
            assert response.status_code == 200
            assert response.mimetype == "application/pdf"
            # Verify MCP client was called
            mock_mcp_client.call_tool.assert_called()
        finally:
            # Clean up the temporary file (always executed, even if test fails)
            if os.path.exists(dummy_pdf_path):
                os.remove(dummy_pdf_path)


    @patch("main.MCPClient")
    def test_export_campaign_not_found(self, mock_mcp_client_class):
        """
        Tests that the endpoint returns a 404 error if the campaign doesn't exist.
        """

        # Mock MCP call to return campaign not found
        mock_mcp_client = MagicMock()
        mock_mcp_client_class.return_value = mock_mcp_client
        
        async def mock_mcp_side_effect(tool_name, arguments):
            if tool_name == "export_campaign":
                # Return failure result indicating campaign not found
                return {
                    "success": False,
                    "error": "Campaign not found",
                    "status_code": 404
                }
            return None
        
        mock_mcp_client.call_tool.side_effect = mock_mcp_side_effect

        response = self.client.get(
            f"/api/campaigns/{self.campaign_id}/export?format=pdf",
            headers={"X-Test-Bypass-Auth": "true", "X-Test-User-ID": self.user_id},
        )

        assert response.status_code == 404
        response_data = response.get_json()
        assert response_data["error"] == "Campaign not found"

    @classmethod
    def tearDownClass(cls):
        """Stop module-level firebase_admin patch exactly once after all tests."""
        patcher.stop()


if __name__ == "__main__":
    unittest.main()
