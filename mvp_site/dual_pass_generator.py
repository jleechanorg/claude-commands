"""
Dual-Pass Generation System (Option 7)
First pass generates narrative, second pass verifies and injects missing entities.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging
from entity_validator import EntityValidator, ValidationResult

logger = logging.getLogger(__name__)


@dataclass
class GenerationPass:
    """Represents a single generation pass"""
    pass_number: int
    prompt: str
    response: str
    entities_found: List[str]
    validation_result: Optional[ValidationResult] = None


@dataclass
class DualPassResult:
    """Result of dual-pass generation"""
    first_pass: GenerationPass
    second_pass: Optional[GenerationPass]
    final_narrative: str
    total_entities_found: List[str]
    success: bool
    improvement_achieved: bool


class DualPassGenerator:
    """
    Implements dual-pass generation to improve entity tracking.
    Pass 1: Generate initial narrative
    Pass 2: Verify entities and inject missing ones
    """
    
    def __init__(self):
        self.validator = EntityValidator()
        self.entity_injection_templates = self._build_injection_templates()
    
    def _build_injection_templates(self) -> Dict[str, List[str]]:
        """Build templates for injecting missing entities"""
        # Use only generic templates that work for any campaign
        return {
            'generic': [
                "{entity}, who had been present but silent, {action}.",
                "Nearby, {entity} {action}, adding their perspective to the scene.",
                "{entity} steps forward and {action}.",
                "{entity}'s voice cuts through: '{dialogue}'",
                "From across the room, {entity} {action}.",
                "{entity} looks up from their position and {action}."
            ]
        }
    
    def generate_with_dual_pass(self, initial_prompt: str, expected_entities: List[str],
                               location: Optional[str] = None,
                               generation_callback: callable = None) -> DualPassResult:
        """
        Execute dual-pass generation with entity verification.
        
        Args:
            initial_prompt: The original prompt for narrative generation
            expected_entities: Entities that should be present
            location: Current scene location
            generation_callback: Function to call AI generation (gemini_service.continue_story)
        
        Returns:
            DualPassResult with both passes and final narrative
        """
        logger.info("Starting dual-pass generation")
        
        # PASS 1: Initial narrative generation
        logger.info("Pass 1: Generating initial narrative")
        first_pass_response = generation_callback(initial_prompt) if generation_callback else ""
        
        first_pass_validation = self.validator.validate_entity_presence(
            first_pass_response, expected_entities, location
        )
        
        first_pass = GenerationPass(
            pass_number=1,
            prompt=initial_prompt,
            response=first_pass_response,
            entities_found=first_pass_validation.found_entities,
            validation_result=first_pass_validation
        )
        
        logger.info(f"Pass 1 completed: {len(first_pass_validation.found_entities)}/{len(expected_entities)} entities found")
        
        # Check if second pass is needed
        if not first_pass_validation.retry_needed:
            logger.info("Pass 1 successful, no second pass needed")
            return DualPassResult(
                first_pass=first_pass,
                second_pass=None,
                final_narrative=first_pass_response,
                total_entities_found=first_pass_validation.found_entities,
                success=True,
                improvement_achieved=False
            )
        
        # PASS 2: Entity injection and enhancement
        logger.info(f"Pass 2: Injecting missing entities: {first_pass_validation.missing_entities}")
        
        second_pass_prompt = self._create_injection_prompt(
            first_pass_response, 
            first_pass_validation.missing_entities,
            location
        )
        
        second_pass_response = generation_callback(second_pass_prompt) if generation_callback else ""
        
        # Combine first pass and second pass
        enhanced_narrative = self._combine_narratives(first_pass_response, second_pass_response)
        
        # Validate final result
        final_validation = self.validator.validate_entity_presence(
            enhanced_narrative, expected_entities, location
        )
        
        second_pass = GenerationPass(
            pass_number=2,
            prompt=second_pass_prompt,
            response=second_pass_response,
            entities_found=final_validation.found_entities,
            validation_result=final_validation
        )
        
        # Determine success and improvement
        improvement_achieved = len(final_validation.found_entities) > len(first_pass_validation.found_entities)
        success = not final_validation.retry_needed
        
        logger.info(f"Dual-pass completed: {len(final_validation.found_entities)}/{len(expected_entities)} entities found, "
                   f"improvement: {improvement_achieved}")
        
        return DualPassResult(
            first_pass=first_pass,
            second_pass=second_pass,
            final_narrative=enhanced_narrative,
            total_entities_found=final_validation.found_entities,
            success=success,
            improvement_achieved=improvement_achieved
        )
    
    def _create_injection_prompt(self, original_narrative: str, 
                                missing_entities: List[str],
                                location: Optional[str] = None) -> str:
        """Create prompt for second pass entity injection"""
        injection_instructions = []
        
        injection_instructions.append(
            "You need to enhance the following narrative by adding the missing characters. "
            "The characters should be naturally integrated into the scene."
        )
        
        injection_instructions.append(f"\nORIGINAL NARRATIVE:\n{original_narrative}")
        
        injection_instructions.append(f"\nMISSING CHARACTERS TO ADD: {', '.join(missing_entities)}")
        
        # Add generic instructions for each missing entity
        for entity in missing_entities:
            # Use generic, context-aware instructions for all entities
            injection_instructions.append(
                f"- {entity}: Should be naturally present and contribute meaningfully to the scene"
            )
        
        if location:
            injection_instructions.append(f"\nSETTING: {location} - ensure all characters fit naturally in this location")
        
        injection_instructions.append(
            "\nProvide an enhanced version of the narrative that includes all missing characters "
            "while maintaining the original story's flow and tone. Add their dialogue, actions, "
            "or presence as appropriate."
        )
        
        return "\n".join(injection_instructions)
    
    def _combine_narratives(self, first_pass: str, second_pass: str) -> str:
        """Intelligently combine first and second pass narratives"""
        # Simple combination for now - could be enhanced with more sophisticated merging
        if not second_pass.strip():
            return first_pass
        
        # If second pass is a complete rewrite, use it
        if len(second_pass) > len(first_pass) * 0.8:
            return second_pass
        
        # Otherwise, append enhancement
        separator = "\n\n" if not first_pass.endswith('\n') else ""
        return f"{first_pass}{separator}{second_pass}"
    
    def create_entity_injection_snippet(self, entity: str, location: Optional[str] = None,
                                      context: str = "responds to the situation") -> str:
        """Create a snippet to inject a missing entity"""
        entity_lower = entity.lower()
        
        # Find appropriate template
        template_key = 'generic'
        for key in self.entity_injection_templates:
            if key in entity_lower:
                template_key = key
                break
        
        templates = self.entity_injection_templates[template_key]
        
        # Choose template based on context
        if template_key == 'generic':
            template = templates[0]  # Use first generic template
            return template.format(entity=entity, action=context)
        else:
            template = templates[0]  # Use first specific template
            return template.format(action=context, context=location or "the current situation")


class AdaptiveEntityInjector:
    """
    Advanced entity injection that adapts based on narrative context.
    """
    
    def __init__(self):
        self.injection_strategies = {
            'dialogue_based': self._inject_via_dialogue,
            'action_based': self._inject_via_action,
            'presence_based': self._inject_via_presence,
            'reaction_based': self._inject_via_reaction
        }
    
    def inject_entities_adaptively(self, narrative: str, missing_entities: List[str],
                                  location: Optional[str] = None) -> str:
        """Adaptively inject missing entities based on narrative context"""
        enhanced_narrative = narrative
        
        for entity in missing_entities:
            injection_strategy = self._choose_injection_strategy(narrative, entity)
            injector = self.injection_strategies[injection_strategy]
            
            enhanced_narrative = injector(enhanced_narrative, entity, location)
            logger.info(f"Injected {entity} using {injection_strategy} strategy")
        
        return enhanced_narrative
    
    def _choose_injection_strategy(self, narrative: str, entity: str) -> str:
        """Choose the best injection strategy based on narrative context"""
        narrative_lower = narrative.lower()
        
        # If there's dialogue, use dialogue-based injection
        if '"' in narrative or "says" in narrative_lower:
            return 'dialogue_based'
        
        # If there's action, use action-based injection
        if any(word in narrative_lower for word in ['moves', 'walks', 'turns', 'looks']):
            return 'action_based'
        
        # If emotional content, use reaction-based
        if any(word in narrative_lower for word in ['scared', 'helpless', 'worried', 'angry']):
            return 'reaction_based'
        
        # Default to presence-based
        return 'presence_based'
    
    def _inject_via_dialogue(self, narrative: str, entity: str, location: Optional[str]) -> str:
        """Inject entity through dialogue"""
        dialogue_snippet = f'\n\n{entity} speaks up: "I understand the gravity of this situation."'
        return narrative + dialogue_snippet
    
    def _inject_via_action(self, narrative: str, entity: str, location: Optional[str]) -> str:
        """Inject entity through action"""
        action_snippet = f'\n\n{entity} steps forward, their presence adding weight to the moment.'
        return narrative + action_snippet
    
    def _inject_via_presence(self, narrative: str, entity: str, location: Optional[str]) -> str:
        """Inject entity through simple presence"""
        presence_snippet = f'\n\n{entity} remains nearby, observing the unfolding situation.'
        return narrative + presence_snippet
    
    def _inject_via_reaction(self, narrative: str, entity: str, location: Optional[str]) -> str:
        """Inject entity through emotional reaction"""
        reaction_snippet = f'\n\n{entity} shows clear concern for the emotional weight of the moment.'
        return narrative + reaction_snippet


# Global instances
dual_pass_generator = DualPassGenerator()
adaptive_injector = AdaptiveEntityInjector()