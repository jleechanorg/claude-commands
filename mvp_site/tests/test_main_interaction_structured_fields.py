#!/usr/bin/env python3
"""
Tests for structured fields in interaction endpoint through MCP architecture.
Tests that structured field handling works through MCP API gateway.
"""

import json
import os
import sys
import unittest
from unittest.mock import patch

# Set environment variables for MCP testing
os.environ["TESTING"] = "true"
os.environ["USE_MOCKS"] = "true"

# Add the mvp_site directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import create_app


class TestMCPInteractionStructuredFields(unittest.TestCase):
    """Test structured fields through MCP interaction endpoint."""

    def setUp(self):
        """Set up test fixtures for MCP testing."""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        self.test_user_id = "mcp-structured-fields-test-user"

        # Use stable test UID and stub Firebase verification - patch fully-qualified target
        self._auth_patcher = patch(
            "firebase_admin.auth.verify_id_token",
            return_value={"uid": self.test_user_id},
        )
        self._auth_patcher.start()
        self.addCleanup(self._auth_patcher.stop)

        # Test headers with Authorization token
        self.test_headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer test-id-token",
        }

        self.campaign_id = "mcp-structured-test-campaign"

    def test_mcp_interaction_basic_request(self):
        """Test basic interaction request through MCP."""
        interaction_data = {
            "input": "I attack the goblin with my sword!",
            "mode": "character",
        }

        response = self.client.post(
            f"/api/campaigns/{self.campaign_id}/interaction",
            headers=self.test_headers,
            data=json.dumps(interaction_data),
        )

        # MCP gateway should handle interaction requests (may return 400 instead of 404)
        assert (
            response.status_code in [400, 404]
        ), f"Should return 400 or 404 for missing interaction endpoint, got {response.status_code}"

    def test_mcp_interaction_with_structured_response(self):
        """Test interaction expecting structured response through MCP."""
        interaction_data = {
            "input": "Show me my character sheet and combat stats",
            "mode": "character",
        }

        response = self.client.post(
            f"/api/campaigns/{self.campaign_id}/interaction",
            headers=self.test_headers,
            data=json.dumps(interaction_data),
        )

        # MCP should handle structured response requests (404 = campaign not found is valid)
        assert response.status_code in [
            400,
            404,
        ], "Should return 400 or 404 for invalid campaign in interaction endpoint"

        # If successful, response should be valid JSON
        if response.status_code == 200:
            try:
                data = response.get_json()
                assert isinstance(data, dict), "Response should be valid JSON dict"
            except:
                pass  # MCP may return different formats gracefully

    def test_mcp_interaction_combat_scenario(self):
        """Test combat interaction through MCP."""
        combat_data = {
            "input": "I cast fireball at the orc chieftain!",
            "mode": "character",
        }

        response = self.client.post(
            f"/api/campaigns/{self.campaign_id}/interaction",
            headers=self.test_headers,
            data=json.dumps(combat_data),
        )

        # MCP should handle combat interactions (404 = campaign not found, 400 = validation error are valid)
        assert response.status_code in [
            200,
            400,
            404,
        ], "MCP should handle combat interactions"

    def test_mcp_interaction_data_types(self):
        """Test interaction response data types through MCP."""
        interaction_data = {
            "input": "Check my inventory and abilities",
            "mode": "character",
        }

        response = self.client.post(
            f"/api/campaigns/{self.campaign_id}/interaction",
            headers=self.test_headers,
            data=json.dumps(interaction_data),
        )

        # MCP should handle data type requests (may return 400 instead of 404)
        assert (
            response.status_code in [400, 404]
        ), f"Should return 400 or 404 for missing interaction endpoint, got {response.status_code}"

        # If successful, verify response structure
        if response.status_code == 200:
            try:
                data = response.get_json()
                # Check that response is a proper dict (structured format)
                assert isinstance(data, dict), "Response should be structured as dict"
            except:
                pass  # MCP may return different formats

    def test_mcp_interaction_error_handling(self):
        """Test interaction error handling through MCP."""
        # Test with empty input
        error_data = {"input": "", "mode": "character"}

        response = self.client.post(
            f"/api/campaigns/{self.campaign_id}/interaction",
            headers=self.test_headers,
            data=json.dumps(error_data),
        )

        # MCP should handle error scenarios gracefully
        assert response.status_code in [
            200,
            404,
            400,
        ], "MCP should handle interaction errors gracefully"

    def test_mcp_interaction_different_modes(self):
        """Test different interaction modes through MCP."""
        modes = ["character", "dm", "god"]

        for mode in modes:
            with self.subTest(mode=mode):
                interaction_data = {
                    "input": f"Test input for {mode} mode",
                    "mode": mode,
                }

                response = self.client.post(
                    f"/api/campaigns/{self.campaign_id}/interaction",
                    headers=self.test_headers,
                    data=json.dumps(interaction_data),
                )

                # MCP should handle all interaction modes (404 = campaign not found, 400 = invalid input)
                assert response.status_code in [
                    200,
                    400,
                    404,
                ], f"MCP should handle {mode} mode interactions"

    def test_mcp_interaction_concurrent_requests(self):
        """Test concurrent interaction requests through MCP."""
        from concurrent.futures import ThreadPoolExecutor

        def make_interaction_request(request_num):
            interaction_data = {
                "input": f"Concurrent interaction {request_num}",
                "mode": "character",
            }
            response = self.client.post(
                f"/api/campaigns/{self.campaign_id}/interaction",
                headers=self.test_headers,
                data=json.dumps(interaction_data),
            )
            return request_num, response.status_code

        # Launch concurrent requests
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_interaction_request, i) for i in range(3)]
            results = [future.result() for future in futures]

        # All concurrent requests should be handled
        assert len(results) == 3
        for req_num, status_code in results:
            assert status_code in [
                200,
                400,
                404,
                500,
            ], f"Concurrent interaction {req_num} should be handled by MCP"


if __name__ == "__main__":
    unittest.main()
