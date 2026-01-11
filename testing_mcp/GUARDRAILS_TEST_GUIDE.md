# Guide: Creating a New Guardrails Test

This guide explains how to create a test to verify the outcome declaration detection guardrails functionality added in PR #3383.

## Overview

The guardrails functionality prevents players from declaring outcomes (e.g., "I kill the goblin") and forces attempt-based gameplay ("I try to strike the goblin" → roll → narrate result).

## Test Structure Pattern

Based on existing tests like `test_god_mode_validation.py`, here's the pattern:

### 1. Test File Structure

```python
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
    DEFAULT_EVIDENCE_ENV,  # Includes CAPTURE_RAW_LLM=true
)
from lib.campaign_utils import (
    create_campaign,
    process_action,
    get_campaign_state,
    ensure_game_state_seed,
)
from lib.model_utils import settings_for_model, update_user_settings
from lib.evidence_utils import (
    get_evidence_dir,
    capture_provenance,
    write_with_checksum,
    save_request_responses,
    create_evidence_bundle,
)

# Evidence stored per evidence-standards.md: /tmp/<repo>/<branch>/<work>/<timestamp>/
DEFAULT_MODEL = "gemini-3-flash-preview"  # Pin model to avoid fallback noise
```

### 2. Test Scenarios

Define scenarios that test outcome declaration rejection:

```python
OUTCOME_DECLARATION_SCENARIOS = [
    {
        "name": "Combat - Instant Kill Declaration",
        "description": "Player declares instant kill outcome",
        "user_input": "It pierces the guard's throat instantly killing him",
        "expected_behavior": "reject",  # Should reject outcome declaration
        "expected_keywords": [
            "cannot process outcome declarations",
            "describe what your character attempts",
            "attempt",
        ],
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
        "name": "Social - NPC Decision Declaration",
        "description": "Player declares NPC decision",
        "user_input": "The king agrees with my proposal",
        "expected_behavior": "reject",
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
        "expected_behavior": "reject",
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
]
```

### 3. Validation Function

Create a function to validate LLM response:

```python
def validate_outcome_declaration_response(
    narrative: str,
    scenario: dict[str, Any],
) -> dict[str, Any]:
    """Validate LLM response matches expected behavior for outcome declarations.
    
    Args:
        narrative: The LLM-generated narrative text
        scenario: Test scenario dict with expected_behavior and expected_keywords
        
    Returns:
        Dict with 'passed', 'errors', 'warnings', and validation details
    """
    errors: list[str] = []
    warnings: list[str] = []
    
    narrative_lower = narrative.lower()
    expected_behavior = scenario.get("expected_behavior", "accept")
    expected_keywords = scenario.get("expected_keywords", [])
    
    if expected_behavior == "reject":
        # Should contain rejection keywords
        found_keywords = []
        for keyword in expected_keywords:
            if keyword.lower() in narrative_lower:
                found_keywords.append(keyword)
            else:
                errors.append(f"Missing expected rejection keyword: '{keyword}'")
        
        # Should NOT contain outcome declaration patterns
        outcome_patterns = [
            "kills", "destroys", "defeats", "dies", "falls",
            "agrees", "convinced", "finds", "opens",
        ]
        found_outcomes = []
        for pattern in outcome_patterns:
            if pattern in narrative_lower:
                found_outcomes.append(pattern)
                errors.append(f"LLM accepted outcome declaration pattern: '{pattern}'")
        
        passed = len(errors) == 0
        if not passed and found_keywords:
            # Partial pass - rejection detected but some patterns accepted
            warnings.append("Rejection detected but some outcome patterns still present")
            
    else:  # expected_behavior == "accept"
        # Should NOT contain rejection keywords
        for keyword in expected_keywords:
            if keyword.lower() in narrative_lower:
                errors.append(f"Unexpected rejection keyword found: '{keyword}'")
        
        # Should process as attempt (may contain dice rolls, DCs, etc.)
        attempt_indicators = ["try", "attempt", "roll", "check", "dc"]
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
```

### 4. Test Execution Function

```python
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
        action=scenario["user_input"],
    )
    
    # Extract narrative from response
    narrative = result.get("narrative", "")
    
    # Validate response
    validation = validate_outcome_declaration_response(narrative, scenario)
    
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
```

### 5. Main Test Function

```python
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
        campaign_id = create_campaign(client, user_id)
        ensure_game_state_seed(client, user_id=user_id, campaign_id=campaign_id)
        
        # Run scenario
        scenario_result = run_scenario(client, user_id, campaign_id, scenario)
        results["scenarios"].append(scenario_result)
        
        if scenario_result["passed"]:
            results["test_result"]["passed"] += 1
        results["test_result"]["total"] += 1
        
        # Clear captures between scenarios (optional)
        client.clear_captures()
    
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
```

### 6. CLI Entry Point

