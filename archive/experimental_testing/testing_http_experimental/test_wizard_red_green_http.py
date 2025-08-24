#!/usr/bin/env python3
"""
HTTP API version of red/green wizard test.

This test validates the red/green testing methodology by comparing
broken vs fixed behavior using HTTP API calls instead of browser automation.
Shares test data and validation logic with the browser version.
"""

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import shared testing utilities
from testing_ui.testing_shared import (
    TEST_SCENARIOS,
    generate_test_user_id,
    get_test_url,
    setup_http_test_session,
    validate_campaign_created_successfully,
    validate_no_dragon_knight_in_custom,
)


def test_red_empty_custom_campaign():
    """RED TEST: Empty custom campaign that should show the bug (if it exists)"""

    print("🔴 RED TEST: Empty custom campaign (HTTP API)...")
    print("   This test checks if the bug still exists")

    # Use shared test scenario for red test
    scenario = TEST_SCENARIOS["red_green_comparison"]
    red_campaign_data = scenario["red_data"].copy()

    # Setup HTTP session using shared utility
    base_url = get_test_url("http")
    test_user_id = generate_test_user_id("red-test-http")
    session, _ = setup_http_test_session(base_url, test_user_id)

    print("📤 Creating RED test campaign (empty fields)")
    print(f"   Title: {red_campaign_data['title']}")
    print(f"   Character: '{red_campaign_data['character_name']}' (empty)")
    print(f"   Setting: '{red_campaign_data['setting']}' (empty)")
    print(f"   Custom options: {red_campaign_data['custom_options']} (none)")

    # Make campaign creation request
    response = session.post(f"{base_url}/api/campaigns", json=red_campaign_data)

    print(f"📥 Response status: {response.status_code}")

    if response.status_code == 201:
        response_data = response.json()

        # Validate basic campaign creation
        campaign_id = validate_campaign_created_successfully(response_data, "http")
        print(f"✓ RED campaign created with ID: {campaign_id}")

        # Retrieve the created campaign to analyze content
        print("📤 Retrieving RED campaign data...")
        get_response = session.get(f"{base_url}/api/campaigns/{campaign_id}")

        if get_response.status_code == 200:
            campaign_details = get_response.json()

            # Extract all text content for analysis
            full_content = ""

            if (
                "narrative_history" in campaign_details
                and campaign_details["narrative_history"]
            ):
                for entry in campaign_details["narrative_history"]:
                    if isinstance(entry, dict):
                        for _key, value in entry.items():
                            if isinstance(value, str):
                                full_content += f" {value}"

            print(f"📄 RED test content length: {len(full_content)} characters")

            # Check if this shows the bug (Dragon Knight content in custom campaign)
            dragon_knight_indicators = [
                "ser arion",
                "dragon knight",
                "celestial imperium",
                "empress sariel",
            ]
            found_bug_indicators = []

            content_lower = full_content.lower()
            for indicator in dragon_knight_indicators:
                if indicator in content_lower:
                    found_bug_indicators.append(indicator)

            if len(found_bug_indicators) > 0:
                print(
                    f"🔴 RED TEST RESULT: Bug detected! Found Dragon Knight content: {found_bug_indicators}"
                )
                print("   This indicates the bug exists and needs fixing")
                red_result = "BUG_DETECTED"
            else:
                print("🔴 RED TEST RESULT: No Dragon Knight content found")
                print(
                    "   This suggests the bug is already fixed or doesn't occur in this scenario"
                )
                red_result = "NO_BUG"

            return campaign_id, red_result

        print(f"❌ Failed to retrieve RED campaign: {get_response.text}")
        raise Exception(
            f"RED campaign retrieval failed with status {get_response.status_code}"
        )

    print(f"❌ Failed to create RED campaign: {response.text}")
    raise Exception(f"RED campaign creation failed with status {response.status_code}")


