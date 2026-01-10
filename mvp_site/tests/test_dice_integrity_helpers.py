from mvp_site import dice_integrity


def test_add_missing_dice_fields_requires_dice_rolls():
    missing: list[str] = []
    dice_integrity.add_missing_dice_fields(
        missing,
        structured_response=None,
        require_dice_rolls=True,
        dice_integrity_violation=False,
    )
    assert "dice_rolls" in missing
    assert "dice_integrity" not in missing


def test_add_missing_dice_fields_integrity_violation():
    missing: list[str] = []
    dice_integrity.add_missing_dice_fields(
        missing,
        structured_response=None,
        require_dice_rolls=False,
        dice_integrity_violation=True,
    )
    assert "dice_integrity" in missing


def test_build_dice_integrity_reprompt_lines_code_exec():
    lines = dice_integrity.build_dice_integrity_reprompt_lines(
        dice_integrity.dice_strategy.DICE_STRATEGY_CODE_EXECUTION
    )
    assert any("code_execution" in line for line in lines)
    assert all("tool_requests" not in line for line in lines)


def test_build_dice_integrity_reprompt_lines_native_two_phase():
    lines = dice_integrity.build_dice_integrity_reprompt_lines(
        dice_integrity.dice_strategy.DICE_STRATEGY_NATIVE_TWO_PHASE
    )
    assert any("tool_requests" in line for line in lines)
    assert all("code_execution" not in line for line in lines)
    # Verify dc_reasoning guidance is included
    assert any("dc_reasoning" in line for line in lines)


def test_has_dice_tool_results_rejects_error_responses():
    """Tool errors should NOT count as valid dice results."""
    # Tool call returned an error (e.g., missing dc_reasoning)
    tool_results = [
        {
            "tool": "roll_skill_check",
            "result": {"error": "dc_reasoning is required and must be a non-empty string"}
        }
    ]
    assert dice_integrity._has_dice_tool_results(tool_results) is False


def test_has_dice_tool_results_accepts_valid_results():
    """Valid dice results should be accepted."""
    tool_results = [
        {
            "tool": "roll_skill_check",
            "result": {
                "roll": 15,
                "total": 18,
                "formatted": "[DC 15: guard is alert] Perception: 1d20+3 = 18 vs DC 15 (Success)",
                "success": True
            }
        }
    ]
    assert dice_integrity._has_dice_tool_results(tool_results) is True


def test_has_dice_tool_errors_detects_errors():
    """Should detect and extract tool error messages."""
    tool_results = [
        {
            "tool": "roll_skill_check",
            "result": {"error": "dc_reasoning is required"}
        },
        {
            "tool": "roll_saving_throw",
            "result": {"error": "dc_reasoning is required"}
        }
    ]
    has_errors, errors = dice_integrity._has_dice_tool_errors(tool_results)
    assert has_errors is True
    assert len(errors) == 2
    assert "roll_skill_check: dc_reasoning is required" in errors


def test_has_dice_tool_errors_no_errors():
    """Should return False when no errors."""
    tool_results = [
        {
            "tool": "roll_skill_check",
            "result": {"roll": 15, "total": 18, "success": True}
        }
    ]
    has_errors, errors = dice_integrity._has_dice_tool_errors(tool_results)
    assert has_errors is False
    assert errors == []


# =============================================================================
# Tests for _validate_dice_integrity_always
# =============================================================================
from unittest.mock import Mock

from mvp_site import constants
from mvp_site.narrative_response_schema import NarrativeResponse


def test_validate_dice_integrity_always_no_dice():
    """No dice_rolls should always be valid."""
    resp = NarrativeResponse(narrative="You absorb the orb.", dice_rolls=[])
    api_response = Mock()
    api_response._tool_requests_executed = False

    is_valid, reason = dice_integrity._validate_dice_integrity_always(
        structured_response=resp,
        api_response=api_response,
        mode=constants.MODE_CHARACTER,
        is_god_mode=False,
        is_dm_mode=False,
    )
    assert is_valid is True
    assert reason is None


