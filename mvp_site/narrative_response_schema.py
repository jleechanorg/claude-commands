"""
Simplified structured narrative generation schemas
Based on Milestone 0.4 Combined approach implementation (without pydantic dependency)
"""

import json
import re
from typing import Any

from mvp_site import logging_util
from mvp_site.json_utils import unescape_json_string
from mvp_site.robust_json_parser import parse_llm_json_response

# Planning block extraction from narrative is deprecated - blocks should only come from JSON

# Precompiled regex patterns for better performance
JSON_MARKDOWN_PATTERN = re.compile(r"```json\s*\n?(.*?)\n?```", re.DOTALL)
GENERIC_MARKDOWN_PATTERN = re.compile(r"```\s*\n?(.*?)\n?```", re.DOTALL)
NARRATIVE_PATTERN = re.compile(r'"narrative"\s*:\s*"([^"]*(?:\\.[^"]*)*)"')

# JSON cleanup patterns
JSON_STRUCTURE_PATTERN = re.compile(r"[{}\[\]]")
JSON_KEY_QUOTES_PATTERN = re.compile(r'"([^"]+)":')
JSON_COMMA_SEPARATOR_PATTERN = re.compile(r'",\s*"')
WHITESPACE_PATTERN = re.compile(
    r"[^\S\r\n]+"
)  # Normalize spaces while preserving line breaks


