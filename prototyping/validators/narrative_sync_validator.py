"""
Narrative Synchronization Validator for Milestone 0.4
Specifically designed to detect and prevent entity desynchronization in narratives.
"""

import os
import re
import sys
from dataclasses import dataclass
from enum import Enum

try:
    from prototype.logging_config import setup_logging, with_metrics
    from prototype.validation_utils import find_entity_mentions, normalize_text
    from prototype.validator import BaseValidator, ValidationResult
except ImportError:
    # Handle both relative and absolute imports
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from logging_config import setup_logging, with_metrics
    from validator import BaseValidator, ValidationResult


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
    physical_markers: list[str] = None  # e.g., "bandaged ear", "trembling"

    def __post_init__(self):
        if self.physical_markers is None:
            self.physical_markers = []


class NarrativeSyncValidator(BaseValidator):
    """
    Advanced validator specifically designed for preventing narrative desynchronization.
    Addresses issues found in both mock campaigns and real Sariel campaign.
    """

    def __init__(self):
        super().__init__("NarrativeSyncValidator")
        self.logger = setup_logging(self.name)

        # Patterns for detecting presence indicators
        self.presence_patterns = {
            "entry": [
                r"(\w+) entered",
                r"(\w+) walked in",
                r"(\w+) arrived",
                r"(\w+) joined",
                r"(\w+) appeared",
            ],
            "exit": [
                r"(\w+) left",
                r"(\w+) departed",
                r"(\w+) walked out",
                r"(\w+) disappeared",
                r"(\w+) vanished",
            ],
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

        # Emotional state patterns
        self.emotional_patterns = {
            "grief": ["mourning", "grieving", "sorrowful", "bereaved"],
            "anger": ["furious", "enraged", "angry", "wrathful"],
            "fear": ["terrified", "afraid", "fearful", "frightened"],
            "guilt": ["guilty", "ashamed", "remorseful"],
        }

    def _analyze_entity_presence(
        self, narrative: str, entity: str
    ) -> EntityPresenceType:
        """Determine if an entity is physically present or just mentioned"""
        narrative_lower = narrative.lower()
        entity_lower = entity.lower()

        # Check for explicit absence indicators
        for pattern in self.presence_patterns["absent_reference"]:
            if re.search(pattern.replace(r"(\w+)", entity_lower), narrative_lower):
                return EntityPresenceType.MENTIONED_ABSENT

        # Check for entry (suggests now present)
        for pattern in self.presence_patterns["entry"]:
            if re.search(pattern.replace(r"(\w+)", entity_lower), narrative_lower):
                return EntityPresenceType.PHYSICALLY_PRESENT

        # Check for direct actions (suggests present)
        action_patterns = [
            f"{entity_lower} said",
            f"{entity_lower} looked",
            f"{entity_lower} moved",
            f"{entity_lower} reached",
        ]

        for pattern in action_patterns:
            if pattern in narrative_lower:
                return EntityPresenceType.PHYSICALLY_PRESENT

        # Check if only mentioned in dialogue or thoughts
        thought_patterns = [
            f"thought of {entity_lower}",
            f"remembered {entity_lower}",
            f"about {entity_lower}",
        ]

        for pattern in thought_patterns:
            if pattern in narrative_lower:
                return EntityPresenceType.MENTIONED_ABSENT

        # If mentioned but no clear indicators
        if entity_lower in narrative_lower:
            return EntityPresenceType.AMBIGUOUS

        # Not found at all
        return None

    def _extract_physical_states(self, narrative: str) -> dict[str, list[str]]:
        """Extract physical state descriptions from narrative"""
        states = {}

        for pattern in self.physical_state_patterns:
            matches = re.finditer(pattern, narrative, re.IGNORECASE)
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

    @with_metrics("NarrativeSyncValidator")
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

        Args:
            narrative_text: The generated narrative
            expected_entities: List of entities that should appear
            location: Current scene location
            previous_states: Previous entity states for continuity checking
        """
        result = ValidationResult()

        # Analyze each entity's presence type
        entity_analysis = {}
        physically_present = []
        mentioned_absent = []
        ambiguous = []
        missing = []

        for entity in expected_entities:
            presence = self._analyze_entity_presence(narrative_text, entity)

            if presence == EntityPresenceType.PHYSICALLY_PRESENT:
                physically_present.append(entity)
                entity_analysis[entity] = "present"
            elif presence == EntityPresenceType.MENTIONED_ABSENT:
                mentioned_absent.append(entity)
                entity_analysis[entity] = "mentioned_absent"
            elif presence == EntityPresenceType.AMBIGUOUS:
                ambiguous.append(entity)
                entity_analysis[entity] = "ambiguous"
                result.warnings.append(
                    f"{entity}'s presence is ambiguous - unclear if physically present"
                )
            else:
                missing.append(entity)
                entity_analysis[entity] = "missing"

        # Extract physical states
        physical_states = self._extract_physical_states(narrative_text)

        # Detect scene transitions
        transitions = self._detect_scene_transitions(narrative_text)

        # Check continuity if previous states provided
        continuity_issues = []
        if previous_states:
            continuity_issues = self._check_continuity(narrative_text, previous_states)
            result.warnings.extend(continuity_issues)

        # Calculate results
        result.entities_found = physically_present + mentioned_absent
        result.entities_missing = missing
        result.all_entities_present = len(missing) == 0 and len(ambiguous) == 0

        # Calculate confidence based on clarity
        total_entities = len(expected_entities)
        if total_entities > 0:
            clear_entities = len(physically_present) + len(mentioned_absent)
            result.confidence = clear_entities / total_entities

            # Reduce confidence for ambiguous entities
            if ambiguous:
                result.confidence *= 1 - 0.1 * len(ambiguous)
        else:
            result.confidence = 1.0

        # Add detailed metadata
        result.metadata = {
            "validator_name": self.name,
            "method": "narrative_sync",
            "narrative_length": len(narrative_text),
            "entity_analysis": entity_analysis,
            "physically_present": physically_present,
            "mentioned_absent": mentioned_absent,
            "ambiguous": ambiguous,
            "missing": missing,
            "physical_states": physical_states,
            "scene_transitions": transitions,
            "continuity_issues": continuity_issues,
        }

        # Add specific warnings for common issues
        if len(transitions) > 0 and not any(
            trans
            for trans in transitions
            if any(ent.lower() in trans.lower() for ent in expected_entities)
        ):
            result.warnings.append(
                "Scene transition detected but no character movement described"
            )

        if len(mentioned_absent) > len(physically_present):
            result.warnings.append(
                "More entities mentioned as absent than physically present - possible scene confusion"
            )

        # Add validation details
        result.validation_details = {
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
                "maintains_continuity": len(continuity_issues) == 0,
                "clear_presence_indicators": len(ambiguous) == 0,
            },
        }

        return result
