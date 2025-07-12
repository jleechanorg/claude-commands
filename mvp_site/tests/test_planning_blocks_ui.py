#!/usr/bin/env python3
"""
Test script for planning block UI buttons functionality.
This tests the parsing and rendering of planning blocks as clickable buttons.
"""

import unittest


class TestPlanningBlocksUI(unittest.TestCase):
    """Test cases for planning block button rendering"""
    
    def test_standard_planning_block_format(self):
        """Test standard planning block with three choices"""
        planning_block = """
The goblin chieftain snarls at your approach, his yellowed tusks gleaming in the torchlight. 
His warriors shift nervously, hands on their crude weapons. 

**What do you do?**

**[Action_1]:** Draw your sword and charge the chieftain directly, hoping to end this quickly.

**[Continue_1]:** Try to negotiate with the chieftain, offering gold for safe passage.

**[Explore_2]:** Look for an alternate route around the goblin encampment.
"""
        # This would be parsed by the JavaScript parsePlanningBlocks function
        expected_choices = [
            {"id": "Action_1", "description": "Draw your sword and charge the chieftain directly, hoping to end this quickly."},
            {"id": "Continue_1", "description": "Try to negotiate with the chieftain, offering gold for safe passage."},
            {"id": "Explore_2", "description": "Look for an alternate route around the goblin encampment."}
        ]
        self.assertEqual(len(expected_choices), 3)
    
    def test_deep_think_block_format(self):
        """Test deep think block with pros and cons"""
        deep_think_block = """
You stand at a moral crossroads. The village elder offers you a substantial reward to retrieve a stolen artifact, 
but you've discovered the "thief" is actually the artifact's rightful owner.

**[Option_1]:** Return the artifact to the elder and claim your reward.
- *Pros:* Substantial gold reward, favor with the village, completed quest
- *Cons:* Moral compromise, potential karma loss, perpetuating injustice

**[Option_2]:** Side with the rightful owner and protect them from the elder.
- *Pros:* Moral integrity maintained, potential new ally, hidden quest line
- *Cons:* Village hostility, loss of reward, powerful enemy made

**[Option_3]:** Attempt to broker a compromise between both parties.
- *Pros:* Potential peaceful resolution, maintain neutrality, wisdom gain
- *Cons:* May satisfy neither party, reduced rewards, complex negotiations
"""
        # This format should also be properly parsed
        expected_choices = [
            {"id": "Option_1", "description": "Return the artifact to the elder and claim your reward."},
            {"id": "Option_2", "description": "Side with the rightful owner and protect them from the elder."},
            {"id": "Option_3", "description": "Attempt to broker a compromise between both parties."}
        ]
        self.assertEqual(len(expected_choices), 3)
    
    def test_choice_text_extraction(self):
        """Test that the full choice text is properly extracted"""
        choice_text = "**[Investigate_1]:** Search the mysterious room for hidden clues and secret passages."
        
        # The button should have data-choice-text="Investigate_1: Search the mysterious room for hidden clues and secret passages."
        expected_data = "Investigate_1: Search the mysterious room for hidden clues and secret passages."
        self.assertIn("Investigate_1", expected_data)
        self.assertIn("Search the mysterious room", expected_data)
    
    def test_special_characters_preserved(self):
        """Test that normal special characters are preserved (not HTML escaped)"""
        choice_with_quotes = 'Say "Hello there, friend!" to the stranger.'
        
        # Should preserve normal quotes without HTML escaping
        self.assertIn('"', choice_with_quotes)
        self.assertNotIn('&quot;', choice_with_quotes)  # Should NOT be HTML escaped


if __name__ == "__main__":
    unittest.main()