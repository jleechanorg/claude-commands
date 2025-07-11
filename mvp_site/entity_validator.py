"""
Enhanced Post-Generation Validation with Retry (Option 2 Enhanced)
Validates AI output for missing entities and implements retry logic.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import re
import logging_util
from entity_utils import filter_unknown_entities
logger = logging_util.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of entity validation"""
    passed: bool
    missing_entities: List[str]
    found_entities: List[str]
    confidence_score: float
    retry_needed: bool
    retry_suggestions: List[str]


class EntityValidator:
    """
    Enhanced post-generation validator that checks for missing entities
    and provides retry logic for improved entity tracking.
    """
    
    def __init__(self, min_confidence_threshold: float = 0.7):
        self.min_confidence_threshold = min_confidence_threshold
        self.entity_patterns = self._build_entity_patterns()
    
    def _build_entity_patterns(self) -> Dict[str, List[str]]:
        """Build regex patterns for entity detection"""
        return {
            'direct_mention': [
                r'\b{entity}\b',  # Direct name mention
                r'\b{entity}(?:\'s|\s+says|\s+does|\s+is|\s+was)',  # Possessive or action
            ],
            'pronoun_reference': [
                r'(?:he|she|they|him|her|them)\b',  # Pronoun references
            ],
            'role_reference': [
                r'\b(?:the\s+)?(?:guard|captain|magister|lady|lord|advisor|scholar)\b',
            ],
            'action_attribution': [
                r'(?:says|speaks|responds|nods|smiles|frowns|looks|turns)',
            ]
        }
    
    def validate_entity_presence(self, narrative_text: str, 
                                expected_entities: List[str],
                                location: Optional[str] = None) -> ValidationResult:
        """
        Validate that expected entities are present in the narrative.
        Returns detailed validation result with retry suggestions.
        """
        # Filter out 'Unknown' from expected entities - it's not a real entity
        expected_entities = filter_unknown_entities(expected_entities)
        
        narrative_lower = narrative_text.lower()
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
            overall_confidence = sum(confidence_scores.values()) / len(expected_entities)
        else:
            overall_confidence = 1.0
        
        # Determine if retry is needed
        retry_needed = len(missing_entities) > 0 or overall_confidence < self.min_confidence_threshold
        
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
            retry_suggestions=retry_suggestions
        )
        
        logger.info(f"Entity validation: {len(found_entities)}/{len(expected_entities)} found, "
                   f"confidence: {overall_confidence:.2f}")
        
        return result
    
    def _calculate_entity_presence_score(self, narrative_text: str, entity: str) -> float:
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
            rf'{re.escape(entity_lower)}\s+(?:says|speaks|responds|does|is|was)',
            rf'(?:says|speaks|responds)\s+{re.escape(entity_lower)}',
            rf'{re.escape(entity_lower)}\'s\s+(?:voice|words|response)'
        ]
        
        for pattern in action_patterns:
            if re.search(pattern, narrative_lower):
                score += 0.3
                break
        
        # Pronoun references (lower confidence, need context)
        if entity_lower in narrative_lower:
            pronouns = ['he', 'she', 'they', 'him', 'her', 'them']
            pronoun_count = sum(narrative_lower.count(pronoun) for pronoun in pronouns)
            if pronoun_count > 0:
                score += min(pronoun_count * 0.05, 0.15)
        
        return min(score, 1.0)
    
    def _generate_retry_suggestions(self, missing_entities: List[str], 
                                  found_entities: List[str],
                                  narrative_text: str,
                                  location: Optional[str] = None) -> List[str]:
        """Generate specific suggestions for retry prompts"""
        suggestions = []
        
        if not missing_entities:
            return suggestions
        
        # Generic suggestions for missing entities
        for entity in missing_entities:
            suggestions.append(f"Include {entity} in the scene with dialogue, actions, or reactions")
        
        # Generic location-based suggestions
        if location and missing_entities:
            suggestions.append(f"Ensure the missing characters fit naturally in {location}")
        
        # General narrative suggestions
        if len(missing_entities) > len(found_entities):
            suggestions.append("Ensure all characters present in the scene have some role or mention")
        
        if len(missing_entities) >= 2:
            suggestions.append("Consider adding dialogue between the missing characters")
        
        return suggestions
    
    def create_retry_prompt(self, original_prompt: str, validation_result: ValidationResult,
                           location: Optional[str] = None) -> str:
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
            retry_instructions.append(f"Setting: {location} - ensure all characters appropriate to this location are present")
        
        # Combine instructions
        retry_text = "\n".join(retry_instructions)
        enhanced_prompt = f"{original_prompt}\n\n=== RETRY INSTRUCTIONS ===\n{retry_text}\n\nPlease revise your response to include all required characters."
        
        return enhanced_prompt


class EntityRetryManager:
    """
    Manages retry logic for entity validation failures.
    Implements smart retry strategies to improve entity tracking.
    """
    
    def __init__(self, max_retries: int = 2):
        self.max_retries = max_retries
        self.validator = EntityValidator()
        self.retry_history = {}
    
    def validate_with_retry(self, narrative_text: str, expected_entities: List[str],
                           location: Optional[str] = None,
                           retry_callback: Optional[callable] = None) -> Tuple[ValidationResult, int]:
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
        while (validation_result.retry_needed and 
               retry_attempts < self.max_retries and 
               retry_callback is not None):
            
            retry_attempts += 1
            logger.info(f"Entity validation failed, attempting retry {retry_attempts}/{self.max_retries}")
            
            # Create retry prompt
            retry_prompt = self.validator.create_retry_prompt(
                "Please revise the narrative to include all required characters",
                validation_result,
                location
            )
            
            # Call retry callback to regenerate narrative
            try:
                current_narrative = retry_callback(retry_prompt, missing_entities=validation_result.missing_entities)
                
                # Validate the new narrative
                validation_result = self.validator.validate_entity_presence(
                    current_narrative, expected_entities, location
                )
                
                logger.info(f"Retry {retry_attempts} result: {len(validation_result.found_entities)}/{len(expected_entities)} entities found")
                
            except Exception as e:
                logger.error(f"Retry {retry_attempts} failed with error: {e}")
                break
        
        # Log final result
        if validation_result.passed:
            logger.info(f"Entity validation passed after {retry_attempts} retries")
        else:
            logger.warning(f"Entity validation failed after {retry_attempts} retries. Missing: {validation_result.missing_entities}")
        
        return validation_result, retry_attempts
    
    def get_retry_statistics(self) -> Dict[str, Any]:
        """Get statistics about retry performance"""
        # This could be expanded to track retry success rates over time
        return {
            "max_retries_configured": self.max_retries,
            "validator_threshold": self.validator.min_confidence_threshold
        }


# Global instances
entity_validator = EntityValidator()
entity_retry_manager = EntityRetryManager()