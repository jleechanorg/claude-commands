"""
End-to-end test for prompt loading functionality.

Tests the relationship/reputation file separation refactor:
- Separate files load correctly via load_detailed_sections()
- extract_llm_instruction_hints() parses LLM response correctly
- PromptBuilder.add_selected_prompt_instructions() loads sections on demand
"""

# ruff: noqa: E402,PT009

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

# Ensure TESTING_AUTH_BYPASS is set before importing app modules
os.environ.setdefault("TESTING_AUTH_BYPASS", "true")

# Allow direct invocation without requiring PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from mvp_site import agent_prompts, constants


class TestPromptLoadingEnd2End(unittest.TestCase):
    """Test prompt loading through the full application stack."""

    def test_relationship_file_exists_and_loads(self):
        """Verify relationship_instruction.md exists and loads without error."""
        # This tests the PATH_MAP integration
        content = agent_prompts._load_instruction_file(
            constants.PROMPT_TYPE_RELATIONSHIP
        )

        # Verify content loaded
        self.assertIsInstance(content, str)
        self.assertGreater(
            len(content), 100, "Relationship file should have substantial content"
        )

        # Verify key content markers from the relationship instruction
        self.assertIn("Relationship", content)
        self.assertIn("trust_level", content)
        self.assertIn("npc_data", content)

    def test_reputation_file_exists_and_loads(self):
        """Verify reputation_instruction.md exists and loads without error."""
        content = agent_prompts._load_instruction_file(constants.PROMPT_TYPE_REPUTATION)

        # Verify content loaded
        self.assertIsInstance(content, str)
        self.assertGreater(
            len(content), 100, "Reputation file should have substantial content"
        )

        # Verify key content markers from the reputation instruction
        self.assertIn("Reputation", content)
        self.assertIn("public", content)
        self.assertIn("private", content)

    def test_load_detailed_sections_relationships(self):
        """Test load_detailed_sections with relationships section."""
        result = agent_prompts.load_detailed_sections(["relationships"])

        # Verify section header is present
        self.assertIn("--- RELATIONSHIPS MECHANICS ---", result)

        # Verify content is included
        self.assertIn("trust_level", result)

    def test_load_detailed_sections_reputation(self):
        """Test load_detailed_sections with reputation section."""
        result = agent_prompts.load_detailed_sections(["reputation"])

        # Verify section header is present
        self.assertIn("--- REPUTATION MECHANICS ---", result)

        # Verify content is included
        self.assertIn("notoriety_level", result)

    def test_load_detailed_sections_both(self):
        """Test load_detailed_sections with both sections."""
        result = agent_prompts.load_detailed_sections(["relationships", "reputation"])

        # Both headers should be present
        self.assertIn("--- RELATIONSHIPS MECHANICS ---", result)
        self.assertIn("--- REPUTATION MECHANICS ---", result)

        # Content from both files
        self.assertIn("trust_level", result)
        self.assertIn("notoriety_level", result)

    def test_load_detailed_sections_empty_list(self):
        """Test load_detailed_sections with empty list returns empty string."""
        result = agent_prompts.load_detailed_sections([])
        self.assertEqual(result, "")

    def test_load_detailed_sections_unknown_section(self):
        """Test load_detailed_sections gracefully ignores unknown sections."""
        # Unknown section should be ignored, not raise error
        result = agent_prompts.load_detailed_sections(["unknown_section"])
        self.assertEqual(result, "")

    def test_load_detailed_sections_mixed_valid_invalid(self):
        """Test load_detailed_sections with mix of valid and invalid sections."""
        result = agent_prompts.load_detailed_sections(
            ["relationships", "invalid", "reputation"]
        )

        # Valid sections should load
        self.assertIn("--- RELATIONSHIPS MECHANICS ---", result)
        self.assertIn("--- REPUTATION MECHANICS ---", result)

        # Invalid section should not appear
        self.assertNotIn("invalid", result.lower().split("---")[0])  # Not in content


