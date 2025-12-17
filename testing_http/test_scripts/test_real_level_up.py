#!/usr/bin/env python3
"""
Real Level-Up API Test with Full Evidence Capture

This test exercises the actual level-up validation path through real API calls
and captures HTTP status codes, response times, and Firestore state.

Usage:
    # Against local server (default)
    python test_real_level_up.py

    # Against preview server
    BASE_URL=https://mvp-site-app-s3-i6xf2p72ka-uc.a.run.app python test_real_level_up.py

    # Against production
    BASE_URL=https://worldarchitect.ai python test_real_level_up.py
"""

import json
import os
import time
import requests
from datetime import datetime
from pathlib import Path

# Configurable via environment variable
BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8085")
EVIDENCE_DIR = Path(__file__).parent / "evidence" / f"level_up_{int(time.time())}"

# Load auth token
auth_file = Path.home() / ".worldarchitect-ai" / "auth-token.json"
with open(auth_file) as f:
    auth_data = json.load(f)

AUTH_TOKEN = auth_data["idToken"]
USER_ID = auth_data.get("localId") or auth_data.get("user", {}).get("uid")

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {AUTH_TOKEN}"
}

evidence_log = []

def log_evidence(step: str, data: dict):
    """Log evidence with timestamp."""
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "step": step,
        **data
    }
    evidence_log.append(entry)
    print(f"\n{'='*60}")
    print(f"STEP: {step}")
    print(f"{'='*60}")
    for k, v in data.items():
        if isinstance(v, dict):
            print(f"{k}: {json.dumps(v, indent=2)[:500]}")
        else:
            print(f"{k}: {v}")

def mcp_call(tool_name: str, arguments: dict, request_id: int = 1):
    """Make an MCP tool call with full HTTP evidence capture."""
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        },
        "id": request_id
    }

    start_time = time.time()
    response = requests.post(f"{BASE_URL}/mcp", headers=HEADERS, json=payload)
    elapsed_ms = (time.time() - start_time) * 1000

    return {
        "status_code": response.status_code,
        "elapsed_ms": round(elapsed_ms, 2),
        "response": response.json() if response.status_code == 200 else response.text
    }

def extract_content(result: dict) -> dict | None:
    """Extract content from MCP response."""
    try:
        # Try direct result first (for create_campaign)
        mcp_result = result["response"]["result"]
        if isinstance(mcp_result, dict) and "campaign_id" in mcp_result:
            return mcp_result
        # Try content array format (for get_campaign_state)
        if "content" in mcp_result:
            text = mcp_result["content"][0]["text"]
            return json.loads(text)
        return mcp_result
    except (KeyError, TypeError, json.JSONDecodeError):
        return None

