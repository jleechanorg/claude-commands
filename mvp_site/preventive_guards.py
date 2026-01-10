from __future__ import annotations

from copy import deepcopy
from typing import Any

from mvp_site import constants
from mvp_site.game_state import GameState
from mvp_site.llm_response import LLMResponse
from mvp_site.memory_utils import (
    AUTO_MEMORY_MAX_LENGTH,
    AUTO_MEMORY_PREFIX,
    is_duplicate_memory,
)


def enforce_preventive_guards(
    game_state: GameState, llm_response: LLMResponse, mode: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Harden structured responses to prevent backtracking without surfacing errors.

    Returns a tuple of (state_changes, extras) where ``state_changes`` is a
    defensive copy of the model-provided updates augmented with continuity
    safeguards, and ``extras`` contains auxiliary values (e.g., synthesized
    ``god_mode_response``) that should be added to the unified response and
    stored structured fields.
    """

    extras: dict[str, Any] = {}

    _fill_god_mode_response(mode, llm_response, extras)

    metadata = getattr(llm_response, "processing_metadata", {}) or {}
    if metadata.get("item_exploit_blocked"):
        return {}, extras

    state_changes: dict[str, Any] = deepcopy(llm_response.get_state_updates())

    dice_rolls = getattr(llm_response, "dice_rolls", [])
    resources = getattr(llm_response, "resources", "")

    if dice_rolls or resources:
        _ensure_world_time(state_changes, game_state)
        _ensure_core_memory(state_changes, llm_response.narrative_text)

    _ensure_location_progress(state_changes, llm_response, game_state)

    if resources:
        _ensure_resource_checkpoint(state_changes, resources)

    # Persist dm_notes from debug_info to state so they survive across turns
    _ensure_dm_notes_persistence(state_changes, llm_response, game_state)

    return state_changes, extras


def _fill_god_mode_response(
    mode: str, llm_response: LLMResponse, extras: dict[str, Any]
) -> None:
    structured = getattr(llm_response, "structured_response", None)
    existing = getattr(structured, constants.FIELD_GOD_MODE_RESPONSE, None)
    if mode == constants.MODE_GOD and not existing:
        extras[constants.FIELD_GOD_MODE_RESPONSE] = llm_response.narrative_text


def _ensure_world_time(state_changes: dict[str, Any], game_state: GameState) -> None:
    world_data = state_changes.setdefault("world_data", {})
    world_time = world_data.get("world_time")
    if isinstance(world_time, dict) and world_time and "hour" in world_time:
        return

    existing = game_state.world_data.get("world_time")
    if isinstance(existing, dict) and existing:
        world_data["world_time"] = deepcopy(existing)
    else:
        world_data["world_time"] = {"hour": 12, "minute": 0, "time_of_day": "day"}


def _ensure_core_memory(state_changes: dict[str, Any], narrative: str) -> None:
    custom_state = state_changes.setdefault("custom_campaign_state", {})
    core_memories = custom_state.get("core_memories")
    if not isinstance(core_memories, list):
        core_memories = []
    snippet = narrative.strip()
    if snippet:
        entry = f"{AUTO_MEMORY_PREFIX} {snippet}"[:AUTO_MEMORY_MAX_LENGTH]
        # Check for duplicates or near-duplicates using centralized logic
        if not is_duplicate_memory(entry, core_memories):
            core_memories.append(entry)
    custom_state["core_memories"] = core_memories


def _ensure_location_progress(
    state_changes: dict[str, Any],
    llm_response: LLMResponse,
    game_state: GameState,
) -> None:
    location = llm_response.get_location_confirmed()
    world_data = state_changes.setdefault("world_data", {})
    custom_state = state_changes.setdefault("custom_campaign_state", {})

    if location and location.lower() != "unknown":
        world_data["current_location_name"] = location
        custom_state["last_location"] = location
        return

    prior_location = game_state.world_data.get("current_location_name")
    if prior_location and "current_location_name" not in world_data:
        world_data["current_location_name"] = prior_location
        custom_state["last_location"] = prior_location


def _ensure_resource_checkpoint(state_changes: dict[str, Any], resources: str) -> None:
    resource_state = state_changes.setdefault("world_resources", {})
    if isinstance(resource_state, dict):
        resource_state["last_note"] = resources


def _ensure_dm_notes_persistence(
    state_changes: dict[str, Any],
    llm_response: LLMResponse,
    game_state: GameState,
) -> None:
    """Copy dm_notes from LLM debug_info to state_changes for persistence.

    The LLM writes dm_notes to debug_info (top-level response field), but only
    state_updates get persisted to game state. This function bridges the gap
    by copying dm_notes into state_changes["debug_info"]["dm_notes"].

    Existing dm_notes from game_state are preserved and new notes appended.
    """
    llm_debug_info = llm_response.get_debug_info()
    new_dm_notes = llm_debug_info.get("dm_notes", [])

    # Normalize to list
    if isinstance(new_dm_notes, str):
        new_dm_notes = [new_dm_notes] if new_dm_notes.strip() else []
    elif not isinstance(new_dm_notes, list):
        new_dm_notes = []

    if not new_dm_notes:
        return

    # Get existing dm_notes from game_state
    existing_debug_info = getattr(game_state, "debug_info", {}) or {}
    existing_dm_notes = existing_debug_info.get("dm_notes", [])
    if not isinstance(existing_dm_notes, list):
        existing_dm_notes = []

    # Merge: existing + new (deduplicated)
    merged_notes = list(existing_dm_notes)
    for note in new_dm_notes:
        if isinstance(note, str) and note.strip() and note not in merged_notes:
            merged_notes.append(note)

    # Write to state_changes so it persists
    debug_info_state = state_changes.setdefault("debug_info", {})
    debug_info_state["dm_notes"] = merged_notes
