#!/usr/bin/env python3
"""
Test planning block buttons with a real campaign flow.
This test navigates through the actual app to verify the feature works.
"""

import os

from playwright.sync_api import sync_playwright

# Screenshot directory
SCREENSHOT_DIR = "/tmp/worldarchitectai/real_campaign_test"


def main():
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("🌐 Navigating to test server...")
        page.goto("http://localhost:6006?test_mode=true")

        # Wait for page to load
        page.wait_for_load_state("networkidle")
        page.screenshot(path=f"{SCREENSHOT_DIR}/01_homepage.png")
        print(f"✅ Screenshot: {SCREENSHOT_DIR}/01_homepage.png")

        # Check if we need to create a new campaign
        print("🔍 Checking for existing campaigns...")
        campaign_list = page.query_selector("#campaign-list")

        if campaign_list:
            # Look for existing campaigns
            campaign_items = page.query_selector_all(".list-group-item")
            if len(campaign_items) > 0:
                print(f"   Found {len(campaign_items)} existing campaign(s)")
                # Click the first campaign
                campaign_items[0].click()
                print("   ✅ Clicked first campaign")
            else:
                print("   No campaigns found, creating new one...")
                create_campaign(page)
        else:
            print("   Not on dashboard, creating campaign...")
            create_campaign(page)

        # Wait for game view
        print("⏳ Waiting for game view to load...")
        page.wait_for_selector("#game-view", state="visible", timeout=30000)
        page.wait_for_load_state("networkidle")

        # Check story content
        story_content = page.query_selector("#story-content")
        if story_content:
            story_text = story_content.inner_text()
            print(f"📖 Story content length: {len(story_text)} characters")

        page.screenshot(path=f"{SCREENSHOT_DIR}/02_game_view.png")
        print(f"✅ Screenshot: {SCREENSHOT_DIR}/02_game_view.png")

        # Look for planning blocks
        print("🔍 Looking for planning block choices...")
        planning_blocks = page.query_selector_all(".planning-block-choices")

        if len(planning_blocks) > 0:
            print(f"   ✅ Found {len(planning_blocks)} planning block(s)!")

            # Analyze the buttons
            last_block = planning_blocks[-1]
            buttons = last_block.query_selector_all(".choice-button")
            print(f"   📊 Found {len(buttons)} choice buttons")

            for i, button in enumerate(buttons):
                choice_id = button.query_selector(".choice-id")
                choice_desc = button.query_selector(".choice-description")
                if choice_id and choice_desc:
                    id_text = choice_id.inner_text()
                    desc_text = choice_desc.inner_text()[:50] + "..."
                    print(f"      Button {i + 1}: {id_text} - {desc_text}")

            page.screenshot(path=f"{SCREENSHOT_DIR}/03_planning_blocks_found.png")
            print(f"✅ Screenshot: {SCREENSHOT_DIR}/03_planning_blocks_found.png")

            # Try hovering and clicking
            if len(buttons) > 0:
                first_button = buttons[0]
                first_button.hover()
                page.wait_for_timeout(500)
                page.screenshot(path=f"{SCREENSHOT_DIR}/04_button_hover.png")
                print(f"✅ Screenshot: {SCREENSHOT_DIR}/04_button_hover.png")

                # Check if custom button exists
                custom_button = page.query_selector(".choice-button-custom")
                if custom_button:
                    print("   ✅ Found [Custom] button!")
                    custom_button.hover()
                    page.wait_for_timeout(500)
                    page.screenshot(path=f"{SCREENSHOT_DIR}/05_custom_hover.png")
                    print(f"✅ Screenshot: {SCREENSHOT_DIR}/05_custom_hover.png")
                else:
                    print("   ❌ Custom button not found")

        else:
            print("   ❌ No planning blocks found in current view")
            print("   📝 Sending an interaction to generate response...")

            # Send a test interaction
            user_input = page.query_selector("#user-input")
            if user_input:
                user_input.fill("I look around and assess my surroundings.")
                send_button = page.query_selector("button:has-text('Send')")
                if send_button:
                    send_button.click()
                    print("   ⏳ Waiting for AI response...")

                    # Wait for response (look for new planning blocks)
                    try:
                        page.wait_for_selector(".planning-block-choices", timeout=30000)
                        print("   ✅ Planning blocks appeared!")
                        page.screenshot(
                            path=f"{SCREENSHOT_DIR}/06_after_interaction.png"
                        )
                        print(
                            f"✅ Screenshot: {SCREENSHOT_DIR}/06_after_interaction.png"
                        )
                    except:
                        print("   ❌ Timeout waiting for planning blocks")
                        page.screenshot(path=f"{SCREENSHOT_DIR}/06_no_blocks_error.png")

        browser.close()

    print(f"\n📸 Test complete! Screenshots saved to: {SCREENSHOT_DIR}")
    print("\nResults:")
    print("- Homepage loaded ✅")
    print("- Game view accessible ✅")
    print(
        f"- Planning blocks: {'FOUND ✅' if len(planning_blocks) > 0 else 'NOT FOUND ❌'}"
    )
    print(f"- Custom button: {'FOUND ✅' if custom_button else 'NOT TESTED'}")


def create_campaign(page):
    """Helper to create a new campaign."""
    # Click new campaign button
    new_campaign_btn = page.query_selector("button:has-text('New Campaign')")
    if new_campaign_btn:
        new_campaign_btn.click()
        print("   ✅ Clicked New Campaign button")

    # Fill form
    page.wait_for_selector("#new-campaign-view", state="visible")

    title_input = page.query_selector("#campaign-title")
    if title_input:
        title_input.fill("Test Campaign for Planning Blocks")

    prompt_input = page.query_selector("#campaign-prompt")
    if prompt_input:
        prompt_input.fill(
            "A test campaign to verify planning block buttons work. Start in a tavern."
        )

    # Submit
    submit_btn = page.query_selector("button[type='submit']")
    if submit_btn:
        submit_btn.click()
        print("   ✅ Submitted campaign creation form")


if __name__ == "__main__":
    main()
