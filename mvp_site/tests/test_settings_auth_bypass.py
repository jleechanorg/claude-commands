#!/usr/bin/env python3
"""
Tests for settings authentication bypass through MCP architecture.
Tests verification that auth bypass works through MCP API gateway.
"""

import json
import os
import sys
import unittest

# Set environment variables for MCP testing
os.environ["TESTING"] = "true"
os.environ["USE_MOCKS"] = "true"

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import create_app


class TestMCPSettingsAuthBypass(unittest.TestCase):
    """Test settings authentication bypass through MCP API gateway."""

    def setUp(self):
        """Set up Flask test client for MCP architecture."""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.test_user_id = "mcp-settings-auth-test-user"

        # Headers for MCP authentication bypass
        self.bypass_headers = {
            "X-Test-Bypass-Auth": "true",
            "X-Test-User-ID": self.test_user_id,
            "Content-Type": "application/json",
        }

    def test_mcp_settings_page_auth_bypass(self):
        """Test settings page auth bypass through MCP."""
        response = self.client.get("/settings", headers=self.bypass_headers)

        # MCP gateway should handle settings page requests with auth bypass
        assert (
            response.status_code == 200
        ), "MCP gateway should handle settings page with auth bypass"

    def test_mcp_settings_api_get_auth_bypass(self):
        """Test settings API GET with auth bypass through MCP."""
        response = self.client.get("/api/settings", headers=self.bypass_headers)

        # MCP gateway should handle settings API GET with auth bypass
        assert (
            response.status_code == 200
        ), "MCP gateway should handle settings API GET with auth bypass"

        # If successful, should return valid response
        if response.status_code == 200:
            data = response.get_json()
            assert isinstance(data, dict), "Settings response should be dict"

    def test_mcp_settings_api_post_auth_bypass(self):
        """Test settings API POST with auth bypass through MCP."""
        payload = {"gemini_model": "gemini-2.5-flash"}

        response = self.client.post(
            "/api/settings", headers=self.bypass_headers, data=json.dumps(payload)
        )

        # MCP gateway should handle settings API POST with auth bypass
        assert (
            response.status_code == 200
        ), "MCP gateway should handle settings API POST with auth bypass"

        # If successful, should return valid response
        if response.status_code == 200:
            data = response.get_json()
            assert isinstance(data, dict), "Settings response should be dict"

    def test_mcp_settings_without_auth_bypass(self):
        """Test settings without auth bypass through MCP."""
        # Test without auth bypass headers
        response = self.client.get("/settings")

        # MCP gateway should handle missing auth appropriately
        assert (
            response.status_code == 401
        ), "MCP gateway should handle missing auth for settings"

    def test_mcp_settings_partial_auth_headers(self):
        """Test settings with partial auth headers through MCP."""
        partial_headers = {
            "X-Test-Bypass-Auth": "true",
            "Content-Type": "application/json",
        }
        response = self.client.get("/api/settings", headers=partial_headers)

        # MCP gateway should handle partial auth headers
        assert (
            response.status_code == 401
        ), "MCP gateway should handle partial auth headers by requiring user ID"

    def test_mcp_settings_invalid_auth_headers(self):
        """Test settings with invalid auth headers through MCP."""
        invalid_headers = {
            "X-Test-Bypass-Auth": "false",
            "Content-Type": "application/json",
        }
        response = self.client.get("/api/settings", headers=invalid_headers)

        # MCP gateway should handle invalid auth headers
        assert (
            response.status_code == 401
        ), "MCP gateway should handle invalid auth headers"

    def test_mcp_settings_concurrent_auth_requests(self):
        """Test concurrent settings requests with auth bypass through MCP."""
        from concurrent.futures import ThreadPoolExecutor

        def make_settings_request(request_num):
            headers = {
                "X-Test-Bypass-Auth": "true",
                "X-Test-User-ID": f"mcp-concurrent-settings-user-{request_num}",
                "Content-Type": "application/json",
            }
            response = self.client.get("/api/settings", headers=headers)
            return request_num, response.status_code

        # Launch concurrent requests
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_settings_request, i) for i in range(3)]
            results = [future.result() for future in futures]

        # All concurrent requests should be handled
        assert len(results) == 3
        for req_num, status_code in results:
            assert (
                status_code == 200
            ), f"Concurrent settings request {req_num} should be handled by MCP with proper auth headers"


if __name__ == "__main__":
    # Run the failing tests to demonstrate the problem
    unittest.main(verbosity=2)
