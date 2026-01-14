#!/usr/bin/env python3
"""
Reproduction test for Bug #1: Classifier model failing to load in Cloud Run.

This test reproduces the classifier initialization failure by:
1. Starting a local server with ENABLE_SEMANTIC_ROUTING=true
2. Attempting to use the classifier
3. Verifying it fails to load and defaults to MODE_CHARACTER (0.00 confidence)

RED STATE PROOF: This test should FAIL (classifier not working) before the fix.
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

from testing_mcp.lib.campaign_utils import create_campaign, process_action
from testing_mcp.lib.evidence_utils import (
    capture_provenance,
    create_evidence_bundle,
    get_evidence_dir,
    save_evidence,
    save_request_responses,
)
from testing_mcp.lib.mcp_client import MCPClient
from testing_mcp.lib.server_utils import pick_free_port, start_local_mcp_server

TEST_NAME = "classifier_model_loading_failure"


def test_classifier_initialization_failure():
    """Test that reproduces classifier model loading failure."""
    parser = argparse.ArgumentParser(
        description="Reproduce classifier model loading failure"
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
            "ENABLE_SEMANTIC_ROUTING": "true",  # Force classifier initialization
            "WORLDAI_DEV_MODE": "true",
        }
        local_server = start_local_mcp_server(port, env_overrides=env_overrides)
        log_path = local_server.log_path
        server_url = f"{local_server.base_url}/mcp"
        print(f"✅ Server started: {server_url}")
        print(f"📝 Log file: {log_path}")
        time.sleep(5)  # Give server time to start and attempt classifier init
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
        user_id = "test_classifier_failure_user"

        campaign_id = create_campaign(
            client,
            user_id=user_id,
            title="Classifier Failure Test",
            setting="Test setting for classifier failure reproduction",
            description="Campaign to test classifier model loading failure",
        )
        print(f"📝 Created campaign: {campaign_id}")

        # Test scenarios that should trigger classifier
        test_scenarios = [
            {
                "name": "Combat Intent",
                "input": "I attack the goblin",
                "expected_mode": "COMBAT",
            },
            {
                "name": "Info Intent",
                "input": "Show my inventory",
                "expected_mode": "INFO",
            },
            {
                "name": "Think Intent",
                "input": "What should I do?",
                "expected_mode": "THINK",
            },
            {
                "name": "Rewards Intent",
                "input": "claim my rewards",
                "expected_mode": "REWARDS",
            },
        ]

        results = {
            "scenarios": [],
            "classifier_failed": False,
            "classifier_ready": False,
        }
        request_responses = []

        # Check server logs for classifier initialization status
        if log_path and log_path.exists():
            log_content = log_path.read_text(errors="ignore")
            if "CLASSIFIER: Initialization failed" in log_content:
                results["classifier_failed"] = True
                print("❌ RED STATE CONFIRMED: Classifier initialization failed")
            elif "CLASSIFIER: Ready for inference" in log_content:
                results["classifier_ready"] = True
                print("✅ Classifier initialized successfully")
            else:
                print("⚠️  Classifier initialization status unclear from logs")

        # Test each scenario
        for scenario in test_scenarios:
            print(f"\n🧪 Testing: {scenario['name']}")
            print(f"   Input: '{scenario['input']}'")
            print(f"   Expected mode: {scenario['expected_mode']}")

            try:
                response = process_action(
                    client,
                    user_id=user_id,
                    campaign_id=campaign_id,
                    user_input=scenario["input"],
                    mode=None,  # Let classifier decide
                )

                request_responses.append(
                    {
                        "scenario": scenario["name"],
                        "request": {"user_input": scenario["input"], "mode": None},
                        "response": response,
                    }
                )

                # Check logs for routing decision AFTER the request
                # Wait a moment for logs to flush
                time.sleep(0.5)
                
                if log_path and log_path.exists():
                    # Read fresh log content (read from end to get latest entries)
                    fresh_log = log_path.read_text(errors="ignore")
                    # Get last 5000 chars to check recent routing decisions (increased for better detection)
                    recent_log = fresh_log[-5000:] if len(fresh_log) > 5000 else fresh_log
                    
                    # Look for semantic intent classification log patterns
                    # Pattern: "SEMANTIC_INTENT_<MODE>: (<confidence>) -> <Agent>"
                    import re
                    expected_pattern = f"SEMANTIC_INTENT_{scenario['expected_mode']}"
                    story_fallback_pattern = "SEMANTIC_INTENT_STORY: \\(0\\.00\\)"
                    classifier_error_pattern = "CLASSIFIER.*failed|Model not ready|Initialization failed"
                    
                    # Check for expected routing
                    expected_match = re.search(rf"SEMANTIC_INTENT_{scenario['expected_mode']}.*?\(([\d.]+)\)", recent_log)
                    story_match = re.search(story_fallback_pattern, recent_log)
                    error_match = re.search(classifier_error_pattern, recent_log, re.IGNORECASE)
                    
                    if expected_match:
                        confidence = float(expected_match.group(1))
                        print(f"   ✅ Correctly routed to {scenario['expected_mode']} (confidence: {confidence:.2f})")
                        results["scenarios"].append(
                            {
                                "name": scenario["name"],
                                "campaign_id": campaign_id,
                                "passed": True,
                                "errors": [],
                                "routed_to": scenario["expected_mode"],
                                "confidence": confidence,
                            }
                        )
                    elif story_match:
                        print(f"   ❌ RED STATE: Defaulted to STORY (0.00) - classifier not working")
                        results["scenarios"].append(
                            {
                                "name": scenario["name"],
                                "campaign_id": campaign_id,
                                "passed": False,
                                "errors": [
                                    "Classifier defaulted to MODE_CHARACTER (0.00 confidence) - model not loaded"
                                ],
                                "routed_to": "CHARACTER",
                                "confidence": 0.00,
                            }
                        )
                    elif error_match:
                        error_line = error_match.group(0)
                        print(f"   ❌ RED STATE: Classifier error detected: {error_line[:80]}")
                        results["scenarios"].append(
                            {
                                "name": scenario["name"],
                                "campaign_id": campaign_id,
                                "passed": False,
                                "errors": [
                                    f"Classifier initialization error: {error_line[:100]}"
                                ],
                                "routed_to": "UNKNOWN",
                            }
                        )
                    else:
                        # Check for any SEMANTIC_INTENT log to see what happened
                        semantic_logs = [line for line in recent_log.splitlines() if "SEMANTIC_INTENT" in line]
                        if semantic_logs:
                            last_semantic = semantic_logs[-1]
                            # Extract mode and confidence
                            mode_match = re.search(r"SEMANTIC_INTENT_(\w+):", last_semantic)
                            conf_match = re.search(r"\(([\d.]+)\)", last_semantic)
                            actual_mode = mode_match.group(1) if mode_match else "UNKNOWN"
                            actual_conf = float(conf_match.group(1)) if conf_match else None
                            
                            print(f"   ⚠️  Found semantic routing: {actual_mode} (confidence: {actual_conf})")
                            print(f"      Expected: {scenario['expected_mode']}")
                            
                            if actual_mode == scenario['expected_mode']:
                                # Correct routing, just missed the pattern match
                                results["scenarios"].append(
                                    {
                                        "name": scenario["name"],
                                        "campaign_id": campaign_id,
                                        "passed": True,
                                        "errors": [],
                                        "routed_to": actual_mode,
                                        "confidence": actual_conf,
                                    }
                                )
                            else:
                                results["scenarios"].append(
                                    {
                                        "name": scenario["name"],
                                        "campaign_id": campaign_id,
                                        "passed": False,
                                        "errors": [f"Routed to {actual_mode} instead of {scenario['expected_mode']}"],
                                        "routed_to": actual_mode,
                                        "confidence": actual_conf,
                                    }
                                )
                        else:
                            # No semantic routing logs - check for other routing methods
                            if "CHARACTER_CREATION_ACTIVE" in recent_log:
                                print(f"   ⚠️  Routed via state check (CharacterCreationAgent) - semantic classifier may not have run")
                            elif "THINK_MODE_DETECTED" in recent_log:
                                print(f"   ⚠️  Routed via prefix check (PlanningAgent) - semantic classifier skipped")
                            elif "GOD_MODE_DETECTED" in recent_log:
                                print(f"   ⚠️  Routed via god mode - semantic classifier skipped")
                            else:
                                print(f"   ⚠️  No SEMANTIC_INTENT logs found - routing may have happened via other priority or default")
                            
                            results["scenarios"].append(
                                {
                                    "name": scenario["name"],
                                    "campaign_id": campaign_id,
                                    "passed": False,
                                    "errors": ["Could not verify semantic routing from logs - may have routed via state/prefix/default"],
                                    "log_snippet": recent_log[-500:] if len(recent_log) > 500 else recent_log,
                                }
                            )

                time.sleep(1)  # Small delay between requests

            except Exception as e:
                print(f"   ❌ Error: {e}")
                results["scenarios"].append(
                    {
                        "name": scenario["name"],
                        "campaign_id": campaign_id,
                        "passed": False,
                        "errors": [str(e)],
                    }
                )

        # Summary
        print(f"\n{'='*70}")
        print(f"📊 TEST SUMMARY")
        print(f"{'='*70}")
        total = len(results["scenarios"])
        passed = sum(1 for s in results["scenarios"] if s.get("passed", False))
        failed = total - passed

        print(f"Total scenarios: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Classifier failed to initialize: {results['classifier_failed']}")
        print(f"Classifier ready: {results['classifier_ready']}")

        if results["classifier_failed"] or failed > 0:
            print(f"\n❌ RED STATE CONFIRMED: Classifier is not working")
            print(f"   This is expected BEFORE the fix is applied")
        else:
            print(f"\n✅ Classifier appears to be working")

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
                server_env_overrides={"ENABLE_SEMANTIC_ROUTING": "true"} if local_server else None,
            )

            # Save request/response pairs
            save_request_responses(evidence_dir, request_responses)

            # Save server logs if available
            if log_path and log_path.exists():
                artifacts_dir = evidence_dir / "artifacts"
                artifacts_dir.mkdir(exist_ok=True)
                shutil.copy2(log_path, artifacts_dir / "server.log")

            # Create evidence bundle
            results_dict = {
                "scenarios": results["scenarios"],
                "summary": {
                    "total_scenarios": total,
                    "passed": passed,
                    "failed": failed,
                    "classifier_failed": results["classifier_failed"],
                    "classifier_ready": results["classifier_ready"],
                    "red_state_confirmed": results["classifier_failed"] or failed > 0,
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
        if results["classifier_failed"] or failed > 0:
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
    test_classifier_initialization_failure()