def main():
    print("="*60)
    print("REAL LEVEL-UP API TEST WITH EVIDENCE CAPTURE")
    print("="*60)
    print(f"Server: {BASE_URL}")
    print(f"User ID: {USER_ID}")
    print(f"Evidence Dir: {EVIDENCE_DIR}")

    # Create evidence directory
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: Health check
    log_evidence("Health Check", {
        "url": f"{BASE_URL}/health",
        "method": "GET"
    })

    start = time.time()
    health = requests.get(f"{BASE_URL}/health")
    elapsed = (time.time() - start) * 1000

    log_evidence("Health Response", {
        "status_code": health.status_code,
        "elapsed_ms": round(elapsed, 2),
        "body": health.json()
    })

    if health.status_code != 200:
        print("❌ Server not healthy")
        return 1

    # Step 2: Create campaign
    log_evidence("Create Campaign", {
        "tool": "create_campaign",
        "user_id": USER_ID
    })

    result = mcp_call("create_campaign", {
        "user_id": USER_ID,
        "title": f"LevelUpTest_{int(time.time())}",
        "character": "A brave warrior seeking adventure",
        "setting": "A medieval fantasy kingdom",
        "description": "Testing level-up mechanics"
    })

    log_evidence("Create Campaign Response", result)

    if result["status_code"] != 200:
        print(f"❌ Failed to create campaign: {result}")
        return 1

    campaign_data = extract_content(result)
    if not campaign_data or "campaign_id" not in campaign_data:
        print(f"❌ No campaign_id in response: {result}")
        return 1

    CAMPAIGN_ID = campaign_data["campaign_id"]
    print(f"✅ Campaign created: {CAMPAIGN_ID}")

    # Step 3: Get initial state
    log_evidence("Get Initial State", {
        "tool": "get_campaign_state",
        "campaign_id": CAMPAIGN_ID
    })

    result = mcp_call("get_campaign_state", {
        "user_id": USER_ID,
        "campaign_id": CAMPAIGN_ID
    })

    log_evidence("Initial State Response", result)

    initial_state = extract_content(result)
    initial_pc = initial_state.get("game_state", {}).get("player_character_data", {}) if initial_state else {}
    initial_level = initial_pc.get("level")
    initial_xp = initial_pc.get("experience", {}).get("current") if isinstance(initial_pc.get("experience"), dict) else initial_pc.get("experience")

    log_evidence("Initial Character State", {
        "level": initial_level,
        "xp": initial_xp,
        "full_pc_data": initial_pc
    })

    # Step 4: Process action that should trigger XP/level validation
    # We'll send a command that the narrator should interpret as XP gain
    log_evidence("Process Action - XP Gain Request", {
        "tool": "process_action",
        "campaign_id": CAMPAIGN_ID,
        "action": "Award XP for completing quest"
    })

    result = mcp_call("process_action", {
        "user_id": USER_ID,
        "campaign_id": CAMPAIGN_ID,
        "user_input": "I completed the quest and the DM awards me 500 experience points for my heroic deeds.",
        "mode": "narrator"
    })

    log_evidence("Process Action Response", {
        "status_code": result["status_code"],
        "elapsed_ms": result["elapsed_ms"],
        "response_preview": str(result["response"])[:1000]
    })

    # Step 5: Get state AFTER action to verify persistence
    log_evidence("Get State After Action", {
        "tool": "get_campaign_state",
        "campaign_id": CAMPAIGN_ID
    })

    result = mcp_call("get_campaign_state", {
        "user_id": USER_ID,
        "campaign_id": CAMPAIGN_ID
    })

    log_evidence("State After Action Response", result)

    after_state = extract_content(result)
    after_pc = after_state.get("game_state", {}).get("player_character_data", {}) if after_state else {}
    after_level = after_pc.get("level")
    after_xp = after_pc.get("experience", {}).get("current") if isinstance(after_pc.get("experience"), dict) else after_pc.get("experience")

    log_evidence("After Action Character State", {
        "level": after_level,
        "xp": after_xp,
        "full_pc_data": after_pc
    })

    # Step 6: Comparison
    log_evidence("State Comparison", {
        "before": {"level": initial_level, "xp": initial_xp},
        "after": {"level": after_level, "xp": after_xp},
        "changed": initial_level != after_level or initial_xp != after_xp
    })

    # Step 7: Test type coercion by checking the stored types
    log_evidence("Type Analysis", {
        "level_type": type(after_level).__name__ if after_level else "None",
        "xp_type": type(after_xp).__name__ if after_xp else "None",
        "level_is_int": isinstance(after_level, int),
        "xp_is_int": isinstance(after_xp, int)
    })

    # Save full evidence
    evidence_file = EVIDENCE_DIR / "evidence.json"
    with open(evidence_file, "w") as f:
        json.dump({
            "test_run": datetime.utcnow().isoformat() + "Z",
            "server": BASE_URL,
            "user_id": USER_ID,
            "campaign_id": CAMPAIGN_ID,
            "evidence_log": evidence_log,
            "summary": {
                "initial_state": {"level": initial_level, "xp": initial_xp},
                "final_state": {"level": after_level, "xp": after_xp},
                "all_http_200": all(e.get("status_code") == 200 for e in evidence_log if "status_code" in e)
            }
        }, f, indent=2)

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Campaign ID: {CAMPAIGN_ID}")
    print(f"Initial: level={initial_level}, xp={initial_xp}")
    print(f"After:   level={after_level}, xp={after_xp}")
    print(f"Evidence saved to: {evidence_file}")

    return 0

if __name__ == "__main__":
    exit(main())
