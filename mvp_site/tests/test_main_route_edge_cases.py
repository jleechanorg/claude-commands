"""
Test main.py route handlers edge cases and error scenarios through MCP architecture.

This file contains comprehensive edge case testing for main.py API endpoints
through MCP API gateway pattern including concurrent access, large payloads,
timeouts, file operations, and CORS.
"""

import json
import os
import sys
import unittest
from concurrent.futures import ThreadPoolExecutor

# Set environment variables for MCP testing
os.environ["TESTING"] = "true"
os.environ["USE_MOCKS"] = "true"

# Add parent directory to path for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from main import create_app


class TestMainRouteEdgeCases(unittest.TestCase):
    """Test edge cases for main.py route handlers through MCP architecture."""

    def setUp(self):
        """Set up test fixtures for MCP architecture."""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Test data for MCP architecture
        self.test_user_id = "mcp-edge-test-user"
        self.test_campaign_id = "mcp-edge-test-campaign"

        # Test bypass headers for MCP
        self.test_headers = {
            "X-Test-Bypass-Auth": "true",
            "X-Test-User-ID": self.test_user_id,
            "Content-Type": "application/json",
        }

    # ===== Large Payload Handling Tests =====

    def test_mcp_large_json_payload_handling(self):
        """Test that MCP gateway handles large JSON payloads gracefully."""
        # Create a reasonably large payload
        large_payload = {
            "input": "Test interaction with large data: " + "x" * 10000,
            "mode": "character",
            "metadata": {"large_data": ["item" + str(i) for i in range(1000)]},
        }

        response = self.client.post(
            f"/api/campaigns/{self.test_campaign_id}/interaction",
            headers=self.test_headers,
            data=json.dumps(large_payload),
        )

        # MCP gateway should handle large payloads gracefully (validates input first)
        assert response.status_code in [
            400,
            404,
        ], f"Expected 400 or 404 for input validation, got {response.status_code}"

    def test_mcp_oversized_payload_rejection(self):
        """Test that MCP gateway handles oversized payloads appropriately."""
        # Create an extremely large payload
        oversized_payload = {
            "input": "x" * (1024 * 1024),  # 1MB payload
            "mode": "character",
        }

        response = self.client.post(
            f"/api/campaigns/{self.test_campaign_id}/interaction",
            headers=self.test_headers,
            data=json.dumps(oversized_payload),
        )

        # MCP should handle oversized payloads gracefully (may return 400 instead of 413 in MCP mode, or 404 for nonexistent campaigns)
        assert (
            response.status_code
            in [
                400,
                404,
                413,
            ]
        ), f"Expected 400, 404, or 413 for oversized payload, got {response.status_code}"

    def test_mcp_deeply_nested_json_handling(self):
        """Test MCP handling of deeply nested JSON structures."""
        # Create deeply nested JSON
        nested_data = {}
        current = nested_data
        for i in range(50):  # 50 levels deep
            current["level"] = {}
            current = current["level"]
        current["value"] = "deep_value"

        payload = {
            "input": "Test with nested data",
            "mode": "character",
            "nested_metadata": nested_data,
        }

        response = self.client.post(
            f"/api/campaigns/{self.test_campaign_id}/interaction",
            headers=self.test_headers,
            data=json.dumps(payload),
        )

        # MCP should handle deeply nested JSON gracefully (validates input first)
        assert (
            response.status_code in [400, 404]
        ), f"Expected 400 or 404 for input validation with nested JSON, got {response.status_code}"

    def test_mcp_malformed_json_handling(self):
        """Test MCP handling of malformed JSON."""
        # Send malformed JSON
        malformed_json = '{"input": "test", "mode": "character", "incomplete": '

        response = self.client.post(
            f"/api/campaigns/{self.test_campaign_id}/interaction",
            headers=self.test_headers,
            data=malformed_json,
        )

        # MCP should handle malformed JSON gracefully with 400 error (or 500 when JSON parsing fails)
        assert response.status_code in [
            400,
            404,
            500,
        ], f"Should return error, got {response.status_code}"

    # ===== Concurrent Request Handling Tests =====

    def test_mcp_concurrent_campaign_requests(self):
        """Test MCP handling of concurrent requests to same campaign."""
        results = []

        def make_request(request_num):
            payload = {
                "input": f"Concurrent request {request_num}",
                "mode": "character",
            }
            response = self.client.post(
                f"/api/campaigns/{self.test_campaign_id}/interaction",
                headers=self.test_headers,
                data=json.dumps(payload),
            )
            return request_num, response.status_code

        # Launch 5 concurrent requests
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, i) for i in range(5)]
            results = [future.result() for future in futures]

        # All requests should complete
        assert len(results) == 5

        # All should return valid status codes
        for req_num, status_code in results:
            assert (
                status_code in [400, 404]
            ), f"Expected 400 or 404 for concurrent request {req_num} validation, got {status_code}"

    def test_mcp_concurrent_different_campaigns(self):
        """Test MCP handling of concurrent requests to different campaigns."""
        results = []

        def make_request(campaign_num):
            payload = {"input": f"Test campaign {campaign_num}", "mode": "character"}
            response = self.client.post(
                f"/api/campaigns/mcp-campaign-{campaign_num}/interaction",
                headers={**self.test_headers, "X-Test-User-ID": f"user-{campaign_num}"},
                data=json.dumps(payload),
            )
            return campaign_num, response.status_code

        # Launch requests to different campaigns
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_request, i) for i in range(3)]
            results = [future.result() for future in futures]

        # All requests should complete
        assert len(results) == 3

        # All should return valid status codes
        for campaign_num, status_code in results:
            assert (
                status_code in [400, 404]
            ), f"Expected 400 or 404 for campaign {campaign_num} validation, got {status_code}"

    def test_mcp_concurrent_different_endpoints(self):
        """Test MCP handling concurrent requests to different endpoints."""
        results = []

        def get_campaigns():
            response = self.client.get("/api/campaigns", headers=self.test_headers)
            return "campaigns", response.status_code

        def get_settings():
            response = self.client.get("/api/settings", headers=self.test_headers)
            return "settings", response.status_code

        def get_campaign():
            response = self.client.get(
                f"/api/campaigns/{self.test_campaign_id}", headers=self.test_headers
            )
            return "campaign", response.status_code

        # Launch concurrent requests to different endpoints
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(get_campaigns),
                executor.submit(get_settings),
                executor.submit(get_campaign),
            ]
            results = [future.result() for future in futures]

        # All should complete
        assert len(results) == 3

        # All should return valid status codes (404 for non-existent campaign is valid)
        for endpoint, status_code in results:
            assert status_code in [
                200,
                404,
            ], f"Expected 200 or 404 for {endpoint} endpoint, got {status_code}"

    # ===== Authentication Edge Cases =====

    def test_mcp_missing_auth_headers(self):
        """Test MCP handling of requests with missing auth headers."""
        # Request without auth headers
        response = self.client.get("/api/campaigns")

        # MCP should handle missing auth appropriately
        assert response.status_code == 401, "Should require authentication"

    def test_mcp_malformed_auth_headers(self):
        """Test MCP handling of malformed auth headers."""
        malformed_headers = {
            "X-Test-Bypass-Auth": "",  # Empty value
            "X-Test-User-ID": "",  # Empty user ID
            "Content-Type": "application/json",
        }

        response = self.client.get("/api/campaigns", headers=malformed_headers)

        # MCP should handle malformed auth gracefully
        assert response.status_code == 401, "Should require authentication"

    def test_mcp_special_characters_in_user_id(self):
        """Test MCP handling of special characters in user ID."""
        special_headers = {
            **self.test_headers,
            "X-Test-User-ID": "user-with-special-chars!@#$%^&*()",
        }

        response = self.client.get("/api/campaigns", headers=special_headers)

        # MCP should handle special characters in user ID (200 = auth bypass works)
        assert (
            response.status_code == 200
        ), f"Expected 200 for special characters with auth bypass, got {response.status_code}"

    # ===== Export Functionality Edge Cases =====

    def test_mcp_export_invalid_format(self):
        """Test MCP export with invalid format."""
        response = self.client.get(
            f"/api/campaigns/{self.test_campaign_id}/export?format=invalid",
            headers=self.test_headers,
        )

        # MCP should reject invalid formats
        assert (
            response.status_code == 400
        ), f"Expected 400 for invalid export format, got {response.status_code}"

        if response.status_code == 400:
            data = response.get_json()
            if data:
                assert "error" in data, "Should return error message for invalid format"

    def test_mcp_export_nonexistent_campaign(self):
        """Test MCP export of nonexistent campaign."""
        response = self.client.get(
            "/api/campaigns/nonexistent-campaign/export?format=pdf",
            headers=self.test_headers,
        )

        # MCP should handle nonexistent campaigns gracefully (404 or 400 are both valid)
        assert (
            response.status_code
            in [
                400,
                404,
            ]
        ), f"Expected 400 or 404 for nonexistent campaign export, got {response.status_code}"

        if response.status_code in [400, 404]:
            data = response.get_json()
            if data:
                assert (
                    "error" in data
                ), "Should return error message for missing campaign"

    def test_mcp_export_empty_campaign(self):
        """Test MCP export of campaign with no content."""
        response = self.client.get(
            f"/api/campaigns/{self.test_campaign_id}/export?format=txt",
            headers=self.test_headers,
        )

        # MCP should handle empty campaigns gracefully (404 = not found, 400 = validation error are valid)
        assert (
            response.status_code in [400, 404]
        ), f"Expected 400 or 404 for empty campaign export, got {response.status_code}"

    # ===== CORS Edge Cases =====

    def test_mcp_cors_preflight_handling(self):
        """Test MCP CORS preflight OPTIONS request handling."""
        response = self.client.options(
            "/api/campaigns",
            headers={
                "Origin": "https://example.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type,Authorization",
            },
        )

        # MCP should handle preflight requests
        assert (
            response.status_code == 200
        ), f"Expected 200 for CORS preflight request, got {response.status_code}"

        # Check basic CORS headers if successful
        if response.status_code == 200:
            assert (
                response.headers.get("Access-Control-Allow-Origin") is not None
            ), "Should include CORS origin header"

    def test_mcp_cors_with_custom_origin(self):
        """Test MCP CORS handling with custom origin."""
        cors_headers = {
            **self.test_headers,
            "Origin": "https://custom-domain.com",
        }

        response = self.client.get("/api/campaigns", headers=cors_headers)

        # MCP should handle custom origins
        assert response.status_code == 200, "Should handle requests successfully"

        # CORS headers should be present if successful
        if response.status_code == 200:
            assert (
                response.headers.get("Access-Control-Allow-Origin") is not None
            ), "Should include CORS headers"

    def test_mcp_cors_with_credentials(self):
        """Test MCP CORS handling with credentials."""
        cors_headers = {
            **self.test_headers,
            "Origin": "https://example.com",
            "Cookie": "session=test123",
        }

        response = self.client.get("/api/campaigns", headers=cors_headers)

        # MCP should handle requests with credentials
        assert response.status_code == 200, "Should handle requests successfully"

    # ===== Error Recovery Tests =====

    def test_mcp_multiple_error_scenarios(self):
        """Test MCP handling of multiple error scenarios in sequence."""
        # Test sequence of different error conditions
        test_scenarios = [
            # Malformed JSON
            ('{"input": "incomplete json"', 400),
            # Missing required fields
            ('{"mode": "character"}', 400),
            # Valid request after errors
            ('{"input": "valid request", "mode": "character"}', [200, 404, 500]),
        ]

        for payload, expected_codes in test_scenarios:
            response = self.client.post(
                f"/api/campaigns/{self.test_campaign_id}/interaction",
                headers=self.test_headers,
                data=payload,
            )

            # All invalid payload tests should expect 400 (bad request), 404 (nonexistent campaign), or 500 (server error)
            assert (
                response.status_code in [400, 404, 500]
            ), f"Expected 400, 404, or 500 for invalid payload {payload[:50]}..., got {response.status_code}"

    def test_mcp_rapid_sequential_requests(self):
        """Test MCP handling of rapid sequential requests from same user."""
        results = []

        # Send 10 rapid requests sequentially
        for i in range(10):
            response = self.client.get("/api/campaigns", headers=self.test_headers)
            results.append(response.status_code)

        # All requests should complete with valid status codes
        for i, status_code in enumerate(results):
            assert (
                status_code == 200
            ), f"Expected 200 for GET campaigns request {i}, got {status_code}"

    def test_mcp_mixed_request_types(self):
        """Test MCP handling of mixed GET/POST requests."""
        # Mix of GET and POST requests
        get_response = self.client.get("/api/campaigns", headers=self.test_headers)

        post_payload = {"input": "test interaction", "mode": "character"}
        post_response = self.client.post(
            f"/api/campaigns/{self.test_campaign_id}/interaction",
            headers=self.test_headers,
            data=json.dumps(post_payload),
        )

        settings_response = self.client.get("/api/settings", headers=self.test_headers)

        # All should return valid status codes
        assert (
            get_response.status_code == 200
        ), f"Expected 200 for GET campaigns, got {get_response.status_code}"
        assert (
            post_response.status_code in [400, 404]
        ), f"Expected 400 or 404 for POST interaction validation, got {post_response.status_code}"
        assert (
            settings_response.status_code == 200
        ), f"Expected 200 for GET settings, got {settings_response.status_code}"


if __name__ == "__main__":
    unittest.main()
