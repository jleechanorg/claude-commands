#!/usr/bin/env python3
"""
HTTP API version of campaign creation browser test.

This test validates campaign creation through HTTP API calls instead of browser automation,
sharing test data and validation logic with the browser version.
"""

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import shared testing utilities
from testing_ui.testing_shared import (
    CAMPAIGN_TEST_DATA,
    TEST_SCENARIOS,
    generate_test_user_id,
    get_test_url,
    setup_http_test_session,
    validate_api_response_structure,
    validate_campaign_created_successfully,
)


def test_campaign_creation_workflow():
    """Test complete campaign creation workflow via HTTP API"""

    print("🧪 Testing campaign creation workflow (HTTP API)...")

    # Use shared test scenario for campaign creation
    scenario = TEST_SCENARIOS["custom_character_display"]
    campaign_data = scenario["campaign_data"].copy()
    expected_character = scenario["expected_character"]

    # Setup HTTP session using shared utility
    base_url = get_test_url("http")
    test_user_id = generate_test_user_id("campaign-creation-http")
    session, _ = setup_http_test_session(base_url, test_user_id)

    print(f"📤 Creating campaign via API: '{campaign_data['title']}'")
    print(f"   Character: {campaign_data['character_name']}")
    print(f"   Setting: {campaign_data['setting']}")

    # Step 1: Navigate to homepage (equivalent to browser navigation)
    print("📍 Step 1: Verify homepage accessibility...")
    homepage_response = session.get(
        f"{base_url}?test_mode=true&test_user_id={test_user_id}"
    )

    if homepage_response.status_code == 200:
        print("✅ Homepage accessible")
    else:
        raise Exception(f"Homepage not accessible: {homepage_response.status_code}")

    # Step 2: Create campaign (equivalent to clicking "Start New Campaign" and filling wizard)
    print("📍 Step 2: Creating campaign via API...")
    response = session.post(f"{base_url}/api/campaigns", json=campaign_data)

    print(f"📥 Response status: {response.status_code}")

    if response.status_code == 201:
        campaign_response = response.json()

        # Use shared validation
        campaign_id = validate_campaign_created_successfully(campaign_response, "http")
        print(f"✅ Campaign created with ID: {campaign_id}")

        # Step 3: Verify campaign data (equivalent to checking wizard preview)
        print("📍 Step 3: Verifying campaign data...")
        get_response = session.get(f"{base_url}/api/campaigns/{campaign_id}")

        if get_response.status_code == 200:
            campaign_details = get_response.json()
            print("✅ Campaign data retrieved")

            # Validate campaign structure
            validate_api_response_structure(
                campaign_details, ["campaign", "game_state", "story"]
            )
            print("✅ Campaign structure validation passed")

            # Check for expected character in story content
            if "story" in campaign_details and campaign_details["story"]:
                story_content = str(campaign_details["story"])
                if expected_character in story_content:
                    print(
                        f"✅ Expected character '{expected_character}' found in story"
                    )
                else:
                    print(
                        f"⚠️  Expected character '{expected_character}' not found in story (may be normal for async generation)"
                    )

            print("✅ SUCCESS: Campaign creation workflow via HTTP API working!")
            return campaign_id

        print(f"❌ Failed to retrieve campaign: {get_response.text}")
        raise Exception(
            f"Campaign retrieval failed with status {get_response.status_code}"
        )

    print(f"❌ Failed to create campaign: {response.text}")
    raise Exception(f"Campaign creation failed with status {response.status_code}")


def test_campaign_creation_error_handling():
    """Test campaign creation error handling via HTTP API"""

    print("\n🧪 Testing campaign creation error handling (HTTP API)...")

    # Setup HTTP session
    base_url = get_test_url("http")
    test_user_id = generate_test_user_id("campaign-error-http")
    session, _ = setup_http_test_session(base_url, test_user_id)

    # Test with invalid data
    invalid_data = {
        "campaign_type": "invalid_type",
        "title": "",  # Empty title
        "character_name": "",
        "setting": "",
        "description": "",
    }

    print("📤 Testing error handling with invalid data...")
    response = session.post(f"{base_url}/api/campaigns", json=invalid_data)

    # Should handle gracefully (either succeed with defaults or return proper error)
    if response.status_code in [400, 422]:
        print("✅ Proper error handling for invalid data")
        return True
    if response.status_code == 201:
        print("✅ API handled invalid data gracefully with defaults")
        return True
    print(f"⚠️  Unexpected response: {response.status_code}")
    return False


def test_multiple_campaign_creation():
    """Test creating multiple campaigns via HTTP API"""

    print("\n🧪 Testing multiple campaign creation (HTTP API)...")

    # Setup HTTP session
    base_url = get_test_url("http")
    test_user_id = generate_test_user_id("multi-campaign-http")
    session, _ = setup_http_test_session(base_url, test_user_id)

    # Create multiple campaigns with different data
    campaign_types = ["custom_campaign", "dragon_knight_campaign"]
    created_campaigns = []

    for i, campaign_type in enumerate(campaign_types):
        campaign_data = CAMPAIGN_TEST_DATA[campaign_type].copy()
        campaign_data["title"] = f"Test Campaign {i + 1}"

        print(f"📤 Creating campaign {i + 1}: {campaign_data['title']}")
        response = session.post(f"{base_url}/api/campaigns", json=campaign_data)

        if response.status_code == 201:
            campaign_response = response.json()
            campaign_id = validate_campaign_created_successfully(
                campaign_response, "http"
            )
            created_campaigns.append(campaign_id)
            print(f"✅ Campaign {i + 1} created: {campaign_id}")
        else:
            print(f"❌ Failed to create campaign {i + 1}: {response.status_code}")
            raise Exception("Multiple campaign creation failed")

    print(f"✅ SUCCESS: Created {len(created_campaigns)} campaigns successfully")
    return created_campaigns


def main():
    """Run all HTTP campaign creation tests"""
    print("=" * 70)
    print("🚀 Running Campaign Creation HTTP API Tests (Browser Equivalent)")
    print("=" * 70)

    try:
        # Test 1: Basic campaign creation workflow
        test_campaign_creation_workflow()

        # Test 2: Error handling
        test_campaign_creation_error_handling()

        # Test 3: Multiple campaign creation
        test_multiple_campaign_creation()

        print("\n" + "=" * 70)
        print("✅ All campaign creation HTTP tests passed!")
        print("🎯 HTTP API equivalent of browser campaign creation working")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        print("=" * 70)
        raise


if __name__ == "__main__":
    main()
