from __future__ import annotations

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
    """Return True if new_time is backward or equal to old_time."""

    if not old_time or not new_time:
        return False

    old_tuple = world_time_to_comparable(old_time)
    new_tuple = world_time_to_comparable(new_time)

    return new_tuple <= old_tuple


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
) -> dict[str, Any]:
    """Normalize world_time without inferring or advancing time.

    The LLM is authoritative for timeline control. When the model supplies a
    timestamp string, we parse it; when it supplies a structured world_time, we
    normalize the microsecond field. If world_time is missing or empty, we leave
    it untouched.
    """

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
        world_data["world_time"] = _with_default_microsecond(candidate_time)
        return state_changes

    # If the model omitted world_time entirely, leave it unchanged.
    world_data.pop("world_time", None)
    return state_changes
