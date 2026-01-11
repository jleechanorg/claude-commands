"""
Narrative Synchronization Validator for Production Entity Tracking
Adapted from Milestone 0.4 prototype for production use in llm_service.py

REFACTORED: Now delegates to EntityValidator for all entity presence logic.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from mvp_site import logging_util
from mvp_site.entity_validator import EntityValidator


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

        # Delegate all entity validation logic to EntityValidator
        self.entity_validator = EntityValidator()

        # Emotional state patterns (kept here as they're narrative-specific)
        self.emotional_patterns = {
            "grief": ["mourning", "grieving", "sorrowful", "bereaved"],
            "anger": ["furious", "enraged", "angry", "wrathful"],
            "fear": ["terrified", "afraid", "fearful", "frightened"],
            "guilt": ["guilty", "ashamed", "remorseful"],
        }

    def _check_continuity(
        self, narrative: str, previous_states: dict[str, EntityContext]
    ) -> list[str]:
        """Check for continuity issues with previous states"""
        issues = []

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
        location: str | None = None,
        previous_states: dict[str, EntityContext] | None = None,
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

        logging_util.info(
            f"NarrativeSyncValidator delegated to EntityValidator: "
            f"{len(result.found_entities)}/{len(expected_entities)} found"
        )

        return result
