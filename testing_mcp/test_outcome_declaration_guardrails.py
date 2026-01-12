#!/usr/bin/env python3
"""Outcome declaration guardrails validation tests.

Tests verify that the LLM rejects outcome declarations and requires
attempt-based actions per the Player Action Guardrails section in
mvp_site/prompts/narrative_system_instruction.md.

Run (local MCP already running):
    python testing_mcp/test_outcome_declaration_guardrails.py --server-url http://127.0.0.1:8001

Run (start local MCP automatically):
    python testing_mcp/test_outcome_declaration_guardrails.py --start-local --evidence

Run (with evidence capture):
    python testing_mcp/test_outcome_declaration_guardrails.py --start-local --evidence --work-name outcome_declaration_guardrails
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from lib import MCPClient
from lib.server_utils import (
    LocalServer,
    pick_free_port,
    start_local_mcp_server,
    DEFAULT_EVIDENCE_ENV,
)
from lib.campaign_utils import (
    create_campaign,
    process_action,
    ensure_game_state_seed,
)
from lib.model_utils import settings_for_model, update_user_settings, DEFAULT_MODEL_MATRIX
from lib.evidence_utils import (
    get_evidence_dir,
    capture_provenance,
    create_evidence_bundle,
)
from lib.firestore_validation import validate_action_resolution_in_firestore

# Evidence stored per evidence-standards.md: /tmp/<repo>/<branch>/<work>/<timestamp>/
DEFAULT_MODEL = "gemini-3-flash-preview"  # Always use gemini-3-flash-preview

# =============================================================================
# Test Scenarios
# =============================================================================

OUTCOME_DECLARATION_SCENARIOS: list[dict[str, Any]] = [
    {
        "name": "Combat - Instant Kill Declaration",
        "description": "Player declares instant kill outcome",
        "user_input": "It pierces the guard's throat instantly killing him",
        "expected_behavior": "resolve_with_audit",  # Should resolve with audit trail
        "expected_keywords": [],  # No longer checking for rejection keywords
        "exploit_type": "outcome_declaration",
    },
    {
        "name": "Combat - Attempt (Valid)",
        "description": "Player describes attempt correctly",
        "user_input": "I try to pierce the goblin's throat",
        "expected_behavior": "accept",  # Should accept attempt
        "expected_keywords": [],  # No specific rejection needed
        "exploit_type": "outcome_declaration",
    },
    {
        "name": "Combat - Past Tense Outcome",
        "description": "Player declares past-tense outcome",
        "user_input": "My sword slices through, and he falls dead",
        "expected_behavior": "resolve_with_audit",
        "expected_keywords": [
            "cannot process outcome declarations",
            "attempt",
        ],
        "exploit_type": "outcome_declaration",
    },
    {
        "name": "Social - NPC Decision Declaration",
        "description": "Player declares NPC decision",
        "user_input": "The king agrees with my proposal",
        "expected_behavior": "resolve_with_audit",
        "expected_keywords": [
            "cannot process outcome declarations",
            "attempt",
        ],
        "exploit_type": "outcome_declaration",
    },
    {
        "name": "Social - Attempt (Valid)",
        "description": "Player describes social attempt correctly",
        "user_input": "I try to convince the king to help us",
        "expected_behavior": "accept",
        "expected_keywords": [],
        "exploit_type": "outcome_declaration",
    },
    {
        "name": "Exploration - Finding Declaration",
        "description": "Player declares finding",
        "user_input": "I find the hidden treasure",
        "expected_behavior": "resolve_with_audit",
        "expected_keywords": [
            "cannot process outcome declarations",
            "attempt",
        ],
        "exploit_type": "outcome_declaration",
    },
    {
        "name": "Exploration - Attempt (Valid)",
        "description": "Player describes search attempt correctly",
        "user_input": "I search the room for traps",
        "expected_behavior": "accept",
        "expected_keywords": [],
        "exploit_type": "outcome_declaration",
    },
    {
        "name": "Combat - Future Tense Outcome",
        "description": "Player declares definitive future outcome",
        "user_input": "The goblin will die from this attack",
        "expected_behavior": "resolve_with_audit",
        "expected_keywords": [
            "cannot process outcome declarations",
            "attempt",
        ],
        "exploit_type": "outcome_declaration",
    },
    # =============================================================================
    # False Positive Prevention Tests - Valid scenarios that contain outcome words
    # but should NOT be rejected (they reference past events, use modals, etc.)
    # =============================================================================
    {
        "name": "False Positive 1 - Past Event Looting",
        "description": "Player references past kill while looting (should accept)",
        "user_input": "I loot the goblin I killed earlier",
        "expected_behavior": "accept",
        "expected_keywords": [],  # Should NOT reject - "killed" refers to past event
        "exploit_type": "outcome_declaration",
        "validation_notes": "Contains 'killed' but has 'earlier' context - past reference",
    },
    {
        "name": "False Positive 2 - Body Search",
        "description": "Player searches body of defeated enemy (should accept)",
        "user_input": "I search the body of the bandit I defeated",
        "expected_behavior": "accept",
        "expected_keywords": [],  # Should NOT reject - "defeated" refers to past event
        "exploit_type": "outcome_declaration",
        "validation_notes": "Contains 'defeated' but has 'the body of' context - past reference",
    },
    {
        "name": "False Positive 3 - Intent Statement",
        "description": "Player states intent with modal verb (should accept)",
        "user_input": "I want to kill the dragon",
        "expected_behavior": "accept",
        "expected_keywords": [],  # Should NOT reject - "want to" = intent, not declaration
        "exploit_type": "outcome_declaration",
        "validation_notes": "Contains 'kill' but 'want to' indicates intent, not outcome declaration",
    },
    {
        "name": "False Positive 4 - Hypothetical Question",
        "description": "Player asks hypothetical question (should accept)",
        "user_input": "If the king agrees, what happens next?",
        "expected_behavior": "accept",
        "expected_keywords": [],  # Should NOT reject - conditional question, not declaration
        "exploit_type": "outcome_declaration",
        "validation_notes": "Contains 'agrees' but 'if' + question format = hypothetical, not declaration",
    },
    {
        "name": "False Positive 5 - Location Reference",
        "description": "Player references location of past event (should accept)",
        "user_input": "I return to the cave where we killed the necromancer",
        "expected_behavior": "accept",
        "expected_keywords": [],  # Should NOT reject - "where we" = past geographic reference
        "exploit_type": "outcome_declaration",
        "validation_notes": "Contains 'killed' but 'where we' indicates past geographic reference",
    },
    {
        "name": "False Positive 6 - Conditional Strategy",
        "description": "Player describes conditional plan (should accept)",
        "user_input": "If I can find the secret door, I'll signal the party",
        "expected_behavior": "accept",
        "expected_keywords": [],  # Should NOT reject - conditional planning, not declaration
        "exploit_type": "outcome_declaration",
        "validation_notes": "Contains 'find' but 'if I can' = conditional planning, not outcome declaration",
    },
    {
        "name": "False Positive 7 - Rules Question",
        "description": "Player asks meta question about mechanics (should accept)",
        "user_input": "What happens if my attack kills it?",
        "expected_behavior": "accept",
        "expected_keywords": [],  # Should NOT reject - meta question about mechanics
        "exploit_type": "outcome_declaration",
        "validation_notes": "Contains 'kills' but 'what happens if' = meta question, not outcome declaration",
    },
    {
        "name": "False Positive 8 - Quoting GM",
        "description": "Player references past GM narration (should accept)",
        "user_input": "You said earlier I killed the guard - can I take his armor?",
        "expected_behavior": "accept",
        "expected_keywords": [],  # Should NOT reject - referencing past narration
        "exploit_type": "outcome_declaration",
        "validation_notes": "Contains 'killed' but 'you said earlier' = referencing past narration, not declaring outcome",
    },
]

# =============================================================================
# Validation Functions
# =============================================================================


def validate_outcome_declaration_response(
    narrative: str,
    scenario: dict[str, Any],
    structured_response: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate LLM response matches expected behavior for outcome declarations.
    
    Args:
        narrative: The LLM-generated narrative text
        scenario: Test scenario dict with expected_behavior
        structured_response: Optional parsed JSON response with action_resolution field
        
    Returns:
        Dict with 'passed', 'errors', 'warnings', and validation details
    """
    errors: list[str] = []
    warnings: list[str] = []
    
    narrative_lower = narrative.lower()
    expected_behavior = scenario.get("expected_behavior", "accept")
    
    if expected_behavior == "resolve_with_audit":
        # Should NOT contain rejection phrases (old rejection-based approach)
        rejection_phrases = [
            "cannot process outcome declarations",
            "i cannot process",
            "outcome declarations",
        ]
        for phrase in rejection_phrases:
            if phrase in narrative_lower:
                errors.append(f"LLM rejected input (old approach). Expected resolution with audit trail. Found: '{phrase}'")
        
        # Should contain action_resolution JSON field
        if structured_response:
            action_resolution = structured_response.get("action_resolution")
            
            if not action_resolution:
                errors.append("Missing action_resolution JSON field. LLM should document reinterpretation in audit trail.")
            else:
                # Validate audit trail completeness - new action_resolution schema
                # Required fields for action_resolution: reinterpreted, audit_flags
                # Optional but recommended: mechanics, player_input, interpreted_as
                required_fields = ["audit_flags"]
                missing_fields = [field for field in required_fields if field not in action_resolution]
                if missing_fields:
                    errors.append(f"action_resolution missing required fields: {missing_fields}")
                
                # Check reinterpreted is True for outcome declarations
                if "reinterpreted" not in action_resolution:
                    errors.append("action_resolution missing required field: reinterpreted")
                else:
                    reinterpreted = action_resolution.get("reinterpreted", False)
                    if not reinterpreted:
                        errors.append("action_resolution.reinterpreted should be True when reinterpreting outcome declarations")
                
                # Check audit_flags contains player_declared_outcome
                audit_flags = action_resolution.get("audit_flags", [])
                if not isinstance(audit_flags, list):
                    errors.append("action_resolution.audit_flags must be a list")
                elif "player_declared_outcome" not in audit_flags:
                    errors.append("audit_flags should include 'player_declared_outcome' when reinterpreting player input")
                
                # Validate mechanics object if present (optional but recommended)
                mechanics = action_resolution.get("mechanics", {})
                if mechanics:
                    if not isinstance(mechanics, dict):
                        errors.append("action_resolution.mechanics must be a dict")
                    # Check for rolls or audit_events if mechanics present
                    if "rolls" not in mechanics and "audit_events" not in mechanics:
                        # Old schema might have "outcome" field instead
                        if "outcome" not in mechanics:
                            warnings.append("action_resolution.mechanics should contain rolls or audit_events for complete audit trail")
        else:
            warnings.append("No structured_response provided - cannot validate action_resolution JSON")
        
        # Should process the action (narrative should describe attempt/resolution, not rejection)
        if not errors and len(narrative) < 50:
            warnings.append("Narrative seems too short - may not have processed the action")
        
        passed = len(errors) == 0
            
    else:  # expected_behavior == "accept"
        # Should NOT contain rejection keywords (check regardless of expected_keywords)
        rejection_phrases = [
            "cannot process outcome declarations",
            "i cannot process",
            "outcome declarations",
        ]
        for phrase in rejection_phrases:
            if phrase in narrative_lower:
                errors.append(f"LLM rejected input but expected ACCEPT. Found rejection phrase: '{phrase}'")
        
        # Should process as attempt (may contain dice rolls, DCs, etc.)
        attempt_indicators = ["try", "attempt", "roll", "check", "dc", "d20", "attack"]
        found_attempts = [ind for ind in attempt_indicators if ind in narrative_lower]
        
        passed = len(errors) == 0
        if not found_attempts:
            warnings.append("No attempt indicators found - may not be processing as attempt")
    
    return {
        "passed": passed,
        "errors": errors,
        "warnings": warnings,
        "narrative_length": len(narrative),
        "expected_behavior": expected_behavior,
    }


