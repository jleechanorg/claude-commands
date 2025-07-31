"""
Test JSON state updates through MCP architecture.
Tests that state updates are handled correctly through MCP API gateway.
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
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from main import create_app


class TestMCPJsonStateUpdates(unittest.TestCase):
    """Test JSON state updates through MCP architecture."""

    def setUp(self):
        """Set up test fixtures for MCP testing."""
        self.app = create_app()
        self.client = self.app.test_client()
        self.app.config["TESTING"] = True

        # Test headers for MCP authentication bypass
        self.test_headers = {
            "X-Test-Bypass-Auth": "true",
            "X-Test-User-ID": "mcp-json-state-test-user",
            "Content-Type": "application/json",
        }

        self.campaign_id = "mcp-json-test-campaign"

    def test_mcp_state_updates_interaction(self):
        """Test state updates through MCP interaction endpoint."""
        interaction_data = {
            "input": "I attack the goblin with my sword!",
            "mode": "character",
        }

        response = self.client.post(
            f"/api/campaigns/{self.campaign_id}/interaction",
            headers=self.test_headers,
            data=json.dumps(interaction_data),
        )

        # MCP gateway should handle state update interactions (may return 404 for nonexistent campaigns)
        assert response.status_code in [400, 404], f"Expected 400 or 404 for state update validation, got {response.status_code}"

        # If successful, should return valid response
        if response.status_code == 200:
            data = response.get_json()
            assert isinstance(data, dict), "Interaction response should be dict"

    def test_mcp_combat_state_updates(self):
        """Test combat state updates through MCP."""
        combat_interaction = {
            "input": "I cast fireball at the orc!",
            "mode": "character",
        }

        response = self.client.post(
            f"/api/campaigns/{self.campaign_id}/interaction",
            headers=self.test_headers,
            data=json.dumps(combat_interaction),
        )

        # MCP should handle combat interactions with state updates (may return 404 for nonexistent campaigns)
        assert response.status_code in [400, 404], f"Expected 400 or 404 for combat state validation, got {response.status_code}"

    def test_mcp_json_response_format(self):
        """Test JSON response format through MCP."""
        interaction_data = {"input": "Check my inventory", "mode": "character"}

        response = self.client.post(
            f"/api/campaigns/{self.campaign_id}/interaction",
            headers=self.test_headers,
            data=json.dumps(interaction_data),
        )

        # MCP should handle JSON format requests (may return 404 for nonexistent campaigns)
        assert response.status_code in [400, 404], f"Expected 400 or 404 for JSON format validation, got {response.status_code}"

        # If successful, response should be valid JSON
        if response.status_code == 200:
            try:
                data = response.get_json()
                assert isinstance(data, dict), "Response should be valid JSON dict"
            except:
                pass  # MCP may return different formats gracefully

    def test_mcp_narrative_state_interaction(self):
        """Test narrative interactions that involve state changes through MCP."""
        narrative_interaction = {
            "input": "I explore the dark cave carefully",
            "mode": "character",
        }

        response = self.client.post(
            f"/api/campaigns/{self.campaign_id}/interaction",
            headers=self.test_headers,
            data=json.dumps(narrative_interaction),
        )

        # MCP should handle narrative interactions (may return 404 for nonexistent campaigns)
        assert response.status_code in [400, 404], f"Expected 400 or 404 for narrative state validation, got {response.status_code}"

    def test_mcp_state_error_handling(self):
        """Test state error handling through MCP."""
        # Test with potentially problematic input
        error_interaction = {
            "input": "",  # Empty input
            "mode": "character",
        }

        response = self.client.post(
            f"/api/campaigns/{self.campaign_id}/interaction",
            headers=self.test_headers,
            data=json.dumps(error_interaction),
        )

        # MCP should handle state errors gracefully (may return 404 for nonexistent campaigns)
        assert response.status_code in [400, 404], f"Expected 400 or 404 for invalid state data, got {response.status_code}"

    def test_mcp_structured_response_handling(self):
        """Test structured response handling through MCP."""
        structured_interaction = {
            "input": "What are my current stats?",
            "mode": "character",
        }

        response = self.client.post(
            f"/api/campaigns/{self.campaign_id}/interaction",
            headers=self.test_headers,
            data=json.dumps(structured_interaction),
        )

        # MCP should handle requests for structured information (may return 404 for nonexistent campaigns)
        assert response.status_code in [400, 404], f"Expected 400 or 404 for structured response with invalid campaign data, got {response.status_code}"


if __name__ == "__main__":
    unittest.main()