class NarrativeResponse:
    """Schema for structured narrative generation response"""

    def __init__(
        self,
        narrative: str,
        entities_mentioned: list[str] = None,
        location_confirmed: str = "Unknown",
        turn_summary: str = None,
        state_updates: dict[str, Any] = None,
        debug_info: dict[str, Any] = None,
        god_mode_response: str = None,
        session_header: str = None,
        planning_block: str = None,
        dice_rolls: list[str] = None,
        resources: str = None,
        **kwargs,
    ):
        # Core required fields
        self.narrative = self._validate_narrative(narrative)
        self.entities_mentioned = self._validate_entities(entities_mentioned or [])
        self.location_confirmed = location_confirmed or "Unknown"
        self.turn_summary = turn_summary
        self.state_updates = self._validate_state_updates(state_updates)
        self.debug_info = self._validate_debug_info(debug_info)
        self.god_mode_response = god_mode_response

        # New always-visible fields
        self.session_header = self._validate_string_field(
            session_header, "session_header"
        )
        self.planning_block = self._validate_planning_block(planning_block)
        self.dice_rolls = self._validate_list_field(dice_rolls, "dice_rolls")
        self.resources = self._validate_string_field(resources, "resources")

        # Store any extra fields that Gemini might include (shouldn't be any now)
        self.extra_fields = kwargs

    def _validate_narrative(self, narrative: str) -> str:
        """Validate narrative content"""
        if not isinstance(narrative, str):
            raise ValueError("Narrative must be a string")

        return narrative.strip()

    def _validate_entities(self, entities: list[str]) -> list[str]:
        """Validate and clean entity list"""
        if not isinstance(entities, list):
            raise ValueError("Entities must be a list")

        return [str(entity).strip() for entity in entities if str(entity).strip()]

    def _validate_state_updates(self, state_updates: Any) -> dict[str, Any]:
        """Validate and clean state updates"""
        if state_updates is None:
            return {}

        if not isinstance(state_updates, dict):
            logging_util.warning(
                f"Invalid state_updates type: {type(state_updates).__name__}, expected dict. Using empty dict instead."
            )
            return {}

        return state_updates

    def _validate_debug_info(self, debug_info: Any) -> dict[str, Any]:
        """Validate and clean debug info"""
        if debug_info is None:
            return {}

        if not isinstance(debug_info, dict):
            logging_util.warning(
                f"Invalid debug_info type: {type(debug_info).__name__}, expected dict. Using empty dict instead."
            )
            return {}

        return debug_info

    def _validate_string_field(self, value: Any, field_name: str) -> str:
        """Validate a string field with null/type checking"""
        if value is None:
            return ""

        if not isinstance(value, str):
            logging_util.warning(
                f"Invalid {field_name} type: {type(value).__name__}, expected str. Converting to string."
            )
            try:
                return str(value)
            except Exception as e:
                logging_util.error(f"Failed to convert {field_name} to string: {e}")
                return ""

        return value

    def _validate_list_field(self, value: Any, field_name: str) -> list[str]:
        """Validate a list field with null/type checking"""
        if value is None:
            return []

        if not isinstance(value, list):
            logging_util.warning(
                f"Invalid {field_name} type: {type(value).__name__}, expected list. Using empty list."
            )
            return []

        # Convert all items to strings
        validated_list = []
        for item in value:
            if item is not None:
                try:
                    validated_list.append(str(item))
                except Exception as e:
                    logging_util.warning(
                        f"Failed to convert {field_name} item to string: {e}"
                    )

        return validated_list

    def _validate_planning_block(self, planning_block: Any) -> dict[str, Any]:
        """Validate planning block content - JSON ONLY format"""
        if planning_block is None:
            return {}

        # JSON format - ONLY supported format
        if isinstance(planning_block, dict):
            return self._validate_planning_block_json(planning_block)

        # String format - NO LONGER SUPPORTED
        if isinstance(planning_block, str):
            logging_util.error(
                f"❌ STRING PLANNING BLOCKS NO LONGER SUPPORTED: String planning blocks are deprecated. Only JSON format is allowed. Received: {planning_block[:100]}..."
            )
            return {}

        # Invalid type - reject
        logging_util.error(
            f"❌ INVALID PLANNING BLOCK TYPE: Expected dict (JSON object), got {type(planning_block).__name__}. Planning blocks must be JSON objects with 'thinking' and 'choices' fields."
        )
        return {}

    def _validate_planning_block_json(
        self, planning_block: dict[str, Any]
    ) -> dict[str, Any]:
        """Validate JSON-format planning block structure"""
        validated = {}

        # Validate thinking field
        thinking = planning_block.get("thinking", "")
        if not isinstance(thinking, str):
            thinking = str(thinking) if thinking is not None else ""
        validated["thinking"] = thinking

        # Validate optional context field
        context = planning_block.get("context", "")
        if not isinstance(context, str):
            context = str(context) if context is not None else ""
        validated["context"] = context

        # Validate choices object
        choices = planning_block.get("choices", {})
        if not isinstance(choices, dict):
            logging_util.warning("Planning block choices must be a dict object")
            choices = {}

        validated_choices = {}
        for choice_key, choice_data in choices.items():
            # Validate choice key format (snake_case, allowing god: prefix)
            if not re.match(r"^(god:)?[a-zA-Z_][a-zA-Z0-9_]*$", choice_key):
                logging_util.warning(
                    f"Choice key '{choice_key}' is not a valid identifier, skipping"
                )
                continue

            # Validate choice data structure
            if not isinstance(choice_data, dict):
                logging_util.warning(
                    f"Choice '{choice_key}' data must be a dict, skipping"
                )
                continue

            validated_choice = {}

            # Required: text field
            text = choice_data.get("text", "")
            if not isinstance(text, str):
                text = str(text) if text is not None else ""
            validated_choice["text"] = text

            # Required: description field
            description = choice_data.get("description", "")
            if not isinstance(description, str):
                description = str(description) if description is not None else ""
            validated_choice["description"] = description

            # Optional: risk_level field
            risk_level = choice_data.get("risk_level", "low")
            if risk_level not in ["safe", "low", "medium", "high"]:
                risk_level = "low"
            validated_choice["risk_level"] = risk_level

            # Optional: analysis field (for deep think blocks)
            if "analysis" in choice_data:
                analysis = choice_data["analysis"]
                if isinstance(analysis, dict):
                    validated_choice["analysis"] = analysis

            # Only add choice if it has both text and description
            if validated_choice["text"] and validated_choice["description"]:
                validated_choices[choice_key] = validated_choice
            else:
                logging_util.warning(
                    f"Choice '{choice_key}' missing required text or description, skipping"
                )

        validated["choices"] = validated_choices

        # Security check - sanitize any HTML/script content
        return self._sanitize_planning_block_content(validated)

    def _sanitize_planning_block_content(
        self, planning_block: dict[str, Any]
    ) -> dict[str, Any]:
        """Validate planning block content - remove dangerous scripts but preserve normal text"""

        def sanitize_string(value: str) -> str:
            """Remove dangerous script tags but preserve normal apostrophes and quotes"""
            if not isinstance(value, str):
                return str(value)

            # Only remove actual script tags and dangerous HTML
            # Don't escape normal apostrophes and quotes since frontend handles display
            dangerous_patterns = [
                r"<script[^>]*>.*?</script>",
                r"<iframe[^>]*>.*?</iframe>",
                r"<img[^>]*>",  # Remove all img tags (can have malicious attributes)
                r"javascript:",
                r"on\w+\s*=.*?[\s>]",  # event handlers like onclick= onerror=
            ]

            cleaned = value
            for pattern in dangerous_patterns:
                cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE | re.DOTALL)

            return cleaned

        sanitized = {}

        # Sanitize thinking
        sanitized["thinking"] = sanitize_string(planning_block.get("thinking", ""))

        # Sanitize context
        if "context" in planning_block:
            sanitized["context"] = sanitize_string(planning_block["context"])

        # Sanitize choices
        sanitized_choices = {}
        for choice_key, choice_data in planning_block.get("choices", {}).items():
            sanitized_choice = {}
            sanitized_choice["text"] = sanitize_string(choice_data.get("text", ""))
            sanitized_choice["description"] = sanitize_string(
                choice_data.get("description", "")
            )
            sanitized_choice["risk_level"] = choice_data.get("risk_level", "low")

            # Keep analysis if present (but sanitize strings within it)
            if "analysis" in choice_data:
                analysis = choice_data["analysis"]
                if isinstance(analysis, dict):
                    sanitized_analysis = {}
                    for key, value in analysis.items():
                        if isinstance(value, str):
                            sanitized_analysis[key] = sanitize_string(value)
                        elif isinstance(value, list):
                            sanitized_analysis[key] = [
                                sanitize_string(item) if isinstance(item, str) else item
                                for item in value
                            ]
                        else:
                            sanitized_analysis[key] = value
                    sanitized_choice["analysis"] = sanitized_analysis

            sanitized_choices[choice_key] = sanitized_choice

        sanitized["choices"] = sanitized_choices

        return sanitized

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        result = {
            "narrative": self.narrative,
            "entities_mentioned": self.entities_mentioned,
            "location_confirmed": self.location_confirmed,
            "turn_summary": self.turn_summary,
            "state_updates": self.state_updates,
            "debug_info": self.debug_info,
            "session_header": self.session_header,
            "planning_block": self.planning_block,
            "dice_rolls": self.dice_rolls,
            "resources": self.resources,
        }

        # Include god_mode_response if present
        if self.god_mode_response:
            result["god_mode_response"] = self.god_mode_response

        return result


