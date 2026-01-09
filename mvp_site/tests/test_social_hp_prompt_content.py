from pathlib import Path

from mvp_site import agent_prompts


def test_social_hp_enforcement_reminder_mentions_request_severity_and_resistance():
    reminder = agent_prompts.SOCIAL_HP_ENFORCEMENT_REMINDER
    assert "REQUEST SEVERITY" in reminder
    assert "request_severity" in reminder
    assert "resistance_shown" in reminder
    assert "PROGRESS MECHANICS" in reminder


def test_game_state_instruction_documents_request_severity_and_resistance():
    prompt_path = (
        Path(__file__).resolve().parents[1] / "prompts" / "game_state_instruction.md"
    )
    content = prompt_path.read_text(encoding="utf-8")
    assert "request_severity" in content
    assert "resistance_shown" in content
