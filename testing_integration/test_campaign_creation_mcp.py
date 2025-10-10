#!/usr/bin/env python3
"""
Test: Campaign Creation End-to-End via MCP Server

Executes comprehensive campaign creation test suite against WorldArchitect MCP server.
Saves all test results to /tmp/worldarchitect_test_results/[timestamp]/
"""

import json
import os
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import requests

from mvp_site import constants

MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL")
MCP_REQUEST_TIMEOUT = float(os.environ.get("MCP_REQUEST_TIMEOUT", "240"))
DEFAULT_TEST_USER = os.environ.get("MCP_TEST_USER_ID")
AUTO_MODE = bool(MCP_SERVER_URL)


def _generate_user_id() -> str:
    if DEFAULT_TEST_USER:
        return DEFAULT_TEST_USER
    unique_suffix = datetime.now().strftime("%Y%m%d%H%M%S") + uuid.uuid4().hex[:6]
    return f"codex_mcp_autotest_{unique_suffix}"


def call_mcp_tool(name: str, arguments: Dict[str, Any], *, request_id: str | None = None) -> Dict[str, Any]:
    if not MCP_SERVER_URL:
        raise RuntimeError("MCP_SERVER_URL environment variable is not set.")

    request_payload = {
        "jsonrpc": "2.0",
        "id": request_id or f"{name}_{uuid.uuid4().hex}",
        "method": "tools/call",
        "params": {
            "name": name,
            "arguments": arguments,
        },
    }

    arg_keys = ", ".join(sorted(arguments.keys())) or "<no args>"
    print(f"→ Calling MCP tool '{name}' (args: {arg_keys})")

    response = requests.post(
        MCP_SERVER_URL,
        json=request_payload,
        timeout=MCP_REQUEST_TIMEOUT,
    )
    response.raise_for_status()

    data = response.json()
    if "error" in data and data["error"]:
        raise RuntimeError(f"JSON-RPC error: {data['error']}")

    result = data.get("result")
    if isinstance(result, dict):
        status = result.get("success")
        status_text = "success" if status else "error"
        print(f"← MCP tool '{name}' completed ({status_text})")
        return result

    if isinstance(result, str):
        try:
            return json.loads(result)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Unexpected non-JSON response: {result}") from exc

    raise RuntimeError(f"Unexpected response payload: {data}")


def truncate_text(value: str | None, limit: int = 4000) -> str:
    if value is None:
        return ""
    if len(value) <= limit:
        return value
    return f"{value[:limit]}...[truncated]"



