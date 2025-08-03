"""
Hybrid validator combining multiple validation approaches.
Uses both token-based and LLM-based validation for best accuracy.
"""

import statistics

from prototype.logging_config import setup_logging, with_metrics
from prototype.validator import BaseValidator, ValidationResult

from .fuzzy_token_validator import FuzzyTokenValidator
from .llm_validator import LLMValidator
from .token_validator import TokenValidator


class HybridValidator(BaseValidator):
    """
    Combines multiple validators for comprehensive validation.
    """

    def __init__(
        self,
        token_validator: BaseValidator | None = None,
        fuzzy_validator: BaseValidator | None = None,
        llm_validator: BaseValidator | None = None,
        combination_strategy: str = "weighted_vote",
    ):
        """
        Initialize hybrid validator.

        Args:
            token_validator: Token-based validator instance
            fuzzy_validator: Fuzzy matching validator instance
            llm_validator: LLM-based validator instance
            combination_strategy: How to combine results
                ("weighted_vote", "unanimous", "majority", "confidence_based")
        """
        super().__init__("HybridValidator")
        self.logger = setup_logging(self.name)

        # Initialize validators if not provided
        self.validators = {
            "token": token_validator or TokenValidator(),
            "fuzzy": fuzzy_validator or FuzzyTokenValidator(),
            "llm": llm_validator or LLMValidator(),
        }

        self.combination_strategy = combination_strategy

        # Weights for different validators (can be tuned)
        self.validator_weights = {"token": 0.3, "fuzzy": 0.4, "llm": 0.3}

    def _combine_results(
        self, results: dict[str, ValidationResult]
    ) -> ValidationResult:
        """Combine results from multiple validators."""
        if self.combination_strategy == "weighted_vote":
            return self._weighted_vote_combination(results)
        if self.combination_strategy == "unanimous":
            return self._unanimous_combination(results)
        if self.combination_strategy == "majority":
            return self._majority_vote_combination(results)
        if self.combination_strategy == "confidence_based":
            return self._confidence_based_combination(results)
        raise ValueError(f"Unknown combination strategy: {self.combination_strategy}")

    def _weighted_vote_combination(
        self, results: dict[str, ValidationResult]
    ) -> ValidationResult:
        """Combine results using weighted voting."""
        combined = ValidationResult()

        # Track entity votes with weights
        entity_scores = {}  # entity -> score

        # Process each validator's results
        for validator_name, result in results.items():
            weight = self.validator_weights.get(validator_name, 0.33)

            # Add positive votes for found entities
            for entity in result.entities_found:
                if entity not in entity_scores:
                    entity_scores[entity] = 0
                entity_scores[entity] += weight * result.confidence

            # Subtract votes for missing entities
            for entity in result.entities_missing:
                if entity not in entity_scores:
                    entity_scores[entity] = 0
                entity_scores[entity] -= weight * result.confidence

        # Determine final entity status based on scores
        threshold = 0.5  # Entities with score > 0.5 are considered found

        all_mentioned_entities = set()
        for result in results.values():
            all_mentioned_entities.update(result.entities_found)
            all_mentioned_entities.update(result.entities_missing)

        for entity in all_mentioned_entities:
            score = entity_scores.get(entity, 0)
            if score > threshold:
                combined.entities_found.append(entity)
            else:
                combined.entities_missing.append(entity)

        # Calculate combined confidence
        confidences = [r.confidence for r in results.values()]
        weights = [self.validator_weights.get(name, 0.33) for name in results]

        weighted_sum = sum(c * w for c, w in zip(confidences, weights, strict=False))
        total_weight = sum(weights)
        combined.confidence = weighted_sum / total_weight if total_weight > 0 else 0

        # Set all_entities_present
        combined.all_entities_present = len(combined.entities_missing) == 0

        # Combine entity states
        combined.entity_states = self._merge_entity_states(results)

        # Add metadata
        combined.metadata = {
            "validator_name": self.name,
            "method": "hybrid",
            "combination_strategy": self.combination_strategy,
            "validators_used": list(results.keys()),
            "entity_scores": entity_scores,
        }

        return combined

    def _unanimous_combination(
        self, results: dict[str, ValidationResult]
    ) -> ValidationResult:
        """All validators must agree for an entity to be found."""
        combined = ValidationResult()

        # Get entities from first result as baseline
        first_result = next(iter(results.values()))
        all_expected = set(first_result.entities_found + first_result.entities_missing)

        # Check each entity
        for entity in all_expected:
            found_count = sum(1 for r in results.values() if entity in r.entities_found)

            if found_count == len(results):
                # All validators agree entity is present
                combined.entities_found.append(entity)
            else:
                combined.entities_missing.append(entity)

        # Conservative confidence (minimum)
        combined.confidence = min(r.confidence for r in results.values())
        combined.all_entities_present = len(combined.entities_missing) == 0

        # Metadata
        combined.metadata = {
            "validator_name": self.name,
            "method": "hybrid",
            "combination_strategy": self.combination_strategy,
            "validators_used": list(results.keys()),
        }

        return combined

    def _majority_vote_combination(
        self, results: dict[str, ValidationResult]
    ) -> ValidationResult:
        """Simple majority vote for each entity."""
        combined = ValidationResult()

        # Collect all entities
        all_entities = set()
        for result in results.values():
            all_entities.update(result.entities_found)
            all_entities.update(result.entities_missing)

        # Vote on each entity
        for entity in all_entities:
            found_votes = sum(1 for r in results.values() if entity in r.entities_found)
            missing_votes = sum(
                1 for r in results.values() if entity in r.entities_missing
            )

            if found_votes > missing_votes:
                combined.entities_found.append(entity)
            else:
                combined.entities_missing.append(entity)

        # Median confidence
        combined.confidence = statistics.median(r.confidence for r in results.values())
        combined.all_entities_present = len(combined.entities_missing) == 0

        # Metadata
        combined.metadata = {
            "validator_name": self.name,
            "method": "hybrid",
            "combination_strategy": self.combination_strategy,
            "validators_used": list(results.keys()),
        }

        return combined

    def _confidence_based_combination(
        self, results: dict[str, ValidationResult]
    ) -> ValidationResult:
        """Use the result from the most confident validator."""
        # Find most confident result
        most_confident = max(results.items(), key=lambda x: x[1].confidence)
        validator_name, best_result = most_confident

        # Copy the best result
        combined = ValidationResult()
        combined.entities_found = best_result.entities_found.copy()
        combined.entities_missing = best_result.entities_missing.copy()
        combined.confidence = best_result.confidence
        combined.all_entities_present = best_result.all_entities_present
        combined.entity_states = (
            best_result.entity_states.copy() if best_result.entity_states else {}
        )

        # Add hybrid metadata
        combined.metadata = {
            "validator_name": self.name,
            "method": "hybrid",
            "combination_strategy": self.combination_strategy,
            "selected_validator": validator_name,
            "all_confidences": {name: r.confidence for name, r in results.items()},
        }

        return combined

    def _merge_entity_states(
        self, results: dict[str, ValidationResult]
    ) -> dict[str, list[str]]:
        """Merge entity states from multiple validators."""
        merged_states = {}

        for result in results.values():
            if result.entity_states:
                for entity, states in result.entity_states.items():
                    if entity not in merged_states:
                        merged_states[entity] = []
                    merged_states[entity].extend(states)

        # Deduplicate states
        for entity in merged_states:
            merged_states[entity] = list(set(merged_states[entity]))

        return merged_states

    @with_metrics("HybridValidator")
    def validate(
        self,
        narrative_text: str,
        expected_entities: list[str],
        location: str = None,
        **kwargs,
    ) -> ValidationResult:
        """
        Validate using multiple approaches and combine results.
        """
        # Run all validators
        results = {}

        for name, validator in self.validators.items():
            try:
                self.logger.info(f"Running {name} validator...")
                result = validator.validate(
                    narrative_text, expected_entities, location, **kwargs
                )
                results[name] = result
                self.logger.info(
                    f"{name} found: {result.entities_found}, confidence: {result.confidence:.2f}"
                )
            except Exception as e:
                self.logger.error(f"Error in {name} validator: {e}")
                # Continue with other validators

        if not results:
            # All validators failed
            result = ValidationResult()
            result.entities_missing = expected_entities
            result.errors.append("All validators failed")
            return result

        # Combine results
        combined = self._combine_results(results)

        # Add validation details from each validator
        combined.validation_details = {
            "individual_results": {
                name: {
                    "entities_found": result.entities_found,
                    "entities_missing": result.entities_missing,
                    "confidence": result.confidence,
                }
                for name, result in results.items()
            }
        }

        return combined
