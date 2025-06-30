"""
Token-based validator implementation.
Uses string matching techniques to detect entity presence in narratives.
"""

import re
from typing import List, Dict, Any, Set

from ..validator import BaseValidator, ValidationResult, EntityManifest
from ..validation_utils import (
    normalize_text, find_entity_mentions, extract_pronouns,
    detect_entity_states, check_narrative_coherence, merge_entity_references
)
from ..logging_config import with_metrics, setup_logging


class SimpleTokenValidator(BaseValidator):
    """
    Simple token-based validator using basic string matching.
    This is the simplest implementation with exact name matching only.
    """
    
    def __init__(self):
        super().__init__("SimpleTokenValidator")
        self.logger = setup_logging(self.name)
        
    @with_metrics("SimpleTokenValidator")
    def validate(self, 
                 narrative_text: str, 
                 expected_entities: List[str],
                 location: str = None,
                 **kwargs) -> ValidationResult:
        """
        Validate using simple string matching for entity names.
        """
        result = ValidationResult()
        
        # Normalize narrative for searching
        normalized_narrative = normalize_text(narrative_text)
        
        # Track found entities
        entities_found = set()
        entity_references = {}
        
        # Search for each expected entity
        for entity in expected_entities:
            # Simple case-insensitive search
            entity_lower = entity.lower()
            
            # Check if entity name appears in narrative with word boundaries
            # Use word boundary regex to avoid partial matches
            pattern = r'\b' + re.escape(entity_lower) + r'\b'
            if re.search(pattern, normalized_narrative):
                entities_found.add(entity)
                
                # Find all mentions
                mentions = find_entity_mentions(narrative_text, entity)
                if mentions:
                    entity_references[entity] = mentions
                    
        # Calculate results
        result.entities_found = list(entities_found)
        result.entities_missing = [e for e in expected_entities if e not in entities_found]
        result.all_entities_present = len(result.entities_missing) == 0
        
        # Simple confidence based on exact matches
        if expected_entities:
            result.confidence = len(entities_found) / len(expected_entities)
        else:
            result.confidence = 1.0
            
        # Add metadata
        result.metadata = {
            "validator_name": self.name,
            "method": "token",
            "narrative_length": len(narrative_text),
            "matching_type": "exact_name_only"
        }
        
        # Add warnings for edge cases
        if len(narrative_text) < 50:
            result.warnings.append("Very short narrative - results may be unreliable")
            
        return result


class TokenValidator(BaseValidator):
    """
    Enhanced token-based validator with descriptor matching and fuzzy search.
    """
    
    def __init__(self, enable_fuzzy: bool = False, fuzzy_threshold: float = 0.85):
        super().__init__("TokenValidator")
        self.logger = setup_logging(self.name)
        self.enable_fuzzy = enable_fuzzy
        self.fuzzy_threshold = fuzzy_threshold
        
    @with_metrics("TokenValidator")
    def validate(self, 
                 narrative_text: str, 
                 expected_entities: List[str],
                 location: str = None,
                 **kwargs) -> ValidationResult:
        """
        Validate using advanced token matching with descriptors.
        """
        result = ValidationResult()
        
        # Create entity manifest for descriptor lookup
        manifest = EntityManifest(expected_entities, location)
        descriptor_map = manifest.get_all_descriptors()
        
        # Track findings
        entities_found = set()
        entity_references = {}
        all_mentions = []
        
        # Search for each expected entity
        for entity in expected_entities:
            entity_mentions = []
            
            # Get descriptors for this entity
            entity_record = next(
                (e for e in manifest.entities if e["name"] == entity), 
                None
            )
            
            if entity_record:
                descriptors = entity_record["descriptors"]
                
                # Find mentions using name and descriptors
                mentions = find_entity_mentions(
                    narrative_text, entity, descriptors
                )
                
                if mentions:
                    entities_found.add(entity)
                    entity_mentions.extend(mentions)
                    all_mentions.extend(mentions)
            
            # Store references if found
            if entity_mentions:
                entity_references[entity] = merge_entity_references(entity_mentions)
        
        # Check for pronouns (informational only)
        pronouns = extract_pronouns(narrative_text)
        if pronouns and len(entities_found) < len(expected_entities):
            result.warnings.append(
                f"Found {len(pronouns)} pronouns that might refer to missing entities"
            )
        
        # Detect entity states
        detected_states = detect_entity_states(narrative_text)
        if detected_states:
            result.metadata["detected_states"] = detected_states
            
            # Map states to entities if possible
            entity_states = {}
            for state, sentences in detected_states.items():
                for entity in entities_found:
                    for sentence in sentences:
                        if entity.lower() in sentence.lower():
                            if entity not in entity_states:
                                entity_states[entity] = []
                            entity_states[entity].append(state)
            
            if entity_states:
                # Remove duplicates
                for entity in entity_states:
                    entity_states[entity] = list(set(entity_states[entity]))
                    
                result.entity_states = entity_states
        
        # Calculate results
        coherence = check_narrative_coherence(entities_found, expected_entities)
        result.entities_found = list(entities_found)
        result.entities_missing = coherence["missing_entities"]
        result.all_entities_present = coherence["all_present"]
        
        # Calculate confidence based on match quality
        if all_mentions:
            avg_confidence = sum(m.get("confidence", 0) for m in all_mentions) / len(all_mentions)
            result.confidence = coherence["coverage"] * avg_confidence
        else:
            result.confidence = 0.0
        
        # Add detailed metadata
        result.metadata = {
            "validator_name": self.name,
            "method": "token",
            "narrative_length": len(narrative_text),
            "matching_types": ["exact_name", "descriptors"],
            "descriptor_count": len(descriptor_map),
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
                    "match_type": ref["type"],
                    "score": ref.get("confidence", 1.0)
                }
                for entity, refs in entity_references.items()
                for ref in refs
            ]
        }
        
        return result