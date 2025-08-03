#!/usr/bin/env python3
"""
Red/Green test for backstory cutoff bug in character creation.

This test reproduces the issue where character backstories are being cut off
mid-sentence during character creation, specifically around text like:
"His formative years were steeped in the Empress's doctrine of"

The issue appears to be in how we extract or process the narrative field
from the AI response during character creation.
"""

import os
import sys
import unittest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from json_utils import extract_field_value
from robust_json_parser import parse_llm_json_response


class TestBackstoryCutoffBug(unittest.TestCase):
    """Test the backstory cutoff bug using red/green methodology."""

    def setUp(self):
        """Set up test data with character creation response that triggers the bug."""
        # This is similar to the actual response that caused the backstory cutoff
        self.character_creation_response = """{
            "narrative": "[Mode: STORY MODE]\\n[CHARACTER CREATION - Step 2 of 7]\\n\\n\\"Understood,\\" the voice echoes, settling into the space around you like a gentle breeze carrying ancient wisdom. \\"Let me craft a character worthy of this realm's grandeur and complexity.\\"\\n\\nA moment of profound focus passes, and then the details of your destined persona begin to take shape:\\n\\n**CHARACTER SHEET**\\nName: Ser Arion val Valerion\\nRace: Human (Vaelthorne nobility)\\nClass: Paladin | Level: 1\\nBackground: Noble\\nAlignment: Lawful Good\\nMBTI: ESTJ\\n\\n**Ability Scores:**\\nSTR: 16 (+3) | DEX: 12 (+1) | CON: 14 (+2)\\nINT: 13 (+1) | WIS: 15 (+2) | CHA: 14 (+2)\\n\\n**Hit Points:** 12/12 | **Armor Class:** 16 (Chain Mail)\\n**Proficiency Bonus:** +2\\n**Saving Throw Proficiencies:** Wisdom, Charisma\\n**Skills:** Athletics (+5), History (+3), Insight (+4), Persuasion (+4)\\n\\n**Equipment:** Chain mail, shield, longsword, javelin (5), explorer's pack, signet ring of House Valerion, scroll of pedigree, fine clothes, belt pouch with 25 gp\\n\\n**Key Features & Abilities (Level 1):**\\n*   **Divine Sense:** Detect celestials, fiends, and undead within 60 feet (3 uses per long rest)\\n*   **Lay on Hands:** Heal 5 hit points per day (pool refreshes on long rest)\\n*   **Fighting Style:** (Will be chosen at Level 2)\\n*   **Noble Feature - Position of Privilege:** Due to your noble birth, people are inclined to think the best of you\\n\\n**Backstory:**\\nBorn into the esteemed House Valerion, Ser Arion's childhood was one of privilege and rigorous training. From a young age, he displayed a natural aptitude for martial prowess, earning him the title of prodigy. His formative years were steeped in the Empress's doctrine of",
            "planning_block": {
                "text": "The character sheet for Ser Arion val Valerion is complete. The next step is to confirm if the player wants to proceed with this character or make adjustments before starting the campaign.",
                "options": [
                    "Make Changes: Request adjustments to Ser Arion's character sheet.",
                    "Play as Ser Arion: Begin the adventure with Ser Arion val Valerion as designed.",
                    "Start Over: Discard this character and begin designing a new one from scratch.",
                    "Custom Action"
                ]
            },
            "state_updates": {
                "character_creation_step": 2,
                "character_name": "Ser Arion val Valerion",
                "character_class": "Paladin",
                "character_race": "Human"
            }
        }"""

        # What the backstory SHOULD contain (full version)
        self.expected_full_backstory = """Born into the esteemed House Valerion, Ser Arion's childhood was one of privilege and rigorous training. From a young age, he displayed a natural aptitude for martial prowess, earning him the title of prodigy. His formative years were steeped in the Empress's doctrine of divine justice and unwavering loyalty to the realm. Under the tutelage of master-at-arms Sir Gareth the Stalwart, Arion learned not just the art of combat, but the sacred oaths that bind a true paladin.

His coming of age was marked by the Ceremony of the Silver Blade, where he swore the Sacred Vows before the High Cleric of Aethermoor. The divine light that surrounded him during this ritual was seen by all as a sign of his destined path. Now, with sword blessed and purpose clear, Ser Arion stands ready to serve both crown and divine will, wherever duty may call him."""

        # The truncated version (what the bug produces)
        self.truncated_backstory = """Born into the esteemed House Valerion, Ser Arion's childhood was one of privilege and rigorous training. From a young age, he displayed a natural aptitude for martial prowess, earning him the title of prodigy. His formative years were steeped in the Empress's doctrine of"""

    def test_backstory_extraction_RED_phase(self):
        """
        RED PHASE: Demonstrate that the current narrative extraction
        produces a truncated backstory.
        """
        # Extract the narrative from the JSON
        extracted_narrative = extract_field_value(
            self.character_creation_response, "narrative"
        )

        assert extracted_narrative is not None, "Should extract narrative field"

        # The current narrative should contain the truncated backstory
        assert "Born into the esteemed House Valerion" in extracted_narrative
        assert (
            "His formative years were steeped in the Empress's doctrine of"
            in extracted_narrative
        )

        # But it should NOT contain the complete backstory ending
        # (This is the bug - the response is getting cut off)
        complete_ending_phrases = [
            "divine justice and unwavering loyalty",
            "master-at-arms Sir Gareth",
            "Ceremony of the Silver Blade",
            "Sacred Vows before the High Cleric",
        ]

        has_complete_ending = any(
            phrase in extracted_narrative for phrase in complete_ending_phrases
        )

        # RED PHASE: This should fail because the backstory is truncated
        if has_complete_ending:
            self.fail(
                "🔴 RED PHASE FAILED: The backstory appears to be complete already. The bug may not exist or may have been fixed."
            )

        print("\n🔴 RED PHASE: Confirmed backstory truncation")
        print(f"Narrative length: {len(extracted_narrative)} characters")
        print(f"Backstory ends with: ...{extracted_narrative[-100:]}")

    def test_backstory_length_analysis(self):
        """Analyze where exactly the backstory gets cut off."""
        extracted_narrative = extract_field_value(
            self.character_creation_response, "narrative"
        )

        # Find the backstory section
        backstory_start = extracted_narrative.find("**Backstory:**")
        assert backstory_start != -1, "Should find backstory section"

        backstory_section = extracted_narrative[backstory_start:]

        # Check if it ends abruptly (common signs of truncation)
        truncation_indicators = [
            'doctrine of"',  # Ends with quote but no closing
            'doctrine of\\"',  # Escaped quote at end
            "doctrine of,",  # Comma without continuation
            "doctrine of",  # Just cuts off completely
        ]

        has_truncation = any(
            indicator in backstory_section for indicator in truncation_indicators
        )

        print("\n📊 BACKSTORY ANALYSIS:")
        print(f"Full narrative length: {len(extracted_narrative)}")
        print(f"Backstory section length: {len(backstory_section)}")
        print(f"Backstory ends with: '{backstory_section[-50:]}'")
        print(f"Truncation detected: {has_truncation}")

        # This helps us understand the exact nature of the truncation
        assert has_truncation, "Expected to find truncation indicators"

    def test_character_creation_response_parsing(self):
        """Test that we can properly parse the character creation response."""
        # Use the robust JSON parser to handle the response
        parsed_response, was_incomplete = parse_llm_json_response(
            self.character_creation_response
        )

        assert parsed_response is not None, "Should parse the response"
        assert "narrative" in parsed_response, "Should contain narrative field"
        assert (
            "planning_block" in parsed_response
        ), "Should contain planning_block field"
        assert "state_updates" in parsed_response, "Should contain state_updates field"

        # Check that the parsing preserves the narrative content
        narrative = parsed_response["narrative"]
        assert "Ser Arion val Valerion" in narrative
        assert "**Backstory:**" in narrative

        print("\n✅ JSON PARSING: Successfully parsed response")
        print(f"Narrative field length: {len(narrative)}")

    def test_identify_root_cause(self):
        """Identify where the truncation might be happening."""
        # Test various potential causes:

        # 1. JSON extraction issue
        raw_json = self.character_creation_response
        extracted = extract_field_value(raw_json, "narrative")

        # 2. Check if the issue is in the original JSON
        import json

        try:
            parsed = json.loads(raw_json)
            json_narrative = parsed.get("narrative", "")
            print("\n🔍 ROOT CAUSE ANALYSIS:")
            print(f"Raw JSON narrative length: {len(json_narrative)}")
            print(f"Extracted narrative length: {len(extracted) if extracted else 0}")

            if json_narrative == extracted:
                print("✅ JSON extraction is working correctly")
                print("❌ Issue is in the original AI response generation")
            else:
                print("❌ JSON extraction is modifying the content")

        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
            print("Issue might be in malformed JSON from AI")

    def test_backstory_completion_GREEN_phase(self):
        """
        GREEN PHASE: Test with a complete, untruncated response.

        This simulates what the response SHOULD look like when fixed.
        """
        # Create a complete response with full backstory
        complete_response = self.character_creation_response.replace(
            "His formative years were steeped in the Empress's doctrine of",
            "His formative years were steeped in the Empress's doctrine of divine justice and unwavering loyalty to the realm. Under the tutelage of master-at-arms Sir Gareth the Stalwart, Arion learned not just the art of combat, but the sacred oaths that bind a true paladin.\\n\\nHis coming of age was marked by the Ceremony of the Silver Blade, where he swore the Sacred Vows before the High Cleric of Aethermoor. The divine light that surrounded him during this ritual was seen by all as a sign of his destined path. Now, with sword blessed and purpose clear, Ser Arion stands ready to serve both crown and divine will, wherever duty may call him.",
        )

        # Extract the narrative
        extracted_narrative = extract_field_value(complete_response, "narrative")

        assert extracted_narrative is not None

        # Should now contain the complete backstory
        complete_ending_phrases = [
            "divine justice and unwavering loyalty",
            "master-at-arms Sir Gareth",
            "Ceremony of the Silver Blade",
            "Sacred Vows before the High Cleric",
        ]

        found_phrases = [
            phrase
            for phrase in complete_ending_phrases
            if phrase in extracted_narrative
        ]

        print("\n🟢 GREEN PHASE: Complete backstory test")
        print(
            f"Found {len(found_phrases)}/{len(complete_ending_phrases)} expected phrases"
        )
        print(f"Complete narrative length: {len(extracted_narrative)}")

        # This should pass with a complete response
        assert (
            len(found_phrases) >= 3
        ), f"Should find most backstory elements, found: {found_phrases}"


if __name__ == "__main__":
    unittest.main(verbosity=2)
