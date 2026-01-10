"""Utility helpers for extracting structured Gemini response fields."""

from __future__ import annotations

from typing import Any, TypeVar

from mvp_site import constants

T = TypeVar("T")


def _get_structured_attr(
    structured_response: Any,
    field_name: str,
    default: T,
    *,
    treat_falsy_as_default: bool = False,
) -> T:
    """Return a structured response attribute or a typed default.

    Gemini can omit fields entirely or explicitly set them to ``None``. We coerce
    ``None`` back to the supplied ``default`` so callers always receive the
    expected type (``str``/``list``/``dict``). ``getattr`` handles the case where
    the attribute does not exist; we only need to guard the ``None`` sentinel.
    """

    value = getattr(structured_response, field_name, default)
    if value is None or (treat_falsy_as_default and not value):
        return default
    return value


def extract_structured_fields(gemini_response_obj: Any) -> dict[str, Any]:
    """Extract structured fields from a LLMResponse-like object."""

    structured_fields: dict[str, Any] = {}

    sr = getattr(gemini_response_obj, "structured_response", None)
    if sr:
        structured_fields = {
            constants.FIELD_SESSION_HEADER: _get_structured_attr(
                sr, constants.FIELD_SESSION_HEADER, ""
            ),
            constants.FIELD_PLANNING_BLOCK: _get_structured_attr(
                sr, constants.FIELD_PLANNING_BLOCK, ""
            ),
            constants.FIELD_DICE_ROLLS: _get_structured_attr(
                sr, constants.FIELD_DICE_ROLLS, []
            ),
            constants.FIELD_DICE_AUDIT_EVENTS: _get_structured_attr(
                sr, constants.FIELD_DICE_AUDIT_EVENTS, []
            ),
            # FIELD_RESOURCES is consumed downstream by Firestore writes which
            # expect a mapping. Returning ``{}`` keeps backwards compatibility
            # with earlier schemas that defaulted to a dict-like payload.
            constants.FIELD_RESOURCES: _get_structured_attr(
                sr, constants.FIELD_RESOURCES, {}, treat_falsy_as_default=True
            ),
            constants.FIELD_DEBUG_INFO: _get_structured_attr(
                sr, constants.FIELD_DEBUG_INFO, {}
            ),
            constants.FIELD_GOD_MODE_RESPONSE: _get_structured_attr(
                sr, constants.FIELD_GOD_MODE_RESPONSE, ""
            ),
            constants.FIELD_DIRECTIVES: _get_structured_attr(
                sr, constants.FIELD_DIRECTIVES, {}
            ),
        }

        # Store a filtered subset of state_updates needed for Living World UI
        # This keeps storage small while still surfacing relevant debug data
        state_updates: dict[str, Any] = _get_structured_attr(
            sr, constants.FIELD_STATE_UPDATES, {}
        )
        if isinstance(state_updates, dict):
            allowed_keys = {
                "world_events",
                "faction_updates",
                "time_events",
                "rumors",
                "scene_event",
                "complications",
            }
            filtered_state_updates = {
                key: value
                for key, value in state_updates.items()
                if key in allowed_keys and value not in (None, {}, [])
            }

            if filtered_state_updates:
                structured_fields[constants.FIELD_STATE_UPDATES] = (
                    filtered_state_updates
                )

            world_events = filtered_state_updates.get("world_events")
            if world_events and isinstance(world_events, dict):
                structured_fields["world_events"] = world_events

            # BEAD W2-7m1: Also check for world_events nested inside custom_campaign_state
            # The LLM sometimes incorrectly nests world_events here instead of at top-level.
            # Extract it to prevent split storage between correct and incorrect locations.
            if not world_events or not isinstance(world_events, dict):
                custom_state = state_updates.get("custom_campaign_state", {})
                if isinstance(custom_state, dict):
                    nested_world_events = custom_state.get("world_events")
                    if nested_world_events and isinstance(nested_world_events, dict):
                        structured_fields["world_events"] = nested_world_events
                        # Also add to filtered_state_updates for consistency
                        if constants.FIELD_STATE_UPDATES in structured_fields:
                            structured_fields[constants.FIELD_STATE_UPDATES][
                                "world_events"
                            ] = nested_world_events
                        else:
                            structured_fields[constants.FIELD_STATE_UPDATES] = {
                                "world_events": nested_world_events
                            }

    return structured_fields
