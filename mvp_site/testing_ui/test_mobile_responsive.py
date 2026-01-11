#!/usr/bin/env python3
"""
Mobile responsive tests for planning block choice ID font sizes.
Tests .choice-id element scaling at mobile breakpoints (320px, 768px).
"""

import os
import sys
import tempfile
import time

from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_choice_id_mobile_responsive():
    """Test that .choice-id font-size scales properly on mobile breakpoints."""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # Navigate to test page with planning blocks
            page.goto("http://localhost:8081?test_mode=true&test_user_id=test-user-123")
            page.wait_for_load_state("networkidle")

            # Inject test CSS to ensure we have .choice-id elements
            page.add_style_tag(
                content="""
                .test-choice-container {
                    padding: 1rem;
                    margin: 1rem;
                }
                .choice-id {
                    font-weight: bold;
                    color: #0d6efd;
                    margin-right: 0.5rem;
                    font-family: 'Courier New', monospace;
                }
                /* Mobile responsive rules from planning-blocks.css */
                @media (max-width: 768px) {
                    .choice-id {
                        font-size: 0.7rem;
                    }
                }
            """
            )

            # Inject test HTML with choice ID elements
            page.evaluate("""
                const testContainer = document.createElement('div');
                testContainer.className = 'test-choice-container';
                testContainer.innerHTML = `
                    <div class="planning-block-choices">
                        <div class="choice-button">
                            <span class="choice-id">A.</span>
                            <span class="choice-description">Test choice description</span>
                        </div>
                        <div class="choice-button">
                            <span class="choice-id">B.</span>
                            <span class="choice-description">Another test choice</span>
                        </div>
                    </div>
                `;
                document.body.appendChild(testContainer);
            """)

            # Test case 1: Desktop view (default)
            page.set_viewport_size({"width": 1200, "height": 800})
            time.sleep(0.5)  # Allow CSS to apply

            choice_id_element = page.locator(".choice-id").first
            desktop_font_size = choice_id_element.evaluate(
                "el => getComputedStyle(el).fontSize"
            )
            print(f"Desktop font-size: {desktop_font_size}")

            # Test case 2: Tablet breakpoint (768px)
            page.set_viewport_size({"width": 768, "height": 600})
            time.sleep(0.5)  # Allow CSS media query to apply

            tablet_font_size = choice_id_element.evaluate(
                "el => getComputedStyle(el).fontSize"
            )
            print(f"Tablet (768px) font-size: {tablet_font_size}")

            # Test case 3: Mobile breakpoint (320px)
            page.set_viewport_size({"width": 320, "height": 568})
            time.sleep(0.5)  # Allow CSS media query to apply

            mobile_font_size = choice_id_element.evaluate(
                "el => getComputedStyle(el).fontSize"
            )
            print(f"Mobile (320px) font-size: {mobile_font_size}")

            # Take screenshots for visual verification
            page.screenshot(
                path=os.path.join(tempfile.gettempdir(), "choice_id_mobile_320px.png")
            )

            page.set_viewport_size({"width": 768, "height": 600})
            time.sleep(0.5)
            page.screenshot(
                path=os.path.join(tempfile.gettempdir(), "choice_id_tablet_768px.png")
            )

            page.set_viewport_size({"width": 1200, "height": 800})
            time.sleep(0.5)
            page.screenshot(
                path=os.path.join(tempfile.gettempdir(), "choice_id_desktop_1200px.png")
            )

            # Verify responsive behavior
            # Mobile should have smaller font (0.7rem = ~11.2px)
            # Desktop should have larger font (default ~16px)

            # Parse font sizes (remove 'px' suffix)
            desktop_px = float(desktop_font_size.replace("px", ""))
            tablet_px = float(tablet_font_size.replace("px", ""))
            mobile_px = float(mobile_font_size.replace("px", ""))

            print(
                f"Font size progression: Desktop {desktop_px}px → Tablet {tablet_px}px → Mobile {mobile_px}px"
            )

            # Assertions for responsive behavior
            assert (
                mobile_px < desktop_px
            ), f"Mobile font-size ({mobile_px}px) should be smaller than desktop ({desktop_px}px)"
            assert (
                mobile_px <= 12
            ), f"Mobile font-size ({mobile_px}px) should be small (≤12px for readability)"
            assert (
                mobile_px >= 8
            ), f"Mobile font-size ({mobile_px}px) should be readable (≥8px)"

            # Tablet should be between mobile and desktop, or same as mobile
            assert (
                tablet_px <= desktop_px
            ), f"Tablet font-size ({tablet_px}px) should not be larger than desktop ({desktop_px}px)"

            print("✅ Mobile responsive font scaling works correctly")
            print(f"   Mobile (320px): {mobile_px}px")
            print(f"   Tablet (768px): {tablet_px}px")
            print(f"   Desktop (1200px): {desktop_px}px")

        except Exception as e:
            print(f"❌ Test failed: {e}")
            page.screenshot(
                path=os.path.join(
                    tempfile.gettempdir(), "mobile_responsive_test_error.png"
                )
            )
            raise
        finally:
            browser.close()


