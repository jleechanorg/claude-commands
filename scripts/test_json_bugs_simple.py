#!/usr/bin/env python3
"""
Simple test script to verify JSON display bugs are fixed.
This script tests the two main bugs identified in PR #278:
1. LLM Not Respecting Character Actions (State Updates)
2. Raw JSON Returned to User
"""

import json
import os
import sys
import traceback

# Add the mvp_site directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mvp_site"))

from narrative_response_schema import parse_structured_response
from robust_json_parser import parse_llm_json_response


def test_state_updates_extraction():
    """Test Bug 1: State updates properly extracted from JSON"""
    print("Testing Bug 1: State Updates Extraction")

    # Test JSON with state updates
    test_json = {
        "narrative": "You swing your sword at the orc.",
        "state_updates": {
            "player_character_data": {"hp_current": "18"},
            "npc_data": {"orc_warrior": {"status": "wounded"}},
            "custom_campaign_state": {"combat_round": "2"},
        },
    }

    response_text = json.dumps(test_json)
    narrative_text, parsed_response = parse_structured_response(response_text)

    # Verify state updates are captured
    print(f"✓ Narrative extracted: {narrative_text}")
    print(f"✓ State updates present: {parsed_response.state_updates}")

    # Check specific values
    assert parsed_response.state_updates["player_character_data"]["hp_current"] == "18"
    assert (
        parsed_response.state_updates["npc_data"]["orc_warrior"]["status"] == "wounded"
    )

    print("✓ Bug 1 test passed: State updates properly extracted\n")


def test_raw_json_parsing():
    """Test Bug 2: Raw JSON properly parsed and cleaned"""
    print("Testing Bug 2: Raw JSON Parsing")

    # Test malformed JSON
    malformed_json = '{"narrative": "You enter the tavern.", "state_updates": {'

    result, was_incomplete = parse_llm_json_response(malformed_json)

    print(f"✓ Malformed JSON handled: {result}")
    print(f"✓ Was incomplete: {was_incomplete}")

    # Should have extracted something usable
    assert "narrative" in result
    assert "You enter the tavern." in result["narrative"]

    print("✓ Bug 2 test passed: Raw JSON properly parsed\n")


def test_narrative_extraction():
    """Test that narrative is properly extracted without JSON artifacts"""
    print("Testing Bug 2: Narrative Extraction")

    # Test with extra debug fields
    complex_json = {
        "narrative": "You cast a spell and lightning crackles.",
        "state_updates": {"player_character_data": {"spell_slots": "2"}},
        "reasoning": "This is debug info",
        "metadata": {"model": "gemini-2.5-flash"},
    }

    response_text = json.dumps(complex_json)
    narrative_text, parsed_response = parse_structured_response(response_text)

    # Verify clean narrative
    print(f"✓ Clean narrative: {narrative_text}")
    assert "lightning crackles" in narrative_text
    assert "reasoning" not in narrative_text
    assert "metadata" not in narrative_text

    print("✓ Bug 2 test passed: Narrative properly extracted\n")


def main():
    """Run all tests"""
    print("Running JSON Display Bug Tests")
    print("=" * 40)

    try:
        test_state_updates_extraction()
        test_raw_json_parsing()
        test_narrative_extraction()

        print("🎉 All tests passed! JSON display bugs appear to be fixed.")

    except Exception as e:
        print(f"❌ Test failed: {e}")

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
