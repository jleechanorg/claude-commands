#!/usr/bin/env python3
"""
Integration tests for validation system.
Tests the complete flow from game state through validation to results.
"""

import os
import sys
import time
import unittest
from unittest.mock import patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_state_integration import MockGameState, NarrativeValidationMixin
from validators.fuzzy_token_validator import FuzzyTokenValidator
from validators.hybrid_validator import HybridValidator
from validators.llm_validator import LLMValidator
from validators.token_validator import TokenValidator


class TestGameStateIntegration(unittest.TestCase):
    """Test integration with game state."""

    def setUp(self):
        """Set up test fixtures."""
        self.game_state = MockGameState()

    def test_entity_manifest_generation(self):
        """Test that entity manifest is correctly generated."""
        manifest = self.game_state.get_active_entity_manifest()

        assert manifest["location"] == "Kaelan's Cell"
        assert manifest["entity_count"] == 2
        assert len(manifest["entities"]) == 2

        # Check entity details
        gideon = next(e for e in manifest["entities"] if e["name"] == "Gideon")
        assert "knight" in gideon["descriptors"]
        assert "conscious" in gideon["status"]

    def test_manifest_caching(self):
        """Test that manifest caching works correctly."""
        # First call
        manifest1 = self.game_state.get_active_entity_manifest()

        # Modify state (should not affect cached result)
        self.game_state.party_members.append("Marcus")

        # Second call (should be cached)
        manifest2 = self.game_state.get_active_entity_manifest()

        # Should be the same (cached)
        assert manifest1["entity_count"] == manifest2["entity_count"]

        # Clear cache by setting timestamp to None
        self.game_state._manifest_timestamp = None

        # Third call (should regenerate)
        manifest3 = self.game_state.get_active_entity_manifest()
        assert manifest3["entity_count"] == 3  # Now includes Marcus

    def test_validate_narrative_consistency(self):
        """Test narrative validation integration."""
        # Test with valid narrative
        result = self.game_state.validate_narrative_consistency(
            "Gideon stepped forward while Rowan prepared her spells."
        )

        assert result["is_valid"]
        assert result["missing_entities"] == []
        assert result["confidence"] > 0.8

        # Test with missing entity
        result = self.game_state.validate_narrative_consistency(
            "The knight stood alone in the chamber."
        )

        assert not result["is_valid"]
        assert "Rowan" in result["missing_entities"]

    def test_strictness_levels(self):
        """Test different strictness levels."""
        ambiguous_narrative = "Someone moved in the shadows."

        # Strict should reject ambiguous
        result_strict = self.game_state.validate_narrative_consistency(
            ambiguous_narrative, strictness="strict"
        )
        assert not result_strict["is_valid"]

        # Lenient might be more forgiving
        result_lenient = self.game_state.validate_narrative_consistency(
            ambiguous_narrative, strictness="lenient"
        )
        # Lenient still won't accept completely ambiguous, but confidence differs
        assert result_lenient["confidence"] < result_strict["confidence"]