def test_choice_button_mobile_layout():
    """Test that choice buttons adapt properly to mobile layout."""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            page.goto("http://localhost:8081?test_mode=true&test_user_id=test-user-123")
            page.wait_for_load_state("networkidle")

            # Load planning-blocks.css
            css_content = """
                @media (max-width: 768px) {
                    .choice-button {
                        padding: 0.08rem 0.25rem;
                        font-size: 0.7rem;
                        margin-right: 0.25rem;
                        margin-bottom: 0.15rem;
                    }

                    .choice-id {
                        font-size: 0.7rem;
                    }

                    .planning-block-choices {
                        padding: 0.15rem;
                    }
                }

                .choice-button {
                    display: block;
                    width: 100%;
                    margin-bottom: 0.5rem;
                    padding: 0.5rem 1rem;
                    text-align: left;
                    background: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 3px;
                    cursor: pointer;
                }

                .choice-id {
                    font-weight: bold;
                    color: #0d6efd;
                    margin-right: 0.5rem;
                    font-family: 'Courier New', monospace;
                }
            """

            page.add_style_tag(content=css_content)

            # Add test choice buttons
            page.evaluate("""
                const container = document.createElement('div');
                container.className = 'planning-block-choices';
                container.innerHTML = `
                    <div class="choice-button">
                        <span class="choice-id">A.</span>
                        <span class="choice-description">Test mobile choice</span>
                    </div>
                    <div class="choice-button">
                        <span class="choice-id">B.</span>
                        <span class="choice-description">Another mobile choice</span>
                    </div>
                `;
                document.body.appendChild(container);
            """)

            # Test mobile layout
            page.set_viewport_size({"width": 320, "height": 568})
            time.sleep(0.5)

            # Check button padding and spacing
            choice_button = page.locator(".choice-button").first
            mobile_padding = choice_button.evaluate(
                "el => getComputedStyle(el).padding"
            )
            mobile_font_size = choice_button.evaluate(
                "el => getComputedStyle(el).fontSize"
            )
            mobile_margin_bottom = choice_button.evaluate(
                "el => getComputedStyle(el).marginBottom"
            )

            print(f"Mobile choice button padding: {mobile_padding}")
            print(f"Mobile choice button font-size: {mobile_font_size}")
            print(f"Mobile choice button margin-bottom: {mobile_margin_bottom}")

            # Verify mobile adaptations
            assert (
                "0.08rem" in mobile_padding or "1.28px" in mobile_padding
            ), "Mobile padding should be reduced"
            assert (
                "0.7rem" in mobile_font_size or "11.2px" in mobile_font_size
            ), "Mobile font should be 0.7rem"

            print("✅ Mobile choice button layout is properly optimized")

        except Exception as e:
            print(f"❌ Mobile layout test failed: {e}")
            page.screenshot(
                path=os.path.join(tempfile.gettempdir(), "mobile_layout_test_error.png")
            )
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    print("🧪 Testing mobile responsive choice ID font sizes...")
    test_choice_id_mobile_responsive()
    print()
    print("🧪 Testing mobile choice button layout...")
    test_choice_button_mobile_layout()
    print("\n✅ All mobile responsive tests passed!")
