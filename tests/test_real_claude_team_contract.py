import re

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEAM = ROOT / ".claude" / "commands" / "team-claude.md"
SIDEKICK_CMD = ROOT / ".claude" / "commands" / "sidekick.md"
SIDEKICK_SKILL = ROOT / ".claude" / "skills" / "sidekick" / "SKILL.md"
SWARM_SKILL = ROOT / ".claude" / "skills" / "swarm" / "SKILL.md"
RG = ROOT / ".claude" / "commands" / "rg.md"
REDGREEN = ROOT / ".claude" / "commands" / "redgreen.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


CHECKPOINT_CADENCE_RE = re.compile(
    r"5-minute checkpoint cadence",
    re.IGNORECASE,
)
CHECKPOINT_KEYWORDS = (
    "STATE.md",
    "br sync",
    "isolated state repo",
)
COMMIT_SAFETY_KEYWORDS = (
    "git add -A",
    "isolated state repo",
    "WIP branch",
    "path-scoped",
)
# /advice Round 2 (2026-07-14) tightenings — presence-only checks were too weak.
CADENCE_TIME_RE = re.compile(r"≤\s*5\s*min", re.IGNORECASE)
BR_UPDATE_RE = re.compile(r"br\s+update", re.IGNORECASE)
GITIGNORED_TMP_RE = re.compile(r"gitignored", re.IGNORECASE)
NONREPO_FALLBACK_RE = re.compile(r"non-?repo", re.IGNORECASE)
SINGLE_WRITER_RE = re.compile(r"single-?writer|one\s+writer|one\s+bead\s+writer", re.IGNORECASE)
TEAM_CLAUDE = ROOT / ".claude" / "commands" / "team-claude.md"


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


def test_sidekick_declares_5min_checkpoint_cadence():
    """The sidekick skill must declare the mandatory 5-minute checkpoint cadence.

    Contract: at minimum, the skill must call out the cadence, name STATE.md +
    br sync + the safe-commit escape hatch (isolated state repo / WIP branch).
    Regression target: sidekick missions that drove only chat-only heartbeats
    and lost >30 minutes of lane work on a crash.
    """
    skill_text = read(SIDEKICK_SKILL)
    assert CHECKPOINT_CADENCE_RE.search(skill_text), (
        "sidekick skill must declare the '5-minute checkpoint cadence' contract"
    )
    for keyword in CHECKPOINT_KEYWORDS:
        assert keyword in skill_text, (
            f"sidekick skill must mention {keyword!r} in its checkpoint contract"
        )
    assert any(k in skill_text for k in COMMIT_SAFETY_KEYWORDS), (
        "sidekick skill must include commit-safety guidance "
        "(git add -A ban + isolated repo / WIP branch / path-scoped add)"
    )
    # /advice Round 2 tightenings (2026-07-14): presence-only is too weak; the doc
    # must name the time budget, the `br update` mechanism (not just `br sync`),
    # the gitignored-`.tmp` caveat, the non-repo fallback, and the single-writer
    # rule so concurrent lanes can't clobber the same bead body.
    assert CADENCE_TIME_RE.search(skill_text), (
        "sidekick skill must name the ≤5-min cadence budget literally"
    )
    assert BR_UPDATE_RE.search(skill_text), (
        "sidekick skill must say `br update` (not just `br sync` — br sync "
        "is DB↔JSONL, it does not update the bead body)"
    )
    assert GITIGNORED_TMP_RE.search(skill_text), (
        "sidekick skill must call out the gitignored-`.tmp/` caveat"
    )
    assert NONREPO_FALLBACK_RE.search(skill_text), (
        "sidekick skill must state the non-repo fallback path"
    )
    assert SINGLE_WRITER_RE.search(skill_text), (
        "sidekick skill must designate a single bead writer (no clobber race)"
    )


