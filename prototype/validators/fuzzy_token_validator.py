"""
Fuzzy token validator with advanced pattern matching.
Handles name variations, partial matches, and complex references.
"""

import re
from typing import List, Dict, Any, Set, Tuple
from difflib import SequenceMatcher

from ..validator import BaseValidator, ValidationResult, EntityManifest
from ..validation_utils import (
    normalize_text, find_entity_mentions, fuzzy_match_entity,
    extract_pronouns, detect_entity_states, check_narrative_coherence,
    merge_entity_references, calculate_string_similarity
)
from ..logging_config import with_metrics, setup_logging


class FuzzyTokenValidator(BaseValidator):
    """
    Advanced token validator with fuzzy matching and pattern recognition.
    """
    
    def __init__(self, fuzzy_threshold: float = 0.8):
        super().__init__("FuzzyTokenValidator")
        self.logger = setup_logging(self.name)
        self.fuzzy_threshold = fuzzy_threshold
        
        # Define name variation patterns
        self.name_patterns = {
            "titles": [
                r"(?:ser|sir|lord|lady|master|mistress)\s+{name}",
                r"{name}\s+(?:the|of)\s+\w+",  # e.g., "Gideon the Bold"
            ],
            "possessive": [
                r"{name}(?:'s|'s|s')",  # Gideon's, Gideons'
            ],
            "partial": [
                r"{name}[—–-]+",  # Cut-off names like "Gid--"
                r"\.{3}\s*{name}",  # "...Gideon"
                r"{name}\s*\.{3}",  # "Gideon..."
            ],
            "informal": [
                r"(?:young|old|little|big)\s+{name}",
                r"{name}(?:y|ie)",  # Nicknames like "Rowey" for Rowan
            ]
        }
        
        # Role-based patterns for common character types
        self.role_patterns = {
            "warrior": ["knight", "warrior", "fighter", "soldier", "guard"],
            "healer": ["healer", "cleric", "priest", "priestess", "medic"],
            "mage": ["wizard", "mage", "sorcerer", "sorceress", "magician"],
            "rogue": ["thief", "rogue", "assassin", "scout", "spy"]
        }
        
    def _generate_name_patterns(self, entity_name: str) -> List[re.Pattern]:
        """Generate regex patterns for name variations."""
        patterns = []
        name_lower = entity_name.lower()
        
        # Add patterns for each variation type
        for pattern_type, pattern_list in self.name_patterns.items():
            for pattern_template in pattern_list:
                # Replace {name} with actual entity name
                pattern = pattern_template.replace("{name}", re.escape(name_lower))
                try:
                    compiled = re.compile(pattern, re.IGNORECASE)
                    patterns.append(compiled)
                except re.error:
                    self.logger.warning(f"Invalid regex pattern: {pattern}")
                    
        return patterns
    
    def _find_role_based_matches(self, text: str, entity_name: str) -> List[Dict]:
        """Find matches based on character roles/classes."""
        matches = []
        text_lower = text.lower()
        
        # Determine likely role based on entity name or known mappings
        likely_role = None
        if entity_name.lower() == "gideon":
            likely_role = "warrior"
        elif entity_name.lower() == "rowan":
            likely_role = "healer"
            
        if likely_role and likely_role in self.role_patterns:
            for role_term in self.role_patterns[likely_role]:
                pattern = re.compile(r'\b' + re.escape(role_term) + r'\b', re.IGNORECASE)
                for match in pattern.finditer(text):
                    matches.append({
                        "text": text[match.start():match.end()],
                        "position": match.start(),
                        "type": "role",
                        "confidence": 0.7  # Lower confidence for role-based matches
                    })
                    
        return matches
    
    def _contextual_pronoun_resolution(self, text: str, pronouns: List[Dict], 
                                      entities: List[str]) -> Dict[str, List[Dict]]:
        """
        Attempt to resolve pronouns to entities based on context.
        """
        resolved_pronouns = {}
        sentences = text.split('.')
        
        for pronoun_info in pronouns:
            pronoun_pos = pronoun_info["position"]
            
            # Find which sentence contains this pronoun
            current_pos = 0
            for sentence in sentences:
                if current_pos <= pronoun_pos < current_pos + len(sentence):
                    # Look for entity mentions in same or previous sentence
                    for entity in entities:
                        if entity.lower() in sentence.lower():
                            if entity not in resolved_pronouns:
                                resolved_pronouns[entity] = []
                            resolved_pronouns[entity].append({
                                **pronoun_info,
                                "confidence": 0.6,
                                "resolution_method": "same_sentence"
                            })
                            break
                    break
                current_pos += len(sentence) + 1
                
        return resolved_pronouns
    
    @with_metrics("FuzzyTokenValidator")
    def validate(self, 
                 narrative_text: str, 
                 expected_entities: List[str],
                 location: str = None,
                 **kwargs) -> ValidationResult:
        """
        Validate using fuzzy matching and advanced patterns.
        """
        result = ValidationResult()
        
        # Create entity manifest
        manifest = EntityManifest(expected_entities, location)
        
        # Track all findings
        entities_found = set()
        entity_references = {}
        all_matches = []
        
        # Search for each expected entity
        for entity in expected_entities:
            entity_matches = []
            
            # 1. Exact and descriptor matches (from base implementation)
            entity_record = next(
                (e for e in manifest.entities if e["name"] == entity), 
                None
            )
            
            if entity_record:
                descriptors = entity_record["descriptors"]
                exact_matches = find_entity_mentions(narrative_text, entity, descriptors)
                entity_matches.extend(exact_matches)
            
            # 2. Name variation patterns
            name_patterns = self._generate_name_patterns(entity)
            for pattern in name_patterns:
                for match in pattern.finditer(narrative_text):
                    entity_matches.append({
                        "text": narrative_text[match.start():match.end()],
                        "position": match.start(),
                        "type": "pattern",
                        "confidence": 0.85
                    })
            
            # 3. Fuzzy string matching
            fuzzy_matches = fuzzy_match_entity(
                narrative_text, entity, self.fuzzy_threshold
            )
            entity_matches.extend(fuzzy_matches)
            
            # 4. Role-based matching
            role_matches = self._find_role_based_matches(narrative_text, entity)
            entity_matches.extend(role_matches)
            
            # Merge and deduplicate matches
            if entity_matches:
                entities_found.add(entity)
                merged_matches = merge_entity_references(entity_matches)
                entity_references[entity] = merged_matches
                all_matches.extend(merged_matches)
        
        # 5. Pronoun resolution
        pronouns = extract_pronouns(narrative_text)
        if pronouns:
            resolved = self._contextual_pronoun_resolution(
                narrative_text, pronouns, list(entities_found)
            )
            
            # Add resolved pronouns to entity references
            for entity, pronoun_refs in resolved.items():
                if entity in entity_references:
                    entity_references[entity].extend(pronoun_refs)
                else:
                    entity_references[entity] = pronoun_refs
                    
            result.metadata["resolved_pronouns"] = len(resolved)
        
        # Detect entity states
        detected_states = detect_entity_states(narrative_text)
        if detected_states:
            result.entity_states = {}
            for entity in entities_found:
                for state, sentences in detected_states.items():
                    for sentence in sentences:
                        if entity.lower() in sentence.lower():
                            if entity not in result.entity_states:
                                result.entity_states[entity] = []
                            result.entity_states[entity].append(state)
        
        # Calculate final results
        coherence = check_narrative_coherence(entities_found, expected_entities)
        result.entities_found = list(entities_found)
        result.entities_missing = coherence["missing_entities"]
        result.all_entities_present = coherence["all_present"]
        
        # Calculate weighted confidence
        if all_matches:
            # Weight by match type
            type_weights = {
                "name": 1.0,
                "descriptor": 0.9,
                "pattern": 0.85,
                "fuzzy": 0.8,
                "role": 0.7,
                "pronoun": 0.6
            }
            
            weighted_sum = sum(
                m.get("confidence", 1.0) * type_weights.get(m.get("type", "name"), 0.5)
                for m in all_matches
            )
            avg_weighted_confidence = weighted_sum / len(all_matches)
            result.confidence = coherence["coverage"] * avg_weighted_confidence
        else:
            result.confidence = 0.0
        
        # Add comprehensive metadata
        result.metadata = {
            "validator_name": self.name,
            "method": "token",
            "variant": "fuzzy",
            "narrative_length": len(narrative_text),
            "fuzzy_threshold": self.fuzzy_threshold,
            "match_types_used": list(set(m.get("type", "unknown") for m in all_matches)),
            "total_matches": len(all_matches),
            "pronoun_count": len(pronouns),
            "coverage": coherence["coverage"]
        }
        
        # Add entity references
        if entity_references:
            result.entity_references = entity_references
        
        # Add validation details
        result.validation_details = {
            "token_matches": [
                {
                    "entity": entity,
                    "matched_text": ref["text"],
                    "match_type": ref.get("type", "unknown"),
                    "score": ref.get("confidence", 1.0),
                    "position": ref.get("position", -1)
                }
                for entity, refs in entity_references.items()
                for ref in refs
            ]
        }
        
        # Add warnings for low confidence matches
        low_confidence_matches = [
            m for m in all_matches 
            if m.get("confidence", 1.0) < 0.7
        ]
        if low_confidence_matches:
            result.warnings.append(
                f"Found {len(low_confidence_matches)} low-confidence matches"
            )
        
        return result