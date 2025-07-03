"""
Unit tests for Enhanced Post-Generation Validation with Retry (Option 2 Enhanced)
Tests entity validation and retry logic functionality.
"""

import unittest
from unittest.mock import Mock, patch, call
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from entity_validator import EntityValidator, EntityRetryManager, ValidationResult, entity_validator, entity_retry_manager


class TestEntityValidator(unittest.TestCase):
    
    def setUp(self):
        self.validator = EntityValidator(min_confidence_threshold=0.7)
    
    def test_validate_entity_presence_success(self):
        """Test successful entity validation"""
        narrative = "Sariel draws her sword while Cassian watches nervously from the corner."
        expected_entities = ["Sariel", "Cassian"]
        
        result = self.validator.validate_entity_presence(narrative, expected_entities)
        
        self.assertTrue(result.passed)
        self.assertFalse(result.retry_needed)
        self.assertEqual(set(result.found_entities), set(expected_entities))
        self.assertEqual(len(result.missing_entities), 0)
        self.assertGreater(result.confidence_score, 0.7)
    
    def test_validate_entity_presence_missing_entities(self):
        """Test validation with missing entities"""
        narrative = "Sariel looks around the empty throne room."
        expected_entities = ["Sariel", "Cassian", "Lady Cressida"]
        
        result = self.validator.validate_entity_presence(narrative, expected_entities)
        
        self.assertFalse(result.passed)
        self.assertTrue(result.retry_needed)
        self.assertIn("Sariel", result.found_entities)
        self.assertIn("Cassian", result.missing_entities)
        self.assertIn("Lady Cressida", result.missing_entities)
    
    def test_calculate_entity_presence_score_direct_mention(self):
        """Test scoring for direct entity mentions"""
        narrative = "Cassian speaks to Sariel about the urgent matter."
        
        score = self.validator._calculate_entity_presence_score(narrative, "Cassian")
        
        # Direct mention should score high (0.8+)
        self.assertGreater(score, 0.8)
    
    def test_calculate_entity_presence_score_action_attribution(self):
        """Test scoring for action attribution patterns"""
        narrative = "Cassian says the situation is dire."
        
        score = self.validator._calculate_entity_presence_score(narrative, "Cassian")
        
        # Direct mention + action attribution should score very high (capped at 1.0)
        self.assertEqual(score, 1.0)
    
    def test_calculate_entity_presence_score_partial_match(self):
        """Test scoring for partial name matches"""
        narrative = "Lady Cressida greets the visitors warmly."
        
        score = self.validator._calculate_entity_presence_score(narrative, "Lady Cressida Valeriana")
        
        # Partial match should give some score (2/3 of name parts match)
        self.assertGreater(score, 0.3)
        self.assertLess(score, 0.8)
    
    def test_generate_retry_suggestions_cassian(self):
        """Test retry suggestions for Cassian specifically"""
        missing_entities = ["Cassian"]
        suggestions = self.validator._generate_retry_suggestions(
            missing_entities, ["Sariel"], "narrative text", "Throne Room"
        )
        
        # Should have Cassian-specific suggestion
        cassian_suggestion = next((s for s in suggestions if "Cassian" in s), None)
        self.assertIsNotNone(cassian_suggestion)
        # Verify the suggestion content
        if cassian_suggestion:
            self.assertIn("cassian", cassian_suggestion.lower())
            self.assertIn("dialogue, actions, or reactions", cassian_suggestion.lower())
    
    def test_generate_retry_suggestions_location_specific(self):
        """Test location-specific retry suggestions"""
        missing_entities = ["Lady Cressida"]
        suggestions = self.validator._generate_retry_suggestions(
            missing_entities, [], "narrative", "Lady Cressida's Chambers"
        )
        
        # Should have location-specific suggestion
        location_suggestion = next((s for s in suggestions if "chambers" in s.lower()), None)
        self.assertIsNotNone(location_suggestion)
    
    def test_create_retry_prompt(self):
        """Test retry prompt creation"""
        original_prompt = "Continue the story."
        validation_result = ValidationResult(
            passed=False,
            missing_entities=["Cassian", "Lady Cressida"],
            found_entities=["Sariel"],
            confidence_score=0.4,
            retry_needed=True,
            retry_suggestions=["Include Cassian's reaction", "Show Lady Cressida in chambers"]
        )
        
        retry_prompt = self.validator.create_retry_prompt(
            original_prompt, validation_result, "Throne Room"
        )
        
        self.assertIn("RETRY INSTRUCTIONS", retry_prompt)
        self.assertIn("Cassian", retry_prompt)
        self.assertIn("Lady Cressida", retry_prompt)
        self.assertIn("Throne Room", retry_prompt)
        self.assertIn("Continue the story.", retry_prompt)
    
    def test_create_retry_prompt_no_retry_needed(self):
        """Test retry prompt when no retry is needed"""
        original_prompt = "Continue the story."
        validation_result = ValidationResult(
            passed=True,
            missing_entities=[],
            found_entities=["Sariel"],
            confidence_score=0.9,
            retry_needed=False,
            retry_suggestions=[]
        )
        
        retry_prompt = self.validator.create_retry_prompt(original_prompt, validation_result)
        
        # Should return original prompt unchanged
        self.assertEqual(retry_prompt, original_prompt)


