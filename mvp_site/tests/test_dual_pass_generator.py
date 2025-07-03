"""
Unit tests for Dual-Pass Generation System (Option 7)
Tests dual-pass narrative generation with entity verification.
"""

import unittest
from unittest.mock import Mock, patch, call
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dual_pass_generator import (
    DualPassGenerator, AdaptiveEntityInjector, GenerationPass, DualPassResult,
    dual_pass_generator, adaptive_injector
)
from entity_validator import ValidationResult


class TestDualPassGenerator(unittest.TestCase):
    
    def setUp(self):
        self.generator = DualPassGenerator()
    
    def test_build_injection_templates(self):
        """Test that injection templates are properly built"""
        templates = self.generator._build_injection_templates()
        
        # Current implementation only has generic templates
        self.assertIn('generic', templates)
        self.assertIsInstance(templates['generic'], list)
        self.assertGreater(len(templates['generic']), 0)
        
        # Check that templates have placeholders
        generic_template = templates['generic'][0]
        self.assertIn('{entity}', generic_template)
        self.assertIn('{action}', generic_template)
    
    @patch('dual_pass_generator.EntityValidator')
    def test_generate_with_dual_pass_success_first_pass(self, mock_validator_class):
        """Test dual-pass generation when first pass succeeds"""
        # Mock validator
        mock_validator = Mock()
        mock_validator_class.return_value = mock_validator
        
        # First pass succeeds
        successful_validation = ValidationResult(
            passed=True, missing_entities=[], found_entities=["Sariel", "Cassian"],
            confidence_score=0.9, retry_needed=False, retry_suggestions=[]
        )
        mock_validator.validate_entity_presence.return_value = successful_validation
        
        # Mock generation callback
        generation_callback = Mock(return_value="Sariel and Cassian discuss the matter.")
        
        result = self.generator.generate_with_dual_pass(
            "Continue the story", ["Sariel", "Cassian"],
            generation_callback=generation_callback
        )
        
        self.assertTrue(result.success)
        self.assertFalse(result.improvement_achieved)
        self.assertIsNone(result.second_pass)
        self.assertEqual(result.final_narrative, "Sariel and Cassian discuss the matter.")
        generation_callback.assert_called_once()
    
    @patch('dual_pass_generator.EntityValidator')
    def test_generate_with_dual_pass_requires_second_pass(self, mock_validator_class):
        """Test dual-pass generation when second pass is needed"""
        # Mock validator
        mock_validator = Mock()
        mock_validator_class.return_value = mock_validator
        
        # First pass fails, second pass succeeds
        first_validation = ValidationResult(
            passed=False, missing_entities=["Cassian"], found_entities=["Sariel"],
            confidence_score=0.5, retry_needed=True, retry_suggestions=["Include Cassian"]
        )
        second_validation = ValidationResult(
            passed=True, missing_entities=[], found_entities=["Sariel", "Cassian"],
            confidence_score=0.9, retry_needed=False, retry_suggestions=[]
        )
        mock_validator.validate_entity_presence.side_effect = [first_validation, second_validation]
        
        # Mock generation callback
        generation_callback = Mock(side_effect=[
            "Sariel looks around the room.",  # First pass
            "Cassian steps forward to join Sariel."  # Second pass
        ])
        
        result = self.generator.generate_with_dual_pass(
            "Continue the story", ["Sariel", "Cassian"],
            generation_callback=generation_callback
        )
        
        self.assertTrue(result.success)
        self.assertTrue(result.improvement_achieved)
        self.assertIsNotNone(result.second_pass)
        self.assertEqual(generation_callback.call_count, 2)
        
        # Check that final narrative was enhanced (since second pass is much shorter, it gets appended)
        self.assertIn("Cassian", result.final_narrative)
    
    def test_create_injection_prompt(self):
        """Test injection prompt creation for second pass"""
        original_narrative = "Sariel enters the throne room."
        missing_entities = ["Cassian", "Lady Cressida"]
        
        prompt = self.generator._create_injection_prompt(
            original_narrative, missing_entities, "Throne Room"
        )
        
        self.assertIn("enhance the following narrative", prompt)
        self.assertIn("Sariel enters the throne room", prompt)
        self.assertIn("Cassian", prompt)
        self.assertIn("Lady Cressida", prompt)
        self.assertIn("Throne Room", prompt)
        self.assertIn("naturally present and contribute meaningfully", prompt)  # Generic instruction
    
    def test_combine_narratives_complete_rewrite(self):
        """Test narrative combination when second pass is complete rewrite"""
        first_pass = "Short narrative."
        second_pass = "This is a much longer and more detailed narrative that clearly replaces the first one completely."
        
        combined = self.generator._combine_narratives(first_pass, second_pass)
        
        # Should use second pass since it's much longer (complete rewrite)
        self.assertEqual(combined, second_pass)
    
    def test_combine_narratives_append_enhancement(self):
        """Test narrative combination when second pass is enhancement"""
        first_pass = "Sariel enters the throne room and looks around carefully."
        second_pass = "Cassian appears."
        
        combined = self.generator._combine_narratives(first_pass, second_pass)
        
        # Should append since second pass is much shorter
        self.assertIn("Sariel enters the throne room", combined)
        self.assertIn("Cassian appears", combined)
    
    def test_create_entity_injection_snippet_cassian(self):
        """Test entity injection snippet creation for specific entities"""
        snippet = self.generator.create_entity_injection_snippet(
            "Cassian", "Throne Room", "responds nervously"
        )
        
        self.assertIn("Cassian", snippet)
        self.assertIn("responds nervously", snippet)
    
    def test_create_entity_injection_snippet_generic(self):
        """Test entity injection snippet creation for generic entities"""
        snippet = self.generator.create_entity_injection_snippet(
            "Unknown Character", "Location", "speaks up"
        )
        
        self.assertIn("Unknown Character", snippet)
        self.assertIn("speaks up", snippet)


