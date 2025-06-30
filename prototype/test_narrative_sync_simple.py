#!/usr/bin/env python3
"""
Simple test runner for the Narrative Sync Validator
Can be run directly without pytest
"""

import sys
import os

# Add prototype to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from validators.narrative_sync_validator import (
    NarrativeSyncValidator, EntityContext, EntityPresenceType
)


def test_thornwood_split_party():
    """Test Case 1: Split party from Thornwood Conspiracy"""
    print("\n🧪 Test 1: Thornwood Split Party Scenario")
    
    narrative = """
    The wizard and cleric waited anxiously in the tavern, discussing their 
    next move. The barkeep brought them another round of ale as they pored 
    over the city maps.
    """
    
    expected_entities = ["Kira", "Aldric", "Finn"]
    validator = NarrativeSyncValidator()
    
    result = validator.validate(narrative, expected_entities)
    
    print(f"   Entities found: {result.entities_found}")
    print(f"   Entities missing: {result.entities_missing}")
    print(f"   Analysis: {result.metadata['entity_analysis']}")
    
    # Check results
    assert "Kira" in result.entities_missing, "Kira should be detected as missing"
    assert "Aldric" in result.entities_found, "Aldric (wizard) should be found"
    assert "Finn" in result.entities_found, "Finn (cleric) should be found"
    
    print("   ✅ PASS: Correctly identified missing rogue in split party")
    return True


def test_sariel_ambiguous_presence():
    """Test Case 2: Ambiguous presence from Sariel campaign"""
    print("\n🧪 Test 2: Sariel Ambiguous Presence")
    
    narrative = """
    Cassian's voice was tight and strained. "Uncle Titus is leading a 
    punitive campaign against Mordan's entire clan. We will burn them 
    from the history books."
    """
    
    expected_entities = ["Cassian", "Titus"]
    validator = NarrativeSyncValidator()
    
    result = validator.validate(narrative, expected_entities)
    
    print(f"   Entity analysis: {result.metadata['entity_analysis']}")
    print(f"   Physically present: {result.metadata['physically_present']}")
    print(f"   Mentioned absent: {result.metadata['mentioned_absent']}")
    
    # Check results
    assert "Cassian" in result.entities_found, "Cassian should be found"
    assert result.metadata["entity_analysis"]["Titus"] == "mentioned_absent", \
        "Titus should be detected as mentioned but absent"
    
    print("   ✅ PASS: Correctly distinguished present vs mentioned entities")
    return True


def test_physical_state_continuity():
    """Test Case 3: Physical state tracking"""
    print("\n🧪 Test 3: Physical State Continuity")
    
    narrative = """
    Sariel entered the chamber, her mourning robes trailing behind her. 
    The old magister noticed her arrival and gestured to a chair.
    """
    
    expected_entities = ["Sariel", "Magister"]
    
    # Previous state had bandaged ear
    previous_states = {
        "Sariel": EntityContext(
            name="Sariel",
            presence_type=EntityPresenceType.PHYSICALLY_PRESENT,
            physical_markers=["bandaged ear", "trembling hands"]
        )
    }
    
    validator = NarrativeSyncValidator()
    result = validator.validate(
        narrative, expected_entities, 
        previous_states=previous_states
    )
    
    print(f"   Warnings: {result.warnings}")
    print(f"   Physical states found: {result.metadata.get('physical_states', {})}")
    
    # Check for continuity warnings
    has_continuity_warning = any(
        "bandaged ear" in warning 
        for warning in result.warnings
    )
    
    assert has_continuity_warning, "Should warn about missing physical markers"
    
    print("   ✅ PASS: Detected missing physical state continuity")
    return True


def test_perfect_entity_tracking():
    """Test Case 4: Good entity tracking example"""
    print("\n🧪 Test 4: Perfect Entity Tracking")
    
    narrative = """
    Sariel clung to Cressida, burying her face in the soft silk of her 
    shoulder. Cressida's hand stroked her hair gently, providing the 
    first true comfort since Mother's death. "I don't blame you," 
    Cressida said firmly.
    """
    
    expected_entities = ["Sariel", "Cressida"]
    validator = NarrativeSyncValidator()
    
    result = validator.validate(narrative, expected_entities)
    
    print(f"   All entities present: {result.all_entities_present}")
    print(f"   Confidence: {result.confidence:.2f}")
    print(f"   Entity analysis: {result.metadata['entity_analysis']}")
    
    # Check results
    assert len(result.entities_found) == 2, "Should find both entities"
    assert len(result.entities_missing) == 0, "Should have no missing entities"
    assert result.all_entities_present, "All entities should be present"
    assert result.confidence > 0.9, "Confidence should be high"
    
    print("   ✅ PASS: Perfect tracking validated correctly")
    return True


def test_scene_transitions():
    """Test Case 5: Scene transition detection"""
    print("\n🧪 Test 5: Scene Transition Detection")
    
    narrative = """
    Leaving the chamber behind, Sariel moved to the archives. She 
    arrived at the dusty repository of ancient knowledge.
    """
    
    validator = NarrativeSyncValidator()
    transitions = validator._detect_scene_transitions(narrative)
    
    print(f"   Transitions detected: {transitions}")
    
    assert len(transitions) > 0, "Should detect transitions"
    assert any("moved to" in t for t in transitions), "Should detect 'moved to'"
    assert any("arrived at" in t for t in transitions), "Should detect 'arrived at'"
    
    print("   ✅ PASS: Scene transitions detected correctly")
    return True


def main():
    """Run all tests"""
    print("="*60)
    print("NARRATIVE SYNC VALIDATOR TEST SUITE")
    print("="*60)
    
    tests = [
        test_thornwood_split_party,
        test_sariel_ambiguous_presence,
        test_physical_state_continuity,
        test_perfect_entity_tracking,
        test_scene_transitions
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"   ❌ FAIL: {str(e)}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✅ ALL TESTS PASSED!")
        print("\nThe Narrative Sync Validator successfully:")
        print("- Detects missing entities in split party scenarios")
        print("- Distinguishes physically present vs mentioned entities")
        print("- Tracks physical state continuity")
        print("- Identifies scene transitions")
        print("- Validates perfect entity tracking")
    else:
        print("❌ SOME TESTS FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()