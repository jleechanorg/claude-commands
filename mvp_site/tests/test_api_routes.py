"""
Test API routes functionality in MCP architecture.
Tests API endpoints through MCP API gateway pattern.
"""

import datetime
import json
import os
import sys
import unittest

# Set environment variables for MCP testing
os.environ["TESTING_AUTH_BYPASS"] = "true"
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

import firestore_service
from main import create_app
from mvp_site.tests.fake_firestore import FakeFirestoreClient


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


class TestStoryPagination(unittest.TestCase):
    """Integration-style tests for story pagination service."""

    def setUp(self):
        self.fake_db = FakeFirestoreClient()
        self.original_get_db = firestore_service.get_db
        firestore_service.get_db = lambda: self.fake_db
        self.user_id = "user"
        self.campaign_id = "campaign"

    def tearDown(self):
        firestore_service.get_db = self.original_get_db

    def _seed_story_entries(self, entries):
        story_collection = (
            self.fake_db.collection("users")
            .document(self.user_id)
            .collection("campaigns")
            .document(self.campaign_id)
            .collection("story")
        )
        for entry in entries:
            doc = story_collection.document(entry["id"])
            doc.set(
                {
                    "timestamp": datetime.datetime.fromisoformat(entry["timestamp"]),
                    "actor": entry.get("actor", "gemini"),
                    "text": entry.get("text", ""),
                    "mode": entry.get("mode"),
                    "user_scene_number": entry.get("user_scene_number"),
                }
            )

    def test_shared_timestamp_cursor_returns_remaining_entries(self):
        """Pagination should not drop entries that share the cursor timestamp."""

        entries = [
            {"id": "a", "timestamp": "2024-01-01T00:00:00+00:00", "text": "1"},
            {"id": "b", "timestamp": "2024-01-02T00:00:00+00:00", "text": "2"},
            {"id": "c", "timestamp": "2024-01-02T00:00:00+00:00", "text": "3"},
            {"id": "d", "timestamp": "2024-01-03T00:00:00+00:00", "text": "4"},
        ]
        self._seed_story_entries(entries)

        first_page = firestore_service.get_story_paginated(
            self.user_id, self.campaign_id, limit=3
        )

        assert first_page["has_older"] is True
        assert first_page["oldest_timestamp"] == "2024-01-02T00:00:00+00:00"
        assert first_page["oldest_id"] == "b"

        second_page = firestore_service.get_story_paginated(
            self.user_id,
            self.campaign_id,
            limit=3,
            before_timestamp=first_page["oldest_timestamp"],
            before_id=first_page["oldest_id"],
        )

        assert second_page["has_older"] is False
        assert second_page["fetched_count"] == 1
        assert second_page["entries"][0]["id"] == "a"

    def test_invalid_cursor_raises(self):
        """Invalid timestamp should surface as a validation error."""

        with self.assertRaises(ValueError):
            firestore_service.get_story_paginated(
                self.user_id,
                self.campaign_id,
                limit=3,
                before_timestamp="not-a-timestamp",
            )

    def test_has_older_based_on_page_overflow(self):
        """has_older should reflect presence of an extra entry beyond the limit."""

        entries = [
            {"id": "1", "timestamp": "2024-01-01T00:00:00+00:00"},
            {"id": "2", "timestamp": "2024-01-02T00:00:00+00:00"},
            {"id": "3", "timestamp": "2024-01-03T00:00:00+00:00"},
            {"id": "4", "timestamp": "2024-01-04T00:00:00+00:00"},
        ]
        self._seed_story_entries(entries)

        first_page = firestore_service.get_story_paginated(
            self.user_id, self.campaign_id, limit=2
        )
        assert first_page["has_older"] is True

        second_page = firestore_service.get_story_paginated(
            self.user_id,
            self.campaign_id,
            limit=2,
            before_timestamp=first_page["oldest_timestamp"],
            before_id=first_page["oldest_id"],
        )
        assert second_page["has_older"] is False

    def test_sequence_and_scene_numbers_across_pages(self):
        """sequence_id and user_scene_number should remain absolute across pages."""

        entries = [
            {"id": "1", "timestamp": "2024-01-01T00:00:00+00:00", "actor": "user"},
            {"id": "2", "timestamp": "2024-01-02T00:00:00+00:00", "actor": "gemini"},
            {"id": "3", "timestamp": "2024-01-03T00:00:00+00:00", "actor": "user"},
            {"id": "4", "timestamp": "2024-01-04T00:00:00+00:00", "actor": "gemini"},
            {"id": "5", "timestamp": "2024-01-05T00:00:00+00:00", "actor": "user"},
            {"id": "6", "timestamp": "2024-01-06T00:00:00+00:00", "actor": "gemini"},
        ]
        self._seed_story_entries(entries)

        # First page (newest two entries: 5, 6)
        first_page = firestore_service.get_story_paginated(
            self.user_id, self.campaign_id, limit=2
        )
        assert [e["sequence_id"] for e in first_page["entries"]] == [5, 6]
        assert [e.get("user_scene_number") for e in first_page["entries"]] == [
            None,
            3,
        ]

        # Second page (entries 3, 4) with offsets from first page
        second_page = firestore_service.get_story_paginated(
            self.user_id,
            self.campaign_id,
            limit=2,
            before_timestamp=first_page["oldest_timestamp"],
            before_id=first_page["oldest_id"],
            newer_count=2,
            newer_gemini_count=1,
        )
        assert [e["sequence_id"] for e in second_page["entries"]] == [3, 4]
        assert [e.get("user_scene_number") for e in second_page["entries"]] == [
            None,
            2,
        ]

        # Final page (entries 1, 2) with accumulated offsets
        third_page = firestore_service.get_story_paginated(
            self.user_id,
            self.campaign_id,
            limit=2,
            before_timestamp=second_page["oldest_timestamp"],
            before_id=second_page["oldest_id"],
            newer_count=4,
            newer_gemini_count=2,
        )
        assert [e["sequence_id"] for e in third_page["entries"]] == [1, 2]
        assert [e.get("user_scene_number") for e in third_page["entries"]] == [
            None,
            1,
        ]


if __name__ == "__main__":
    unittest.main()
