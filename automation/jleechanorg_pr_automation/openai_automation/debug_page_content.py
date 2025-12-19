#!/usr/bin/env python3
"""
Debug script to check what's actually on the Codex page when connected via CDP.
"""
import asyncio
import os
import tempfile
from pathlib import Path

from jleechanorg_pr_automation.openai_automation.codex_github_mentions import (
    CodexGitHubMentionsAutomation,
)


async def debug_page():
    """Connect to Chrome and inspect the actual page content."""
    automation = CodexGitHubMentionsAutomation(cdp_url="http://127.0.0.1:9222", all_tasks=True)

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
        'a:has-text("GitHub Mention:")',
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
            if 0 < len(elements) < 20:
                for i, elem in enumerate(elements[:3]):
                    try:
                        text = await elem.text_content()
                        preview = text[:80] if text else "(no text)"
                        print(f"    [{i}]: {preview}")
                    except Exception as inner_err:
                        print(f"    [{i}]: error reading text_content: {inner_err!r}")
        except Exception as e:
            print(f"  {selector}: Error - {e}")

    # Get page HTML (first 2000 chars)
    html = await automation.page.content()
    print(f"\n📝 Page HTML (first 2000 chars):")
    print(html[:2000])

    # Take screenshot using a secure temp file
    base_dir = Path("/tmp/automate_codex_update")
    base_dir.mkdir(parents=True, exist_ok=True)
    fd, screenshot_path = tempfile.mkstemp(prefix="debug_screenshot_", suffix=".png", dir=str(base_dir))
    await automation.page.screenshot(path=screenshot_path)
    try:
        os.close(fd)
    except OSError:
        # Debug script: safe to ignore close errors on temp fd
        pass
    print(f"\n📸 Screenshot saved to: {screenshot_path}")

    await automation.cleanup()


if __name__ == "__main__":
    asyncio.run(debug_page())