def test_swarm_declares_5min_checkpoint_cadence():
    """The swarm skill must mirror the sidekick's 5-minute checkpoint cadence.

    All swarm work runs inside the sidekick — so the cadence contract travels
    with the swarm doc too.
    """
    swarm_text = read(SWARM_SKILL)
    assert CHECKPOINT_CADENCE_RE.search(swarm_text), (
        "swarm skill must declare the '5-minute checkpoint cadence' contract"
    )
    for keyword in CHECKPOINT_KEYWORDS:
        assert keyword in swarm_text, (
            f"swarm skill must mention {keyword!r} in its checkpoint contract"
        )
    assert any(k in swarm_text for k in COMMIT_SAFETY_KEYWORDS), (
        "swarm skill must include commit-safety guidance "
        "(git add -A ban + isolated repo / WIP branch / path-scoped add)"
    )
    assert CADENCE_TIME_RE.search(swarm_text), (
        "swarm skill must name the ≤5-min cadence budget literally"
    )
    assert BR_UPDATE_RE.search(swarm_text), (
        "swarm skill must say `br update` (not just `br sync`)"
    )
    assert NONREPO_FALLBACK_RE.search(swarm_text), (
        "swarm skill must state the non-repo fallback path"
    )
    assert SINGLE_WRITER_RE.search(swarm_text), (
        "swarm skill must designate a single bead writer (no clobber race)"
    )


def test_sidekick_command_carries_5min_checkpoint_contract():
    """The /sidekick slash command (user-facing entry point) must carry the same
    5-minute checkpoint contract so it survives any future trim of the skill
    body. Behavior contract item 6 (added in this commit) enforces this.
    """
    command_text = read(SIDEKICK_CMD)
    assert CHECKPOINT_CADENCE_RE.search(command_text), (
        "/sidekick command must carry the '5-minute checkpoint cadence' contract"
    )
    assert "STATE.md" in command_text
    # /advice Round 2: require the literal `br update ... br sync` pair, not just
    # any incidental `br` token, so the command contract isn't trivially passable.
    assert "br update" in command_text, (
        "/sidekick command must show `br update <P1-bead-id> --append ...`"
    )
    assert "br sync" in command_text, (
        "/sidekick command must show the post-update `br sync` flush"
    )
    assert any(k in command_text for k in COMMIT_SAFETY_KEYWORDS), (
        "/sidekick command must include commit-safety guidance"
    )
    assert CADENCE_TIME_RE.search(command_text), (
        "/sidekick command must name the ≤5-min cadence budget literally"
    )
    assert GITIGNORED_TMP_RE.search(command_text), (
        "/sidekick command must call out the gitignored-`.tmp/` caveat "
        "(otherwise the safe-commit rule has a known unfixed gap)"
    )
    assert SINGLE_WRITER_RE.search(command_text), (
        "/sidekick command must designate a single bead writer"
    )


def test_team_claude_carries_5min_checkpoint_contract():
    """The /team-claude command operates the same machinery as /sidekick —
    its agent-team lanes have the same crash-window risk and the same
    commit-safety hazard. /advice Round 2 (2026-07-14) flagged that the
    pre-existing test only reads team-claude.md for the tmux/model contract
    and the new cadence test only touches sidekick.md — leaving team-claude
    as a regression blind spot. Close the gap.
    """
    team_text = read(TEAM_CLAUDE)
    assert CHECKPOINT_CADENCE_RE.search(team_text), (
        "/team-claude command must carry the '5-minute checkpoint cadence' contract "
        "(same machinery as /sidekick — same crash-window + commit-safety risk)"
    )
    assert CADENCE_TIME_RE.search(team_text), (
        "/team-claude must name the ≤5-min cadence budget literally"
    )
    assert any(k in team_text for k in COMMIT_SAFETY_KEYWORDS), (
        "/team-claude must include commit-safety guidance "
        "(git add -A ban + isolated repo / WIP branch / path-scoped add)"
    )
