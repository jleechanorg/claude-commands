#!/usr/bin/env python3
"""
Test: Campaign Creation End-to-End via MCP Server

Executes comprehensive campaign creation test suite against WorldArchitect MCP server.
Saves all test results to /tmp/worldarchitect_test_results/[timestamp]/
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


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


def run_test_case_1(output_dir: Path) -> Dict[str, Any]:
    """Test Case 1: Dragon Knight Default Campaign"""
    print("\n" + "="*80)
    print("🧪 TEST CASE 1: Dragon Knight Default Campaign")
    print("="*80)

    test_result = {
        "test_name": "test_case_1_dragon_knight_default",
        "description": "Dragon Knight campaign with default character and setting",
        "passed": False,
        "timestamp": datetime.now().isoformat()
    }

    try:
        # This is a manual test execution guide
        # In practice, you would call the MCP server here via stdio
        print("\n📋 MANUAL EXECUTION REQUIRED:")
        print("1. Use MCP tool: mcp__worldarchitect__create_campaign")
        print("2. Parameters:")
        print("   - user_id: test_user_mcp_validation")
        print("   - title: Dragon Knight Default Test")
        print("   - character: (empty string)")
        print("   - setting: World of Assiah. Caught between an oath to a ruthless tyrant...")
        print("   - selected_prompts: ['defaultWorld', 'mechanicalPrecision', 'companions']")
        print("\n3. Expected: Campaign created with UUID, opening story generated")

        test_result["status"] = "MANUAL_EXECUTION_REQUIRED"
        test_result["instructions"] = "Execute via MCP worldarchitect create_campaign tool"

        save_test_result(output_dir, "test_case_1", test_result)
        return test_result

    except Exception as e:
        test_result["error"] = str(e)
        test_result["passed"] = False
        save_test_result(output_dir, "test_case_1", test_result)
        return test_result


def run_test_case_2(output_dir: Path) -> Dict[str, Any]:
    """Test Case 2: Custom Campaign Random Character/World"""
    print("\n" + "="*80)
    print("🧪 TEST CASE 2: Custom Campaign Random Character/World")
    print("="*80)

    test_result = {
        "test_name": "test_case_2_custom_random",
        "description": "Custom campaign with empty character/setting for AI random generation",
        "passed": False,
        "timestamp": datetime.now().isoformat()
    }

    try:
        print("\n📋 MANUAL EXECUTION REQUIRED:")
        print("1. Use MCP tool: mcp__worldarchitect__create_campaign")
        print("2. Parameters:")
        print("   - user_id: test_user_mcp_validation")
        print("   - title: Custom Random Test")
        print("   - character: (empty string)")
        print("   - setting: (empty string)")
        print("   - selected_prompts: ['defaultWorld', 'mechanicalPrecision', 'companions']")
        print("\n3. Expected: AI generates random character and world")

        test_result["status"] = "MANUAL_EXECUTION_REQUIRED"
        test_result["instructions"] = "Execute via MCP worldarchitect create_campaign tool"

        save_test_result(output_dir, "test_case_2", test_result)
        return test_result

    except Exception as e:
        test_result["error"] = str(e)
        test_result["passed"] = False
        save_test_result(output_dir, "test_case_2", test_result)
        return test_result


def run_test_case_3(output_dir: Path) -> Dict[str, Any]:
    """Test Case 3: Custom Campaign Full Customization"""
    print("\n" + "="*80)
    print("🧪 TEST CASE 3: Custom Campaign Full Customization")
    print("="*80)

    test_result = {
        "test_name": "test_case_3_custom_full",
        "description": "Custom campaign with full character, setting, and description",
        "passed": False,
        "timestamp": datetime.now().isoformat()
    }

    try:
        print("\n📋 MANUAL EXECUTION REQUIRED:")
        print("1. Use MCP tool: mcp__worldarchitect__create_campaign")
        print("2. Parameters:")
        print("   - user_id: test_user_mcp_validation")
        print("   - title: Custom Full Test")
        print("   - character: Zara the Mystic")
        print("   - setting: Floating islands connected by rainbow bridges in the realm of Aethermoor")
        print("   - description: A world where magic flows through crystalline ley lines")
        print("   - selected_prompts: ['mechanicalPrecision', 'companions']")
        print("\n3. Expected: Campaign created with custom world-building")

        test_result["status"] = "MANUAL_EXECUTION_REQUIRED"
        test_result["instructions"] = "Execute via MCP worldarchitect create_campaign tool"

        save_test_result(output_dir, "test_case_3", test_result)
        return test_result

    except Exception as e:
        test_result["error"] = str(e)
        test_result["passed"] = False
        save_test_result(output_dir, "test_case_3", test_result)
        return test_result


def run_test_case_4(output_dir: Path) -> Dict[str, Any]:
    """Test Case 4: Real API Integration Verification"""
    print("\n" + "="*80)
    print("🧪 TEST CASE 4: Real API Integration Verification")
    print("="*80)

    test_result = {
        "test_name": "test_case_4_real_api_integration",
        "description": "Verify real Gemini API and Firebase integration",
        "passed": False,
        "timestamp": datetime.now().isoformat()
    }

    try:
        print("\n📋 MANUAL VERIFICATION REQUIRED:")
        print("1. Use MCP tool: mcp__worldarchitect__get_campaigns_list")
        print("2. Parameters:")
        print("   - user_id: test_user_mcp_validation")
        print("\n3. Verify:")
        print("   - All 3 test campaigns appear in list")
        print("   - Campaign IDs are UUIDs (not mock IDs like 'campaign-12345')")
        print("   - All campaigns have unique, generated content")
        print("\n4. Use MCP tool: mcp__worldarchitect__get_campaign_state")
        print("5. Parameters:")
        print("   - user_id: test_user_mcp_validation")
        print("   - campaign_id: (one of the test campaign IDs)")
        print("\n6. Verify:")
        print("   - D&D attribute system present (STR, DEX, CON, INT, WIS, CHA)")
        print("   - Game state structure complete")
        print("   - Firebase persistence confirmed")

        test_result["status"] = "MANUAL_VERIFICATION_REQUIRED"
        test_result["instructions"] = "Execute via MCP worldarchitect list/get tools"

        save_test_result(output_dir, "test_case_4", test_result)
        return test_result

    except Exception as e:
        test_result["error"] = str(e)
        test_result["passed"] = False
        save_test_result(output_dir, "test_case_4", test_result)
        return test_result


def main():
    """Execute all test cases and generate summary report"""
    print("\n" + "🌟"*40)
    print("WorldArchitect MCP Server - Campaign Creation Test Suite")
    print("🌟"*40)

    # Create output directory
    output_dir = create_test_output_dir()

    # Execute test cases
    test_results: List[Dict[str, Any]] = []

    test_results.append(run_test_case_1(output_dir))
    test_results.append(run_test_case_2(output_dir))
    test_results.append(run_test_case_3(output_dir))
    test_results.append(run_test_case_4(output_dir))

    # Generate summary
    passed_count = sum(1 for r in test_results if r.get("passed", False))
    total_count = len(test_results)

    summary = {
        "timestamp": datetime.now().isoformat(),
        "user_id": "test_user_mcp_validation",
        "mcp_server": "worldarchitect",
        "test_suite": "campaign_creation",
        "total_count": total_count,
        "passed_count": passed_count,
        "failed_count": total_count - passed_count,
        "all_passed": passed_count == total_count,
        "test_cases": test_results,
        "output_directory": str(output_dir)
    }

    save_test_summary(output_dir, summary)

    # Print final summary
    print("\n" + "="*80)
    print("📊 TEST EXECUTION SUMMARY")
    print("="*80)
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