def test_green_filled_custom_campaign():
    """GREEN TEST: Properly filled custom campaign that should work correctly"""

    print("\n🟢 GREEN TEST: Properly filled custom campaign (HTTP API)...")
    print("   This test shows the correct behavior")

    # Use shared test scenario for green test
    scenario = TEST_SCENARIOS["red_green_comparison"]
    green_campaign_data = scenario["green_data"].copy()

    # Setup HTTP session
    base_url = get_test_url("http")
    test_user_id = generate_test_user_id("green-test-http")
    session, _ = setup_http_test_session(base_url, test_user_id)

    print("📤 Creating GREEN test campaign (properly filled)")
    print(f"   Title: {green_campaign_data['title']}")
    print(f"   Character: '{green_campaign_data['character_name']}' (filled)")
    print(f"   Setting: '{green_campaign_data['setting']}' (filled)")
    print(f"   Custom options: {green_campaign_data['custom_options']}")

    # Make campaign creation request
    response = session.post(f"{base_url}/api/campaigns", json=green_campaign_data)

    print(f"📥 Response status: {response.status_code}")

    if response.status_code == 201:
        response_data = response.json()

        # Validate basic campaign creation
        campaign_id = validate_campaign_created_successfully(response_data, "http")
        print(f"✓ GREEN campaign created with ID: {campaign_id}")

        # Retrieve the created campaign to analyze content
        print("📤 Retrieving GREEN campaign data...")
        get_response = session.get(f"{base_url}/api/campaigns/{campaign_id}")

        if get_response.status_code == 200:
            campaign_details = get_response.json()

            # Extract all text content for analysis
            full_content = ""

            if (
                "narrative_history" in campaign_details
                and campaign_details["narrative_history"]
            ):
                for entry in campaign_details["narrative_history"]:
                    if isinstance(entry, dict):
                        for _key, value in entry.items():
                            if isinstance(value, str):
                                full_content += f" {value}"

            print(f"📄 GREEN test content length: {len(full_content)} characters")

            # Check that GREEN test shows correct behavior (custom character appears)
            expected_character = green_campaign_data["character_name"]
            expected_setting = green_campaign_data["setting"]

            if expected_character in full_content:
                print(
                    f"✓ Expected character '{expected_character}' found in GREEN test"
                )
                character_found = True
            else:
                print(
                    f"⚠️  Expected character '{expected_character}' not found in GREEN test"
                )
                character_found = False

            if expected_setting in full_content:
                print(f"✓ Expected setting '{expected_setting}' found in GREEN test")
                setting_found = True
            else:
                print(
                    f"⚠️  Expected setting '{expected_setting}' not found in GREEN test"
                )
                setting_found = False

            # Most importantly, GREEN test should NOT have Dragon Knight content
            try:
                validate_no_dragon_knight_in_custom(full_content, "http")
                print("✓ GREEN TEST: No Dragon Knight contamination")
                no_contamination = True
            except AssertionError as e:
                print(f"❌ GREEN TEST: Dragon Knight contamination detected: {e}")
                no_contamination = False

            # Determine GREEN test result
            if no_contamination and (character_found or setting_found):
                green_result = "WORKING_CORRECTLY"
                print("🟢 GREEN TEST RESULT: Working correctly!")
            else:
                green_result = "ISSUES_DETECTED"
                print("🟢 GREEN TEST RESULT: Some issues detected")

            return campaign_id, green_result

        print(f"❌ Failed to retrieve GREEN campaign: {get_response.text}")
        raise Exception(
            f"GREEN campaign retrieval failed with status {get_response.status_code}"
        )

    print(f"❌ Failed to create GREEN campaign: {response.text}")
    raise Exception(
        f"GREEN campaign creation failed with status {response.status_code}"
    )


def compare_red_green_results(red_result, green_result):
    """Compare RED and GREEN test results to determine overall status"""

    print("\n📊 RED/GREEN TEST COMPARISON:")
    print("=" * 50)
    print(f"🔴 RED TEST (empty custom):    {red_result}")
    print(f"🟢 GREEN TEST (filled custom): {green_result}")
    print("=" * 50)

    if red_result == "NO_BUG" and green_result == "WORKING_CORRECTLY":
        print("✅ PERFECT: Bug is fixed and correct behavior works")
        return "PERFECT"
    if red_result == "BUG_DETECTED" and green_result == "WORKING_CORRECTLY":
        print("⚠️  PARTIAL: Bug exists but workaround (filled fields) works")
        return "PARTIAL_FIX"
    if red_result == "NO_BUG" and green_result == "ISSUES_DETECTED":
        print("🤔 UNEXPECTED: No bug in empty case but issues in filled case")
        return "UNEXPECTED"
    if red_result == "BUG_DETECTED" and green_result == "ISSUES_DETECTED":
        print("❌ BROKEN: Bug exists and even workaround has issues")
        return "BROKEN"
    print("🤷 UNKNOWN: Unexpected combination of results")
    return "UNKNOWN"


def main():
    """Run all HTTP red/green wizard tests"""
    print("=" * 70)
    print("🚀 Running Red/Green Wizard HTTP API Tests (Shared Utilities)")
    print("=" * 70)

    try:
        # Run RED test (should show bug if it exists)
        red_campaign_id, red_result = test_red_empty_custom_campaign()

        # Run GREEN test (should show correct behavior)
        green_campaign_id, green_result = test_green_filled_custom_campaign()

        # Compare results
        overall_result = compare_red_green_results(red_result, green_result)

        print(f"\n🎯 OVERALL RED/GREEN TEST RESULT: {overall_result}")
        print("=" * 70)

        if overall_result in ["PERFECT", "PARTIAL_FIX"]:
            print("✅ Red/Green testing completed successfully!")
        else:
            print("⚠️  Red/Green testing identified issues that need attention")

        print("=" * 70)

    except Exception as e:
        print(f"\n❌ Red/Green test failed: {str(e)}")
        print("=" * 70)
        raise


if __name__ == "__main__":
    main()
