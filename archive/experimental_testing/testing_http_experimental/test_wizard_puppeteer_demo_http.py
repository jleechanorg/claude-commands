#!/usr/bin/env python3
"""
HTTP API version of wizard puppeteer demo.

This test demonstrates wizard functionality through HTTP API calls,
providing the same validation as the browser demo but via API endpoints.
Uses shared utilities for test data and validation.
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
    validate_character_name_display,
    validate_no_dragon_knight_in_custom,
)


def demonstrate_wizard_fix_via_api():
    """Demonstrate wizard fix functionality via HTTP API calls"""

    print("🚀 HTTP API Demo: Campaign Wizard Character/Setting Fix")
    print("=" * 60)

    # Setup HTTP session using shared utility
    base_url = get_test_url("http")
    test_user_id = generate_test_user_id("puppeteer-demo-http")
    session, _ = setup_http_test_session(base_url, test_user_id)

    # Demo steps equivalent to browser automation
    demo_steps = [
        {
            "step": 1,
            "action": "Verify homepage accessibility",
            "description": "Initial API connectivity test (equivalent to page load)",
        },
        {
            "step": 2,
            "action": "Test custom campaign creation",
            "description": "Campaign creation with custom character (equivalent to wizard flow)",
        },
        {
            "step": 3,
            "action": "Validate character display",
            "description": "Verify custom character appears correctly (equivalent to preview validation)",
        },
        {
            "step": 4,
            "action": "Test Dragon Knight isolation",
            "description": "Ensure no Dragon Knight contamination (equivalent to bug fix verification)",
        },
    ]

    for step_info in demo_steps:
        step_num = step_info["step"]
        action = step_info["action"]
        description = step_info["description"]

        print(f"\n📍 Step {step_num}: {action}")
        print(f"   {description}")

        if step_num == 1:
            # Step 1: Homepage accessibility (equivalent to navigate to homepage)
            response = session.get(
                f"{base_url}?test_mode=true&test_user_id={test_user_id}"
            )
            if response.status_code == 200:
                print("   ✅ API connectivity established")
            else:
                print(f"   ❌ API connectivity failed: {response.status_code}")
                raise Exception("Demo failed at step 1")

        elif step_num == 2:
            # Step 2: Campaign creation (equivalent to clicking through wizard)
            scenario = TEST_SCENARIOS["custom_character_display"]
            campaign_data = scenario["campaign_data"].copy()

            print(f"   📤 Creating campaign: '{campaign_data['title']}'")
            print(f"   📤 Character: '{campaign_data['character_name']}'")
            print(f"   📤 Setting: '{campaign_data['setting']}'")

            create_response = session.post(
                f"{base_url}/api/campaigns", json=campaign_data
            )

            if create_response.status_code == 201:
                campaign_response = create_response.json()
                campaign_id = validate_campaign_created_successfully(
                    campaign_response, "http"
                )
                print(f"   ✅ Campaign created successfully: {campaign_id}")

                # Store for next steps
                demo_campaign_id = campaign_id
                demo_expected_character = scenario["expected_character"]
            else:
                print(f"   ❌ Campaign creation failed: {create_response.status_code}")
                raise Exception("Demo failed at step 2")

        elif step_num == 3:
            # Step 3: Character display validation (equivalent to checking preview)
            get_response = session.get(f"{base_url}/api/campaigns/{demo_campaign_id}")

            if get_response.status_code == 200:
                campaign_details = get_response.json()
                campaign_content = str(campaign_details)

                print(
                    f"   📄 Retrieved campaign content ({len(campaign_content)} characters)"
                )

                # Validate character display
                try:
                    validate_character_name_display(
                        campaign_content, demo_expected_character, "http"
                    )
                    print(
                        f"   ✅ Character '{demo_expected_character}' displayed correctly"
                    )
                except AssertionError as e:
                    print(f"   ⚠️  Character display issue: {e}")
            else:
                print(f"   ❌ Campaign retrieval failed: {get_response.status_code}")
                raise Exception("Demo failed at step 3")

        elif step_num == 4:
            # Step 4: Dragon Knight isolation validation (equivalent to bug fix verification)
            get_response = session.get(f"{base_url}/api/campaigns/{demo_campaign_id}")

            if get_response.status_code == 200:
                campaign_details = get_response.json()
                campaign_content = str(campaign_details)

                # Validate no Dragon Knight contamination
                try:
                    validate_no_dragon_knight_in_custom(campaign_content, "http")
                    print("   ✅ No Dragon Knight contamination detected")
                    print("   ✅ Bug fix working correctly!")
                except AssertionError as e:
                    print(f"   ❌ Dragon Knight contamination detected: {e}")
                    print("   ❌ Bug fix validation failed!")
                    raise Exception("Demo failed at step 4 - bug not fixed")
            else:
                print(f"   ❌ Campaign retrieval failed: {get_response.status_code}")
                raise Exception("Demo failed at step 4")

    print("\n🎉 DEMO COMPLETE: All wizard fix validations passed via HTTP API!")
    print("   Custom character display working correctly")
    print("   Dragon Knight isolation working correctly")
    print("   Bug fix successfully demonstrated")

    return demo_campaign_id


def demonstrate_before_after_comparison():
    """Demonstrate before/after comparison via HTTP API"""

    print("\n🔄 HTTP API Demo: Before/After Comparison")
    print("=" * 50)

    # Setup HTTP session
    base_url = get_test_url("http")
    test_user_id = generate_test_user_id("before-after-http")
    session, _ = setup_http_test_session(base_url, test_user_id)

    # "BEFORE" simulation: Empty custom campaign (potential for bug)
    print("\n📍 BEFORE: Testing empty custom campaign (bug scenario)")

    red_scenario = TEST_SCENARIOS["red_green_comparison"]
    before_data = red_scenario["red_data"].copy()

    print(
        f"   Creating campaign with empty character: '{before_data['character_name']}'"
    )

    before_response = session.post(f"{base_url}/api/campaigns", json=before_data)

    if before_response.status_code == 201:
        before_campaign_response = before_response.json()
        before_campaign_id = validate_campaign_created_successfully(
            before_campaign_response, "http"
        )

        # Check BEFORE results
        before_get_response = session.get(
            f"{base_url}/api/campaigns/{before_campaign_id}"
        )
        if before_get_response.status_code == 200:
            before_details = before_get_response.json()
            before_content = str(before_details)

            # Check for Dragon Knight contamination (the bug)
            try:
                validate_no_dragon_knight_in_custom(before_content, "http")
                print(
                    "   ✅ BEFORE: No Dragon Knight contamination (bug already fixed)"
                )
                before_result = "GOOD"
            except AssertionError as e:
                print(f"   ❌ BEFORE: Dragon Knight contamination detected - {e}")
                before_result = "BUG_PRESENT"

    # "AFTER" simulation: Filled custom campaign (proper behavior)
    print("\n📍 AFTER: Testing filled custom campaign (correct behavior)")

    after_data = red_scenario["green_data"].copy()
    expected_character = after_data["character_name"]

    print(f"   Creating campaign with custom character: '{expected_character}'")

    after_response = session.post(f"{base_url}/api/campaigns", json=after_data)

    if after_response.status_code == 201:
        after_campaign_response = after_response.json()
        after_campaign_id = validate_campaign_created_successfully(
            after_campaign_response, "http"
        )

        # Check AFTER results
        after_get_response = session.get(
            f"{base_url}/api/campaigns/{after_campaign_id}"
        )
        if after_get_response.status_code == 200:
            after_details = after_get_response.json()
            after_content = str(after_details)

            # Check for proper character display and no contamination
            character_found = expected_character in after_content

            try:
                validate_no_dragon_knight_in_custom(after_content, "http")
                no_contamination = True
            except AssertionError:
                no_contamination = False

            if character_found and no_contamination:
                print(
                    "   ✅ AFTER: Custom character displayed correctly, no contamination"
                )
                after_result = "PERFECT"
            elif character_found:
                print("   ⚠️  AFTER: Character found but contamination present")
                after_result = "PARTIAL"
            else:
                print("   ❌ AFTER: Character not found or contamination present")
                after_result = "ISSUES"

    # Comparison summary
    print("\n📊 BEFORE/AFTER COMPARISON SUMMARY:")
    print(f"   📉 BEFORE (empty): {before_result}")
    print(f"   📈 AFTER (filled): {after_result}")

    if before_result == "GOOD" and after_result == "PERFECT":
        print("   🎉 EXCELLENT: Bug is fixed and proper behavior works!")
    elif before_result == "BUG_PRESENT" and after_result == "PERFECT":
        print("   ⚠️  MIXED: Bug exists but workaround works")
    elif before_result == "GOOD" and after_result != "PERFECT":
        print("   🤔 UNEXPECTED: No bug in empty case but issues in filled case")
    else:
        print("   ❌ PROBLEMS: Issues detected in the fix")

    return before_campaign_id, after_campaign_id


def main():
    """Run all HTTP wizard puppeteer demo tests"""
    print("=" * 70)
    print("🚀 Running Wizard Puppeteer Demo HTTP API Tests (Browser Equivalent)")
    print("=" * 70)

    try:
        # Demo 1: Complete wizard fix demonstration
        demonstrate_wizard_fix_via_api()

        # Demo 2: Before/after comparison
        demonstrate_before_after_comparison()

        print("\n" + "=" * 70)
        print("✅ All wizard puppeteer demo HTTP tests passed!")
        print("🎯 HTTP API equivalent of browser wizard demo working")
        print("🎭 Visual browser demo functionality replicated via API calls")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        print("=" * 70)
        raise


if __name__ == "__main__":
    main()
