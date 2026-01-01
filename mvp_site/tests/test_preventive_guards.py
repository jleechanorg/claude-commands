import pytest

from mvp_site import constants, preventive_guards
from mvp_site.game_state import GameState
from mvp_site.llm_response import LLMResponse
from mvp_site.narrative_response_schema import NarrativeResponse


@pytest.fixture
def base_game_state():
    state = GameState(user_id="user-123")
    # Seed time data so we can verify preservation
    state.world_data["world_time"] = {
        "hour": 10,
        "minute": 15,
        "time_of_day": "morning",
    }
    state.world_data["current_location_name"] = "Harbor"
    state.custom_campaign_state = {}
    return state


def _make_response(**kwargs):
    debug_info = kwargs.pop("debug_info", None)
    structured = NarrativeResponse(
        narrative=kwargs.pop("narrative", ""),
        entities_mentioned=[],
        location_confirmed=kwargs.pop("location_confirmed", "Unknown"),
        state_updates=kwargs.pop("state_updates", {}),
        dice_rolls=kwargs.pop("dice_rolls", []),
        resources=kwargs.pop("resources", ""),
    )
    # Inject debug_info into structured response if provided
    if debug_info is not None:
        structured.debug_info = debug_info
    return LLMResponse(
        narrative_text=structured.narrative,
        structured_response=structured,
    )


def test_enforces_god_mode_response_when_missing(base_game_state):
    response = _make_response(narrative="Repair the timeline.")

    state_changes, extras = preventive_guards.enforce_preventive_guards(
        base_game_state, response, constants.MODE_GOD
    )

    assert extras.get("god_mode_response") == "Repair the timeline."
    assert state_changes["world_data"]["current_location_name"] == "Harbor"


def test_infers_time_and_memory_from_dice_rolls(base_game_state):
    response = _make_response(
        narrative="You sprint across the deck as arrows fly.",
        dice_rolls=["1d20"],
        state_updates={},
    )

    state_changes, extras = preventive_guards.enforce_preventive_guards(
        base_game_state, response, constants.MODE_CHARACTER
    )

    # World time should be preserved to avoid regressions even if model forgot to emit it
    assert state_changes["world_data"]["world_time"]["hour"] == 10
    # A core memory entry should be recorded to anchor the turn
    core_memories = state_changes["custom_campaign_state"]["core_memories"]
    assert any("sprint across the deck" in entry for entry in core_memories)
    assert extras == {}


def test_tracks_location_when_missing_state_update(base_game_state):
    response = _make_response(
        narrative="You leave the harbor and arrive at the bridge.",
        location_confirmed="Bridge",
        state_updates={},
    )

    state_changes, _ = preventive_guards.enforce_preventive_guards(
        base_game_state, response, constants.MODE_CHARACTER
    )

    assert state_changes["world_data"]["current_location_name"] == "Bridge"
    assert state_changes["custom_campaign_state"]["last_location"] == "Bridge"


def test_falls_back_to_prior_time_when_missing(base_game_state):
    base_game_state.world_data.pop("world_time")
    response = _make_response(
        narrative="The sun hangs high as you rest.",
        dice_rolls=["1d6"],
        state_updates={},
    )

    state_changes, _ = preventive_guards.enforce_preventive_guards(
        base_game_state, response, constants.MODE_CHARACTER
    )

    world_time = state_changes["world_data"]["world_time"]
    assert world_time["hour"] == 12
    assert world_time["minute"] == 0
    assert world_time["time_of_day"] == "day"


def test_tracks_resource_checkpoint_when_resources_present(base_game_state):
    response = _make_response(
        narrative="You gather herbs and stash them in your pack.",
        resources="inventory: herbs",
        state_updates={},
    )

    state_changes, _ = preventive_guards.enforce_preventive_guards(
        base_game_state, response, constants.MODE_CHARACTER
    )

    assert state_changes["world_resources"]["last_note"] == "inventory: herbs"


def test_preserves_prior_location_when_unknown_confirmed(base_game_state):
    response = _make_response(
        narrative="You circle back, no landmarks in sight.",
        location_confirmed="Unknown",
        state_updates={},
    )

    state_changes, _ = preventive_guards.enforce_preventive_guards(
        base_game_state, response, constants.MODE_CHARACTER
    )

    assert state_changes["world_data"]["current_location_name"] == "Harbor"
    assert state_changes["custom_campaign_state"]["last_location"] == "Harbor"


def test_persists_dm_notes_from_debug_info(base_game_state):
    """Verify dm_notes from LLM debug_info are copied to state_changes for persistence.

    This tests the fix for the issue where LLM writes dm_notes to debug_info but
    only state_updates get persisted. The preventive_guards module now bridges
    this gap by copying dm_notes into state_changes.
    """
    response = _make_response(
        narrative="Power level adjusted for Tier 2.",
        debug_info={"dm_notes": ["Updating narrative tone to 'Tier 2 Heroic'"]},
        state_updates={},
    )

    state_changes, _ = preventive_guards.enforce_preventive_guards(
        base_game_state, response, constants.MODE_GOD
    )

    # dm_notes should be persisted in state_changes.debug_info
    assert "debug_info" in state_changes
    assert "dm_notes" in state_changes["debug_info"]
    assert state_changes["debug_info"]["dm_notes"] == [
        "Updating narrative tone to 'Tier 2 Heroic'"
    ]


def test_dm_notes_merged_with_existing(base_game_state):
    """Verify new dm_notes are appended to existing notes without duplicates."""
    # Set up existing dm_notes in game state
    base_game_state.debug_info = {"dm_notes": ["Previous note"]}

    response = _make_response(
        narrative="Another adjustment.",
        debug_info={"dm_notes": ["New note", "Previous note"]},  # One duplicate
        state_updates={},
    )

    state_changes, _ = preventive_guards.enforce_preventive_guards(
        base_game_state, response, constants.MODE_GOD
    )

    # Should have both notes, with duplicate removed
    dm_notes = state_changes["debug_info"]["dm_notes"]
    assert "Previous note" in dm_notes
    assert "New note" in dm_notes
    assert dm_notes.count("Previous note") == 1  # No duplicate


def test_dm_notes_handles_string_input():
    """Verify dm_notes works when LLM returns a string instead of list."""
    game_state = GameState(user_id="user-123")

    response = _make_response(
        narrative="Single note test.",
        debug_info={"dm_notes": "Single note as string"},
        state_updates={},
    )

    state_changes, _ = preventive_guards.enforce_preventive_guards(
        game_state, response, constants.MODE_GOD
    )

    # String should be normalized to list
    assert state_changes["debug_info"]["dm_notes"] == ["Single note as string"]
