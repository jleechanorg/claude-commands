"""Helper functions for action_resolution/outcome_resolution handling.

Centralizes the logic for accessing and building action_resolution/outcome_resolution
fields across llm_response.py and world_logic.py to eliminate duplication.
"""

import json
from typing import Any


def extract_dice_rolls_from_action_resolution(action_resolution: dict[str, Any]) -> list[str]:
    """Extract and format dice rolls from action_resolution.mechanics.rolls.
    
    Converts structured roll objects from action_resolution.mechanics.rolls
    into formatted strings for the legacy dice_rolls field (for UI display).
    
    Format: "notation = result (purpose)" or "notation = result vs DC dc - Success/Failure (purpose)"
    
    Args:
        action_resolution: action_resolution dict (may be empty)
        
    Returns:
        list[str]: Formatted dice roll strings, empty list if no rolls found
    """
    if not action_resolution or not isinstance(action_resolution, dict):
        return []
    
    mechanics = action_resolution.get("mechanics", {})
    if not isinstance(mechanics, dict):
        return []
    
    rolls = mechanics.get("rolls", [])
    if not isinstance(rolls, list):
        return []
    
    formatted_rolls = []
    for roll in rolls:
        if not isinstance(roll, dict):
            continue
        
        notation = roll.get("notation", "")
        result = roll.get("result")
        purpose = roll.get("purpose", "")
        dc = roll.get("dc")
        success = roll.get("success")
        
        if not notation or result is None:
            continue
        
        # Format: "notation = result (purpose)"
        roll_str = f"{notation} = {result}"
        
        # Add DC and success/failure if present
        if dc is not None:
            roll_str += f" vs DC {dc}"
            if success is True:
                roll_str += " - Success"
            elif success is False:
                roll_str += " - Failure"
        
        # Add purpose if present
        if purpose:
            roll_str += f" ({purpose})"
        
        formatted_rolls.append(roll_str)
    
    return formatted_rolls


def extract_dice_audit_events_from_action_resolution(action_resolution: dict[str, Any]) -> list[str]:
    """Extract audit events from action_resolution.mechanics.audit_events.
    
    Args:
        action_resolution: action_resolution dict (may be empty)
        
    Returns:
        list[str]: Audit event strings, empty list if none found
    """
    if not action_resolution or not isinstance(action_resolution, dict):
        return []
    
    mechanics = action_resolution.get("mechanics", {})
    if not isinstance(mechanics, dict):
        return []
    
    audit_events = mechanics.get("audit_events", [])
    if not isinstance(audit_events, list):
        return []
    
    # Convert all audit events to strings
    formatted_events = []
    for event in audit_events:
        if isinstance(event, str):
            formatted_events.append(event)
        elif isinstance(event, dict):
            # Serialize dict to JSON for stable, readable output
            formatted_events.append(json.dumps(event, ensure_ascii=False, default=str))
    
    return formatted_events


def get_action_resolution(structured_response: Any) -> dict[str, Any]:
    """Get action_resolution from structured response with backward compat fallback.

    Checks action_resolution first (new field), falls back to outcome_resolution
    (legacy field) for backward compatibility.

    Args:
        structured_response: NarrativeResponse object or any object with action_resolution/outcome_resolution attributes

    Returns:
        dict: action_resolution dict, or empty dict if neither field present
    """
    if structured_response is None:
        return {}

    # Check action_resolution first (new field)
    if hasattr(structured_response, "action_resolution"):
        ar = structured_response.action_resolution
        # Use is not None to preserve empty dict {} as present
        if ar is not None:
            return ar

    # Fall back to outcome_resolution for backward compatibility
    if hasattr(structured_response, "outcome_resolution"):
        or_val = structured_response.outcome_resolution
        if or_val is not None:
            return or_val

    return {}


def get_outcome_resolution(structured_response: Any) -> dict[str, Any]:
    """Get outcome_resolution from structured response (backward compat accessor).

    Direct accessor for outcome_resolution field. Returns empty dict if not present.

    Args:
        structured_response: NarrativeResponse object or any object with outcome_resolution attribute

    Returns:
        dict: outcome_resolution dict, or empty dict if not present
    """
    if structured_response is None:
        return {}

    if hasattr(structured_response, "outcome_resolution"):
        or_val = structured_response.outcome_resolution
        return or_val or {}

    return {}


def add_action_resolution_to_response(
    structured_response: Any, unified_response: dict[str, Any]
) -> None:
    """Add action_resolution and outcome_resolution to unified_response dict.
    
    Also extracts dice_rolls and dice_audit_events from action_resolution.mechanics
    and populates the legacy fields for UI backward compatibility.

    Adds both fields to the unified_response dict for API responses.
    Handles type coercion (ensures dict type) and None values (skips them).

    Args:
        structured_response: NarrativeResponse object or any object with action_resolution/outcome_resolution attributes
        unified_response: Dict to add fields to (modified in place)
    """
    if structured_response is None:
        return

    # Include action_resolution (primary field name)
    action_resolution_dict = None
    if hasattr(structured_response, "action_resolution"):
        action_resolution = getattr(structured_response, "action_resolution", None)
        if action_resolution is not None:
            action_resolution_dict = (
                action_resolution if isinstance(action_resolution, dict) else {}
            )
            unified_response["action_resolution"] = action_resolution_dict

    # Keep outcome_resolution for backward compatibility
    if hasattr(structured_response, "outcome_resolution"):
        outcome_resolution = getattr(structured_response, "outcome_resolution", None)
        if outcome_resolution is not None:
            unified_response["outcome_resolution"] = (
                outcome_resolution if isinstance(outcome_resolution, dict) else {}
            )
            # Also try to extract from outcome_resolution if action_resolution not present
            if action_resolution_dict is None:
                action_resolution_dict = (
                    outcome_resolution if isinstance(outcome_resolution, dict) else {}
                )

    # Extract dice_rolls from action_resolution.mechanics.rolls
    # This ensures UI backward compatibility - dice_rolls field is populated automatically
    # Priority: Always prefer extracted rolls from action_resolution (single source of truth)
    if action_resolution_dict:
        extracted_rolls = extract_dice_rolls_from_action_resolution(action_resolution_dict)
        if extracted_rolls:
            # Always use extracted rolls when available (they're from the single source of truth)
            # This overrides any existing dice_rolls for consistency
            unified_response["dice_rolls"] = extracted_rolls
    
    # Extract dice_audit_events from action_resolution.mechanics.audit_events
    if action_resolution_dict:
        extracted_events = extract_dice_audit_events_from_action_resolution(action_resolution_dict)
        if extracted_events:
            # Always use extracted events when available (they're from the single source of truth)
            # This overrides any existing dice_audit_events for consistency
            unified_response["dice_audit_events"] = extracted_events
