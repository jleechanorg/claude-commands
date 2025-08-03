#!/usr/bin/env python3
"""
Simple test to demonstrate mock service working with screenshot.
"""

import time

from playwright.sync_api import sync_playwright


def test_mock_demo():
    """Create campaign and take screenshot to verify mock is working."""

    print("Mock Service Demo Test")
    print("=" * 50)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # Navigate to the new campaign page
            test_url = "http://localhost:6006/new-campaign?test_mode=true&test_user_id=mock-demo-test"
            print(f"Navigating to: {test_url}")

            response = page.goto(test_url, wait_until="networkidle", timeout=15000)
            print(f"✓ Server responded with status: {response.status}")

            # Take screenshot of the campaign creation form
            screenshot_path = "/tmp/worldarchitectai/browser/mock_demo_01_form.png"
            page.screenshot(path=screenshot_path)
            print(f"✓ Screenshot saved: {screenshot_path}")

            # Fill in campaign details
            print("\nFilling campaign form...")

            try:
                # Wait for form to load
                page.wait_for_selector("#campaign-title", timeout=5000)

                # Fill basic fields
                page.fill("#campaign-title", "Mock Test Campaign")
                page.fill("#campaign-description", "Testing mock Gemini service")

                # Select Dragon Knight campaign type if available
                dragon_knight_btn = page.query_selector(
                    "button[data-campaign-type='dragon_knight']"
                )
                if dragon_knight_btn:
                    dragon_knight_btn.click()
                    print("✓ Selected Dragon Knight campaign type")

                # Take screenshot after form filled
                page.screenshot(
                    path="/tmp/worldarchitectai/browser/mock_demo_02_filled.png"
                )
                print("✓ Form filled screenshot saved")

                # Try to submit the form
                submit_btn = page.query_selector(
                    "button[type='submit'], .btn-primary, #create-campaign-btn"
                )
                if submit_btn:
                    print("Found submit button, clicking...")
                    submit_btn.click()

                    # Wait for response (this should use mock service)
                    time.sleep(3)

                    # Take final screenshot
                    page.screenshot(
                        path="/tmp/worldarchitectai/browser/mock_demo_03_result.png"
                    )
                    print("✓ Result screenshot saved")

                    # Check if we got redirected to game view
                    current_url = page.url
                    if "/campaign/" in current_url:
                        print(f"✓ Redirected to campaign: {current_url}")
                    else:
                        print(f"Still on form page: {current_url}")

                else:
                    print("⚠️  No submit button found")

            except Exception as e:
                print(f"⚠️  Form interaction failed: {e}")
                page.screenshot(
                    path="/tmp/worldarchitectai/browser/mock_demo_error.png"
                )

            print("\n✓ Test completed")

        except Exception as e:
            print(f"\n✗ Test failed: {e}")

        finally:
            browser.close()


if __name__ == "__main__":
    test_mock_demo()
