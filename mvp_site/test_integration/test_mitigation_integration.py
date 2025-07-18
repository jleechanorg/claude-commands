"""
Integration tests for all 4 mitigation strategies working together.
Tests end-to-end scenarios and integration between different mitigation approaches.
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dual_pass_generator import DualPassGenerator
from entity_instructions import EntityInstructionGenerator
from entity_preloader import EntityPreloader
from entity_validator import EntityRetryManager, EntityValidator


class TestMitigationIntegration(unittest.TestCase):
    """Integration tests for all 4 mitigation strategies"""

    def setUp(self):
        self.preloader = EntityPreloader()
        self.validator = EntityValidator()
        self.retry_manager = EntityRetryManager(max_retries=1)  # Reduced for testing
        self.dual_pass = DualPassGenerator()
        self.instruction_gen = EntityInstructionGenerator()

        # Sample data for testing
        self.sample_game_state = {
            "session_data": {
                "player_characters": [
                    {"name": "Sariel", "hp_current": 25, "hp_max": 30}
                ],
                "npcs": [
                    {"name": "Cassian", "location": "Throne Room"},
                    {"name": "Lady Cressida", "location": "Lady Cressida's Chambers"},
                ],
            }
        }

        self.expected_entities = ["Sariel", "Cassian"]
        self.location = "Throne Room"

    def test_preloader_with_instruction_generator(self):
        """Test Option 3 (Preloader) + Option 5 (Instructions) integration"""
        with patch("entity_preloader.create_from_game_state") as mock_create:
            # Mock manifest with proper string attributes
            mock_pc = Mock()
            mock_pc.display_name = "Sariel"
            mock_pc.name = "Sariel"
            mock_pc.hp_current = 25
            mock_pc.hp_max = 30

            mock_npc = Mock()
            mock_npc.display_name = "Cassian"
            mock_npc.name = "Cassian"
            mock_npc.location = "Throne Room"

            mock_manifest = Mock(player_characters=[mock_pc], npcs=[mock_npc])
            mock_create.return_value = mock_manifest

            # Generate preload text
            preload_text = self.preloader.create_entity_preload_text(
                self.sample_game_state, 1, 1, self.location
            )

            # Generate instructions
            instructions = self.instruction_gen.generate_entity_instructions(
                self.expected_entities, ["Cassian"], self.location
            )

            # Verify both contain entity information
            self.assertIn("Sariel", preload_text)
            self.assertIn("Cassian", preload_text)
            self.assertIn("Sariel", instructions)
            self.assertIn("Cassian", instructions)

            # Verify complementary information
            self.assertIn("ENTITY MANIFEST", preload_text)
            self.assertIn("MANDATORY ENTITY REQUIREMENTS", instructions)

    def test_validator_with_retry_manager(self):
        """Test Option 2 (Validator) + Retry Manager integration"""
        # Test narrative missing entities
        narrative_missing = "Sariel looks around the empty room."

        # Mock retry callback
        retry_callback = Mock(return_value="Sariel and Cassian discuss the situation.")

        # Test validation with retry
        result, attempts = self.retry_manager.validate_with_retry(
            narrative_missing, self.expected_entities, self.location, retry_callback
        )

        # Should have attempted retry
        self.assertEqual(attempts, 1)
        retry_callback.assert_called_once()

        # Final result should be better
        self.assertGreater(len(result.found_entities), 0)

    def test_dual_pass_with_validator(self):
        """Test Option 7 (Dual Pass) + Option 2 (Validator) integration"""
        # Mock generation callback that improves on second pass
        generation_callback = Mock(
            side_effect=[
                "Sariel enters the room.",  # First pass - missing Cassian
                "Cassian steps forward to greet Sariel.",  # Second pass - adds Cassian
            ]
        )

        result = self.dual_pass.generate_with_dual_pass(
            "Continue the story",
            self.expected_entities,
            self.location,
            generation_callback,
        )

        # Should have used both passes
        self.assertIsNotNone(result.first_pass)
        self.assertIsNotNone(result.second_pass)

        # Should show improvement
        self.assertTrue(result.improvement_achieved)

        # Final narrative should contain both entities
        self.assertIn("Sariel", result.final_narrative)
        self.assertIn("Cassian", result.final_narrative)

    def test_full_pipeline_integration(self):
        """Test all 4 strategies working together in complete pipeline"""
        with patch("entity_preloader.create_from_game_state") as mock_create:
            # Setup mock manifest with proper string attributes
            mock_pc = Mock()
            mock_pc.display_name = "Sariel"
            mock_pc.name = "Sariel"

            mock_npc = Mock()
            mock_npc.display_name = "Cassian"
            mock_npc.name = "Cassian"
            mock_npc.location = "Throne Room"

            mock_manifest = Mock(player_characters=[mock_pc], npcs=[mock_npc])
            mock_create.return_value = mock_manifest

            # Step 1: Generate preload text (Option 3)
            preload_text = self.preloader.create_entity_preload_text(
                self.sample_game_state, 1, 1, self.location
            )

            # Step 2: Generate instructions (Option 5)
            instructions = self.instruction_gen.generate_entity_instructions(
                self.expected_entities, ["Cassian"], self.location
            )

            # Step 3: Combine into enhanced prompt
            enhanced_prompt = f"{preload_text}\n\n{instructions}\n\nContinue the story."

            # Step 4: Simulate AI generation with missing entity
            simulated_response = "Sariel looks around the throne room."

            # Step 5: Validate response (Option 2)
            validation = self.validator.validate_entity_presence(
                simulated_response, self.expected_entities, self.location
            )

            # Should detect missing Cassian
            self.assertFalse(validation.passed)
            self.assertIn("Cassian", validation.missing_entities)

            # Step 6: Use dual-pass for correction (Option 7)
            def mock_generation(prompt):
                if "enhance the following narrative" in prompt:
                    return "Cassian appears."  # Short enhancement
                return "Sariel looks around the throne room."

            dual_pass_result = self.dual_pass.generate_with_dual_pass(
                enhanced_prompt, self.expected_entities, self.location, mock_generation
            )

            # Final result should include both entities
            self.assertIn("Sariel", dual_pass_result.final_narrative)
            self.assertIn("Cassian", dual_pass_result.final_narrative)
            # Should have attempted dual pass
            self.assertIsNotNone(dual_pass_result.first_pass)
            self.assertIsNotNone(dual_pass_result.second_pass)

    def test_cassian_problem_mitigation(self):
        """Test specific mitigation for The Cassian Problem"""
        player_input = "Tell Cassian I was scared and helpless"

        # Generate Cassian-specific instruction
        cassian_instruction = self.instruction_gen.create_entity_specific_instruction(
            "Cassian", player_input
        )

        # Should have emotional handling
        self.assertIn("CRITICAL", cassian_instruction)
        self.assertIn("emotional appeal", cassian_instruction)

        # Generate entity instructions with emotional context
        instructions = self.instruction_gen.generate_entity_instructions(
            ["Sariel", "Cassian"], ["Cassian"], self.location
        )

        # Should prioritize Cassian as referenced
        self.assertIn("Cassian", instructions)
        self.assertIn("MANDATORY", instructions)

        # Test validation of response that ignores Cassian
        bad_response = "Sariel stands alone in the throne room, feeling isolated."
        validation = self.validator.validate_entity_presence(
            bad_response, ["Sariel", "Cassian"], self.location
        )

        # Should detect Cassian problem
        self.assertFalse(validation.passed)
        self.assertIn("Cassian", validation.missing_entities)

        # Should have Cassian-specific retry suggestions
        cassian_suggestions = [
            s for s in validation.retry_suggestions if "Cassian" in s
        ]
        self.assertGreater(len(cassian_suggestions), 0)

    def test_location_enforcement_integration(self):
        """Test location-based entity enforcement across strategies"""
        location = "Lady Cressida's Chambers"
        entities = ["Sariel", "Lady Cressida"]

        # Option 5: Should generate location-specific instructions
        instructions = self.instruction_gen.generate_entity_instructions(
            entities, [], location
        )

        # Should require Lady Cressida in her chambers
        self.assertIn("Lady Cressida", instructions)
        self.assertIn("MANDATORY", instructions)

        # Option 3: Should include location context
        location_specific = self.instruction_gen.create_location_specific_instructions(
            location, entities
        )

        self.assertIn("Lady Cressida", location_specific)
        self.assertIn("chambers", location_specific.lower())

        # Option 2: Should validate location appropriateness
        bad_response = "Sariel explores the empty chambers."
        validation = self.validator.validate_entity_presence(
            bad_response, entities, location
        )

        self.assertFalse(validation.passed)
        self.assertIn("Lady Cressida", validation.missing_entities)

    def test_performance_optimized_pipeline(self):
        """Test optimized pipeline avoiding timeout issues"""
        # Use minimal data structures
        minimal_entities = ["Sariel", "Cassian"]
        minimal_location = "Throne Room"

        # Quick validation test
        quick_narrative = "Sariel and Cassian talk."
        validation = self.validator.validate_entity_presence(
            quick_narrative, minimal_entities, minimal_location
        )

        # Should pass quickly
        self.assertTrue(validation.passed)
        self.assertEqual(len(validation.found_entities), 2)

        # Quick instruction generation
        quick_instructions = self.instruction_gen.generate_entity_instructions(
            minimal_entities, ["Cassian"], minimal_location
        )

        # Should generate without timeout
        self.assertIn("Sariel", quick_instructions)
        self.assertIn("Cassian", quick_instructions)
        self.assertLess(len(quick_instructions), 2000)  # Keep instructions concise


class TestMitigationStatistics(unittest.TestCase):
    """Test statistical analysis of mitigation effectiveness"""

    def setUp(self):
        self.validator = EntityValidator()
        self.retry_manager = EntityRetryManager()

    def test_validation_confidence_scoring(self):
        """Test validation confidence scoring accuracy"""
        test_cases = [
            ("Sariel and Cassian discuss the matter.", ["Sariel", "Cassian"], 0.8),
            ("Sariel looks around.", ["Sariel", "Cassian"], 0.4),
            ("The room is empty.", ["Sariel", "Cassian"], 0.0),
        ]

        for narrative, entities, expected_min_score in test_cases:
            result = self.validator.validate_entity_presence(narrative, entities)

            if expected_min_score > 0.5:
                self.assertGreaterEqual(result.confidence_score, expected_min_score)
            else:
                self.assertLessEqual(result.confidence_score, expected_min_score + 0.2)

    def test_retry_statistics_tracking(self):
        """Test retry statistics and performance tracking"""
        stats = self.retry_manager.get_retry_statistics()

        self.assertIn("max_retries_configured", stats)
        self.assertIn("validator_threshold", stats)
        self.assertIsInstance(stats["max_retries_configured"], int)
        self.assertIsInstance(stats["validator_threshold"], float)


if __name__ == "__main__":
    unittest.main()