# =============================================================================
# Test Execution
# =============================================================================


def run_scenario(
    client: MCPClient,
    user_id: str,
    campaign_id: str,
    scenario: dict[str, Any],
) -> dict[str, Any]:
    """Run a single test scenario.
    
    Args:
        client: MCP client instance
        user_id: User ID for the test
        campaign_id: Campaign ID (create fresh per scenario for isolation)
        scenario: Test scenario dict
        
    Returns:
        Result dict with passed, errors, narrative, etc.
    """
    # Process the user action
    result = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=scenario["user_input"],
    )
    
    # Extract narrative and structured response from result
    narrative = result.get("narrative", "")
    # Extract structured response - check action_resolution first, then outcome_resolution for backward compat
    # (process_action returns the full response dict with all JSON fields)
    structured_response = {}
    
    # Check for action_resolution first (new field)
    if "action_resolution" in result and result["action_resolution"]:
        structured_response["action_resolution"] = result["action_resolution"]
    # Also check if it's in a nested structured_response object
    elif result.get("structured_response") and isinstance(result["structured_response"], dict):
        if "action_resolution" in result["structured_response"]:
            structured_response["action_resolution"] = result["structured_response"]["action_resolution"]
        # Fallback to outcome_resolution for backward compatibility
        elif "outcome_resolution" in result["structured_response"]:
            structured_response["action_resolution"] = result["structured_response"]["outcome_resolution"]
        else:
            structured_response = result["structured_response"]
    # Fallback to outcome_resolution (legacy field) if action_resolution not found
    elif "outcome_resolution" in result and result["outcome_resolution"]:
        structured_response["action_resolution"] = result["outcome_resolution"]
    # Final fallback to empty dict if not found
    if not structured_response.get("action_resolution"):
        structured_response = (
            result.get("response_json") or
            result.get("json_response") or
            {}  # Fallback to empty dict if not found
        )
    
    # Validate response
    validation = validate_outcome_declaration_response(narrative, scenario, structured_response)
    
    # Validate Firestore persistence (CRITICAL: Check that audit trail is actually saved)
    firestore_validation = validate_action_resolution_in_firestore(
        user_id=user_id,
        campaign_id=campaign_id,
        limit=1,  # Check latest entry (should be the one we just created)
        require_audit_flags=True,
    )
    
    # Merge Firestore validation errors/warnings into main validation
    combined_errors = list(validation["errors"])
    combined_warnings = list(validation.get("warnings", []))
    
    # Add Firestore validation errors (these are critical - audit trail must be persisted)
    combined_errors.extend(firestore_validation["errors"])
    combined_warnings.extend(firestore_validation["warnings"])
    
    # Test fails if either API validation OR Firestore validation fails
    passed = validation["passed"] and firestore_validation["passed"]
    
    return {
        "name": scenario["name"],
        "campaign_id": campaign_id,  # Required for log traceability
        "passed": passed,
        "errors": combined_errors,
        "warnings": combined_warnings,
        "narrative": narrative,
        "narrative_length": validation["narrative_length"],
        "expected_behavior": scenario["expected_behavior"],
        "user_input": scenario["user_input"],
        "firestore_validation": {
            "passed": firestore_validation["passed"],
            "entries_checked": firestore_validation["entries_checked"],
            "entries_with_action_resolution": firestore_validation["entries_with_action_resolution"],
        },
    }


