"""
Simplified structured narrative generation schemas
Based on Milestone 0.4 Combined approach implementation (without pydantic dependency)
"""

from typing import List, Optional, Dict, Any
import json
import logging_util
import re
from robust_json_parser import parse_llm_json_response

# Precompiled regex patterns for better performance
JSON_MARKDOWN_PATTERN = re.compile(r'```json\s*\n?(.*?)\n?```', re.DOTALL)
GENERIC_MARKDOWN_PATTERN = re.compile(r'```\s*\n?(.*?)\n?```', re.DOTALL)
NARRATIVE_PATTERN = re.compile(r'"narrative"\s*:\s*"([^"]*(?:\\.[^"]*)*)"')

# JSON cleanup patterns
JSON_STRUCTURE_PATTERN = re.compile(r'[{}\[\]]')
JSON_KEY_QUOTES_PATTERN = re.compile(r'"([^"]+)":')
JSON_COMMA_SEPARATOR_PATTERN = re.compile(r'",\s*"')
WHITESPACE_PATTERN = re.compile(r'[^\S\r\n]+')  # Normalize spaces while preserving line breaks

class NarrativeResponse:
    """Schema for structured narrative generation response"""
    
    def __init__(self, narrative: str, entities_mentioned: List[str] = None, 
                 location_confirmed: str = "Unknown", turn_summary: str = None,
                 state_updates: Dict[str, Any] = None, debug_info: Dict[str, Any] = None,
                 god_mode_response: str = None, **kwargs):
        # Core required fields
        self.narrative = self._validate_narrative(narrative)
        self.entities_mentioned = self._validate_entities(entities_mentioned or [])
        self.location_confirmed = location_confirmed or "Unknown"
        self.turn_summary = turn_summary
        self.state_updates = self._validate_state_updates(state_updates)
        self.debug_info = self._validate_debug_info(debug_info)
        self.god_mode_response = god_mode_response
        
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
            logging_util.warning(f"Invalid state_updates type: {type(state_updates).__name__}, expected dict. Using empty dict instead.")
            return {}
        
        return state_updates
    
    def _validate_debug_info(self, debug_info: Any) -> Dict[str, Any]:
        """Validate and clean debug info"""
        if debug_info is None:
            return {}
        
        if not isinstance(debug_info, dict):
            logging_util.warning(f"Invalid debug_info type: {type(debug_info).__name__}, expected dict. Using empty dict instead.")
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

def _combine_god_mode_and_narrative(god_mode_response: str, narrative: Optional[str]) -> str:
    """
    Helper function to combine god_mode_response and narrative fields.
    
    Args:
        god_mode_response: The god mode response text
        narrative: Optional narrative text (may be None or empty)
        
    Returns:
        Combined response with god_mode_response first, then narrative if present
    """
    combined_response = god_mode_response
    if narrative and narrative.strip():
        combined_response += "\n\n" + narrative
    return combined_response


