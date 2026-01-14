#!/usr/bin/env python3
"""
Reproduction test for Bug #2: JSON parsing errors in LLM responses.

This test reproduces JSON parsing failures by:
1. Creating a campaign with large context (simulating real campaign complexity)
2. Making requests that trigger LLM responses
3. Verifying JSON parsing errors occur

RED STATE PROOF: This test should FAIL (JSON parsing errors) before the fix.
"""

import argparse
import os
import shutil
import sys
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from testing_mcp.lib.evidence_utils import (
    capture_provenance,
    create_evidence_bundle,
    get_evidence_dir,
    save_request_responses,
)
from testing_mcp.lib.mcp_client import MCPClient
from testing_mcp.lib.campaign_utils import create_campaign, process_action
from testing_mcp.lib.server_utils import pick_free_port, start_local_mcp_server

TEST_NAME = "json_parsing_failure"


def test_json_parsing_failure():
    """Test that reproduces JSON parsing failures."""
    parser = argparse.ArgumentParser(
        description="Reproduce JSON parsing failure in LLM responses"
    )
    parser.add_argument(
        "--start-local",
        action="store_true",
        help="Start local MCP server automatically",
    )
    parser.add_argument(
        "--server-url",
        type=str,
        help="MCP server URL (e.g., http://127.0.0.1:8001)",
    )
    parser.add_argument(
        "--evidence",
        action="store_true",
        help="Capture evidence bundle",
    )
    args = parser.parse_args()

    evidence_dir = None
    if args.evidence:
        evidence_dir = get_evidence_dir(TEST_NAME)
        print(f"📦 Evidence directory: {evidence_dir}")

    # Setup server
    server_url = args.server_url
    local_server = None
    log_path = None

    if args.start_local:
        port = pick_free_port()
        print(f"🚀 Starting local MCP server on port {port}...")
        env_overrides = {
            "WORLDAI_DEV_MODE": "true",
        }
        local_server = start_local_mcp_server(port, env_overrides=env_overrides)
        log_path = local_server.log_path
        server_url = f"{local_server.base_url}/mcp"
        print(f"✅ Server started: {server_url}")
        print(f"📝 Log file: {log_path}")
        time.sleep(3)  # Give server time to start
    else:
        if not server_url:
            parser.error("Must provide --server-url or --start-local")
        print(f"⚠️  Using external server - log checks will be limited")

    client = MCPClient(server_url, timeout_s=600.0)

    try:
        # Wait for server to be healthy
        if local_server:
            import requests

            base_url = local_server.base_url
            start_wait = time.time()
            healthy = False
            while time.time() - start_wait < 30:
                try:
                    r = requests.get(f"{base_url}/health", timeout=1)
                    if r.status_code == 200:
                        healthy = True
                        break
                except (requests.RequestException, ConnectionError):
                    pass
                time.sleep(0.5)

            if not healthy:
                print("❌ Server failed to start")
                sys.exit(1)

        # Create a test campaign
        user_id = "test_json_parsing_user"
        campaign_id = create_campaign(
            client,
            user_id=user_id,
            title="JSON Parsing Failure Test",
            setting="Test setting for JSON parsing failure reproduction",
            description="Campaign to test JSON parsing errors with complex context",
        )
        print(f"📝 Created campaign: {campaign_id}")

        # Build up context to simulate real campaign complexity
        # Make multiple requests to build history
        print("\n📚 Building campaign context...")
        context_building_inputs = [
            "I explore the dungeon",
            "I check for traps",
            "I listen at the door",
            "I open the door carefully",
            "I enter the room",
            "I look around",
            "I search for treasure",
            "I check my inventory",
        ]

        for i, input_text in enumerate(context_building_inputs, 1):
            print(f"  [{i}/{len(context_building_inputs)}] {input_text}")
            try:
                process_action(
                    client,
                    user_id=user_id,
                    campaign_id=campaign_id,
                    user_input=input_text,
                    mode=None,
                )
                time.sleep(1)  # Small delay between requests
            except Exception as e:
                print(f"    ⚠️  Error building context: {e}")

        # Test scenarios that might trigger JSON parsing errors
        test_scenarios = [
            {
                "name": "Complex Action",
                "input": "I cast fireball at the group of goblins while dodging their arrows and preparing a second spell",
            },
            {
                "name": "Multi-step Action",
                "input": "I want to search the room, check for hidden doors, examine the bookshelf, and then rest",
            },
            {
                "name": "Long Narrative Request",
                "input": "I carefully examine the ancient tome, reading through its pages to understand the magical rituals described within, then I compare it to my spellbook to see if I can learn any new spells",
            },
        ]

        results = {
            "scenarios": [],
            "json_parsing_errors": [],
        }
        request_responses = []

        # Test each scenario
        for scenario in test_scenarios:
            print(f"\n🧪 Testing: {scenario['name']}")
            print(f"   Input: '{scenario['input'][:60]}...'")

            try:
                response = process_action(
                    client,
                    user_id=user_id,
                    campaign_id=campaign_id,
                    user_input=scenario["input"],
                    mode=None,
                )

                request_responses.append(
                    {
                        "scenario": scenario["name"],
                        "request": {"user_input": scenario["input"], "mode": None},
                        "response": response,
                    }
                )

                # Check logs for JSON parsing errors
                if log_path and log_path.exists():
                    # Read fresh log content
                    fresh_log = log_path.read_text(errors="ignore")
                    # Look for JSON parsing errors
                    if "Failed to parse JSON response" in fresh_log:
                        print(f"   ❌ RED STATE CONFIRMED: JSON parsing error detected")
                        # Extract error details
                        error_lines = [
                            line
                            for line in fresh_log.splitlines()
                            if "Failed to parse JSON" in line or "Expecting value" in line
                        ]
                        error_msg = error_lines[-1] if error_lines else "JSON parsing error"
                        results["json_parsing_errors"].append(
                            {
                                "scenario": scenario["name"],
                                "error": error_msg,
                            }
                        )
                        results["scenarios"].append(
                            {
                                "name": scenario["name"],
                                "campaign_id": campaign_id,
                                "passed": False,
                                "errors": [error_msg],
                                "json_parsing_error": True,
                            }
                        )
                    else:
                        print(f"   ✅ No JSON parsing errors detected")
                        results["scenarios"].append(
                            {
                                "name": scenario["name"],
                                "campaign_id": campaign_id,
                                "passed": True,
                                "errors": [],
                                "json_parsing_error": False,
                            }
                        )
                else:
                    print(f"   ⚠️  Could not check logs for JSON parsing errors")
                    results["scenarios"].append(
                        {
                            "name": scenario["name"],
                            "campaign_id": campaign_id,
                            "passed": False,
                            "errors": ["Could not verify JSON parsing from logs"],
                        }
                    )

                time.sleep(2)  # Delay between requests

            except Exception as e:
                print(f"   ❌ Error: {e}")
                # Check if it's a JSON parsing error
                error_str = str(e)
                if "JSON" in error_str or "parse" in error_str.lower():
                    results["json_parsing_errors"].append(
                        {
                            "scenario": scenario["name"],
                            "error": error_str,
                        }
                    )
                results["scenarios"].append(
                    {
                        "name": scenario["name"],
                        "campaign_id": campaign_id,
                        "passed": False,
                        "errors": [error_str],
                    }
                )

        # Summary
        print(f"\n{'='*70}")
        print(f"📊 TEST SUMMARY")
        print(f"{'='*70}")
        total = len(results["scenarios"])
        passed = sum(1 for s in results["scenarios"] if s.get("passed", False))
        failed = total - passed
        json_errors = len(results["json_parsing_errors"])

        print(f"Total scenarios: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"JSON parsing errors: {json_errors}")

        if json_errors > 0:
            print(f"\n❌ RED STATE CONFIRMED: JSON parsing errors detected")
            print(f"   This is expected BEFORE the fix is applied")
            for error in results["json_parsing_errors"]:
                print(f"   - {error['scenario']}: {error['error']}")
        else:
            print(f"\n✅ No JSON parsing errors detected")

        # Capture evidence
        if args.evidence and evidence_dir:
            print(f"\n📦 Capturing evidence to {evidence_dir}...")

            # Capture provenance
            # Extract port from server URL
            import re
            port_match = re.search(r':(\d+)', server_url)
            port = int(port_match.group(1)) if port_match else None
            provenance = capture_provenance(
                server_url,
                local_server.pid if local_server else None,
            )

            # Save request/response pairs
            save_request_responses(evidence_dir, request_responses)

            # Save server logs if available
            if log_path and log_path.exists():
                artifacts_dir = evidence_dir / "artifacts"
                artifacts_dir.mkdir(exist_ok=True)
                shutil.copy2(log_path, artifacts_dir / "server.log")

            # Extract JSON parsing errors from logs
            json_error_log = None
            if log_path and log_path.exists():
                log_content = log_path.read_text(errors="ignore")
                error_lines = [
                    line
                    for line in log_content.splitlines()
                    if "Failed to parse JSON" in line
                    or "Expecting value" in line
                    or "JSON" in line and "error" in line.lower()
                ]
                if error_lines:
                    json_error_log = "\n".join(error_lines[-20:])  # Last 20 error lines
                    artifacts_dir = evidence_dir / "artifacts"
                    artifacts_dir.mkdir(exist_ok=True)
                    (artifacts_dir / "json_parsing_errors.log").write_text(json_error_log)

            # Create evidence bundle
            results_dict = {
                "scenarios": results["scenarios"],
                "summary": {
                    "total_scenarios": total,
                    "passed": passed,
                    "failed": failed,
                    "json_parsing_errors": json_errors,
                    "red_state_confirmed": json_errors > 0,
                },
            }
            create_evidence_bundle(
                evidence_dir=evidence_dir,
                test_name=TEST_NAME,
                provenance=provenance,
                results=results_dict,
                request_responses=request_responses,
                server_log_path=log_path if log_path and log_path.exists() else None,
            )

            print(f"✅ Evidence captured to {evidence_dir}")

        # Exit with error if red state confirmed
        if json_errors > 0:
            sys.exit(1)
        else:
            sys.exit(0)

    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        if local_server:
            print(f"\n🛑 Stopping local server...")
            local_server.stop()


if __name__ == "__main__":
    test_json_parsing_failure()