def run_tests(
    server_url: str,
    *,
    model_id: str,
    work_name: str = "outcome_declaration_guardrails",
    scenario_slice: str | None = None,
) -> dict[str, Any]:
    """Run all test scenarios.
    
    Args:
        server_url: MCP server URL
        model_id: Model to test against
        work_name: Work name for evidence directory
        save_evidence: Whether to save evidence bundle
        scenario_slice: Optional slice string "start:end"
        
    Returns:
        Test results dict
    """
    client = MCPClient(server_url)
    client.wait_healthy()
    
    # Create test user
    user_id = f"test_user_{int(datetime.now(timezone.utc).timestamp())}_{model_id.replace('/', '-')}"
    
    # Pin model settings to avoid fallback noise
    update_user_settings(
        client,
        user_id=user_id,
        settings=settings_for_model(model_id),
    )
    
    results = {
        "scenarios": [],
        "test_result": {
            "passed": 0,
            "total": 0,
        },
    }
    
    scenarios = OUTCOME_DECLARATION_SCENARIOS
    if scenario_slice:
        try:
            start_str, end_str = scenario_slice.split(":")
            start = int(start_str) if start_str else 0
            end = int(end_str) if end_str else len(scenarios)
            scenarios = scenarios[start:end]
        except ValueError:
            print(f"⚠️ Invalid slice format '{scenario_slice}', running all scenarios")

    # Run each scenario with fresh campaign for isolation
    for scenario in scenarios:
        # Create fresh campaign per scenario to avoid context pollution
        # IMPORTANT: Must include "narrative" prompt to load guardrails
        campaign_id = create_campaign(
            client,
            user_id,
            selected_prompts=["narrative", "mechanics"],  # Load narrative_system_instruction.md with guardrails
        )
        ensure_game_state_seed(client, user_id=user_id, campaign_id=campaign_id)
        
        # Run scenario
        scenario_result = run_scenario(client, user_id, campaign_id, scenario)
        results["scenarios"].append(scenario_result)
        
        if scenario_result["passed"]:
            results["test_result"]["passed"] += 1
        results["test_result"]["total"] += 1
        
        # Clear captures between scenarios (optional, but we'll keep them all)
        # client.clear_captures()
    
    # Capture request/response pairs for evidence (always generated)
    request_responses = client.get_captures_as_dict()
    
    # Capture provenance (always generated)
    port = server_url.split(":")[-1].rstrip("/")
    provenance = capture_provenance(
        base_url=server_url,
        server_pid=None,  # Will be captured from port if available
    )
    
    # Get evidence directory (always generated)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence_dir = get_evidence_dir(work_name, timestamp)
    
    # Create evidence bundle (always generated)
    create_evidence_bundle(
        evidence_dir=evidence_dir,
        test_name=work_name,
        provenance=provenance,
        results=results,
        request_responses=request_responses,
        methodology_text=None,  # Will be auto-generated
    )
    
    print(f"✅ Evidence saved to: {evidence_dir}")
    
    return results


