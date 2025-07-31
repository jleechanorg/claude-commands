"""
Simple test to check what format Gemini is actually responding in.
"""

import json
import os
import sys
import unittest

from main import create_app

import firestore_service

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

import builtins
import contextlib

from integration_test_lib import (
    IntegrationTestSetup,
    setup_integration_test_environment,
)

# Handle missing dependencies gracefully
try:
    DEPS_AVAILABLE = True
except ImportError as e:
    print(f"Integration test dependencies not available: {e}")
    DEPS_AVAILABLE = False

# Test configuration
TEST_USER_ID = "test-json-format"


@unittest.skipIf(not DEPS_AVAILABLE, "Dependencies not available")
class TestGeminiJSONFormat(unittest.TestCase):
    """Test what format Gemini is actually using for responses."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests."""
        cls.test_setup = setup_integration_test_environment(project_root)
        cls.app = create_app()
        cls.client = cls.app.test_client()

        # Ensure we have API keys
        if not os.environ.get("GEMINI_API_KEY"):
            raise unittest.SkipTest("GEMINI_API_KEY not found")

    def test_initial_campaign_response_format(self):
        """Test the format of the initial campaign creation response."""
        print("\n=== Testing Initial Campaign Response Format ===")

        headers = IntegrationTestSetup.create_test_headers(TEST_USER_ID)

        # Create a simple campaign
        response = self.client.post(
            "/api/campaigns",
            headers=headers,
            json={
                "title": "Format Test Campaign",
                "prompt": "You are in a forest clearing.",
                "selected_prompts": ["narrative"],  # Simple setup
            },
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        campaign_id = data["campaign_id"]

        # Get the campaign story
        campaign, story = firestore_service.get_campaign_by_id(
            TEST_USER_ID, campaign_id
        )

        print(f"\nNumber of story entries: {len(story)}")

        # Look at the initial AI response
        for i, entry in enumerate(story):
            print(f"\n--- Entry {i} ---")
            print(f"Actor: {entry.get('actor')}")
            print(f"Text length: {len(entry.get('text', ''))}")

            if entry.get("actor") == "gemini":
                text = entry.get("text", "")
                print(f"\nFirst 100 chars: {text[:100]}...")

                # Check if it's JSON
                try:
                    parsed = json.loads(text)
                    print("\n✅ Response is valid JSON!")
                    print(f"JSON keys: {list(parsed.keys())}")
                    if "debug_info" in parsed:
                        print(f"debug_info content: {parsed['debug_info']}")
                    if "narrative" in parsed:
                        print(f"narrative preview: {parsed['narrative'][:100]}...")
                except json.JSONDecodeError:
                    print("\n❌ Response is NOT JSON - it's plain text")

                    # Check for debug tags
                    debug_tags = [
                        "[DEBUG_START]",
                        "[SESSION_HEADER]",
                        "[STATE_UPDATES_PROPOSED]",
                        "--- PLANNING BLOCK ---",
                    ]
                    found_tags = [tag for tag in debug_tags if tag in text]
                    if found_tags:
                        print(f"Found tags in text: {found_tags}")

        # Clean up
        with contextlib.suppress(builtins.BaseException):
            firestore_service.delete_campaign(TEST_USER_ID, campaign_id)

    def test_interaction_response_format(self):
        """Test the format of interaction responses."""
        print("\n=== Testing Interaction Response Format ===")

        headers = IntegrationTestSetup.create_test_headers(TEST_USER_ID)

        # Create campaign
        response = self.client.post(
            "/api/campaigns",
            headers=headers,
            json={
                "title": "Interaction Format Test",
                "prompt": "You stand at a crossroads.",
                "selected_prompts": ["narrative"],
            },
        )

        assert response.status_code == 201
        campaign_id = json.loads(response.data)["campaign_id"]

        # Make an interaction
        response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            headers=headers,
            json={"input": "I look around.", "mode": "character"},
        )

        assert response.status_code == 200
        interaction_data = json.loads(response.data)

        print(f"\nInteraction response keys: {list(interaction_data.keys())}")
        print(f"Response text preview: {interaction_data.get('response', '')[:200]}...")

        # Check the stored format
        campaign, story = firestore_service.get_campaign_by_id(
            TEST_USER_ID, campaign_id
        )

        # Find the latest AI response
        ai_responses = [e for e in story if e.get("actor") == "gemini"]
        if ai_responses:
            latest = ai_responses[-1]
            text = latest.get("text", "")

            print(f"\nLatest AI response preview: {text[:200]}...")

            # Check format
            try:
                parsed = json.loads(text)
                print("\n✅ Interaction response is JSON!")
                print(f"Keys: {list(parsed.keys())}")
            except:
                print("\n❌ Interaction response is plain text")

        # Clean up
        with contextlib.suppress(builtins.BaseException):
            firestore_service.delete_campaign(TEST_USER_ID, campaign_id)


if __name__ == "__main__":
    unittest.main(verbosity=2)
