"""
Simplified structured narrative generation schemas
Based on Milestone 0.4 Combined approach implementation (without pydantic dependency)
"""

from typing import List, Optional, Dict, Any
import json
import logging
import re
from robust_json_parser import parse_llm_json_response

class NarrativeResponse:
    """Schema for structured narrative generation response"""
    
    def __init__(self, narrative: str, entities_mentioned: List[str] = None, 
                 location_confirmed: str = "Unknown", turn_summary: str = None,
                 state_updates: Dict[str, Any] = None, debug_info: Dict[str, Any] = None, **kwargs):
        # Core required fields
        self.narrative = self._validate_narrative(narrative)
        self.entities_mentioned = self._validate_entities(entities_mentioned or [])
        self.location_confirmed = location_confirmed or "Unknown"
        self.turn_summary = turn_summary
        self.state_updates = self._validate_state_updates(state_updates)
        self.debug_info = self._validate_debug_info(debug_info)
        
        # Store any extra fields that Gemini might include (shouldn't be any now)
        self.extra_fields = kwargs
    
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
    
    def _validate_state_updates(self, state_updates: Any) -> Dict[str, Any]:
        """Validate and clean state updates"""
        if state_updates is None:
            return {}
        
        if not isinstance(state_updates, dict):
            logging.warning(f"Invalid state_updates type: {type(state_updates).__name__}, expected dict. Using empty dict instead.")
            return {}
        
        return state_updates
    
    def _validate_debug_info(self, debug_info: Any) -> Dict[str, Any]:
        """Validate and clean debug info"""
        if debug_info is None:
            return {}
        
        if not isinstance(debug_info, dict):
            logging.warning(f"Invalid debug_info type: {type(debug_info).__name__}, expected dict. Using empty dict instead.")
            return {}
        
        return debug_info
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "narrative": self.narrative,
            "entities_mentioned": self.entities_mentioned,
            "location_confirmed": self.location_confirmed,
            "turn_summary": self.turn_summary,
            "state_updates": self.state_updates,
            "debug_info": self.debug_info
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
            "location_confirmed": "The current location name",
            "state_updates": {
                "player_character_data": {"hp_current": "updated value if changed"},
                "npc_data": {"npc_name": {"status": "updated status"}},
                "world_data": {"current_location": "if moved"},
                "custom_campaign_state": {"any": "custom updates"}
            }
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

ENTITY TRACKING NOTES:
- Include ALL required entities ({entities_list}) in BOTH the narrative AND entities_mentioned array
- Set location_confirmed to match the current location from the manifest
- Update state_updates with any changes to entity status, health, or relationships
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
    
    # First check if the JSON is wrapped in markdown code blocks
    json_content = response_text
    
    # Pattern to match ```json ... ``` blocks
    pattern = r'```json\s*\n?(.*?)\n?```'
    match = re.search(pattern, response_text, re.DOTALL)
    
    if match:
        json_content = match.group(1).strip()
        logging.info("Extracted JSON from markdown code block")
    else:
        # Also try without the 'json' language identifier
        pattern = r'```\s*\n?(.*?)\n?```'
        match = re.search(pattern, response_text, re.DOTALL)
        
        if match:
            content = match.group(1).strip()
            if content.startswith('{') and content.endswith('}'):
                json_content = content
                logging.info("Extracted JSON from generic code block")
    
    # Use the robust parser on the extracted content
    parsed_data, was_incomplete = parse_llm_json_response(json_content)
    
    if was_incomplete:
        narrative_len = len(parsed_data.get('narrative', '')) if parsed_data else 0
        token_count = narrative_len // 4  # Rough estimate
        logging.info(f"Recovered from incomplete JSON response. Narrative length: {narrative_len} characters (~{token_count} tokens)")
    
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
            # Extract only the fields we know about, let **kwargs handle the rest
            known_fields = {
                'narrative': narrative,
                'entities_mentioned': parsed_data.get('entities_mentioned', []),
                'location_confirmed': parsed_data.get('location_confirmed') or 'Unknown',
                'state_updates': parsed_data.get('state_updates', {}),
                'debug_info': parsed_data.get('debug_info', {})
            }
            # Pass any other fields as kwargs
            extra_fields = {k: v for k, v in parsed_data.items() if k not in known_fields}
            fallback_response = NarrativeResponse(**known_fields, **extra_fields)
            return narrative, fallback_response
    
    # Additional mitigation: Try to extract narrative from raw JSON-like text
    # This handles cases where JSON wasn't properly parsed but contains "narrative": "..."
    narrative_pattern = r'"narrative"\s*:\s*"([^"]*(?:\\.[^"]*)*)"'
    narrative_match = re.search(narrative_pattern, response_text)
    
    if narrative_match:
        extracted_narrative = narrative_match.group(1)
        # Unescape JSON string escapes
        extracted_narrative = extracted_narrative.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
        logging.info("Extracted narrative from JSON-like text pattern")
        
        fallback_response = NarrativeResponse(
            narrative=extracted_narrative,
            entities_mentioned=[],
            location_confirmed="Unknown"
        )
        return extracted_narrative, fallback_response
    
    # Final fallback: Clean up raw text for display
    # Remove JSON-like structures and format for readability
    cleaned_text = response_text
    
    # If it looks like JSON (has curly braces and quotes), try to make it readable
    if '{' in cleaned_text and '"' in cleaned_text:
        # Remove common JSON syntax that users shouldn't see
        cleaned_text = re.sub(r'[{}\[\]]', '', cleaned_text)  # Remove braces and brackets
        cleaned_text = re.sub(r'"([^"]+)":', r'\1:', cleaned_text)  # Remove quotes from keys
        cleaned_text = re.sub(r'",\s*"', '. ', cleaned_text)  # Replace JSON comma separators
        cleaned_text = re.sub(r'\\n', '\n', cleaned_text)  # Convert \n to actual newlines
        cleaned_text = re.sub(r'\\"', '"', cleaned_text)  # Unescape quotes
        cleaned_text = re.sub(r'\\\\', '\\', cleaned_text)  # Unescape backslashes
        cleaned_text = re.sub(r'[^\S\r\n]+', ' ', cleaned_text)  # Normalize spaces while preserving line breaks
        cleaned_text = cleaned_text.strip()
        logging.warning("Applied final cleanup to make JSON-like text readable")
    
    # Final fallback response
    fallback_response = NarrativeResponse(
        narrative=cleaned_text,
        entities_mentioned=[],
        location_confirmed="Unknown"
    )
    
    return cleaned_text, fallback_response

def create_generic_json_instruction() -> str:
    """
    Create generic JSON response format instruction when no entity tracking is needed
    (e.g., during character creation, campaign initialization, or scenes without entities)
    """
    # The JSON format is now defined in game_state_instruction.md which is always loaded
    # This function returns empty string since the format is already specified
    return ""

def create_structured_prompt_injection(manifest_text: str, expected_entities: List[str]) -> str:
    """
    Create structured prompt injection for JSON response format
    
    Args:
        manifest_text: Formatted scene manifest (can be empty)
        expected_entities: List of entities that must be mentioned (can be empty)
        
    Returns:
        Formatted prompt injection string
    """
    if expected_entities:
        # Use full entity tracking instruction when entities are present
        instruction = EntityTrackingInstruction.create_from_manifest(manifest_text, expected_entities)
        return instruction.to_prompt_injection()
    else:
        # Use generic JSON response format when no entities (e.g., character creation)
        return create_generic_json_instruction()

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