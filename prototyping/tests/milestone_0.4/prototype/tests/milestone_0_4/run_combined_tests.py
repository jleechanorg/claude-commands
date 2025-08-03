#!/usr/bin/env python3
"""
Run Combined tests (Approach 3) for Milestone 0.4
"""

import json
import os
import sys
from datetime import datetime

project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.insert(0, project_root)

from prototype.tests.milestone_0_4.test_structured_generation import (
    TestApproach,
    TestHarness,
)
from scripts.test_scenarios import get_all_scenarios


def run_combined_tests():
    """Run Combined approach on all campaigns and scenarios"""

    # Create test harness
    harness = TestHarness()

    # Override to only test Combined approach
    harness.config["approaches"] = [TestApproach.COMBINED.value]

    print("Running Combined Tests (Structure + Validation)")
    print("=" * 60)

    # Test matrix
    campaigns = [
        "sariel_v2_001",
        "thornwood_001",
        "darkmoor_001",
        "brass_compass_001",
        "frostholm_001",
    ]
    scenarios = get_all_scenarios()

    total_tests = len(campaigns) * len(scenarios)
    print(f"Total tests to run: {total_tests}")
    print(f"Campaigns: {len(campaigns)}")
    print(f"Scenarios: {len(scenarios)}")
    print()

    # Run tests
    results_by_campaign = {}
    results_by_scenario = {}

    test_num = 0
    for campaign in campaigns:
        campaign_results = []

        for scenario in scenarios:
            test_num += 1
            print(f"Test {test_num}/{total_tests}: {campaign}/{scenario}", end="... ")

            result = harness._run_single_test(
                campaign_id=campaign,
                scenario_id=scenario,
                approach=TestApproach.COMBINED,
            )

            campaign_results.append(result)

            # Track by scenario
            if scenario not in results_by_scenario:
                results_by_scenario[scenario] = []
            results_by_scenario[scenario].append(result)

            print(f"Success: {result.success_rate:.1%}")

        results_by_campaign[campaign] = campaign_results

    # Calculate statistics
    print("\n" + "=" * 60)
    print("COMBINED APPROACH TEST RESULTS")
    print("=" * 60)

    # Overall stats
    all_results = [r for results in results_by_campaign.values() for r in results]
    overall_success = sum(r.success_rate for r in all_results) / len(all_results)
    overall_time = sum(r.total_time_ms for r in all_results) / len(all_results)

    print("\nOverall Performance:")
    print(f"  Average success rate: {overall_success:.1%}")
    print(f"  Average time: {overall_time:.2f}ms")
    print(
        f"  Total desync incidents: {sum(1 for r in all_results if r.desync_detected)}/{len(all_results)}"
    )

    # Compare to other approaches
    improvements = {}
    try:
        with open("analysis/test_results/baseline_test_results.json") as f:
            baseline = json.load(f)
            baseline_success = baseline["summary"]["average_success_rate"]
            improvements["baseline"] = (
                ((overall_success - baseline_success) / baseline_success * 100)
                if baseline_success > 0
                else 0
            )
    except:
        pass

    try:
        with open("analysis/test_results/pydantic_test_results.json") as f:
            pydantic = json.load(f)
            pydantic_success = pydantic["summary"]["average_success_rate"]
            improvements["pydantic"] = (
                ((overall_success - pydantic_success) / pydantic_success * 100)
                if pydantic_success > 0
                else 0
            )
    except:
        pass

    if improvements:
        print("\nImprovements:")
        for approach, improvement in improvements.items():
            print(f"  Over {approach}: {improvement:+.1f}%")

    # By campaign
    print("\nBy Campaign:")
    for campaign, results in results_by_campaign.items():
        avg_success = sum(r.success_rate for r in results) / len(results)
        desyncs = sum(1 for r in results if r.desync_detected)
        print(
            f"  {campaign:20} Success: {avg_success:5.1%}  Desyncs: {desyncs}/{len(results)}"
        )

    # By scenario
    print("\nBy Scenario Type:")
    for scenario, results in results_by_scenario.items():
        avg_success = sum(r.success_rate for r in results) / len(results)
        desyncs = sum(1 for r in results if r.desync_detected)
        print(
            f"  {scenario:20} Success: {avg_success:5.1%}  Desyncs: {desyncs}/{len(results)}"
        )

    # Synergy analysis
    print("\nSynergy Analysis:")

    # Check if combined is better than either alone
    if "baseline" in improvements and "pydantic" in improvements:
        if improvements["baseline"] > 0 and improvements["pydantic"] > 0:
            print("  Combined approach outperforms both individual approaches!")
        elif improvements["pydantic"] < 0:
            print("  Validation layer may be hindering structured generation")
        else:
            print("  Marginal improvement over structured approach alone")

    # Overhead analysis
    avg_validation_time = sum(r.validation_time_ms for r in all_results) / len(
        all_results
    )
    print(f"  Average validation overhead: {avg_validation_time:.2f}ms")

    # Save detailed results
    output_dir = harness.config["output_dir"]
    os.makedirs(output_dir, exist_ok=True)

    combined_report = {
        "test_type": "combined",
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_tests": len(all_results),
            "average_success_rate": overall_success,
            "average_time_ms": overall_time,
            "total_desyncs": sum(1 for r in all_results if r.desync_detected),
            "improvements": improvements,
        },
        "by_campaign": {
            campaign: {
                "success_rate": sum(r.success_rate for r in results) / len(results),
                "desync_count": sum(1 for r in results if r.desync_detected),
                "average_time": sum(r.total_time_ms for r in results) / len(results),
            }
            for campaign, results in results_by_campaign.items()
        },
        "by_scenario": {
            scenario: {
                "success_rate": sum(r.success_rate for r in results) / len(results),
                "desync_count": sum(1 for r in results if r.desync_detected),
            }
            for scenario, results in results_by_scenario.items()
        },
        "synergy_metrics": {
            "validation_overhead_ms": avg_validation_time,
            "beats_both_approaches": improvements.get("baseline", 0) > 0
            and improvements.get("pydantic", 0) > 0,
        },
    }

    report_path = os.path.join(output_dir, "combined_test_results.json")
    with open(report_path, "w") as f:
        json.dump(combined_report, f, indent=2)

    print(f"\nDetailed results saved to: {report_path}")

    # Save harness results too
    harness._save_results()

    return combined_report


if __name__ == "__main__":
    report = run_combined_tests()
