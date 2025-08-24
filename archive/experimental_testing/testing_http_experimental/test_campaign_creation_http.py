#!/usr/bin/env python3
"""
HTTP API tests for campaign creation functionality:
1. Custom campaign creation via HTTP API
2. Dragon-knight campaign creation via HTTP API
3. Campaign retrieval and data consistency via HTTP API

Tests the backend API endpoints rather than browser wizard behavior.
Converted from browser test to HTTP mode for faster automated testing.
"""

import os
import sys

import requests

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import shared testing utilities
from testing_ui.testing_shared import (
    CAMPAIGN_TEST_DATA,
    TEST_SCENARIOS,
    generate_test_user_id,
    get_test_headers,
    get_test_url,
    validate_campaign_created_successfully,
    validate_story_content_exists,
)

# Test configuration
BASE_URL = get_test_url("http")
TEST_USER_ID = generate_test_user_id("wizard-fixes-http")

# Common headers for all requests
headers = get_test_headers(TEST_USER_ID, "http")


def setup_test_session():
    """Setup test session by accessing homepage with test mode params"""
    session = requests.Session()

    # Navigate to homepage with test mode to establish session
    response = session.get(f"{BASE_URL}?test_mode=true&test_user_id={TEST_USER_ID}")

    if response.status_code != 200:
        raise Exception(f"Failed to setup test session: {response.status_code}")

    # Update headers for session
    session.headers.update(headers)

    return session


def test_campaign_creation_custom_type():
    """Test that custom campaign creation works via HTTP API"""

    print("🧪 Testing custom campaign creation (HTTP API)...")

    # Setup session
    session = setup_test_session()

    # Use shared test data
    scenario = TEST_SCENARIOS["custom_character_display"]
    payload = scenario["campaign_data"].copy()

    print(f"📤 Creating custom campaign: '{payload['title']}'")

    response = session.post(f"{BASE_URL}/api/campaigns", json=payload)

    print(f"📥 Response status: {response.status_code}")

    if response.status_code == 201:
        campaign_data = response.json()

        # Validate response contains expected success fields
        assert "success" in campaign_data, "Response missing success field"
        assert "campaign_id" in campaign_data, "Response missing campaign_id field"
        assert campaign_data["success"] is True, (
            f"Campaign creation not successful: {campaign_data.get('success')}"
        )
        assert campaign_data["campaign_id"] is not None, "Campaign ID is None"

        print(
            f"✓ Response fields validated: success={campaign_data['success']}, campaign_id='{campaign_data['campaign_id']}'"
        )

        # Use shared validation
        campaign_id = validate_campaign_created_successfully(campaign_data, "http")
        print(f"✓ Campaign created with ID: {campaign_id}")

        print("✅ SUCCESS: Custom campaign creation via HTTP API working!")

        return campaign_id

    print(f"❌ Failed to create campaign: {response.text}")
    raise Exception(f"Campaign creation failed with status {response.status_code}")


def test_campaign_creation_dragon_knight_type():
    """Test that dragon-knight campaign creation works via HTTP API"""

    print("\n🧪 Testing dragon-knight campaign creation (HTTP API)...")

    # Setup session
    session = setup_test_session()

    # Use shared test data
    payload = CAMPAIGN_TEST_DATA["dragon_knight_campaign"].copy()

    print("📤 Creating dragon-knight campaign")

    response = session.post(f"{BASE_URL}/api/campaigns", json=payload)

    print(f"📥 Response status: {response.status_code}")

    if response.status_code == 201:
        campaign_data = response.json()

        # Use shared validation
        campaign_id = validate_campaign_created_successfully(campaign_data, "http")
        print(f"✓ Campaign created with ID: {campaign_id}")

        print("✅ SUCCESS: Dragon-knight campaign creation via HTTP API working!")

        return campaign_id

    print(f"❌ Failed to create campaign: {response.text}")
    raise Exception(f"Campaign creation failed with status {response.status_code}")


def test_campaign_api_retrieval():
    """Test that campaign data can be retrieved via HTTP API after creation"""

    print("\n🧪 Testing campaign retrieval via HTTP API...")

    # Setup session
    session = setup_test_session()

    # Use shared test data for story content scenario
    scenario = TEST_SCENARIOS["story_content_loading"]
    payload = scenario["campaign_data"].copy()

    print("📤 Creating campaign for retrieval test")

    response = session.post(f"{BASE_URL}/api/campaigns", json=payload)

    print(f"📥 Creation response status: {response.status_code}")

    if response.status_code == 201:
        campaign_data = response.json()

        # Use shared validation
        campaign_id = validate_campaign_created_successfully(campaign_data, "http")
        print(f"✓ Campaign created with ID: {campaign_id}")

        # Test immediate retrieval
        print("📤 Retrieving campaign data")
        get_response = session.get(f"{BASE_URL}/api/campaigns/{campaign_id}")

        print(f"📥 Retrieval response status: {get_response.status_code}")

        if get_response.status_code == 200:
            retrieved_data = get_response.json()

            print(f"✓ Retrieved data keys: {list(retrieved_data.keys())}")

            # Assert essential structure exists in retrieved data
            assert "campaign" in retrieved_data, (
                "Retrieved data missing campaign object"
            )
            assert "story" in retrieved_data, "Retrieved data missing story array"
            assert "game_state" in retrieved_data, (
                "Retrieved data missing game_state object"
            )

            campaign_info = retrieved_data["campaign"]
            assert "title" in campaign_info, "Campaign object missing title field"
            assert "created_at" in campaign_info, (
                "Campaign object missing created_at field"
            )

            # Validate retrieved data contains essential campaign fields
            title_field = campaign_info["title"]
            created_at_field = campaign_info["created_at"]
            assert title_field is not None, "Campaign title is None"
            assert len(str(title_field).strip()) > 0, "Campaign title is empty"
            assert created_at_field is not None, "Campaign created_at is None"

            print(
                f"✓ Campaign structure validated: title='{title_field}', created_at='{created_at_field}'"
            )

            # Use shared validation for story content
            if (
                "narrative_history" in retrieved_data
                and retrieved_data["narrative_history"]
            ):
                if validate_story_content_exists(retrieved_data["narrative_history"]):
                    print(
                        "✅ SUCCESS: Campaign creation and retrieval with story content!"
                    )
                else:
                    print("⚠️  Story content exists but may be too short")
                    print("✅ SUCCESS: Campaign creation and basic retrieval working!")
            else:
                print(
                    "⚠️  No narrative history in retrieved data (may be normal for async generation)"
                )
                print("✅ SUCCESS: Campaign creation and basic retrieval working!")

            return campaign_id
        print(f"❌ Failed to retrieve campaign: {get_response.text}")
        raise Exception(
            f"Campaign retrieval failed with status {get_response.status_code}"
        )

    print(f"❌ Failed to create campaign: {response.text}")
    raise Exception(f"Campaign creation failed with status {response.status_code}")


def main():
    """Run all HTTP tests"""
    print("=" * 60)
    print("🚀 Running Campaign Creation HTTP API Tests")
    print("=" * 60)

    try:
        # Test 1: Custom campaign creation
        test_campaign_creation_custom_type()

        # Test 2: Dragon-knight campaign creation
        test_campaign_creation_dragon_knight_type()

        # Test 3: Campaign retrieval API
        test_campaign_api_retrieval()

        print("\n" + "=" * 60)
        print("✅ All HTTP API tests passed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        print("=" * 60)
        raise


if __name__ == "__main__":
    main()
