#!/usr/bin/env python3
"""
HTTP API version of real API capture test.

WARNING: This test uses REAL APIs and costs money!

This test captures real Gemini API responses by making HTTP requests
to the campaign creation endpoint with real API mode enabled.
Shares test data and validation logic with the browser version.
"""

import json
import os
import sys
import time

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import shared testing utilities
from testing_ui.testing_shared import (
    CAMPAIGN_TEST_DATA,
    TEST_SCENARIOS,
    generate_test_user_id,
    get_test_url,
    setup_http_test_session,
    setup_test_environment,
    validate_campaign_created_successfully,
    validate_story_content_exists,
)


def test_real_api_campaign_creation():
    """Test campaign creation with REAL APIs to capture response data"""

    print("⚠️  WARNING: USING REAL APIs - This will cost money!")
    print("🧪 Testing real API campaign creation (HTTP API)...")

    # Use shared test scenario for API response capture
    scenario = TEST_SCENARIOS["api_response_capture"]
    campaign_data = scenario["campaign_data"].copy()
    expected_character = scenario["expected_character"]

    # Setup environment for REAL API usage (no mocks)
    setup_test_environment(
        use_real_api=True, port="8087"
    )  # Different port for real API tests

    # Setup HTTP session using shared utility
    base_url = get_test_url("http").replace("8086", "8087")  # Use real API port
    test_user_id = generate_test_user_id("real-api-capture-http")
    session, _ = setup_http_test_session(base_url, test_user_id)

    print("📤 Creating campaign with REAL APIs for response capture")
    print(f"   Title: {campaign_data['title']}")
    print(f"   Character: {campaign_data['character_name']}")
    print(f"   Setting: {campaign_data['setting']}")
    print("💰 This will make actual Gemini API calls and cost money!")

    # Record start time for performance analysis
    start_time = time.time()

    # Make campaign creation request with real APIs
    response = session.post(f"{base_url}/api/campaigns", json=campaign_data)

    creation_time = time.time() - start_time
    print(f"⏱️  Campaign creation took: {creation_time:.2f} seconds")
    print(f"📥 Response status: {response.status_code}")

    if response.status_code == 201:
        response_data = response.json()

        # Validate basic campaign creation
        campaign_id = validate_campaign_created_successfully(response_data, "http")
        print(f"✓ Campaign created with ID: {campaign_id}")

        # Capture response structure for mock updates
        print("📋 Capturing API response structure...")
        response_structure = {
            "creation_response": response_data,
            "creation_time_seconds": creation_time,
            "timestamp": time.time(),
        }

        # Retrieve the created campaign to capture full response data
        print("📤 Retrieving campaign data to capture full API response...")
        get_start_time = time.time()
        get_response = session.get(f"{base_url}/api/campaigns/{campaign_id}")
        retrieval_time = time.time() - get_start_time

        print(f"⏱️  Campaign retrieval took: {retrieval_time:.2f} seconds")

        if get_response.status_code == 200:
            campaign_details = get_response.json()
            print(
                f"✓ Retrieved campaign data with keys: {list(campaign_details.keys())}"
            )

            # Add retrieval data to captured response
            response_structure["retrieval_response"] = campaign_details
            response_structure["retrieval_time_seconds"] = retrieval_time

            # Analyze the real API response structure
            print("\n📊 REAL API RESPONSE ANALYSIS:")
            print("=" * 50)

            # Check narrative history structure
            if "narrative_history" in campaign_details:
                narrative_history = campaign_details["narrative_history"]
                print(
                    f"📖 Narrative history entries: {len(narrative_history) if narrative_history else 0}"
                )

                if narrative_history and len(narrative_history) > 0:
                    first_entry = narrative_history[0]
                    if isinstance(first_entry, dict):
                        print(f"📋 First entry fields: {list(first_entry.keys())}")

                        # Capture field structures for mock generation
                        response_structure["narrative_structure"] = {
                            "entry_count": len(narrative_history),
                            "first_entry_fields": list(first_entry.keys()),
                            "field_types": {
                                k: type(v).__name__ for k, v in first_entry.items()
                            },
                        }

                        # Check for structured fields
                        structured_fields = [
                            "planning_block",
                            "god_mode_response",
                            "session_header",
                            "resources",
                            "dice_rolls",
                        ]
                        found_structured = [
                            field for field in structured_fields if field in first_entry
                        ]
                        print(f"🏗️  Structured fields found: {found_structured}")

                        # Validate story content exists
                        if validate_story_content_exists(narrative_history):
                            print("✓ Real API generated substantial story content")
                        else:
                            print("⚠️  Story content appears short or missing")

                        # Check character integration
                        if "god_mode_response" in first_entry:
                            god_mode_text = first_entry["god_mode_response"]
                            if expected_character in god_mode_text:
                                print(
                                    f"✓ Character '{expected_character}' properly integrated in story"
                                )
                            else:
                                print(
                                    f"⚠️  Character '{expected_character}' not found in story text"
                                )

                        # Sample content lengths for mock generation
                        content_lengths = {}
                        for field in found_structured:
                            if field in first_entry and isinstance(
                                first_entry[field], str
                            ):
                                content_lengths[field] = len(first_entry[field])

                        response_structure["content_analysis"] = {
                            "character_integrated": expected_character
                            in str(first_entry),
                            "content_lengths": content_lengths,
                            "total_content_length": len(str(first_entry)),
                        }

                        print(f"📏 Content lengths: {content_lengths}")

            # Save captured response data for mock updates
            capture_filename = (
                f"/tmp/worldarchitectai/real_api_capture_{int(time.time())}.json"
            )
            os.makedirs(os.path.dirname(capture_filename), exist_ok=True)

            with open(capture_filename, "w") as f:
                json.dump(response_structure, f, indent=2, default=str)

            print(f"💾 Real API response data saved to: {capture_filename}")
            print("   This data can be used to update mock responses")

            print("\n✅ SUCCESS: Real API capture completed!")
            print("💰 Cost: This test made actual API calls")
            print("🎯 Use captured data to improve mock accuracy")

            return campaign_id, response_structure

        print(f"❌ Failed to retrieve campaign: {get_response.text}")
        raise Exception(
            f"Campaign retrieval failed with status {get_response.status_code}"
        )

    print(f"❌ Failed to create campaign with real APIs: {response.text}")
    raise Exception(
        f"Real API campaign creation failed with status {response.status_code}"
    )


