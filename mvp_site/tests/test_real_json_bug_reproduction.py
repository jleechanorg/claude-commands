"""Test to reproduce the exact JSON bug from user's campaign."""

import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from narrative_response_schema import parse_structured_response


class TestRealJsonBugReproduction(unittest.TestCase):
    """Test to reproduce the exact JSON bug the user is experiencing."""
    
    def test_user_exact_scene_2_json(self):
        """Test the exact JSON structure from user's Scene #2."""
        # This is the exact JSON structure the user is seeing in their campaign
        user_scene_2_json = '''{
    "narrative": "[Mode: STORY MODE]\\n[CHARACTER CREATION - Step 2 of 7]\\n\\n\\"Understood,\\" the voice echoes, a comforting presence as you consider your newfound destiny. \\"Allow me to craft an identity that truly reflects the unique challenges and incredible potential of Nolan's son, a being poised between two worlds.\\"\\n\\nA moment passes, a flicker of energy coalescing, and then a detailed image of your persona forms in your mind's eye. This is the beginning of your legend, a hero (or something more) forging their path in a world suddenly much, much larger than it seemed.\\n\\nHere is the character I've designed for you, embodying the nascent powers and internal conflicts of a Viltrumite coming into his own:\\n\\n**CHARACTER SHEET**\\nName: Mark Grayson\\nRace: Viltrumite (Custom)\\nClass: Viltrumite Paragon (Custom) | Level: 1\\nBackground: Student\\nAlignment: Chaotic Good (struggling with his father's methods)\\nMBTI: ISFP\\n\\n**Ability Scores:**\\nSTR: 15 (+2) | DEX: 14 (+2) | CON: 13 (+1)\\nINT: 12 (+1) | WIS: 10 (+0) | CHA: 8 (-1)\\n\\n**Hit Points:** 11/11 | **Armor Class:** 12 (Unarmored)\\n**Proficiency Bonus:** +2\\n**Saving Throw Proficiencies:** Strength, Constitution\\n**Skills:** Athletics (+4), Acrobatics (+4), Insight (+2), Intimidation (+1)\\n\\n**Equipment:** Simple civilian clothes, a basic communicator device (for early contact, range 1 mile)\\n**Gold:** 0 gp (Still relies on his parents for pocket money)\\n\\n**Key Features & Abilities (Level 1):**\\n*   **Viltrumite Physiology:** Your body is incredibly dense and resilient.\\n    *   **Super Strength (Nascant):** You have advantage on Strength (Athletics) checks for lifting, pushing, or breaking objects. Your carrying capacity and the weight you can push, drag, or lift are doubled.\\n    *   **Enhanced Durability:** While you are wearing no armor and not wielding a shield, your AC equals 10 + your Dexterity modifier + your Constitution modifier.\\n    *   **Accelerated Healing (Minor):** At the start of your turn, if you have at least 1 hit point, you regain 1 hit point.\\n    *   **Latent Flight:** You can jump twice as high and twice as far as normal. As a bonus action, you can gain a flying speed of 30 feet until the end of your turn. You can use this feature a number of times equal to your Proficiency Bonus per long rest.\\n*   **Unarmed Strikes:** Your unarmed strikes deal 1d4 + Strength modifier bludgeoning damage.\\n\\n**Backstory:**\\nMark Grayson, a seemingly ordinary high school student, recently had his world turned upside down with the shocking revelation of his true heritage: he is a Viltrumite, son of the legendary hero Omni-Man (Nolan). As his incredible powers manifest, his father has begun to aggressively train him, pushing him towards a destiny Mark is still struggling to accept. He values his human mother and friends deeply, finding himself agonizingly torn between the immense, terrifying responsibility of his Viltrumite lineage and the normal, grounded life he desperately clings to.\\n\\n**Why This Character:**\\nI chose to embody Mark Grayson as a 'Viltrumite Paragon' because it directly translates the essence of Nolan's son from the *Invincible* series into a D&D 5e framework. His base stats reflect his burgeoning physical prowess, agility, and initial durability. The custom 'Viltrumite Physiology' feature provides mechanical representations of his strength, regeneration, and nascent flight, allowing for clear progression as he levels up. His lower Charisma score highlights his initial awkwardness, emotional turmoil, and the difficulty he faces in navigating the complex morality of his father's legacy. This build allows for a compelling narrative arc, showing his journey from a confused teenager to a truly powerful and conflicted hero.\\n\\nWhat do you think of this character? Would you like to play as Mark Grayson, or would you like me to make some changes to his abilities, background, or personality?\\n\\n--- PLANNING BLOCK ---\\nWhat is your choice?\\n1. **Approve:** I'm ready to play as Mark Grayson, exactly as presented.\\n2. **Modify Abilities:** I'd like to adjust his ability scores or powers.\\n3. **Modify Background/Personality:** I'd like to adjust his backstory, alignment, or personality traits.\\n4. **Reroll:** Generate a completely different character concept for me.",
    "god_mode_response": "",
    "entities_mentioned": [
        "Mark Grayson",
        "Nolan"
    ],
    "location_confirmed": "Character Creation",
    "state_updates": {
        "custom_campaign_state": {
            "character_creation": {
                "in_progress": true,
                "current_step": 2,
                "method_chosen": "AI_generation"
            }
        },
        "player_character_data": {
            "string_id": "pc_mark_grayson_001",
            "name": "Mark Grayson",
            "level": 1,
            "class": "Viltrumite Paragon",
            "background": "Student",
            "alignment": "Chaotic Good",
            "mbti": "ISFP",
            "hp_current": 11,
            "hp_max": 11,
            "temp_hp": 0,
            "armor_class": 12
        }
    },
    "debug_info": {
        "dm_notes": [
            "User chose option 2 for character creation"
        ],
        "dice_rolls": [],
        "resources": "HD: 1/1, Latent Flight: 0/2",
        "state_rationale": "Updated character creation progress to step 2"
    }
}'''
        
        print(f"\\nTesting exact user JSON structure...")
        print(f"Input length: {len(user_scene_2_json)}")
        print(f"Input preview: {user_scene_2_json[:200]}...")
        
        # Parse the response 
        narrative_text, structured_response = parse_structured_response(user_scene_2_json)
        
        print(f"\\nResult length: {len(narrative_text)}")
        print(f"Result preview: {narrative_text[:200]}...")
        
        # The critical test: should NOT return raw JSON
        self.assertNotIn('"narrative":', narrative_text, 
                        "Parsed result should not contain raw JSON keys")
        self.assertNotIn('"god_mode_response":', narrative_text, 
                        "Parsed result should not contain raw JSON keys")
        self.assertNotIn('"entities_mentioned":', narrative_text, 
                        "Parsed result should not contain raw JSON keys")
        
        # Should contain the actual narrative content
        self.assertIn("CHARACTER CREATION - Step 2 of 7", narrative_text,
                     "Should contain the actual narrative content")
        self.assertIn("Mark Grayson", narrative_text,
                     "Should contain character information")
        
        # Structured response should be valid
        self.assertIsNotNone(structured_response)
        self.assertIn("Mark Grayson", structured_response.entities_mentioned)
        self.assertEqual(structured_response.location_confirmed, "Character Creation")
        
    def test_user_simplified_version(self):
        """Test a simplified version to isolate the issue."""
        simple_json = '''{
    "narrative": "This is the story content that should be displayed.",
    "god_mode_response": "",
    "entities_mentioned": ["test"],
    "location_confirmed": "Test Location",
    "state_updates": {},
    "debug_info": {}
}'''
        
        narrative_text, structured_response = parse_structured_response(simple_json)
        
        # Should return clean narrative
        self.assertEqual(narrative_text, "This is the story content that should be displayed.")
        self.assertNotIn('"narrative":', narrative_text)


if __name__ == '__main__':
    unittest.main()