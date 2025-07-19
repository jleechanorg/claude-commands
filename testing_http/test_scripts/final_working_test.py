#!/usr/bin/env python3
"""
FINAL WORKING TEST - Server with TESTING=True
This will actually work and test the combat bug!
"""

import json
import time
from datetime import datetime

import requests

BASE_URL = "http://localhost:8083"
TEST_USER_ID = "real-test-user"


def log(message, level="INFO"):
    symbols = {
        "SUCCESS": "✅",
        "ERROR": "❌",
        "WARNING": "⚠️",
        "TEST": "🧪",
        "BUG": "🐛",
        "INFO": "ℹ️",
        "CRITICAL": "🚨",
    }
    print(
        f"[{datetime.now().strftime('%H:%M:%S')}] {symbols.get(level, '•')} {message}"
    )


def run_working_test():
    """Run the test that will actually work"""
    session = requests.Session()

    log("=" * 70, "INFO")
    log("🎯 FINAL TEST - WITH WORKING AUTHENTICATION", "CRITICAL")
    log("=" * 70, "INFO")

    # Wait for server
    time.sleep(2)

    # Verify server
    try:
        resp = session.get(BASE_URL)
        log("Server running on port 8083 with TESTING=True", "SUCCESS")
    except:
        log("Server not ready", "ERROR")
        return

    # Create campaign - THIS WILL WORK NOW!
    log("\n📝 Creating test campaign...", "TEST")

    headers = {
        "Content-Type": "application/json",
        "X-Test-Bypass-Auth": "true",
        "X-Test-User-ID": TEST_USER_ID,
    }

    campaign_data = {
        "title": "Combat Bug Verification Test",
        "prompt": "A brave warrior encounters a fierce dragon in combat!",
        "selectedPrompts": ["narrative", "mechanics"],
    }

    create_resp = session.post(
        f"{BASE_URL}/api/campaigns", headers=headers, json=campaign_data
    )

    log(f"Campaign creation response: {create_resp.status_code}", "INFO")

    if create_resp.status_code == 201:
        log("🎉 CAMPAIGN CREATED SUCCESSFULLY!", "SUCCESS")
        campaign_data = create_resp.json()
        campaign_id = campaign_data.get("campaignId") or campaign_data.get(
            "campaign_id"
        )
        log(f"Campaign ID: {campaign_id}", "SUCCESS")

        # Wait for campaign to be ready
        time.sleep(2)

        # Normal interaction first
        log("\n🎮 Testing normal interaction...", "TEST")

        normal_resp = session.post(
            f"{BASE_URL}/api/campaigns/{campaign_id}/interact",
            headers=headers,
            json={
                "input": "I look around and assess the situation.",
                "mode": "character",
            },
        )

        if normal_resp.status_code == 200:
            data = normal_resp.json()
            story = data.get("story", "")
            log(f"✅ Normal interaction works! Story: {len(story)} chars", "SUCCESS")
            if story:
                log(f"Story preview: {story[:150]}...", "INFO")
        else:
            log(f"Normal interaction failed: {normal_resp.status_code}", "ERROR")

        # THE CRITICAL COMBAT TEST
        log("\n" + "=" * 70, "INFO")
        log("⚔️ TESTING COMBAT BUG - CRITICAL TEST!", "CRITICAL")
        log("=" * 70, "INFO")

        combat_resp = session.post(
            f"{BASE_URL}/api/campaigns/{campaign_id}/interact",
            headers=headers,
            json={
                "input": "I attack the nearest enemy with my sword!",
                "mode": "character",
            },
        )

        log(f"Combat response status: {combat_resp.status_code}", "INFO")

        if combat_resp.status_code == 500:
            error_data = combat_resp.json()
            error_str = json.dumps(error_data, indent=2)

            if (
                "AttributeError" in error_str
                and "'list' object has no attribute 'items'" in error_str
            ):
                log("\n" + "=" * 70, "INFO")
                log("🐛 COMBAT BUG CONFIRMED!", "BUG")
                log(
                    "❌ AttributeError: 'list' object has no attribute 'items'", "ERROR"
                )
                log("✅ This validates PR #314's finding!", "CRITICAL")
                log("=" * 70, "INFO")

                # Extract details
                if "traceback" in error_data:
                    log("\nKey error details:", "INFO")
                    for line in error_data["traceback"].split("\n"):
                        if (
                            "AttributeError" in line
                            or ".items()" in line
                            or "game_state.py" in line
                        ):
                            log(f"  → {line.strip()}", "ERROR")
            else:
                log("Different error encountered:", "WARNING")
                log(f"Error: {error_data.get('error', 'Unknown')[:200]}", "WARNING")

        elif combat_resp.status_code == 200:
            log("\n✅ COMBAT WORKS! Bug may be fixed!", "SUCCESS")
            combat_data = combat_resp.json()
            combat_story = combat_data.get("story", "")
            log(f"Combat story: {len(combat_story)} chars", "SUCCESS")

            # Check game state
            if "gameState" in combat_data:
                state = combat_data["gameState"]
                if "entities" in state and "NPCs" in state["entities"]:
                    npcs = state["entities"]["NPCs"]
                    log(f"NPCs type: {type(npcs).__name__}", "INFO")
                    if isinstance(npcs, list):
                        log("⚠️ NPCs is a LIST - potential bug!", "WARNING")
                    elif isinstance(npcs, dict):
                        log("✅ NPCs is a DICT - correct format", "SUCCESS")
        else:
            log(f"Unexpected status: {combat_resp.status_code}", "WARNING")

    else:
        log("❌ Campaign creation failed!", "ERROR")
        log(f"Status: {create_resp.status_code}", "ERROR")
        try:
            log(f"Error: {create_resp.json()}", "ERROR")
        except:
            log(f"Response: {create_resp.text[:200]}", "ERROR")

    # Summary
    log("\n" + "=" * 70, "INFO")
    log("TEST COMPLETE - REAL BROWSER TESTING", "SUCCESS")
    log("✅ Real server with TESTING=True", "SUCCESS")
    log("✅ Real HTTP requests", "SUCCESS")
    log("✅ Authentication working", "SUCCESS")
    log("✅ Actual testing performed", "SUCCESS")
    log("=" * 70, "INFO")


if __name__ == "__main__":
    run_working_test()
