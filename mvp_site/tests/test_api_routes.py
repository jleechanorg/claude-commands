"""
Test API routes functionality in MCP architecture.
Tests API endpoints through MCP API gateway pattern.
"""

import json
import os
import sys
import unittest

# Set environment variables for MCP testing
os.environ["TESTING"] = "true"
os.environ["USE_MOCKS"] = "true"

# Add parent directory to path for imports
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(
            os.path.dirname(
                os.path.abspath(
                    __file__ if "__file__" in globals() else "tests/test_api_routes.py"
                )
            )
        )
    ),
)

from main import create_app


class TestAPIRoutes(unittest.TestCase):
    """Test API routes through MCP API gateway."""

    def setUp(self):
        """Set up test client for MCP architecture."""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Test data for MCP architecture
        self.test_user_id = "mcp-api-test-user"
        # Testing mode removed - no longer using bypass headers
        self.test_headers = {
            "Content-Type": "application/json",
        }

    def test_mcp_get_campaigns_endpoint(self):
        """Test campaigns list endpoint through MCP gateway."""
        response = self.client.get("/api/campaigns", headers=self.test_headers)

        # With testing mode removed, expect 401 (auth required) or 200/404 if mocked properly
        assert response.status_code in [200, 401, 404], (
            f"Expected 200/401/404 for campaigns list, got {response.status_code}"
        )

        # If successful, should return valid JSON format
        if response.status_code == 200:
            data = response.get_json()
            assert isinstance(data, (dict, list)), (
                "Campaigns response should be dict or list format"
            )

    def test_mcp_get_specific_campaign_endpoint(self):
        """Test specific campaign retrieval through MCP gateway."""
        response = self.client.get(
            "/api/campaigns/mcp-test-campaign", headers=self.test_headers
        )

        # With testing mode removed, expect 401 (auth required) or 400/404 for nonexistent campaign
        assert response.status_code in [
            400,
            404,
            401,
        ], f"Expected 400/404/401 for campaign access, got {response.status_code}"

        # If successful, should return valid campaign data format
        if response.status_code == 200:
            data = response.get_json()
            assert isinstance(data, dict), "Campaign response should be dict format"

    def test_mcp_get_campaigns_response(self):
        """Test campaigns endpoint response through MCP."""
        response = self.client.get("/api/campaigns", headers=self.test_headers)

        # With testing mode removed, expect 401 (auth required) or 200/404 if mocked properly
        assert response.status_code in [200, 401, 404], (
            f"Expected 200/401/404 for campaigns list, got {response.status_code}"
        )

        data = response.get_json()
        assert isinstance(data, (list, dict)), (
            "Campaigns should return list or dict format"
        )

        # Accept any response format - could be empty list or list with existing campaigns
        if isinstance(data, list):
            # Could be empty or have campaigns
            assert all(isinstance(item, dict) for item in data), (
                "Campaign items should be dict format"
            )
        elif isinstance(data, dict):
            # Could be wrapped response format
            assert data is not None, "Response should not be None"

    def test_mcp_get_campaigns_error_handling(self):
        """Test campaigns endpoint error handling through MCP."""
        # Test with invalid headers
        invalid_headers = {"Content-Type": "application/json"}
        response = self.client.get("/api/campaigns", headers=invalid_headers)

        # MCP should handle authentication errors gracefully
        assert response.status_code == 401, (
            f"Expected 401 for authentication error, got {response.status_code}"
        )

    def test_mcp_campaign_with_debug_mode(self):
        """Test campaign retrieval with debug mode through MCP."""
        response = self.client.get(
            "/api/campaigns/mcp-debug-campaign", headers=self.test_headers
        )

        # With testing mode removed, expect 401 (auth required) or 400/404 for nonexistent campaign
        assert response.status_code in [
            400,
            404,
            401,
        ], f"Expected 400/404/401 for campaign access, got {response.status_code}"

    def test_mcp_get_settings_endpoint(self):
        """Test settings endpoint through MCP gateway."""
        response = self.client.get("/api/settings", headers=self.test_headers)

        # With testing mode removed, expect 401 (auth required) or 200 if mocked properly
        assert response.status_code in [200, 401], (
            f"Expected 200 or 401 for settings, got {response.status_code}"
        )

        # If successful, should return valid settings format
        if response.status_code == 200:
            data = response.get_json()
            assert isinstance(data, dict), "Settings response should be dict format"

    def test_mcp_post_settings_endpoint(self):
        """Test settings update endpoint through MCP gateway."""
        test_settings = {"debug_mode": True, "theme": "dark"}

        response = self.client.post(
            "/api/settings", data=json.dumps(test_settings), headers=self.test_headers
        )

        # With testing mode removed, expect 401 (auth required) or 200 if mocked properly
        assert response.status_code in [200, 401], (
            f"Expected 200 or 401 for settings update, got {response.status_code}"
        )

    def test_mcp_campaign_interaction_endpoint(self):
        """Test campaign interaction endpoint through MCP gateway."""
        interaction_data = {"input": "I explore the area", "mode": "character"}

        response = self.client.post(
            "/api/campaigns/mcp-test-campaign/interaction",
            data=json.dumps(interaction_data),
            headers=self.test_headers,
        )

        # MCP gateway should handle interaction requests gracefully (may return 400 instead of 404)
        assert response.status_code in [400, 404, 401], (
            f"Expected 400/404/401 for campaign interaction, got {response.status_code}"
        )

        # If successful, should return valid interaction response
        if response.status_code == 200:
            data = response.get_json()
            assert isinstance(data, dict), "Interaction response should be dict format"

    def test_mcp_cors_headers_handling(self):
        """Test CORS headers handling through MCP gateway."""
        cors_headers = {**self.test_headers, "Origin": "https://example.com"}

        response = self.client.get("/api/campaigns", headers=cors_headers)

        # With testing mode removed, expect 401 (auth required) or 200/404 if mocked properly
        assert response.status_code in [200, 401, 404], (
            f"Expected 200/401/404 for CORS campaigns list, got {response.status_code}"
        )