class TestExtractLLMInstructionHints(unittest.TestCase):
    """Test extraction of instruction hints from LLM responses."""

    def test_extract_hints_valid_response(self):
        """Test extracting hints from a properly formatted LLM response."""
        llm_response = {
            "narrative": "The story continues...",
            "debug_info": {"meta": {"needs_detailed_instructions": ["relationships"]}},
        }

        hints = agent_prompts.extract_llm_instruction_hints(llm_response)
        self.assertEqual(hints, ["relationships"])

    def test_extract_hints_multiple_sections(self):
        """Test extracting multiple hint sections."""
        llm_response = {
            "narrative": "The story continues...",
            "debug_info": {
                "meta": {"needs_detailed_instructions": ["relationships", "reputation"]}
            },
        }

        hints = agent_prompts.extract_llm_instruction_hints(llm_response)
        self.assertEqual(set(hints), {"relationships", "reputation"})

    def test_extract_hints_no_debug_info(self):
        """Test response without debug_info returns empty list."""
        llm_response = {"narrative": "The story continues..."}

        hints = agent_prompts.extract_llm_instruction_hints(llm_response)
        self.assertEqual(hints, [])

    def test_extract_hints_no_meta(self):
        """Test response without meta returns empty list."""
        llm_response = {"narrative": "The story continues...", "debug_info": {}}

        hints = agent_prompts.extract_llm_instruction_hints(llm_response)
        self.assertEqual(hints, [])

    def test_extract_hints_no_needs_detailed(self):
        """Test response without needs_detailed_instructions returns empty list."""
        llm_response = {
            "narrative": "The story continues...",
            "debug_info": {"meta": {}},
        }

        hints = agent_prompts.extract_llm_instruction_hints(llm_response)
        self.assertEqual(hints, [])

    def test_extract_hints_invalid_hint_type(self):
        """Test that non-string hints are filtered out."""
        llm_response = {
            "narrative": "The story continues...",
            "debug_info": {
                "meta": {"needs_detailed_instructions": ["relationships", 123, None]}
            },
        }

        hints = agent_prompts.extract_llm_instruction_hints(llm_response)
        self.assertEqual(hints, ["relationships"])

    def test_extract_hints_invalid_section_name(self):
        """Test that invalid section names are filtered out."""
        llm_response = {
            "narrative": "The story continues...",
            "debug_info": {
                "meta": {
                    "needs_detailed_instructions": ["relationships", "invalid_section"]
                }
            },
        }

        hints = agent_prompts.extract_llm_instruction_hints(llm_response)
        self.assertEqual(hints, ["relationships"])

    def test_extract_hints_not_a_dict(self):
        """Test non-dict input returns empty list."""
        hints = agent_prompts.extract_llm_instruction_hints("not a dict")
        self.assertEqual(hints, [])

        hints = agent_prompts.extract_llm_instruction_hints(None)
        self.assertEqual(hints, [])

    def test_extract_hints_debug_info_not_dict(self):
        """Test non-dict debug_info returns empty list."""
        llm_response = {
            "narrative": "The story continues...",
            "debug_info": "not a dict",
        }

        hints = agent_prompts.extract_llm_instruction_hints(llm_response)
        self.assertEqual(hints, [])


