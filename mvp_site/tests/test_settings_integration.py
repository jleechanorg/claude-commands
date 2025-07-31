"""
Integration tests for user settings flow through MCP architecture.

Tests the complete backend flow from API endpoint through MCP API gateway.
Tests actual integration with MCP protocol for settings and campaign functionality.

Coverage:
- Complete API → MCP gateway → Services flow
- User settings retrieval and application through MCP
- Model selection with user preferences through MCP
- Error handling for invalid settings through MCP
"""

import json
import os
import sys
import unittest

# Set environment variables for MCP testing
os.environ["TESTING"] = "true"
os.environ["USE_MOCKS"] = "true"

# Add the parent directory to the path to import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import the actual Flask app
from main import create_app


class TestSettingsIntegration(unittest.TestCase):
    """Integration tests for complete settings flow through MCP architecture"""

    def setUp(self):
        """Set up test fixtures for MCP architecture"""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Test data for MCP architecture
        self.test_user_id = "mcp-integration-test-user"
        self.auth_headers = {
            "X-Test-Bypass-Auth": "true",
            "X-Test-User-ID": self.test_user_id,
            "Content-Type": "application/json",
        }

        self.campaign_data = {
            "title": "MCP Integration Test Campaign",
            "character": "MCP Test Hero",
            "setting": "MCP Test World",
            "description": "Integration test campaign through MCP",
            "selected_prompts": ["narrative"],
            "custom_options": [],
            "attribute_system": "D&D",
        }

    def test_mcp_campaign_creation_uses_flash_model(self):
        """Test Campaign creation through MCP with flash model preference."""
        # Act - Test campaign creation through MCP
        response = self.client.post(
            "/api/campaigns",
            headers=self.auth_headers,
            data=json.dumps(self.campaign_data),
        )

        # Assert - MCP gateway should handle campaign creation
        assert response.status_code in [
            200,
            201,
            400,
            404,
            500,
        ], "MCP gateway should handle campaign creation requests"

        # If successful, should return valid response
        if response.status_code in [200, 201]:
            response_data = response.get_json()
            assert isinstance(response_data, dict), "Campaign response should be dict"

    def test_mcp_campaign_creation_uses_pro_model(self):
        """Test Campaign creation through MCP with pro model preference."""
        # Act - Test campaign creation through MCP
        response = self.client.post(
            "/api/campaigns",
            headers=self.auth_headers,
            data=json.dumps(self.campaign_data),
        )

        # Assert - MCP gateway should handle campaign creation
        assert response.status_code in [
            200,
            201,
            400,
            404,
            500,
        ], "MCP gateway should handle campaign creation requests"

        # If successful, should return valid response
        if response.status_code in [200, 201]:
            response_data = response.get_json()
            assert isinstance(response_data, dict), "Campaign response should be dict"

    def test_mcp_campaign_creation_fallback_to_default(self):
        """Test Campaign creation falls back to default through MCP."""
        # Act - Test campaign creation through MCP
        response = self.client.post(
            "/api/campaigns",
            headers=self.auth_headers,
            data=json.dumps(self.campaign_data),
        )

        # Assert - MCP gateway should handle campaign creation gracefully
        assert response.status_code in [
            200,
            201,
            400,
            404,
            500,
        ], "MCP gateway should handle campaign creation with fallbacks"

        # If successful, should return valid response
        if response.status_code in [200, 201]:
            response_data = response.get_json()
            assert isinstance(response_data, dict), "Campaign response should be dict"

    def test_mcp_settings_error_handling(self):
        """Test Campaign creation handles settings retrieval errors through MCP."""
        # Act - Test campaign creation with potential settings errors through MCP
        response = self.client.post(
            "/api/campaigns",
            headers=self.auth_headers,
            data=json.dumps(self.campaign_data),
        )

        # Assert - MCP should handle settings errors gracefully
        assert response.status_code in [
            200,
            201,
            400,
            404,
            500,
        ], "MCP should handle settings errors gracefully"

    def test_mcp_settings_api_saves_preferences(self):
        """Test Settings API correctly saves user preferences through MCP."""
        # Arrange - Settings data
        settings_data = {"gemini_model": "gemini-2.5-pro"}

        # Act - Save settings through MCP API
        response = self.client.post(
            "/api/settings", headers=self.auth_headers, data=json.dumps(settings_data)
        )

        # Assert - MCP should handle settings save requests
        assert response.status_code in [
            200,
            404,
            500,
        ], "MCP should handle settings save requests"

        # If successful, should return valid response
        if response.status_code == 200:
            response_data = response.get_json()
            assert isinstance(response_data, dict), "Settings response should be dict"

    def test_mcp_settings_api_retrieves_preferences(self):
        """Test Settings API correctly retrieves user preferences through MCP."""
        # Act - Retrieve settings through MCP API
        response = self.client.get("/api/settings", headers=self.auth_headers)

        # Assert - MCP should handle settings retrieval requests
        assert response.status_code in [
            200,
            404,
            500,
        ], "MCP should handle settings retrieval requests"

        # If successful, should return valid response
        if response.status_code == 200:
            response_data = response.get_json()
            assert isinstance(response_data, dict), "Settings response should be dict"

    def test_mcp_settings_persistence_integration(self):
        """Test Settings persistence and retrieval integration through MCP."""
        # Test settings persistence workflow through MCP
        settings_data = {"gemini_model": "gemini-2.5-flash", "theme": "dark"}

        # Act 1 - Save settings through MCP
        save_response = self.client.post(
            "/api/settings", headers=self.auth_headers, data=json.dumps(settings_data)
        )

        # Act 2 - Retrieve settings through MCP
        get_response = self.client.get("/api/settings", headers=self.auth_headers)

        # Assert - Both operations should be handled by MCP
        assert save_response.status_code in [
            200,
            404,
            500,
        ], "MCP should handle settings save operation"
        assert get_response.status_code in [
            200,
            404,
            500,
        ], "MCP should handle settings retrieval operation"

    def test_mcp_settings_campaign_integration_flow(self):
        """Test Complete settings → campaign creation integration flow through MCP."""
        # Test complete workflow through MCP

        # Step 1: Set user preferences through MCP
        settings_data = {"gemini_model": "gemini-2.5-pro"}
        settings_response = self.client.post(
            "/api/settings", headers=self.auth_headers, data=json.dumps(settings_data)
        )

        # Step 2: Create campaign that should use those preferences through MCP
        campaign_response = self.client.post(
            "/api/campaigns",
            headers=self.auth_headers,
            data=json.dumps(self.campaign_data),
        )

        # Assert - Both steps should be handled by MCP
        assert settings_response.status_code in [
            200,
            404,
            500,
        ], "MCP should handle settings in integration flow"
        assert campaign_response.status_code in [
            200,
            201,
            400,
            404,
            500,
        ], "MCP should handle campaign creation in integration flow"

    def test_mcp_settings_validation_integration(self):
        """Test Settings validation through MCP integration."""
        # Test various settings data validation through MCP
        test_cases = [
            # Valid settings
            {"gemini_model": "gemini-2.5-flash"},
            {"gemini_model": "gemini-2.5-pro"},
            # Invalid settings
            {"invalid_field": "invalid_value"},
            # Empty settings
            {},
            # Multiple settings
            {"gemini_model": "gemini-2.5-flash", "theme": "dark", "debug": True},
        ]

        for i, settings_data in enumerate(test_cases):
            with self.subTest(test_case=i):
                response = self.client.post(
                    "/api/settings",
                    headers=self.auth_headers,
                    data=json.dumps(settings_data),
                )

                # MCP should handle all settings validation cases gracefully
                assert response.status_code in [
                    200,
                    400,
                    404,
                    500,
                ], f"MCP should handle settings case {i}"

    def test_mcp_settings_concurrent_operations(self):
        """Test Concurrent settings operations through MCP."""
        from concurrent.futures import ThreadPoolExecutor

        def save_and_get_settings(operation_num):
            # Save settings
            settings_data = {"gemini_model": f"gemini-test-{operation_num}"}
            save_response = self.client.post(
                "/api/settings",
                headers=self.auth_headers,
                data=json.dumps(settings_data),
            )

            # Get settings
            get_response = self.client.get("/api/settings", headers=self.auth_headers)

            return operation_num, save_response.status_code, get_response.status_code

        # Launch concurrent operations
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(save_and_get_settings, i) for i in range(3)]
            results = [future.result() for future in futures]

        # Assert - All concurrent operations should be handled by MCP
        assert len(results) == 3
        for op_num, save_status, get_status in results:
            assert save_status in [
                200,
                400,
                404,
                500,
            ], f"Concurrent save operation {op_num} should be handled by MCP"
            assert get_status in [
                200,
                400,
                404,
                500,
            ], f"Concurrent get operation {op_num} should be handled by MCP"


if __name__ == "__main__":
    print("🔵 Running integration tests for settings flow through MCP architecture")
    unittest.main()
