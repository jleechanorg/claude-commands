from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEAM = ROOT / ".claude" / "commands" / "team-claude.md"
SIDEKICK_CMD = ROOT / ".claude" / "commands" / "sidekick.md"
SIDEKICK_SKILL = ROOT / ".claude" / "skills" / "sidekick" / "SKILL.md"
RG = ROOT / ".claude" / "commands" / "rg.md"
REDGREEN = ROOT / ".claude" / "commands" / "redgreen.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_rg_alias_points_to_redgreen_contract():
    rg = read(RG)
    redgreen = read(REDGREEN)
    assert "Execute `/redgreen`" in rg
    assert "RED - Test-First Error Reproduction" in redgreen
    assert "Cannot proceed to CODE phase without failing tests" in redgreen


def test_team_claude_uses_real_tmux_claude_code_sonnet_only():
    text = read(TEAM)
    assert "claude --model sonnet --teammate-mode tmux" in text
    assert "tmux new-session" in text
    assert "tmux capture-pane" in text
    assert "Sonnet-only" in text or "sonnet-only" in text.lower()

    forbidden = [
        "claude-pair-coder",
        "claude-pair-verifier",
        "model=\"haiku\"",
        "TaskCreate",
        "TaskUpdate",
        "SendMessage",
        "TeamCreate",
        "Agent(",
        "team_name",
    ]
    for token in forbidden:
        assert token not in text, f"/team-claude still references pseudo primitive {token!r}"


def test_sidekick_uses_real_tmux_claude_code_and_keeps_state_file():
    command_text = read(SIDEKICK_CMD)
    skill_text = read(SIDEKICK_SKILL)
    combined = command_text + "\n" + skill_text

    assert "claude --model sonnet --teammate-mode tmux" in combined
    assert "tmux new-session" in combined
    assert "STATE.md" in combined
    assert "Sonnet-only" in combined or "sonnet-only" in combined.lower()

    forbidden = [
        "TaskCreate",
        "TaskList",
        "TaskUpdate",
        "SendMessage",
        "Agent tool",
        "run_in_background",
        "claude-3-5-sonnet",
        "fable sidekick",
        "model`: `fable",
        "model=\"haiku\"",
    ]
    for token in forbidden:
        assert token not in combined, f"/sidekick still references stale primitive/model {token!r}"
