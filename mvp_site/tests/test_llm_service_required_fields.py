from __future__ import annotations

from unittest.mock import Mock

from mvp_site import constants
from mvp_site.llm_service import (
    _check_dice_integrity,
    _check_missing_required_fields,
    _detect_combat_in_narrative,
    _validate_combat_dice_integrity,
)
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


# =============================================================================
# Tests for _detect_combat_in_narrative
# =============================================================================


def test_detect_combat_in_narrative_active_attack():
    """Active present-tense attack should be detected as combat."""
    assert _detect_combat_in_narrative("The goblin attacks you with its club.") is True
    assert _detect_combat_in_narrative("The orc swings at you.") is True
    assert _detect_combat_in_narrative("The wizard casts fireball at the party.") is True


def test_detect_combat_in_narrative_damage_being_dealt():
    """Damage being dealt should be detected as combat."""
    assert _detect_combat_in_narrative("The arrow strikes, dealing 2d6 damage.") is True
    assert _detect_combat_in_narrative("You take 15 damage from the attack.") is True
    assert _detect_combat_in_narrative("The hit deals damage to the enemy.") is True


def test_detect_combat_in_narrative_dice_patterns():
    """Dice notation in context should be detected as combat."""
    assert _detect_combat_in_narrative("Roll 1d20+5 to hit the goblin.") is True
    assert _detect_combat_in_narrative("Make an attack roll.") is True
    assert _detect_combat_in_narrative("Roll for initiative!") is True


def test_detect_combat_in_narrative_past_tense():
    """Past tense combat references should NOT be detected as active combat."""
    assert _detect_combat_in_narrative("The goblin died in the last encounter.") is False
    assert _detect_combat_in_narrative("You killed the orc previously.") is False
    assert _detect_combat_in_narrative("The battle was won last session.") is False


def test_detect_combat_in_narrative_hypothetical():
    """Hypothetical/conditional combat should NOT be detected as active combat."""
    assert _detect_combat_in_narrative("You could attack the goblin if you wanted.") is False
    assert _detect_combat_in_narrative("If you attack, the guard will retaliate.") is False
    assert _detect_combat_in_narrative("You might want to cast a spell.") is False


def test_detect_combat_in_narrative_no_combat():
    """Non-combat narrative should not be detected as combat."""
    assert _detect_combat_in_narrative("You explore the peaceful village.") is False
    assert _detect_combat_in_narrative("The merchant offers you a deal.") is False
    assert _detect_combat_in_narrative("You rest at the inn.") is False


def test_detect_combat_in_narrative_empty():
    """Empty or None narrative should return False."""
    assert _detect_combat_in_narrative("") is False
    assert _detect_combat_in_narrative(None) is False  # type: ignore


# =============================================================================
# Tests for _check_dice_integrity
# =============================================================================


def test_check_dice_integrity_no_dice_rolls():
    """No dice rolls should always be valid."""
    resp = NarrativeResponse(narrative="test", dice_rolls=[])
    api_response = Mock()
    api_response._tool_requests_executed = False

    is_valid, reason = _check_dice_integrity(
        structured_response=resp,
        api_response=api_response,
    )
    assert is_valid is True
    assert reason == ""


def test_check_dice_integrity_with_tools_executed():
    """Dice rolls with tool execution should be valid."""
    resp = NarrativeResponse(narrative="test", dice_rolls=["1d20+5 = 17"])
    api_response = Mock()
    api_response._tool_requests_executed = True
    api_response._tool_results = [{"tool": "roll_dice", "result": "17"}]

    is_valid, reason = _check_dice_integrity(
        structured_response=resp,
        api_response=api_response,
    )
    assert is_valid is True


def test_check_dice_integrity_fabricated_dice():
    """Dice rolls WITHOUT tool execution should be INVALID (fabrication)."""
    resp = NarrativeResponse(narrative="test", dice_rolls=["1d20+5 = 17"])
    api_response = Mock()
    api_response._tool_requests_executed = False
    api_response._tool_results = []

    is_valid, reason = _check_dice_integrity(
        structured_response=resp,
        api_response=api_response,
    )
    assert is_valid is False
    assert "no tool_requests were executed" in reason


def test_check_dice_integrity_no_metadata():
    """Missing metadata should be permissive (backward compatibility)."""
    resp = NarrativeResponse(narrative="test", dice_rolls=["1d20+5 = 17"])
    api_response = Mock(spec=[])  # No _tool_requests_executed attribute

    is_valid, reason = _check_dice_integrity(
        structured_response=resp,
        api_response=api_response,
    )
    assert is_valid is True  # Permissive for backward compatibility


# =============================================================================
# Tests for _validate_combat_dice_integrity
# =============================================================================


def test_validate_combat_dice_integrity_no_combat():
    """No combat should always be valid."""
    resp = NarrativeResponse(narrative="You rest at the inn.", dice_rolls=[])
    api_response = Mock()
    api_response._tool_requests_executed = False

    is_valid, reason = _validate_combat_dice_integrity(
        user_input="I rest",
        narrative_text="You rest at the inn.",
        structured_response=resp,
        current_game_state=None,
        api_response=api_response,
        mode=constants.MODE_CHARACTER,
        is_god_mode=False,
        is_dm_mode=False,
    )
    assert is_valid is True
    assert reason is None


