#!/usr/bin/env python3
"""
Simple integration test to verify the validation system works end-to-end.
Run from the prototype directory.
"""


def test_basic_integration():
    """Test basic integration of validators."""
    print("=== Basic Integration Test ===")

    # Import components
    from validators.fuzzy_token_validator import FuzzyTokenValidator
    from validators.token_validator import SimpleTokenValidator, TokenValidator

    # Test data
    narrative = "Gideon raised his sword while the healer prepared her spells."
    expected_entities = ["Gideon", "Rowan"]

    # Test each validator
    validators = {
        "SimpleToken": SimpleTokenValidator(),
        "Token": TokenValidator(),
        "Fuzzy": FuzzyTokenValidator(),
    }

    results = {}
    for name, validator in validators.items():
        try:
            result = validator.validate(narrative, expected_entities)
            results[name] = {
                "success": True,
                "found": result["entities_found"],
                "missing": result["entities_missing"],
                "confidence": result["confidence"],
            }
            print(f"\n{name}:")
            print(f"  Found: {result['entities_found']}")
            print(f"  Missing: {result['entities_missing']}")
            print(f"  Confidence: {result['confidence']:.2f}")
        except Exception as e:
            results[name] = {"success": False, "error": str(e)}
            print(f"\n{name}: ERROR - {e}")

    # Summary
    print("\n=== Summary ===")
    success_count = sum(1 for r in results.values() if r.get("success"))
    print(f"Successful validators: {success_count}/{len(validators)}")

    # Check specific results
    if results["Fuzzy"]["success"]:
        fuzzy_result = results["Fuzzy"]
        if set(fuzzy_result["found"]) == set(expected_entities):
            print("✓ Fuzzy validator correctly found all entities")
        else:
            print("✗ Fuzzy validator missed some entities")

    return success_count == len(validators)


def test_game_state_integration():
    """Test integration with game state."""
    print("\n=== Game State Integration Test ===")

    from game_state_integration import MockGameState

    # Create game state
    game_state = MockGameState()

    # Test manifest generation
    manifest = game_state.get_active_entity_manifest()
    print(f"Location: {manifest['location']}")
    print(f"Entity count: {manifest['entity_count']}")
    print(f"Entities: {[e['name'] for e in manifest['entities']]}")

    # Test validation
    test_cases = [
        ("Both present", "Gideon and Rowan entered the chamber."),
        ("One missing", "The knight stood guard alone."),
        ("Descriptors", "The knight and the healer prepared for battle."),
    ]

    for description, narrative in test_cases:
        result = game_state.validate_narrative_consistency(narrative)
        print(f"\n{description}:")
        print(f"  Valid: {result['is_valid']}")
        print(f"  Confidence: {result['confidence']:.2f}")
        if result["missing_entities"]:
            print(f"  Missing: {result['missing_entities']}")

    return True


def test_performance():
    """Test performance meets requirements."""
    print("\n=== Performance Test ===")

    import time

    from validators.fuzzy_token_validator import FuzzyTokenValidator

    validator = FuzzyTokenValidator()
    narrative = "Gideon and Rowan battled the dragon."
    entities = ["Gideon", "Rowan"]

    # Warm up
    validator.validate(narrative, entities)

    # Time 100 validations
    start = time.time()
    for _ in range(100):
        validator.validate(narrative, entities)
    duration = time.time() - start

    avg_time = duration / 100
    print(f"Average validation time: {avg_time * 1000:.2f}ms")
    print("Target: <50ms")

    if avg_time < 0.05:  # 50ms
        print("✓ Performance requirement met")
        return True
    print("✗ Performance too slow")
    return False


def run_all_tests():
    """Run all integration tests."""
    print("Running Integration Tests\n")

    tests = [
        ("Basic Integration", test_basic_integration),
        ("Game State Integration", test_game_state_integration),
        ("Performance", test_performance),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success, None))
        except Exception as e:
            print(f"\n{test_name} failed with error: {e}")
            results.append((test_name, False, str(e)))

    # Final summary
    print("\n" + "=" * 50)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 50)

    for test_name, success, error in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{test_name}: {status}")
        if error:
            print(f"  Error: {error}")

    passed = sum(1 for _, success, _ in results if success)
    print(f"\nTotal: {passed}/{len(tests)} tests passed")

    return passed == len(tests)


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
