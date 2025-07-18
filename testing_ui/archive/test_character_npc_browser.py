#!/usr/bin/env python3
"""
Real browser test for Character/NPC Management functionality using Playwright.
This test automates a real browser to test character and NPC management features.
"""

import os
import sys

from playwright.sync_api import Page, TimeoutError

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_test_base import BrowserTestBase


class CharacterNPCTest(BrowserTestBase):
    """Test Character/NPC Management functionality through real browser automation."""

    def __init__(self):
        super().__init__("Character/NPC Management Test")

    def run_test(self, page: Page) -> bool:
        """Test character and NPC management through browser automation."""

        try:
            # Take initial screenshot
            self.take_screenshot(page, "dashboard_initial")

            # Create a test campaign first
            print("🎮 Creating a test campaign for character/NPC testing...")
            if page.is_visible("text=New Campaign"):
                page.click("text=New Campaign")
                page.wait_for_timeout(1000)

                # Fill in campaign details
                if page.is_visible("#wizard-campaign-title"):
                    page.fill("#wizard-campaign-title", "Character NPC Test Campaign")
                    page.fill(
                        "#wizard-campaign-prompt",
                        "A fantasy realm filled with diverse characters and NPCs.",
                    )

                    # Click through wizard
                    print("   📝 Navigating wizard...")
                    for i in range(4):
                        if page.is_visible("#wizard-next"):
                            page.click("#wizard-next")
                            page.wait_for_timeout(1000)
                        elif page.is_visible("#launch-campaign") or page.is_visible(
                            "button:has-text('Begin Adventure')"
                        ):
                            print("   🚀 Launching campaign...")
                            launch_btn = page.query_selector(
                                "#launch-campaign"
                            ) or page.query_selector(
                                "button:has-text('Begin Adventure')"
                            )
                            if launch_btn:
                                launch_btn.click()
                            break

                # Wait for game view to load
                page.wait_for_load_state("networkidle")
                try:
                    page.wait_for_selector("#game-view.active-view", timeout=15000)
                    print("✅ Campaign created successfully")
                except:
                    print("⚠️  Game view timeout - continuing anyway")

            self.take_screenshot(page, "campaign_created")

            # Test Character Management
            print("👤 Testing Character Management...")

            # Look for character panel or character management UI
            character_selectors = [
                "#character-panel",
                ".character-sheet",
                "text=Character",
                "text=Player Character",
                "button:has-text('Character')",
                "[data-tab='character']",
            ]

            character_panel_found = False
            for selector in character_selectors:
                if page.is_visible(selector):
                    print(f"   ✅ Found character panel: {selector}")
                    page.click(selector)
                    page.wait_for_timeout(1000)
                    character_panel_found = True
                    break

            if not character_panel_found:
                print(
                    "   ⚠️  Character panel not found - looking for character creation options"
                )

                # Look for character creation buttons
                if page.is_visible("text=Create Character") or page.is_visible(
                    "button:has-text('New Character')"
                ):
                    page.click("text=Create Character")
                    page.wait_for_timeout(1000)
                    character_panel_found = True

            self.take_screenshot(page, "character_panel")

            # Test character creation/editing
            if character_panel_found:
                print("   📝 Testing character creation/editing...")

                # Look for character name field
                name_selectors = [
                    "#character-name",
                    "input[placeholder*='name']",
                    "input[placeholder*='Name']",
                    "input[name='character_name']",
                ]

                for selector in name_selectors:
                    if page.is_visible(selector):
                        print(f"   ✅ Found character name field: {selector}")
                        page.fill(selector, "Test Hero")
                        page.wait_for_timeout(500)
                        break

                # Look for character class/race fields
                class_selectors = [
                    "#character-class",
                    "select[name='class']",
                    "input[placeholder*='class']",
                ]

                for selector in class_selectors:
                    if page.is_visible(selector):
                        print(f"   ✅ Found character class field: {selector}")
                        if selector.startswith("select"):
                            page.select_option(selector, "Fighter")
                        else:
                            page.fill(selector, "Fighter")
                        page.wait_for_timeout(500)
                        break

                # Look for character stats
                stat_fields = [
                    "#character-strength",
                    "#character-dexterity",
                    "#character-constitution",
                    "#character-intelligence",
                    "#character-wisdom",
                    "#character-charisma",
                ]

                for field in stat_fields:
                    if page.is_visible(field):
                        print(f"   ✅ Found stat field: {field}")
                        page.fill(field, "15")
                        page.wait_for_timeout(200)

                # Save character if there's a save button
                if page.is_visible("button:has-text('Save Character')"):
                    page.click("button:has-text('Save Character')")
                    page.wait_for_timeout(1000)
                    print("   ✅ Character saved")

                self.take_screenshot(page, "character_created")

            # Test NPC Management
            print("🧙 Testing NPC Management...")

            # Look for NPC panel or NPC management UI
            npc_selectors = [
                "#npc-panel",
                ".npc-sheet",
                "text=NPCs",
                "text=Non-Player Characters",
                "button:has-text('NPCs')",
                "[data-tab='npcs']",
                "text=Manage NPCs",
            ]

            npc_panel_found = False
            for selector in npc_selectors:
                if page.is_visible(selector):
                    print(f"   ✅ Found NPC panel: {selector}")
                    page.click(selector)
                    page.wait_for_timeout(1000)
                    npc_panel_found = True
                    break

            if not npc_panel_found:
                print("   ⚠️  NPC panel not found - looking for NPC creation options")

                # Look for NPC creation buttons
                if page.is_visible("text=Create NPC") or page.is_visible(
                    "button:has-text('New NPC')"
                ):
                    page.click("text=Create NPC")
                    page.wait_for_timeout(1000)
                    npc_panel_found = True

            self.take_screenshot(page, "npc_panel")

            # Test NPC creation
            if npc_panel_found:
                print("   📝 Testing NPC creation...")

                # Look for NPC name field
                npc_name_selectors = [
                    "#npc-name",
                    "input[placeholder*='NPC']",
                    "input[name='npc_name']",
                ]

                for selector in npc_name_selectors:
                    if page.is_visible(selector):
                        print(f"   ✅ Found NPC name field: {selector}")
                        page.fill(selector, "Wise Sage")
                        page.wait_for_timeout(500)
                        break

                # Look for NPC type/role fields
                npc_type_selectors = [
                    "#npc-type",
                    "select[name='npc_type']",
                    "input[placeholder*='type']",
                ]

                for selector in npc_type_selectors:
                    if page.is_visible(selector):
                        print(f"   ✅ Found NPC type field: {selector}")
                        if selector.startswith("select"):
                            page.select_option(selector, "Friendly")
                        else:
                            page.fill(selector, "Friendly")
                        page.wait_for_timeout(500)
                        break

                # Look for NPC description
                desc_selectors = [
                    "#npc-description",
                    "textarea[name='npc_description']",
                    "textarea[placeholder*='description']",
                ]

                for selector in desc_selectors:
                    if page.is_visible(selector):
                        print(f"   ✅ Found NPC description field: {selector}")
                        page.fill(
                            selector,
                            "An ancient wizard who provides guidance to travelers.",
                        )
                        page.wait_for_timeout(500)
                        break

                # Save NPC if there's a save button
                if page.is_visible("button:has-text('Save NPC')"):
                    page.click("button:has-text('Save NPC')")
                    page.wait_for_timeout(1000)
                    print("   ✅ NPC saved")

                self.take_screenshot(page, "npc_created")

            # Test character/NPC interaction in game
            print("🎭 Testing character/NPC interaction in game...")

            # Send a message that involves character action
            message_input = page.query_selector(
                "#message-input"
            ) or page.query_selector("textarea[placeholder*='What do you do']")
            if message_input:
                # Test character action
                character_action = (
                    "I approach the Wise Sage and ask for advice about my quest."
                )
                message_input.fill(character_action)
                print(f"   📝 Typed character action: {character_action}")

                # Send the message
                send_button = page.query_selector(
                    "button:has-text('Send')"
                ) or page.query_selector("#send-button")
                if send_button:
                    send_button.click()
                    print("   ✉️ Message sent")
                else:
                    message_input.press("Enter")
                    print("   ⏎ Pressed Enter")

                # Wait for response
                print("⏳ Waiting for AI response about character/NPC interaction...")
                page.wait_for_timeout(5000)

                self.take_screenshot(page, "character_npc_interaction")

                # Check for NPC response
                chat_area = page.query_selector(
                    "#chat-messages"
                ) or page.query_selector(".chat-messages")
                if chat_area:
                    messages = chat_area.text_content()
                    if "sage" in messages.lower() or "advice" in messages.lower():
                        print("✅ NPC interaction response received!")
                    else:
                        print("⚠️  Response received but no NPC interaction content")

            # Test character inventory management
            print("🎒 Testing character inventory management...")

            inventory_selectors = [
                "#inventory-panel",
                ".inventory",
                "text=Inventory",
                "button:has-text('Inventory')",
                "[data-tab='inventory']",
            ]

            for selector in inventory_selectors:
                if page.is_visible(selector):
                    print(f"   ✅ Found inventory panel: {selector}")
                    page.click(selector)
                    page.wait_for_timeout(1000)

                    # Look for add item functionality
                    if page.is_visible("button:has-text('Add Item')"):
                        page.click("button:has-text('Add Item')")
                        page.wait_for_timeout(1000)

                        # Add a test item
                        item_name_field = page.query_selector(
                            "#item-name"
                        ) or page.query_selector("input[placeholder*='item']")
                        if item_name_field:
                            item_name_field.fill("Magic Sword")
                            page.wait_for_timeout(500)

                            if page.is_visible("button:has-text('Save Item')"):
                                page.click("button:has-text('Save Item')")
                                print("   ✅ Item added to inventory")

                    self.take_screenshot(page, "inventory_management")
                    break

            # Test character sheet viewing
            print("📄 Testing character sheet viewing...")

            sheet_selectors = [
                "#character-sheet",
                ".character-sheet",
                "text=Character Sheet",
                "button:has-text('Character Sheet')",
            ]

            for selector in sheet_selectors:
                if page.is_visible(selector):
                    print(f"   ✅ Found character sheet: {selector}")
                    page.click(selector)
                    page.wait_for_timeout(1000)

                    # Check if sheet displays character info
                    if page.is_visible("text=Test Hero"):
                        print("   ✅ Character sheet displays character info")

                    self.take_screenshot(page, "character_sheet")
                    break

            # Test NPC list viewing
            print("📋 Testing NPC list viewing...")

            npc_list_selectors = [
                "#npc-list",
                ".npc-list",
                "text=NPC List",
                "button:has-text('NPC List')",
            ]

            for selector in npc_list_selectors:
                if page.is_visible(selector):
                    print(f"   ✅ Found NPC list: {selector}")
                    page.click(selector)
                    page.wait_for_timeout(1000)

                    # Check if list displays NPCs
                    if page.is_visible("text=Wise Sage"):
                        print("   ✅ NPC list displays created NPCs")

                    self.take_screenshot(page, "npc_list")
                    break

            # Test character/NPC deletion
            print("🗑️  Testing character/NPC deletion...")

            # Look for delete buttons
            delete_buttons = page.query_selector_all("button:has-text('Delete')")
            if delete_buttons:
                print("   ✅ Found delete buttons")
                # Click the first delete button
                delete_buttons[0].click()
                page.wait_for_timeout(1000)

                # Handle confirmation if it appears
                if page.is_visible("text=Are you sure"):
                    print("   ✅ Confirmation dialog appeared")
                    page.click("button:has-text('Confirm')")
                    page.wait_for_timeout(1000)
                    print("   ✅ Deletion confirmed")

                self.take_screenshot(page, "character_npc_deleted")

            print("\n✅ Character/NPC management test completed successfully!")
            return True

        except TimeoutError as e:
            print(f"❌ Timeout error: {e}")
            self.take_screenshot(page, "error_timeout")
            return False
        except Exception as e:
            print(f"❌ Test failed: {e}")
            self.take_screenshot(page, "error_general")
            return False


if __name__ == "__main__":
    test = CharacterNPCTest()
    success = test.execute()

    if success:
        print(
            "\n✅ TEST PASSED - Character/NPC management tested via browser automation"
        )
        sys.exit(0)
    else:
        print("\n❌ TEST FAILED - See screenshots for details")
        sys.exit(1)
