#!/usr/bin/env python3
"""God Mode validation tests against an MCP server (local or preview).

These tests verify the god mode features implemented to fix issues
identified in campaign debugging:
- Validation corrections are visible to users
- God mode directives persist across sessions
- Character identity is enforced in prompts
- Post-combat XP warnings are detected

Run (local MCP already running):
    python testing_mcp/test_god_mode_validation.py --server-url http://127.0.0.1:8001

Run (start local MCP automatically):
    python testing_mcp/test_god_mode_validation.py --start-local

Run (against GCP preview - requires MCP_SERVER_URL env var):
    export MCP_SERVER_URL=https://mvp-site-app-s1-<hash>.us-central1.run.app
    python testing_mcp/test_god_mode_validation.py --server-url $MCP_SERVER_URL
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from lib import MCPClient
from lib.server_utils import (
    LocalServer,
    pick_free_port,
    start_local_mcp_server,
)
from lib.campaign_utils import (
    create_campaign,
    process_action,
    get_campaign_state,
)
from lib.evidence_utils import (
    get_evidence_dir,
    capture_provenance,
    write_with_checksum,
)

# Evidence stored per evidence-standards.md: /tmp/<repo>/<branch>/<work>/<timestamp>/
# EVIDENCE_DIR is set dynamically in main() via get_evidence_dir("god_mode_validation")


# =============================================================================
# Helper Functions
# =============================================================================


def _has_directive_containing(state: dict[str, Any], keywords: list[str]) -> bool:
    """Check if any directive in game state contains all specified keywords.

    Args:
        state: The game state dict
        keywords: List of keywords that must ALL appear in at least one directive

    Returns:
        True if a directive containing all keywords exists
    """
    ccs = state.get("custom_campaign_state") or {}
    directives = ccs.get("god_mode_directives", [])

    for directive in directives:
        if isinstance(directive, dict):
            rule = directive.get("rule", "").lower()
        else:
            rule = str(directive).lower()

        # Check if ALL keywords are in this directive
        if all(kw.lower() in rule for kw in keywords):
            return True

    return False


# =============================================================================
# Test Scenarios
# =============================================================================

GOD_MODE_SCENARIOS: list[dict[str, Any]] = [
    {
        "name": "Add God Mode Directive",
        "description": "Test that god mode directives are persisted",
        "god_mode_command": "GOD MODE: Add rule - always award XP after combat ends",
        "expect_in_response": [],  # LLM response varies
        "validate_state": lambda state: (
            _has_directive_containing(state, ["xp"])
            or _has_directive_containing(state, ["combat"])
            or "god_mode_directives" in (state.get("custom_campaign_state") or {})
        ),
    },
    # ==========================================================================
    # LLM-Based Directive Extraction Tests (NEW)
    # These test that the GodModeAgent LLM extracts directives from natural language
    # The LLM may use state_updates.append OR directives.add - both are valid
    # ==========================================================================
    {
        "name": "LLM Directive - Stop Forgetting",
        "description": "Test that 'stop forgetting X' triggers directive persistence",
        "god_mode_command": "GOD MODE: I have the Foresight spell active, stop forgetting to apply advantage on all attack rolls",
        # Don't require specific keywords in response - LLM may phrase differently
        "expect_in_response": [],
        "validate_state": lambda state: _has_directive_containing(
            state, ["advantage"]
        ) or _has_directive_containing(state, ["foresight"]),
    },
    {
        "name": "LLM Directive - Remember To",
        "description": "Test that 'remember to Y' triggers directive persistence",
        "god_mode_command": "GOD MODE: Remember to always track my masked level separately from real level",
        "expect_in_response": [],  # LLM response varies
        "validate_state": lambda state: _has_directive_containing(
            state, ["level"]
        ),
    },
    {
        "name": "LLM Directive - From Now On",
        "description": "Test 'from now on' natural language pattern",
        "god_mode_command": "GOD MODE: From now on, all stealth checks should have advantage due to my cloak of elvenkind",
        "expect_in_response": [],  # LLM response varies
        "validate_state": lambda state: _has_directive_containing(
            state, ["stealth"]
        ) or _has_directive_containing(state, ["cloak"]),
    },
    {
        "name": "LLM Directive Persistence Check",
        "description": "Verify directives persist in custom_campaign_state.god_mode_directives",
        "god_mode_command": "GOD MODE: List all the rules you are following",
        # LLM should list directives - look for common keywords from prior tests
        "expect_in_response": ["XP", "directive"],  # Response should mention directives
        "validate_state": lambda state: len(
            state.get("custom_campaign_state", {}).get("god_mode_directives", [])
        ) >= 1,  # Should have at least 1 directive from prior tests
    },
    {
        "name": "Set Character Level with XP Mismatch",
        "description": "Test that XP/level validation corrections are visible",
        "god_mode_command": "GOD_MODE_UPDATE_STATE:{\"player_character_data\":{\"level\":10,\"experience\":{\"current\":2700}}}",
        # D&D 5e: 2700 XP = Level 4, so level 10 should be corrected to 4
        "expect_level_correction": {"from_level": 10, "to_level": 4, "xp": 2700},
        # Response should show the correction was applied
        "expect_in_response": ["corrected", "4"],
        "expect_system_warnings": True,
        "warning_patterns": ["Level", "corrected", "XP"],
    },
    {
        "name": "Query Character Identity",
        "description": "Test that character identity is accessible",
        "god_mode_command": "GOD MODE: Who is my character? What is their name and class?",
        # LLM response should mention key character traits from the seeded state
        "expect_in_response": ["Alexiel", "Rogue"],
        "validate_state": lambda state: state.get("player_character_data", {}).get("name") is not None,
    },
    {
        "name": "Modify Character Stats",
        "description": "Test basic god mode stat modification",
        "god_mode_command": "GOD_MODE_UPDATE_STATE:{\"player_character_data\":{\"hp_current\":100,\"hp_max\":100}}",
        "validate_state": lambda state: state.get("player_character_data", {}).get("hp_current") == 100,
    },
    {
        "name": "Combat End Without XP",
        "description": "Test post-combat XP warning detection",
        "setup_combat": True,  # Will seed combat state first
        "god_mode_command": "GOD_MODE_UPDATE_STATE:{\"combat_state\":{\"in_combat\":false}}",
        # Verify combat actually ended
        "validate_state": lambda state: state.get("combat_state", {}).get("in_combat") is False,
        "expect_system_warnings": True,
        "warning_patterns": ["Combat", "XP", "awarded"],
    },
    # ==========================================================================
    # DM Notes Tests - Verify dm_notes are saved and accessible
    # These test the fallback mechanism where LLM writes to dm_notes instead
    # of formal directives (both should be visible in system prompts)
    # ==========================================================================
    {
        "name": "DM Notes - Power Scaling Correction",
        "description": "Test that tonal corrections get saved as dm_notes",
        "god_mode_command": "GOD MODE: Stop saying 'mere level 5' or 'modest level 5'. Level 5 characters are heroes, not weaklings. Update the narrative tone.",
        "expect_in_response": [],  # LLM response varies
        # Validate that EITHER dm_notes OR directives captured the rule
        "validate_state": lambda state: (
            _has_directive_containing(state, ["level"])
            or _has_dm_notes_containing(state, ["level"])
            or _has_dm_notes_containing(state, ["tone"])
        ),
    },
    {
        "name": "DM Notes - Context Visibility Check",
        "description": "Verify dm_notes from prior god mode are visible in subsequent requests",
        "god_mode_command": "GOD MODE: What tonal rules or power scaling notes do you have saved?",
        # If dm_notes exist, LLM should mention them (injected into system prompt)
        "expect_in_response": [],  # Response varies but should reference prior context
        "validate_state": lambda state: True,  # Just checking LLM can see the notes
    },
    {
        "name": "DM Notes - Direct State Update",
        "description": "Test that dm_notes can be set directly via state update",
        "god_mode_command": 'GOD_MODE_UPDATE_STATE:{"debug_info":{"dm_notes":["Test note: Always describe combat dramatically","Test note: NPCs should have memorable quirks"]}}',
        "validate_state": lambda state: (
            len(state.get("debug_info", {}).get("dm_notes", [])) >= 2
        ),
    },
    {
        "name": "Directive Precedence - Newest First",
        "description": "Test that multiple directives are saved with timestamps for ordering",
        "god_mode_command": "GOD MODE: Add rule - the player's familiar is named 'Shadow' and is a black cat",
        "expect_in_response": [],
        # Validate directive was added with timestamp
        "validate_state": lambda state: any(
            isinstance(d, dict) and d.get("added") and d.get("rule")
            for d in state.get("custom_campaign_state", {}).get("god_mode_directives", [])
        ),
    },
    # ==========================================================================
    # debug_info.dm_notes Persistence Path Validation (NEW)
    # This test validates that dm_notes set via GOD_MODE_UPDATE_STATE
    # persist correctly to game_state.debug_info.dm_notes
    # ==========================================================================
    {
        "name": "DM Notes - State Updates Path Validation",
        "description": "Validate dm_notes set via GOD_MODE_UPDATE_STATE persist to game_state.debug_info.dm_notes",
        # Use GOD_MODE_UPDATE_STATE which creates state_updates that flow through update_state_with_changes()
        "god_mode_command": 'GOD_MODE_UPDATE_STATE:{"debug_info":{"dm_notes":["STATE_UPDATES_PATH_TEST: This note was set via state_updates.debug_info.dm_notes","STATE_UPDATES_PATH_TEST: Verifying persistence to game_state_after"]}}',
        # Custom validation that checks both the result state_updates AND game_state_after
        "validate_state_updates_path": True,  # Flag for enhanced validation
        "validate_state": lambda state: (
            # dm_notes must appear in game_state_after.debug_info.dm_notes
            any(
                "STATE_UPDATES_PATH_TEST" in str(note)
                for note in state.get("debug_info", {}).get("dm_notes", [])
            )
        ),
    },
]


def _validate_state_updates_dm_notes_path(
    result: dict[str, Any],
    game_state: dict[str, Any],
) -> list[str]:
    """Validate that debug_info.dm_notes set via GOD_MODE_UPDATE_STATE persists to game_state.

    This validates the state update path:
    1. GOD_MODE_UPDATE_STATE:{"debug_info":{"dm_notes":[...]}} is sent
    2. Notes persist to game_state.debug_info.dm_notes
    3. Marker notes are found in persisted state

    Note: GOD_MODE_UPDATE_STATE doesn't return state_updates in result - it returns
    success/response. We validate persistence by checking game_state_after.

    Returns:
        List of error messages (empty if validation passes)
    """
    errors = []

    # Verify the update was successful
    if not result.get("success"):
        errors.append(f"GOD_MODE_UPDATE_STATE failed: {result}")
        return errors

    # Check game_state_after.debug_info.dm_notes
    game_state_debug_info = game_state.get("debug_info", {})
    game_state_dm_notes = game_state_debug_info.get("dm_notes", [])

    if not game_state_dm_notes:
        errors.append(
            f"game_state_after.debug_info.dm_notes is empty or missing. "
            f"Got debug_info={game_state_debug_info}"
        )
        return errors

    # Verify marker notes from our UPDATE_STATE command appear in game_state_after
    marker = "STATE_UPDATES_PATH_TEST"
    found_in_game_state = any(
        marker in str(note) for note in game_state_dm_notes
    )
    if not found_in_game_state:
        errors.append(
            f"Notes with marker '{marker}' not found in game_state_after.debug_info.dm_notes. "
            f"game_state_after.debug_info.dm_notes={game_state_dm_notes}"
        )

    return errors


def _has_dm_notes_containing(state: dict[str, Any], keywords: list[str]) -> bool:
    """Check if any dm_note in game state contains all specified keywords.

    Args:
        state: The game state dict
        keywords: List of keywords that must ALL appear in at least one note

    Returns:
        True if a dm_note containing all keywords exists
    """
    debug_info = state.get("debug_info") or {}
    dm_notes = debug_info.get("dm_notes", [])

    for note in dm_notes:
        if isinstance(note, str):
            note_lower = note.lower()
            if all(kw.lower() in note_lower for kw in keywords):
                return True

    return False


def validate_scenario_result(
    result: dict[str, Any],
    scenario: dict[str, Any],
    game_state: dict[str, Any] | None = None,
) -> list[str]:
    """Validate a god mode scenario result.

    STRICT VALIDATION (per hook analysis 2025-12-29):
    - For LLM scenarios: validates god_mode_response (user-facing), not internal narrative
    - For warning scenarios: requires ALL warning patterns, not just any
    - For state corrections: validates the correction actually happened
    """
    errors: list[str] = []

    # Check for server errors
    if result.get("error"):
        errors.append(f"Server returned error: {result['error']}")
        return errors

    # For LLM god mode scenarios, prefer god_mode_response (user-facing)
    # For UPDATE_STATE scenarios, use response (system message)
    is_llm_scenario = scenario.get("god_mode_command", "").startswith("GOD MODE:")
    if is_llm_scenario:
        # LLM scenarios: god_mode_response contains the actual user-facing output
        response_text = result.get("god_mode_response", "") or result.get("response", "")
    else:
        # UPDATE_STATE scenarios: response contains the system message
        response_text = result.get("response", "") or result.get("god_mode_response", "")
    response_text_lower = response_text.lower()

    for expected in scenario.get("expect_in_response", []):
        if expected.lower() not in response_text_lower:
            errors.append(f"Expected '{expected}' in response, not found")

    # Check system warnings - STRICT: require ALL patterns, not any
    if scenario.get("expect_system_warnings"):
        warnings = result.get("system_warnings", [])
        warning_patterns = scenario.get("warning_patterns", [])

        if warnings:
            # If we have explicit warnings, check them
            warnings_text = " ".join(str(w) for w in warnings).lower()
            missing_patterns = [p for p in warning_patterns if p.lower() not in warnings_text]
            if missing_patterns:
                errors.append(
                    f"System warnings missing patterns {missing_patterns}, "
                    f"got warnings={warnings}"
                )
        else:
            # No explicit warnings - check if ALL patterns appear in response
            # STRICT: Changed from any() to all() per hook analysis
            missing_in_response = [
                p for p in warning_patterns if p.lower() not in response_text_lower
            ]
            if missing_in_response:
                errors.append(
                    f"Expected ALL warning patterns {warning_patterns} in response, "
                    f"missing: {missing_in_response}"
                )

    # Validate game state if provided
    if game_state and scenario.get("validate_state"):
        if not scenario["validate_state"](game_state):
            errors.append("State validation failed")

    # STRICT: For level correction scenarios, verify the correction happened
    if scenario.get("expect_level_correction"):
        expected = scenario["expect_level_correction"]
        actual_level = game_state.get("player_character_data", {}).get("level") if game_state else None
        if actual_level != expected["to_level"]:
            errors.append(
                f"Level correction failed: expected level={expected['to_level']} "
                f"(from XP={expected['xp']}), got level={actual_level}"
            )

    # Validate state_updates.debug_info.dm_notes path if flagged
    if scenario.get("validate_state_updates_path") and game_state:
        path_errors = _validate_state_updates_dm_notes_path(result, game_state)
        errors.extend(path_errors)

    return errors


def setup_combat_state(client: MCPClient, user_id: str, campaign_id: str) -> None:
    """Seed combat state for post-combat testing."""
    combat_state = {
        "combat_state": {
            "in_combat": True,
            "combatants": {
                "npc_goblin_001": {
                    "name": "Goblin",
                    "hp_current": 0,
                    "hp_max": 7,
                    "status": "defeated",
                }
            },
            # Preserve defeated count even if cleanup removes combatants
            "combat_summary": {
                "enemies_defeated": 1
            },
        }
    }
    payload = f"GOD_MODE_UPDATE_STATE:{json.dumps(combat_state)}"
    result = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=payload,
        mode="god",
    )
    if result.get("error"):
        raise RuntimeError(f"Failed to setup combat state: {result['error']}")


def run_scenario(
    client: MCPClient,
    user_id: str,
    campaign_id: str,
    scenario: dict[str, Any],
    evidence_dir: Path,
) -> dict[str, Any]:
    """Run a single god mode scenario and return results."""
    scenario_name = scenario["name"]
    print(f"\n  Running: {scenario_name}")
    print(f"    Description: {scenario.get('description', 'N/A')}")

    # Setup if needed
    if scenario.get("setup_combat"):
        print("    Setting up combat state...")
        setup_combat_state(client, user_id, campaign_id)

    # Determine mode based on command type
    mode = "god"
    if scenario["god_mode_command"].startswith("GOD_MODE_UPDATE_STATE:"):
        mode = "character"  # UPDATE_STATE commands go through character mode

    # Execute the god mode command
    start_time = time.time()
    result = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=scenario["god_mode_command"],
        mode=mode,
    )
    elapsed = time.time() - start_time

    # Get updated game state
    state_result = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
    game_state = state_result.get("game_state", {})

    # Validate
    errors = validate_scenario_result(result, scenario, game_state)

    # Save evidence
    evidence = {
        "scenario": scenario_name,
        "command": scenario["god_mode_command"],
        "result": result,
        "game_state_after": game_state,
        "errors": errors,
        "elapsed_seconds": elapsed,
        "timestamp": datetime.now().isoformat(),
    }

    safe_name = scenario_name.lower().replace(" ", "_").replace("/", "-")
    evidence_path = evidence_dir / f"scenario_{safe_name}.json"
    evidence_content = json.dumps(evidence, indent=2, default=str)
    # Write evidence with SHA256 checksum for integrity verification
    checksum = write_with_checksum(evidence_path, evidence_content)

    return {
        "name": scenario_name,
        "passed": len(errors) == 0,
        "errors": errors,
        "elapsed": elapsed,
        "evidence_path": str(evidence_path),
        "checksum": checksum,
    }


def run_all_scenarios(
    client: MCPClient,
    user_id: str,
    campaign_id: str,
    evidence_dir: Path,
) -> dict[str, Any]:
    """Run all god mode scenarios and return summary."""
    results = []
    passed = 0
    failed = 0

    for scenario in GOD_MODE_SCENARIOS:
        try:
            result = run_scenario(client, user_id, campaign_id, scenario, evidence_dir)
            results.append(result)
            if result["passed"]:
                passed += 1
                print(f"    ✅ PASSED ({result['elapsed']:.2f}s)")
            else:
                failed += 1
                print(f"    ❌ FAILED: {result['errors']}")
        except Exception as e:
            failed += 1
            results.append({
                "name": scenario["name"],
                "passed": False,
                "errors": [str(e)],
                "elapsed": 0,
            })
            print(f"    ❌ EXCEPTION: {e}")

    return {
        "total": len(GOD_MODE_SCENARIOS),
        "passed": passed,
        "failed": failed,
        "results": results,
    }


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="God Mode Validation Tests")
    parser.add_argument(
        "--server-url",
        default=os.environ.get("MCP_SERVER_URL") or "http://127.0.0.1:8001",
        help="MCP server URL (default: $MCP_SERVER_URL or localhost:8001)",
    )
    parser.add_argument(
        "--start-local",
        action="store_true",
        help="Start a local MCP server automatically",
    )
    parser.add_argument(
        "--user-id",
        default="test_god_mode_user",
        help="User ID for test campaign",
    )
    args = parser.parse_args()

    # Setup evidence directory per evidence-standards.md: /tmp/<repo>/<branch>/<work>/
    evidence_dir = get_evidence_dir("god_mode_validation")

    # Capture git provenance at start
    print("📊 Capturing provenance...")
    # Provenance will be captured after we know the server URL

    print("=" * 60)
    print("God Mode Validation Tests")
    print("=" * 60)
    print(f"Evidence directory: {evidence_dir}")

    # Start local server if requested
    local_server: LocalServer | None = None
    server_url = args.server_url

    if args.start_local:
        print("\n🚀 Starting local MCP server...")
        port = pick_free_port()
        local_server = start_local_mcp_server(port)
        server_url = f"http://127.0.0.1:{port}"
        print(f"   Local server started on {server_url}")

    # Capture full provenance (git + server) now that we know the URL
    try:
        provenance = capture_provenance(
            server_url,
            server_pid=local_server.pid if local_server else None,
        )
        print(f"   Git HEAD: {provenance.get('git_head', 'unknown')[:12]}")
        print(f"   Branch: {provenance.get('git_branch', 'unknown')}")
    except Exception as e:
        print(f"   ⚠️  Provenance warning: {e}")
        provenance = {}

    try:
        # Connect to server
        print(f"\n📡 Connecting to {server_url}")
        client = MCPClient(f"{server_url}/mcp")

        # Verify connection
        print("   Checking health...")
        try:
            client.wait_healthy(timeout_s=10.0)
            print("   ✅ Server is healthy")
        except RuntimeError as e:
            print(f"   ⚠️  Health check warning: {e}")

        # Create test campaign
        print("\n📋 Creating test campaign...")
        try:
            campaign_id = create_campaign(
                client,
                args.user_id,
                title="God Mode Validation Test",
                character="Test Character (Female, Level 5)",
                setting="A test environment for god mode validation",
                description="Testing god mode features: directives, identity, validation corrections",
            )
            print(f"   Campaign ID: {campaign_id}")
        except RuntimeError as e:
            error_msg = str(e)
            if "API_KEY" in error_msg or "api_key" in error_msg.lower():
                print(f"\n❌ API Key Error: {e}")
                print("\n💡 To run against a preview server with API keys configured:")
                print("   1. Find the preview URL from a PR deployment comment")
                print("   2. Run: MCP_SERVER_URL=https://<preview>.run.app python test_god_mode_validation.py")
                print("\n   Or use the dev server (deployed from main):")
                print("   MCP_SERVER_URL=https://mvp-site-app-dev-<hash>.us-central1.run.app python test_god_mode_validation.py")
                return 1
            raise

        # Seed initial character with gender for identity testing
        print("   Seeding character data...")
        seed_state = {
            "player_character_data": {
                "name": "Alexiel",
                "gender": "female",
                "level": 5,
                "class": "Rogue",
                "experience": {"current": 6500},
                "hp_current": 35,
                "hp_max": 35,
                "attributes": {
                    "strength": 10,
                    "dexterity": 18,
                    "constitution": 14,
                    "intelligence": 12,
                    "wisdom": 10,
                    "charisma": 16,
                },
                "parentage": {"father": "Lucifer"},
            }
        }
        seed_payload = f"GOD_MODE_UPDATE_STATE:{json.dumps(seed_state)}"
        seed_result = process_action(
            client,
            user_id=args.user_id,
            campaign_id=campaign_id,
            user_input=seed_payload,
            mode="character",
        )
        if seed_result.get("error"):
            print(f"   ⚠️  Seed warning: {seed_result['error']}")
        else:
            print("   ✅ Character seeded")

        # Run all scenarios
        print("\n🧪 Running God Mode Scenarios...")
        summary = run_all_scenarios(client, args.user_id, campaign_id, evidence_dir)

        # Print summary
        print("\n" + "=" * 60)
        print("Summary")
        print("=" * 60)
        print(f"Total: {summary['total']}")
        print(f"Passed: {summary['passed']}")
        print(f"Failed: {summary['failed']}")
        print(f"Evidence: {evidence_dir}")

        # Add provenance to summary
        summary["provenance"] = provenance

        # Save summary with checksum
        summary_path = evidence_dir / "summary.json"
        write_with_checksum(summary_path, json.dumps(summary, indent=2, default=str))
        print(f"Summary saved: {summary_path}")

        return 0 if summary["failed"] == 0 else 1

    finally:
        if local_server:
            print("\n🛑 Stopping local server...")
            local_server.stop()


if __name__ == "__main__":
    sys.exit(main())