def create_test_output_dir() -> Path:
    """Create unique test output directory in /tmp/"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"/tmp/worldarchitect_test_results/{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Test results will be saved to: {output_dir}")
    return output_dir


def save_test_result(output_dir: Path, test_name: str, result_data: Dict[str, Any]) -> None:
    """Save individual test result to JSON file"""
    result_file = output_dir / f"{test_name}.json"
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(result_data, f, indent=2, ensure_ascii=False)
    print(f"💾 Saved: {result_file.name}")


def save_test_summary(output_dir: Path, summary_data: Dict[str, Any]) -> None:
    """Save overall test summary"""
    summary_file = output_dir / "test_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)

    # Also save human-readable markdown report
    report_file = output_dir / "test_report.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(generate_markdown_report(summary_data))

    print(f"\n📊 Test Summary: {summary_file}")
    print(f"📄 Test Report: {report_file}")


def generate_markdown_report(summary_data: Dict[str, Any]) -> str:
    """Generate human-readable markdown test report"""
    report_lines = [
        "# WorldArchitect MCP Server Test Report",
        f"\n**Test Execution Time**: {summary_data['timestamp']}",
        f"**Overall Result**: {'✅ PASS' if summary_data['all_passed'] else '❌ FAIL'}",
        f"**Tests Passed**: {summary_data['passed_count']}/{summary_data['total_count']}",
        "\n---\n",
        "\n## Test Cases\n"
    ]

    for test in summary_data.get("test_cases", []):
        status = "✅ PASS" if test["passed"] else "❌ FAIL"
        test_name = test.get("test_name", "Unknown Test")
        report_lines.append(f"\n### {test_name} {status}\n")

        if test.get("campaign_id"):
            report_lines.append(f"- **Campaign ID**: {test['campaign_id']}")
        if test.get("title"):
            report_lines.append(f"- **Title**: {test['title']}")
        if test.get("character"):
            report_lines.append(f"- **Character**: {test['character']}")
        if test.get("setting"):
            report_lines.append(f"- **Setting**: {test['setting'][:100]}...")
        if test.get("error"):
            report_lines.append(f"- **Error**: {test['error']}")
        report_lines.append("")

    report_lines.append("\n---\n\n## Test Configuration\n")
    report_lines.append(f"- **User ID**: {summary_data.get('user_id', 'N/A')}")
    report_lines.append(f"- **MCP Server**: {summary_data.get('mcp_server', 'worldarchitect')}")
    report_lines.append(f"- **Test Suite**: {summary_data.get('test_suite', 'campaign_creation')}")

    return "\n".join(report_lines)


def run_test_case_1(output_dir: Path, context: Dict[str, Any]) -> Dict[str, Any]:
    """Test Case 1: Dragon Knight Default Campaign"""
    print("\n" + "=" * 80)
    print("🧪 TEST CASE 1: Dragon Knight Default Campaign")
    print("=" * 80)
    test_result = {
        "test_name": "test_case_1_dragon_knight_default",
        "description": "Dragon Knight campaign with default character and setting",
        "passed": False,
        "timestamp": datetime.now().isoformat(),
    }

    if AUTO_MODE:
        try:
            print("🤖 AUTO: Creating default Dragon Knight campaign via MCP")
            arguments = {
                "user_id": context["user_id"],
                "title": "Dragon Knight Default Test",
                "character": "",
                "setting": (
                    "World of Assiah. Caught between an oath to a ruthless tyrant "
                    "and a vow to protect the innocent."
                ),
                "selected_prompts": [
                    "defaultWorld",
                    "mechanicalPrecision",
                    "companions",
                ],
                "custom_options": ["defaultWorld", "companions"],
            }

            response = call_mcp_tool("create_campaign", arguments)
            test_result["response"] = response

            campaign_id = response.get("success") and response.get("campaign_id")
            if campaign_id:
                test_result["campaign_id"] = campaign_id
                test_result["title"] = response.get("title")
                opening_story = response.get("opening_story")
                if opening_story:
                    test_result["opening_story_preview"] = truncate_text(opening_story, 1200)
                test_result["passed"] = True
                context.setdefault("campaigns", []).append(
                    {"id": campaign_id, "title": response.get("title", "")}
                )
                print(f"✅ Created campaign {campaign_id} for user {context['user_id']}")
            else:
                test_result["error"] = response.get(
                    "error", "Create campaign returned no campaign_id"
                )

        except (requests.RequestException, json.JSONDecodeError, RuntimeError) as exc:
            test_result["error"] = str(exc)
            print(f"❌ AUTO: Test case 1 failed: {exc}")
    else:
        print("\n📋 MANUAL EXECUTION REQUIRED:")
        print("1. Use MCP tool: mcp__worldarchitect__create_campaign")
        print("2. Parameters:")
        print("   - user_id: test_user_mcp_validation")
        print("   - title: Dragon Knight Default Test")
        print("   - character: (empty string)")
        print(
            "   - setting: World of Assiah. Caught between an oath to a ruthless tyrant..."
        )
        print(
            "   - selected_prompts: ['defaultWorld', 'mechanicalPrecision', 'companions']"
        )
        print("\n3. Expected: Campaign created with UUID, opening story generated")

        test_result["status"] = "MANUAL_EXECUTION_REQUIRED"
        test_result["instructions"] = (
            "Execute via MCP worldarchitect create_campaign tool"
        )

    save_test_result(output_dir, "test_case_1", test_result)
    return test_result


def run_test_case_2(output_dir: Path, context: Dict[str, Any]) -> Dict[str, Any]:
    """Test Case 2: Custom Campaign Random Character/World"""
    print("\n" + "=" * 80)
    print("🧪 TEST CASE 2: Custom Campaign Random Character/World")
    print("=" * 80)
    test_result = {
        "test_name": "test_case_2_custom_random",
        "description": "Custom campaign with empty character/setting for AI random generation",
        "passed": False,
        "timestamp": datetime.now().isoformat(),
    }

    if AUTO_MODE:
        try:
            print("🤖 AUTO: Creating random campaign (Test Case 2)")
            title = f"Custom Random Test {context['run_id']}"
            arguments = {
                "user_id": context["user_id"],
                "title": title,
                "character": "",
                "setting": "",
                "selected_prompts": [
                    "defaultWorld",
                    "mechanicalPrecision",
                    "companions",
                ],
                "custom_options": ["companions"],
            }

            response = call_mcp_tool("create_campaign", arguments)
            test_result["response"] = response

            campaign_id = response.get("success") and response.get("campaign_id")
            if campaign_id:
                test_result["campaign_id"] = campaign_id
                test_result["title"] = response.get("title", title)
                test_result["passed"] = True
                context.setdefault("campaigns", []).append(
                    {"id": campaign_id, "title": response.get("title", title)}
                )
                print(f"✅ Random campaign created with id {campaign_id}")
            else:
                test_result["error"] = response.get(
                    "error", "Random campaign creation did not succeed"
                )

        except (requests.RequestException, json.JSONDecodeError, RuntimeError) as exc:
            test_result["error"] = str(exc)
            print(f"❌ AUTO: Test case 2 failed: {exc}")
    else:
        print("📋 MANUAL EXECUTION REQUIRED:")
        print("1. Use MCP tool: mcp__worldarchitect__create_campaign")
        print("2. Parameters:")
        print("   - user_id: test_user_mcp_validation")
        print("   - title: Custom Random Test")
        print("   - character: (empty string)")
        print("   - setting: (empty string)")
        print(
            "   - selected_prompts: ['defaultWorld', 'mechanicalPrecision', 'companions']"
        )
        print("3. Expected: AI generates random character and world")

        test_result["status"] = "MANUAL_EXECUTION_REQUIRED"
        test_result["instructions"] = (
            "Execute via MCP worldarchitect create_campaign tool"
        )

    save_test_result(output_dir, "test_case_2", test_result)
    return test_result


def run_test_case_3(output_dir: Path, context: Dict[str, Any]) -> Dict[str, Any]:
    """Test Case 3: Custom Campaign Full Customization"""
    print("\n" + "=" * 80)
    print("🧪 TEST CASE 3: Custom Campaign Full Customization")
    print("=" * 80)
    test_result = {
        "test_name": "test_case_3_custom_full",
        "description": "Custom campaign with full character, setting, and description",
        "passed": False,
        "timestamp": datetime.now().isoformat(),
    }

    if AUTO_MODE:
        try:
            print("🤖 AUTO: Creating fully customized campaign (Test Case 3)")
            title = f"Custom Full Test {context['run_id']}"
            arguments = {
                "user_id": context["user_id"],
                "title": title,
                "character": "Zara the Mystic",
                "setting": (
                    "Floating islands connected by rainbow bridges in the realm of Aethermoor"
                ),
                "description": "A world where magic flows through crystalline ley lines",
                "selected_prompts": ["mechanicalPrecision", "companions"],
                "custom_options": ["companions"],
            }

            response = call_mcp_tool("create_campaign", arguments)
            test_result["response"] = response

            campaign_id = response.get("success") and response.get("campaign_id")
            if campaign_id:
                test_result["campaign_id"] = campaign_id
                test_result["title"] = response.get("title", title)
                opening_story = response.get("opening_story")
                if opening_story:
                    test_result["opening_story_preview"] = truncate_text(opening_story, 1200)
                test_result["passed"] = True
                context.setdefault("campaigns", []).append(
                    {"id": campaign_id, "title": response.get("title", title)}
                )
                print(f"✅ Custom campaign created with id {campaign_id}")
            else:
                test_result["error"] = response.get(
                    "error", "Custom campaign creation did not succeed"
                )

        except (requests.RequestException, json.JSONDecodeError, RuntimeError) as exc:
            test_result["error"] = str(exc)
            print(f"❌ AUTO: Test case 3 failed: {exc}")
    else:
        print("📋 MANUAL EXECUTION REQUIRED:")
        print("1. Use MCP tool: mcp__worldarchitect__create_campaign")
        print("2. Parameters:")
        print("   - user_id: test_user_mcp_validation")
        print("   - title: Custom Full Test")
        print("   - character: Zara the Mystic")
        print(
            "   - setting: Floating islands connected by rainbow bridges in the realm of Aethermoor"
        )
        print(
            "   - description: A world where magic flows through crystalline ley lines"
        )
        print("   - selected_prompts: ['mechanicalPrecision', 'companions']")
        print("3. Expected: Campaign created with custom world-building")

        test_result["status"] = "MANUAL_EXECUTION_REQUIRED"
        test_result["instructions"] = (
            "Execute via MCP worldarchitect create_campaign tool"
        )

    save_test_result(output_dir, "test_case_3", test_result)
    return test_result


def run_test_case_4(output_dir: Path, context: Dict[str, Any]) -> Dict[str, Any]:
    """Test Case 4: Real API Integration Verification"""
    print("\n" + "=" * 80)
    print("🧪 TEST CASE 4: Real API Integration Verification")
    print("=" * 80)
    test_result = {
        "test_name": "test_case_4_real_api_integration",
        "description": "Verify real Gemini API and Firebase integration",
        "passed": False,
        "timestamp": datetime.now().isoformat(),
        "campaign_checks": [],
    }

    if AUTO_MODE:
        try:
            print("🤖 AUTO: Fetching campaign list for verification")
            list_args = {"user_id": context["user_id"], "limit": 20}
            campaigns_response = call_mcp_tool("get_campaigns_list", list_args)
            test_result["campaigns_list_response"] = campaigns_response

            if not campaigns_response.get("success"):
                test_result["error"] = campaigns_response.get(
                    "error", "Failed to retrieve campaigns list"
                )
            else:
                campaigns = campaigns_response.get("campaigns", [])
                test_result["campaigns_list_count"] = len(campaigns)
                campaign_ids = {
                    campaign.get("id") for campaign in campaigns if campaign.get("id")
                }

                missing = [
                    entry["id"]
                    for entry in context.get("campaigns", [])
                    if entry["id"] not in campaign_ids
                ]

                if missing:
                    test_result["error"] = f"Missing campaigns in list: {missing}"
                    print(f"❌ AUTO: Missing campaigns in list response: {missing}")
                else:
                    attribute_checks_passed = True
                    for entry in context.get("campaigns", []):
                        state_args = {
                            "user_id": context["user_id"],
                            "campaign_id": entry["id"],
                        }
                        print(f"🤖 AUTO: Fetching state for campaign {entry['id']}")
                        state_response = call_mcp_tool(
                            "get_campaign_state", state_args
                        )
                        detail = {
                            "campaign_id": entry["id"],
                            "title": entry.get("title"),
                            "success": state_response.get("success", False),
                        }

                        if state_response.get("success"):
                            game_state = state_response.get("game_state", {})
                            attr_system = (
                                game_state.get("custom_campaign_state", {}).get(
                                    "attribute_system"
                                )
                            )
                            detail["attribute_system"] = attr_system
                            if attr_system != constants.ATTRIBUTE_SYSTEM_DND:
                                detail["error"] = "Attribute system mismatch"
                                attribute_checks_passed = False
                                print(
                                    f"❌ AUTO: Attribute system mismatch for {entry['id']}: {attr_system}"
                                )
                        else:
                            detail["error"] = state_response.get(
                                "error", "State retrieval failed"
                            )
                            attribute_checks_passed = False
                            print(
                                f"❌ AUTO: State retrieval failed for {entry['id']}: {detail['error']}"
                            )

                        test_result["campaign_checks"].append(detail)

                    if attribute_checks_passed:
                        test_result["passed"] = True
                        print("✅ AUTO: Campaign state verification passed")
                    else:
                        test_result.setdefault("error", "Attribute validation failed")

        except (requests.RequestException, json.JSONDecodeError, RuntimeError) as exc:
            test_result["error"] = str(exc)
            print(f"❌ AUTO: Test case 4 failed: {exc}")
    else:
        print("📋 MANUAL VERIFICATION REQUIRED:")
        print("1. Use MCP tool: mcp__worldarchitect__get_campaigns_list")
        print("2. Parameters:")
        print("   - user_id: test_user_mcp_validation")
        print("3. Verify:")
        print("   - All 3 test campaigns appear in list")
        print("   - Campaign IDs are UUIDs (not mock IDs like 'campaign-12345')")
        print("   - All campaigns have unique, generated content")
        print("4. Use MCP tool: mcp__worldarchitect__get_campaign_state")
        print("5. Parameters:")
        print("   - user_id: test_user_mcp_validation")
        print("   - campaign_id: (one of the test campaign IDs)")
        print("6. Verify:")
        print("   - D&D attribute system present (STR, DEX, CON, INT, WIS, CHA)")
        print("   - Game state structure complete")
        print("   - Firebase persistence confirmed")

        test_result["status"] = "MANUAL_VERIFICATION_REQUIRED"
        test_result["instructions"] = (
            "Execute via MCP worldarchitect list/get tools"
        )

    save_test_result(output_dir, "test_case_4", test_result)
    return test_result


def main():
    """Execute all test cases and generate summary report"""
    print("\n" + "🌟" * 40)
    print("WorldArchitect MCP Server - Campaign Creation Test Suite")
    print("🌟" * 40)
    print(f"AUTO_MODE={AUTO_MODE}, MCP_SERVER_URL={MCP_SERVER_URL}")
    # Create output directory
    output_dir = create_test_output_dir()

    user_id = _generate_user_id() if AUTO_MODE else "test_user_mcp_validation"
    context: Dict[str, Any] = {
        "user_id": user_id,
        "campaigns": [],
        "run_id": uuid.uuid4().hex[:6],
        "server_url": MCP_SERVER_URL,
    }

    # Execute test cases
    test_results: List[Dict[str, Any]] = []

    test_results.append(run_test_case_1(output_dir, context))
    test_results.append(run_test_case_2(output_dir, context))
    test_results.append(run_test_case_3(output_dir, context))
    test_results.append(run_test_case_4(output_dir, context))

    # Generate summary
    passed_count = sum(1 for r in test_results if r.get("passed", False))
    total_count = len(test_results)

    summary = {
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "mcp_server": context.get("server_url", "worldarchitect"),
        "test_suite": "campaign_creation",
        "total_count": total_count,
        "passed_count": passed_count,
        "failed_count": total_count - passed_count,
        "all_passed": passed_count == total_count,
        "test_cases": test_results,
        "output_directory": str(output_dir),
        "automation_mode": AUTO_MODE,
    }

    save_test_summary(output_dir, summary)

    # Print final summary
    print("\n" + "=" * 80)
    print("📊 TEST EXECUTION SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {total_count}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {total_count - passed_count}")
    print(f"Status: {'✅ ALL PASS' if summary['all_passed'] else '❌ SOME FAILURES'}")
    print(f"\n📁 Results saved to: {output_dir}")
    print("="*80 + "\n")

    # Return exit code
    return 0 if summary["all_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
