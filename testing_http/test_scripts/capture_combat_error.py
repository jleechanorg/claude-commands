#!/usr/bin/env python3
"""
Comprehensive test to capture the combat AttributeError with full details
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8086"  # Monitored server
TEST_USER_ID = "combat-error-test"

def log(msg, level="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] {level}: {msg}")

log("🔍 COMBAT ERROR CAPTURE TEST", "CRITICAL")
log("=" * 70)

# Wait for server
time.sleep(2)

headers = {
    "Content-Type": "application/json",
    "X-Test-Bypass-Auth": "true",
    "X-Test-User-ID": TEST_USER_ID
}

# Step 1: Create campaign
log("\n1️⃣ Creating campaign with combat scenario...")
campaign_resp = requests.post(
    f"{BASE_URL}/api/campaigns",
    headers=headers,
    json={
        "title": "Combat Error Capture Test",
        "prompt": "A mighty warrior faces a deadly dragon in combat. The dragon roars and prepares to attack!",
        "selectedPrompts": ["narrative", "mechanics"]
    }
)

if campaign_resp.status_code != 201:
    log(f"Campaign creation failed: {campaign_resp.status_code}", "ERROR")
    log(f"Response: {campaign_resp.text[:500]}", "ERROR")
    exit(1)

campaign_data = campaign_resp.json()
campaign_id = campaign_data.get("campaignId") or campaign_data.get("campaign_id")
log(f"✅ Campaign created: {campaign_id}", "SUCCESS")

# Step 2: Normal interaction first
log("\n2️⃣ Testing normal interaction first...")
normal_resp = requests.post(
    f"{BASE_URL}/api/campaigns/{campaign_id}/interaction",
    headers=headers,
    json={
        "input": "I look around and assess the situation.",
        "mode": "character"
    }
)

if normal_resp.status_code == 200:
    log("✅ Normal interaction successful", "SUCCESS")
    data = normal_resp.json()
    if "gameState" in data and "entities" in data["gameState"]:
        entities = data["gameState"]["entities"]
        if "NPCs" in entities:
            npcs = entities["NPCs"]
            log(f"NPCs data type: {type(npcs).__name__}", "DEBUG")
            if isinstance(npcs, dict):
                log(f"NPCs entries: {list(npcs.keys())}", "DEBUG")
            elif isinstance(npcs, list):
                log(f"NPCs list length: {len(npcs)}", "DEBUG")

# Step 3: Combat interaction to trigger error
log("\n3️⃣ TRIGGERING COMBAT - EXPECTING ATTRIBUTEERROR...")
log("=" * 70, "CRITICAL")

combat_inputs = [
    "I attack the dragon with my sword!",
    "I cast fireball at the dragon!",
    "I charge into combat!"
]

for i, combat_input in enumerate(combat_inputs, 1):
    log(f"\nCombat attempt {i}: '{combat_input}'")
    
    combat_resp = requests.post(
        f"{BASE_URL}/api/campaigns/{campaign_id}/interaction",
        headers=headers,
        json={
            "input": combat_input,
            "mode": "character"
        }
    )
    
    log(f"Response status: {combat_resp.status_code}")
    
    if combat_resp.status_code == 500:
        try:
            error_data = combat_resp.json()
            
            # Check if it's the AttributeError we're looking for
            if "AttributeError" in str(error_data) and "'list' object has no attribute 'items'" in str(error_data):
                log("\n🐛 COMBAT BUG CONFIRMED!", "CRITICAL")
                log("=" * 70)
                
                # Extract key information
                log(f"\nError Type: {error_data.get('error_type', 'Unknown')}", "ERROR")
                log(f"Error Message: {error_data.get('error', 'Unknown')}", "ERROR")
                log(f"Error ID: {error_data.get('error_id', 'Unknown')}", "ERROR")
                
                # Extract traceback details
                if "traceback" in error_data:
                    log("\n📍 TRACEBACK ANALYSIS:", "CRITICAL")
                    traceback_lines = error_data["traceback"].split("\n")
                    
                    # Find the exact line causing the error
                    for j, line in enumerate(traceback_lines):
                        if "AttributeError" in line:
                            # Show context around the error
                            start = max(0, j - 5)
                            end = min(len(traceback_lines), j + 3)
                            
                            log("\n🔴 ERROR CONTEXT:")
                            for k in range(start, end):
                                if k == j:
                                    log(f">>> {traceback_lines[k]}", "ERROR")
                                else:
                                    log(f"    {traceback_lines[k]}")
                    
                    # Find the specific code line
                    for line in traceback_lines:
                        if ".py" in line and "line" in line:
                            if "for" in line or "items()" in line:
                                log(f"\n🎯 PROBLEMATIC CODE: {line.strip()}", "CRITICAL")
                
                # Save full error details
                with open("/tmp/combat_error_full_details.json", "w") as f:
                    json.dump(error_data, f, indent=2)
                log("\n✅ Full error details saved to: /tmp/combat_error_full_details.json", "SUCCESS")
                
                log("\n" + "=" * 70)
                log("🏁 BUG SUCCESSFULLY CAPTURED!", "SUCCESS")
                log("This confirms PR #314's finding about the AttributeError!", "SUCCESS")
                break
                
            else:
                log(f"Different 500 error: {error_data.get('error', 'Unknown')}", "WARNING")
                
        except Exception as e:
            log(f"Failed to parse error response: {e}", "ERROR")
            log(f"Raw response: {combat_resp.text[:500]}", "ERROR")
    
    elif combat_resp.status_code == 200:
        log("Combat succeeded without error - bug may be fixed or not triggered", "WARNING")
    
    else:
        log(f"Unexpected status: {combat_resp.status_code}", "WARNING")

log("\n" + "=" * 70)
log("Test complete. Check /tmp/combat_bug_debug.log for server-side logs.", "INFO")