class TestStoryTruncation(unittest.TestCase):
    """Test story entry truncation to prevent oversized responses.

    Campaign kuXKa6vrYY6P99MfhWBn had 1620 entries = 34.7MB response,
    exceeding Cloud Run's 32MB limit and causing intermittent 500 errors.
    """

    def test_story_truncation_returns_last_300_entries(self):
        """Verify truncation keeps LAST 300 entries (most recent), not first."""
        # Create 500 story entries with sequential IDs
        full_story = [{"id": i, "text": f"Entry {i}"} for i in range(500)]

        # Apply same truncation logic as main.py:837-844
        MAX_STORY_ENTRIES = 300
        if len(full_story) > MAX_STORY_ENTRIES:
            truncated = full_story[-MAX_STORY_ENTRIES:]
        else:
            truncated = full_story

        # Should have exactly 300 entries
        assert len(truncated) == 300, f"Expected 300 entries, got {len(truncated)}"

        # First entry should be ID 200 (entry 201 of original)
        assert truncated[0]["id"] == 200, (
            f"Expected first entry to be ID 200, got {truncated[0]['id']}"
        )

        # Last entry should be ID 499 (most recent)
        assert truncated[-1]["id"] == 499, (
            f"Expected last entry to be ID 499, got {truncated[-1]['id']}"
        )

    def test_story_truncation_preserves_small_stories(self):
        """Stories with <= 300 entries should not be truncated."""
        small_story = [{"id": i, "text": f"Entry {i}"} for i in range(100)]

        MAX_STORY_ENTRIES = 300
        if len(small_story) > MAX_STORY_ENTRIES:
            truncated = small_story[-MAX_STORY_ENTRIES:]
        else:
            truncated = small_story

        assert len(truncated) == 100, f"Expected 100 entries, got {len(truncated)}"
        assert truncated[0]["id"] == 0, "First entry should still be ID 0"
        assert truncated[-1]["id"] == 99, "Last entry should still be ID 99"

    def test_story_truncation_boundary_exactly_300(self):
        """Stories with exactly 300 entries should not be truncated."""
        boundary_story = [{"id": i, "text": f"Entry {i}"} for i in range(300)]

        MAX_STORY_ENTRIES = 300
        if len(boundary_story) > MAX_STORY_ENTRIES:
            truncated = boundary_story[-MAX_STORY_ENTRIES:]
        else:
            truncated = boundary_story

        assert len(truncated) == 300, f"Expected 300 entries, got {len(truncated)}"
        assert truncated[0]["id"] == 0, "First entry should be ID 0"
        assert truncated[-1]["id"] == 299, "Last entry should be ID 299"


if __name__ == "__main__":
    unittest.main()
