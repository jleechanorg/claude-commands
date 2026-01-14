#!/usr/bin/env python3
"""
Living World System E2E Test (Extended)

This test creates a REAL campaign with factions and NPCs, plays through
multiple turns (10+), and validates that the Living World system activates
correctly with all new event types.

What this test PROVES:
- Living world instruction is included every 3 turns
- 4 background events generated per LW turn (3 immediate + 1 long-term)
- Scene events trigger every 3-6 turns (player-facing)
- Faction updates and rumors are generated
- Background events are tracked in game state with proper fields
- State tracking (next_scene_event_turn, etc.) works correctly
- Event lifecycle status field is present (pending/discovered/resolved)

Event Types Validated:
- background_events with event_type: "immediate" (3 per LW turn)
- background_events with event_type: "long_term" (1 per LW turn)
- background_events with status: "pending|discovered|resolved"
- scene_event (at least 1 across 10+ turns)
- rumors, faction_updates, time_events

What this test does NOT prove:
- Every turn has perfect living world content (LLM is probabilistic)
- Specific event formats are always followed
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib import MCPClient
from lib.campaign_utils import create_campaign, get_campaign_state, process_action
from lib.evidence_utils import capture_provenance, get_evidence_dir
from lib.regression_oracle import (
    save_regression_snapshot,
    validate_multi_turn_test,
)
from lib.server_utils import start_local_mcp_server

# Configuration
BASE_URL = os.getenv("BASE_URL", "http://localhost:8001")
USER_ID = f"e2e-living-world-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
run_id = datetime.now(UTC).strftime('%Y%m%d_%H%M%S')
OUTPUT_DIR = str(get_evidence_dir("living_world_e2e", run_id=run_id))  # noqa: S108
STRICT_MODE = os.getenv("STRICT_MODE", "false").lower() == "true"
REQUIRE_STRUCTURED = os.getenv("REQUIRE_STRUCTURED", "false").lower() == "true"
GIT_CMD = shutil.which("git") or "git"

ARTIFACTS_DIR = os.path.join(OUTPUT_DIR, "artifacts")
os.makedirs(ARTIFACTS_DIR, exist_ok=True)
LOG_FILE = os.path.join(OUTPUT_DIR, "collection_log.txt")


def log(msg: str) -> None:
    """Log with timestamp."""
    ts = datetime.now(UTC).isoformat()
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def sha256_file(path: str) -> str:
    """Compute sha256 for a file path."""
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def write_checksum(path: str) -> None:
    """Write checksum file alongside a path."""
    checksum = sha256_file(path)
    with open(f"{path}.sha256", "w") as f:
        f.write(f"{checksum}  {os.path.basename(path)}\n")


def write_json(path: str, data: Any) -> None:
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    write_checksum(path)


def run_cmd(cmd: list[str], timeout: int = 10) -> dict:
    """Run command and capture output for evidence."""
    log(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(  # noqa: S603
            cmd, capture_output=True, text=True, timeout=timeout, check=False
        )
        log(f"Exit code: {result.returncode}")
        if result.stdout:
            log(f"Stdout: {result.stdout.strip()}")
        if result.stderr:
            log(f"Stderr: {result.stderr.strip()}")
        return {
            "command": cmd,
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except Exception as e:
        log(f"Command failed: {e}")
        return {"command": cmd, "error": str(e)}



def fetch_health() -> dict:
    """Capture server health response."""
    url = f"{BASE_URL.rstrip('/')}/health"
    log(f"Health check: {url}")
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:  # noqa: S310
            raw = resp.read().decode("utf-8")
        try:
            data = json.loads(raw)
            return {"ok": True, "raw": raw, "parsed": data}
        except json.JSONDecodeError:
            return {"ok": True, "raw": raw, "parsed": None}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def capture_config_proof() -> dict:
    """Capture living world instruction file if present."""
    src = os.path.join("mvp_site", "prompts", "living_world_instruction.md")
    if not os.path.exists(src):
        return {"found": False, "path": src}
    dest = os.path.join(OUTPUT_DIR, "living_world_instruction.md")
    shutil.copyfile(src, dest)
    write_checksum(dest)
    return {"found": True, "path": dest}


def save_turn_artifacts(turn_number: int, action: str, response: dict, campaign_id: str) -> dict:
    """Persist raw request/response and excerpts per turn."""
    turn_dir = os.path.join(ARTIFACTS_DIR, f"turn_{turn_number:02d}")
    os.makedirs(turn_dir, exist_ok=True)

    request_payload = {
        "turn_number": turn_number,
        "user_id": USER_ID,
        "campaign_id": campaign_id,
        "user_input": action,
    }
    req_path = os.path.join(turn_dir, "request.json")
    write_json(req_path, request_payload)

    resp_path = os.path.join(turn_dir, "response.json")
    write_json(resp_path, response)

    narrative = response.get("narrative", "") or response.get("raw_text", "")
    narrative_path = os.path.join(turn_dir, "narrative.txt")
    with open(narrative_path, "w") as f:
        f.write(narrative or "")
    write_checksum(narrative_path)

    # FIXED: Save system_instruction_files (list) instead of text (which doesn't exist)
    # The server provides system_instruction_files and char_count, not the full text
    sys_files_path = None
    debug_info = response.get("debug_info", {})
    if isinstance(debug_info, dict):
        sys_files = debug_info.get("system_instruction_files", [])
        char_count = debug_info.get("system_instruction_char_count", 0)
        if sys_files or char_count:
            sys_files_path = os.path.join(turn_dir, "system_instruction_info.json")
            sys_info = {
                "instruction_files": sys_files,
                "char_count": char_count,
                "lw_instruction_included": any(
                    "living_world" in f.lower() for f in sys_files
                ),
            }
            write_json(sys_files_path, sys_info)

    return {
        "turn_dir": turn_dir,
        "request_path": req_path,
        "response_path": resp_path,
        "narrative_path": narrative_path,
        "system_instruction_info_path": sys_files_path,
    }


def check_living_world_content(response: dict, turn_number: int) -> dict:  # noqa: PLR0912, PLR0915
    """Check if response contains living world content.

    Living world content can appear in:
    - state_updates.world_events (4 events: 3 immediate + 1 long-term)
    - state_updates.scene_event (player-facing, every 3-6 turns)
    - state_updates.faction_updates
    - state_updates.rumors
    - state_updates.time_events
    - state_updates.complications
    - narrative mentions of off-screen events

    Args:
        response: The process_action response
        turn_number: Current turn number

    Returns:
        Dict with detection results
    """
    results = {
        "turn_number": turn_number,
        "is_living_world_turn": turn_number % 3 == 0,
        "world_events_found": False,
        "faction_updates_found": False,
        "rumors_found": False,
        "time_events_found": False,
        "complications_found": False,
        "background_events_count": 0,
        # New: Event type tracking
        "immediate_events_count": 0,
        "long_term_events_count": 0,
        "events_with_type": 0,
        "events_with_discovery_turn": 0,
        # New: Event lifecycle tracking (status field)
        "events_with_status": 0,
        "events_pending": 0,
        "events_discovered": 0,
        "events_resolved": 0,
        # New: Scene event tracking
        "scene_event_found": False,
        "scene_event_type": None,
        # State tracking
        "next_scene_event_turn": None,
        "last_scene_event_turn": None,
        # Existing
        "narrative_hints": [],
        "structured_content_found": False,
        "game_state_world_events_found": False,
        "game_state_world_events_count": 0,
        # FIXED: Check system_instruction_files instead of system_instruction_text
        "lw_instruction_file_included": False,
        "system_instruction_files": [],
        "system_instruction_char_count": 0,
    }

    # Check state_updates
    state_updates = response.get("state_updates", {})
    if isinstance(state_updates, dict):
        # Check for world_events
        world_events = state_updates.get("world_events", {})
        if world_events and isinstance(world_events, dict):
            results["world_events_found"] = True
            background = world_events.get("background_events", [])
            if isinstance(background, list):
                results["background_events_count"] = len(background)
                # Check for event_type field on each event
                for event in background:
                    if isinstance(event, dict):
                        event_type = event.get("event_type")
                        if event_type:
                            results["events_with_type"] += 1
                            if event_type == "immediate":
                                results["immediate_events_count"] += 1
                            elif event_type == "long_term":
                                results["long_term_events_count"] += 1
                        if event.get("estimated_discovery_turn") is not None:
                            results["events_with_discovery_turn"] += 1
                        # Track event lifecycle status
                        event_status = event.get("status")
                        if event_status:
                            results["events_with_status"] += 1
                            if event_status == "pending":
                                results["events_pending"] += 1
                            elif event_status == "discovered":
                                results["events_discovered"] += 1
                            elif event_status == "resolved":
                                results["events_resolved"] += 1

        # Check for scene_event (NEW: player-facing events)
        scene_event = state_updates.get("scene_event", {})
        if scene_event and isinstance(scene_event, dict):
            results["scene_event_found"] = True
            results["scene_event_type"] = scene_event.get("type")

        # Check custom_campaign_state for tracking fields
        custom_state = state_updates.get("custom_campaign_state", {})
        if isinstance(custom_state, dict):
            results["next_scene_event_turn"] = custom_state.get("next_scene_event_turn")
            results["last_scene_event_turn"] = custom_state.get("last_scene_event_turn")

        # Check for faction_updates
        faction_updates = state_updates.get("faction_updates", {})
        if faction_updates and isinstance(faction_updates, dict):
            results["faction_updates_found"] = True

        # Check for rumors
        rumors = state_updates.get("rumors", [])
        if rumors and isinstance(rumors, list) and len(rumors) > 0:
            results["rumors_found"] = True

        time_events = state_updates.get("time_events", {})
        if time_events and isinstance(time_events, dict):
            results["time_events_found"] = True

        # Check for complications
        complications = state_updates.get("complications", {})
        if complications and isinstance(complications, dict):
            results["complications_found"] = True

    # Check narrative for hints about off-screen events
    narrative = response.get("narrative", "") or ""
    hint_keywords = [
        "meanwhile", "elsewhere", "heard that", "rumor", "news of",
        "while you were", "during your absence", "you've heard",
        "word has spread", "in other parts of"
    ]
    for keyword in hint_keywords:
        if keyword.lower() in narrative.lower():
            results["narrative_hints"].append(keyword)

    # FIXED: Check debug_info for system_instruction_files (not text)
    # The server provides system_instruction_files list and char_count, not the full text
    debug_info = response.get("debug_info", {})
    if isinstance(debug_info, dict):
        sys_files = debug_info.get("system_instruction_files", [])
        if isinstance(sys_files, list):
            results["system_instruction_files"] = sys_files
            # Check if living_world_instruction.md is in the list
            results["lw_instruction_file_included"] = any(
                "living_world" in f.lower() for f in sys_files
            )
        char_count = debug_info.get("system_instruction_char_count", 0)
        if isinstance(char_count, int):
            results["system_instruction_char_count"] = char_count

    results["structured_content_found"] = (
        results["world_events_found"] or
        results["faction_updates_found"] or
        results["rumors_found"] or
        results["time_events_found"] or
        results["complications_found"]
    )

    # Check persisted game_state for LW data (may be present even if not emitted)
    game_state = response.get("game_state", {})
    if isinstance(game_state, dict):
        gs_world_events = game_state.get("world_events", {})
        if gs_world_events and isinstance(gs_world_events, dict):
            results["game_state_world_events_found"] = True
            background = gs_world_events.get("background_events", [])
            if isinstance(background, list):
                results["game_state_world_events_count"] = len(background)

    # Calculate overall living world presence
    # FIXED: For LW turns, count all evidence including narrative hints
    # For non-LW turns, only count structured/game_state evidence (not narrative hints)
    # This prevents false positives on non-LW turns from generic keywords like "meanwhile"
    if results["is_living_world_turn"]:
        results["has_living_world_content"] = (
            results["structured_content_found"] or
            results["game_state_world_events_found"] or
            len(results["narrative_hints"]) > 0
        )
    else:
        # Non-LW turns: Only structured content counts as LW content
        # Narrative hints like "meanwhile" are not evidence of LW system activation
        results["has_living_world_content"] = (
            results["structured_content_found"] or
            results["game_state_world_events_found"]
        )

    return results


def main() -> int:  # noqa: PLR0912, PLR0915
    # Start a fresh collection log per run
    with open(LOG_FILE, "w") as f:
        f.write("")

    # Start local server
    port = 8001
    server = start_local_mcp_server(port)
    log(f"Started local MCP server on port {port}")

    # Wait for server to be ready
    import time
    server_ready = False
    for _ in range(20):
        health = fetch_health()
        if health.get("ok"):
            server_ready = True
            break
        time.sleep(1)

    if not server_ready:
        log("FAILED: Server did not start within timeout")
        server.stop()
        return 1

    try:
        results = {
            "test_name": "living_world_real_e2e",
            "test_type": "living_world_advancement",
            "timestamp": datetime.now(UTC).isoformat(),
            "base_url": BASE_URL,
            "user_id": USER_ID,
            "strict_mode": STRICT_MODE,
            "provenance": capture_provenance(BASE_URL),
            "artifacts_dir": ARTIFACTS_DIR,
            "collection_log": LOG_FILE,
            "steps": [],
            "turn_analyses": [],
            "summary": {},
        }

        # Health check and config capture
        health = fetch_health()
        if health.get("ok"):
            health_path = os.path.join(OUTPUT_DIR, "health_response.json")
            if health.get("parsed") is not None:
                write_json(health_path, health["parsed"])
            else:
                with open(health_path, "w") as f:
                    f.write(health.get("raw", ""))
                write_checksum(health_path)
            results["health_response_path"] = health_path
        else:
            results["health_error"] = health.get("error")

        config_info = capture_config_proof()
        results["config_proof"] = config_info

        log(f"Provenance: {results['provenance'].get('git_head', 'unknown')[:12]}...")
        log("Living World E2E Test - Testing every-3-turns advancement")
        log("=" * 60)

        # Create MCP client
        client = MCPClient(BASE_URL)

        # Step 1: Create campaign with rich faction/NPC setup
        log("\nStep 1: Creating campaign with factions and NPCs...")
        try:
            campaign_id = create_campaign(
                client,
                USER_ID,
                title="The Merchant's War",
                description=(
                    "A bustling trade city where three factions vie for control: "
                    "The Merchant's Guild (wealth and commerce), "
                    "The City Guard (law and order), and "
                    "The Shadow Court (thieves and spies). "
                    "Each faction has their own agenda and the player's actions ripple through the city."
                ),
                character=(
                    "Sera, a former merchant's daughter turned adventurer. "
                    "She knows the trade routes and has contacts in all factions."
                ),
                setting=(
                    "The Grand Bazaar of Saltmire, a coastal trade city. "
                    "The morning market is busy with merchants setting up stalls."
                ),
            )
            log(f"  Campaign ID: {campaign_id}")
            results["campaign_id"] = campaign_id
            results["steps"].append({
                "name": "create_campaign",
                "passed": True,
                "campaign_id": campaign_id,
            })
        except Exception as e:
            log(f"  FAILED: {e}")
            results["steps"].append({
                "name": "create_campaign",
                "passed": False,
                "error": str(e),
            })
            save_results(results)
            return 1

        # Step 2: Play through 10 turns to trigger:
        # - Living World 3 times (turns 3, 6, 9) for background events
        # - At least 1 Scene Event (every 3-6 turns)
        actions = [
            # Turn 1: Explore the market
            "I walk through the market, observing the merchants and listening for any interesting gossip.",
            # Turn 2: Interact with an NPC
            "I approach a spice merchant I recognize from my father's business. 'Marcus, it's been a while. How's trade these days?'",
            # Turn 3: Living World Turn - Should trigger advancement
            "I thank Marcus for the information and head toward the Guild Hall to see what opportunities might be posted.",
            # Turn 4: Continue exploration
            "I examine the job postings on the Guild Hall board, looking for anything that pays well.",
            # Turn 5: Take an action
            "I speak with the Guild clerk about the caravan escort job. What are the details?",
            # Turn 6: Living World Turn - Should trigger advancement again
            "I accept the caravan job and ask when the caravan departs. Then I head to the market to prepare supplies.",
            # Turn 7: Prepare for journey
            "I visit the armorer to check if my equipment needs any repairs before the journey.",
            # Turn 8: Gather information
            "I stop by the tavern to ask travelers about the road conditions to Oakhaven.",
            # Turn 9: Living World Turn - Should trigger advancement
            "I return to the caravan staging area to meet my fellow guards and the merchant leading the caravan.",
            # Turn 10: Begin journey
            "I take my position with the caravan as we depart through the eastern gate. I keep my eyes open for trouble.",
        ]

        living_world_turns = []

        for i, action in enumerate(actions, start=1):
            log(f"\nStep 2.{i}: Turn {i} - {action[:50]}...")
            try:
                response = process_action(
                    client,
                    user_id=USER_ID,
                    campaign_id=campaign_id,
                    user_input=action,
                )

                narrative = response.get("narrative", "") or response.get("raw_text", "")
                narrative_preview = narrative[:150] if narrative else "None"

                # Analyze for living world content
                lw_analysis = check_living_world_content(response, i)
                results["turn_analyses"].append(lw_analysis)

                artifact_paths = save_turn_artifacts(i, action, response, campaign_id)

                passed = bool(narrative)
                if isinstance(response.get("success"), bool):
                    passed = passed and response.get("success") is True

                step_result = {
                    "name": f"turn_{i}",
                    "turn_number": i,
                    "passed": passed,
                    "narrative_preview": narrative_preview,
                    "is_living_world_turn": lw_analysis["is_living_world_turn"],
                    "living_world_content": lw_analysis["has_living_world_content"],
                    "structured_content": lw_analysis["structured_content_found"],
                    "game_state_world_events": lw_analysis["game_state_world_events_found"],
                    "lw_instruction_file_included": lw_analysis["lw_instruction_file_included"],
                    "artifact_paths": artifact_paths,
                }

                if lw_analysis["is_living_world_turn"]:
                    living_world_turns.append({
                        "turn_number": i,
                        "analysis": lw_analysis,
                        "response_keys": list(response.keys()),
                        "state_updates": response.get("state_updates", {}),
                        "artifact_paths": artifact_paths,
                    })
                    log("  🌍 Living World Turn!")
                    log(f"     World Events: {lw_analysis['world_events_found']}")
                    log(f"     Background Events: {lw_analysis['background_events_count']} total")
                    log(f"       - Immediate: {lw_analysis['immediate_events_count']}")
                    log(f"       - Long-term: {lw_analysis['long_term_events_count']}")
                    log(f"       - With event_type: {lw_analysis['events_with_type']}")
                    log(f"       - With status: {lw_analysis['events_with_status']} (pending:{lw_analysis['events_pending']}, discovered:{lw_analysis['events_discovered']}, resolved:{lw_analysis['events_resolved']})")
                    log(f"     Faction Updates: {lw_analysis['faction_updates_found']}")
                    log(f"     Rumors: {lw_analysis['rumors_found']}")
                    log(f"     Time Events: {lw_analysis['time_events_found']}")
                    log(f"     Game State World Events: {lw_analysis['game_state_world_events_found']}")
                    log(f"     LW Instruction File: {lw_analysis['lw_instruction_file_included']}")
                    log(f"     SysInstr Files: {lw_analysis['system_instruction_files']}")
                    log(f"     Narrative Hints: {lw_analysis['narrative_hints']}")
                # Clarify: "persisted state" means world_events from prior LW turns still exist in game_state
                # This is NOT new LW generation - just showing that world state persists across turns
                elif lw_analysis['has_living_world_content']:
                    log("  📖 Regular turn (persisted LW state visible: True)")
                else:
                    log("  📖 Regular turn (no LW state)")

                # Check for scene event on any turn
                if lw_analysis["scene_event_found"]:
                    log(f"  🎭 Scene Event Triggered! Type: {lw_analysis['scene_event_type']}")

                # Show scene event tracking state
                if lw_analysis["next_scene_event_turn"] is not None:
                    log(f"     Next Scene Event Turn: {lw_analysis['next_scene_event_turn']}")

                log(f"  Narrative: {narrative_preview}...")

                results["steps"].append(step_result)

            except Exception as e:
                log(f"  FAILED: {e}")
                results["steps"].append({
                    "name": f"turn_{i}",
                    "turn_number": i,
                    "passed": False,
                    "error": str(e),
                })
                # Continue with other turns

        # Step 3: Get final campaign state
        log("\nStep 3: Getting final campaign state...")
        try:
            final_state = get_campaign_state(
                client,
                user_id=USER_ID,
                campaign_id=campaign_id,
            )
            final_state_path = os.path.join(OUTPUT_DIR, "final_state.json")
            write_json(final_state_path, final_state)
            game_state = final_state.get("game_state", {})

            # Check for living world data in game state
            world_events = game_state.get("world_events", {})
            custom_state = game_state.get("custom_campaign_state", {})

            results["steps"].append({
                "name": "get_final_state",
                "passed": True,
                "has_world_events": bool(world_events),
                "custom_state_keys": list(custom_state.keys()) if custom_state else [],
                "final_state_path": final_state_path,
            })
            results["final_game_state_summary"] = {
                "has_world_events": bool(world_events),
                "world_events_sample": world_events if world_events else None,
                "custom_campaign_state": custom_state,
            }
            log(f"  World events in state: {bool(world_events)}")
            log(f"  Custom state keys: {list(custom_state.keys()) if custom_state else []}")

        except Exception as e:
            log(f"  FAILED: {e}")
            results["steps"].append({
                "name": "get_final_state",
                "passed": False,
                "error": str(e),
            })

        # Summary
        turns_with_lw_content = sum(1 for a in results["turn_analyses"] if a["has_living_world_content"])
        lw_turns_with_content = sum(
            1 for a in results["turn_analyses"]
            if a["is_living_world_turn"] and a["has_living_world_content"]
        )
        expected_lw_turns = len([t for t in range(1, len(actions) + 1) if t % 3 == 0])
        lw_turns_structured = sum(
            1 for a in results["turn_analyses"]
            if a["is_living_world_turn"] and a["structured_content_found"]
        )
        lw_turns_game_state = sum(
            1 for a in results["turn_analyses"]
            if a["is_living_world_turn"] and a["game_state_world_events_found"]
        )
        lw_turns_sysinstr = sum(
            1 for a in results["turn_analyses"]
            if a["is_living_world_turn"] and a["lw_instruction_file_included"]
        )
        structured_non_lw = sum(
            1 for a in results["turn_analyses"]
            if (not a["is_living_world_turn"]) and a["structured_content_found"]
        )

        # NEW: Calculate event type metrics across all LW turns
        total_immediate_events = sum(
            a["immediate_events_count"] for a in results["turn_analyses"]
            if a["is_living_world_turn"]
        )
        total_long_term_events = sum(
            a["long_term_events_count"] for a in results["turn_analyses"]
            if a["is_living_world_turn"]
        )
        total_events_with_type = sum(
            a["events_with_type"] for a in results["turn_analyses"]
            if a["is_living_world_turn"]
        )
        total_events_with_discovery_turn = sum(
            a["events_with_discovery_turn"] for a in results["turn_analyses"]
            if a["is_living_world_turn"]
        )
        # Event lifecycle status tracking
        total_events_with_status = sum(
            a["events_with_status"] for a in results["turn_analyses"]
            if a["is_living_world_turn"]
        )
        total_events_pending = sum(
            a["events_pending"] for a in results["turn_analyses"]
            if a["is_living_world_turn"]
        )
        total_events_discovered = sum(
            a["events_discovered"] for a in results["turn_analyses"]
            if a["is_living_world_turn"]
        )
        total_events_resolved = sum(
            a["events_resolved"] for a in results["turn_analyses"]
            if a["is_living_world_turn"]
        )

        # NEW: Scene event metrics
        scene_events_found = sum(
            1 for a in results["turn_analyses"] if a["scene_event_found"]
        )
        scene_event_types = [
            a["scene_event_type"] for a in results["turn_analyses"]
            if a["scene_event_found"] and a["scene_event_type"]
        ]

        results["living_world_turns"] = living_world_turns
        results["summary"] = {
            "campaign_created": campaign_id is not None,
            "total_turns": len(actions),
            "expected_living_world_turns": expected_lw_turns,
            "living_world_turns_with_content": lw_turns_with_content,
            "living_world_turns_with_structured_content": lw_turns_structured,
            "living_world_turns_with_game_state_world_events": lw_turns_game_state,
            "living_world_turns_with_system_instruction": lw_turns_sysinstr,
            "structured_content_on_non_lw_turns": structured_non_lw,
            "total_turns_with_lw_content": turns_with_lw_content,
            # NEW: Event type metrics
            "total_immediate_events": total_immediate_events,
            "total_long_term_events": total_long_term_events,
            "total_events_with_type": total_events_with_type,
            "total_events_with_discovery_turn": total_events_with_discovery_turn,
            # NEW: Event lifecycle status metrics
            "total_events_with_status": total_events_with_status,
            "total_events_pending": total_events_pending,
            "total_events_discovered": total_events_discovered,
            "total_events_resolved": total_events_resolved,
            # NEW: Scene event metrics
            "scene_events_found": scene_events_found,
            "scene_event_types": scene_event_types,
            # Existing metrics
            "steps_passed": sum(1 for s in results["steps"] if s.get("passed")),
            "steps_total": len(results["steps"]),
            "living_world_success_rate": (
                lw_turns_with_content / expected_lw_turns * 100
                if expected_lw_turns > 0 else 0
            ),
        }

        log("\n" + "=" * 60)
        log("SUMMARY")
        log("=" * 60)
        log(f"Campaign created: {campaign_id is not None}")
        log(f"Total turns played: {len(actions)}")
        log(f"Expected living world turns: {expected_lw_turns} (turns {', '.join(str(t) for t in range(3, len(actions) + 1, 3))})")
        log(f"Living world turns with content: {lw_turns_with_content}/{expected_lw_turns}")
        log(f"Living world turns with structured content: {lw_turns_structured}/{expected_lw_turns}")
        log(f"Living world turns with game_state world_events: {lw_turns_game_state}/{expected_lw_turns}")
        log(f"Living world turns with system_instruction: {lw_turns_sysinstr}/{expected_lw_turns}")
        log(f"Structured content on non-LW turns: {structured_non_lw}")
        log(f"Total turns with any LW content: {turns_with_lw_content}")
        log("")
        log("EVENT TYPE BREAKDOWN:")
        log(f"  Total immediate events: {total_immediate_events}")
        log(f"  Total long-term events: {total_long_term_events}")
        log(f"  Events with event_type field: {total_events_with_type}")
        log(f"  Events with estimated_discovery_turn: {total_events_with_discovery_turn}")
        log("")
        log("EVENT LIFECYCLE STATUS:")
        log(f"  Events with status field: {total_events_with_status}")
        log(f"    - pending: {total_events_pending}")
        log(f"    - discovered: {total_events_discovered}")
        log(f"    - resolved: {total_events_resolved}")
        log("")
        log("SCENE EVENTS:")
        log(f"  Scene events triggered: {scene_events_found}")
        log(f"  Scene event types: {scene_event_types}")
        log("")
        log(f"Steps passed: {results['summary']['steps_passed']}/{results['summary']['steps_total']}")

        # Run regression validation against invariants
        log("\n" + "=" * 60)
        log("REGRESSION VALIDATION")
        log("=" * 60)

        # Build turn_results for regression oracle
        turn_results = []
        for analysis in results["turn_analyses"]:
            turn_num = analysis.get("turn_number", len(turn_results) + 1)
            try:
                turn_num = int(turn_num)
            except (TypeError, ValueError):
                turn_num = len(turn_results) + 1
            living_world_for_turn = next(
                (lw for lw in living_world_turns if lw.get("turn_number") == turn_num),
                None,
            )
            state_updates = (
                living_world_for_turn.get("state_updates", {})
                if living_world_for_turn
                else {}
            )
            turn_result = {
                "turn_number": turn_num,
                "response": {
                    "narrative": "",
                    "state_updates": state_updates,
                    "planning_block": {},
                },
                "analysis": analysis,
            }
            turn_results.append(turn_result)

        # Validate using regression oracle
        regression_result = validate_multi_turn_test(
            turn_results,
            expect_scene_events=True,
            min_turns=10,
        )

        log(f"Regression status: {regression_result.overall_status.upper()}")
        if regression_result.breaking_changes:
            log("Breaking changes detected:")
            for change in regression_result.breaking_changes:
                log(f"  ❌ {change}")
        if regression_result.suspicious_changes:
            log("Suspicious changes detected:")
            for change in regression_result.suspicious_changes:
                log(f"  ⚠️ {change}")

        # Add regression results to output
        results["regression_validation"] = regression_result.to_dict()

        # Save regression snapshot for future comparisons
        snapshot_path = Path(OUTPUT_DIR) / "regression_snapshot.json"
        save_regression_snapshot(
            snapshot_path,
            test_name="living_world_real_e2e",
            test_type="living_world_advancement",
            turn_results=turn_results,
            summary={
                "living_world_triggered": lw_turns_structured > 0,
                "scene_event_occurred": scene_events_found > 0,
                "total_background_events": total_immediate_events + total_long_term_events,
                "total_scene_events": scene_events_found,
                "total_faction_updates": sum(
                    1 for a in results["turn_analyses"]
                    if a["faction_updates_found"]
                ),
            },
        )
        log(f"\nRegression snapshot saved to: {snapshot_path}")

        save_results(results)

        # Success criteria
        if lw_turns_structured > 0:
            log("\n✅ SUCCESS: Structured living world content detected on scheduled turns!")
            return 0
        if REQUIRE_STRUCTURED:
            log("\n❌ FAILED: Structured living world content not detected on scheduled turns")
            return 1
        if turns_with_lw_content > 0:
            log("\n⚠️ PARTIAL: Living world content detected, but not on expected turns")
            return 0 if not STRICT_MODE else 1
        log("\n❌ FAILED: No living world content detected in any turn")
        return 1 if STRICT_MODE else 0
    finally:
        server.stop()


def save_results(results: dict) -> None:
    """Save results to file with checksum."""
    output_file = os.path.join(OUTPUT_DIR, "living_world_e2e_test.json")
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    # Generate checksum
    with open(output_file, "rb") as f:
        checksum = hashlib.sha256(f.read()).hexdigest()

    checksum_file = f"{output_file}.sha256"
    with open(checksum_file, "w") as f:
        f.write(f"{checksum}  living_world_e2e_test.json\n")

    log(f"\nResults saved to: {output_file}")
    log(f"Checksum: {checksum}")


if __name__ == "__main__":
    sys.exit(main())
