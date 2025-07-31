import os
import unittest


class TestPromptMissionExamples(unittest.TestCase):
    """Test that the game_state_instruction.md contains proper examples for mission handling."""

    def setUp(self):
        """Load the prompt file."""
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts",
            "game_state_instruction.md",
        )
        with open(prompt_path) as f:
            self.prompt_content = f.read()

    def test_preferred_list_format_example_exists(self):
        """Test that the prompt contains the preferred list format example."""
        # Check for the preferred method marker
        assert "PREFERRED METHOD" in self.prompt_content

        # Check that it shows the correct list format
        assert '"active_missions": [' in self.prompt_content

        # Check that example missions have mission_id
        assert '"mission_id": "main_quest_1"' in self.prompt_content
        assert '"mission_id": "side_quest_1"' in self.prompt_content

        # Check that examples have all required fields
        assert '"title": "Defeat the Dark Lord"' in self.prompt_content
        assert '"status": "accepted"' in self.prompt_content
        assert '"objective": "Travel to the Dark Tower"' in self.prompt_content

    def test_dictionary_format_warning_exists(self):
        """Test that the prompt warns about dictionary format."""
        # Check for the warning marker
        assert "TOLERATED BUT NOT RECOMMENDED" in self.prompt_content

        # Check that it shows the problematic dictionary format
        assert '"active_missions": {' in self.prompt_content
        assert '"main_quest_1": {' in self.prompt_content

    def test_update_guidance_exists(self):
        """Test that the prompt explains how to update missions."""
        # Check for update guidance
        assert "When updating a mission" in self.prompt_content
        assert "mission_id" in self.prompt_content
        assert "used to identify which mission to update" in self.prompt_content

    def test_active_missions_must_be_list_rule(self):
        """Test that the mandatory rule about active_missions being a list is present."""
        # Look for the data schema rules section
        assert "Data Schema Rules (MANDATORY)" in self.prompt_content

        # Check for the specific rule about active_missions
        assert "active_missions` is ALWAYS a LIST" in self.prompt_content
        assert "DO NOT** change this field to a dictionary" in self.prompt_content


if __name__ == "__main__":
    unittest.main()
