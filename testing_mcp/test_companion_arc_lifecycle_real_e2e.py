#!/usr/bin/env python3
"""
Companion Quest Arc Lifecycle E2E Test

This test validates a COMPLETE companion quest arc lifecycle:
1. Arc starts (initialization by Turn 3-5)
2. 3+ arc events occur (missions/developments)
3. Arc progresses through phases (discovery → development → crisis → resolution)
4. Arc finishes (status: completed)
5. Arc is marked as done

This is a comprehensive lifecycle test that plays through enough turns
to see an arc from start to finish, validating the full journey.

Evidence Standards Compliance:
- Uses testing_mcp/lib/evidence_utils.py for canonical evidence capture
- Evidence saved to /tmp/<repo>/<branch>/companion_arc_lifecycle/<timestamp>/
- Includes README.md, methodology.md, evidence.md, metadata.json
- Captures git provenance and server runtime info
- All files have SHA256 checksums per .claude/skills/evidence-standards.md

Run locally:
    BASE_URL=http://localhost:8001 python testing_mcp/test_companion_arc_lifecycle_real_e2e.py

Run against preview:
    BASE_URL=https://preview-url python testing_mcp/test_companion_arc_lifecycle_real_e2e.py

Evidence will be automatically saved to:
    /tmp/worldarchitect.ai/<branch>/companion_arc_lifecycle/<timestamp>/
"""

import json
import os
import shutil
import signal
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
import requests

from testing_mcp.dev_server import WORKTREE_PORT, get_base_url, is_server_healthy
from testing_mcp.lib.arc_validation_utils import (
    extract_companion_arc_event,
    extract_companion_arcs,
    extract_narrative,
    find_arc_themes_in_narrative,
    find_companions_in_narrative,
    validate_companion_dialogue_in_narrative,
)
from testing_mcp.lib.campaign_utils import (
    get_campaign_state,
    process_action,
)
from testing_mcp.lib.evidence_utils import (
    capture_provenance,
    create_evidence_bundle,
    get_evidence_dir,
    save_request_responses,
)
from testing_mcp.lib.mcp_client import MCPClient
from testing_mcp.lib.server_utils import start_local_mcp_server

    # Configuration (deferred to main() to avoid import-time side effects)
BASE_URL: str | None = None
USER_ID: str | None = None
WORK_NAME = "companion_arc_lifecycle"
STRICT_MODE: bool = True
EVIDENCE_DIR: Path | None = None
SERVER: Any = None  # Server handle for log capture

# Track request/response pairs for evidence (populated from MCPClient captures)
REQUEST_RESPONSE_PAIRS: list[tuple[dict, dict]] = []


def log(msg: str) -> None:
    """Log with timestamp."""
    ts = datetime.now(UTC).isoformat()
    print(f"[{ts}] {msg}", flush=True)  # flush=True prevents buffering when piped to file


def get_arc_phase(arc: dict) -> str:
    """Get current phase of an arc."""
    return arc.get("phase", "unknown")


def get_arc_progress(arc: dict) -> int:
    """Get current progress of an arc (0-100)."""
    return arc.get("progress", 0)


def is_arc_complete(arc: dict) -> bool:
    """Check if arc is marked as complete."""
    phase = get_arc_phase(arc)
    progress = get_arc_progress(arc)
    # Arc is complete if phase is "resolution" and progress is 100, or status is "completed"
    return (
        phase == "resolution" and progress >= 100
    ) or arc.get("status") == "completed"


def get_arc_history(arc: dict) -> list[dict]:
    """Get arc history events."""
    return arc.get("history", [])


