#!/usr/bin/env python3
"""Reproduction test for Narrative Lag / Off-by-One Error.

Focus: Verifying that the GM responds to the CURRENT turn, not the previous one.
Issue: In long campaigns, "context weighting" caused GM to prioritize unresolved
intents from history over the current action.

Run (local MCP already running):
    cd testing_mcp
    python test_narrative_lag_repro.py --server-url http://127.0.0.1:8001

Run (start local MCP automatically):
    cd testing_mcp
    python test_narrative_lag_repro.py --start-local
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

sys.path.insert(0, str(Path(__file__).parent))

from lib.campaign_utils import create_campaign, process_action
from lib.evidence_utils import (
    capture_provenance,
    create_evidence_bundle,
    get_evidence_dir,
)
from lib.server_utils import (
    DEFAULT_EVIDENCE_ENV,
    LocalServer,
    PROJECT_ROOT,
    pick_free_port,
)
from lib.mcp_client import MCPClient

# Constants
WORK_NAME = "narrative_lag_repro"
DEFAULT_SERVER_URL = "http://127.0.0.1:8001"

# Generic filler actions to build up context history
# CRITICAL: Need 50+ entries to exploit "lost-in-the-middle" effect
# Research shows LLMs attend best to beginning/end, struggle with middle content
# By putting user_action in middle of very long JSON, we increase chance of failure
BASE_FILLER_ACTIONS = [
    "I look around the tavern.",
    "I order a drink.",
    "I ask about local rumors.",
    "I check my equipment.",
    "I walk to the door.",
    "I open the door.",
    "I look at the street.",
    "I walk down the street.",
    "I see a shop.",
    "I enter the shop.",
    "I browse the shop's wares.",
    "I ask the shopkeeper about rare items.",
    "I examine a mysterious artifact.",
    "I negotiate a price.",
    "I leave the shop.",
    "I continue down the street.",
    "I notice a strange building.",
    "I approach the building cautiously.",
    "I examine the door.",
    "I look for any signs or markings.",
]

# Expand to create long story_history that buries user_action in middle
# Research: "Lost-in-the-middle" effect - need 30+ entries to exploit
# This creates VERY long story_history that buries user_action in middle of JSON
# Use 3x multiplier for 60 actions to maximize "lost-in-the-middle" effect
FILLER_ACTIONS = BASE_FILLER_ACTIONS * 2  # 40 actions total - enough to exploit middle effect

# The critical sequence to test context lag
# ACTION_A: Creates an ongoing unresolved intent (ritual that requires continuation)
# Make ritual explicitly multi-stage to create strong unresolved intent
# ACTION_B: MUCH WEAKER interrupt - research shows weaker commands more likely to fail
# If narrative lag exists, GM will continue the ritual instead of responding to STOP
ACTION_A = "I begin a complex ritual to decipher the ancient mural. I start chanting the first incantation and begin tracing the runes with my finger. This ritual requires multiple stages and will take several minutes to complete. I focus all my concentration on the ritual. The first stage is complete, now I must continue to the second stage. The ritual's power is building, I can feel the arcane energy flowing through me. I must complete the second stage to unlock the mural's secrets."
ACTION_B = "Wait."

def start_flask_server(port: int, env_overrides: dict[str, str] | None = None) -> LocalServer:
    """Start Flask main.py server with real services."""
    # Try venv first (has all dependencies), then fallback to system python
    python_bin = PROJECT_ROOT / "venv" / "bin" / "python3"
    if not python_bin.exists():
        python_bin = PROJECT_ROOT / "venv" / "bin" / "python"
    if not python_bin.exists():
        python_bin = Path(sys.executable)
    
    env = dict(os.environ)
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    for key, value in DEFAULT_EVIDENCE_ENV.items():
        env.setdefault(key, value)
    if env_overrides:
        env.update(env_overrides)

    env["MOCK_SERVICES_MODE"] = "false"
    env["TESTING"] = "true"  # Auth bypass headers enabled
    env["FLASK_DEBUG"] = "0" # Disable reloader for stability
    env["CAPTURE_RAW_LLM"] = "false" # Reduce logging overhead
    if env.get("WORLDAI_GOOGLE_APPLICATION_CREDENTIALS") and not env.get("WORLDAI_DEV_MODE"):
        env["WORLDAI_DEV_MODE"] = "true"
    env["PORT"] = str(port)

    log_root = PROJECT_ROOT / "tmp" / "mcp_server_logs"
    log_root.mkdir(parents=True, exist_ok=True)
    log_path = log_root / f"flask_main_{port}.log"
    log_f = open(log_path, "wb")
    
    proc = subprocess.Popen(
        [str(python_bin), "-m", "mvp_site.main"],
        cwd=str(PROJECT_ROOT),
        env=env,
        stdout=log_f,
        stderr=subprocess.STDOUT,
    )

    return LocalServer(proc=proc, base_url=f"http://127.0.0.1:{port}", log_path=log_path, _log_file=log_f)

def verify_real_mode(server_url: str) -> bool:
    try:
        response = requests.get(f"{server_url}/health", timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False

def wait_for_server(server_url: str, timeout: int = 120) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        if verify_real_mode(server_url):
            return True
        time.sleep(1)
    return False

def run_test(client: MCPClient, user_id: str) -> dict[str, Any]:
    print(f"\n[1/4] Creating campaign...")
    campaign_id = create_campaign(
        client,
        user_id,
        title="Narrative Lag Test",
        character="Wizard",
        setting="Ancient Ruins",
        description="Testing context priority",
    )
    print(f"      Campaign ID: {campaign_id}")

    # FORCE COMPLETE CHARACTER CREATION
    print(f"\n[Setup] Force-completing character creation via God Mode...")
    god_mode_payload = {
        "custom_campaign_state": {
            "character_creation_completed": True,
            "character_creation_in_progress": False
        },
        "player_character_data": {
            "name": "Test Wizard",
            "class": "Wizard",
            "level": 1,
            "hp_current": 10,
            "hp_max": 10
        }
    }
    process_action(
        client, 
        user_id=user_id, 
        campaign_id=campaign_id, 
        user_input=f"GOD_MODE_UPDATE_STATE:{json.dumps(god_mode_payload)}"
    )

    # Check initial state
    print(f"\n[Check] Verifying campaign start...")
    initial_resp = process_action(client, user_id=user_id, campaign_id=campaign_id, user_input="I look around.")
    initial_narrative = initial_resp.get("narrative", "")
    print(f"      Initial Narrative: {initial_narrative[:200]}...")
    
    # We expect standard story mode now
    if "CHARACTER CREATION" in initial_narrative:
        print("      WARNING: Still in character creation despite God Mode update.")

    # Build up VERY LONG story history to trigger narrative lag
    # Research: "Lost-in-the-middle" effect - LLMs attend best to beginning/end
    # Strategy: Put user_action in MIDDLE of very long JSON to exploit this
    # Use ALL filler actions (40+) to create maximum context imbalance
    num_fillers = len(FILLER_ACTIONS)
    print(f"\n[2/4] Filling context with {num_fillers} actions to exploit 'lost-in-the-middle' effect...")
    print(f"      (Research: LLMs struggle with middle content in long contexts)")
    for i, action in enumerate(FILLER_ACTIONS):
        if (i + 1) % 10 == 0 or i < 5:  # Print every 10th or first 5
            print(f"      Action {i+1}/{num_fillers}: {action}")
        process_action(client, user_id=user_id, campaign_id=campaign_id, user_input=action)
        # No sleep - process as fast as possible for long test

    print(f"\n[3/4] Performing Action A (The Hook): '{ACTION_A}'")
    resp_a = process_action(client, user_id=user_id, campaign_id=campaign_id, user_input=ACTION_A)
    narrative_a = resp_a.get("narrative", "")
    print(f"      GM Response A (Preview): {narrative_a[:200]}...")

    print(f"\n[4/4] Performing Action B (The Interrupt): '{ACTION_B}'")
    resp_b = process_action(client, user_id=user_id, campaign_id=campaign_id, user_input=ACTION_B)
    narrative_b = resp_b.get("narrative", "")
    print(f"      GM Response B (Full): {narrative_b}")

    # ANALYSIS - More aggressive detection of narrative lag
    narrative_b_lower = narrative_b.lower()
    
    # Success markers: Response B should respond to the interrupt/wait/stop
    # With weak interrupt "Wait", we need broader markers
    success_markers = ["attack", "sword", "goblin", "combat", "strike", "hit", "miss", "damage", "weapon", "enemy", "stop", "interrupt", "wait", "pause", "hesitate", "halt", "cease"]
    has_success_marker = any(m in narrative_b_lower for m in success_markers)

    # Failure markers: Response B should NOT continue the ritual as if nothing happened
    ignores_attack = not has_success_marker
    
    # Ritual continuation markers - these indicate the ritual is STILL HAPPENING (bad)
    ritual_continuation_markers = [
        "continue chanting", "still chanting", "keep chanting", "chanting continues",
        "ritual continues", "continuing the ritual", "ritual proceeds", "ritual completes",
        "finish the ritual", "complete the ritual", "ritual finishes", "chanting reaches",
        "second stage", "third stage", "next stage", "stage of your ritual", "ritual fails to take form"
    ]
    continues_ritual = any(m in narrative_b_lower for m in ritual_continuation_markers)
    
    # Ritual acknowledgment markers - these just mention ritual was interrupted (good)
    ritual_acknowledgment_markers = [
        "ritual is severed", "chanting dies", "ritual snaps", "ritual interrupted",
        "ritual stops", "chanting stops", "ritual ends", "ritual breaks", "abandon the"
    ]
    acknowledges_interruption = any(m in narrative_b_lower for m in ritual_acknowledgment_markers)
    
    ritual_markers = ["chant", "ritual", "runes", "decipher", "concentrat"]
    mentions_ritual = any(m in narrative_b_lower for m in ritual_markers)

    # Strong Fail: Continues ritual OR mentions ritual BUT NOT attack/stopping
    strong_fail = (continues_ritual or (mentions_ritual and ignores_attack and not acknowledges_interruption))

    status = "PASS"
    fail_reason = ""
    
    if strong_fail:
        status = "FAIL"
        fail_reason = "GM ignored the stop/attack and continued ritual (Narrative Lag Detected)"
    elif ignores_attack:
        status = "FAIL"
        fail_reason = "GM ignored the attack (General non-responsiveness)"
    
    result = {
        "status": status,
        "fail_reason": fail_reason,
        "narrative_a": narrative_a,
        "narrative_b": narrative_b,
        "checks": {
            "has_success_marker": has_success_marker,
            "mentions_ritual": mentions_ritual,
            "ignores_attack": ignores_attack,
            "strong_fail": strong_fail
        }
    }
    
    return result

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--server-url", default=DEFAULT_SERVER_URL)
    parser.add_argument("--start-local", action="store_true")
    parser.add_argument("--savetmp", action="store_true")
    parser.add_argument("--user-id", default="test_lag_user")
    args = parser.parse_args()

    server_url = args.server_url
    local_server = None
    env_overrides = {"MOCK_SERVICES_MODE": "false", "TESTING": "true"}

    try:
        if args.start_local:
            print("Starting local server...")
            port = pick_free_port()
            # Capture credential env vars for evidence provenance
            for cred_var in ["WORLDAI_GOOGLE_APPLICATION_CREDENTIALS", "GOOGLE_APPLICATION_CREDENTIALS", "FIRESTORE_EMULATOR_HOST"]:
                if os.environ.get(cred_var):
                    env_overrides[cred_var] = os.environ[cred_var]
            local_server = start_flask_server(port, env_overrides)
            server_url = local_server.base_url
            print(f"Server log: {local_server.log_path}")
            if not wait_for_server(server_url, timeout=90):
                print("Server failed to start")
                with open(local_server.log_path, 'r') as f:
                    print(f.read())
                return 1

        print(f"Connecting to {server_url}...")
        client = MCPClient(server_url)
        
        result = run_test(client, args.user_id)
        
        print("\n" + "="*60)
        print(f"RESULT: {result['status']}")
        if result['status'] == "FAIL":
            print(f"Reason: {result['fail_reason']}")
        print("="*60)

        # ALWAYS save evidence to /tmp (per evidence-standards.md)
        evidence_dir = get_evidence_dir(WORK_NAME)
        print(f"\nSaving evidence to {evidence_dir}...")
        bundle_files = create_evidence_bundle(
            evidence_dir,
            test_name=WORK_NAME,
            provenance=capture_provenance(server_url, local_server.proc.pid if local_server else None, server_env_overrides=env_overrides),
            results=result,
            request_responses=client.get_captures_as_dict() if hasattr(client, "get_captures_as_dict") else None,
            server_log_path=local_server.log_path if local_server else None,
        )
        latest_link = evidence_dir / "latest"
        print(f"Evidence saved to {latest_link} -> {bundle_files.get('readme', 'unknown')}")

        return 0 if result['status'] == "PASS" else 1

    except Exception as e:
        print(f"Test execution failed: {e}")
        if local_server:
            print("\nDumping server log (last 50 lines):")
            try:
                with open(local_server.log_path, 'r') as f:
                    lines = f.readlines()
                    print("".join(lines[-50:]))
            except Exception as log_err:
                print(f"Could not read log: {log_err}")
        return 1
    finally:
        if local_server:
            local_server.stop()

if __name__ == "__main__":
    sys.exit(main())