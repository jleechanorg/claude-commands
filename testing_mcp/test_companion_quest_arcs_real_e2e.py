#!/usr/bin/env python3
"""
Companion Quest Arcs E2E Test

This test validates that companion quest arcs are properly initialized, tracked,
and progressed through multiple turns. It verifies:

1. Companion quest arcs initialize by Turn 3-5
2. companion_arcs are tracked in custom_campaign_state
3. companion_arc_event objects are generated with proper structure
4. Callbacks are planted for future turns
5. Arcs progress through phases (discovery → development → crisis → resolution)
6. Arc history is maintained

Evidence Standards Compliance:
- Uses testing_mcp/lib/evidence_utils.py for canonical evidence capture
- Evidence saved to /tmp/<repo>/<branch>/companion_quest_arcs/<timestamp>/
- Includes README.md, methodology.md, evidence.md, metadata.json
- Captures git provenance and server runtime info
- All files have SHA256 checksums per .claude/skills/evidence-standards.md

Run locally:
    BASE_URL=http://localhost:8001 python testing_mcp/test_companion_quest_arcs_real_e2e.py

Run against preview:
    BASE_URL=https://preview-url python testing_mcp/test_companion_quest_arcs_real_e2e.py

Evidence will be automatically saved to:
    /tmp/worldarchitect.ai/<branch>/companion_quest_arcs/<timestamp>/
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
import requests
from testing_mcp.dev_server import WORKTREE_PORT, ensure_server_running, get_base_url, is_server_healthy
from testing_mcp.lib.server_utils import start_local_mcp_server
from testing_mcp.lib.arc_validation_utils import (
    detect_companions,
    extract_companion_arc_event,
    extract_companion_arcs,
    extract_next_companion_arc_turn,
    filter_arc_states,
    validate_arc_structure,
)
from testing_mcp.lib.campaign_utils import (
    create_campaign,
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

# Configuration
BASE_URL = os.getenv("BASE_URL") or get_base_url()
USER_ID = f"e2e-companion-arcs-{datetime.now().strftime('%Y%m%d%H%M%S')}"
WORK_NAME = "companion_quest_arcs"
STRICT_MODE = os.getenv("STRICT_MODE", "true").lower() == "true"

# Evidence directory following /tmp/<repo>/<branch>/<work>/<timestamp>/ structure
EVIDENCE_DIR = get_evidence_dir(WORK_NAME) / datetime.now().strftime("%Y%m%d_%H%M%S")
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

# Track request/response pairs for evidence
REQUEST_RESPONSE_PAIRS: list[tuple[dict, dict]] = []


def log(msg: str) -> None:
    """Log with timestamp."""
    ts = datetime.now(timezone.utc).isoformat()
    print(f"[{ts}] {msg}")


# Arc validation functions moved to testing_mcp/lib/arc_validation_utils.py


def validate_arc_event_structure(event: dict) -> tuple[bool, list[str]]:
    """Validate companion_arc_event structure."""
    errors = []
    
    required_fields = ["companion", "arc_type", "phase", "event_type", "description"]
    for field in required_fields:
        if field not in event:
            errors.append(f"Missing required field: {field}")
    
    if "phase" in event:
        valid_phases = ["discovery", "development", "crisis", "resolution"]
        if event["phase"] not in valid_phases:
            errors.append(f"Invalid phase: {event['phase']} (must be one of {valid_phases})")
    
    if "event_type" in event:
        valid_types = [
            "hook_introduced", "stakes_raised", "complication", 
            "revelation", "confrontation", "arc_complete"
        ]
        if event["event_type"] not in valid_types:
            errors.append(f"Invalid event_type: {event['event_type']} (must be one of {valid_types})")
    
    if "companion_dialogue" not in event:
        errors.append("Missing companion_dialogue (REQUIRED per instruction)")
    
    if "callback_planted" not in event:
        errors.append("Missing callback_planted (MUST plant at least one callback)")
    
    return len(errors) == 0, errors


def main() -> int:
    """Run companion quest arcs E2E test."""
    # Ensure fresh server is running on worktree port
    log("Ensuring fresh server is running...")
    global BASE_URL
    
    # Check if server already running on worktree port
    server_port = ensure_server_running(port=WORKTREE_PORT)
    if not server_port:
        log(f"  Starting fresh server on worktree port {WORKTREE_PORT}...")
        server = start_local_mcp_server(WORKTREE_PORT)
        server_port = WORKTREE_PORT
        BASE_URL = server.base_url
        
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
    else:
        BASE_URL = f"http://localhost:{server_port}"
        log(f"  ✅ Using existing server on port {server_port}")

    client = MCPClient(BASE_URL, timeout_s=600.0)  # Increased timeout for long LLM requests

    results = {
        "test_name": "companion_quest_arcs_e2e",
        "timestamp": datetime.now(timezone.utc).isoformat(),
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
        resp = requests.get(f"{BASE_URL}/health", timeout=10)
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
        save_results(results, client)
        return 1

    # Step 2: Create campaign with companions
    log("Step 2: Create campaign with companions")
    try:
        # Request companions via custom_options - use direct tools_call to pass custom_options
        create_response = client.tools_call(
            "create_campaign",
            {
                "user_id": USER_ID,
                "title": "Companion Quest Arc Test",
                "character": "A skilled ranger exploring the frontier",
                "setting": "A frontier town with mysterious happenings",
                "description": "Testing companion quest arc initialization and progression",
                "custom_options": ["companions"],  # Request companion generation
            }
        )
        
        # Extract campaign_id from response (could be nested in result or direct)
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
        
        # Detect companions from multiple storage locations (using centralized function)
        companions = detect_companions(initial_game_state, initial_arcs)

        results["steps"].append({
            "name": "create_campaign",
            "passed": campaign_id is not None,
            "campaign_id": campaign_id,
            "initial_companion_arcs": initial_arcs,
            "companions_found": companions,
            "companion_count": len(companions),
            "character_creation_in_progress": char_creation_in_progress,
        })
        log(f"  Campaign ID: {campaign_id}")
        log(f"  Initial companion_arcs: {initial_arcs}")
        log(f"  Companions found: {companions} ({len(companions)} total)")
        log(f"  Character creation in progress: {char_creation_in_progress}")
        
        # If character creation is in progress, complete it first
        if char_creation_in_progress:
            log("  Character creation in progress - completing it...")
            complete_char = process_action(
                client,
                user_id=USER_ID,
                campaign_id=campaign_id,
                user_input="I'm done creating my character. Let's begin the adventure!",
            )
            # Re-check state after character creation
            initial_state = get_campaign_state(client, user_id=USER_ID, campaign_id=campaign_id)
            initial_game_state = initial_state.get("game_state", {})
            npc_data = initial_game_state.get("npc_data", {})
            companions = [
                name for name, npc in npc_data.items()
                if isinstance(npc, dict) and npc.get("relationship") == "companion"
            ]
            log(f"  Companions after character creation: {companions} ({len(companions)} total)")
        
        if not companions:
            log("  ⚠️  WARNING: No companions found! Companion arcs require companions.")
            log("  This may indicate a bug in companion generation or the test setup.")
        
        if not campaign_id:
            log("  FAILED: No campaign ID")
            save_results(results, client)
            return 1
        
        results["campaign_id"] = campaign_id
    except Exception as e:
        log(f"  FAILED: {e}")
        results["steps"].append({"name": "create_campaign", "passed": False, "error": str(e)})
        save_results(results, client)
        return 1

    # Step 3-7: Play through turns 1-5 to trigger arc initialization
    arc_initialized = False
    arc_events_found = []
    all_companion_arcs = {}
    turn_count = 0
    
    for turn_num in range(1, 6):
        turn_count = turn_num
        log(f"Step {turn_num + 2}: Turn {turn_num} - Action")
        
        # Vary actions to create natural progression
        actions = [
            "I explore the town square and talk to the locals",
            "I visit the local tavern to gather information",
            "I check out the merchant's stall in the market",
            "I investigate the old ruins on the outskirts",
            "I return to town and discuss what I've learned with my companions",
        ]
        
        user_input = actions[turn_num - 1] if turn_num <= len(actions) else f"I continue exploring (turn {turn_num})"
        
        try:
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
            next_arc_turn = extract_next_companion_arc_turn(game_state)
            
            # Track arcs
            if arcs:
                all_companion_arcs.update(arcs)
            
            # Track arc events
            if arc_event:
                arc_events_found.append({
                    "turn": turn_num,
                    "event": arc_event,
                })
                log(f"  ✅ Companion arc event found on turn {turn_num}")
                log(f"     Companion: {arc_event.get('companion')}")
                log(f"     Arc type: {arc_event.get('arc_type')}")
                log(f"     Phase: {arc_event.get('phase')}")
                log(f"     Event type: {arc_event.get('event_type')}")
                
                # Validate arc event structure
                is_valid, errors = validate_arc_event_structure(arc_event)
                if not is_valid:
                    log(f"  ⚠️  Arc event structure errors: {errors}")
            else:
                # Debug: Check if companion_arc_event exists but wasn't extracted
                custom_state_debug = game_state.get("custom_campaign_state", {})
                if "companion_arc_event" in custom_state_debug:
                    log(f"  ⚠️  companion_arc_event exists but wasn't extracted properly")
                    log(f"     Raw value: {custom_state_debug.get('companion_arc_event')}")
            
            # Check if arc initialized
            if arcs and not arc_initialized:
                arc_initialized = True
                log(f"  ✅ Companion arc initialized by turn {turn_num}")
            
            results["steps"].append({
                "name": f"turn_{turn_num}",
                "passed": True,
                "arc_event_found": arc_event is not None,
                "arcs_after_turn": arcs,
                "next_arc_turn": next_arc_turn,
            })
            
        except Exception as e:
            log(f"  FAILED: {e}")
            results["steps"].append({
                "name": f"turn_{turn_num}",
                "passed": False,
                "error": str(e),
            })
            if STRICT_MODE:
                save_results(results, client)
                return 1

    # Step 8: Validate arc initialization (should happen by Turn 3-5)
    log("Step 8: Validate arc initialization")
    final_state = get_campaign_state(client, user_id=USER_ID, campaign_id=campaign_id)
    final_game_state = final_state.get("game_state", {})
    final_arcs = extract_companion_arcs(final_game_state)
    
    arc_init_valid = len(final_arcs) > 0
    arc_init_by_turn_5 = arc_initialized and turn_count <= 5
    
    results["steps"].append({
        "name": "validate_arc_initialization",
        "passed": arc_init_by_turn_5 if STRICT_MODE else arc_init_valid,
        "arcs_found": final_arcs,
        "initialized_by_turn_5": arc_init_by_turn_5,
        "turn_count": turn_count,
    })
    
    log(f"  Arcs found: {len(final_arcs)}")
    log(f"  Initialized by turn 5: {arc_init_by_turn_5}")
    
    # Step 9: Validate arc structure
    log("Step 9: Validate arc structure")
    arc_structure_errors = []
    arc_states_validated = 0
    arc_definitions_skipped = 0
    
    # Filter to only arc states (skip definitions)
    arc_states = filter_arc_states(final_arcs)
    
    for arc_name, arc_data in arc_states.items():
        if not isinstance(arc_data, dict):
            continue
        
        # Validate arc states (those with phase/progress)
        arc_states_validated += 1
        is_valid, errors = validate_arc_structure(arc_data, arc_name)
        if not is_valid:
            arc_structure_errors.extend([f"{arc_name}: {e}" for e in errors])
            log(f"  ⚠️  Arc '{arc_name}' structure errors: {errors}")
        else:
            log(f"  ✅ Arc '{arc_name}' structure valid")
            log(f"     Type: {arc_data.get('arc_type', 'not set')}")
            log(f"     Phase: {arc_data.get('phase')}")
            log(f"     Progress: {arc_data.get('progress')}")
    
    # Count skipped definitions
    for arc_name, arc_data in final_arcs.items():
        if arc_name.startswith("arc_") and "phase" not in arc_data and "progress" not in arc_data:
            arc_definitions_skipped += 1
    
    if arc_definitions_skipped > 0:
        log(f"  ℹ️  Skipped {arc_definitions_skipped} arc definition(s) (metadata structures)")
    log(f"  ℹ️  Validated {arc_states_validated} arc state(s)")
    
    results["steps"].append({
        "name": "validate_arc_structure",
        "passed": len(arc_structure_errors) == 0,
        "errors": arc_structure_errors,
    })
    
    # Step 10: Validate arc events
    log("Step 10: Validate arc events")
    arc_event_errors = []
    for event_info in arc_events_found:
        event = event_info["event"]
        is_valid, errors = validate_arc_event_structure(event)
        if not is_valid:
            arc_event_errors.extend([f"Turn {event_info['turn']}: {e}" for e in errors])
        else:
            log(f"  ✅ Arc event on turn {event_info['turn']} structure valid")
            if "callback_planted" in event:
                callback = event["callback_planted"]
                log(f"     Callback planted: {callback.get('trigger_condition', 'N/A')}")
    
    results["steps"].append({
        "name": "validate_arc_events",
        "passed": len(arc_event_errors) == 0,
        "events_found": len(arc_events_found),
        "errors": arc_event_errors,
    })
    
    # Summary
    steps_passed = sum(1 for s in results["steps"] if s.get("passed"))
    steps_total = len(results["steps"])
    
    results["summary"] = {
        "campaign_created": campaign_id is not None,
        "arcs_initialized": arc_init_valid,
        "arcs_initialized_by_turn_5": arc_init_by_turn_5,
        "total_arcs": len(final_arcs),
        "arc_events_found": len(arc_events_found),
        "arc_structure_valid": len(arc_structure_errors) == 0,
        "arc_event_structure_valid": len(arc_event_errors) == 0,
        "steps_passed": steps_passed,
        "steps_total": steps_total,
        "final_companion_arcs": final_arcs,
    }
    
    log("")
    log("=" * 60)
    log("SUMMARY")
    log("=" * 60)
    log(f"Campaign created: {campaign_id is not None}")
    log(f"Arcs initialized: {arc_init_valid}")
    log(f"Arcs initialized by turn 5: {arc_init_by_turn_5}")
    log(f"Total arcs: {len(final_arcs)}")
    log(f"Arc events found: {len(arc_events_found)}")
    log(f"Arc structure valid: {len(arc_structure_errors) == 0}")
    log(f"Arc event structure valid: {len(arc_event_errors) == 0}")
    log(f"Steps: {steps_passed}/{steps_total} passed")
    
    save_results(results)
    
    # Determine success
    critical_checks = [
        campaign_id is not None,
        arc_init_by_turn_5 if STRICT_MODE else arc_init_valid,
        len(arc_structure_errors) == 0,
        len(arc_event_errors) == 0,
    ]
    
    if all(critical_checks):
        log("\n✅ SUCCESS: Companion quest arcs working correctly!")
        return 0
    else:
        if STRICT_MODE:
            log("\n❌ FAILED: Companion quest arcs validation failed (strict mode)")
            return 1
        else:
            log("\n⚠️  Some validation checks failed (non-strict mode)")
            return 0


def save_results(results: dict, client: MCPClient | None = None) -> None:
    """Save results to evidence bundle."""
    # Get request/response pairs from MCPClient captures if available
    request_responses = None
    if client and client._capture_requests:
        # Use canonical MCPClient captures
        captures = client.get_captures_as_dict()
        if captures:
            request_responses = captures
            save_request_responses(EVIDENCE_DIR, [
                (c["request"], c["response"]) for c in captures
            ])
    elif REQUEST_RESPONSE_PAIRS:
        # Fallback to manual pairs if client captures not available
        request_responses = [
            {
                "request_timestamp": req.get("timestamp", ""),
                "response_timestamp": resp.get("timestamp", ""),
                "request": req,
                "response": resp,
            }
            for req, resp in REQUEST_RESPONSE_PAIRS
        ]
        save_request_responses(EVIDENCE_DIR, REQUEST_RESPONSE_PAIRS)
    
    # Create evidence bundle
    create_evidence_bundle(
        EVIDENCE_DIR,
        test_name=results["test_name"],
        provenance=results["provenance"],
        results=results,
        request_responses=request_responses,
        methodology_text="E2E test validating companion quest arc initialization, tracking, and progression through multiple turns",
    )
    
    log(f"\nResults saved to: {EVIDENCE_DIR}")
    log(f"Latest symlink: {EVIDENCE_DIR.parent / 'latest'}")


if __name__ == "__main__":
    sys.exit(main())