class TestPromptBuilderIntegration(unittest.TestCase):
    """Test PromptBuilder integration with detailed sections."""

    def setUp(self):
        """Set up PromptBuilder instance."""
        self.builder = agent_prompts.PromptBuilder()

    def test_add_selected_prompt_instructions_auto_includes_sections(self):
        """Test add_selected_prompt_instructions auto-includes relationship/reputation for narrative."""
        parts = []
        self.builder.add_selected_prompt_instructions(
            parts,
            selected_prompts=[constants.PROMPT_TYPE_NARRATIVE],
            llm_requested_sections=None,
            essentials_only=True,
        )

        # Should auto-include relationship/reputation when narrative is selected
        combined = "\n".join(parts)
        self.assertIn("--- RELATIONSHIPS MECHANICS ---", combined)
        self.assertIn("--- REPUTATION MECHANICS ---", combined)

    def test_add_selected_prompt_instructions_with_sections(self):
        """Test add_selected_prompt_instructions with LLM requested sections."""
        parts = []
        self.builder.add_selected_prompt_instructions(
            parts,
            selected_prompts=[constants.PROMPT_TYPE_NARRATIVE],
            llm_requested_sections=["relationships", "reputation"],
            essentials_only=True,
        )

        # Should include relationship and reputation sections
        combined = "\n".join(parts)
        self.assertIn("--- RELATIONSHIPS MECHANICS ---", combined)
        self.assertIn("--- REPUTATION MECHANICS ---", combined)

    def test_add_selected_prompt_instructions_defaults_on_empty_sections(self):
        """Test add_selected_prompt_instructions defaults when sections list is empty."""
        parts = []
        self.builder.add_selected_prompt_instructions(
            parts,
            selected_prompts=[constants.PROMPT_TYPE_NARRATIVE],
            llm_requested_sections=[],
            essentials_only=True,
        )

        combined = "\n".join(parts)
        self.assertIn("--- RELATIONSHIPS MECHANICS ---", combined)
        self.assertIn("--- REPUTATION MECHANICS ---", combined)

    def test_add_selected_prompt_instructions_without_narrative(self):
        """Test add_selected_prompt_instructions without narrative doesn't auto-include sections."""
        parts = []
        self.builder.add_selected_prompt_instructions(
            parts,
            selected_prompts=[constants.PROMPT_TYPE_MECHANICS],  # No narrative
            llm_requested_sections=[],
            essentials_only=True,
        )

        # Without narrative, should NOT auto-include relationship/reputation
        combined = "\n".join(parts)
        self.assertNotIn("--- RELATIONSHIPS MECHANICS ---", combined)
        self.assertNotIn("--- REPUTATION MECHANICS ---", combined)

    def test_add_selected_prompt_instructions_loads_llm_requested_in_full_prompt(self):
        """In full-prompt mode, load detailed sections when LLM explicitly requests them.

        This enables dynamic prompt loading where the LLM can request specific
        sections (e.g., relationships, reputation) for the next turn via
        debug_info.meta.needs_detailed_instructions.
        """

        parts = []
        self.builder.add_selected_prompt_instructions(
            parts,
            selected_prompts=[constants.PROMPT_TYPE_NARRATIVE],
            llm_requested_sections=["relationships", "reputation"],
            essentials_only=False,
        )

        combined = "\n".join(parts)
        # Detailed sections SHOULD be loaded when LLM explicitly requests them
        self.assertIn("--- RELATIONSHIPS MECHANICS ---", combined)
        self.assertIn("--- REPUTATION MECHANICS ---", combined)


class TestSectionToPromptTypeMapping(unittest.TestCase):
    """Test the SECTION_TO_PROMPT_TYPE mapping is correct."""

    def test_relationships_maps_correctly(self):
        """Test relationships maps to PROMPT_TYPE_RELATIONSHIP."""
        self.assertEqual(
            agent_prompts.SECTION_TO_PROMPT_TYPE["relationships"],
            constants.PROMPT_TYPE_RELATIONSHIP,
        )

    def test_reputation_maps_correctly(self):
        """Test reputation maps to PROMPT_TYPE_REPUTATION."""
        self.assertEqual(
            agent_prompts.SECTION_TO_PROMPT_TYPE["reputation"],
            constants.PROMPT_TYPE_REPUTATION,
        )

    def test_all_mappings_have_valid_paths(self):
        """Test all section mappings have corresponding PATH_MAP entries."""
        for section, prompt_type in agent_prompts.SECTION_TO_PROMPT_TYPE.items():
            self.assertIn(
                prompt_type,
                agent_prompts.PATH_MAP,
                f"Section '{section}' maps to '{prompt_type}' which is missing from PATH_MAP",
            )


class TestTokenSavings(unittest.TestCase):
    """Test that token savings are achieved when sections not loaded."""

    def test_no_sections_vs_all_sections_size_difference(self):
        """Verify significant size difference when sections are loaded vs not."""
        # No sections loaded
        no_sections = agent_prompts.load_detailed_sections([])

        # All sections loaded
        all_sections = agent_prompts.load_detailed_sections(
            ["relationships", "reputation"]
        )

        # No sections should be empty
        self.assertEqual(len(no_sections), 0)

        # All sections should have substantial content (>10KB based on file analysis)
        self.assertGreater(
            len(all_sections),
            10000,
            "Combined sections should be >10KB (saves ~3400 tokens when not loaded)",
        )


