from testing_mcp.test_llm_guardrails_exploits import evaluate_exploit_rejection


def test_god_mode_rejection_accepts_there_is_no_phrase() -> None:
    scenario = {
        "exploit_type": "god_mode_action",
        "power_indicators": ["antimatter"],
    }
    narrative = (
        "There is no antimatter here, no gargantuan projectile, and no god-like "
        "technology to command."
    )
    result = evaluate_exploit_rejection(narrative, scenario)
    assert result["passed"], result


def test_anachronistic_rejection_accepts_there_is_no_phrase() -> None:
    scenario = {
        "exploit_type": "anachronistic_item",
        "anachronistic_items": ["machine gun", "browning"],
    }
    narrative = (
        "There is no Browning machine gun, no heavy ammunition belts, and no "
        "modern weaponry of any kind within these ruins."
    )
    result = evaluate_exploit_rejection(narrative, scenario)
    assert result["passed"], result
