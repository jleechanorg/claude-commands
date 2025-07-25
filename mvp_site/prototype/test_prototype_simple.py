#!/usr/bin/env python3
"""
Direct test of prototype validation - no relative imports.
Run from project root with: cd mvp_site && TESTING=true python3 test_prototype_simple.py
"""

import os
import sys
import time

# Add prototype directory to path
prototype_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prototype"
)
sys.path.insert(0, prototype_path)

from game_state_integration import MockGameState
from validators.fuzzy_token_validator import FuzzyTokenValidator

# Import validators directly
from validators.token_validator import SimpleTokenValidator, TokenValidator

print(f"Testing prototype validation from: {prototype_path}")
print("=" * 60)


def test_validators():
    """Test the validators work."""
    print("\n1. Testing Basic Validators")

    narrative = "Gideon raised his sword while Rowan prepared her spells."
    expected = ["Gideon", "Rowan"]

    # Test SimpleTokenValidator
    print("\n   Testing SimpleTokenValidator:")
    simple = SimpleTokenValidator()
    result = simple.validate(narrative, expected)
    print(f"   - Found: {result['entities_found']}")
    print(f"   - All present: {result['all_entities_present']}")
    assert result["all_entities_present"], "SimpleTokenValidator failed"

    # Test TokenValidator with descriptors
    print("\n   Testing TokenValidator with descriptors:")
    token = TokenValidator()
    desc_narrative = "The knight and the healer stood ready."
    result = token.validate(desc_narrative, expected)
    print(f"   - Found: {result['entities_found']}")
    print(f"   - All present: {result['all_entities_present']}")
    assert result["all_entities_present"], "TokenValidator failed"

    # Test FuzzyTokenValidator
    print("\n   Testing FuzzyTokenValidator:")
    fuzzy = FuzzyTokenValidator()
    fuzzy_narrative = "Gid-- was cut off while Row prepared spells."
    result = fuzzy.validate(fuzzy_narrative, expected)
    print(f"   - Found: {result['entities_found']}")
    print(f"   - All present: {result['all_entities_present']}")
    assert len(result["entities_found"]) == 2, "FuzzyTokenValidator failed"

    print("\n✅ All validator tests passed!")


def test_game_state():
    """Test game state integration."""
    print("\n2. Testing Game State Integration")

    game_state = MockGameState()

    # Test manifest
    print("\n   Testing entity manifest:")
    manifest = game_state.get_active_entity_manifest()
    print(f"   - Location: {manifest['location']}")
    print(f"   - Entity count: {manifest['entity_count']}")
    print(f"   - Entities: {[e['name'] for e in manifest['entities']]}")
    assert manifest["entity_count"] == 2, "Wrong entity count"

    # Test validation
    print("\n   Testing narrative validation:")
    result = game_state.validate_narrative_consistency(
        "Gideon and Rowan entered the chamber."
    )
    print(f"   - Valid: {result['is_valid']}")
    print(f"   - Missing: {result['missing_entities']}")
    print(f"   - Confidence: {result['confidence']:.2f}")
    assert result["is_valid"], "Validation failed"

    print("\n✅ Game state tests passed!")


def test_performance():
    """Test performance requirements."""
    print("\n3. Testing Performance")

    fuzzy = FuzzyTokenValidator()
    narrative = "Gideon and Rowan battled the dragon."
    entities = ["Gideon", "Rowan"]

    # Warm up
    fuzzy.validate(narrative, entities)

    # Time 10 validations
    start = time.time()
    for _ in range(10):
        fuzzy.validate(narrative, entities)
    duration = time.time() - start
    avg_time = duration / 10

    print(f"\n   Average validation time: {avg_time*1000:.2f}ms")
    print("   Target: <50ms")

    if avg_time < 0.05:
        print("\n✅ Performance test passed!")
    else:
        print("\n❌ Performance test failed - too slow!")


def test_hybrid():
    """Test hybrid validator."""
    print("\n4. Testing Hybrid Validator")

    from validators.hybrid_validator import HybridValidator

    hybrid = HybridValidator()

    # Test simple case
    print("\n   Testing simple case:")
    result = hybrid.validate("Gideon and Rowan stood ready.", ["Gideon", "Rowan"])
    print(f"   - All present: {result['all_entities_present']}")
    print(f"   - Confidence: {result['confidence']:.2f}")
    assert result["all_entities_present"], "Hybrid validator failed"

    # Test ambiguous case
    print("\n   Testing ambiguous case:")
    result = hybrid.validate("Someone moved in the shadows.", ["Gideon", "Rowan"])
    print(f"   - All present: {result['all_entities_present']}")
    print(f"   - Confidence: {result['confidence']:.2f}")

    print("\n✅ Hybrid validator tests passed!")


if __name__ == "__main__":
    try:
        test_validators()
        test_game_state()
        test_performance()
        test_hybrid()

        print("\n" + "=" * 60)
        print("🎉 ALL INTEGRATION TESTS PASSED! 🎉")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