class TestNarrativeServiceIntegration(unittest.TestCase):
    """Test integration with narrative generation service."""

    def setUp(self):
        """Set up test fixtures."""
        self.game_state = MockGameState()
        self.service = NarrativeValidationMixin()

    def test_generate_narrative_with_validation(self):
        """Test complete narrative generation flow."""
        result = self.service.generate_narrative_with_validation(
            self.game_state, "Describe the party preparing for battle"
        )

        assert "narrative" in result
        assert "validation" in result
        assert "manifest_used" in result

        # Should generate valid narrative
        assert result["validation"]["is_valid"]

    def test_validation_failure_retry(self):
        """Test retry logic on validation failure."""
        # Mock the generate method to fail first time
        original_method = self.service._mock_generate_narrative
        call_count = 0

        def mock_fail_then_succeed(prompt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return "The chamber was empty."  # Missing entities
            return "Gideon and Rowan prepared for battle."

        self.service._mock_generate_narrative = mock_fail_then_succeed

        result = self.service.generate_narrative_with_validation(
            self.game_state, "Describe the scene"
        )

        # Should have retried and succeeded
        assert call_count == 2
        assert result["validation"]["is_valid"]

        # Restore original
        self.service._mock_generate_narrative = original_method

    def test_prompt_sanitization(self):
        """Test that entity names are sanitized."""
        # Add entity with dangerous characters
        self.game_state.party_members.append("Evil'; DROP TABLE--")

        result = self.service.generate_narrative_with_validation(
            self.game_state, "Test prompt"
        )

        # Should not have SQL injection in narrative
        assert "DROP TABLE" not in result["narrative"]


class TestValidatorIntegration(unittest.TestCase):
    """Test validators work correctly together."""

    def setUp(self):
        """Set up validators."""
        self.token_validator = TokenValidator()
        self.fuzzy_validator = FuzzyTokenValidator()
        self.llm_validator = LLMValidator()  # Uses mock
        self.hybrid_validator = HybridValidator()

        self.test_narrative = "Ser Vance raised his sword while the healer chanted."
        self.expected_entities = ["Gideon", "Rowan"]

    def test_validator_consistency(self):
        """Test that validators produce consistent results."""
        results = {}

        for name, validator in [
            ("token", self.token_validator),
            ("fuzzy", self.fuzzy_validator),
            ("llm", self.llm_validator),
            ("hybrid", self.hybrid_validator),
        ]:
            result = validator.validate(
                self.test_narrative, self.expected_entities, "Combat Arena"
            )
            results[name] = result

        # All should find both entities (via descriptors)
        for name, result in results.items():
            assert set(result.entities_found) == set(
                self.expected_entities
            ), f"{name} validator failed to find all entities"

    def test_hybrid_combination_strategies(self):
        """Test different hybrid combination strategies."""
        strategies = ["weighted_vote", "unanimous", "majority", "confidence_based"]

        for strategy in strategies:
            hybrid = HybridValidator(combination_strategy=strategy)
            result = hybrid.validate(self.test_narrative, self.expected_entities)

            # All strategies should work for clear case
            assert result.all_entities_present, f"{strategy} strategy failed"


class TestEndToEndFlow(unittest.TestCase):
    """Test complete end-to-end validation flow."""

    def test_full_integration_flow(self):
        """Test from game state to final validation result."""
        # 1. Create game state
        game_state = MockGameState()
        game_state.party_members = ["Gideon", "Rowan", "Marcus"]
        game_state.current_location = "Dragon's Lair"

        # 2. Generate manifest
        manifest = game_state.get_active_entity_manifest()
        assert manifest["entity_count"] == 3

        # 3. Create narrative
        narrative = "Gideon, Rowan, and Marcus faced the dragon together."

        # 4. Validate
        result = game_state.validate_narrative_consistency(narrative)

        # 5. Verify result
        assert result["is_valid"]
        assert len(result["missing_entities"]) == 0
        assert result["confidence"] > 0.9

    def test_performance_requirements(self):
        """Test that validation meets performance requirements."""

        game_state = MockGameState()
        narrative = "Gideon and Rowan explored the dungeon."

        # Warm up cache
        game_state.get_active_entity_manifest()

        # Time validation
        start = time.time()
        for _ in range(10):
            game_state.validate_narrative_consistency(narrative)
        duration = (time.time() - start) / 10

        # Should be under 50ms (0.05s)
        assert duration < 0.05, f"Validation too slow: {duration * 1000:.1f}ms"


class TestErrorHandling(unittest.TestCase):
    """Test error handling in integration."""

    def test_validator_failure_handling(self):
        """Test handling when validator fails."""
        game_state = MockGameState()

        # Mock validator to raise exception
        with patch(
            "validators.fuzzy_token_validator.FuzzyTokenValidator.validate"
        ) as mock_validate:
            mock_validate.side_effect = Exception("Validator error")

            result = game_state.validate_narrative_consistency("Test narrative")

            # Should handle gracefully
            assert not result["is_valid"]
            assert result["confidence"] == 0.0
            assert "Validator error" in result["validation_errors"][0]

    def test_empty_narrative_handling(self):
        """Test handling of empty narratives."""
        game_state = MockGameState()

        result = game_state.validate_narrative_consistency("")

        assert not result["is_valid"]
        assert result["missing_entities"] == ["Gideon", "Rowan"]

    def test_empty_party_handling(self):
        """Test handling when no party members."""
        game_state = MockGameState()
        game_state.party_members = []

        result = game_state.validate_narrative_consistency("The chamber was silent.")

        # Should be valid (no entities expected)
        assert result["is_valid"]
        assert result["missing_entities"] == []


if __name__ == "__main__":
    unittest.main()