# =============================================================================
# CLI Entry Point
# =============================================================================


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--server-url", default="http://localhost:8001")
    parser.add_argument("--start-local", action="store_true")
    parser.add_argument("--work-name", default="outcome_declaration_guardrails")
    parser.add_argument("--slice", type=str, help="Slice of scenarios to run (e.g. '0:8')")
    args = parser.parse_args()
    
    server: LocalServer | None = None
    
    try:
        # Always use gemini-3-flash-preview
        models = ["gemini-3-flash-preview"]

        if args.start_local:
            # Start local server with evidence capture enabled
            port = pick_free_port()
            env_overrides = {
                **DEFAULT_EVIDENCE_ENV,  # CAPTURE_RAW_LLM=true, etc.
                "WORLDAI_DEV_MODE": "true",
            }
            # Use first model as default if possible, but it doesn't strictly matter
            # as run_tests updates user settings per run.
            server = start_local_mcp_server(
                port=port,
                env_overrides=env_overrides,
            )
            server_url = f"http://127.0.0.1:{port}"
            print(f"✅ Started local server on {server_url}")
        else:
            server_url = args.server_url
        
        all_passed = True
        aggregated_results = []

        print(f"Running tests for models: {', '.join(models)}")

        for model_id in models:
            print(f"\n{'='*60}")
            print(f"Testing Model: {model_id}")
            print(f"{'='*60}")

            # Run tests (evidence always generated)
            results = run_tests(
                server_url,
                model_id=model_id,
                work_name=args.work_name,
                scenario_slice=args.slice,
            )
            
            # Print summary for this model
            passed = results["test_result"]["passed"]
            total = results["test_result"]["total"]
            print(f"\nModel Results ({model_id}): {passed}/{total} PASSED")
            
            if passed < total:
                all_passed = False
            
            for scenario in results["scenarios"]:
                status = "✅ PASS" if scenario["passed"] else "❌ FAIL"
                print(f"{status} {scenario['name']}")
                if scenario.get("errors"):
                    for error in scenario["errors"]:
                        print(f"  Error: {error}")
                if scenario.get("warnings"):
                    for warning in scenario["warnings"]:
                        print(f"  Warning: {warning}")
                # Show first 100 chars of narrative for context
                narrative_preview = scenario.get("narrative", "")[:100]
                if narrative_preview:
                    print(f"  Narrative preview: {narrative_preview}...")
                print()
            
            aggregated_results.append((model_id, passed, total))

        print(f"\n{'='*60}")
        print("FINAL SUMMARY")
        print(f"{'='*60}")
        for model_id, passed, total in aggregated_results:
            print(f"{model_id}: {passed}/{total} PASSED")

        # Exit with error code if any failed
        if not all_passed:
            sys.exit(1)
            
    finally:
        if server:
            server.stop()


if __name__ == "__main__":
    main()
