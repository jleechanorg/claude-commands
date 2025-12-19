from __future__ import annotations

from mvp_site import constants
from mvp_site.llm_service import _check_missing_required_fields
from mvp_site.narrative_response_schema import NarrativeResponse


def _valid_planning_block() -> dict:
    return {
        "thinking": "t",
        "choices": {"a": {"text": "x", "description": "y", "risk_level": "low"}},
    }


def test_check_missing_required_fields_does_not_require_dice_by_default():
    resp = NarrativeResponse(
        narrative="n",
        planning_block=_valid_planning_block(),
        session_header="h",
        dice_rolls=[],
    )

    missing = _check_missing_required_fields(resp, constants.MODE_CHARACTER)
    assert "dice_rolls" not in missing


def test_check_missing_required_fields_requires_dice_rolls_when_requested():
    resp = NarrativeResponse(
        narrative="n",
        planning_block=_valid_planning_block(),
        session_header="h",
        dice_rolls=[],
    )

    missing = _check_missing_required_fields(
        resp, constants.MODE_CHARACTER, require_dice_rolls=True
    )
    assert "dice_rolls" in missing


def test_check_missing_required_fields_accepts_non_empty_dice_rolls_when_required():
    resp = NarrativeResponse(
        narrative="n",
        planning_block=_valid_planning_block(),
        session_header="h",
        dice_rolls=["Attack: 1d20+5 = 12+5 = 17 vs AC 14 (Hit)"],
    )

    missing = _check_missing_required_fields(
        resp, constants.MODE_CHARACTER, require_dice_rolls=True
    )
    assert "dice_rolls" not in missing


def test_should_require_dice_rolls_only_for_combat_actions():
    from mvp_site.game_state import GameState
    from mvp_site.llm_service import _should_require_dice_rolls_for_turn

    gs = GameState(combat_state={"in_combat": True})

    assert (
        _should_require_dice_rolls_for_turn(
            current_game_state=gs,
            user_input="I attack the goblin",
            mode=constants.MODE_CHARACTER,
            is_god_mode=False,
            is_dm_mode=False,
        )
        is True
    )

    assert (
        _should_require_dice_rolls_for_turn(
            current_game_state=gs,
            user_input="/smoke",
            mode=constants.MODE_CHARACTER,
            is_god_mode=False,
            is_dm_mode=False,
        )
        is False
    )

    assert (
        _should_require_dice_rolls_for_turn(
            current_game_state=GameState(combat_state={"in_combat": False}),
            user_input="I attack the goblin",
            mode=constants.MODE_CHARACTER,
            is_god_mode=False,
            is_dm_mode=False,
        )
        is False
    )
