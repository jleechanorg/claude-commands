#!/usr/bin/env python3
"""
Run 10 Sariel campaign replays to measure entity tracking desync rates.
This provides statistical significance for the architectural decision validation.
"""

import json
import os
import subprocess
import time
from datetime import datetime
from typing import Any

# Ensure we're in the project root
project_root = os.path.abspath(os.path.dirname(__file__))
os.chdir(project_root)


def run_single_sariel_test() -> dict[str, Any]:
    """Run a single Sariel campaign integration test and return results"""
    print("🎯 Starting Sariel campaign replay...")

    # Activate venv and run the test
    cmd = [
        "bash",
        "-c",
        "source /home/jleechan/projects/worldarchitect.ai/venv/bin/activate && "
        "cd mvp_site && "
        "TESTING=true python3 -m unittest tests.test_sariel_campaign_integration.TestSarielCampaignIntegration.test_sariel_campaign_replay -v",
    ]

    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    duration = time.time() - start_time

    if result.returncode == 0:
        print(f"✅ Test completed successfully in {duration:.1f}s")

        # Load the results file that was saved by the test
        results_path = os.path.join(
            "mvp_site", "tests", "data", "sariel_integration_test_results.json"
        )
        if os.path.exists(results_path):
            with open(results_path) as f:
                test_results = json.load(f)
            test_results["test_duration"] = duration
            return test_results
        print("⚠️ Results file not found, test may have failed to save results")
        return None
    print(f"❌ Test failed in {duration:.1f}s")
    print(f"STDOUT: {result.stdout}")
    print(f"STDERR: {result.stderr}")
    return None


def analyze_replay_results(all_results: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyze results from multiple replays"""
    if not all_results:
        return {"error": "No successful test results to analyze"}

    total_replays = len(all_results)
    total_interactions = sum(r.get("total_interactions", 0) for r in all_results)
    total_successful = sum(r.get("successful_tracking", 0) for r in all_results)

    # Calculate overall success rate
    overall_success_rate = (
        total_successful / total_interactions if total_interactions > 0 else 0
    )

    # Cassian problem tracking
    cassian_successes = sum(
        1 for r in all_results if r.get("cassian_problem_handled", False)
    )
    cassian_rate = cassian_successes / total_replays

    # Calculate success rates per replay
    individual_rates = [
        r.get("success_rate", 0) for r in all_results if "success_rate" in r
    ]

    # Entity-specific analysis
    entity_stats = {}
    interaction_stats = {}

    # Analyze each interaction across all replays
    for _replay_idx, replay_result in enumerate(all_results):
        for detail in replay_result.get("detailed_results", []):
            interaction_num = detail.get("interaction", 0)

            if interaction_num not in interaction_stats:
                interaction_stats[interaction_num] = {
                    "total_runs": 0,
                    "successful_runs": 0,
                    "entities_expected": detail.get("expected", []),
                    "success_by_entity": {},
                }

            interaction_stats[interaction_num]["total_runs"] += 1
            if detail.get("success", False):
                interaction_stats[interaction_num]["successful_runs"] += 1

            # Track entity-specific success
            expected = detail.get("expected", [])
            found = detail.get("found", [])

            for entity in expected:
                if entity not in entity_stats:
                    entity_stats[entity] = {"appearances": 0, "found": 0}
                entity_stats[entity]["appearances"] += 1
                if entity in found:
                    entity_stats[entity]["found"] += 1

    # Calculate per-interaction success rates
    for interaction_num in interaction_stats:
        stats = interaction_stats[interaction_num]
        stats["success_rate"] = stats["successful_runs"] / stats["total_runs"]

    # Calculate per-entity tracking rates
    for entity in entity_stats:
        stats = entity_stats[entity]
        stats["tracking_rate"] = (
            stats["found"] / stats["appearances"] if stats["appearances"] > 0 else 0
        )

    return {
        "summary": {
            "total_replays": total_replays,
            "total_interactions": total_interactions,
            "total_successful_tracking": total_successful,
            "overall_success_rate": overall_success_rate,
            "cassian_problem_rate": cassian_rate,
            "individual_success_rates": individual_rates,
            "avg_success_rate": sum(individual_rates) / len(individual_rates)
            if individual_rates
            else 0,
            "min_success_rate": min(individual_rates) if individual_rates else 0,
            "max_success_rate": max(individual_rates) if individual_rates else 0,
        },
        "entity_tracking": entity_stats,
        "interaction_analysis": interaction_stats,
        "raw_results": all_results,
    }


def main():
    """Run 10 Sariel campaign replays and analyze results"""
    print("🚀 Starting 10 Sariel Campaign Replays for Desync Rate Analysis")
    print("=" * 60)

    all_results = []
    successful_tests = 0

    for replay_num in range(1, 11):
        print(f"\n📋 REPLAY {replay_num}/10")
        print("-" * 30)

        test_result = run_single_sariel_test()

        if test_result:
            test_result["replay_number"] = replay_num
            all_results.append(test_result)
            successful_tests += 1

            # Quick summary
            success_rate = test_result.get("success_rate", 0)
            cassian_handled = test_result.get("cassian_problem_handled", False)
            print(f"   Success Rate: {success_rate:.1%}")
            print(f"   Cassian Problem: {'✅' if cassian_handled else '❌'}")
        else:
            print(f"   ❌ Replay {replay_num} failed")

        # Brief pause between tests to avoid overwhelming the API
        if replay_num < 10:
            print("   ⏳ Waiting 2 seconds...")
            time.sleep(2)

    print("\n🎯 REPLAY SUMMARY")
    print("=" * 60)
    print(f"Successful replays: {successful_tests}/10")

    if successful_tests > 0:
        print("\n📊 Analyzing results...")
        analysis = analyze_replay_results(all_results)

        # Save comprehensive results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"sariel_replays_analysis_{timestamp}.json"

        with open(results_file, "w") as f:
            json.dump(analysis, f, indent=2)

        print(f"✅ Analysis saved to: {results_file}")

        # Print key findings
        summary = analysis["summary"]
        print("\n🔍 KEY FINDINGS:")
        print(f"   Overall Success Rate: {summary['overall_success_rate']:.1%}")
        print(f"   Cassian Problem Rate: {summary['cassian_problem_rate']:.1%}")
        print(f"   Average Success Rate: {summary['avg_success_rate']:.1%}")
        print(
            f"   Range: {summary['min_success_rate']:.1%} - {summary['max_success_rate']:.1%}"
        )

        # Entity tracking breakdown
        print("\n👥 ENTITY TRACKING RATES:")
        entity_stats = analysis["entity_tracking"]
        for entity, stats in sorted(
            entity_stats.items(), key=lambda x: x[1]["tracking_rate"], reverse=True
        ):
            rate = stats["tracking_rate"]
            appearances = stats["appearances"]
            found = stats["found"]
            print(f"   {entity}: {rate:.1%} ({found}/{appearances})")

        # Most problematic interactions
        print("\n⚠️  INTERACTION ANALYSIS:")
        interaction_stats = analysis["interaction_analysis"]
        for interaction_num in sorted(interaction_stats.keys()):
            stats = interaction_stats[interaction_num]
            rate = stats["success_rate"]
            entities = ", ".join(stats["entities_expected"])
            print(
                f"   Interaction {interaction_num}: {rate:.1%} success (expects: {entities})"
            )
    else:
        print("❌ No successful tests to analyze")


if __name__ == "__main__":
    main()
