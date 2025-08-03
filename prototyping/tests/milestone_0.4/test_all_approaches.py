#!/usr/bin/env python3
"""
Test all three approaches and compare results
"""

from test_structured_generation import TestApproach, TestHarness


def test_all_approaches():
    """Test all approaches on same scenario"""

    harness = TestHarness()
    results = []

    # Test each approach
    for approach in TestApproach:
        result = harness._run_single_test(
            campaign_id="test_campaign",
            scenario_id="multi_character",
            approach=approach,
        )
        results.append(result)

        print(f"\n{approach.value.upper()} Results:")
        print(f"  Success rate: {result.success_rate:.2%}")
        print(f"  Found: {result.entities_found}")
        print(f"  Missing: {result.entities_missing}")
        print(f"  Time: {result.total_time_ms:.2f}ms")
        print(f"  Tokens: ~{result.estimated_tokens}")
        print(f"  Narrative: {result.narrative_excerpt}")

    # Compare results
    print("\n" + "=" * 60)
    print("COMPARISON SUMMARY")
    print("=" * 60)

    for i, approach in enumerate(TestApproach):
        r = results[i]
        print(
            f"{approach.value:20} | Success: {r.success_rate:6.1%} | Time: {r.total_time_ms:6.2f}ms | Cost: ${r.estimated_cost:.4f}"
        )

    # Calculate improvements
    baseline = results[0].success_rate
    pydantic_improvement = (
        (results[1].success_rate - baseline) / baseline * 100 if baseline > 0 else 0
    )
    combined_improvement = (
        (results[2].success_rate - baseline) / baseline * 100 if baseline > 0 else 0
    )

    print("\nImprovement over baseline:")
    print(f"  Pydantic-only: {pydantic_improvement:+.1f}%")
    print(f"  Combined:      {combined_improvement:+.1f}%")


if __name__ == "__main__":
    print("Testing All Three Approaches")
    print("=" * 60)

    test_all_approaches()
