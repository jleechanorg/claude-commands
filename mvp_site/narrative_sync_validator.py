"""
Narrative Synchronization Validator for Production Entity Tracking
Adapted from Milestone 0.4 prototype for production use in gemini_service.py
"""

import re
import logging
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


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
    location: Optional[str] = None
    last_action: Optional[str] = None
    emotional_state: Optional[str] = None
    physical_markers: List[str] = None  # e.g., "bandaged ear", "trembling"
    
    def __post_init__(self):
        if self.physical_markers is None:
            self.physical_markers = []


@dataclass
class ValidationResult:
    """Result of narrative validation"""
    entities_found: List[str] = None
    entities_missing: List[str] = None
    all_entities_present: bool = False
    confidence: float = 0.0
    warnings: List[str] = None
    metadata: Dict[str, Any] = None
    validation_details: Dict[str, Any] = None
    
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
    Production version adapted from Milestone 0.4 prototype.
    """
    
    def __init__(self):
        self.name = "NarrativeSyncValidator"
        self.logger = logging.getLogger(self.name)
        
        # Patterns for detecting presence indicators
        self.presence_patterns = {
            "entry": [
                r"(\w+) entered",
                r"(\w+) walked in",
                r"(\w+) arrived",
                r"(\w+) joined",
                r"(\w+) appeared"
            ],
            "exit": [
                r"(\w+) left",
                r"(\w+) departed",
                r"(\w+) walked out",
                r"(\w+) disappeared",
                r"(\w+) vanished"
            ],
            "absent_reference": [
                r"(\w+), who was not there",
                r"the absent (\w+)",
                r"(\w+) remained at",
                r"(\w+) was still in",
                r"thinking of (\w+)"
            ],
            "location_transition": [
                r"moved to (.+)",
                r"arrived at (.+)",
                r"found (?:yourself|themselves) in (.+)",
                r"now in (.+)"
            ]
        }
        
        # Physical state patterns
        self.physical_state_patterns = [
            r"bandaged (\w+)",
            r"trembling (\w+)?",
            r"tear[- ]?stained",
            r"wounded (\w+)",
            r"bloodied (\w+)",
            r"exhausted"
        ]
        
        # Emotional state patterns
        self.emotional_patterns = {
            "grief": ["mourning", "grieving", "sorrowful", "bereaved"],
            "anger": ["furious", "enraged", "angry", "wrathful"],
            "fear": ["terrified", "afraid", "fearful", "frightened"],
            "guilt": ["guilty", "ashamed", "remorseful"]
        }
        
        # Pre-compile regex patterns for better performance
        self._compiled_patterns = {}
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Pre-compile regex patterns for better performance"""
        # Compile physical state patterns
        self._compiled_patterns['physical_states'] = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.physical_state_patterns
        ]
    
    def _analyze_entity_presence(self, narrative: str, entity: str) -> EntityPresenceType:
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
            f"spoke of {entity_lower}"
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
    
    def _extract_physical_states(self, narrative: str) -> Dict[str, List[str]]:
        """Extract physical state descriptions from narrative"""
        states = {}
        
        # Use pre-compiled patterns for better performance
        compiled_patterns = self._compiled_patterns.get('physical_states', [])
        for pattern in compiled_patterns:
            matches = pattern.finditer(narrative)
            for match in matches:
                state = match.group(0)
                # Try to associate with nearby entity names
                context = narrative[max(0, match.start()-50):min(len(narrative), match.end()+50)]
                
                # Simple heuristic: look for capitalized words nearby
                entities = re.findall(r'\b[A-Z][a-z]+\b', context)
                for entity in entities:
                    if entity not in states:
                        states[entity] = []
                    states[entity].append(state)
        
        return states
    
    def _detect_scene_transitions(self, narrative: str) -> List[str]:
        """Detect location transitions in the narrative"""
        transitions = []
        
        for pattern_list in self.presence_patterns["location_transition"]:
            matches = re.finditer(pattern_list, narrative, re.IGNORECASE)
            for match in matches:
                transitions.append(match.group(0))
        
        return transitions
    
    def _check_continuity(self, 
                         narrative: str,
                         previous_states: Dict[str, EntityContext]) -> List[str]:
        """Check for continuity issues with previous states"""
        issues = []
        
        # Extract current physical states
        current_physical = self._extract_physical_states(narrative)
        
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
    
    def validate(self, 
                 narrative_text: str, 
                 expected_entities: List[str],
                 location: str = None,
                 previous_states: Dict[str, EntityContext] = None,
                 **kwargs) -> ValidationResult:
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
                    f"⚠️ {entity}'s presence is ambiguous - unclear if physically present"
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
        # For entity tracking purposes, we just need entities to be acknowledged (present OR absent mention is fine)
        # Only missing entities are a problem
        result.all_entities_present = len(missing) == 0
        
        # Calculate confidence based on clarity
        total_entities = len(expected_entities)
        if total_entities > 0:
            clear_entities = len(physically_present) + len(mentioned_absent)
            result.confidence = clear_entities / total_entities
            
            # Reduce confidence for ambiguous entities
            if ambiguous:
                result.confidence *= (1 - 0.1 * len(ambiguous))
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
            "continuity_issues": continuity_issues
        }
        
        # Add specific warnings for common issues
        if len(transitions) > 0 and not any(
            trans for trans in transitions 
            if any(ent.lower() in trans.lower() for ent in expected_entities)
        ):
            result.warnings.append(
                "⚠️ Scene transition detected but no character movement described"
            )
        
        if len(mentioned_absent) > len(physically_present):
            result.warnings.append(
                "⚠️ More entities mentioned as absent than physically present - possible scene confusion"
            )
        
        # Add validation details
        result.validation_details = {
            "presence_analysis": [
                {
                    "entity": entity,
                    "presence_type": entity_analysis.get(entity, "not_found"),
                    "physical_states": physical_states.get(entity, [])
                }
                for entity in expected_entities
            ],
            "narrative_features": {
                "has_transitions": len(transitions) > 0,
                "maintains_continuity": len(continuity_issues) == 0,
                "clear_presence_indicators": len(ambiguous) == 0
            }
        }
        
        return result