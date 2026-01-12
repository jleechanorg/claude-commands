"""Helper functions for action_resolution/outcome_resolution handling.

Centralizes the logic for accessing and building action_resolution/outcome_resolution
fields across llm_response.py and world_logic.py to eliminate duplication.
"""

from typing import Any


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

    Adds both fields to the unified_response dict for API responses.
    Handles type coercion (ensures dict type) and None values (skips them).

    Args:
        structured_response: NarrativeResponse object or any object with action_resolution/outcome_resolution attributes
        unified_response: Dict to add fields to (modified in place)
    """
    if structured_response is None:
        return

    # Include action_resolution (primary field name)
    if hasattr(structured_response, "action_resolution"):
        action_resolution = getattr(structured_response, "action_resolution", None)
        if action_resolution is not None:
            unified_response["action_resolution"] = (
                action_resolution if isinstance(action_resolution, dict) else {}
            )

    # Keep outcome_resolution for backward compatibility
    if hasattr(structured_response, "outcome_resolution"):
        outcome_resolution = getattr(structured_response, "outcome_resolution", None)
        if outcome_resolution is not None:
            unified_response["outcome_resolution"] = (
                outcome_resolution if isinstance(outcome_resolution, dict) else {}
            )
