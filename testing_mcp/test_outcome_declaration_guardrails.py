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
import json
import os
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
from lib.model_utils import settings_for_model, update_user_settings
from lib.evidence_utils import (
    get_evidence_dir,
    capture_provenance,
    create_evidence_bundle,
)

# Evidence stored per evidence-standards.md: /tmp/<repo>/<branch>/<work>/<timestamp>/
DEFAULT_MODEL = "gemini-3-flash-preview"  # Pin model to avoid fallback noise

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
        structured_response: Optional parsed JSON response with outcome_resolution field
        
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
        
        # Should contain outcome_resolution JSON field
        if structured_response:
            outcome_resolution = structured_response.get("outcome_resolution")
            if not outcome_resolution:
                errors.append("Missing outcome_resolution JSON field. LLM should document reinterpretation in audit trail.")
            else:
                # Validate audit trail completeness
                required_fields = ["trigger", "player_intent", "original_input", "resolution_type", "mechanics", "audit_flags"]
                missing_fields = [field for field in required_fields if field not in outcome_resolution]
                if missing_fields:
                    errors.append(f"outcome_resolution missing required fields: {missing_fields}")
                
                # Check audit_flags contains player_declared_outcome
                audit_flags = outcome_resolution.get("audit_flags", [])
                if "player_declared_outcome" not in audit_flags:
                    errors.append("audit_flags should include 'player_declared_outcome' when reinterpreting player input")
                
                # Validate mechanics object
                mechanics = outcome_resolution.get("mechanics", {})
                if not mechanics:
                    errors.append("outcome_resolution.mechanics is required")
                elif "outcome" not in mechanics:
                    errors.append("outcome_resolution.mechanics.outcome is required")
        else:
            warnings.append("No structured_response provided - cannot validate outcome_resolution JSON")
        
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
    # Extract structured response - check outcome_resolution directly in result
    # (process_action returns the full response dict with all JSON fields)
    # The outcome_resolution field should be at the top level of result if present
    structured_response = {}
    if "outcome_resolution" in result and result["outcome_resolution"]:
        structured_response["outcome_resolution"] = result["outcome_resolution"]
    # Also check if it's in a nested structured_response object
    elif result.get("structured_response") and isinstance(result["structured_response"], dict):
        if "outcome_resolution" in result["structured_response"]:
            structured_response["outcome_resolution"] = result["structured_response"]["outcome_resolution"]
        else:
            structured_response = result["structured_response"]
    # Fallback to empty dict if not found
    if not structured_response.get("outcome_resolution"):
        structured_response = (
            result.get("response_json") or
            result.get("json_response") or
            {}  # Fallback to empty dict if not found
        )
    
    # Validate response
    validation = validate_outcome_declaration_response(narrative, scenario, structured_response)
    
    return {
        "name": scenario["name"],
        "campaign_id": campaign_id,  # Required for log traceability
        "passed": validation["passed"],
        "errors": validation["errors"],
        "warnings": validation.get("warnings", []),
        "narrative": narrative,
        "narrative_length": validation["narrative_length"],
        "expected_behavior": scenario["expected_behavior"],
        "user_input": scenario["user_input"],
    }


def run_tests(
    server_url: str,
    *,
    work_name: str = "outcome_declaration_guardrails",
    save_evidence: bool = False,
) -> dict[str, Any]:
    """Run all test scenarios.
    
    Args:
        server_url: MCP server URL
        work_name: Work name for evidence directory
        save_evidence: Whether to save evidence bundle
        
    Returns:
        Test results dict
    """
    client = MCPClient(server_url)
    client.wait_healthy()
    
    # Create test user
    user_id = f"test_user_{int(datetime.now(timezone.utc).timestamp())}"
    
    # Pin model settings to avoid fallback noise
    update_user_settings(
        client,
        user_id=user_id,
        settings=settings_for_model(DEFAULT_MODEL),
    )
    
    results = {
        "scenarios": [],
        "test_result": {
            "passed": 0,
            "total": 0,
        },
    }
    
    # Run each scenario with fresh campaign for isolation
    for scenario in OUTCOME_DECLARATION_SCENARIOS:
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
    
    # Capture request/response pairs for evidence
    request_responses = client.get_captures_as_dict()
    
    if save_evidence:
        # Capture provenance
        port = server_url.split(":")[-1].rstrip("/")
        provenance = capture_provenance(
            base_url=server_url,
            server_pid=None,  # Will be captured from port if available
        )
        
        # Get evidence directory
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        evidence_dir = get_evidence_dir(work_name, timestamp)
        
        # Create evidence bundle
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
    parser.add_argument("--evidence", action="store_true", help="Save evidence bundle")
    parser.add_argument("--work-name", default="outcome_declaration_guardrails")
    args = parser.parse_args()
    
    server: LocalServer | None = None
    
    try:
        if args.start_local:
            # Start local server with evidence capture enabled
            port = pick_free_port()
            server = start_local_mcp_server(
                port=port,
                env_overrides={
                    **DEFAULT_EVIDENCE_ENV,  # CAPTURE_RAW_LLM=true, etc.
                    "WORLDAI_DEV_MODE": "true",
                },
            )
            server_url = f"http://127.0.0.1:{port}"
            print(f"✅ Started local server on {server_url}")
        else:
            server_url = args.server_url
        
        # Run tests
        results = run_tests(
            server_url,
            work_name=args.work_name,
            save_evidence=args.evidence,
        )
        
        # Print summary
        passed = results["test_result"]["passed"]
        total = results["test_result"]["total"]
        print(f"\n{'='*60}")
        print(f"Test Results: {passed}/{total} PASSED")
        print(f"{'='*60}\n")
        
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
        
        # Exit with error code if any failed
        if passed < total:
            sys.exit(1)
            
    finally:
        if server:
            server.stop()


if __name__ == "__main__":
    main()
