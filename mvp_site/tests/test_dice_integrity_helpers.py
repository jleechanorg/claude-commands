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
