from unittest.mock import patch

from mvp_site import dice, logging_util


def test_log_narrative_dice_detected_only_when_present():
    expected = logging_util.with_campaign(
        "DICE_NARRATIVE_DETECTED: Dice patterns found in narrative text."
    )
    with patch("mvp_site.dice.logging_util.info") as info:
        dice.log_narrative_dice_detected(False)
        info.assert_not_called()

    with patch("mvp_site.dice.logging_util.info") as info:
        dice.log_narrative_dice_detected(True)
        info.assert_called_once_with(expected)


def test_log_dice_fabrication_check_debug_switch():
    expected = logging_util.with_campaign(
        "🔍 DICE_FABRICATION_CHECK: "
        "has_dice_in_narrative=True, "
        "has_dice_in_structured=False, "
        "code_execution_used=True, "
        "tool_requests_executed=False"
    )
    with patch("mvp_site.dice.logging_util.warning") as warning:
        dice.log_dice_fabrication_check(
            has_dice_in_narrative=True,
            has_dice_in_structured=False,
            code_execution_used=True,
            tool_requests_executed=False,
            debug_enabled=True,
        )
        warning.assert_called_once_with(expected)

    with patch("mvp_site.dice.logging_util.debug") as debug:
        dice.log_dice_fabrication_check(
            has_dice_in_narrative=True,
            has_dice_in_structured=False,
            code_execution_used=True,
            tool_requests_executed=False,
            debug_enabled=False,
        )
        debug.assert_called_once_with(expected)


def test_log_dice_fabrication_detected():
    expected = logging_util.with_campaign(
        "🚨 DICE_FABRICATION_DETECTED: Found dice in response but no tool/code execution evidence! "
        "has_dice_in_narrative=True, has_dice_in_structured=False"
    )
    with patch("mvp_site.dice.logging_util.warning") as warning:
        dice.log_dice_fabrication_detected(
            has_dice_in_narrative=True,
            has_dice_in_structured=False,
        )
        warning.assert_called_once_with(expected)


def test_log_code_exec_fabrication_violation():
    expected = logging_util.with_campaign(
        "🎲 CODE_EXEC_FABRICATION: Dice in response but no code_execution detected. "
        "Will trigger reprompt to enforce real code execution."
    )
    with patch("mvp_site.dice.logging_util.warning") as warning:
        dice.log_code_exec_fabrication_violation()
        warning.assert_called_once_with(expected)


def test_log_narrative_dice_fabrication_violation():
    expected = logging_util.with_campaign(
        "🎲 NARRATIVE_DICE_FABRICATION: Dice patterns found in narrative without tool evidence. "
        "Will trigger reprompt to enforce real dice."
    )
    with patch("mvp_site.dice.logging_util.warning") as warning:
        dice.log_narrative_dice_fabrication_violation()
        warning.assert_called_once_with(expected)


def test_log_pre_post_detection_context_debug_only():
    expected = logging_util.with_campaign(
        "🔍 PRE/POST DETECTION CONTEXT: "
        "dice_strategy=code_execution, "
        "tool_requests_executed=True, "
        "tool_results_count=2, "
        "code_execution_used=True"
    )
    with patch("mvp_site.dice.logging_util.warning") as warning:
        dice.log_pre_post_detection_context(
            dice_strategy="code_execution",
            tool_requests_executed=True,
            tool_results_count=2,
            code_execution_used=True,
            debug_enabled=True,
        )
        warning.assert_called_once_with(expected)

    with patch("mvp_site.dice.logging_util.warning") as warning:
        dice.log_pre_post_detection_context(
            dice_strategy="code_execution",
            tool_requests_executed=True,
            tool_results_count=2,
            code_execution_used=True,
            debug_enabled=False,
        )
        warning.assert_not_called()


def test_log_post_detection_result_debug_only():
    expected = logging_util.with_campaign(
        "🔍 POST-DETECTION: _detect_narrative_dice_fabrication returned "
        "True | dice_rolls=['1d20 = 10']"
    )
    with patch("mvp_site.dice.logging_util.warning") as warning:
        dice.log_post_detection_result(
            narrative_dice_fabrication=True,
            dice_rolls=["1d20 = 10"],
            debug_enabled=True,
        )
        warning.assert_called_once_with(expected)

    with patch("mvp_site.dice.logging_util.warning") as warning:
        dice.log_post_detection_result(
            narrative_dice_fabrication=True,
            dice_rolls=["1d20 = 10"],
            debug_enabled=False,
        )
        warning.assert_not_called()