def test_validate_dice_integrity_always_with_tools():
    """Dice_rolls with tool execution should be valid."""
    resp = NarrativeResponse(
        narrative="You roll an Arcana check.",
        dice_rolls=["[DC 15] Arcana: 1d20+5 = 20 (Success)"],
    )
    api_response = Mock()
    api_response._tool_requests_executed = True

    is_valid, reason = dice_integrity._validate_dice_integrity_always(
        structured_response=resp,
        api_response=api_response,
        mode=constants.MODE_CHARACTER,
        is_god_mode=False,
        is_dm_mode=False,
    )
    assert is_valid is True


def test_validate_dice_integrity_always_fabricated():
    """Dice_rolls without tool execution should be INVALID."""
    resp = NarrativeResponse(
        narrative="You roll an Arcana check.",
        dice_rolls=["[DC 15] Arcana: 1d20+5 = 20 (Success)"],
    )
    api_response = Mock()
    api_response._tool_requests_executed = False

    is_valid, reason = dice_integrity._validate_dice_integrity_always(
        structured_response=resp,
        api_response=api_response,
        mode=constants.MODE_CHARACTER,
        is_god_mode=False,
        is_dm_mode=False,
    )
    assert is_valid is False
    assert "DICE INTEGRITY VIOLATION" in reason


def test_validate_dice_integrity_always_god_mode_bypass():
    """God mode should bypass validation."""
    resp = NarrativeResponse(
        narrative="You absorb the orb.",
        dice_rolls=["[DC 15] Arcana: 1d20+5 = 20 (Success)"],  # Fabricated
    )
    api_response = Mock()
    api_response._tool_requests_executed = False

    is_valid, reason = dice_integrity._validate_dice_integrity_always(
        structured_response=resp,
        api_response=api_response,
        mode=constants.MODE_CHARACTER,
        is_god_mode=True,
        is_dm_mode=False,
    )
    assert is_valid is True  # Bypassed


def test_validate_dice_integrity_always_dm_mode_bypass():
    """DM mode should bypass validation."""
    resp = NarrativeResponse(
        narrative="You absorb the orb.",
        dice_rolls=["[DC 15] Arcana: 1d20+5 = 20 (Success)"],  # Fabricated
    )
    api_response = Mock()
    api_response._tool_requests_executed = False

    is_valid, reason = dice_integrity._validate_dice_integrity_always(
        structured_response=resp,
        api_response=api_response,
        mode=constants.MODE_CHARACTER,
        is_god_mode=False,
        is_dm_mode=True,
    )
    assert is_valid is True  # Bypassed


def test_validate_dice_integrity_always_code_execution_strategy_bypass():
    """Code execution strategy should bypass this check (has its own)."""
    resp = NarrativeResponse(
        narrative="You absorb the orb.",
        dice_rolls=["[DC 15] Arcana: 1d20+5 = 20 (Success)"],  # Would fail for two_phase
    )
    api_response = Mock()
    api_response._tool_requests_executed = False

    is_valid, reason = dice_integrity._validate_dice_integrity_always(
        structured_response=resp,
        api_response=api_response,
        mode=constants.MODE_CHARACTER,
        is_god_mode=False,
        is_dm_mode=False,
        dice_roll_strategy=dice_integrity.dice_strategy.DICE_STRATEGY_CODE_EXECUTION,
    )
    assert is_valid is True  # Bypassed for code_execution


def test_validate_dice_integrity_always_native_two_phase_checks():
    """Native two phase strategy should validate tool_requests."""
    resp = NarrativeResponse(
        narrative="You roll an Arcana check.",
        dice_rolls=["[DC 15] Arcana: 1d20+5 = 20 (Success)"],
    )
    api_response = Mock()
    api_response._tool_requests_executed = False

    is_valid, reason = dice_integrity._validate_dice_integrity_always(
        structured_response=resp,
        api_response=api_response,
        mode=constants.MODE_CHARACTER,
        is_god_mode=False,
        is_dm_mode=False,
        dice_roll_strategy=dice_integrity.dice_strategy.DICE_STRATEGY_NATIVE_TWO_PHASE,
    )
    assert is_valid is False  # Should fail for native_two_phase
    assert "DICE INTEGRITY VIOLATION" in reason
