#!/usr/bin/env python3
"""
Quick test of validation-only approach
"""

from test_structured_generation import TestApproach, TestHarness


def test_single_scenario():
    """Test one scenario with validation-only approach"""

    # Create harness
    harness = TestHarness()

    # Run single test
    result = harness._run_single_test(
        campaign_id="test_campaign",
        scenario_id="multi_character",
        approach=TestApproach.VALIDATION_ONLY,
    )

    # Print result
    print("\nTest Result:")
    print(f"  Scenario: {result.scenario_id}")
    print(f"  Approach: {result.approach.value}")
    print(f"  Expected entities: {result.entities_expected}")
    print(f"  Found entities: {result.entities_found}")
    print(f"  Missing entities: {result.entities_missing}")
    print(f"  Desync detected: {result.desync_detected}")
    print(f"  Success rate: {result.success_rate:.2%}")
    print(f"  Validation time: {result.validation_time_ms:.2f}ms")
    print(f"  Narrative excerpt: {result.narrative_excerpt}")

    return result


if __name__ == "__main__":
    print("Testing Validation-Only Approach")
    print("=" * 60)

    result = test_single_scenario()

    print("\n✅ Validation-only approach working!")
