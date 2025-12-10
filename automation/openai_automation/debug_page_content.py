#!/usr/bin/env python3
"""
Debug script to check what's actually on the Codex page when connected via CDP.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from codex_github_mentions import CodexGitHubMentionsAutomation


async def debug_page():
    """Connect to Chrome and inspect the actual page content."""
    automation = CodexGitHubMentionsAutomation()

    # Connect to existing browser
    if not await automation.connect_to_existing_browser():
        print("❌ Failed to connect")
        return

    # Navigate to Codex
    await automation.navigate_to_codex()

    # Wait extra time for dynamic content
    print("\n⏳ Waiting 10 seconds for page to fully load...")
    await asyncio.sleep(10)

    # Get page title
    title = await automation.page.title()
    print(f"\n📄 Page title: {title}")

    # Get current URL
    url = automation.page.url
    print(f"🔗 Current URL: {url}")

    # Try multiple selectors
    print("\n🔍 Testing different selectors:")

    selectors = [
        'a[href*="/codex/"]',
        'a:has-text("Github Mention:")',
        'a[href^="https://chatgpt.com/codex/"]',
        '[role="link"]',
        'a',
        'div[role="article"]',
        'article',
    ]

    for selector in selectors:
        try:
            elements = await automation.page.locator(selector).all()
            print(f"  {selector}: {len(elements)} elements")
            if len(elements) > 0 and len(elements) < 20:
                # Show text content of first few
                for i, elem in enumerate(elements[:3]):
                    try:
                        text = await elem.text_content()
                        preview = text[:80] if text else "(no text)"
                        print(f"    [{i}]: {preview}")
                    except:
                        pass
        except Exception as e:
            print(f"  {selector}: Error - {e}")

    # Get page HTML (first 2000 chars)
    html = await automation.page.content()
    print(f"\n📝 Page HTML (first 2000 chars):")
    print(html[:2000])

    # Take screenshot
    screenshot_path = "/tmp/automate_codex_update/debug_screenshot.png"
    Path("/tmp/automate_codex_update").mkdir(parents=True, exist_ok=True)
    await automation.page.screenshot(path=screenshot_path)
    print(f"\n📸 Screenshot saved to: {screenshot_path}")


if __name__ == "__main__":
    asyncio.run(debug_page())
