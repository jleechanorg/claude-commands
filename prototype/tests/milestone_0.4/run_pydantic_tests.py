#!/usr/bin/env python3
"""
Run Pydantic-only tests (Approach 2) for Milestone 0.4
"""

import json
import os
from datetime import datetime
import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from prototype.tests.milestone_0_4.test_structured_generation import TestHarness, TestApproach
from scripts.test_scenarios import get_all_scenarios


def run_pydantic_tests():
    """Run Pydantic-only approach on all campaigns and scenarios"""
    
    # Create test harness
    harness = TestHarness()
    
    # Override to only test Pydantic approach
    harness.config["approaches"] = [TestApproach.PYDANTIC_ONLY.value]
    
    print("Running Pydantic-Only Tests (Structured Generation)")
    print("="*60)
    
    # Test matrix
    campaigns = ["sariel_v2_001", "thornwood_001", "darkmoor_001", 
                 "brass_compass_001", "frostholm_001"]
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
                approach=TestApproach.PYDANTIC_ONLY
            )
            
            campaign_results.append(result)
            
            # Track by scenario
            if scenario not in results_by_scenario:
                results_by_scenario[scenario] = []
            results_by_scenario[scenario].append(result)
            
            print(f"Success: {result.success_rate:.1%}")
        
        results_by_campaign[campaign] = campaign_results
    
    # Calculate statistics
    print("\n" + "="*60)
    print("PYDANTIC-ONLY TEST RESULTS")
    print("="*60)
    
    # Overall stats
    all_results = [r for results in results_by_campaign.values() for r in results]
    overall_success = sum(r.success_rate for r in all_results) / len(all_results)
    overall_time = sum(r.total_time_ms for r in all_results) / len(all_results)
    
    print(f"\nOverall Performance:")
    print(f"  Average success rate: {overall_success:.1%}")
    print(f"  Average time: {overall_time:.2f}ms")
    print(f"  Total desync incidents: {sum(1 for r in all_results if r.desync_detected)}/{len(all_results)}")
    
    # Compare to baseline
    try:
        with open("analysis/test_results/baseline_test_results.json", 'r') as f:
            baseline = json.load(f)
            baseline_success = baseline["summary"]["average_success_rate"]
            improvement = ((overall_success - baseline_success) / baseline_success * 100) if baseline_success > 0 else 0
            print(f"  Improvement over baseline: {improvement:+.1f}%")
    except:
        print("  (Baseline comparison not available)")
    
    # By campaign
    print(f"\nBy Campaign:")
    for campaign, results in results_by_campaign.items():
        avg_success = sum(r.success_rate for r in results) / len(results)
        desyncs = sum(1 for r in results if r.desync_detected)
        print(f"  {campaign:20} Success: {avg_success:5.1%}  Desyncs: {desyncs}/{len(results)}")
    
    # By scenario  
    print(f"\nBy Scenario Type:")
    for scenario, results in results_by_scenario.items():
        avg_success = sum(r.success_rate for r in results) / len(results)
        desyncs = sum(1 for r in results if r.desync_detected)
        print(f"  {scenario:20} Success: {avg_success:5.1%}  Desyncs: {desyncs}/{len(results)}")
    
    # Structure effectiveness
    print(f"\nStructure Effectiveness:")
    simple_scenarios = ["multi_character", "split_party"]
    complex_scenarios = ["combat_injured", "hidden_characters", "npc_heavy"]
    
    simple_success = sum(r.success_rate for s in simple_scenarios for r in results_by_scenario.get(s, [])) / (len(simple_scenarios) * len(campaigns))
    complex_success = sum(r.success_rate for s in complex_scenarios for r in results_by_scenario.get(s, [])) / (len(complex_scenarios) * len(campaigns))
    
    print(f"  Simple scenarios: {simple_success:.1%}")
    print(f"  Complex scenarios: {complex_success:.1%}")
    print(f"  Difference: {simple_success - complex_success:+.1f}%")
    
    # Save detailed results
    output_dir = harness.config["output_dir"]
    os.makedirs(output_dir, exist_ok=True)
    
    pydantic_report = {
        "test_type": "pydantic_only",
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_tests": len(all_results),
            "average_success_rate": overall_success,
            "average_time_ms": overall_time,
            "total_desyncs": sum(1 for r in all_results if r.desync_detected),
            "improvement_over_baseline": improvement if 'improvement' in locals() else None
        },
        "by_campaign": {
            campaign: {
                "success_rate": sum(r.success_rate for r in results) / len(results),
                "desync_count": sum(1 for r in results if r.desync_detected),
                "average_time": sum(r.total_time_ms for r in results) / len(results)
            }
            for campaign, results in results_by_campaign.items()
        },
        "by_scenario": {
            scenario: {
                "success_rate": sum(r.success_rate for r in results) / len(results),
                "desync_count": sum(1 for r in results if r.desync_detected)
            }
            for scenario, results in results_by_scenario.items()
        },
        "structure_effectiveness": {
            "simple_scenarios": simple_success,
            "complex_scenarios": complex_success
        }
    }
    
    report_path = os.path.join(output_dir, "pydantic_test_results.json")
    with open(report_path, 'w') as f:
        json.dump(pydantic_report, f, indent=2)
    
    print(f"\nDetailed results saved to: {report_path}")
    
    # Save harness results too
    harness._save_results()
    
    return pydantic_report


if __name__ == "__main__":
    report = run_pydantic_tests()