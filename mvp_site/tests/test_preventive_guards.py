import pytest

from mvp_site import constants
from mvp_site.game_state import GameState
from mvp_site.gemini_response import GeminiResponse
from mvp_site.narrative_response_schema import NarrativeResponse


@pytest.fixture
def base_game_state():
    state = GameState(user_id="user-123")
    # Seed time data so we can verify preservation
    state.world_data["world_time"] = {"hour": 10, "minute": 15, "time_of_day": "morning"}
    state.world_data["current_location_name"] = "Harbor"
    return state


def _make_response(**kwargs):
    structured = NarrativeResponse(
        narrative=kwargs.pop("narrative", ""),
        entities_mentioned=[],
        location_confirmed=kwargs.pop("location_confirmed", "Unknown"),
        state_updates=kwargs.pop("state_updates", {}),
        dice_rolls=kwargs.pop("dice_rolls", []),
        resources=kwargs.pop("resources", ""),
    )
    return GeminiResponse(
        narrative_text=structured.narrative,
        structured_response=structured,
    )


def test_enforces_god_mode_response_when_missing(base_game_state):
    response = _make_response(narrative="Repair the timeline.")
    from mvp_site import preventive_guards

    state_changes, extras = preventive_guards.enforce_preventive_guards(
        base_game_state, response, constants.MODE_GOD
    )

    assert extras.get("god_mode_response") == "Repair the timeline."
    assert state_changes["world_data"]["current_location_name"] == "Harbor"


def test_infers_time_and_memory_from_dice_rolls(base_game_state):
    response = _make_response(
        narrative="You sprint across the deck as arrows fly.", dice_rolls=["1d20"], state_updates={}
    )
    from mvp_site import preventive_guards

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
    from mvp_site import preventive_guards

    state_changes, _ = preventive_guards.enforce_preventive_guards(
        base_game_state, response, constants.MODE_CHARACTER
    )

    assert state_changes["world_data"]["current_location_name"] == "Bridge"
    assert state_changes["custom_campaign_state"]["last_location"] == "Bridge"
