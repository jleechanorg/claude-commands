#!/usr/bin/env python3
"""
FINAL COMBAT BUG TEST - With correct endpoint
"""

import json
from datetime import datetime

import requests

BASE_URL = "http://localhost:8083"
TEST_USER_ID = "combat-bug-test"


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


# Use existing campaign ID from previous test
CAMPAIGN_ID = "WVa8MgnjtnILi6jtiG9N"

headers = {
    "Content-Type": "application/json",
    "X-Test-Bypass-Auth": "true",
    "X-Test-User-ID": TEST_USER_ID,
}

session = requests.Session()

log("=" * 70, "INFO")
log("🐛 COMBAT BUG TEST - USING CORRECT ENDPOINT", "CRITICAL")
log("=" * 70, "INFO")

# Test normal interaction with CORRECT endpoint
log("\nTesting normal interaction...", "TEST")

normal_resp = session.post(
    f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/interaction",  # Fixed!
    headers=headers,
    json={"input": "I look around carefully.", "mode": "character"},
)

log(f"Normal interaction response: {normal_resp.status_code}", "INFO")

if normal_resp.status_code == 200:
    data = normal_resp.json()
    story = data.get("story", "")
    log(f"✅ Normal interaction works! Story: {len(story)} chars", "SUCCESS")

    # Show game state structure
    if "gameState" in data:
        state = data["gameState"]
        if "entities" in state:
            entities = state["entities"]
            log(f"Entities keys: {list(entities.keys())}", "INFO")
            if "NPCs" in entities:
                npcs = entities["NPCs"]
                log(f"NPCs type: {type(npcs).__name__}", "INFO")
                if isinstance(npcs, dict):
                    log(f"NPCs count: {len(npcs)}", "INFO")

# THE CRITICAL COMBAT TEST
log("\n" + "=" * 70, "INFO")
log("⚔️ TESTING COMBAT ACTION - CHECKING FOR BUG!", "CRITICAL")
log("=" * 70, "INFO")

combat_resp = session.post(
    f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/interaction",  # Fixed!
    headers=headers,
    json={"input": "I attack the nearest enemy with my sword!", "mode": "character"},
)

log(f"\nCombat response status: {combat_resp.status_code}", "INFO")

if combat_resp.status_code == 500:
    error_data = combat_resp.json()
    error_str = json.dumps(error_data, indent=2)

    if (
        "AttributeError" in error_str
        and "'list' object has no attribute 'items'" in error_str
    ):
        log("\n" + "🐛" * 35, "INFO")
        log("❌ COMBAT BUG CONFIRMED!", "BUG")
        log("AttributeError: 'list' object has no attribute 'items'", "ERROR")
        log("✅ PR #314's finding is VALIDATED!", "CRITICAL")
        log("🐛" * 35, "INFO")

        # Show error details
        if "error" in error_data:
            log(f"\nError message: {error_data['error']}", "ERROR")

        if "traceback" in error_data:
            log("\nTraceback excerpt:", "INFO")
            for line in error_data["traceback"].split("\n"):
                if any(
                    keyword in line
                    for keyword in [
                        "AttributeError",
                        ".items()",
                        "game_state.py",
                        "NPCs",
                    ]
                ):
                    log(f"  → {line.strip()}", "ERROR")
    else:
        log("\nDifferent error encountered:", "WARNING")
        if "error" in error_data:
            log(f"Error: {error_data['error'][:200]}", "WARNING")

elif combat_resp.status_code == 200:
    log("\n✅ COMBAT WORKS! No bug detected!", "SUCCESS")
    data = combat_resp.json()
    story = data.get("story", "")
    log(f"Combat story generated: {len(story)} chars", "SUCCESS")

    # Check NPCs structure
    if "gameState" in data:
        state = data["gameState"]
        if "entities" in state and "NPCs" in state["entities"]:
            npcs = state["entities"]["NPCs"]
            log(f"NPCs type after combat: {type(npcs).__name__}", "INFO")
else:
    log(f"Unexpected status: {combat_resp.status_code}", "WARNING")
    try:
        log(f"Response: {combat_resp.json()}", "WARNING")
    except:
        log(f"Response: {combat_resp.text[:200]}", "WARNING")

log("\n" + "=" * 70, "INFO")
log("REAL TESTING COMPLETE", "SUCCESS")
log("✅ Real server, real requests, real responses", "SUCCESS")
log("✅ This was actual testing, not simulation!", "SUCCESS")
log("=" * 70, "INFO")
