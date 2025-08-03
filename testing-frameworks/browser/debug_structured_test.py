#!/usr/bin/env python3
"""
Simple test to load a campaign and check console for structured fields debug logs.
"""
import os
import sys

sys.path.append('/home/jleechan/projects/worldarchitect.ai/worktree_human2')

import json
import signal
import subprocess
import time

from playwright.sync_api import sync_playwright


def main():
    # Start server
    print("🚀 Starting test server...")
    server = subprocess.Popen([
        'python', '/home/jleechan/projects/worldarchitect.ai/worktree_human2/mvp_site/main.py', 'serve'
    ], env={**os.environ, 'TESTING': 'true', 'PORT': '8088'})

    time.sleep(3)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()

            # Capture console logs
            console_logs = []
            page.on("console", lambda msg: console_logs.append(f"{msg.type}: {msg.text}"))

            # Navigate to test mode
            print("🌐 Loading campaign page...")
            page.goto("http://localhost:8088?test_mode=true&test_user_id=test-user-123", wait_until="networkidle")

            # Wait a bit for initial load
            time.sleep(2)

            # Create a fresh campaign to ensure we get a Gemini response
            print("📝 Creating fresh campaign...")
            page.goto("http://localhost:8088/wizard?test_mode=true&test_user_id=test-user-123")
            time.sleep(1)

            # Fill minimal campaign details
            page.fill('input[name="title"]', 'Debug Test Campaign')
            page.fill('input[name="character"]', 'Debug Tester')
            page.click('button:has-text("Next")')
            time.sleep(1)
            page.click('button:has-text("Next")')
            time.sleep(1)
            page.click('button:has-text("Begin")')

            # Wait for campaign page to load
            time.sleep(3)

            print("🔍 Checking console logs for structured fields...")
            for log in console_logs:
                if any(keyword in log.lower() for keyword in ['dice_rolls', 'resources', 'structured', 'planning']):
                    print(f"  📋 {log}")

            print(f"\n📊 Total console messages: {len(console_logs)}")

            # Take screenshot
            page.screenshot(path="/tmp/worldarchitectai/debug_structured_fields.png")
            print("📸 Screenshot saved: /tmp/worldarchitectai/debug_structured_fields.png")

        except Exception as e:
            print(f"❌ Error during test: {e}")

            browser.close()

    finally:
        print("🛑 Stopping server...")
        server.terminate()
        server.wait()

if __name__ == "__main__":
    main()
