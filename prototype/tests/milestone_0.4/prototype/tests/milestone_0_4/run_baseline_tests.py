#!/usr/bin/env python3
"""
Run baseline tests (Approach 1) for Milestone 0.4
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


def run_baseline_tests():
    """Run validation-only approach on all campaigns and scenarios"""

    # Create test harness
    harness = TestHarness()

    # Override to only test validation approach
    harness.config["approaches"] = [TestApproach.VALIDATION_ONLY.value]

    print("Running Baseline Tests (Validation-Only)")
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
                approach=TestApproach.VALIDATION_ONLY,
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
    print("BASELINE TEST RESULTS")
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

    # Desync patterns
    pattern_counts = {}
    for result in all_results:
        if result.desync_pattern:
            pattern_counts[result.desync_pattern] = (
                pattern_counts.get(result.desync_pattern, 0) + 1
            )

    print("\nDesync Patterns:")
    for pattern, count in sorted(
        pattern_counts.items(), key=lambda x: x[1], reverse=True
    ):
        print(f"  {pattern:25} {count:3} ({count / len(all_results) * 100:4.1f}%)")

    # Save detailed results
    output_dir = harness.config["output_dir"]
    os.makedirs(output_dir, exist_ok=True)

    baseline_report = {
        "test_type": "baseline_validation_only",
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_tests": len(all_results),
            "average_success_rate": overall_success,
            "average_time_ms": overall_time,
            "total_desyncs": sum(1 for r in all_results if r.desync_detected),
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
                "common_patterns": [
                    r.desync_pattern for r in results if r.desync_pattern
                ],
            }
            for scenario, results in results_by_scenario.items()
        },
        "pattern_distribution": pattern_counts,
    }

    report_path = os.path.join(output_dir, "baseline_test_results.json")
    with open(report_path, "w") as f:
        json.dump(baseline_report, f, indent=2)

    print(f"\nDetailed results saved to: {report_path}")

    # Save harness results too
    harness._save_results()

    return baseline_report


if __name__ == "__main__":
    report = run_baseline_tests()
