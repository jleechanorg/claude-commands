from __future__ import annotations

import logging
import re
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

MONTH_MAP = {
    "hammer": 1,
    "alturiak": 2,
    "ches": 3,
    "tarsakh": 4,
    "mirtul": 5,
    "kythorn": 6,
    "flamerule": 7,
    "eleasis": 8,
    "eleint": 9,
    "marpenoth": 10,
    "uktar": 11,
    "nightal": 12,
    # Common abbreviations
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}

# Required fields for a valid world_time object
# These MUST all be present for temporal comparison to work correctly
REQUIRED_WORLD_TIME_FIELDS = frozenset(
    {
        "year",
        "month",
        "day",
        "hour",
        "minute",
        "second",
        "microsecond",
        "time_of_day",
    }
)


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _normalize_month(month_raw: Any) -> int:
    if isinstance(month_raw, str):
        normalized_month = re.sub(r"[^a-z]", "", month_raw.strip().lower())
        mapped = MONTH_MAP.get(normalized_month)
        if mapped is not None:
            return mapped
    return _safe_int(month_raw)


def validate_world_time_completeness(
    world_time: dict[str, Any] | None,
) -> tuple[bool, set[str]]:
    """Check if world_time has all required fields.

    Args:
        world_time: The world_time dict to validate

    Returns:
        Tuple of (is_complete, missing_fields)
        - is_complete: True if all required fields present with non-None values
        - missing_fields: Set of field names that are missing or None
    """
    if not world_time or not isinstance(world_time, dict):
        return False, REQUIRED_WORLD_TIME_FIELDS.copy()

    missing = set()
    for field in REQUIRED_WORLD_TIME_FIELDS:
        if field not in world_time or world_time[field] is None:
            missing.add(field)

    return len(missing) == 0, missing


def complete_partial_world_time(
    partial_time: dict[str, Any],
    existing_time: dict[str, Any] | None,
) -> dict[str, Any]:
    """Complete a partial world_time by filling missing fields from existing state.

    When the LLM generates partial time data (e.g., only hour/minute), this function
    fills in the missing fields from the existing state to maintain temporal consistency.

    Args:
        partial_time: The incomplete world_time from LLM response
        existing_time: The current world_time from game state (source for missing fields)

    Returns:
        Complete world_time dict with all required fields filled
    """
    if partial_time is None or not isinstance(partial_time, dict):
        return partial_time

    completed = deepcopy(partial_time)

    # If we have existing time, use it to fill missing fields
    if existing_time and isinstance(existing_time, dict):
        for field in REQUIRED_WORLD_TIME_FIELDS:
            if (
                (field not in completed or completed[field] is None)
                and field in existing_time
                and existing_time[field] is not None
            ):
                completed[field] = existing_time[field]

    # Set defaults for any still-missing fields (fallback)
    defaults = {
        "year": 1492,  # Default Forgotten Realms year
        "month": 1,
        "day": 1,
        "hour": 12,
        "minute": 0,
        "second": 0,
        "microsecond": 0,
        "time_of_day": "Midday",
    }

    for field, default_value in defaults.items():
        if field not in completed or completed[field] is None:
            completed[field] = default_value

    return completed


def world_time_to_comparable(world_time: dict[str, Any] | None) -> tuple[int, ...]:
    """Convert world_time dict to comparable tuple (year, month, day, hour, min, sec, microsec)."""

    if not world_time or not isinstance(world_time, dict):
        return (0, 0, 0, 0, 0, 0, 0)

    year = _safe_int(world_time.get("year", 0))
    month = _normalize_month(world_time.get("month", 0))
    day = _safe_int(world_time.get("day", 0))
    hour = _safe_int(world_time.get("hour", 0))
    minute = _safe_int(world_time.get("minute", 0))
    second = _safe_int(world_time.get("second", 0))
    microsecond = _safe_int(world_time.get("microsecond", 0))

    return (year, month, day, hour, minute, second, microsecond)


def parse_timestamp_to_world_time(timestamp: Any) -> dict[str, int] | None:
    """Parse an ISO-like timestamp into a world_time dict.

    Timestamps with timezone offsets are normalized to UTC to keep temporal
    comparisons consistent regardless of source timezone.
    """

    if timestamp is None:
        return None

    ts_string = str(timestamp).strip()
    if not ts_string:
        return None

    normalized = ts_string[:-1] + "+00:00" if ts_string.endswith("Z") else ts_string

    try:
        parsed = datetime.fromisoformat(normalized)
    except (TypeError, ValueError):
        return None

    if parsed.tzinfo:
        parsed = parsed.astimezone(UTC)

    return {
        "year": parsed.year,
        "month": parsed.month,
        "day": parsed.day,
        "hour": parsed.hour,
        "minute": parsed.minute,
        "second": parsed.second,
        "microsecond": parsed.microsecond,
    }