class TestPendingInstructionHintsWiring(unittest.TestCase):
    """Test the full wiring: GameState.pending_instruction_hints → Agent → PromptBuilder.

    This validates that when the LLM requests detailed instructions via
    debug_info.meta.needs_detailed_instructions (stored as pending_instruction_hints
    in GameState), those instructions are actually loaded on the next turn.
    """

    def test_needs_relationship_hint_loads_relationship_instructions(self):
        """Validate that pending_instruction_hints=['relationships'] loads relationship_instruction.md.

        This is the key end-to-end test for dynamic prompt loading:
        1. GameState has pending_instruction_hints: ["relationships"]
        2. StoryModeAgent receives these via llm_requested_sections parameter
        3. PromptBuilder loads relationship_instruction.md content
        4. The RELATIONSHIPS MECHANICS marker appears in final instructions
        """
        # Import here to avoid circular imports at module level
        from mvp_site.agents import StoryModeAgent
        from mvp_site.game_state import GameState

        # Create GameState with pending_instruction_hints (simulates previous turn's LLM request)
        game_state = GameState(
            player_character_data={"name": "TestHero"},
            pending_instruction_hints=["relationships"],  # LLM requested this
        )

        # Create StoryModeAgent with this game state
        agent = StoryModeAgent(game_state)

        # Build system instructions, passing the hints (as continue_story does)
        system_instructions = agent.build_system_instructions(
            selected_prompts=[constants.PROMPT_TYPE_NARRATIVE],
            llm_requested_sections=game_state.pending_instruction_hints,
        )

        # Validate that relationship instructions were loaded
        self.assertIn(
            "--- RELATIONSHIPS MECHANICS ---",
            system_instructions,
            "Relationship instructions should be loaded when pending_instruction_hints=['relationships']",
        )

    def test_needs_reputation_hint_loads_reputation_instructions(self):
        """Validate that pending_instruction_hints=['reputation'] loads reputation_instruction.md."""
        from mvp_site.agents import StoryModeAgent
        from mvp_site.game_state import GameState

        game_state = GameState(
            player_character_data={"name": "TestHero"},
            pending_instruction_hints=["reputation"],
        )

        agent = StoryModeAgent(game_state)
        system_instructions = agent.build_system_instructions(
            selected_prompts=[constants.PROMPT_TYPE_NARRATIVE],
            llm_requested_sections=game_state.pending_instruction_hints,
        )

        self.assertIn(
            "--- REPUTATION MECHANICS ---",
            system_instructions,
            "Reputation instructions should be loaded when pending_instruction_hints=['reputation']",
        )

    def test_needs_both_hints_loads_both_instructions(self):
        """Validate that pending_instruction_hints=['relationships', 'reputation'] loads both."""
        from mvp_site.agents import StoryModeAgent
        from mvp_site.game_state import GameState

        game_state = GameState(
            player_character_data={"name": "TestHero"},
            pending_instruction_hints=["relationships", "reputation"],
        )

        agent = StoryModeAgent(game_state)
        system_instructions = agent.build_system_instructions(
            selected_prompts=[constants.PROMPT_TYPE_NARRATIVE],
            llm_requested_sections=game_state.pending_instruction_hints,
        )

        self.assertIn("--- RELATIONSHIPS MECHANICS ---", system_instructions)
        self.assertIn("--- REPUTATION MECHANICS ---", system_instructions)

    def test_empty_hints_does_not_load_detailed_sections(self):
        """Validate that empty pending_instruction_hints does NOT load detailed sections."""
        from mvp_site.agents import StoryModeAgent
        from mvp_site.game_state import GameState

        game_state = GameState(
            player_character_data={"name": "TestHero"},
            pending_instruction_hints=[],  # Empty - no hints requested
        )

        agent = StoryModeAgent(game_state)
        system_instructions = agent.build_system_instructions(
            selected_prompts=[constants.PROMPT_TYPE_NARRATIVE],
            llm_requested_sections=game_state.pending_instruction_hints,
        )

        # Should NOT contain detailed section markers
        self.assertNotIn(
            "--- RELATIONSHIPS MECHANICS ---",
            system_instructions,
            "Relationship instructions should NOT be loaded when no hints requested",
        )
        self.assertNotIn(
            "--- REPUTATION MECHANICS ---",
            system_instructions,
            "Reputation instructions should NOT be loaded when no hints requested",
        )


if __name__ == "__main__":
    unittest.main()