def test_validate_combat_dice_integrity_combat_with_tools():
    """Combat with proper tool execution should be valid."""
    resp = NarrativeResponse(
        narrative="The goblin attacks you!",
        dice_rolls=["1d20+3 = 15"],
    )
    api_response = Mock()
    api_response._tool_requests_executed = True

    is_valid, reason = _validate_combat_dice_integrity(
        user_input="I attack the goblin",
        narrative_text="The goblin attacks you!",
        structured_response=resp,
        current_game_state=None,
        api_response=api_response,
        mode=constants.MODE_CHARACTER,
        is_god_mode=False,
        is_dm_mode=False,
    )
    assert is_valid is True


def test_validate_combat_dice_integrity_fabricated_combat_dice():
    """Combat with fabricated dice should be INVALID."""
    resp = NarrativeResponse(
        narrative="The goblin attacks you!",
        dice_rolls=["1d20+3 = 15 (fabricated)"],
    )
    api_response = Mock()
    api_response._tool_requests_executed = False

    is_valid, reason = _validate_combat_dice_integrity(
        user_input="I attack the goblin",
        narrative_text="The goblin attacks you!",
        structured_response=resp,
        current_game_state=None,
        api_response=api_response,
        mode=constants.MODE_CHARACTER,
        is_god_mode=False,
        is_dm_mode=False,
    )
    assert is_valid is False
    assert reason is not None
    assert "DICE INTEGRITY VIOLATION" in reason


def test_validate_combat_dice_integrity_god_mode_bypass():
    """God mode should bypass validation."""
    resp = NarrativeResponse(
        narrative="The goblin attacks you!",
        dice_rolls=["1d20+3 = 15"],
    )
    api_response = Mock()
    api_response._tool_requests_executed = False

    is_valid, reason = _validate_combat_dice_integrity(
        user_input="I attack",
        narrative_text="The goblin attacks you!",
        structured_response=resp,
        current_game_state=None,
        api_response=api_response,
        mode=constants.MODE_CHARACTER,
        is_god_mode=True,  # God mode bypass
        is_dm_mode=False,
    )
    assert is_valid is True  # Bypassed


def test_validate_combat_dice_integrity_dm_mode_bypass():
    """DM mode should bypass validation."""
    resp = NarrativeResponse(
        narrative="The goblin attacks you!",
        dice_rolls=["1d20+3 = 15"],
    )
    api_response = Mock()
    api_response._tool_requests_executed = False

    is_valid, reason = _validate_combat_dice_integrity(
        user_input="I attack",
        narrative_text="The goblin attacks you!",
        structured_response=resp,
        current_game_state=None,
        api_response=api_response,
        mode=constants.MODE_CHARACTER,
        is_god_mode=False,
        is_dm_mode=True,  # DM mode bypass
    )
    assert is_valid is True  # Bypassed


# =============================================================================
# Tests for dice_integrity in _check_missing_required_fields
# =============================================================================


def test_check_missing_required_fields_dice_integrity_violation():
    """dice_integrity_violation should add 'dice_integrity' to missing fields."""
    resp = NarrativeResponse(
        narrative="n",
        planning_block=_valid_planning_block(),
        session_header="h",
        dice_rolls=["1d20 = 15"],
    )

    missing = _check_missing_required_fields(
        resp,
        constants.MODE_CHARACTER,
        dice_integrity_violation=True,
    )
    assert "dice_integrity" in missing


def test_check_missing_required_fields_no_dice_integrity_violation():
    """No dice_integrity_violation should not add 'dice_integrity' to missing fields."""
    resp = NarrativeResponse(
        narrative="n",
        planning_block=_valid_planning_block(),
        session_header="h",
        dice_rolls=["1d20 = 15"],
    )

    missing = _check_missing_required_fields(
        resp,
        constants.MODE_CHARACTER,
        dice_integrity_violation=False,
    )
    assert "dice_integrity" not in missing


# =============================================================================
# Tests for reprompt tool_results preservation
# =============================================================================


def test_build_reprompt_includes_tool_results_when_available():
    """RED TEST: _build_reprompt_for_missing_fields should include tool_results context.

    When reprompting after Phase 2 returned malformed JSON, the reprompt message
    MUST include the original tool_results so the model can reference them.

    Without this, the model might fabricate new dice results during reprompt.
    """
    from mvp_site.llm_service import _build_reprompt_for_missing_fields

    original_response = '{"narrative": "The goblin attacks!", "dice_rolls": []}'
    missing_fields = ["dice_rolls"]

    # Tool results that should be included in reprompt
    tool_results = [
        {"tool": "roll_dice", "args": {"notation": "1d20+5"}, "result": {"total": 17, "rolls": [12]}},
    ]

    # RED: Current implementation doesn't accept tool_results parameter
    # This test documents that it SHOULD accept and include tool_results
    reprompt = _build_reprompt_for_missing_fields(
        original_response,
        missing_fields,
        tool_results=tool_results,  # This parameter doesn't exist yet
    )

    # The reprompt should mention the tool results
    assert "17" in reprompt or "tool" in reprompt.lower(), (
        "Reprompt MUST include tool_results context to prevent dice fabrication"
    )