def extract_world_time_from_response(llm_response: Any) -> dict[str, Any] | None:
    """Extract world_time from LLM response state_updates."""

    try:
        state_updates = (
            llm_response.get_state_updates()
            if hasattr(llm_response, "get_state_updates")
            else {}
        )
        world_data = state_updates.get("world_data", {})
        candidate_time = world_data.get("world_time")
        if isinstance(candidate_time, str):
            parsed_from_string = parse_timestamp_to_world_time(candidate_time)
            if parsed_from_string:
                return parsed_from_string
            candidate_time = None

        if not isinstance(candidate_time, dict) or not candidate_time:
            timestamp_raw = world_data.get("timestamp_iso") or world_data.get(
                "timestamp"
            )
            parsed_timestamp = parse_timestamp_to_world_time(timestamp_raw)
            if parsed_timestamp:
                return parsed_timestamp

        return candidate_time if isinstance(candidate_time, dict) else None
    except Exception:
        return None


def check_temporal_violation(
    old_time: dict[str, Any] | None, new_time: dict[str, Any] | None
) -> bool:
    """Return True if new_time moves backward compared to old_time."""

    if not old_time or not new_time:
        return False

    old_tuple = world_time_to_comparable(old_time)
    new_tuple = world_time_to_comparable(new_time)

    return new_tuple < old_tuple


def apply_timestamp_to_world_time(state_changes: dict[str, Any]) -> dict[str, Any]:
    """Populate world_time from timestamp fields when missing."""

    world_data = state_changes.get("world_data")
    if not isinstance(world_data, dict):
        return state_changes

    existing_time = world_data.get("world_time")
    if isinstance(existing_time, dict) and existing_time:
        return state_changes

    timestamp_raw = world_data.get("timestamp_iso") or world_data.get("timestamp")
    parsed = parse_timestamp_to_world_time(timestamp_raw)
    if parsed:
        world_data["world_time"] = parsed

    return state_changes


def format_world_time_for_prompt(world_time: dict[str, Any] | None) -> str:
    """Format world_time dict for human-readable prompt display."""

    if not world_time:
        return "Unknown"

    year = world_time.get("year", "????")
    month = world_time.get("month", "??")
    day = world_time.get("day", "??")
    try:
        hour = int(world_time.get("hour", 0))
        minute = int(world_time.get("minute", 0))
    except (ValueError, TypeError):
        hour, minute = 0, 0
    time_of_day = world_time.get("time_of_day", "")

    time_str = f"{hour:02d}:{minute:02d}"
    if time_of_day:
        time_str = f"{time_of_day} ({time_str})"

    return f"{year} DR, {month} {day}, {time_str}"


def _with_default_microsecond(world_time: dict[str, Any]) -> dict[str, Any]:
    updated = deepcopy(world_time)
    updated["microsecond"] = _safe_int(updated.get("microsecond", 0))
    return updated


def ensure_progressive_world_time(
    state_changes: dict[str, Any],
    *,
    is_god_mode: bool,
    existing_time: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Normalize world_time, completing partial data from existing state.

    The LLM is authoritative for timeline control. When the model supplies a
    timestamp string, we parse it; when it supplies a structured world_time, we
    normalize the microsecond field and complete any missing fields from the
    existing game state. If world_time is missing or empty, we leave it untouched.

    Args:
        state_changes: The state updates from LLM response
        is_god_mode: True if in god mode (bypasses validation)
        existing_time: Current world_time from game state (used to complete partial data)

    Returns:
        Updated state_changes with normalized world_time
    """
    logger = logging.getLogger(__name__)

    if is_god_mode:
        return state_changes

    world_data = state_changes.setdefault("world_data", {})
    candidate_time = world_data.get("world_time")

    if isinstance(candidate_time, str):
        parsed_str = parse_timestamp_to_world_time(candidate_time)
        if parsed_str:
            world_data["world_time"] = parsed_str
        else:
            world_data.pop("world_time", None)
        return state_changes

    if isinstance(candidate_time, dict):
        # Check for incomplete time data and complete from existing state
        is_complete, missing_fields = validate_world_time_completeness(candidate_time)

        if not is_complete:
            logger.warning(
                f"⚠️ INCOMPLETE_WORLD_TIME: LLM generated partial time data. "
                f"Missing fields: {sorted(missing_fields)}. "
                f"Completing from existing state."
            )
            candidate_time = complete_partial_world_time(candidate_time, existing_time)

        world_data["world_time"] = _with_default_microsecond(candidate_time)
        return state_changes

    # If the model omitted world_time entirely, leave it unchanged.
    world_data.pop("world_time", None)
    return state_changes
