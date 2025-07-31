"""
Unit tests for Dual-Pass Generation System (Option 7)
Tests dual-pass narrative generation with entity verification.
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch

# Add parent directory to path for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from dual_pass_generator import (
    AdaptiveEntityInjector,
    DualPassGenerator,
    DualPassResult,
    GenerationPass,
    adaptive_injector,
    dual_pass_generator,
)
from entity_validator import ValidationResult, entity_validator


class TestDualPassGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = DualPassGenerator()

    def test_build_injection_templates(self):
        """Test that injection templates are properly built via EntityValidator"""
        # This functionality now lives in EntityValidator

        missing_entities = ["Gideon", "Sariel"]
        templates = entity_validator.create_injection_templates(missing_entities)

        # Should have templates for each missing entity
        assert "Gideon" in templates
        assert "Sariel" in templates
        assert isinstance(templates["Gideon"], list)
        assert len(templates["Gideon"]) > 0

        # Check that templates have placeholders
        generic_template = templates["Gideon"][0]
        assert "{entity}" in generic_template
        assert "{action}" in generic_template

    @patch("dual_pass_generator.EntityValidator")
    def test_generate_with_dual_pass_success_first_pass(self, mock_validator_class):
        """Test dual-pass generation when first pass succeeds"""
        # Mock validator
        mock_validator = Mock()
        mock_validator_class.return_value = mock_validator

        # First pass succeeds
        successful_validation = ValidationResult(
            passed=True,
            missing_entities=[],
            found_entities=["Sariel", "Cassian"],
            confidence_score=0.9,
            retry_needed=False,
            retry_suggestions=[],
        )
        mock_validator.validate_entity_presence.return_value = successful_validation

        # Mock generation callback
        generation_callback = Mock(
            return_value="Sariel and Cassian discuss the matter."
        )

        result = self.generator.generate_with_dual_pass(
            "Continue the story",
            ["Sariel", "Cassian"],
            generation_callback=generation_callback,
        )

        assert result.success
        assert not result.improvement_achieved
        assert result.second_pass is None
        assert result.final_narrative == "Sariel and Cassian discuss the matter."
        generation_callback.assert_called_once()

    @patch("dual_pass_generator.EntityValidator")
    def test_generate_with_dual_pass_requires_second_pass(self, mock_validator_class):
        """Test dual-pass generation when second pass is needed"""
        # Mock validator
        mock_validator = Mock()
        mock_validator_class.return_value = mock_validator

        # First pass fails, second pass succeeds
        first_validation = ValidationResult(
            passed=False,
            missing_entities=["Cassian"],
            found_entities=["Sariel"],
            confidence_score=0.5,
            retry_needed=True,
            retry_suggestions=["Include Cassian"],
        )
        second_validation = ValidationResult(
            passed=True,
            missing_entities=[],
            found_entities=["Sariel", "Cassian"],
            confidence_score=0.9,
            retry_needed=False,
            retry_suggestions=[],
        )
        mock_validator.validate_entity_presence.side_effect = [
            first_validation,
            second_validation,
        ]

        # Mock generation callback
        generation_callback = Mock(
            side_effect=[
                "Sariel looks around the room.",  # First pass
                "Cassian steps forward to join Sariel.",  # Second pass
            ]
        )

        result = self.generator.generate_with_dual_pass(
            "Continue the story",
            ["Sariel", "Cassian"],
            generation_callback=generation_callback,
        )

        assert result.success
        assert result.improvement_achieved
        assert result.second_pass is not None
        assert generation_callback.call_count == 2

        # Check that final narrative was enhanced (since second pass is much shorter, it gets appended)
        assert "Cassian" in result.final_narrative

    def test_create_injection_prompt(self):
        """Test injection prompt creation for second pass"""
        original_narrative = "Sariel enters the throne room."
        missing_entities = ["Cassian", "Lady Cressida"]

        prompt = self.generator._create_injection_prompt(
            original_narrative, missing_entities, "Throne Room"
        )

        assert "enhance the following narrative" in prompt
        assert "Sariel enters the throne room" in prompt
        assert "Cassian" in prompt
        assert "Lady Cressida" in prompt
        assert "Throne Room" in prompt
        assert "naturally present and contribute meaningfully" in prompt  # Generic instruction

    def test_combine_narratives_complete_rewrite(self):
        """Test narrative combination when second pass is complete rewrite"""
        first_pass = "Short narrative."
        second_pass = "This is a much longer and more detailed narrative that clearly replaces the first one completely."

        combined = self.generator._combine_narratives(first_pass, second_pass)

        # Should use second pass since it's much longer (complete rewrite)
        assert combined == second_pass

    def test_combine_narratives_append_enhancement(self):
        """Test narrative combination when second pass is enhancement"""
        first_pass = "Sariel enters the throne room and looks around carefully."
        second_pass = "Cassian appears."

        combined = self.generator._combine_narratives(first_pass, second_pass)

        # Should append since second pass is much shorter
        assert "Sariel enters the throne room" in combined
        assert "Cassian appears" in combined

    def test_create_entity_injection_snippet_cassian(self):
        """Test entity injection snippet creation for specific entities"""
        snippet = self.generator.create_entity_injection_snippet(
            "Cassian", "Throne Room", "responds nervously"
        )

        assert "Cassian" in snippet
        assert "responds nervously" in snippet

    def test_create_entity_injection_snippet_generic(self):
        """Test entity injection snippet creation for generic entities"""
        snippet = self.generator.create_entity_injection_snippet(
            "Unknown Character", "Location", "speaks up"
        )

        assert "Unknown Character" in snippet
        assert "speaks up" in snippet


class TestAdaptiveEntityInjector(unittest.TestCase):
    def setUp(self):
        self.injector = AdaptiveEntityInjector()

    def test_choose_injection_strategy_dialogue(self):
        """Test strategy selection for dialogue-heavy narratives"""
        narrative = 'Sariel says "Hello" to the guard.'

        strategy = self.injector._choose_injection_strategy(narrative, "Cassian")

        assert strategy == "dialogue_based"

    def test_choose_injection_strategy_action(self):
        """Test strategy selection for action-heavy narratives"""
        narrative = "Sariel moves quickly across the room and looks around."

        strategy = self.injector._choose_injection_strategy(narrative, "Cassian")

        assert strategy == "action_based"

    def test_choose_injection_strategy_emotional(self):
        """Test strategy selection for emotional narratives"""
        narrative = "Sariel feels scared and helpless in the situation."

        strategy = self.injector._choose_injection_strategy(narrative, "Cassian")

        assert strategy == "reaction_based"

    def test_choose_injection_strategy_default(self):
        """Test default strategy selection"""
        narrative = "A simple narrative without special keywords."

        strategy = self.injector._choose_injection_strategy(narrative, "Cassian")

        assert strategy == "presence_based"

    def test_inject_via_dialogue(self):
        """Test dialogue-based entity injection"""
        original = "Sariel looks around the room."

        result = self.injector._inject_via_dialogue(original, "Cassian", "Throne Room")

        assert "Sariel looks around the room" in result
        assert "Cassian speaks up" in result
        assert "understand the gravity" in result

    def test_inject_via_action(self):
        """Test action-based entity injection"""
        original = "The tension builds in the room."

        result = self.injector._inject_via_action(original, "Cassian", "Throne Room")

        assert "The tension builds" in result
        assert "Cassian steps forward" in result

    def test_inject_via_presence(self):
        """Test presence-based entity injection"""
        original = "The scene unfolds slowly."

        result = self.injector._inject_via_presence(original, "Cassian", "Throne Room")

        assert "The scene unfolds" in result
        assert "Cassian remains nearby" in result

    def test_inject_via_reaction(self):
        """Test reaction-based entity injection"""
        original = "The emotional moment reaches its peak."

        result = self.injector._inject_via_reaction(original, "Cassian", "Throne Room")

        assert "emotional moment reaches" in result
        assert "Cassian shows clear concern" in result

    def test_inject_entities_adaptively(self):
        """Test full adaptive injection process"""
        narrative = "Sariel speaks about her fears."
        missing_entities = ["Cassian", "Lady Cressida"]

        result = self.injector.inject_entities_adaptively(narrative, missing_entities)

        assert "Sariel speaks about her fears" in result
        assert "Cassian" in result
        assert "Lady Cressida" in result


class TestDataClasses(unittest.TestCase):
    def test_generation_pass_creation(self):
        """Test GenerationPass dataclass creation"""
        validation_result = ValidationResult(
            passed=True,
            missing_entities=[],
            found_entities=["Sariel"],
            confidence_score=0.9,
            retry_needed=False,
            retry_suggestions=[],
        )

        pass_obj = GenerationPass(
            pass_number=1,
            prompt="Test prompt",
            response="Test response",
            entities_found=["Sariel"],
            validation_result=validation_result,
        )

        assert pass_obj.pass_number == 1
        assert pass_obj.prompt == "Test prompt"
        assert pass_obj.response == "Test response"
        assert "Sariel" in pass_obj.entities_found
        assert pass_obj.validation_result == validation_result

    def test_dual_pass_result_creation(self):
        """Test DualPassResult dataclass creation"""
        first_pass = GenerationPass(1, "prompt", "response", ["Sariel"])

        result = DualPassResult(
            first_pass=first_pass,
            second_pass=None,
            final_narrative="Final narrative",
            total_entities_found=["Sariel"],
            success=True,
            improvement_achieved=False,
        )

        assert result.first_pass == first_pass
        assert result.second_pass is None
        assert result.final_narrative == "Final narrative"
        assert result.success
        assert not result.improvement_achieved


class TestGlobalInstances(unittest.TestCase):
    def test_global_dual_pass_generator_exists(self):
        """Test that global dual pass generator instance exists"""
        assert isinstance(dual_pass_generator, DualPassGenerator)

    def test_global_adaptive_injector_exists(self):
        """Test that global adaptive injector instance exists"""
        assert isinstance(adaptive_injector, AdaptiveEntityInjector)


if __name__ == "__main__":
    unittest.main()
