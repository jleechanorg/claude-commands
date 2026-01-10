"""
Enhanced Post-Generation Validation with Retry (Option 2 Enhanced)
Validates AI output for missing entities and implements retry logic.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from mvp_site import logging_util

# =============================================================================
# Utility Functions (consolidated from entity_utils.py)
# =============================================================================


def filter_unknown_entities(entities: list[str]) -> list[str]:
    """
    Filter out 'Unknown' entities from a list.

    'Unknown' is used as a default location name when location is not found
    in world_data and should not be treated as a real entity for validation.

    Args:
        entities: List of entity names to filter

    Returns:
        List of entities with 'Unknown' entries removed
    """
    return [e for e in entities if e.lower() != "unknown"]


def is_unknown_entity(entity: str) -> bool:
    """
    Check if an entity is the 'Unknown' placeholder.

    Args:
        entity: Entity name to check

    Returns:
        True if entity is 'Unknown' (case-insensitive), False otherwise
    """
    return entity.lower() == "unknown"


# =============================================================================
# Enums and Data Classes
# =============================================================================


class EntityPresenceType(Enum):
    """Types of entity presence in narrative"""

    PHYSICALLY_PRESENT = "physically_present"
    MENTIONED_ABSENT = "mentioned_absent"  # Talked about but not there
    IMPLIED_PRESENT = "implied_present"  # Should be there based on context
    AMBIGUOUS = "ambiguous"  # Unclear if present or not


@dataclass
class ValidationResult:
    """Result of entity validation - unified format for all validators"""

    passed: bool
    missing_entities: list[str]
    found_entities: list[str]
    confidence_score: float
    retry_needed: bool
    retry_suggestions: list[str]
    # Extended fields for narrative sync compatibility
    entities_found: list[str] = None
    entities_missing: list[str] = None
    all_entities_present: bool = False
    confidence: float = 0.0
    warnings: list[str] = None
    metadata: dict[str, Any] = None
    validation_details: dict[str, Any] = None

    def __post_init__(self):
        # Maintain backward compatibility by syncing fields
        if self.entities_found is None:
            self.entities_found = self.found_entities
        if self.entities_missing is None:
            self.entities_missing = self.missing_entities
        if self.warnings is None:
            self.warnings = []
        if self.metadata is None:
            self.metadata = {}
        if self.validation_details is None:
            self.validation_details = {}
        self.all_entities_present = len(self.missing_entities) == 0
        self.confidence = self.confidence_score


class EntityValidator:
    """
    Enhanced post-generation validator that checks for missing entities
    and provides retry logic for improved entity tracking.
    """

    def __init__(self, min_confidence_threshold: float = 0.7):
        self.min_confidence_threshold = min_confidence_threshold
        self.entity_patterns = self._build_entity_patterns()
        self.name = "EntityValidator"

        # Advanced patterns from NarrativeSyncValidator (consolidated)
        self.presence_patterns = {
            "absent_reference": [
                r"(\w+), who was not there",
                r"the absent (\w+)",
                r"(\w+) remained at",
                r"(\w+) was still in",
                r"thinking of (\w+)",
            ],
            "location_transition": [
                r"moved to (.+)",
                r"arrived at (.+)",
                r"found (?:yourself|themselves) in (.+)",
                r"now in (.+)",
            ],
        }

        # Physical state patterns
        self.physical_state_patterns = [
            r"bandaged (\w+)",
            r"trembling (\w+)?",
            r"tear[- ]?stained",
            r"wounded (\w+)",
            r"bloodied (\w+)",
            r"exhausted",
        ]

        # Pre-compile regex patterns for better performance
        self._compiled_patterns: dict[str, list[re.Pattern[str]]] = {}
        self._compile_patterns()

    def _build_entity_patterns(self) -> dict[str, list[str]]:
        """Build regex patterns for entity detection"""
        return {
            "direct_mention": [
                r"\b{entity}\b",  # Direct name mention
                r"\b{entity}(?:\'s|\s+says|\s+does|\s+is|\s+was)",  # Possessive or action
            ],
            "pronoun_reference": [
                r"(?:he|she|they|him|her|them)\b",  # Pronoun references
            ],
            "role_reference": [
                r"\b(?:the\s+)?(?:guard|captain|magister|lady|lord|advisor|scholar)\b",
            ],
            "action_attribution": [
                r"(?:says|speaks|responds|nods|smiles|frowns|looks|turns)",
            ],
        }

    def _compile_patterns(self):
        """Pre-compile regex patterns for better performance"""
        # Compile physical state patterns
        self._compiled_patterns["physical_states"] = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.physical_state_patterns
        ]

        # Compile presence patterns for better performance
        self._compiled_patterns["absent_reference"] = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.presence_patterns["absent_reference"]
        ]
        self._compiled_patterns["location_transition"] = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.presence_patterns["location_transition"]
        ]

    def analyze_entity_presence(
        self, narrative: str, entity: str
    ) -> EntityPresenceType:
        """Determine if an entity is physically present or just mentioned (consolidated from NarrativeSyncValidator)"""
        narrative_lower = narrative.lower()
        entity_lower = entity.lower()

        # Check for explicit absence indicators first (using compiled patterns)
        compiled_absent_patterns: list[re.Pattern[str]] = self._compiled_patterns.get(
            "absent_reference", []
        )
        for pattern in compiled_absent_patterns:
            pattern_str = pattern.pattern.replace(r"(\w+)", entity_lower)
            if re.search(pattern_str, narrative_lower, re.IGNORECASE):
                return EntityPresenceType.MENTIONED_ABSENT

        # Check if only mentioned in dialogue or thoughts
        thought_patterns = [
            f"thought of {entity_lower}",
            f"remembered {entity_lower}",
            f"thinking of {entity_lower}",
            f"spoke of {entity_lower}",
        ]

        for pattern in thought_patterns:
            if pattern in narrative_lower:
                return EntityPresenceType.MENTIONED_ABSENT

        # If entity is mentioned in narrative, assume physically present unless proven otherwise
        if entity_lower in narrative_lower:
            return EntityPresenceType.PHYSICALLY_PRESENT

        # Not found at all
        return None

    def extract_physical_states(self, narrative: str) -> dict[str, list[str]]:
        """Extract physical state descriptions from narrative (consolidated from NarrativeSyncValidator)"""
        states: dict[str, list[str]] = {}

        # Use pre-compiled patterns for better performance
        compiled_patterns: list[re.Pattern[str]] = self._compiled_patterns.get(
            "physical_states", []
        )
        for pattern in compiled_patterns:
            matches = pattern.finditer(narrative)
            for match in matches:
                state = match.group(0)
                # Try to associate with nearby entity names
                context = narrative[
                    max(0, match.start() - 50) : min(len(narrative), match.end() + 50)
                ]

                # Simple heuristic: look for capitalized words nearby
                entities = re.findall(r"\b[A-Z][a-z]+\b", context)
                for entity in entities:
                    if entity not in states:
                        states[entity] = []
                    states[entity].append(state)

        return states

    def detect_scene_transitions(self, narrative: str) -> list[str]:
        """Detect location transitions in the narrative (consolidated from NarrativeSyncValidator)"""
        transitions = []

        # Use compiled patterns for better performance
        compiled_transition_patterns: list[re.Pattern[str]] = (
            self._compiled_patterns.get("location_transition", [])
        )
        for pattern in compiled_transition_patterns:
            matches = pattern.finditer(narrative)
            for match in matches:
                transitions.append(match.group(0))

        return transitions

    def create_injection_templates(
        self, missing_entities: list[str], context: dict[str, Any] = None
    ) -> dict[str, list[str]]:
        """Create entity injection templates (consolidated from DualPassGenerator)"""
        templates = {}

        # Generic templates that work for any campaign
        generic_templates = [
            "{entity}, who had been present but silent, {action}.",
            "Nearby, {entity} {action}, adding their perspective to the scene.",
            "{entity} steps forward and {action}.",
            "{entity}'s voice cuts through: '{dialogue}'",
            "From across the room, {entity} {action}.",
            "{entity} looks up from their position and {action}.",
        ]

        for entity in missing_entities:
            templates[entity] = generic_templates

        return templates

    def validate_entity_presence(
        self,
        narrative_text: str,
        expected_entities: list[str],
        location: Optional[str] = None,
    ) -> ValidationResult:
        """
        Validate that expected entities are present in the narrative.
        Returns detailed validation result with retry suggestions.
        """
        # Filter out 'Unknown' from expected entities - it's not a real entity
        expected_entities = filter_unknown_entities(expected_entities)

        found_entities = []
        missing_entities = []
        confidence_scores = {}

        for entity in expected_entities:
            entity_score = self._calculate_entity_presence_score(narrative_text, entity)
            confidence_scores[entity] = entity_score

            if entity_score > self.min_confidence_threshold:
                found_entities.append(entity)
            else:
                missing_entities.append(entity)

        # Calculate overall confidence
        if expected_entities:
            overall_confidence = sum(confidence_scores.values()) / len(
                expected_entities
            )
        else:
            overall_confidence = 1.0

        # Determine if retry is needed
        retry_needed = (
            len(missing_entities) > 0
            or overall_confidence < self.min_confidence_threshold
        )

        # Generate retry suggestions
        retry_suggestions = self._generate_retry_suggestions(
            missing_entities, found_entities, narrative_text, location
        )

        result = ValidationResult(
            passed=not retry_needed,
            missing_entities=missing_entities,
            found_entities=found_entities,
            confidence_score=overall_confidence,
            retry_needed=retry_needed,
            retry_suggestions=retry_suggestions,
        )

        logging_util.info(
            f"Entity validation: {len(found_entities)}/{len(expected_entities)} found, "
            f"confidence: {overall_confidence:.2f}"
        )

        return result

    def _calculate_entity_presence_score(
        self, narrative_text: str, entity: str
    ) -> float:
        """Calculate confidence score for entity presence in narrative"""
        narrative_lower = narrative_text.lower()
        entity_lower = entity.lower()
        score = 0.0

        # Direct name mention (highest score)
        if entity_lower in narrative_lower:
            score += 0.8

            # Bonus for multiple mentions
            mentions = narrative_lower.count(entity_lower)
            score += min(mentions * 0.1, 0.2)

        # Check for partial name matches (for compound names)
        entity_parts = entity_lower.split()
        if len(entity_parts) > 1:
            partial_matches = sum(1 for part in entity_parts if part in narrative_lower)
            if partial_matches > 0:
                score += (partial_matches / len(entity_parts)) * 0.5

        # Action attribution patterns
        action_patterns = [
            rf"{re.escape(entity_lower)}\s+(?:says|speaks|responds|does|is|was)",
            rf"(?:says|speaks|responds)\s+{re.escape(entity_lower)}",
            rf"{re.escape(entity_lower)}\'s\s+(?:voice|words|response)",
        ]

        for pattern in action_patterns:
            if re.search(pattern, narrative_lower):
                score += 0.3
                break

        # Pronoun references (lower confidence, need context)
        if entity_lower in narrative_lower:
            pronouns = ["he", "she", "they", "him", "her", "them"]
            pronoun_count = sum(narrative_lower.count(pronoun) for pronoun in pronouns)
            if pronoun_count > 0:
                score += min(pronoun_count * 0.05, 0.15)

        return min(score, 1.0)

    def _generate_retry_suggestions(
        self,
        missing_entities: list[str],
        found_entities: list[str],
        narrative_text: str,
        location: Optional[str] = None,
    ) -> list[str]:
        """Generate specific suggestions for retry prompts"""
        suggestions: list[str] = []

        if not missing_entities:
            return suggestions

        # Generic suggestions for missing entities
        for entity in missing_entities:
            suggestions.append(
                f"Include {entity} in the scene with dialogue, actions, or reactions"
            )

        # Generic location-based suggestions
        if location and missing_entities:
            suggestions.append(
                f"Ensure the missing characters fit naturally in {location}"
            )

        # General narrative suggestions
        if len(missing_entities) > len(found_entities):
            suggestions.append(
                "Ensure all characters present in the scene have some role or mention"
            )

        if len(missing_entities) >= 2:
            suggestions.append(
                "Consider adding dialogue between the missing characters"
            )

        return suggestions

    def create_retry_prompt(
        self,
        original_prompt: str,
        validation_result: ValidationResult,
        location: Optional[str] = None,
    ) -> str:
        """Create an enhanced prompt for retry when entities are missing"""
        if not validation_result.retry_needed:
            return original_prompt

        retry_instructions = []

        # Missing entity instructions
        if validation_result.missing_entities:
            entity_list = ", ".join(validation_result.missing_entities)
            retry_instructions.append(
                f"IMPORTANT: The following characters are missing from your response and MUST be included: {entity_list}"
            )

        # Specific suggestions
        if validation_result.retry_suggestions:
            retry_instructions.append("Specific requirements:")
            for suggestion in validation_result.retry_suggestions:
                retry_instructions.append(f"- {suggestion}")

        # Location context
        if location:
            retry_instructions.append(
                f"Setting: {location} - ensure all characters appropriate to this location are present"
            )

        # Combine instructions
        retry_text = "\n".join(retry_instructions)
        return f"{original_prompt}\n\n=== RETRY INSTRUCTIONS ===\n{retry_text}\n\nPlease revise your response to include all required characters."

    def validate(
        self,
        narrative_text: str,
        expected_entities: list[str],
        location: Optional[str] = None,
        previous_states: Optional[dict[str, Any]] = None,
        **kwargs,
    ) -> ValidationResult:
        """
        Comprehensive validation method that supports both EntityValidator and NarrativeSyncValidator interfaces.
        This method consolidates all validation logic in one place.
        """
        # Filter out 'Unknown' from expected entities - it's not a real entity
        expected_entities = filter_unknown_entities(expected_entities)

        # Analyze each entity's presence type using advanced detection
        entity_analysis = {}
        physically_present = []
        mentioned_absent = []
        ambiguous = []
        missing = []

        for entity in expected_entities:
            presence = self.analyze_entity_presence(narrative_text, entity)

            if presence == EntityPresenceType.PHYSICALLY_PRESENT:
                physically_present.append(entity)
                entity_analysis[entity] = "present"
            elif presence == EntityPresenceType.MENTIONED_ABSENT:
                mentioned_absent.append(entity)
                entity_analysis[entity] = "mentioned_absent"
            elif presence == EntityPresenceType.AMBIGUOUS:
                ambiguous.append(entity)
                entity_analysis[entity] = "ambiguous"
            else:
                missing.append(entity)
                entity_analysis[entity] = "missing"

        # Extract additional narrative features
        physical_states = self.extract_physical_states(narrative_text)
        transitions = self.detect_scene_transitions(narrative_text)

        # Calculate overall confidence
        total_entities = len(expected_entities)
        if total_entities > 0:
            clear_entities = len(physically_present) + len(mentioned_absent)
            confidence = clear_entities / total_entities

            # Reduce confidence for ambiguous entities
            if ambiguous:
                confidence *= 1 - 0.1 * len(ambiguous)
        else:
            confidence = 1.0

        # Generate retry suggestions
        retry_suggestions = self._generate_retry_suggestions(
            missing, physically_present + mentioned_absent, narrative_text, location
        )

        # Create warnings
        warnings = []
        if ambiguous:
            for entity in ambiguous:
                warnings.append(
                    f"⚠️ {entity}'s presence is ambiguous - unclear if physically present"
                )

        # Note: Entity transition validation is now handled by enhanced system instructions
        # that guide narrative generation to naturally include character movement descriptions
        # This removes brittle string matching in favor of semantic understanding

        if len(mentioned_absent) > len(physically_present):
            warnings.append(
                "⚠️ More entities mentioned as absent than physically present - possible scene confusion"
            )

        # Build comprehensive result
        result = ValidationResult(
            # EntityValidator interface
            passed=len(missing) == 0,
            missing_entities=missing,
            found_entities=physically_present + mentioned_absent,
            confidence_score=confidence,
            retry_needed=len(missing) > 0,
            retry_suggestions=retry_suggestions,
            # NarrativeSyncValidator interface (automatically synced in __post_init__)
            warnings=warnings,
            metadata={
                "validator_name": self.name,
                "method": "comprehensive_validation",
                "narrative_length": len(narrative_text),
                "entity_analysis": entity_analysis,
                "physically_present": physically_present,
                "mentioned_absent": mentioned_absent,
                "ambiguous": ambiguous,
                "missing": missing,
                "physical_states": physical_states,
                "scene_transitions": transitions,
            },
            validation_details={
                "presence_analysis": [
                    {
                        "entity": entity,
                        "presence_type": entity_analysis.get(entity, "not_found"),
                        "physical_states": physical_states.get(entity, []),
                    }
                    for entity in expected_entities
                ],
                "narrative_features": {
                    "has_transitions": len(transitions) > 0,
                    "clear_presence_indicators": len(ambiguous) == 0,
                },
            },
        )

        logging_util.info(
            f"Comprehensive validation: {len(result.found_entities)}/{len(expected_entities)} found, "
            f"confidence: {confidence:.2f}, warnings: {len(warnings)}"
        )

        return result


class EntityRetryManager:
    """
    Manages retry logic for entity validation failures.
    Implements smart retry strategies to improve entity tracking.
    """

    def __init__(self, max_retries: int = 2):
        self.max_retries = max_retries
        self.validator = EntityValidator()
        self.retry_history: dict[str, int] = {}

    def validate_with_retry(
        self,
        narrative_text: str,
        expected_entities: list[str],
        location: Optional[str] = None,
        retry_callback: Optional[Callable] = None,
    ) -> tuple[ValidationResult, int]:
        """
        Validate entity presence with automatic retry logic.

        Args:
            narrative_text: The AI-generated narrative
            expected_entities: List of entities that should be present
            location: Current scene location
            retry_callback: Function to call for regeneration (narrative_generator)

        Returns:
            Tuple of (final_validation_result, retry_attempts_used)
        """
        validation_result = self.validator.validate_entity_presence(
            narrative_text, expected_entities, location
        )

        retry_attempts = 0
        current_narrative = narrative_text

        # Retry loop
        while (
            validation_result.retry_needed
            and retry_attempts < self.max_retries
            and retry_callback is not None
        ):
            retry_attempts += 1
            logging_util.info(
                f"Entity validation failed, attempting retry {retry_attempts}/{self.max_retries}"
            )

            # Create retry prompt
            retry_prompt = self.validator.create_retry_prompt(
                "Please revise the narrative to include all required characters",
                validation_result,
                location,
            )

            # Call retry callback to regenerate narrative
            try:
                current_narrative = retry_callback(
                    retry_prompt, missing_entities=validation_result.missing_entities
                )

                # Validate the new narrative
                validation_result = self.validator.validate_entity_presence(
                    current_narrative, expected_entities, location
                )

                logging_util.info(
                    f"Retry {retry_attempts} result: {len(validation_result.found_entities)}/{len(expected_entities)} entities found"
                )

            except Exception as e:
                logging_util.error(f"Retry {retry_attempts} failed with error: {e}")
                break

        # Log final result
        if validation_result.passed:
            logging_util.info(
                f"Entity validation passed after {retry_attempts} retries"
            )
        else:
            logging_util.warning(
                f"Entity validation failed after {retry_attempts} retries. Missing: {validation_result.missing_entities}"
            )

        return validation_result, retry_attempts

    def get_retry_statistics(self) -> dict[str, Any]:
        """Get statistics about retry performance"""
        # This could be expanded to track retry success rates over time
        return {
            "max_retries_configured": self.max_retries,
            "validator_threshold": self.validator.min_confidence_threshold,
        }


# Global instances
entity_validator = EntityValidator()
entity_retry_manager = EntityRetryManager()
