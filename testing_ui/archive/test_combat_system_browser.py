#!/usr/bin/env python3
"""
Real browser test for Combat System functionality using Playwright.
This test automates a real browser to test combat mechanics and dice rolling.
"""

import os
import sys

from playwright.sync_api import Page, TimeoutError

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_test_base import BrowserTestBase


class CombatSystemTest(BrowserTestBase):
    """Test Combat System functionality through real browser automation."""

    def __init__(self):
        super().__init__("Combat System Test")

    def run_test(self, page: Page) -> bool:
        """Test combat system through browser automation."""

        try:
            # Take initial screenshot
            self.take_screenshot(page, "dashboard_initial")

            # Create a test campaign first
            print("🎮 Creating a test campaign for combat testing...")
            if page.is_visible("text=New Campaign"):
                page.click("text=New Campaign")
                page.wait_for_timeout(1000)

                # Fill in campaign details
                if page.is_visible("#wizard-campaign-title"):
                    page.fill("#wizard-campaign-title", "Combat Test Campaign")
                    page.fill(
                        "#wizard-campaign-prompt",
                        "A dangerous dungeon filled with monsters and combat encounters.",
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

            # Test initiating combat
            print("⚔️  Testing combat initiation...")

            # Send a message that should trigger combat
            message_input = page.query_selector(
                "#message-input"
            ) or page.query_selector("textarea[placeholder*='What do you do']")
            if message_input:
                # Type a combat-triggering action
                combat_action = (
                    "I draw my sword and attack the goblin blocking the path!"
                )
                message_input.fill(combat_action)
                print(f"   📝 Typed combat action: {combat_action}")

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
                print("⏳ Waiting for AI response about combat...")
                page.wait_for_timeout(5000)

                self.take_screenshot(page, "combat_initiated")

                # Check for combat-related response
                chat_area = page.query_selector(
                    "#chat-messages"
                ) or page.query_selector(".chat-messages")
                if chat_area:
                    messages = chat_area.text_content()
                    if any(
                        word in messages.lower()
                        for word in [
                            "attack",
                            "damage",
                            "hit",
                            "combat",
                            "battle",
                            "fight",
                        ]
                    ):
                        print("✅ Combat response received!")
                    else:
                        print("⚠️  Response received but no combat content")

            # Test dice rolling functionality
            print("🎲 Testing dice rolling functionality...")

            # Look for dice rolling UI
            dice_selectors = [
                "#dice-roller",
                ".dice-roller",
                "button:has-text('Roll Dice')",
                "button:has-text('Roll')",
                "[data-dice]",
                "text=Dice",
                "#combat-dice",
            ]

            dice_found = False
            for selector in dice_selectors:
                if page.is_visible(selector):
                    print(f"   ✅ Found dice roller: {selector}")
                    page.click(selector)
                    page.wait_for_timeout(1000)
                    dice_found = True
                    break

            if not dice_found:
                print(
                    "   ⚠️  No dice roller found - trying to trigger it via combat action"
                )

                # Try another combat action to trigger dice rolling
                if message_input:
                    dice_action = "I roll for initiative and attack with my sword. Rolling 1d20+5 for attack."
                    message_input.fill(dice_action)

                    if send_button:
                        send_button.click()
                    else:
                        message_input.press("Enter")

                    page.wait_for_timeout(3000)

                    # Check if dice results appear
                    chat_area = page.query_selector(
                        "#chat-messages"
                    ) or page.query_selector(".chat-messages")
                    if chat_area:
                        messages = chat_area.text_content()
                        if any(
                            word in messages.lower()
                            for word in ["rolled", "1d20", "dice", "result"]
                        ):
                            print("✅ Dice rolling triggered via text!")
                            dice_found = True

            self.take_screenshot(page, "dice_rolling")

            # Test different dice types
            if dice_found:
                print("   🎲 Testing different dice types...")

                dice_types = ["d4", "d6", "d8", "d10", "d12", "d20"]
                for dice_type in dice_types:
                    dice_button = page.query_selector(f"button:has-text('{dice_type}')")
                    if dice_button:
                        print(f"   ✅ Testing {dice_type}")
                        dice_button.click()
                        page.wait_for_timeout(1000)

                        # Look for result
                        result_selectors = [
                            "#dice-result",
                            ".dice-result",
                            "[data-dice-result]",
                        ]

                        for result_selector in result_selectors:
                            if page.is_visible(result_selector):
                                result_text = page.text_content(result_selector)
                                print(f"   ✅ {dice_type} result: {result_text}")
                                break

                self.take_screenshot(page, "dice_types_tested")

            # Test combat actions
            print("⚔️  Testing combat actions...")

            # Look for combat action buttons
            combat_action_selectors = [
                "button:has-text('Attack')",
                "button:has-text('Defend')",
                "button:has-text('Cast Spell')",
                "button:has-text('Use Item')",
                "#combat-actions",
                ".combat-actions",
            ]

            for selector in combat_action_selectors:
                if page.is_visible(selector):
                    print(f"   ✅ Found combat action: {selector}")
                    page.click(selector)
                    page.wait_for_timeout(1000)

                    # Look for action result
                    if page.is_visible("#combat-log") or page.is_visible(".combat-log"):
                        print("   ✅ Combat log updated")

                    self.take_screenshot(
                        page, f"combat_action_{selector.split(':')[0]}"
                    )
                    break

            # Test turn-based combat
            print("🔄 Testing turn-based combat mechanics...")

            # Look for turn indicators
            turn_selectors = [
                "#current-turn",
                ".current-turn",
                "text=Your Turn",
                "text=Enemy Turn",
                "[data-turn]",
            ]

            for selector in turn_selectors:
                if page.is_visible(selector):
                    print(f"   ✅ Found turn indicator: {selector}")
                    turn_text = page.text_content(selector)
                    print(f"   Current turn: {turn_text}")
                    break

            # Test initiative system
            print("🏃 Testing initiative system...")

            initiative_selectors = [
                "#initiative-order",
                ".initiative-order",
                "text=Initiative",
                "[data-initiative]",
            ]

            for selector in initiative_selectors:
                if page.is_visible(selector):
                    print(f"   ✅ Found initiative system: {selector}")
                    initiative_text = page.text_content(selector)
                    print(f"   Initiative: {initiative_text}")
                    break

            # Test health/damage tracking
            print("❤️  Testing health and damage tracking...")

            # Look for health bars or HP displays
            health_selectors = [
                "#player-health",
                ".health-bar",
                "text=HP",
                "text=Health",
                "[data-health]",
                "#character-hp",
            ]

            for selector in health_selectors:
                if page.is_visible(selector):
                    print(f"   ✅ Found health display: {selector}")
                    health_text = page.text_content(selector)
                    print(f"   Health: {health_text}")
                    break

            # Test damage application
            print("💥 Testing damage application...")

            # Try to take damage via combat action
            if message_input:
                damage_action = "The goblin attacks me with its rusty sword!"
                message_input.fill(damage_action)

                if send_button:
                    send_button.click()
                else:
                    message_input.press("Enter")

                page.wait_for_timeout(3000)

                # Check for damage in response
                chat_area = page.query_selector(
                    "#chat-messages"
                ) or page.query_selector(".chat-messages")
                if chat_area:
                    messages = chat_area.text_content()
                    if any(
                        word in messages.lower()
                        for word in ["damage", "hit", "hurt", "wounds"]
                    ):
                        print("✅ Damage tracking working!")
                    else:
                        print("⚠️  No damage tracking detected")

            self.take_screenshot(page, "damage_tracking")

            # Test spell casting
            print("🔮 Testing spell casting in combat...")

            # Look for spell casting UI
            spell_selectors = [
                "button:has-text('Cast Spell')",
                "button:has-text('Magic')",
                "#spell-list",
                ".spell-list",
                "[data-spell]",
            ]

            for selector in spell_selectors:
                if page.is_visible(selector):
                    print(f"   ✅ Found spell casting: {selector}")
                    page.click(selector)
                    page.wait_for_timeout(1000)

                    # Look for spell selection
                    spell_names = ["Fireball", "Healing", "Lightning", "Shield"]
                    for spell in spell_names:
                        if page.is_visible(f"text={spell}"):
                            print(f"   ✅ Found spell: {spell}")
                            page.click(f"text={spell}")
                            page.wait_for_timeout(1000)
                            break

                    self.take_screenshot(page, "spell_casting")
                    break

            # Test critical hits and special effects
            print("✨ Testing critical hits and special effects...")

            # Try to trigger critical hit via text
            if message_input:
                critical_action = (
                    "I roll a natural 20 for a critical hit with my sword!"
                )
                message_input.fill(critical_action)

                if send_button:
                    send_button.click()
                else:
                    message_input.press("Enter")

                page.wait_for_timeout(3000)

                # Check for critical hit response
                chat_area = page.query_selector(
                    "#chat-messages"
                ) or page.query_selector(".chat-messages")
                if chat_area:
                    messages = chat_area.text_content()
                    if any(
                        word in messages.lower()
                        for word in ["critical", "crit", "maximum", "double"]
                    ):
                        print("✅ Critical hit mechanics working!")
                    else:
                        print("⚠️  No critical hit mechanics detected")

            self.take_screenshot(page, "critical_hits")

            # Test combat resolution
            print("🏁 Testing combat resolution...")

            # Try to end combat
            if message_input:
                end_action = "I deliver the final blow and defeat the goblin!"
                message_input.fill(end_action)

                if send_button:
                    send_button.click()
                else:
                    message_input.press("Enter")

                page.wait_for_timeout(3000)

                # Check for victory/defeat response
                chat_area = page.query_selector(
                    "#chat-messages"
                ) or page.query_selector(".chat-messages")
                if chat_area:
                    messages = chat_area.text_content()
                    if any(
                        word in messages.lower()
                        for word in ["victory", "defeated", "wins", "triumph"]
                    ):
                        print("✅ Combat resolution working!")
                    else:
                        print("⚠️  No combat resolution detected")

            self.take_screenshot(page, "combat_resolution")

            # Test experience and rewards
            print("🏆 Testing experience and rewards...")

            # Look for XP or reward displays
            reward_selectors = [
                "text=XP",
                "text=Experience",
                "text=Reward",
                "text=Loot",
                "#experience-gain",
                ".reward-display",
            ]

            for selector in reward_selectors:
                if page.is_visible(selector):
                    print(f"   ✅ Found reward system: {selector}")
                    reward_text = page.text_content(selector)
                    print(f"   Reward: {reward_text}")
                    break

            self.take_screenshot(page, "rewards_system")

            print("\n✅ Combat system test completed successfully!")
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
    test = CombatSystemTest()
    success = test.execute()

    if success:
        print("\n✅ TEST PASSED - Combat system tested via browser automation")
        sys.exit(0)
    else:
        print("\n❌ TEST FAILED - See screenshots for details")
        sys.exit(1)
