"""
Simplified structured narrative generation schemas
Based on Milestone 0.4 Combined approach implementation (without pydantic dependency)
"""

from typing import List, Optional, Dict, Any
import json
import logging
from robust_json_parser import parse_llm_json_response

class NarrativeResponse:
    """Schema for structured narrative generation response"""
    
    def __init__(self, narrative: str, entities_mentioned: List[str] = None, 
                 location_confirmed: str = "Unknown", turn_summary: str = None):
        self.narrative = self._validate_narrative(narrative)
        self.entities_mentioned = self._validate_entities(entities_mentioned or [])
        self.location_confirmed = location_confirmed
        self.turn_summary = turn_summary
    
    def _validate_narrative(self, narrative: str) -> str:
        """Validate narrative content"""
        if not isinstance(narrative, str):
            raise ValueError("Narrative must be a string")
        
        cleaned = narrative.strip()
        
        return cleaned
    
    def _validate_entities(self, entities: List[str]) -> List[str]:
        """Validate and clean entity list"""
        if not isinstance(entities, list):
            raise ValueError("Entities must be a list")
        
        return [str(entity).strip() for entity in entities if str(entity).strip()]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "narrative": self.narrative,
            "entities_mentioned": self.entities_mentioned,
            "location_confirmed": self.location_confirmed,
            "turn_summary": self.turn_summary
        }

class EntityTrackingInstruction:
    """Schema for entity tracking instructions to be injected into prompts"""
    
    def __init__(self, scene_manifest: str, expected_entities: List[str], response_format: str):
        self.scene_manifest = scene_manifest
        self.expected_entities = expected_entities
        self.response_format = response_format
    
    @classmethod
    def create_from_manifest(cls, manifest_text: str, expected_entities: List[str]) -> 'EntityTrackingInstruction':
        """Create entity tracking instruction from manifest"""
        response_format = {
            "narrative": "Your narrative text here...",
            "entities_mentioned": expected_entities,
            "location_confirmed": "The current location name"
        }
        
        response_format_str = json.dumps(response_format, indent=2)
        
        return cls(
            scene_manifest=manifest_text,
            expected_entities=expected_entities,
            response_format=response_format_str
        )
    
    def to_prompt_injection(self) -> str:
        """Convert to prompt injection format"""
        entities_list = ", ".join(self.expected_entities)
        
        return f"""
{self.scene_manifest}

CRITICAL ENTITY TRACKING REQUIREMENT:
You MUST mention ALL characters listed in the manifest above in your narrative.
Required entities: {entities_list}

RESPONSE FORMAT REQUIREMENT:
You must format your response as valid JSON with exactly this structure:
{self.response_format}

IMPORTANT NOTES:
- The "narrative" field should contain your complete narrative response
- The "entities_mentioned" field should list ALL entities you referenced in the narrative
- The "location_confirmed" field should match the location from the manifest
- Ensure ALL required entities ({entities_list}) appear in both the narrative text AND the entities_mentioned list
"""

def parse_structured_response(response_text: str) -> tuple[str, NarrativeResponse]:
    """
    Parse structured JSON response from LLM
    
    Returns:
        tuple: (narrative_text, parsed_response_or_none)
    """
    if not response_text:
        empty_response = NarrativeResponse(
            narrative="The story awaits your input...",  # Default narrative for empty response
            entities_mentioned=[],
            location_confirmed="Unknown"
        )
        return empty_response.narrative, empty_response
    
    # Use the robust parser
    parsed_data, was_incomplete = parse_llm_json_response(response_text)
    
    if was_incomplete:
        logging.info(f"Recovered from incomplete JSON response. Narrative length: {len(parsed_data.get('narrative', '')) if parsed_data else 0}")
    
    # Create NarrativeResponse from parsed data
    if parsed_data:
        try:
            validated_response = NarrativeResponse(**parsed_data)
            return validated_response.narrative, validated_response
                
        except (ValueError, TypeError) as e:
            # NarrativeResponse creation failed
            logging.error(f"Failed to create NarrativeResponse: {e}")
            # Return the narrative if we at least got that
            narrative = parsed_data.get('narrative', response_text)
            fallback_response = NarrativeResponse(
                narrative=narrative,
                entities_mentioned=parsed_data.get('entities_mentioned', []),
                location_confirmed=parsed_data.get('location_confirmed', 'Unknown')
            )
        return narrative, fallback_response
    
    # Final fallback: return original text with empty response object
    # This should rarely be reached with the robust parser
    fallback_response = NarrativeResponse(
        narrative=response_text,
        entities_mentioned=[],
        location_confirmed="Unknown"
    )
    
    return response_text, fallback_response

def create_structured_prompt_injection(manifest_text: str, expected_entities: List[str]) -> str:
    """
    Create structured prompt injection for entity tracking
    
    Args:
        manifest_text: Formatted scene manifest
        expected_entities: List of entities that must be mentioned
        
    Returns:
        Formatted prompt injection string
    """
    instruction = EntityTrackingInstruction.create_from_manifest(manifest_text, expected_entities)
    return instruction.to_prompt_injection()

def validate_entity_coverage(response: NarrativeResponse, expected_entities: List[str]) -> Dict[str, Any]:
    """
    Validate that the structured response covers all expected entities
    
    Returns:
        Dict with validation results
    """
    mentioned_entities = set(entity.lower() for entity in response.entities_mentioned)
    expected_entities_lower = set(entity.lower() for entity in expected_entities)
    
    missing_entities = expected_entities_lower - mentioned_entities
    extra_entities = mentioned_entities - expected_entities_lower
    
    # Also check narrative text for entity mentions (backup validation)
    narrative_lower = response.narrative.lower()
    narrative_mentions = set()
    for entity in expected_entities:
        if entity.lower() in narrative_lower:
            narrative_mentions.add(entity.lower())
    
    actually_missing = expected_entities_lower - narrative_mentions
    
    return {
        "schema_valid": len(missing_entities) == 0,
        "narrative_valid": len(actually_missing) == 0,
        "missing_from_schema": list(missing_entities),
        "missing_from_narrative": list(actually_missing),
        "extra_entities": list(extra_entities),
        "coverage_rate": len(narrative_mentions) / len(expected_entities) if expected_entities else 1.0,
        "entities_mentioned_count": len(response.entities_mentioned),
        "expected_entities_count": len(expected_entities)
    }