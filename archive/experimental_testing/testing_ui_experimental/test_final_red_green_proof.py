"""
FINAL Red-Green TDD Proof: Settings Button Fix

This test proves our fix works by testing the navigation mechanism directly.
"""

import pytest
from playwright.sync_api import Page, expect


def test_settings_button_navigation_fix_works(page: Page):
    """
    PROOF that our fix works: Settings button successfully navigates to /settings

    RED (Original Bug): Button would fail to navigate properly
    GREEN (Our Fix): Button successfully changes URL to /settings
    """
    print("🧪 Testing Settings Button Navigation Fix")

    # Start at dashboard with test mode auth
    page.goto("http://localhost:8081?test_mode=true&test_user_id=test-user-123")

    # Wait for page to be ready
    page.wait_for_selector("#user-email", state="visible", timeout=10000)
    page.wait_for_selector("h2:has-text('My Campaigns')", timeout=5000)

    # Record starting state
    initial_url = page.url
    print(f"📍 Starting URL: {initial_url}")

    # Find settings button
    settings_button = page.locator("#settings-btn")
    expect(settings_button).to_be_visible()
    print("✅ Settings button is visible")

    # THE CRITICAL TEST: Click settings button
    print("🔥 Clicking settings button...")
    settings_button.click()

    # Wait for navigation (this would fail with original bug)
    try:
        page.wait_for_url("**/settings", timeout=5000)
        final_url = page.url
        print(f"📍 Final URL: {final_url}")

        # Verify navigation succeeded
        assert "/settings" in final_url, f"Expected /settings in URL, got: {final_url}"
        assert final_url != initial_url, "URL should have changed"

        print("🎉 SUCCESS: Settings button navigation works!")
        print(f"✅ Navigation: {initial_url} → {final_url}")

        return True

    except Exception as e:
        print(f"❌ FAILED: Settings navigation failed: {e}")
        print(f"Current URL: {page.url}")
        raise


def test_compare_with_working_button_for_proof(page: Page):
    """
    Additional proof: Settings button now works like other working buttons
    """
    page.goto("http://localhost:8081?test_mode=true&test_user_id=test-user-123")
    page.wait_for_selector("#user-email", state="visible", timeout=10000)
    page.wait_for_selector("h2:has-text('My Campaigns')", timeout=5000)

    print("🔄 Testing that Settings button works like other buttons...")

    # Test working button first
    start_url = page.url
    new_campaign_btn = page.locator("#go-to-new-campaign")
    new_campaign_btn.click()
    page.wait_for_url("**/new-campaign", timeout=5000)
    working_url = page.url
    print(f"✅ Working button: {start_url} → {working_url}")

    # Go back to dashboard (using browser back)
    page.go_back()
    page.wait_for_selector("h2:has-text('My Campaigns')", timeout=5000)

    # Test settings button
    dashboard_url = page.url
    settings_btn = page.locator("#settings-btn")
    settings_btn.click()
    page.wait_for_url("**/settings", timeout=5000)
    settings_url = page.url
    print(f"✅ Settings button: {dashboard_url} → {settings_url}")

    # Both should successfully navigate
    assert "/new-campaign" in working_url
    assert "/settings" in settings_url

    print("🎉 PROOF COMPLETE: Both buttons use working navigation!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