def parse_structured_response(response_text: str) -> tuple[str, NarrativeResponse]:
    """
    Parse structured response and check for JSON bug issues.
    """
    # DEBUG: Log entry into parse function
    logging_util.debug(f"JSON_BUG_PARSE_ENTRY: Processing response of length {len(response_text)}")
    logging_util.debug(f"JSON_BUG_PARSE_INPUT: {response_text[:300]}...")
    
    # Check if input is already raw JSON
    if response_text.strip().startswith('{') and '"narrative":' in response_text:
        logging_util.error(f"JSON_BUG_PARSE_RAW_JSON_INPUT: Input is already raw JSON!")
        logging_util.error(f"JSON_BUG_PARSE_RAW_CONTENT: {response_text[:500]}...")
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
    
    # Strip "Scene #X:" prefix if present (common in JSON responses)
    scene_prefix_pattern = re.compile(r'^Scene\s+#\d+:\s*', re.IGNORECASE)
    match = scene_prefix_pattern.match(json_content)
    if match:
        json_content = json_content[match.end():]
        logging_util.info(f"Stripped 'Scene #' prefix from JSON response: '{match.group(0)}'")
        logging_util.debug(f"JSON_BUG_STRIPPED_PREFIX: Content after stripping: {json_content[:100]}...")
    
    # Use precompiled pattern to match ```json ... ``` blocks
    match = JSON_MARKDOWN_PATTERN.search(response_text)
    
    if match:
        json_content = match.group(1).strip()
        logging_util.info("Extracted JSON from markdown code block")
    else:
        # Also try without the 'json' language identifier
        match = GENERIC_MARKDOWN_PATTERN.search(response_text)
        
        if match:
            content = match.group(1).strip()
            if content.startswith('{') and content.endswith('}'):
                json_content = content
                logging_util.info("Extracted JSON from generic code block")
    
    # Re-check for Scene prefix after markdown extraction
    scene_match = scene_prefix_pattern.match(json_content)
    if scene_match:
        json_content = json_content[scene_match.end():]
        logging_util.info(f"Stripped 'Scene #' prefix after markdown extraction: '{scene_match.group(0)}'")
    
    # Use the robust parser on the extracted content
    logging_util.debug(f"JSON_BUG_PARSE_JSON_CONTENT: {json_content[:300]}...")
    parsed_data, was_incomplete = parse_llm_json_response(json_content)
    logging_util.debug(f"JSON_BUG_PARSE_ROBUST_RESULT: parsed_data={parsed_data}, was_incomplete={was_incomplete}")
    
    if was_incomplete:
        narrative_len = len(parsed_data.get('narrative', '')) if parsed_data else 0
        token_count = narrative_len // 4  # Rough estimate
        logging_util.info(f"Recovered from incomplete JSON response. Narrative length: {narrative_len} characters (~{token_count} tokens)")
    
    # Create NarrativeResponse from parsed data
    logging_util.debug(f"JSON_BUG_PARSE_PARSED_DATA: {parsed_data}")
    
    if parsed_data:
        try:
            validated_response = NarrativeResponse(**parsed_data)
            # If god_mode_response is present, return both god mode response and narrative
            if hasattr(validated_response, 'god_mode_response') and validated_response.god_mode_response:
                combined_response = _combine_god_mode_and_narrative(
                    validated_response.god_mode_response,
                    validated_response.narrative
                )
                return combined_response, validated_response
            return validated_response.narrative, validated_response
                
        except (ValueError, TypeError) as e:
            # NarrativeResponse creation failed
            logging_util.error(f"JSON_BUG_NARRATIVE_RESPONSE_FAILED: {e}")
            logging_util.error(f"JSON_BUG_FAILED_PARSED_DATA: {parsed_data}")
            # Check for god_mode_response first
            god_mode_response = parsed_data.get('god_mode_response')
            if god_mode_response:
                # For god mode, combine god_mode_response with narrative if both exist
                narrative = parsed_data.get('narrative')
                # Handle null narrative
                if narrative is None:
                    narrative = ''
                combined_response = _combine_god_mode_and_narrative(
                    god_mode_response,
                    narrative
                )
                    
                known_fields = {
                    'narrative': narrative,
                    'god_mode_response': god_mode_response,
                    'entities_mentioned': parsed_data.get('entities_mentioned', []),
                    'location_confirmed': parsed_data.get('location_confirmed') or 'Unknown',
                    'state_updates': parsed_data.get('state_updates', {}),
                    'debug_info': parsed_data.get('debug_info', {})
                }
                # Pass any other fields as kwargs
                extra_fields = {k: v for k, v in parsed_data.items() if k not in known_fields}
                fallback_response = NarrativeResponse(**known_fields, **extra_fields)
                return combined_response, fallback_response
            
            # Return the narrative if we at least got that
            narrative = parsed_data.get('narrative')
            # Handle null or missing narrative - use empty string instead of raw JSON
            if narrative is None:
                narrative = ''
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
    logging_util.debug(f"JSON_BUG_PARSE_FALLBACK_NARRATIVE_EXTRACTION: Trying to extract from {response_text[:200]}...")
    narrative_match = NARRATIVE_PATTERN.search(response_text)
    
    if narrative_match:
        extracted_narrative = narrative_match.group(1)
        # Unescape JSON string escapes
        extracted_narrative = extracted_narrative.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
        logging_util.info("Extracted narrative from JSON-like text pattern")
        
        fallback_response = NarrativeResponse(
            narrative=extracted_narrative,
            entities_mentioned=[],
            location_confirmed="Unknown"
        )
        return extracted_narrative, fallback_response
    
    # Final fallback: Clean up raw text for display
    # Remove JSON-like structures and format for readability
    cleaned_text = response_text
    
    # DEBUG: Log fallback entry conditions
    logging_util.debug(f"RAW_JSON_FALLBACK_ENTRY: response_text[:200] = {response_text[:200]}")
    
    # Safer approach: Only clean if it's clearly malformed JSON
    # Check multiple indicators to avoid corrupting valid narrative text
    is_likely_json = (
        '{' in cleaned_text and '"' in cleaned_text and 
        (cleaned_text.strip().startswith('{') or cleaned_text.strip().startswith('"')) and
        (cleaned_text.strip().endswith('}') or cleaned_text.strip().endswith('"')) and
        cleaned_text.count('"') >= 4  # At least 2 key-value pairs
    )
    
    logging_util.debug(f"RAW_JSON_FALLBACK_IS_LIKELY_JSON: {is_likely_json}")
    
    if is_likely_json:
        # Apply cleanup only to confirmed JSON-like text
        # First, try to extract just the narrative value if possible
        if '"narrative"' in cleaned_text:
            # Try to extract narrative value safely
            narrative_match = NARRATIVE_PATTERN.search(cleaned_text)
            if narrative_match:
                cleaned_text = narrative_match.group(1)
                # Unescape JSON string escapes
                cleaned_text = cleaned_text.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
                logging_util.debug(f"RAW_JSON_FALLBACK_EXTRACTED_NARRATIVE: {cleaned_text[:200]}")
                logging_util.info("Extracted narrative from JSON structure")
            else:
                # Fallback to aggressive cleanup only as last resort
                logging_util.debug(f"RAW_JSON_FALLBACK_BEFORE_AGGRESSIVE_CLEANUP: {cleaned_text[:200]}")
                cleaned_text = JSON_STRUCTURE_PATTERN.sub('', cleaned_text)  # Remove braces and brackets
                cleaned_text = JSON_KEY_QUOTES_PATTERN.sub(r'\1:', cleaned_text)  # Remove quotes from keys
                cleaned_text = JSON_COMMA_SEPARATOR_PATTERN.sub('. ', cleaned_text)  # Replace JSON comma separators
                cleaned_text = cleaned_text.replace('\\n', '\n')  # Convert \n to actual newlines
                cleaned_text = cleaned_text.replace('\\"', '"')  # Unescape quotes
                cleaned_text = cleaned_text.replace('\\\\', '\\')  # Unescape backslashes
                cleaned_text = WHITESPACE_PATTERN.sub(' ', cleaned_text)  # Normalize spaces while preserving line breaks
                cleaned_text = cleaned_text.strip()
                logging_util.debug(f"RAW_JSON_FALLBACK_AFTER_AGGRESSIVE_CLEANUP: {cleaned_text[:200]}")
                logging_util.warning("Applied aggressive cleanup to malformed JSON")
        else:
            # No narrative field found, apply minimal cleanup
            logging_util.debug(f"RAW_JSON_FALLBACK_BEFORE_MINIMAL_CLEANUP: {cleaned_text[:200]}")
            cleaned_text = cleaned_text.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
            logging_util.debug(f"RAW_JSON_FALLBACK_AFTER_MINIMAL_CLEANUP: {cleaned_text[:200]}")
            logging_util.warning("Applied minimal cleanup to JSON-like text without narrative field")
    
    # Final fallback response
    logging_util.debug(f"RAW_JSON_FALLBACK_FINAL_RESULT: {cleaned_text[:200]}")
    
    fallback_response = NarrativeResponse(
        narrative=cleaned_text,
        entities_mentioned=[],
        location_confirmed="Unknown"
    )
    
    # DEBUG: Log what we're returning from parse function
    logging_util.debug(f"JSON_BUG_PARSE_RETURN_TEXT: {cleaned_text[:300]}...")
    logging_util.debug(f"JSON_BUG_PARSE_RETURN_RESPONSE: {fallback_response}")
    
    # Final check for JSON artifacts in returned text
    if '"narrative":' in cleaned_text or '"god_mode_response":' in cleaned_text:
        logging_util.error(f"JSON_BUG_PARSE_RETURNING_JSON: Still returning JSON artifacts!")
        logging_util.error(f"JSON_BUG_PARSE_FINAL_TEXT: {cleaned_text[:500]}...")
        
        # CRITICAL FIX: Apply aggressive cleanup to remove JSON artifacts
        logging_util.info("JSON_BUG_FIX: Applying aggressive cleanup to remove JSON artifacts")
        
        # Try to extract narrative value one more time with more aggressive pattern
        narrative_match = NARRATIVE_PATTERN.search(cleaned_text)
        if narrative_match:
            cleaned_text = narrative_match.group(1)
            # Unescape JSON string escapes
            cleaned_text = cleaned_text.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
            logging_util.info("JSON_BUG_FIX: Successfully extracted narrative from JSON artifacts")
        else:
            # Final aggressive cleanup
            cleaned_text = JSON_STRUCTURE_PATTERN.sub('', cleaned_text)  # Remove braces and brackets
            cleaned_text = JSON_KEY_QUOTES_PATTERN.sub(r'\1:', cleaned_text)  # Remove quotes from keys
            cleaned_text = JSON_COMMA_SEPARATOR_PATTERN.sub('. ', cleaned_text)  # Replace JSON comma separators
            cleaned_text = cleaned_text.replace('\\n', '\n')  # Convert \n to actual newlines
            cleaned_text = cleaned_text.replace('\\"', '"')  # Unescape quotes
            cleaned_text = cleaned_text.replace('\\\\', '\\')  # Unescape backslashes
            cleaned_text = WHITESPACE_PATTERN.sub(' ', cleaned_text)  # Normalize spaces
            cleaned_text = cleaned_text.strip()
            logging_util.info("JSON_BUG_FIX: Applied aggressive cleanup to remove JSON structure")
        
        # Update the fallback response with cleaned text
        fallback_response = NarrativeResponse(
            narrative=cleaned_text,
            entities_mentioned=[],
            location_confirmed="Unknown"
        )
        
        logging_util.info(f"JSON_BUG_FIX: Final cleaned text: {cleaned_text[:200]}...")
    
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