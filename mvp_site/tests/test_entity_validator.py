"""
Unit tests for Enhanced Post-Generation Validation with Retry (Option 2 Enhanced)
Tests entity validation and retry logic functionality.
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch

# Add parent directory to path for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from mvp_site.entity_validator import (
    EntityRetryManager,
    EntityValidator,
    ValidationResult,
    entity_retry_manager,
    entity_validator,
)


class TestEntityValidator(unittest.TestCase):
    def setUp(self):
        self.validator = EntityValidator(min_confidence_threshold=0.7)

    def test_validate_entity_presence_success(self):
        """Test successful entity validation"""
        narrative = (
            "Sariel draws her sword while Cassian watches nervously from the corner."
        )
        expected_entities = ["Sariel", "Cassian"]

        result = self.validator.validate_entity_presence(narrative, expected_entities)

        assert result.passed
        assert not result.retry_needed
        assert set(result.found_entities) == set(expected_entities)
        assert len(result.missing_entities) == 0
        assert result.confidence_score > 0.7

    def test_validate_entity_presence_missing_entities(self):
        """Test validation with missing entities"""
        narrative = "Sariel looks around the empty throne room."
        expected_entities = ["Sariel", "Cassian", "Lady Cressida"]

        result = self.validator.validate_entity_presence(narrative, expected_entities)

        assert not result.passed
        assert result.retry_needed
        assert "Sariel" in result.found_entities
        assert "Cassian" in result.missing_entities
        assert "Lady Cressida" in result.missing_entities

    def test_calculate_entity_presence_score_direct_mention(self):
        """Test scoring for direct entity mentions"""
        narrative = "Cassian speaks to Sariel about the urgent matter."

        score = self.validator._calculate_entity_presence_score(narrative, "Cassian")

        # Direct mention should score high (0.8+)
        assert score > 0.8

    def test_calculate_entity_presence_score_action_attribution(self):
        """Test scoring for action attribution patterns"""
        narrative = "Cassian says the situation is dire."

        score = self.validator._calculate_entity_presence_score(narrative, "Cassian")

        # Direct mention + action attribution should score very high (capped at 1.0)
        assert score == 1.0

    def test_calculate_entity_presence_score_partial_match(self):
        """Test scoring for partial name matches"""
        narrative = "Lady Cressida greets the visitors warmly."

        score = self.validator._calculate_entity_presence_score(
            narrative, "Lady Cressida Valeriana"
        )

        # Partial match should give some score (2/3 of name parts match)
        assert score > 0.3
        assert score < 0.8

    def test_generate_retry_suggestions_cassian(self):
        """Test retry suggestions for Cassian specifically"""
        missing_entities = ["Cassian"]
        suggestions = self.validator._generate_retry_suggestions(
            missing_entities, ["Sariel"], "narrative text", "Throne Room"
        )

        # Should have Cassian-specific suggestion
        cassian_suggestion = next((s for s in suggestions if "Cassian" in s), None)
        assert cassian_suggestion is not None
        # Verify the suggestion content
        if cassian_suggestion:
            assert "cassian" in cassian_suggestion.lower()
            assert "dialogue, actions, or reactions" in cassian_suggestion.lower()

    def test_generate_retry_suggestions_location_specific(self):
        """Test location-specific retry suggestions"""
        missing_entities = ["Lady Cressida"]
        suggestions = self.validator._generate_retry_suggestions(
            missing_entities, [], "narrative", "Lady Cressida's Chambers"
        )

        # Should have location-specific suggestion
        location_suggestion = next(
            (s for s in suggestions if "chambers" in s.lower()), None
        )
        assert location_suggestion is not None

    def test_create_retry_prompt(self):
        """Test retry prompt creation"""
        original_prompt = "Continue the story."
        validation_result = ValidationResult(
            passed=False,
            missing_entities=["Cassian", "Lady Cressida"],
            found_entities=["Sariel"],
            confidence_score=0.4,
            retry_needed=True,
            retry_suggestions=[
                "Include Cassian's reaction",
                "Show Lady Cressida in chambers",
            ],
        )

        retry_prompt = self.validator.create_retry_prompt(
            original_prompt, validation_result, "Throne Room"
        )

        assert "RETRY INSTRUCTIONS" in retry_prompt
        assert "Cassian" in retry_prompt
        assert "Lady Cressida" in retry_prompt
        assert "Throne Room" in retry_prompt
        assert "Continue the story." in retry_prompt

    def test_create_retry_prompt_no_retry_needed(self):
        """Test retry prompt when no retry is needed"""
        original_prompt = "Continue the story."
        validation_result = ValidationResult(
            passed=True,
            missing_entities=[],
            found_entities=["Sariel"],
            confidence_score=0.9,
            retry_needed=False,
            retry_suggestions=[],
        )

        retry_prompt = self.validator.create_retry_prompt(
            original_prompt, validation_result
        )

        # Should return original prompt unchanged
        assert retry_prompt == original_prompt


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

        assert result.passed
        assert attempts == 0  # No retries needed

    @patch("entity_validator.EntityValidator.validate_entity_presence")
    def test_validate_with_retry_success_after_retry(self, mock_validate):
        """Test successful validation after retry"""
        # First validation fails, second succeeds
        first_result = ValidationResult(
            passed=False,
            missing_entities=["Cassian"],
            found_entities=["Sariel"],
            confidence_score=0.5,
            retry_needed=True,
            retry_suggestions=["Include Cassian"],
        )
        second_result = ValidationResult(
            passed=True,
            missing_entities=[],
            found_entities=["Sariel", "Cassian"],
            confidence_score=0.9,
            retry_needed=False,
            retry_suggestions=[],
        )
        mock_validate.side_effect = [first_result, second_result]

        # Mock retry callback
        retry_callback = Mock(return_value="New narrative with Cassian")

        result, attempts = self.retry_manager.validate_with_retry(
            "Original narrative", ["Sariel", "Cassian"], retry_callback=retry_callback
        )

        assert result.passed
        assert attempts == 1
        retry_callback.assert_called_once()

    @patch("entity_validator.EntityValidator.validate_entity_presence")
    def test_validate_with_retry_max_retries_exceeded(self, mock_validate):
        """Test behavior when max retries exceeded"""
        # All validation attempts fail
        failed_result = ValidationResult(
            passed=False,
            missing_entities=["Cassian"],
            found_entities=["Sariel"],
            confidence_score=0.5,
            retry_needed=True,
            retry_suggestions=["Include Cassian"],
        )
        mock_validate.return_value = failed_result

        retry_callback = Mock(return_value="Still missing Cassian")

        result, attempts = self.retry_manager.validate_with_retry(
            "Original narrative", ["Sariel", "Cassian"], retry_callback=retry_callback
        )

        assert not result.passed
        assert attempts == 2  # Max retries
        assert retry_callback.call_count == 2

    def test_validate_with_retry_no_callback(self):
        """Test validation without retry callback"""
        narrative = "Sariel looks around the empty room."
        expected_entities = ["Sariel", "Cassian"]

        result, attempts = self.retry_manager.validate_with_retry(
            narrative, expected_entities
        )

        # Should fail but not attempt retries without callback
        assert not result.passed
        assert attempts == 0

    def test_get_retry_statistics(self):
        """Test retry statistics retrieval"""
        stats = self.retry_manager.get_retry_statistics()

        assert "max_retries_configured" in stats
        assert "validator_threshold" in stats
        assert stats["max_retries_configured"] == 2


class TestValidationResultDataClass(unittest.TestCase):
    def test_validation_result_creation(self):
        """Test ValidationResult dataclass creation"""
        result = ValidationResult(
            passed=True,
            missing_entities=[],
            found_entities=["Sariel"],
            confidence_score=0.9,
            retry_needed=False,
            retry_suggestions=[],
        )

        assert result.passed
        assert len(result.missing_entities) == 0
        assert "Sariel" in result.found_entities
        assert result.confidence_score == 0.9
        assert not result.retry_needed


class TestGlobalInstances(unittest.TestCase):
    def test_global_entity_validator_exists(self):
        """Test that global entity validator instance exists"""
        assert isinstance(entity_validator, EntityValidator)

    def test_global_entity_retry_manager_exists(self):
        """Test that global entity retry manager instance exists"""
        assert isinstance(entity_retry_manager, EntityRetryManager)


if __name__ == "__main__":
    unittest.main()
