#!/usr/bin/env python3
"""
Test all permutations of prompt loading based on checkbox selections.
Tests which prompt files are loaded for different combinations of narrative and mechanics.
"""

import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock dependencies
sys.modules["google"] = MagicMock()
sys.modules["google.genai"] = MagicMock()
sys.modules["firebase_admin"] = MagicMock()
sys.modules["firebase_admin.firestore"] = MagicMock()

os.environ["GEMINI_API_KEY"] = "test"

import gemini_service


class TestPromptLoadingPermutations(unittest.TestCase):
    """Test all permutations of prompt loading based on user selections."""

    def setUp(self):
        """Create temporary directory structure for test files."""
        self.temp_dir = tempfile.mkdtemp()
        self.prompts_dir = os.path.join(self.temp_dir, "prompts")
        os.makedirs(self.prompts_dir)

        # Create test prompt files
        self.test_files = {
            "master_directive.md": "Master directive content",
            "game_state_instruction.md": "Game state content",
            "dnd_srd_instruction.md": "D&D SRD content",
            "narrative_system_instruction.md": "Narrative content",
            "mechanics_system_instruction.md": "Mechanics content with character creation",
            "character_template.md": "Character template content",
        }

        for filename, content in self.test_files.items():
            with open(os.path.join(self.prompts_dir, filename), "w") as f:
                f.write(content)

        # Patch the prompt directory path
        self.patcher = patch("gemini_service.os.path.dirname")
        mock_dirname = self.patcher.start()
        mock_dirname.return_value = self.temp_dir

        # Clear the instruction cache before each test
        gemini_service._loaded_instructions_cache.clear()

    def tearDown(self):
        """Clean up temporary directory and patches."""
        self.patcher.stop()
        shutil.rmtree(self.temp_dir)

    def _get_loaded_files(self, selected_prompts):
        """
        Helper to get which files would be loaded for given selected_prompts.
        Returns a list of loaded file types in order.
        """
        builder = gemini_service.PromptBuilder()
        parts = []

        # Build core instructions (always loaded)
        core_parts = builder.build_core_system_instructions()
        parts.extend(core_parts)

        # Add character instructions (may load character_template)
        builder.add_character_instructions(parts, selected_prompts)

        # Add selected prompt instructions
        builder.add_selected_prompt_instructions(parts, selected_prompts)

        # Add system reference instructions (always includes D&D SRD)
        builder.add_system_reference_instructions(parts)

        # Extract loaded file types from the parts
        loaded_types = []
        for part in parts:
            # Core instructions
            if "Master directive content" in part:
                loaded_types.append("master_directive")
            elif "Game state content" in part:
                loaded_types.append("game_state")
            elif "D&D SRD content" in part:
                loaded_types.append("dnd_srd")
            # Selected prompts
            elif "Narrative content" in part:
                loaded_types.append("narrative")
            elif "Mechanics content" in part:
                loaded_types.append("mechanics")
            # Character template
            elif "Character template content" in part:
                loaded_types.append("character_template")
            # Debug instructions are built dynamically, not from file
            elif "DEBUG MODE" in part:
                loaded_types.append("debug_instructions")

        return loaded_types

    def test_both_checkboxes_selected(self):
        """Test Case 1: Both narrative and mechanics selected (default)."""
        selected_prompts = ["narrative", "mechanics"]
        loaded_files = self._get_loaded_files(selected_prompts)

        # Core files always loaded
        self.assertIn("master_directive", loaded_files)
        self.assertIn("game_state", loaded_files)
        self.assertIn("debug_instructions", loaded_files)
        self.assertIn("dnd_srd", loaded_files)

        # Selected prompt files
        self.assertIn("narrative", loaded_files)
        self.assertIn("mechanics", loaded_files)

        # Character template loaded when narrative is selected
        self.assertIn("character_template", loaded_files)

        # Verify order: master_directive and game_state come first
        self.assertEqual(loaded_files[0], "master_directive")
        self.assertEqual(loaded_files[1], "game_state")
        self.assertEqual(loaded_files[2], "debug_instructions")

    def test_only_narrative_selected(self):
        """Test Case 2: Only narrative checkbox selected."""
        selected_prompts = ["narrative"]
        loaded_files = self._get_loaded_files(selected_prompts)

        # Core files always loaded
        self.assertIn("master_directive", loaded_files)
        self.assertIn("game_state", loaded_files)
        self.assertIn("debug_instructions", loaded_files)
        self.assertIn("dnd_srd", loaded_files)

        # Narrative selected
        self.assertIn("narrative", loaded_files)

        # Mechanics NOT selected
        self.assertNotIn("mechanics", loaded_files)

        # Character template loaded when narrative is selected
        self.assertIn("character_template", loaded_files)

    def test_only_mechanics_selected(self):
        """Test Case 3: Only mechanics checkbox selected."""
        selected_prompts = ["mechanics"]
        loaded_files = self._get_loaded_files(selected_prompts)

        # Core files always loaded
        self.assertIn("master_directive", loaded_files)
        self.assertIn("game_state", loaded_files)
        self.assertIn("debug_instructions", loaded_files)
        self.assertIn("dnd_srd", loaded_files)

        # Mechanics selected
        self.assertIn("mechanics", loaded_files)

        # Narrative NOT selected
        self.assertNotIn("narrative", loaded_files)

        # Character template NOT loaded when only mechanics selected
        self.assertNotIn("character_template", loaded_files)

    def test_no_checkboxes_selected(self):
        """Test Case 4: No checkboxes selected."""
        selected_prompts = []
        loaded_files = self._get_loaded_files(selected_prompts)

        # Core files always loaded
        self.assertIn("master_directive", loaded_files)
        self.assertIn("game_state", loaded_files)
        self.assertIn("debug_instructions", loaded_files)
        self.assertIn("dnd_srd", loaded_files)

        # No optional files loaded
        self.assertNotIn("narrative", loaded_files)
        self.assertNotIn("mechanics", loaded_files)
        self.assertNotIn("character_template", loaded_files)

        # Should have exactly 4 files loaded (3 core + dnd_srd)
        self.assertEqual(len(loaded_files), 4)

    def test_character_creation_triggers_with_mechanics(self):
        """Test that character creation is mentioned when mechanics is loaded."""
        selected_prompts = ["mechanics"]
        builder = gemini_service.PromptBuilder()
        parts = []

        # Build all instructions
        parts.extend(builder.build_core_system_instructions())
        builder.add_character_instructions(parts, selected_prompts)
        builder.add_selected_prompt_instructions(parts, selected_prompts)
        builder.add_system_reference_instructions(parts)

        # Join all parts to check content
        full_content = "\n".join(parts)

        # Mechanics content should be loaded
        self.assertIn("Mechanics content with character creation", full_content)

        # When mechanics is enabled, character creation should be available
        # (The actual character creation trigger is in the mechanics file)

    def test_no_character_creation_without_mechanics(self):
        """Test that character creation is not triggered without mechanics."""
        selected_prompts = ["narrative"]  # Only narrative, no mechanics
        builder = gemini_service.PromptBuilder()
        parts = []

        # Build all instructions
        parts.extend(builder.build_core_system_instructions())
        builder.add_character_instructions(parts, selected_prompts)
        builder.add_selected_prompt_instructions(parts, selected_prompts)
        builder.add_system_reference_instructions(parts)

        # Join all parts to check content
        full_content = "\n".join(parts)

        # Mechanics content should NOT be loaded
        self.assertNotIn("Mechanics content with character creation", full_content)

    def test_prompt_loading_order_consistency(self):
        """Test that files are always loaded in the correct order."""
        test_cases = [
            ["narrative", "mechanics"],
            ["mechanics", "narrative"],  # Different order in input
            ["narrative"],
            ["mechanics"],
            [],
        ]

        for selected_prompts in test_cases:
            loaded_files = self._get_loaded_files(selected_prompts)

            # Core files always come first in this exact order
            core_indices = []
            if "master_directive" in loaded_files:
                core_indices.append(loaded_files.index("master_directive"))
            if "game_state" in loaded_files:
                core_indices.append(loaded_files.index("game_state"))
            if "debug_instructions" in loaded_files:
                core_indices.append(loaded_files.index("debug_instructions"))

            # Verify core files are in order and at the beginning
            self.assertEqual(core_indices, list(range(len(core_indices))))

            # If both narrative and mechanics are selected, narrative comes before mechanics
            if "narrative" in loaded_files and "mechanics" in loaded_files:
                self.assertLess(
                    loaded_files.index("narrative"),
                    loaded_files.index("mechanics"),
                    f"Narrative should come before mechanics for {selected_prompts}",
                )

    def test_character_template_only_with_narrative(self):
        """Test that character_template is only loaded when narrative is selected."""
        test_cases = [
            (["narrative", "mechanics"], True),  # Should load character_template
            (["narrative"], True),  # Should load character_template
            (["mechanics"], False),  # Should NOT load character_template
            ([], False),  # Should NOT load character_template
        ]

        for selected_prompts, should_load_template in test_cases:
            loaded_files = self._get_loaded_files(selected_prompts)

            if should_load_template:
                self.assertIn(
                    "character_template",
                    loaded_files,
                    f"Character template should be loaded for {selected_prompts}",
                )
            else:
                self.assertNotIn(
                    "character_template",
                    loaded_files,
                    f"Character template should NOT be loaded for {selected_prompts}",
                )

    def test_invalid_prompt_type_ignored(self):
        """Test that invalid prompt types are silently ignored."""
        selected_prompts = ["narrative", "invalid_type", "mechanics", "another_invalid"]
        loaded_files = self._get_loaded_files(selected_prompts)

        # Should load valid prompts and ignore invalid ones
        self.assertIn("narrative", loaded_files)
        self.assertIn("mechanics", loaded_files)

        # Invalid types should not appear
        self.assertNotIn("invalid_type", loaded_files)
        self.assertNotIn("another_invalid", loaded_files)


if __name__ == "__main__":
    unittest.main()
