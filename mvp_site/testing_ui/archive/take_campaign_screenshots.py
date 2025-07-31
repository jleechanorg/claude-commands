#!/usr/bin/env python3
"""Take screenshots of the campaign wizard in headless mode."""

from playwright.sync_api import sync_playwright


def take_campaign_screenshots():
    """Take screenshots of all 3 steps of the campaign wizard."""

    with sync_playwright() as p:
        # Launch browser in headless mode
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1200, "height": 800})

        # Navigate to the app
        print("Navigating to app...")
        page.goto("http://localhost:3001/v2/?test_mode=true&test_user_id=test-123")
        page.wait_for_load_state("networkidle")

        # Click on Create Your First Campaign
        print("Clicking Create Campaign button...")
        page.click('button:has-text("Create Your First Campaign")')
        page.wait_for_timeout(1000)

        # Click on Create V2 Campaign
        print("Clicking Create V2 Campaign...")
        page.click('button:has-text("Create V2 Campaign")')
        page.wait_for_timeout(1500)

        # Take screenshot of Step 1
        print("Taking screenshot of Step 1 - Basics...")
        page.screenshot(path="campaign-wizard-step1-basics.png", full_page=True)

        # Click Next to go to Step 2
        print("Going to Step 2...")
        page.click('button:has-text("Next")')
        page.wait_for_timeout(1500)

        # Take screenshot of Step 2
        print("Taking screenshot of Step 2 - AI Style...")
        page.screenshot(path="campaign-wizard-step2-ai-style.png", full_page=True)

        # Click Next to go to Step 3
        print("Going to Step 3...")
        page.click('button:has-text("Next")')
        page.wait_for_timeout(1500)

        # Take screenshot of Step 3
        print("Taking screenshot of Step 3 - Launch...")
        page.screenshot(path="campaign-wizard-step3-launch.png", full_page=True)

        browser.close()
        print("Screenshots saved!")


if __name__ == "__main__":
    take_campaign_screenshots()
