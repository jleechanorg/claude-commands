import os
import unittest


class TestPromptNPCExamples(unittest.TestCase):
    """Test that the game_state_instruction.md contains proper examples for NPC handling."""

    def setUp(self):
        """Load the prompt file."""
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts",
            "game_state_instruction.md",
        )
        with open(prompt_path) as f:
            self.prompt_content = f.read()

    def test_preferred_npc_update_method_exists(self):
        """Test that the prompt contains the preferred NPC update method."""
        # Check for the preferred method marker
        assert "PREFERRED METHOD - Update specific fields" in self.prompt_content

        # Check that it shows proper dictionary updates
        assert '"Goblin_Leader": {' in self.prompt_content
        assert '"hp_current": 0,' in self.prompt_content
        assert '"status": "defeated in battle"' in self.prompt_content

    def test_string_update_warning_exists(self):
        """Test that the prompt warns about string updates but explains they're tolerated."""
        # Check for the warning marker
        assert "TOLERATED BUT NOT RECOMMENDED - String updates" in self.prompt_content

        # Check that it explains the conversion
        assert 'This becomes: `{"status": "defeated"}`' in self.prompt_content
        assert "while preserving other NPC data" in self.prompt_content

    def test_delete_guidance_exists(self):
        """Test that the prompt explains how to delete NPCs."""
        # Check for delete guidance
        assert "To remove an NPC entirely" in self.prompt_content
        assert '"Dead_Enemy": "__DELETE__"' in self.prompt_content

    def test_npc_data_dictionary_rule_exists(self):
        """Test that the mandatory rule about npc_data structure is present."""
        # Check for the specific rule about npc_data
        assert "npc_data` is ALWAYS a DICTIONARY" in self.prompt_content
        assert (
            "values are DICTIONARIES containing the NPC's data sheet"
            in self.prompt_content
        )


if __name__ == "__main__":
    unittest.main()