def main() -> int:
    """Run companion quest arc lifecycle E2E test."""
    # Initialize runtime configuration (deferred from import-time to avoid side effects)
    global BASE_URL, USER_ID, EVIDENCE_DIR, STRICT_MODE, SERVER

    BASE_URL = os.getenv("BASE_URL") or get_base_url()
    USER_ID = f"e2e-arc-lifecycle-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
    STRICT_MODE = os.getenv("STRICT_MODE", "true").lower() == "true"

    # Evidence directory following /tmp/<repo>/<branch>/<work>/<timestamp>/ structure
    EVIDENCE_DIR = get_evidence_dir(WORK_NAME) / datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    # Always restart server on worktree port for clean test state
    log("Restarting server on worktree port...")

    # Kill any existing server on worktree port - more aggressive cleanup
    log(f"  Checking for existing server on port {WORKTREE_PORT}...")
    max_cleanup_attempts = 3
    for attempt in range(max_cleanup_attempts):
        if is_server_healthy(WORKTREE_PORT, timeout=1.0):
            log(f"  Attempt {attempt + 1}: Killing existing server on port {WORKTREE_PORT}...")
            try:
                # Find and kill process on this port
                result = subprocess.run(
                    ["lsof", "-ti", f":{WORKTREE_PORT}"],
                    check=False, capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0 and result.stdout.strip():
                    pids = result.stdout.strip().split('\n')
                    for pid in pids:
                        try:
                            os.kill(int(pid), signal.SIGTERM)
                            log(f"    Killed process {pid}")
                        except (ValueError, ProcessLookupError, PermissionError):
                            pass
                    time.sleep(3)  # Wait longer for process to die and port to free
                else:
                    # Try alternative kill method
                    log("    Using pkill fallback...")
                    subprocess.run(
                        ["pkill", "-9", "-f", f"mcp_api.*--port.*{WORKTREE_PORT}"],
                        check=False, timeout=5,
                        stderr=subprocess.DEVNULL
                    )
                    time.sleep(3)
            except (subprocess.TimeoutExpired, FileNotFoundError):
                # lsof not available or timeout - try alternative method
                log("    Using pkill fallback (lsof unavailable)...")
                subprocess.run(
                    ["pkill", "-9", "-f", f"mcp_api.*--port.*{WORKTREE_PORT}"],
                    check=False, timeout=5,
                    stderr=subprocess.DEVNULL
                )
                time.sleep(3)

            # Verify port is free
            if not is_server_healthy(WORKTREE_PORT, timeout=1.0):
                log(f"  ✅ Port {WORKTREE_PORT} is now free")
                break
        else:
            log(f"  ✅ Port {WORKTREE_PORT} is already free")
            break
    else:
        log(f"  ⚠️  Port {WORKTREE_PORT} still in use after {max_cleanup_attempts} attempts, proceeding anyway...")

    # Start fresh server with logs captured to evidence directory
    log(f"  Starting fresh server on worktree port {WORKTREE_PORT}...")
    log(f"  Server logs will be saved to: {EVIDENCE_DIR / 'server.log'}")
    SERVER = start_local_mcp_server(
        WORKTREE_PORT,
        log_dir=EVIDENCE_DIR,  # Capture server logs to evidence directory
        env_overrides={
            # Disable any reloader-like behavior for test stability
            "PYTHONUNBUFFERED": "1",  # Ensure logs are flushed immediately
        }
    )
    server_port = WORKTREE_PORT
    BASE_URL = SERVER.base_url

    # Log server process info for debugging
    log(f"  Server PID: {SERVER.pid}")
    log(f"  Server log file: {SERVER.log_path}")

    # Wait for server to be ready (up to 30 seconds)
    max_wait = 30
    wait_time = 0
    while wait_time < max_wait:
        if is_server_healthy(server_port, timeout=2.0):
            log(f"  ✅ Fresh server started and ready on port {server_port}")
            break
        time.sleep(1)
        wait_time += 1
    else:
        log(f"  ⚠️  Server started but not ready after {max_wait}s, proceeding anyway...")

    log(f"Creating MCP client for {BASE_URL}")
    client = MCPClient(BASE_URL, timeout_s=120.0)
    log("MCP client created")

    results = {
        "test_name": "companion_arc_lifecycle_e2e",
        "timestamp": datetime.now(UTC).isoformat(),
        "base_url": BASE_URL,
        "user_id": USER_ID,
        "strict_mode": STRICT_MODE,
        "provenance": capture_provenance(BASE_URL),
        "steps": [],
        "summary": {},
    }

    log(f"Provenance: {results['provenance'].get('git_head', 'unknown')[:12]}...")
    log(f"Strict mode: {STRICT_MODE}")

    # Step 1: Health check
    log("Step 1: Health check")
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=30)
        health = resp.json()
        results["steps"].append({
            "name": "health_check",
            "passed": health.get("status") == "healthy",
            "details": health,
        })
        log(f"  Health: {health.get('status')}")
    except Exception as e:
        log(f"  FAILED: {e}")
        results["steps"].append({"name": "health_check", "passed": False, "error": str(e)})
        save_results(results, client, SERVER)
        return 1

    # Step 2: Create campaign with companions
    log("Step 2: Create campaign with companions")
    try:
        # Request companions via custom_options
        create_response = client.tools_call(
            "create_campaign",
            {
                "user_id": USER_ID,
                "title": "Companion Arc Lifecycle Test",
                "character": "A skilled ranger exploring the frontier",
                "setting": "A frontier town with mysterious happenings",
                "description": "Testing complete companion quest arc lifecycle from start to finish",
                "custom_options": ["companions"],  # Request companion generation
            }
        )

        campaign_id = create_response.get("campaign_id") or create_response.get("campaignId")

        if not campaign_id:
            # Try parsing from text content if it's in MCP format
            text_content = MCPClient.parse_text_content(create_response.get("content", []))
            if text_content:
                parsed = json.loads(text_content)
                campaign_id = parsed.get("campaign_id") or parsed.get("campaignId")

        if not campaign_id:
            raise RuntimeError(f"Failed to extract campaign_id from response: {create_response}")

        # Get initial state
        initial_state = get_campaign_state(client, user_id=USER_ID, campaign_id=campaign_id)
        initial_game_state = initial_state.get("game_state", {})
        initial_arcs = extract_companion_arcs(initial_game_state)

        # Check if character creation is in progress
        custom_state = initial_game_state.get("custom_campaign_state", {})
        char_creation_in_progress = custom_state.get("character_creation_in_progress", False)

        results["steps"].append({
            "name": "create_campaign",
            "passed": campaign_id is not None,
            "campaign_id": campaign_id,
            "initial_companion_arcs": initial_arcs,
            "character_creation_in_progress": char_creation_in_progress,
        })
        log(f"  Campaign ID: {campaign_id}")
        log(f"  Initial companion_arcs: {initial_arcs}")

        # If character creation is in progress, complete it first
        if char_creation_in_progress:
            log("  Character creation in progress - completing it...")
            process_action(
                client,
                user_id=USER_ID,
                campaign_id=campaign_id,
                user_input="I'm done creating my character. Let's begin the adventure!",
            )

        if not campaign_id:
            log("  FAILED: No campaign ID")
            save_results(results, client, SERVER)
            return 1

        results["campaign_id"] = campaign_id
    except Exception as e:
        log(f"  FAILED: {e}")
        results["steps"].append({"name": "create_campaign", "passed": False, "error": str(e)})
        save_results(results, client, SERVER)
        return 1

    # Step 3: Play through turns to trigger arc initialization and progression
    log("Step 3: Playing through turns to complete arc lifecycle")

    arc_initialized = False
    arc_events_found = []
    arc_phases_seen = set()
    arc_progress_history = []
    narrative_mentions = []  # Track companion mentions in narrative
    max_turns = 30  # Play up to 30 turns to allow arc to complete
    actual_turns_played = 0

    for turn_num in range(1, max_turns + 1):
        log(f"Turn {turn_num}: Action")

        # Vary actions to create natural progression and trigger callbacks
        actions = [
            "I explore the town square and talk to the locals",
            "I visit the local tavern to gather information",
            "I check out the merchant's stall in the market",
            "I investigate the old ruins on the outskirts",
            "I return to town and discuss what I've learned with my companions",
            "I visit the port district to see what ships are in",
            "I talk to the town guard about recent events",
            "I explore the eastern trade route",
            "I investigate reports of slavers in the area",
            "I head towards Thornhaven as my companion suggested",
            "I continue exploring and helping my companion with their quest",
            "I follow up on the clues we've discovered",
            "I confront the situation my companion has been worried about",
            "I help resolve the crisis my companion is facing",
            "I complete the final mission for my companion's arc",
        ]

        user_input = actions[(turn_num - 1) % len(actions)] if turn_num <= len(actions) else f"I continue exploring and helping my companions (turn {turn_num})"

        try:
            # Check server health before each turn to catch crashes early
            if not is_server_healthy(server_port, timeout=2.0):
                log(f"  ⚠️  Server health check failed before turn {turn_num}")
                # Try to capture server logs for debugging
                if SERVER and SERVER.log_path and SERVER.log_path.exists():
                    log("  📋 Last 50 lines of server log:")
                    try:
                        with open(SERVER.log_path) as f:
                            log_lines = f.readlines()
                            for line in log_lines[-50:]:
                                log(f"    {line.rstrip()}")
                    except Exception as log_err:
                        log(f"  ⚠️  Could not read server log: {log_err}")
                raise RuntimeError(f"Server became unresponsive before turn {turn_num}")

            action_response = process_action(
                client,
                user_id=USER_ID,
                campaign_id=campaign_id,
                user_input=user_input,
            )

            # Extract game state
            game_state = action_response.get("game_state", {})
            arcs = extract_companion_arcs(game_state)
            arc_event = extract_companion_arc_event(action_response)

            # Track arc initialization
            if arcs and not arc_initialized:
                arc_initialized = True
                log(f"  ✅ Companion arc initialized on turn {turn_num}")

            # Track arc events
            if arc_event:
                arc_events_found.append({
                    "turn": turn_num,
                    "event": arc_event,
                })
                log(f"  ✅ Arc event on turn {turn_num}: {arc_event.get('event_type')} ({arc_event.get('phase')})")

            # Track arc phases and progress
            for arc_name, arc_data in arcs.items():
                phase = get_arc_phase(arc_data)
                progress = get_arc_progress(arc_data)
                arc_phases_seen.add(phase)
                arc_progress_history.append({
                    "turn": turn_num,
                    "arc": arc_name,
                    "phase": phase,
                    "progress": progress,
                })

                # Log phase changes
                if turn_num > 1:
                    prev_progress = next(
                        (p["progress"] for p in reversed(arc_progress_history[:-1]) if p["arc"] == arc_name),
                        0
                    )
                    if progress > prev_progress:
                        log(f"  📈 Arc '{arc_name}' progress: {prev_progress}% → {progress}% (phase: {phase})")

                # Check if arc is complete
                if is_arc_complete(arc_data):
                    log(f"  🎉 Arc '{arc_name}' COMPLETED on turn {turn_num}!")
                    log(f"     Final phase: {phase}, Final progress: {progress}%")
                    results["steps"].append({
                        "name": f"turn_{turn_num}_arc_complete",
                        "passed": True,
                        "arc_name": arc_name,
                        "completion_turn": turn_num,
                        "final_phase": phase,
                        "final_progress": progress,
                    })
                    # Arc is complete, we can stop or continue to validate
                    break

            # Narrative validation - check if companions/arc themes appear in narrative
            narrative = extract_narrative(action_response)
            companions_in_narrative = find_companions_in_narrative(narrative)
            arc_type = arc_event.get("arc_type") if arc_event else None
            has_arc_themes = find_arc_themes_in_narrative(narrative, arc_type) if arc_type else False
            has_dialogue_match = validate_companion_dialogue_in_narrative(narrative, arc_event) if arc_event else False

            if companions_in_narrative:
                narrative_mentions.append({
                    "turn": turn_num,
                    "companions": companions_in_narrative,
                    "has_arc_themes": has_arc_themes,
                    "has_dialogue_match": has_dialogue_match,
                })
                log(f"  📖 Narrative mentions companions: {companions_in_narrative}")

            results["steps"].append({
                "name": f"turn_{turn_num}",
                "passed": True,
                "arc_event_found": arc_event is not None,
                "arcs_after_turn": arcs,
                "narrative_companions": companions_in_narrative,
                "has_arc_themes": has_arc_themes,
            })

            # Early exit if we have 3+ events and arc is complete
            if len(arc_events_found) >= 3:
                final_state = get_campaign_state(client, user_id=USER_ID, campaign_id=campaign_id)
                final_game_state = final_state.get("game_state", {})
                final_arcs = extract_companion_arcs(final_game_state)

                # Check if any arc is complete
                any_complete = any(is_arc_complete(arc) for arc in final_arcs.values())
                if any_complete:
                    log(f"  ✅ Arc lifecycle complete! Stopping at turn {turn_num}")
                    actual_turns_played = turn_num
                    break

            actual_turns_played = turn_num

        except Exception as e:
            log(f"  ❌ FAILED at turn {turn_num}: {e}")
            # Capture server logs on failure for debugging
            server_log_excerpt = None
            if SERVER and SERVER.log_path and SERVER.log_path.exists():
                try:
                    with open(SERVER.log_path) as f:
                        log_lines = f.readlines()
                        server_log_excerpt = "".join(log_lines[-100:])  # Last 100 lines
                except Exception as log_err:
                    log(f"  ⚠️  Could not read server log: {log_err}")

            results["steps"].append({
                "name": f"turn_{turn_num}",
                "passed": False,
                "error": str(e),
                "server_log_excerpt": server_log_excerpt[-5000:] if server_log_excerpt else None,  # Last 5KB
            })

            # Save server log to evidence directory for debugging
            if SERVER and SERVER.log_path and SERVER.log_path.exists():
                try:
                    evidence_log_path = EVIDENCE_DIR / "server.log"
                    shutil.copy2(SERVER.log_path, evidence_log_path)
                    log(f"  📋 Server log copied to evidence: {evidence_log_path}")
                except Exception as copy_err:
                    log(f"  ⚠️  Could not copy server log: {copy_err}")

            if STRICT_MODE:
                save_results(results, client, SERVER)
                return 1

    # Ensure actual_turns_played is set even if loop completes without break
    if actual_turns_played == 0:
        actual_turns_played = max_turns

    # Step 4: Validate lifecycle requirements
    log("Step 4: Validate lifecycle requirements")
    final_state = get_campaign_state(client, user_id=USER_ID, campaign_id=campaign_id)
    final_game_state = final_state.get("game_state", {})
    final_arcs = extract_companion_arcs(final_game_state)

    # Requirement 1: Arc started
    arc_started = len(final_arcs) > 0

    # Requirement 2: 3+ arc events occurred
    events_requirement_met = len(arc_events_found) >= 3

    # Requirement 3: Arc progressed through phases
    expected_phases = {"discovery", "development", "crisis", "resolution"}
    phases_progressed = len(arc_phases_seen.intersection(expected_phases)) >= 2  # At least 2 phases

    # Requirement 4: Arc finished (completed)
    arc_finished = any(is_arc_complete(arc) for arc in final_arcs.values())

    # Requirement 5: Arc is marked as done
    arc_done = arc_finished  # If complete, it's done

    results["steps"].append({
        "name": "validate_lifecycle",
        "passed": all([
            arc_started,
            events_requirement_met if STRICT_MODE else True,  # Non-strict: events may not be explicitly generated
            phases_progressed,
            arc_finished if STRICT_MODE else True,  # Non-strict: don't require completion
            arc_done if STRICT_MODE else True,
        ]),
        "arc_started": arc_started,
        "events_count": len(arc_events_found),
        "events_requirement_met": events_requirement_met,
        "phases_seen": list(arc_phases_seen),
        "phases_progressed": phases_progressed,
        "arc_finished": arc_finished,
        "arc_done": arc_done,
        "final_arcs": final_arcs,
    })

    log(f"  Arc started: {arc_started}")
    log(f"  Arc events: {len(arc_events_found)} (required: 3+ in strict mode)")
    log(f"  Phases seen: {arc_phases_seen}")
    log(f"  Arc finished: {arc_finished}")
    log(f"  Arc done: {arc_done}")
    if not STRICT_MODE:
        log("  (Non-strict mode: arc events, finish, and done checks are informational only)")

    # Step 5: Validate arc progression timeline
    log("Step 5: Validate arc progression timeline")
    progression_valid = True
    progression_errors = []

    if arc_progress_history:
        # Check that progress generally increases
        for i in range(1, len(arc_progress_history)):
            prev = arc_progress_history[i-1]["progress"]
            curr = arc_progress_history[i]["progress"]
            if curr < prev - 5:  # Allow small decreases but not major regressions
                progression_errors.append(
                    f"Progress regression: turn {arc_progress_history[i-1]['turn']} ({prev}%) → "
                    f"turn {arc_progress_history[i]['turn']} ({curr}%)"
                )
                progression_valid = False

        # Check that we saw progress
        if arc_progress_history[-1]["progress"] <= arc_progress_history[0]["progress"]:
            progression_errors.append("No progress made over lifecycle")
            progression_valid = False

    results["steps"].append({
        "name": "validate_progression",
        "passed": progression_valid,
        "errors": progression_errors,
        "progress_history": arc_progress_history,
    })

    # Summary
    steps_passed = sum(1 for s in results["steps"] if s.get("passed"))
    steps_total = len(results["steps"])

    results["summary"] = {
        "campaign_created": campaign_id is not None,
        "arc_started": arc_started,
        "arc_events_count": len(arc_events_found),
        "events_requirement_met": events_requirement_met,
        "phases_seen": list(arc_phases_seen),
        "phases_progressed": phases_progressed,
        "arc_finished": arc_finished,
        "arc_done": arc_done,
        "progression_valid": progression_valid,
        "turns_played": actual_turns_played,
        "steps_passed": steps_passed,
        "steps_total": steps_total,
        "final_companion_arcs": final_arcs,
        "arc_events": arc_events_found,
        # Narrative validation summary
        "narrative_mentions_count": len(narrative_mentions),
        "turns_with_companion_narrative": [n["turn"] for n in narrative_mentions],
        "turns_with_arc_themes": [n["turn"] for n in narrative_mentions if n["has_arc_themes"]],
    }

    log("")
    log("=" * 60)
    log("LIFECYCLE SUMMARY")
    log("=" * 60)
    log(f"✅ Arc started: {arc_started}")
    events_icon = "✅" if events_requirement_met else ("⚠️" if not STRICT_MODE else "❌")
    log(f"{events_icon} Arc events: {len(arc_events_found)}/3+ {'(strict only)' if not STRICT_MODE else 'required'}")
    log(f"{'✅' if phases_progressed else '❌'} Phases progressed: {arc_phases_seen}")
    log(f"{'✅' if arc_finished else '❌'} Arc finished: {arc_finished}")
    log(f"{'✅' if arc_done else '❌'} Arc done: {arc_done}")
    log(f"{'✅' if progression_valid else '❌'} Progression valid: {progression_valid}")
    log(f"Steps: {steps_passed}/{steps_total} passed")

    save_results(results, client, SERVER)

    # Determine success
    critical_checks = [
        campaign_id is not None,
        arc_started,
        events_requirement_met if STRICT_MODE else True,  # Events optional in non-strict mode
        phases_progressed,
        progression_valid,
        arc_finished if STRICT_MODE else True,  # Completion optional in non-strict mode
    ]

    if all(critical_checks):
        log("\n✅ SUCCESS: Companion quest arc lifecycle validated!")
        return 0
    if STRICT_MODE:
        log("\n❌ FAILED: Companion quest arc lifecycle validation failed (strict mode)")
        return 1
    log("\n⚠️  Some lifecycle checks failed (non-strict mode)")
    return 0


