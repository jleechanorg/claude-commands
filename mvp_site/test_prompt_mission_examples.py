import unittest
import os
import re


class TestPromptMissionExamples(unittest.TestCase):
    """Test that the game_state_instruction.md contains proper examples for mission handling."""
    
    def setUp(self):
        """Load the prompt file."""
        prompt_path = os.path.join(os.path.dirname(__file__), 'prompts', 'game_state_instruction.md')
        with open(prompt_path, 'r') as f:
            self.prompt_content = f.read()
    
    def test_preferred_list_format_example_exists(self):
        """Test that the prompt contains the preferred list format example."""
        # Check for the preferred method marker
        self.assertIn("PREFERRED METHOD", self.prompt_content)
        
        # Check that it shows the correct list format
        self.assertIn('"active_missions": [', self.prompt_content)
        
        # Check that example missions have mission_id
        self.assertIn('"mission_id": "main_quest_1"', self.prompt_content)
        self.assertIn('"mission_id": "side_quest_1"', self.prompt_content)
        
        # Check that examples have all required fields
        self.assertIn('"title": "Defeat the Dark Lord"', self.prompt_content)
        self.assertIn('"status": "accepted"', self.prompt_content)
        self.assertIn('"objective": "Travel to the Dark Tower"', self.prompt_content)
    
    def test_dictionary_format_warning_exists(self):
        """Test that the prompt warns about dictionary format."""
        # Check for the warning marker
        self.assertIn("TOLERATED BUT NOT RECOMMENDED", self.prompt_content)
        
        # Check that it shows the problematic dictionary format
        self.assertIn('"active_missions": {', self.prompt_content)
        self.assertIn('"main_quest_1": {', self.prompt_content)
    
    def test_update_guidance_exists(self):
        """Test that the prompt explains how to update missions."""
        # Check for update guidance
        self.assertIn("When updating a mission", self.prompt_content)
        self.assertIn("mission_id", self.prompt_content)
        self.assertIn("used to identify which mission to update", self.prompt_content)
    
    def test_active_missions_must_be_list_rule(self):
        """Test that the mandatory rule about active_missions being a list is present."""
        # Look for the data schema rules section
        self.assertIn("Data Schema Rules (MANDATORY)", self.prompt_content)
        
        # Check for the specific rule about active_missions
        self.assertIn("active_missions` is ALWAYS a LIST", self.prompt_content)
        self.assertIn("DO NOT** change this field to a dictionary", self.prompt_content)


if __name__ == '__main__':
    unittest.main()