class TestEntityRetryManager(unittest.TestCase):
    
    def setUp(self):
        self.retry_manager = EntityRetryManager(max_retries=2)
    
    def test_validate_with_retry_success_first_try(self):
        """Test successful validation on first try"""
        narrative = "Sariel and Cassian discuss the situation."
        expected_entities = ["Sariel", "Cassian"]
        
        result, attempts = self.retry_manager.validate_with_retry(
            narrative, expected_entities
        )
        
        self.assertTrue(result.passed)
        self.assertEqual(attempts, 0)  # No retries needed
    
    @patch('entity_validator.EntityValidator.validate_entity_presence')
    def test_validate_with_retry_success_after_retry(self, mock_validate):
        """Test successful validation after retry"""
        # First validation fails, second succeeds
        first_result = ValidationResult(
            passed=False, missing_entities=["Cassian"], found_entities=["Sariel"],
            confidence_score=0.5, retry_needed=True, retry_suggestions=["Include Cassian"]
        )
        second_result = ValidationResult(
            passed=True, missing_entities=[], found_entities=["Sariel", "Cassian"],
            confidence_score=0.9, retry_needed=False, retry_suggestions=[]
        )
        mock_validate.side_effect = [first_result, second_result]
        
        # Mock retry callback
        retry_callback = Mock(return_value="New narrative with Cassian")
        
        result, attempts = self.retry_manager.validate_with_retry(
            "Original narrative", ["Sariel", "Cassian"], 
            retry_callback=retry_callback
        )
        
        self.assertTrue(result.passed)
        self.assertEqual(attempts, 1)
        retry_callback.assert_called_once()
    
    @patch('entity_validator.EntityValidator.validate_entity_presence')
    def test_validate_with_retry_max_retries_exceeded(self, mock_validate):
        """Test behavior when max retries exceeded"""
        # All validation attempts fail
        failed_result = ValidationResult(
            passed=False, missing_entities=["Cassian"], found_entities=["Sariel"],
            confidence_score=0.5, retry_needed=True, retry_suggestions=["Include Cassian"]
        )
        mock_validate.return_value = failed_result
        
        retry_callback = Mock(return_value="Still missing Cassian")
        
        result, attempts = self.retry_manager.validate_with_retry(
            "Original narrative", ["Sariel", "Cassian"],
            retry_callback=retry_callback
        )
        
        self.assertFalse(result.passed)
        self.assertEqual(attempts, 2)  # Max retries
        self.assertEqual(retry_callback.call_count, 2)
    
    def test_validate_with_retry_no_callback(self):
        """Test validation without retry callback"""
        narrative = "Sariel looks around the empty room."
        expected_entities = ["Sariel", "Cassian"]
        
        result, attempts = self.retry_manager.validate_with_retry(
            narrative, expected_entities
        )
        
        # Should fail but not attempt retries without callback
        self.assertFalse(result.passed)
        self.assertEqual(attempts, 0)
    
    def test_get_retry_statistics(self):
        """Test retry statistics retrieval"""
        stats = self.retry_manager.get_retry_statistics()
        
        self.assertIn("max_retries_configured", stats)
        self.assertIn("validator_threshold", stats)
        self.assertEqual(stats["max_retries_configured"], 2)


class TestValidationResultDataClass(unittest.TestCase):
    
    def test_validation_result_creation(self):
        """Test ValidationResult dataclass creation"""
        result = ValidationResult(
            passed=True,
            missing_entities=[],
            found_entities=["Sariel"],
            confidence_score=0.9,
            retry_needed=False,
            retry_suggestions=[]
        )
        
        self.assertTrue(result.passed)
        self.assertEqual(len(result.missing_entities), 0)
        self.assertIn("Sariel", result.found_entities)
        self.assertEqual(result.confidence_score, 0.9)
        self.assertFalse(result.retry_needed)


class TestGlobalInstances(unittest.TestCase):
    
    def test_global_entity_validator_exists(self):
        """Test that global entity validator instance exists"""
        self.assertIsInstance(entity_validator, EntityValidator)
    
    def test_global_entity_retry_manager_exists(self):
        """Test that global entity retry manager instance exists"""
        self.assertIsInstance(entity_retry_manager, EntityRetryManager)


if __name__ == '__main__':
    unittest.main()