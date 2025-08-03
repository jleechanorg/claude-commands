#!/usr/bin/env python3
"""
Focused test to debug inline campaign name editing and story reader controls.
This script navigates to a campaign and attempts to interact with inline editing features.
"""

import os
import sys
import time
import traceback

from playwright.sync_api import sync_playwright

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_inline_editing_features():
    """Test inline editing and story reader controls with detailed debugging."""

    with sync_playwright() as p:
        # Launch browser with devtools open for debugging
        browser = p.chromium.launch(
            headless=False,  # Run with GUI for visual debugging
            devtools=True,  # Open developer tools
        )
        context = browser.new_context()
        page = context.new_page()

        # Enable console logging
        page.on("console", lambda msg: print(f"[CONSOLE {msg.type}] {msg.text}"))
        page.on("pageerror", lambda err: print(f"[PAGE ERROR] {err}"))

        try:
            print("1. Navigating to application...")
            page.goto("http://localhost:6006?test_mode=true")
            page.wait_for_load_state("networkidle")

            # Wait for auth view
            print("2. Waiting for auth view...")
            page.wait_for_selector("#auth-view.active-view", timeout=5000)

            # Click anonymous login
            print("3. Clicking anonymous login...")
            page.click("button:has-text('Continue without login')")

            # Wait for dashboard
            print("4. Waiting for dashboard view...")
            page.wait_for_selector("#dashboard-view.active-view", timeout=10000)

            # Check for existing campaigns
            print("5. Looking for existing campaigns...")
            campaign_cards = page.query_selector_all(".campaign-card")

            if campaign_cards:
                print(f"   Found {len(campaign_cards)} campaigns")
                # Click the first campaign
                page.click(".campaign-card:first-child")
            else:
                print("   No campaigns found - creating a new one...")
                # Create a new campaign first
                page.click("button:has-text('Create New Campaign')")
                page.wait_for_selector("#new-campaign-view.active-view")

                # Fill campaign details
                page.fill("#campaign-title", "Test Campaign for Inline Editing")
                page.fill(
                    "#campaign-prompt",
                    "A test campaign for debugging inline editing features.",
                )

                # Create campaign
                page.click("button:has-text('Create Campaign')")

            # Wait for game view
            print("6. Waiting for game view...")
            page.wait_for_selector("#game-view.active-view", timeout=30000)

            # Check if InlineEditor is available
            print("7. Checking InlineEditor availability...")
            inline_editor_exists = page.evaluate(
                "() => typeof window.InlineEditor !== 'undefined'"
            )
            print(f"   InlineEditor class exists: {inline_editor_exists}")

            # Check if StoryReader is available
            story_reader_exists = page.evaluate(
                "() => typeof window.StoryReader !== 'undefined'"
            )
            print(f"   StoryReader class exists: {story_reader_exists}")

            # Get campaign title element
            print("8. Checking campaign title element...")
            title_element = page.query_selector("#game-title")
            if title_element:
                title_text = title_element.inner_text()
                print(f"   Campaign title: '{title_text}'")

                # Check if it has inline-editable class
                has_inline_class = page.evaluate("""
                    () => {
                        const el = document.getElementById('game-title');
                        return el ? el.classList.contains('inline-editable') : false;
                    }
                """)
                print(f"   Has inline-editable class: {has_inline_class}")

                # Check for any InlineEditor instances
                editor_count = page.evaluate("""
                    () => {
                        // Check if any InlineEditor instances were created
                        const scripts = Array.from(document.querySelectorAll('script'));
                        const appScript = scripts.find(s => s.src && s.src.includes('app.js'));
                        return appScript ? 'app.js loaded' : 'app.js NOT loaded';
                    }
                """)
                print(f"   Script status: {editor_count}")

                # Try to click the title to trigger inline editing
                print("9. Attempting to trigger inline editing...")
                title_element.click()
                time.sleep(1)

                # Check if edit container appeared
                edit_container = page.query_selector(".inline-edit-container")
                if edit_container:
                    print("   ✓ Inline edit container appeared!")

                    # Check for input field
                    edit_input = page.query_selector(".inline-edit-input")
                    if edit_input:
                        print("   ✓ Edit input field found")
                        current_value = edit_input.input_value()
                        print(f"   Current value: '{current_value}'")

                        # Try to edit
                        edit_input.fill("Updated Campaign Name")
                        print("   Filled new value: 'Updated Campaign Name'")

                        # Save
                        save_btn = page.query_selector(".inline-edit-save")
                        if save_btn:
                            print("   ✓ Save button found - clicking...")
                            save_btn.click()
                            time.sleep(2)

                            # Check if title updated
                            new_title = page.query_selector("#game-title").inner_text()
                            print(f"   Title after save: '{new_title}'")
                else:
                    print("   ✗ Inline edit container did NOT appear")
                    print("   Debugging: Checking what happens on click...")

                    # Try manual initialization
                    init_result = page.evaluate("""
                        () => {
                            const titleEl = document.getElementById('game-title');
                            if (!titleEl) return 'No title element found';

                            if (typeof window.InlineEditor === 'undefined') {
                                return 'InlineEditor class not defined';
                            }

                            // Try to create a new instance manually
                            try {
                                const editor = new window.InlineEditor(titleEl, {
                                    saveFn: async (value) => console.log('Save:', value)
                                });
                                return 'InlineEditor created manually';
                            } catch (e) {
                                return 'Error creating InlineEditor: ' + e.message;
                            }
                        }
                    """)
                    print(f"   Manual initialization result: {init_result}")

            # Check for story reader controls
            print("\n10. Checking for story reader controls...")

            # Look for any story reader UI elements
            story_controls = page.evaluate("""
                () => {
                    const selectors = [
                        '.story-reader-controls',
                        '.story-navigation',
                        '.story-controls',
                        '[class*="story"][class*="control"]',
                        '[class*="story"][class*="reader"]',
                        '#story-controls',
                        '#storyControls',
                        '.pause-story',
                        '.continue-story'
                    ];

                    const found = [];
                    for (const selector of selectors) {
                        const els = document.querySelectorAll(selector);
                        if (els.length > 0) {
                            found.push(`${selector}: ${els.length} element(s)`);
                        }
                    }

                    // Also check for any buttons with story-related text
                    const buttons = Array.from(document.querySelectorAll('button'));
                    const storyButtons = buttons.filter(b =>
                        b.textContent.toLowerCase().includes('pause') ||
                        b.textContent.toLowerCase().includes('continue') ||
                        b.textContent.toLowerCase().includes('story')
                    );

                    if (storyButtons.length > 0) {
                        found.push(`Story-related buttons: ${storyButtons.map(b => b.textContent).join(', ')}`);
                    }

                    return found.length > 0 ? found : ['No story reader controls found'];
                }
            """)

            for control in story_controls:
                print(f"   {control}")

            # Check story content area
            print("\n11. Checking story content area...")
            story_content = page.query_selector("#story-content")
            if story_content:
                print("   ✓ Story content area found")
                story_entries = page.query_selector_all("#story-content .story-entry")
                print(f"   Story entries: {len(story_entries)}")

            # Take a screenshot for visual inspection
            print("\n12. Taking screenshot...")
            screenshot_path = "/tmp/inline_editing_debug.png"
            page.screenshot(path=screenshot_path, full_page=True)
            print(f"   Screenshot saved to: {screenshot_path}")

            # Wait for manual inspection
            print(
                "\n[DEBUG MODE] Browser will stay open for 30 seconds for manual inspection..."
            )
            print("You can interact with the page manually to test features.")
            time.sleep(30)

        except Exception as e:
            print(f"\n[ERROR] Test failed: {e}")

            traceback.print_exc()

            # Take error screenshot
            try:
                error_screenshot = "/tmp/inline_editing_error.png"
                page.screenshot(path=error_screenshot, full_page=True)
                print(f"Error screenshot saved to: {error_screenshot}")
            except:
                pass

        finally:
            browser.close()
            print("\nTest completed.")


if __name__ == "__main__":
    print("Inline Editing Debug Test")
    print("=" * 50)
    print("This test will:")
    print("1. Navigate to a campaign")
    print("2. Check if InlineEditor is properly initialized")
    print("3. Attempt to trigger inline editing on campaign name")
    print("4. Look for story reader controls")
    print("5. Take screenshots for debugging")
    print("=" * 50)

    test_inline_editing_features()
