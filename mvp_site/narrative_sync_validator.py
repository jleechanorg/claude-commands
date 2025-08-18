"""
Narrative Synchronization Validator for Production Entity Tracking
Adapted from Milestone 0.4 prototype for production use in gemini_service.py

REFACTORED: Now delegates to EntityValidator for all entity presence logic.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

import logging_util
from entity_validator import EntityValidator


class EntityPresenceType(Enum):
    """Types of entity presence in narrative"""

    PHYSICALLY_PRESENT = "physically_present"
    MENTIONED_ABSENT = "mentioned_absent"  # Talked about but not there
    IMPLIED_PRESENT = "implied_present"  # Should be there based on context
    AMBIGUOUS = "ambiguous"  # Unclear if present or not


@dataclass
class EntityContext:
    """Context information for an entity in the narrative"""

    name: str
    presence_type: EntityPresenceType
    location: str | None = None
    last_action: str | None = None
    emotional_state: str | None = None
    physical_markers: list[str] | None = None  # e.g., "bandaged ear", "trembling"

    def __post_init__(self):
        if self.physical_markers is None:
            self.physical_markers = []


@dataclass
class ValidationResult:
    """Result of narrative validation"""

    entities_found: list[str] | None = None
    entities_missing: list[str] | None = None
    all_entities_present: bool = False
    confidence: float = 0.0
    warnings: list[str] | None = None
    metadata: dict[str, Any] | None = None
    validation_details: dict[str, Any] | None = None

    def __post_init__(self):
        if self.entities_found is None:
            self.entities_found = []
        if self.entities_missing is None:
            self.entities_missing = []
        if self.warnings is None:
            self.warnings = []
        if self.metadata is None:
            self.metadata = {}
        if self.validation_details is None:
            self.validation_details = {}


class NarrativeSyncValidator:
    """
    Advanced validator specifically designed for preventing narrative desynchronization.
    Delegates entity presence logic to EntityValidator while adding narrative-specific features.
    """

    def __init__(self):
        self.name = "NarrativeSyncValidator"
        self.logger = logging_util.getLogger(self.name)

        # Delegate all entity validation logic to EntityValidator
        self.entity_validator = EntityValidator()

        # Emotional state patterns (kept here as they're narrative-specific)
        self.emotional_patterns = {
            "grief": ["mourning", "grieving", "sorrowful", "bereaved"],
            "anger": ["furious", "enraged", "angry", "wrathful"],
            "fear": ["terrified", "afraid", "fearful", "frightened"],
            "guilt": ["guilty", "ashamed", "remorseful"],
        }

    def _compile_patterns(self):
        """Pre-compile regex patterns for better performance"""
        # Compile physical state patterns
        self._compiled_patterns["physical_states"] = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.physical_state_patterns
        ]

    def _analyze_entity_presence(
        self, narrative: str, entity: str
    ) -> EntityPresenceType:
        """Determine if an entity is physically present or just mentioned"""
        narrative_lower = narrative.lower()
        entity_lower = entity.lower()

        # Check for explicit absence indicators first
        for pattern in self.presence_patterns["absent_reference"]:
            if re.search(pattern.replace(r"(\w+)", entity_lower), narrative_lower):
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
        # This is more appropriate for our use case where entities should be mentioned if present
        if entity_lower in narrative_lower:
            return EntityPresenceType.PHYSICALLY_PRESENT

        # Not found at all
        return None

    def _extract_physical_states(self, narrative: str) -> dict[str, list[str]]:
        """Extract physical state descriptions from narrative"""
        states = {}

        # Use pre-compiled patterns for better performance
        compiled_patterns = self._compiled_patterns.get("physical_states", [])
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

    def _detect_scene_transitions(self, narrative: str) -> list[str]:
        """Detect location transitions in the narrative"""
        transitions = []

        for pattern_list in self.presence_patterns["location_transition"]:
            matches = re.finditer(pattern_list, narrative, re.IGNORECASE)
            for match in matches:
                transitions.append(match.group(0))

        return transitions

    def _check_continuity(
        self, narrative: str, previous_states: dict[str, EntityContext]
    ) -> list[str]:
        """Check for continuity issues with previous states"""
        issues = []

        # Extract current physical states
        self._extract_physical_states(narrative)

        # Check if previously noted physical states are maintained
        for entity, context in previous_states.items():
            if context.physical_markers:
                entity_mentioned = entity.lower() in narrative.lower()
                if entity_mentioned:
                    # Check if physical markers are still referenced
                    for marker in context.physical_markers:
                        if marker not in narrative.lower():
                            issues.append(
                                f"{entity}'s '{marker}' not maintained in narrative"
                            )

        return issues

    def validate(
        self,
        narrative_text: str,
        expected_entities: list[str],
        location: str = None,
        previous_states: dict[str, EntityContext] = None,
        **kwargs,
    ) -> ValidationResult:
        """
        Validate narrative synchronization with advanced presence detection.
        REFACTORED: Now delegates all entity logic to EntityValidator.

        Args:
            narrative_text: The generated narrative
            expected_entities: List of entities that should appear
            location: Current scene location
            previous_states: Previous entity states for continuity checking
        """
        # Delegate all entity validation to EntityValidator
        result = self.entity_validator.validate(
            narrative_text, expected_entities, location, previous_states, **kwargs
        )

        # Add continuity checking (narrative-specific logic)
        if previous_states:
            continuity_issues = self._check_continuity(narrative_text, previous_states)
            result.warnings.extend(continuity_issues)

            # Update metadata
            if result.metadata:
                result.metadata["continuity_issues"] = continuity_issues
                result.metadata["validator_name"] = (
                    self.name
                )  # Override to show delegation
                result.metadata["method"] = "narrative_sync_delegation"

        self.logger.info(
            f"NarrativeSyncValidator delegated to EntityValidator: "
            f"{len(result.found_entities)}/{len(expected_entities)} found"
        )

        return result
