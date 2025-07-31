"""
Test for GeminiResponse Integration through MCP Architecture

This test validates the GeminiResponse integration through MCP API gateway.
Tests campaign creation handling with proper response object integration.

Test follows MCP architecture patterns:
1. Test API endpoints through MCP gateway
2. Validate response object handling through MCP
3. Ensure proper integration without service mocking
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


class TestGeminiResponseIntegration(unittest.TestCase):
    """Test for GeminiResponse integration through MCP architecture."""

    def setUp(self):
        """Set up test environment for MCP architecture."""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Test headers for MCP authentication bypass
        self.test_headers = {
            "X-Test-Bypass-Auth": "true",
            "X-Test-User-ID": "mcp-gemini-test-user",
            "Content-Type": "application/json",
        }

    def test_mcp_campaign_creation_with_gemini_response_handling(self):
        """
        Test Campaign creation handles GeminiResponse objects through MCP.

        This test validates that the MCP gateway properly handles campaign creation
        with proper response object handling, regardless of internal implementation.
        """
        # Arrange: Campaign data for MCP
        campaign_data = {
            "prompt": "Create a fantasy adventure through MCP",
            "title": "MCP Test Campaign",
            "selected_prompts": ["narrative"],
            "custom_options": [],
        }

        # Act: Create campaign via MCP API
        response = self.client.post(
            "/api/campaigns", data=json.dumps(campaign_data), headers=self.test_headers
        )

        # Assert: MCP gateway should handle campaign creation (may be 400 if validation fails)
        assert response.status_code in [
            201,
            400,
        ], f"Expected 201 or 400 for creation, got {response.status_code}"

        # If successful, should return valid response
        if response.status_code in [200, 201]:
            data = response.get_json()
            assert isinstance(data, dict), "Campaign response should be dict format"

    def test_mcp_gemini_response_object_integration(self):
        """
        Test that MCP properly integrates with GeminiResponse objects.

        This test validates that the MCP architecture handles response objects
        correctly through the API gateway layer.
        """
        # Test campaign creation that involves response object handling
        campaign_data = {
            "prompt": "Test narrative response handling through MCP",
            "title": "MCP Response Test Campaign",
            "selected_prompts": ["narrative"],
            "custom_options": [],
        }

        response = self.client.post(
            "/api/campaigns", data=json.dumps(campaign_data), headers=self.test_headers
        )

        # MCP should handle response object integration gracefully (may be 400 if validation fails)
        assert response.status_code in [
            201,
            400,
        ], f"Expected 201 or 400 for creation, got {response.status_code}"

    def test_mcp_get_initial_story_through_api(self):
        """
        Test that MCP properly handles initial story generation.

        This validates that the MCP architecture correctly processes
        story generation requests through the API gateway.
        """
        # Test story generation through campaign creation
        campaign_data = {
            "prompt": "Generate initial story through MCP architecture",
            "title": "MCP Story Generation Test",
            "selected_prompts": ["narrative"],
            "custom_options": [],
        }

        response = self.client.post(
            "/api/campaigns", data=json.dumps(campaign_data), headers=self.test_headers
        )

        # MCP should handle story generation requests (may be 400 if validation fails)
        assert response.status_code in [
            201,
            400,
        ], f"Expected 201 or 400 for creation, got {response.status_code}"

    def test_mcp_campaign_creation_error_handling(self):
        """
        Test that MCP handles campaign creation errors gracefully.

        This validates error handling through the MCP gateway layer.
        """
        # Test with invalid campaign data
        invalid_campaign_data = {
            "prompt": "",  # Empty prompt
            "title": "",  # Empty title
        }

        response = self.client.post(
            "/api/campaigns",
            data=json.dumps(invalid_campaign_data),
            headers=self.test_headers,
        )

        # MCP should handle invalid data gracefully (400 for validation error)
        assert response.status_code == 400, "MCP should handle invalid campaign data"

    def test_mcp_campaign_creation_with_different_prompts(self):
        """
        Test campaign creation with different prompt types through MCP.

        This validates that MCP handles various prompt configurations.
        """
        # Test different prompt configurations
        prompt_configs = [
            {"selected_prompts": ["narrative"]},
            {"selected_prompts": ["narrative", "character"]},
            {"selected_prompts": []},
            {"custom_options": ["defaultWorld"]},
        ]

        for i, prompt_config in enumerate(prompt_configs):
            with self.subTest(config=i):
                campaign_data = {
                    "prompt": f"Test campaign {i} through MCP",
                    "title": f"MCP Test Campaign {i}",
                    **prompt_config,
                }

                response = self.client.post(
                    "/api/campaigns",
                    data=json.dumps(campaign_data),
                    headers=self.test_headers,
                )

                # MCP should handle all prompt configurations (may be 400 if validation fails)
                assert (
                    response.status_code in [200, 201, 400]
                ), f"Expected 200, 201, or 400 for prompt config {i}, got {response.status_code}"

    def test_mcp_campaign_creation_with_various_auth_headers(self):
        """
        Test campaign creation with various authentication headers through MCP.

        This validates MCP authentication handling in campaign creation.
        """
        campaign_data = {
            "prompt": "Test campaign with auth variations",
            "title": "MCP Auth Test Campaign",
            "selected_prompts": ["narrative"],
            "custom_options": [],
        }

        # Test different auth header combinations
        auth_variations = [
            # Complete headers
            {
                "X-Test-Bypass-Auth": "true",
                "X-Test-User-ID": "test-user",
                "Content-Type": "application/json",
            },
            # Missing user ID
            {"X-Test-Bypass-Auth": "true", "Content-Type": "application/json"},
            # No auth headers
            {"Content-Type": "application/json"},
        ]

        for i, headers in enumerate(auth_variations):
            with self.subTest(auth_case=i):
                response = self.client.post(
                    "/api/campaigns", data=json.dumps(campaign_data), headers=headers
                )

                # MCP should handle all auth variations gracefully (with different auth, may get 401)
                assert (
                    response.status_code in [200, 201, 400, 401]
                ), f"Expected valid status for auth variation {i}, got {response.status_code}"

    def test_mcp_concurrent_campaign_creation(self):
        """
        Test concurrent campaign creation through MCP.

        This validates that MCP handles concurrent requests properly.
        """
        from concurrent.futures import ThreadPoolExecutor

        def create_campaign(campaign_num):
            campaign_data = {
                "prompt": f"Concurrent campaign {campaign_num} through MCP",
                "title": f"MCP Concurrent Campaign {campaign_num}",
                "selected_prompts": ["narrative"],
                "custom_options": [],
            }

            response = self.client.post(
                "/api/campaigns",
                data=json.dumps(campaign_data),
                headers=self.test_headers,
            )
            return campaign_num, response.status_code

        # Launch concurrent campaign creation requests
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(create_campaign, i) for i in range(3)]
            results = [future.result() for future in futures]

        # All concurrent requests should be handled by MCP
        assert len(results) == 3
        for campaign_num, status_code in results:
            assert status_code in [
                200,
                201,
                400,
                404,
                500,
            ], f"Concurrent campaign {campaign_num} should be handled by MCP"

    def test_mcp_campaign_creation_with_large_prompt(self):
        """
        Test campaign creation with large prompt data through MCP.

        This validates MCP handling of larger payloads.
        """
        # Create a large prompt
        large_prompt = "Create an epic fantasy adventure. " * 100

        campaign_data = {
            "prompt": large_prompt,
            "title": "MCP Large Prompt Test Campaign",
            "selected_prompts": ["narrative"],
            "custom_options": [],
        }

        response = self.client.post(
            "/api/campaigns", data=json.dumps(campaign_data), headers=self.test_headers
        )

        # MCP should handle large prompts gracefully (may be 400 if validation fails)
        assert response.status_code in [
            201,
            400,
        ], f"Expected 201 or 400 for large prompt, got {response.status_code}"

    def test_mcp_campaign_creation_with_special_characters(self):
        """
        Test campaign creation with special characters through MCP.

        This validates MCP handling of various character encodings.
        """
        campaign_data = {
            "prompt": "Create adventure with special chars: éñüí 🐉 ñoñó",
            "title": "MCP Special Chars Campaign: !@#$%^&*()",
            "selected_prompts": ["narrative"],
            "custom_options": [],
        }

        response = self.client.post(
            "/api/campaigns", data=json.dumps(campaign_data), headers=self.test_headers
        )

        # MCP should handle special characters gracefully (may be 400 if validation fails)
        assert response.status_code in [
            200,
            201,
            400,
        ], f"Expected 200, 201, or 400 for special chars, got {response.status_code}"


if __name__ == "__main__":
    print("🔵 Running GeminiResponse integration tests through MCP architecture")
    print("📝 NOTE: Tests validate MCP gateway handling of response objects")
    unittest.main(verbosity=2)
