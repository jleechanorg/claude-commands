#!/usr/bin/env python3
"""
Test UI elements by creating a campaign via API first, then using browser to interact.
This bypasses UI form issues and focuses on testing the display elements.
"""

import os
import sys
import time

import requests
from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def create_campaign_via_api():
    """Create a campaign using the API with test headers."""
    url = "http://localhost:8081/api/campaigns"
    headers = {
        "Content-Type": "application/json",
        "X-Test-Bypass-Auth": "true",
        "X-Test-User-ID": "ui-debug-test",
    }
    data = {
        "title": "Debug Mode UI Test",
        "prompt": "A brave warrior enters a goblin cave",
        "genre": "Fantasy",
        "tone": "Epic",
        "selected_prompts": ["game_state_instruction.md"],
        "character_name": "Test Fighter",
        "character_background": "A warrior testing the UI",
        "debug_mode": True,  # Enable debug mode
    }

    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 201:
        result = response.json()
        return result.get("campaign_id")
    raise Exception(
        f"Failed to create campaign: {response.status_code} - {response.text}"
    )


def test_ui_elements_with_api_campaign():
    """Test UI elements using a campaign created via API."""

    # Create screenshots directory
    screenshots_dir = "ui_verification_screenshots"
    os.makedirs(screenshots_dir, exist_ok=True)

    # First create campaign via API
    print("Creating campaign via API...")
    campaign_id = create_campaign_via_api()
    print(f"✓ Created campaign with ID: {campaign_id}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Log API responses
        def log_response(response):
            if "/api/campaigns/" in response.url and response.status == 200:
                try:
                    data = response.json()
                    if "session_header" in data or "planning_block" in data:
                        print(f"\n📡 API Response fields: {list(data.keys())}")
                        if "session_header" in data:
                            print(
                                f"   session_header: {data['session_header'][:100]}..."
                            )
                        if "planning_block" in data:
                            print(
                                f"   planning_block: {data['planning_block'][:100]}..."
                            )
                except:
                    pass

        page.on("response", log_response)

        try:
            print("\n" + "=" * 60)
            print("UI Elements Verification Test (API Campaign)")
            print("=" * 60)

            # Navigate to dashboard first with test mode
            base_url = "http://localhost:8081?test_mode=true&test_user_id=ui-debug-test"
            page.goto(base_url)
            print(f"✓ Navigated to: {base_url}")

            # Wait for test mode to initialize
            page.wait_for_function("window.testAuthBypass !== undefined", timeout=5000)
            print("✓ Test mode initialized")

            # Wait for campaign list
            page.wait_for_selector("#campaign-list", timeout=10000)
            print("✓ Dashboard loaded")

            # Find and click on our campaign directly
            campaign_links = page.locator("#campaign-list .list-group-item")

            # Look for our campaign by ID or title
            found = False
            for i in range(campaign_links.count()):
                link = campaign_links.nth(i)
                link_html = link.inner_html()
                if campaign_id in link_html or "Debug Mode UI Test" in link_html:
                    link.click()
                    found = True
                    print(f"✓ Clicked on campaign: {campaign_id}")
                    break

            if not found:
                # Click first available campaign
                if campaign_links.count() > 0:
                    campaign_links.first.click()
                    print("✓ Clicked on first campaign")
                else:
                    raise Exception("No campaigns found")

            # Wait for game view to show
            page.wait_for_selector("#game-view.active-view", timeout=10000)
            print("✓ Game view visible")

            # Wait for story content to show
            page.wait_for_selector("#story-content", timeout=10000)

            # Wait for any story entries to appear
            page.wait_for_selector(".story-entry", timeout=10000)
            page.wait_for_timeout(2000)
            print("✓ Campaign loaded successfully")

            # Check debug mode indicator
            debug_indicator = page.locator("#debug-indicator")
            if debug_indicator.count() > 0 and debug_indicator.is_visible():
                print("✓ Debug mode indicator is visible")
            else:
                print("⚠️  Debug mode indicator not visible")

            # Screenshot initial state
            page.screenshot(
                path=f"{screenshots_dir}/01_initial_campaign.png", full_page=True
            )
            print("✓ Screenshot: Initial campaign view")

            # First check if there are already story entries from initial creation
            existing_entries = page.locator(".story-entry").all()
            print(f"✓ Found {len(existing_entries)} initial story entries")

            # Always test with a combat action to ensure dice rolls appear
            if len(existing_entries) > 0:
                print(
                    "✓ Found existing story entries, but testing interaction to verify dice rolls"
                )
                # Send combat action
                user_input = page.locator("#user-input")
                if user_input.count() > 0:
                    # Type combat action
                    user_input.fill(
                        "I attack the goblin with my sword! Roll for attack and damage."
                    )
                    print("✓ Typed combat action")

                    # Send the action
                    user_input.press("Enter")
                    print("✓ Sent combat action")

                    # Wait for response with longer timeout
                    print("\n⏳ Waiting for AI response...")
                    try:
                        page.wait_for_function(
                            "document.querySelector('#user-input').disabled === false",
                            timeout=60000,  # 60 seconds for AI response
                        )
                        page.wait_for_timeout(3000)  # Extra time for DOM updates
                    except:
                        print("⚠️  AI response timed out, checking current state...")

            # Get all story entries after potential action
            story_entries = page.locator(".story-entry").all()
            print(f"✓ Total story entries: {len(story_entries)}")

            if len(story_entries) >= 1:  # At least initial story
                # Get the last entry (AI response)
                last_entry = story_entries[-1]

                # Full response screenshot
                last_entry.screenshot(path=f"{screenshots_dir}/02_full_ai_response.png")
                print("\n📸 Captured full AI response")

                # Check and screenshot each element
                print("\n🔍 Checking for UI elements:")

                # 1. Session Header
                session_header = last_entry.locator(".session-header")
                if session_header.count() > 0 and session_header.is_visible():
                    session_header.screenshot(
                        path=f"{screenshots_dir}/03_session_header.png"
                    )
                    content = session_header.inner_text()
                    print("\n✓ SESSION HEADER found:")
                    print("  Style: Gray background, monospace font")
                    print(f"  Content: {content[:150]}...")
                else:
                    print("\n✗ Session header NOT FOUND")

                # 2. Narrative
                narrative = last_entry.locator("p").first
                if narrative.count() > 0 and narrative.is_visible():
                    narrative.screenshot(path=f"{screenshots_dir}/04_narrative.png")
                    content = narrative.inner_text()
                    print("\n✓ NARRATIVE found:")
                    print(f"  Label: {content.split(':')[0]}:")
                    print(f"  Text: {content.split(':', 1)[1][:100]}...")
                else:
                    print("\n✗ Narrative NOT FOUND")

                # 3. Dice Rolls
                dice_rolls = last_entry.locator(".dice-rolls")
                if dice_rolls.count() > 0 and dice_rolls.is_visible():
                    dice_rolls.screenshot(path=f"{screenshots_dir}/05_dice_rolls.png")
                    content = dice_rolls.inner_text()
                    print("\n✓ DICE ROLLS found:")
                    print("  Style: Green background")
                    print(f"  Content: {content}")
                else:
                    print("\n✗ Dice rolls NOT FOUND")

                # 4. Resources
                resources = last_entry.locator(".resources")
                if resources.count() > 0 and resources.is_visible():
                    resources.screenshot(path=f"{screenshots_dir}/06_resources.png")
                    content = resources.inner_text()
                    print("\n✓ RESOURCES found:")
                    print("  Style: Yellow background")
                    print(f"  Content: {content}")
                else:
                    print("\n✗ Resources NOT FOUND")

                # 5. Planning Block
                planning_block = last_entry.locator(".planning-block")
                if planning_block.count() > 0 and planning_block.is_visible():
                    planning_block.screenshot(
                        path=f"{screenshots_dir}/07_planning_block.png"
                    )
                    content = planning_block.inner_text()
                    print("\n✓ PLANNING BLOCK found:")
                    print("  Style: Blue background")
                    print(f"  Content preview: {content[:200]}...")
                else:
                    print("\n✗ Planning block NOT FOUND")

                # 6. Debug Info (only in debug mode)
                debug_info = last_entry.locator(".debug-info")
                if debug_info.count() > 0 and debug_info.is_visible():
                    debug_info.screenshot(path=f"{screenshots_dir}/08_debug_info.png")
                    content = debug_info.inner_text()
                    print("\n✓ DEBUG INFO found (DEBUG MODE ACTIVE):")
                    print("  Style: Gray background")
                    print(f"  Content preview: {content[:150]}...")
                else:
                    print("\n⚠️  Debug info NOT FOUND - Debug mode may not be active")

                # Final summary
                print("\n" + "=" * 60)
                print("VERIFICATION SUMMARY")
                print("=" * 60)

                # Check raw HTML for elements and log it
                html = last_entry.inner_html()
                print(
                    f"\n📋 Raw HTML of story entry (first 1000 chars):\n{html[:1000]}\n"
                )

                elements_found = {
                    "session-header": "session-header" in html,
                    "dice-rolls": "dice-rolls" in html,
                    "resources": "resources" in html,
                    "planning-block": "planning-block" in html,
                    "debug-info": "debug-info" in html,
                    "Planning Block Text": "--- PLANNING BLOCK ---" in html,
                    "Action Options": "What would you like to do" in html,
                }

                found_count = sum(1 for found in elements_found.values() if found)

                for element, found in elements_found.items():
                    print(f"{'✓' if found else '✗'} {element}")

                print(f"\nTotal: {found_count}/{len(elements_found)} elements found")

                # Full page screenshot
                page.screenshot(
                    path=f"{screenshots_dir}/09_full_page_final.png", full_page=True
                )
                print("\n✓ Final full page screenshot saved")

            else:
                print("❌ No story entries found")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            page.screenshot(
                path=f"{screenshots_dir}/error_screenshot.png", full_page=True
            )
            raise
        finally:
            print(f"\n✓ All screenshots saved in: {screenshots_dir}/")
            print(
                "\nTest complete. Browser will stay open for 20 seconds for inspection..."
            )
            time.sleep(20)
            browser.close()


if __name__ == "__main__":
    print("UI Elements Verification Test - Using API to create campaign")
    print(
        "Make sure server is running with: TESTING=true PORT=8081 python main.py serve"
    )
    print("-" * 60)
    test_ui_elements_with_api_campaign()