```python
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
        
        # Exit with error code if any failed
        if passed < total:
            sys.exit(1)
            
    finally:
        if server:
            server.stop()


if __name__ == "__main__":
    main()
```

## Evidence Standards Compliance

### Required Evidence Files

Per `.claude/skills/evidence-standards.md`, your test must generate:

1. **README.md** - Package manifest with git provenance
2. **methodology.md** - Testing methodology (auto-generated by `create_evidence_bundle`)
3. **evidence.md** - Evidence summary with pass/fail counts
4. **metadata.json** - Machine-readable provenance
5. **run.json** - Test results with scenarios array
6. **request_responses.jsonl** - Raw request/response pairs (MANDATORY for LLM behavior claims)
7. **artifacts/** - Server logs, lsof/ps outputs

### Key Requirements

1. **Git Provenance**: Captured via `capture_provenance()` - includes HEAD, origin/main, changed files
2. **Server Runtime**: Captured via `capture_provenance()` - includes PID, port, process cmdline
3. **Request/Response Capture**: Via `MCPClient.get_captures_as_dict()` → `save_request_responses()`
4. **Checksums**: All files get `.sha256` checksums via `write_with_checksum()`
5. **Scenarios Array**: `run.json` MUST include `scenarios` array with `campaign_id` and `errors` fields
6. **Model Pinning**: Use `update_user_settings()` to pin model and avoid fallback noise
7. **Campaign Isolation**: Create fresh campaign per scenario to prevent context pollution

### Evidence Directory Structure

```
/tmp/worldarchitect.ai/<branch>/outcome_declaration_guardrails/<timestamp>/
├── README.md + .sha256
├── methodology.md + .sha256
├── evidence.md + .sha256
├── metadata.json + .sha256
├── run.json + .sha256
├── request_responses.jsonl + .sha256
└── artifacts/
    ├── server.log + .sha256 (if server log provided)
    ├── lsof_output.txt + .sha256
    └── ps_output.txt + .sha256
```

## Running the Test

### Basic Run (Local Server Already Running)

```bash
python testing_mcp/test_outcome_declaration_guardrails.py \
  --server-url http://127.0.0.1:8001
```

### Start Local Server + Run + Save Evidence

```bash
python testing_mcp/test_outcome_declaration_guardrails.py \
  --start-local \
  --evidence \
  --work-name outcome_declaration_guardrails
```

### Using `/generatetest` Command

You can also use the `/generatetest` command to generate the test skeleton:

```
/generatetest create a test for outcome declaration guardrails that verifies the LLM rejects player-declared outcomes and requires attempt-based actions
```

This will generate a test file following the evidence standards automatically.

## Validation Criteria

Your test should verify:

1. **Rejection of Outcome Declarations**:
   - "kills/destroys/defeats [target]" → REJECTED
   - "The [target] dies/falls/is defeated" → REJECTED
   - "instantly killing/destroying [target]" → REJECTED
   - Past-tense outcomes: "killed", "destroyed", "convinced" → REJECTED
   - Definitive future outcomes: "will die", "will agree" → REJECTED

2. **Acceptance of Attempts**:
   - "I try to pierce his throat" → ACCEPTED (resolve with attack roll)
   - "I swing my sword at his neck" → ACCEPTED (resolve mechanically)
   - "I try to convince the king" → ACCEPTED (resolve with CHA check)

3. **Proper Resolution Flow**:
   - Attempt → DC set → Roll → Narrate result
   - DC set BEFORE roll (check `dice_audit_events` or `tool_results`)
   - Narrative matches roll result

## Example Evidence Output

After running with `--evidence`, you'll get:

```json
{
  "scenarios": [
    {
      "name": "Combat - Instant Kill Declaration",
      "campaign_id": "abc123def456",
      "passed": true,
      "errors": [],
      "warnings": [],
      "narrative": "I cannot process outcome declarations. Please describe what your CHARACTER ATTEMPTS to do...",
      "expected_behavior": "reject"
    }
  ],
  "test_result": {
    "passed": 6,
    "total": 6
  }
}
```

## Related Files

- **System Prompt**: `mvp_site/prompts/narrative_system_instruction.md` (lines ~105-173)
- **Evidence Standards**: `.claude/skills/evidence-standards.md`
- **Test Utilities**: `testing_mcp/lib/evidence_utils.py`
- **MCP Client**: `testing_mcp/lib/mcp_client.py`
- **Server Utils**: `testing_mcp/lib/server_utils.py`

## Next Steps

1. Create `testing_mcp/test_outcome_declaration_guardrails.py` following this pattern
2. Add scenarios covering all exploit types (combat, social, exploration)
3. Run with `--start-local --evidence` to generate evidence bundle
4. Review evidence bundle to verify guardrails are working
5. Update test scenarios based on actual LLM behavior