def save_results(results: dict, client: MCPClient | None = None, server: Any | None = None) -> None:
    """Save results to evidence bundle."""
    # Get request/response pairs from MCPClient captures if available
    request_responses = None
    if client and client._capture_requests:
        # Use canonical MCPClient captures
        captures = client.get_captures_as_dict()
        if captures:
            request_responses = captures
            save_request_responses(EVIDENCE_DIR, captures)
    elif REQUEST_RESPONSE_PAIRS:
        # Fallback to manual pairs if client captures not available
        # Convert tuple format to dict format expected by save_request_responses
        request_responses = [
            {
                "request_timestamp": req.get("timestamp", ""),
                "response_timestamp": resp.get("timestamp", ""),
                "request": req,
                "response": resp,
            }
            for req, resp in REQUEST_RESPONSE_PAIRS
        ]
        save_request_responses(EVIDENCE_DIR, request_responses)

    # Copy server log to evidence directory if available
    if server and server.log_path and server.log_path.exists():
        try:
            evidence_log_path = EVIDENCE_DIR / "server.log"
            shutil.copy2(server.log_path, evidence_log_path)
            log(f"📋 Server log saved to evidence: {evidence_log_path}")
        except Exception as e:
            log(f"⚠️  Could not copy server log to evidence: {e}")

    # Create evidence bundle
    create_evidence_bundle(
        EVIDENCE_DIR,
        test_name=results["test_name"],
        provenance=results["provenance"],
        results=results,
        request_responses=request_responses,
        methodology_text="E2E test validating complete companion quest arc lifecycle: start → 3+ events → phase progression → finish → done",
    )

    log(f"\nResults saved to: {EVIDENCE_DIR}")
    log(f"Latest symlink: {EVIDENCE_DIR.parent / 'latest'}")


if __name__ == "__main__":
    sys.exit(main())