class EntityTrackingInstruction:
    """Schema for entity tracking instructions to be injected into prompts"""

    def __init__(
        self, scene_manifest: str, expected_entities: list[str], response_format: str
    ):
        self.scene_manifest = scene_manifest
        self.expected_entities = expected_entities
        self.response_format = response_format

    @classmethod
    def create_from_manifest(
        cls, manifest_text: str, expected_entities: list[str]
    ) -> "EntityTrackingInstruction":
        """Create entity tracking instruction from manifest"""
        response_format = {
            "narrative": "Your narrative text here...",
            "entities_mentioned": expected_entities,
            "location_confirmed": "The current location name",
            "state_updates": {
                "player_character_data": {"hp_current": "updated value if changed"},
                "npc_data": {"npc_name": {"status": "updated status"}},
                "world_data": {"current_location": "if moved"},
                "custom_campaign_state": {"any": "custom updates"},
            },
        }

        response_format_str = json.dumps(response_format, indent=2)

        return cls(
            scene_manifest=manifest_text,
            expected_entities=expected_entities,
            response_format=response_format_str,
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


def _combine_god_mode_and_narrative(
    god_mode_response: str, narrative: str | None
) -> str:
    """
    Helper function to handle god_mode_response and narrative fields.

    Rules:
    - If BOTH present: return only narrative (god_mode_response shown separately in structured fields)
    - If ONLY god_mode_response: return god_mode_response (also shown in structured fields)
    - If ONLY narrative: return narrative

    Args:
        god_mode_response: The god mode response text
        narrative: Optional narrative text

    Returns:
        Main story text for display
    """
    # If both are present, return only narrative (avoid duplication)
    if narrative and narrative.strip() and god_mode_response:
        return narrative
    # If only narrative, return it
    if narrative and narrative.strip():
        return narrative
    # If only god_mode_response, return it
    if god_mode_response:
        return god_mode_response
    # If neither, return empty string
    return ""


def parse_structured_response(response_text: str) -> tuple[str, NarrativeResponse]:
    """
    Parse structured response and check for JSON bug issues.
    """
    """
    Parse structured JSON response from LLM

    Returns:
        tuple: (narrative_text, parsed_response_or_none)
    """
    if not response_text:
        empty_response = NarrativeResponse(
            narrative="The story awaits your input...",  # Default narrative for empty response
            entities_mentioned=[],
            location_confirmed="Unknown",
        )
        return empty_response.narrative, empty_response

    # First check if the JSON is wrapped in markdown code blocks
    json_content = response_text

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
            if content.startswith("{") and content.endswith("}"):
                json_content = content
                logging_util.info("Extracted JSON from generic code block")

    # Use the robust parser on the extracted content
    parsed_data, was_incomplete = parse_llm_json_response(json_content)

    if was_incomplete:
        narrative_len = len(parsed_data.get("narrative", "")) if parsed_data else 0
        token_count = narrative_len // 4  # Rough estimate
        logging_util.info(
            f"Recovered from incomplete JSON response. Narrative length: {narrative_len} characters (~{token_count} tokens)"
        )

    # Create NarrativeResponse from parsed data

    if parsed_data:
        try:
            # Planning blocks should only come from JSON field, not extracted from narrative
            narrative = parsed_data.get("narrative", "")
            planning_block = parsed_data.get("planning_block", "")

            validated_response = NarrativeResponse(**parsed_data)
            # If god_mode_response is present, return both god mode response and narrative
            if (
                hasattr(validated_response, "god_mode_response")
                and validated_response.god_mode_response
            ):
                combined_response = _combine_god_mode_and_narrative(
                    validated_response.god_mode_response, validated_response.narrative
                )
                return combined_response, validated_response
            return validated_response.narrative, validated_response

        except (ValueError, TypeError):
            # NarrativeResponse creation failed
            # Check for god_mode_response first
            god_mode_response = parsed_data.get("god_mode_response")
            if god_mode_response:
                # For god mode, combine god_mode_response with narrative if both exist
                narrative = parsed_data.get("narrative")
                # Handle null narrative
                if narrative is None:
                    narrative = ""
                combined_response = _combine_god_mode_and_narrative(
                    god_mode_response, narrative
                )

                known_fields = {
                    "narrative": narrative,
                    "god_mode_response": god_mode_response,
                    "entities_mentioned": parsed_data.get("entities_mentioned", []),
                    "location_confirmed": parsed_data.get("location_confirmed")
                    or "Unknown",
                    "state_updates": parsed_data.get("state_updates", {}),
                    "debug_info": parsed_data.get("debug_info", {}),
                }
                # Pass any other fields as kwargs
                extra_fields = {
                    k: v for k, v in parsed_data.items() if k not in known_fields
                }
                fallback_response = NarrativeResponse(**known_fields, **extra_fields)
                return combined_response, fallback_response

            # Return the narrative if we at least got that
            narrative = parsed_data.get("narrative")
            # Handle null or missing narrative - use empty string instead of raw JSON
            if narrative is None:
                narrative = ""

            # Planning blocks should only come from JSON field
            planning_block = parsed_data.get("planning_block", "")

            # Extract only the fields we know about, let **kwargs handle the rest
            known_fields = {
                "narrative": narrative,
                "entities_mentioned": parsed_data.get("entities_mentioned", []),
                "location_confirmed": parsed_data.get("location_confirmed")
                or "Unknown",
                "state_updates": parsed_data.get("state_updates", {}),
                "debug_info": parsed_data.get("debug_info", {}),
                "planning_block": planning_block,
            }
            # Pass any other fields as kwargs
            extra_fields = {
                k: v
                for k, v in parsed_data.items()
                if k not in known_fields and k != "planning_block"
            }
            fallback_response = NarrativeResponse(**known_fields, **extra_fields)
            return narrative, fallback_response

    # Additional mitigation: Try to extract narrative from raw JSON-like text
    # This handles cases where JSON wasn't properly parsed but contains "narrative": "..."
    narrative_match = NARRATIVE_PATTERN.search(response_text)

    if narrative_match:
        extracted_narrative = narrative_match.group(1)
        # Properly unescape JSON string escapes
        extracted_narrative = unescape_json_string(extracted_narrative)
        logging_util.info("Extracted narrative from JSON-like text pattern")

        fallback_response = NarrativeResponse(
            narrative=extracted_narrative,
            entities_mentioned=[],
            location_confirmed="Unknown",
        )
        return extracted_narrative, fallback_response

    # Final fallback: Clean up raw text for display
    # Remove JSON-like structures and format for readability
    cleaned_text = response_text

    # Safer approach: Only clean if it's clearly malformed JSON
    # Check multiple indicators to avoid corrupting valid narrative text
    is_likely_json = (
        "{" in cleaned_text
        and '"' in cleaned_text
        and (
            cleaned_text.strip().startswith("{") or cleaned_text.strip().startswith('"')
        )
        and (cleaned_text.strip().endswith("}") or cleaned_text.strip().endswith('"'))
        and cleaned_text.count('"') >= 4  # At least 2 key-value pairs
    )

    if is_likely_json:
        # Apply cleanup only to confirmed JSON-like text
        # First, try to extract just the narrative value if possible
        if '"narrative"' in cleaned_text:
            # Try to extract narrative value safely
            narrative_match = NARRATIVE_PATTERN.search(cleaned_text)
            if narrative_match:
                cleaned_text = narrative_match.group(1)
                # Unescape JSON string escapes
                cleaned_text = (
                    cleaned_text.replace("\\n", "\n")
                    .replace('\\"', '"')
                    .replace("\\\\", "\\")
                )
                logging_util.info("Extracted narrative from JSON structure")
            else:
                # Fallback to aggressive cleanup only as last resort
                cleaned_text = JSON_STRUCTURE_PATTERN.sub(
                    "", cleaned_text
                )  # Remove braces and brackets
                cleaned_text = JSON_KEY_QUOTES_PATTERN.sub(
                    r"\1:", cleaned_text
                )  # Remove quotes from keys
                cleaned_text = JSON_COMMA_SEPARATOR_PATTERN.sub(
                    ". ", cleaned_text
                )  # Replace JSON comma separators
                cleaned_text = cleaned_text.replace(
                    "\\n", "\n"
                )  # Convert \n to actual newlines
                cleaned_text = cleaned_text.replace('\\"', '"')  # Unescape quotes
                cleaned_text = cleaned_text.replace(
                    "\\\\", "\\"
                )  # Unescape backslashes
                cleaned_text = WHITESPACE_PATTERN.sub(
                    " ", cleaned_text
                )  # Normalize spaces while preserving line breaks
                cleaned_text = cleaned_text.strip()
                logging_util.warning("Applied aggressive cleanup to malformed JSON")
        else:
            # No narrative field found, apply minimal cleanup
            cleaned_text = (
                cleaned_text.replace("\\n", "\n")
                .replace('\\"', '"')
                .replace("\\\\", "\\")
            )
            logging_util.warning(
                "Applied minimal cleanup to JSON-like text without narrative field"
            )

    # Final fallback response

    fallback_response = NarrativeResponse(
        narrative=cleaned_text, entities_mentioned=[], location_confirmed="Unknown"
    )

    # Final check for JSON artifacts in returned text
    if '"narrative":' in cleaned_text or '"god_mode_response":' in cleaned_text:
        # Try to extract narrative value one more time with more aggressive pattern
        narrative_match = NARRATIVE_PATTERN.search(cleaned_text)
        if narrative_match:
            cleaned_text = narrative_match.group(1)
            # Unescape JSON string escapes
            cleaned_text = (
                cleaned_text.replace("\\n", "\n")
                .replace('\\"', '"')
                .replace("\\\\", "\\")
            )
        else:
            # Final aggressive cleanup
            cleaned_text = JSON_STRUCTURE_PATTERN.sub(
                "", cleaned_text
            )  # Remove braces and brackets
            cleaned_text = JSON_KEY_QUOTES_PATTERN.sub(
                r"\1:", cleaned_text
            )  # Remove quotes from keys
            cleaned_text = JSON_COMMA_SEPARATOR_PATTERN.sub(
                ". ", cleaned_text
            )  # Replace JSON comma separators
            cleaned_text = cleaned_text.replace(
                "\\n", "\n"
            )  # Convert \n to actual newlines
            cleaned_text = cleaned_text.replace('\\"', '"')  # Unescape quotes
            cleaned_text = cleaned_text.replace("\\\\", "\\")  # Unescape backslashes
            cleaned_text = WHITESPACE_PATTERN.sub(" ", cleaned_text)  # Normalize spaces
            cleaned_text = cleaned_text.strip()

        # Update the fallback response with cleaned text
        fallback_response = NarrativeResponse(
            narrative=cleaned_text, entities_mentioned=[], location_confirmed="Unknown"
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


def create_structured_prompt_injection(
    manifest_text: str, expected_entities: list[str]
) -> str:
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
        instruction = EntityTrackingInstruction.create_from_manifest(
            manifest_text, expected_entities
        )
        return instruction.to_prompt_injection()
    # Use generic JSON response format when no entities (e.g., character creation)
    return create_generic_json_instruction()


def validate_entity_coverage(
    response: NarrativeResponse, expected_entities: list[str]
) -> dict[str, Any]:
    """
    Validate that the structured response covers all expected entities

    Returns:
        Dict with validation results
    """
    mentioned_entities = {entity.lower() for entity in response.entities_mentioned}
    expected_entities_lower = {entity.lower() for entity in expected_entities}

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
        "coverage_rate": len(narrative_mentions) / len(expected_entities)
        if expected_entities
        else 1.0,
        "entities_mentioned_count": len(response.entities_mentioned),
        "expected_entities_count": len(expected_entities),
    }