class TestAdaptiveEntityInjector(unittest.TestCase):
    
    def setUp(self):
        self.injector = AdaptiveEntityInjector()
    
    def test_choose_injection_strategy_dialogue(self):
        """Test strategy selection for dialogue-heavy narratives"""
        narrative = 'Sariel says "Hello" to the guard.'
        
        strategy = self.injector._choose_injection_strategy(narrative, "Cassian")
        
        self.assertEqual(strategy, 'dialogue_based')
    
    def test_choose_injection_strategy_action(self):
        """Test strategy selection for action-heavy narratives"""
        narrative = "Sariel moves quickly across the room and looks around."
        
        strategy = self.injector._choose_injection_strategy(narrative, "Cassian")
        
        self.assertEqual(strategy, 'action_based')
    
    def test_choose_injection_strategy_emotional(self):
        """Test strategy selection for emotional narratives"""
        narrative = "Sariel feels scared and helpless in the situation."
        
        strategy = self.injector._choose_injection_strategy(narrative, "Cassian")
        
        self.assertEqual(strategy, 'reaction_based')
    
    def test_choose_injection_strategy_default(self):
        """Test default strategy selection"""
        narrative = "A simple narrative without special keywords."
        
        strategy = self.injector._choose_injection_strategy(narrative, "Cassian")
        
        self.assertEqual(strategy, 'presence_based')
    
    def test_inject_via_dialogue(self):
        """Test dialogue-based entity injection"""
        original = "Sariel looks around the room."
        
        result = self.injector._inject_via_dialogue(original, "Cassian", "Throne Room")
        
        self.assertIn("Sariel looks around the room", result)
        self.assertIn("Cassian speaks up", result)
        self.assertIn("understand the gravity", result)
    
    def test_inject_via_action(self):
        """Test action-based entity injection"""
        original = "The tension builds in the room."
        
        result = self.injector._inject_via_action(original, "Cassian", "Throne Room")
        
        self.assertIn("The tension builds", result)
        self.assertIn("Cassian steps forward", result)
    
    def test_inject_via_presence(self):
        """Test presence-based entity injection"""
        original = "The scene unfolds slowly."
        
        result = self.injector._inject_via_presence(original, "Cassian", "Throne Room")
        
        self.assertIn("The scene unfolds", result)
        self.assertIn("Cassian remains nearby", result)
    
    def test_inject_via_reaction(self):
        """Test reaction-based entity injection"""
        original = "The emotional moment reaches its peak."
        
        result = self.injector._inject_via_reaction(original, "Cassian", "Throne Room")
        
        self.assertIn("emotional moment reaches", result)
        self.assertIn("Cassian shows clear concern", result)
    
    def test_inject_entities_adaptively(self):
        """Test full adaptive injection process"""
        narrative = "Sariel speaks about her fears."
        missing_entities = ["Cassian", "Lady Cressida"]
        
        result = self.injector.inject_entities_adaptively(narrative, missing_entities)
        
        self.assertIn("Sariel speaks about her fears", result)
        self.assertIn("Cassian", result)
        self.assertIn("Lady Cressida", result)


class TestDataClasses(unittest.TestCase):
    
    def test_generation_pass_creation(self):
        """Test GenerationPass dataclass creation"""
        validation_result = ValidationResult(
            passed=True, missing_entities=[], found_entities=["Sariel"],
            confidence_score=0.9, retry_needed=False, retry_suggestions=[]
        )
        
        pass_obj = GenerationPass(
            pass_number=1,
            prompt="Test prompt",
            response="Test response",
            entities_found=["Sariel"],
            validation_result=validation_result
        )
        
        self.assertEqual(pass_obj.pass_number, 1)
        self.assertEqual(pass_obj.prompt, "Test prompt")
        self.assertEqual(pass_obj.response, "Test response")
        self.assertIn("Sariel", pass_obj.entities_found)
        self.assertEqual(pass_obj.validation_result, validation_result)
    
    def test_dual_pass_result_creation(self):
        """Test DualPassResult dataclass creation"""
        first_pass = GenerationPass(1, "prompt", "response", ["Sariel"])
        
        result = DualPassResult(
            first_pass=first_pass,
            second_pass=None,
            final_narrative="Final narrative",
            total_entities_found=["Sariel"],
            success=True,
            improvement_achieved=False
        )
        
        self.assertEqual(result.first_pass, first_pass)
        self.assertIsNone(result.second_pass)
        self.assertEqual(result.final_narrative, "Final narrative")
        self.assertTrue(result.success)
        self.assertFalse(result.improvement_achieved)


class TestGlobalInstances(unittest.TestCase):
    
    def test_global_dual_pass_generator_exists(self):
        """Test that global dual pass generator instance exists"""
        self.assertIsInstance(dual_pass_generator, DualPassGenerator)
    
    def test_global_adaptive_injector_exists(self):
        """Test that global adaptive injector instance exists"""
        self.assertIsInstance(adaptive_injector, AdaptiveEntityInjector)


if __name__ == '__main__':
    unittest.main()