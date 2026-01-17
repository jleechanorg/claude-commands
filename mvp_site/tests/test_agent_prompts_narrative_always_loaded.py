"""
Unit tests for agent_prompts.add_selected_prompt_instructions().

Tests the fix for PR #3000: Narrative instructions are always loaded for StoryModeAgent
even when "narrative" is not explicitly in selected_prompts.
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from mvp_site import agent_prompts, constants
from mvp_site.agent_prompts import PromptBuilder, _load_instruction_file


class TestNarrativeAlwaysLoaded(unittest.TestCase):
    """Test that narrative instructions are always loaded for StoryModeAgent."""

    def setUp(self):
        """Set up test fixtures."""
        self.builder = PromptBuilder(None)
        # Mock _load_instruction_file to return predictable content
        self.mock_load_patcher = patch("mvp_site.agent_prompts._load_instruction_file")
        self.mock_load = self.mock_load_patcher.start()
        self.mock_load.side_effect = lambda p_type: f"CONTENT:{p_type}"

    def tearDown(self):
        """Clean up after tests."""
        self.mock_load_patcher.stop()

    def test_narrative_loaded_when_not_in_selected_prompts(self):
        """Test that narrative is loaded even when not in selected_prompts."""
        parts = []
        selected_prompts = [constants.PROMPT_TYPE_MECHANICS]  # Only mechanics, no narrative

        self.builder.add_selected_prompt_instructions(parts, selected_prompts)

        # Verify narrative was loaded
        self.assertIn(f"CONTENT:{constants.PROMPT_TYPE_NARRATIVE}", parts)
        # Verify mechanics was also loaded
        self.assertIn(f"CONTENT:{constants.PROMPT_TYPE_MECHANICS}", parts)
        # Verify narrative appears before mechanics (order matters)
        narrative_idx = parts.index(f"CONTENT:{constants.PROMPT_TYPE_NARRATIVE}")
        mechanics_idx = parts.index(f"CONTENT:{constants.PROMPT_TYPE_MECHANICS}")
        self.assertLess(narrative_idx, mechanics_idx, "Narrative should come before mechanics")

    def test_narrative_loaded_when_explicitly_in_selected_prompts(self):
        """Test that narrative is loaded when explicitly in selected_prompts."""
        parts = []
        selected_prompts = [
            constants.PROMPT_TYPE_NARRATIVE,
            constants.PROMPT_TYPE_MECHANICS,
        ]

        self.builder.add_selected_prompt_instructions(parts, selected_prompts)

        # Verify narrative was loaded
        self.assertIn(f"CONTENT:{constants.PROMPT_TYPE_NARRATIVE}", parts)
        # Verify mechanics was also loaded
        self.assertIn(f"CONTENT:{constants.PROMPT_TYPE_MECHANICS}", parts)

    def test_narrative_loaded_when_selected_prompts_empty(self):
        """Test that narrative is loaded even when selected_prompts is empty."""
        parts = []
        selected_prompts = []

        self.builder.add_selected_prompt_instructions(parts, selected_prompts)

        # Verify narrative was loaded
        self.assertIn(f"CONTENT:{constants.PROMPT_TYPE_NARRATIVE}", parts)
        # Verify mechanics was NOT loaded (not in selected_prompts)
        self.assertNotIn(f"CONTENT:{constants.PROMPT_TYPE_MECHANICS}", parts)

    def test_narrative_loaded_when_selected_prompts_none(self):
        """Test that narrative is loaded even when selected_prompts is None."""
        parts = []
        selected_prompts = None

        self.builder.add_selected_prompt_instructions(parts, selected_prompts)

        # Verify narrative was loaded
        self.assertIn(f"CONTENT:{constants.PROMPT_TYPE_NARRATIVE}", parts)

    def test_original_selected_prompts_not_mutated(self):
        """Test that the original selected_prompts list is not mutated."""
        original_prompts = [constants.PROMPT_TYPE_MECHANICS]
        selected_prompts = list(original_prompts)  # Create a copy
        parts = []

        self.builder.add_selected_prompt_instructions(parts, selected_prompts)

        # Verify original list was not mutated (narrative should not be added to it)
        self.assertEqual(selected_prompts, original_prompts)
        self.assertEqual(len(selected_prompts), 1)
        self.assertEqual(selected_prompts[0], constants.PROMPT_TYPE_MECHANICS)
        # But narrative should still be in parts
        self.assertIn(f"CONTENT:{constants.PROMPT_TYPE_NARRATIVE}", parts)

    def test_mechanics_not_loaded_when_not_in_selected_prompts(self):
        """Test that mechanics is NOT loaded when not in selected_prompts."""
        parts = []
        selected_prompts = []  # Empty, so only narrative should be loaded

        self.builder.add_selected_prompt_instructions(parts, selected_prompts)

        # Verify narrative was loaded
        self.assertIn(f"CONTENT:{constants.PROMPT_TYPE_NARRATIVE}", parts)
        # Verify mechanics was NOT loaded
        self.assertNotIn(f"CONTENT:{constants.PROMPT_TYPE_MECHANICS}", parts)

    def test_essentials_only_mode(self):
        """Test that essentials_only mode works correctly."""
        parts = []
        selected_prompts = [constants.PROMPT_TYPE_MECHANICS]

        # Mock _extract_essentials to return modified content
        with patch("mvp_site.agent_prompts._extract_essentials") as mock_extract:
            mock_extract.side_effect = lambda content: f"ESSENTIALS:{content}"

            self.builder.add_selected_prompt_instructions(
                parts, selected_prompts, essentials_only=True
            )

            # Verify narrative was loaded with essentials extraction
            self.assertIn(f"ESSENTIALS:CONTENT:{constants.PROMPT_TYPE_NARRATIVE}", parts)
            # Verify mechanics was also loaded with essentials extraction
            self.assertIn(f"ESSENTIALS:CONTENT:{constants.PROMPT_TYPE_MECHANICS}", parts)

    def test_llm_requested_sections_with_essentials_only(self):
        """Test that llm_requested_sections works correctly in essentials_only mode."""
        parts = []
        selected_prompts = [constants.PROMPT_TYPE_MECHANICS]
        llm_requested_sections = ["relationships", "reputation"]

        # Mock load_detailed_sections to return content
        with patch("mvp_site.agent_prompts.load_detailed_sections") as mock_load_detailed:
            mock_load_detailed.return_value = "DETAILED_CONTENT"

            self.builder.add_selected_prompt_instructions(
                parts,
                selected_prompts,
                llm_requested_sections=llm_requested_sections,
                essentials_only=True,
            )

            # Verify detailed sections were loaded
            self.assertIn("DETAILED_CONTENT", parts)
            # Verify load_detailed_sections was called with llm_requested_sections
            mock_load_detailed.assert_called_once_with(llm_requested_sections)

    def test_llm_requested_sections_without_essentials_only(self):
        """Test that llm_requested_sections works correctly without essentials_only."""
        parts = []
        selected_prompts = [constants.PROMPT_TYPE_MECHANICS]
        llm_requested_sections = ["relationships", "reputation"]

        # Mock load_detailed_sections to return content
        with patch("mvp_site.agent_prompts.load_detailed_sections") as mock_load_detailed:
            mock_load_detailed.return_value = "DETAILED_CONTENT"

            self.builder.add_selected_prompt_instructions(
                parts,
                selected_prompts,
                llm_requested_sections=llm_requested_sections,
                essentials_only=False,
            )

            # Verify detailed sections were loaded
            self.assertIn("DETAILED_CONTENT", parts)
            # Verify load_detailed_sections was called with llm_requested_sections
            mock_load_detailed.assert_called_once_with(llm_requested_sections)

    def test_essentials_only_without_llm_requested_sections(self):
        """Test essentials_only mode when narrative is in effective_prompts."""
        parts = []
        selected_prompts = []  # Empty, but narrative will be added

        # Mock load_detailed_sections and SECTION_TO_PROMPT_TYPE
        with patch("mvp_site.agent_prompts.load_detailed_sections") as mock_load_detailed:
            with patch("mvp_site.agent_prompts.SECTION_TO_PROMPT_TYPE") as mock_sections:
                mock_sections.keys.return_value = ["relationships", "reputation"]
                mock_load_detailed.return_value = "ALL_DETAILED_CONTENT"

                self.builder.add_selected_prompt_instructions(
                    parts, selected_prompts, essentials_only=True
                )

                # Verify detailed sections were loaded (all sections since narrative is in effective_prompts)
                self.assertIn("ALL_DETAILED_CONTENT", parts)
                # Verify load_detailed_sections was called with all section keys
                mock_load_detailed.assert_called_once_with(["relationships", "reputation"])

    def test_smoke_test_scenario(self):
        """Test the exact scenario from the smoke test failure."""
        # Smoke test passes: selected_prompts: ['mechanicalPrecision']
        # Which maps to: [constants.PROMPT_TYPE_MECHANICS]
        parts = []
        selected_prompts = [constants.PROMPT_TYPE_MECHANICS]

        self.builder.add_selected_prompt_instructions(parts, selected_prompts)

        # CRITICAL: Narrative MUST be loaded even though not in selected_prompts
        # This is what fixes the smoke test failure
        self.assertIn(f"CONTENT:{constants.PROMPT_TYPE_NARRATIVE}", parts)
        # Mechanics should also be loaded
        self.assertIn(f"CONTENT:{constants.PROMPT_TYPE_MECHANICS}", parts)

        # Verify _load_instruction_file was called for both
        self.assertGreaterEqual(self.mock_load.call_count, 2)
        call_args = [call[0][0] for call in self.mock_load.call_args_list]
        self.assertIn(constants.PROMPT_TYPE_NARRATIVE, call_args)
        self.assertIn(constants.PROMPT_TYPE_MECHANICS, call_args)


if __name__ == "__main__":
    unittest.main()
