import unittest
import os


class TestPromptNPCExamples(unittest.TestCase):
    """Test that the game_state_instruction.md contains proper examples for NPC handling."""
    
    def setUp(self):
        """Load the prompt file."""
        prompt_path = os.path.join(os.path.dirname(__file__), 'prompts', 'game_state_instruction.md')
        with open(prompt_path, 'r') as f:
            self.prompt_content = f.read()
    
    def test_preferred_npc_update_method_exists(self):
        """Test that the prompt contains the preferred NPC update method."""
        # Check for the preferred method marker
        self.assertIn("PREFERRED METHOD - Update specific fields", self.prompt_content)
        
        # Check that it shows proper dictionary updates
        self.assertIn('"Goblin_Leader": {', self.prompt_content)
        self.assertIn('"hp_current": 0,', self.prompt_content)
        self.assertIn('"status": "defeated in battle"', self.prompt_content)
    
    def test_string_update_warning_exists(self):
        """Test that the prompt warns about string updates but explains they're tolerated."""
        # Check for the warning marker
        self.assertIn("TOLERATED BUT NOT RECOMMENDED - String updates", self.prompt_content)
        
        # Check that it explains the conversion
        self.assertIn('This becomes: `{"status": "defeated"}`', self.prompt_content)
        self.assertIn("while preserving other NPC data", self.prompt_content)
    
    def test_delete_guidance_exists(self):
        """Test that the prompt explains how to delete NPCs."""
        # Check for delete guidance
        self.assertIn("To remove an NPC entirely", self.prompt_content)
        self.assertIn('"Dead_Enemy": "__DELETE__"', self.prompt_content)
    
    def test_npc_data_dictionary_rule_exists(self):
        """Test that the mandatory rule about npc_data structure is present."""
        # Check for the specific rule about npc_data
        self.assertIn("npc_data` is ALWAYS a DICTIONARY", self.prompt_content)
        self.assertIn("values are DICTIONARIES containing the NPC's data sheet", self.prompt_content)


if __name__ == '__main__':
    unittest.main()