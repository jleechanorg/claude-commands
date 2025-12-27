from __future__ import annotations

from mvp_site.game_state import GameState


def test_validate_checkpoint_consistency_coerces_hp_strings():
    state = GameState(
        player_character_data={"hp_current": "5", "hp_max": "10"},
        world_data={"campaign_state": "active"},
        custom_campaign_state={},
    )

    discrepancies = state.validate_checkpoint_consistency(
        "You are wounded but still standing."
    )
    assert isinstance(discrepancies, list)


def test_validate_checkpoint_consistency_handles_zero_hp_max_string():
    state = GameState(
        player_character_data={"hp_current": "0", "hp_max": "0"},
        world_data={"campaign_state": "active"},
        custom_campaign_state={"character_creation": {"in_progress": False}},
    )

    discrepancies = state.validate_checkpoint_consistency("")
    assert any("hp_max should not be 0" in d for d in discrepancies)
