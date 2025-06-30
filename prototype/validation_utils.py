"""
Shared utilities for all validator types.
Common functions for text processing, entity matching, and validation helpers.
"""

import re
from typing import List, Dict, Tuple, Set, Optional, Any
from difflib import SequenceMatcher
import unicodedata


def normalize_text(text: str) -> str:
    """Normalize text for consistent matching."""
    # Convert to lowercase
    text = text.lower()
    
    # Remove accents and special characters
    text = ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )
    
    # Replace multiple spaces with single space
    text = ' '.join(text.split())
    
    return text.strip()


def extract_sentences(text: str) -> List[str]:
    """Extract sentences from narrative text."""
    # Simple sentence splitting (can be improved)
    sentences = re.split(r'[.!?]+', text)
    return [s.strip() for s in sentences if s.strip()]


def find_entity_mentions(text: str, entity_name: str, 
                        descriptors: List[str] = None) -> List[Dict]:
    """
    Find all mentions of an entity in text.
    
    Args:
        text: The narrative text to search
        entity_name: The entity name to find
        descriptors: Optional list of descriptors/aliases
        
    Returns:
        List of mention dictionaries with text, position, and type
    """
    mentions = []
    text_lower = text.lower()
    
    # Search for direct name mentions
    name_pattern = re.compile(r'\b' + re.escape(entity_name.lower()) + r'\b')
    for match in name_pattern.finditer(text_lower):
        mentions.append({
            "text": text[match.start():match.end()],
            "position": match.start(),
            "type": "name",
            "confidence": 1.0
        })
    
    # Search for descriptor mentions
    if descriptors:
        for descriptor in descriptors:
            desc_pattern = re.compile(r'\b' + re.escape(descriptor.lower()) + r'\b')
            for match in desc_pattern.finditer(text_lower):
                # Avoid duplicates with name matches
                if not any(m["position"] == match.start() for m in mentions):
                    mentions.append({
                        "text": text[match.start():match.end()],
                        "position": match.start(),
                        "type": "descriptor",
                        "confidence": 0.8
                    })
    
    return mentions


def calculate_string_similarity(str1: str, str2: str) -> float:
    """Calculate similarity between two strings (0.0 to 1.0)."""
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()


def fuzzy_match_entity(text: str, entity_name: str, threshold: float = 0.8) -> List[Dict]:
    """
    Find fuzzy matches for an entity name in text.
    
    Args:
        text: The text to search
        entity_name: The entity name to match
        threshold: Minimum similarity threshold (0.0 to 1.0)
        
    Returns:
        List of fuzzy matches with similarity scores
    """
    matches = []
    words = text.split()
    entity_lower = entity_name.lower()
    
    # Check individual words
    for i, word in enumerate(words):
        similarity = calculate_string_similarity(word, entity_lower)
        if similarity >= threshold:
            # Get position in original text
            position = text.find(word)
            matches.append({
                "text": word,
                "position": position,
                "type": "fuzzy",
                "confidence": similarity
            })
    
    # Check word pairs (for names like "Ser Vance")
    for i in range(len(words) - 1):
        word_pair = f"{words[i]} {words[i+1]}"
        similarity = calculate_string_similarity(word_pair, entity_lower)
        if similarity >= threshold:
            position = text.find(word_pair)
            matches.append({
                "text": word_pair,
                "position": position,
                "type": "fuzzy",
                "confidence": similarity
            })
    
    return matches


def extract_pronouns(text: str) -> List[Dict]:
    """Extract pronouns that might refer to entities."""
    pronouns = {
        "male": ["he", "him", "his", "himself"],
        "female": ["she", "her", "hers", "herself"],
        "neutral": ["they", "them", "their", "theirs", "themselves"],
        "group": ["we", "us", "our", "ours", "ourselves"]
    }
    
    found_pronouns = []
    text_lower = text.lower()
    
    for category, pronoun_list in pronouns.items():
        for pronoun in pronoun_list:
            pattern = re.compile(r'\b' + pronoun + r'\b')
            for match in pattern.finditer(text_lower):
                found_pronouns.append({
                    "text": text[match.start():match.end()],
                    "position": match.start(),
                    "type": "pronoun",
                    "category": category
                })
    
    return found_pronouns


def detect_entity_states(text: str) -> Dict[str, List[str]]:
    """Detect entity states mentioned in text (hidden, unconscious, etc)."""
    state_patterns = {
        "hidden": [r"hidden", r"hiding", r"concealed", r"in the shadows"],
        "unconscious": [r"unconscious", r"knocked out", r"fainted", r"collapsed"],
        "combat": [r"fighting", r"battling", r"in combat", r"engaged"],
        "dead": [r"dead", r"deceased", r"killed", r"fallen"],
        "absent": [r"gone", r"missing", r"disappeared", r"left"]
    }
    
    detected_states = {}
    text_lower = text.lower()
    
    for state, patterns in state_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                # Try to find associated entity
                sentences = extract_sentences(text)
                for sentence in sentences:
                    if re.search(pattern, sentence.lower()):
                        # This is a simplified approach - could be enhanced
                        detected_states[state] = detected_states.get(state, [])
                        detected_states[state].append(sentence)
    
    return detected_states


def check_narrative_coherence(entities_found: Set[str], 
                             expected_entities: List[str]) -> Dict[str, Any]:
    """
    Check the coherence of found entities vs expected.
    
    Returns:
        Dictionary with coherence metrics
    """
    expected_set = set(expected_entities)
    
    # Calculate metrics
    missing = expected_set - entities_found
    extra = entities_found - expected_set
    found_expected = entities_found & expected_set
    
    total_expected = len(expected_set)
    coverage = len(found_expected) / total_expected if total_expected > 0 else 0
    
    return {
        "all_present": len(missing) == 0,
        "coverage": coverage,
        "missing_entities": list(missing),
        "extra_entities": list(extra),
        "found_expected": list(found_expected)
    }


def merge_entity_references(references: List[Dict]) -> List[Dict]:
    """Merge and deduplicate entity references."""
    # Sort by position
    sorted_refs = sorted(references, key=lambda x: x.get("position", 0))
    
    # Merge overlapping references
    merged = []
    for ref in sorted_refs:
        if not merged:
            merged.append(ref)
        else:
            last = merged[-1]
            # Check for overlap
            if ref["position"] < last["position"] + len(last.get("text", "")):
                # Overlapping - keep the one with higher confidence
                if ref.get("confidence", 0) > last.get("confidence", 0):
                    merged[-1] = ref
            else:
                merged.append(ref)
    
    return merged


def generate_validation_summary(result: Dict[str, Any]) -> str:
    """Generate a human-readable summary of validation results."""
    summary_parts = []
    
    # Overall result
    if result.get("all_entities_present"):
        summary_parts.append("✓ All expected entities are present")
    else:
        summary_parts.append("✗ Some expected entities are missing")
    
    # Found entities
    found = result.get("entities_found", [])
    if found:
        summary_parts.append(f"Found: {', '.join(found)}")
    
    # Missing entities
    missing = result.get("entities_missing", [])
    if missing:
        summary_parts.append(f"Missing: {', '.join(missing)}")
    
    # Confidence
    confidence = result.get("confidence", 0)
    summary_parts.append(f"Confidence: {confidence:.1%}")
    
    # Warnings
    warnings = result.get("warnings", [])
    if warnings:
        summary_parts.append(f"Warnings: {len(warnings)}")
    
    return " | ".join(summary_parts)