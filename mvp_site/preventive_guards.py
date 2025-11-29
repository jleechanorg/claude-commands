from __future__ import annotations

from copy import deepcopy
from typing import Any

from mvp_site import constants
from mvp_site.game_state import GameState
from mvp_site.gemini_response import GeminiResponse

AUTO_MEMORY_PREFIX = "[auto]"


def enforce_preventive_guards(
    game_state: GameState, gemini_response: GeminiResponse, mode: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Harden structured responses to prevent backtracking without surfacing errors.

    Returns a tuple of (state_changes, extras) where ``state_changes`` is a
    defensive copy of the model-provided updates augmented with continuity
    safeguards, and ``extras`` contains auxiliary values (e.g., synthesized
    ``god_mode_response``) that should be added to the unified response and
    stored structured fields.
    """

    state_changes: dict[str, Any] = deepcopy(gemini_response.get_state_updates())
    extras: dict[str, Any] = {}

    _fill_god_mode_response(mode, gemini_response, extras)

    dice_rolls = getattr(gemini_response, "dice_rolls", []) or []
    resources = getattr(gemini_response, "resources", "") or ""

    if dice_rolls or resources:
        _ensure_world_time(state_changes, game_state)
        _ensure_core_memory(state_changes, gemini_response.narrative_text)

    _ensure_location_progress(state_changes, gemini_response, game_state)

    if resources:
        _ensure_resource_checkpoint(state_changes, resources)

    return state_changes, extras


def _fill_god_mode_response(
    mode: str, gemini_response: GeminiResponse, extras: dict[str, Any]
) -> None:
    structured = getattr(gemini_response, "structured_response", None)
    existing = getattr(structured, constants.FIELD_GOD_MODE_RESPONSE, None)
    if mode == constants.MODE_GOD and not existing:
        extras[constants.FIELD_GOD_MODE_RESPONSE] = gemini_response.narrative_text


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
        entry = f"{AUTO_MEMORY_PREFIX} {snippet}"[:180]
        if entry not in core_memories:
            core_memories.append(entry)
    custom_state["core_memories"] = core_memories


def _ensure_location_progress(
    state_changes: dict[str, Any],
    gemini_response: GeminiResponse,
    game_state: GameState,
) -> None:
    location = gemini_response.get_location_confirmed()
    world_data = state_changes.setdefault("world_data", {})
    custom_state = state_changes.setdefault("custom_campaign_state", {})

    if location and location != "Unknown":
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