def test_real_api_performance_comparison():
    """Compare real API performance vs mock API performance"""

    print("\n🏃 Testing real API vs mock API performance comparison...")

    # Test with mocks first for comparison
    print("🎭 Testing with MOCK APIs...")
    setup_test_environment(use_real_api=False, port="8086")

    mock_base_url = get_test_url("http")
    mock_session, _ = setup_http_test_session(
        mock_base_url, generate_test_user_id("mock-perf")
    )

    campaign_data = CAMPAIGN_TEST_DATA["custom_campaign"].copy()

    mock_start = time.time()
    mock_response = mock_session.post(
        f"{mock_base_url}/api/campaigns", json=campaign_data
    )
    mock_time = time.time() - mock_start

    print(f"🎭 Mock API creation time: {mock_time:.2f} seconds")

    if mock_response.status_code == 201:
        mock_campaign_id = mock_response.json().get("campaign_id")
        mock_get_start = time.time()
        mock_session.get(
            f"{mock_base_url}/api/campaigns/{mock_campaign_id}"
        )
        mock_retrieval_time = time.time() - mock_get_start
        print(f"🎭 Mock API retrieval time: {mock_retrieval_time:.2f} seconds")

        # Now test with real APIs
        print("💰 Testing with REAL APIs...")
        setup_test_environment(use_real_api=True, port="8087")

        real_base_url = get_test_url("http").replace("8086", "8087")
        real_session, _ = setup_http_test_session(
            real_base_url, generate_test_user_id("real-perf")
        )

        real_start = time.time()
        real_response = real_session.post(
            f"{real_base_url}/api/campaigns", json=campaign_data
        )
        real_time = time.time() - real_start

        print(f"💰 Real API creation time: {real_time:.2f} seconds")

        if real_response.status_code == 201:
            real_campaign_id = real_response.json().get("campaign_id")
            real_get_start = time.time()
            real_session.get(
                f"{real_base_url}/api/campaigns/{real_campaign_id}"
            )
            real_retrieval_time = time.time() - real_get_start
            print(f"💰 Real API retrieval time: {real_retrieval_time:.2f} seconds")

            # Performance comparison
            print("\n📈 PERFORMANCE COMPARISON:")
            print("=" * 40)
            print(f"🎭 Mock creation:    {mock_time:.2f}s")
            print(f"💰 Real creation:    {real_time:.2f}s")
            print(f"⚡ Speed difference: {real_time / mock_time:.1f}x slower")
            print(f"🎭 Mock retrieval:   {mock_retrieval_time:.2f}s")
            print(f"💰 Real retrieval:   {real_retrieval_time:.2f}s")
            print("=" * 40)

            return {
                "mock_creation_time": mock_time,
                "real_creation_time": real_time,
                "mock_retrieval_time": mock_retrieval_time,
                "real_retrieval_time": real_retrieval_time,
                "speed_ratio": real_time / mock_time,
            }
        print(f"❌ Real API test failed: {real_response.status_code}")
        return None
    print(f"❌ Mock API test failed: {mock_response.status_code}")
    return None


def main():
    """Run all HTTP real API capture tests"""
    print("=" * 70)
    print("🚀 Running Real API Capture HTTP Tests (Shared Utilities)")
    print("⚠️  WARNING: THESE TESTS USE REAL APIs AND COST MONEY!")
    print("=" * 70)

    try:
        # Test 1: Capture real API responses
        campaign_id, response_data = test_real_api_campaign_creation()

        # Test 2: Performance comparison
        perf_data = test_real_api_performance_comparison()

        print("\n" + "=" * 70)
        print("✅ All real API capture tests completed!")
        print("💰 COST WARNING: Real API calls were made")
        print("📋 Response data captured for mock improvements")
        if perf_data:
            print(f"⚡ Real APIs are {perf_data['speed_ratio']:.1f}x slower than mocks")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ Real API test failed: {str(e)}")
        print("💰 Some real API calls may have been made before failure")
        print("=" * 70)
        raise


if __name__ == "__main__":
    main()
