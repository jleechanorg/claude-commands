from pathlib import Path


def test_social_hp_server_enforcement_markers_removed():
    content = Path(__file__).resolve().parents[1] / "llm_service.py"
    text = content.read_text(encoding="utf-8")

    markers = [
        "SOCIAL_HP_" + "INJECT",
        "SOCIAL_HP_" + "SCALE",
        "SOCIAL_HP_" + "PROGRESS_" + "SYNC",
        "SOCIAL_HP_" + "RESISTANCE",
    ]
    for marker in markers:
        assert marker not in text
