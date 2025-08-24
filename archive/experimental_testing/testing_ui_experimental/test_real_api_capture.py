#!/usr/bin/env python3
"""
Test script to capture real Gemini API responses for mock updates.
WARNING: This uses REAL APIs and costs money!
"""

import json
import os

from playwright.sync_api import sync_playwright

from testing_ui.browser_test_helpers import BrowserTestHelper, setup_test_environment
from testing_ui.config import BASE_URL


def capture_api_response():
    """Run browser test with real API and capture responses."""

    # Set up environment with REAL APIs
    setup_test_environment(use_real_api=True)

    with sync_playwright() as p:
        # Launch browser in headless mode
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()

        # Enable request/response interception to capture API calls
        responses = []

        def handle_response(response):
            """Capture API responses for analysis."""
            if "/api/" in response.url and response.status == 200:
                try:
                    body = response.json()
                    responses.append({"url": response.url, "body": body})
                    print(f"📥 Captured response from: {response.url}")
                except:
                    pass

        # Set up response handler
        context.on("response", handle_response)

        # Create page
        page = context.new_page()

        # Initialize helper
        helper = BrowserTestHelper(page, BASE_URL)

        # Navigate with test auth
        helper.navigate_with_test_auth(test_user_id="real-api-test-user")
        helper.wait_for_auth_bypass()

        # Create a test campaign
        print("\n🚀 Creating campaign with REAL Gemini API...")
        success = helper.create_test_campaign(
            campaign_title="Real API Test Campaign", debug_mode=True
        )

        if success:
            print("\n✅ Campaign created successfully!")

            # Wait a bit more to capture all responses
            page.wait_for_timeout(5000)

            # Save captured responses
            output_dir = "/tmp/worldarchitectai/api_captures"
            os.makedirs(output_dir, exist_ok=True)

            for i, resp in enumerate(responses):
                filename = f"{output_dir}/response_{i}.json"
                with open(filename, "w") as f:
                    json.dump(resp, f, indent=2)
                print(f"💾 Saved: {filename}")

                # If it's a game/story response, print it
                if "game" in resp["url"] or "story" in resp["url"]:
                    print(f"\n📄 API Response from {resp['url']}:")
                    print(json.dumps(resp["body"], indent=2))
        else:
            print("\n❌ Campaign creation failed!")

        # Clean up
        browser.close()

        print(f"\n📊 Total API responses captured: {len(responses)}")
        print(f"📁 Responses saved to: {output_dir}")


if __name__ == "__main__":
    capture_api_response()
