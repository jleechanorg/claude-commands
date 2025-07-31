#!/usr/bin/env python3
"""
Comprehensive test for inline editing and story reader features.
Tests both the inline campaign name editing and story reader controls.
"""

import os
import sys
import time
import traceback

from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_features():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Visual mode for debugging
        page = browser.new_page()

        # Enable console logging
        page.on("console", lambda msg: print(f"[CONSOLE] {msg.text}"))

        print("=== Testing Inline Editing and Story Reader Features ===\n")

        try:
            # 1. Navigate to application
            print("1. Loading application...")
            page.goto("http://localhost:6006?test_mode=true")
            page.wait_for_load_state("networkidle")

            # 2. Anonymous login
            print("2. Performing anonymous login...")
            page.wait_for_selector("#auth-view.active-view", timeout=5000)
            page.click("button:has-text('Continue without login')")

            # 3. Navigate to campaign
            print("3. Navigating to dashboard...")
            page.wait_for_selector("#dashboard-view.active-view", timeout=10000)

            # Find or create campaign
            campaigns = page.query_selector_all(".campaign-card")
            if campaigns:
                print(f"   Found {len(campaigns)} campaigns, using first one")
                page.click(".campaign-card:first-child")
            else:
                print("   No campaigns found, creating new one...")
                page.click("button:has-text('Create New Campaign')")
                page.wait_for_selector("#new-campaign-view.active-view")

                # Fill campaign form
                page.fill("#campaign-title", "Test Campaign for Features")
                page.fill(
                    "#campaign-prompt",
                    "A brave adventurer explores a mysterious dungeon filled with ancient treasures.",
                )
                page.click("button:has-text('Create Campaign')")

            # 4. Wait for game view
            print("4. Waiting for game view to load...")
            page.wait_for_selector("#game-view.active-view", timeout=30000)
            time.sleep(3)  # Let everything initialize

            # === TEST INLINE EDITING ===
            print("\n=== TESTING INLINE EDITING ===")

            # Get title element
            title_el = page.query_selector("#game-title")
            if title_el:
                original_title = title_el.inner_text()
                print(f"5. Found campaign title: '{original_title}'")

                # Check if inline editor is initialized
                has_inline_class = page.evaluate("""
                    () => document.getElementById('game-title').classList.contains('inline-editable')
                """)
                print(f"   Has inline-editable class: {has_inline_class}")

                # Click to edit
                print("6. Clicking title to activate inline editing...")
                title_el.click()
                time.sleep(1)

                # Check if edit mode activated
                edit_container = page.query_selector(".inline-edit-container")
                if edit_container:
                    print("   ✅ Inline edit mode ACTIVATED!")

                    # Get input field
                    edit_input = page.query_selector(".inline-edit-input")
                    if edit_input:
                        # Type new name
                        new_name = "My Awesome Campaign"
                        print(f"7. Changing name to: '{new_name}'")
                        edit_input.fill(new_name)

                        # Save
                        save_btn = page.query_selector(".inline-edit-save")
                        if save_btn:
                            print("8. Clicking save button...")
                            save_btn.click()
                            time.sleep(2)

                            # Verify change
                            updated_title = page.query_selector(
                                "#game-title"
                            ).inner_text()
                            if updated_title == new_name:
                                print(
                                    f"   ✅ Title successfully updated to: '{updated_title}'"
                                )
                            else:
                                print(
                                    f"   ❌ Title update failed. Current: '{updated_title}'"
                                )
                        else:
                            print("   ❌ Save button not found")
                    else:
                        print("   ❌ Edit input field not found")
                else:
                    print("   ❌ Inline edit mode did NOT activate")
                    print("   Attempting manual initialization...")

                    # Try manual init
                    result = page.evaluate("""
                        () => {
                            if (typeof window.InlineEditor === 'undefined') {
                                return 'InlineEditor class not available';
                            }
                            const title = document.getElementById('game-title');
                            new window.InlineEditor(title, {
                                saveFn: async (value) => {
                                    console.log('Saving:', value);
                                    // Would make API call here
                                }
                            });
                            return 'InlineEditor manually initialized';
                        }
                    """)
                    print(f"   Manual init result: {result}")
            else:
                print("   ❌ Campaign title element not found")

            # === TEST STORY READER CONTROLS ===
            print("\n=== TESTING STORY READER CONTROLS ===")

            # Check story content
            story_content = page.query_selector("#story-content")
            if story_content:
                story_entries = page.query_selector_all("#story-content .story-entry")
                print(f"9. Story content found with {len(story_entries)} entries")
            else:
                print("9. Story content area not found")

            # Check for story reader buttons
            read_btn = page.query_selector("#readStoryBtn")
            pause_btn = page.query_selector("#pauseStoryBtn")

            if read_btn:
                print("10. Found 'Read Story' button")
                is_visible = read_btn.is_visible()
                print(f"    Button visible: {is_visible}")

                if is_visible:
                    print("11. Clicking 'Read Story' button...")
                    read_btn.click()
                    time.sleep(1)

                    # Check if pause button appeared
                    pause_visible = pause_btn.is_visible() if pause_btn else False
                    if pause_visible:
                        print(
                            "    ✅ Pause button now visible - story reader activated!"
                        )

                        # Click pause
                        print("12. Testing pause functionality...")
                        pause_btn.click()
                        time.sleep(1)
                        print("    ✅ Pause clicked")
                    else:
                        print("    ❌ Pause button did not appear")

                        # Check if storyReader is available
                        sr_available = page.evaluate(
                            "() => typeof window.storyReader !== 'undefined'"
                        )
                        print(f"    window.storyReader available: {sr_available}")
            else:
                print("10. ❌ 'Read Story' button not found")

                # Debug: List all buttons in game view
                print("\n    Debugging - All buttons in game view:")
                buttons = page.evaluate("""
                    () => {
                        const gameView = document.getElementById('game-view');
                        if (!gameView) return [];
                        const buttons = Array.from(gameView.querySelectorAll('button'));
                        return buttons.map(b => ({
                            id: b.id,
                            text: b.innerText.trim(),
                            visible: window.getComputedStyle(b).display !== 'none'
                        }));
                    }
                """)
                for btn in buttons:
                    print(f"      - {btn}")

            # Take screenshot
            print("\n13. Taking screenshot...")
            screenshot_path = "/tmp/inline_story_features_test.png"
            page.screenshot(path=screenshot_path, full_page=True)
            print(f"    Screenshot saved to: {screenshot_path}")

            print(
                "\n✅ Test completed. Browser will remain open for 20 seconds for inspection..."
            )
            time.sleep(20)

        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")


            traceback.print_exc()

            # Error screenshot
            try:
                page.screenshot(path="/tmp/feature_test_error.png")
                print("Error screenshot saved to: /tmp/feature_test_error.png")
            except:
                pass

        finally:
            browser.close()


if __name__ == "__main__":
    test_features()
