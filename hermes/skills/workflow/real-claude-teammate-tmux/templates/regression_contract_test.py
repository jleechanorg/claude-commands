"""
Regression contract test for real Claude Code teammate commands.

Drop this file at `tests/test_real_claude_team_contract.py` in the target
repo (e.g. jleechanorg/claude-commands). Adjust the FILE_PATHS, REQUIRED
TOKENS, and FORBIDDEN_TOKENS lists per the specific command you are
protecting.

This contract was authored 2026-07-10 to ship jleechanorg/claude-commands
PR #321 (which rewrote /team-claude, /sidekick, and the sidekick skill
to use the real `claude --model sonnet --teammate-mode tmux` primitive
instead of the drifted pseudo-Agent docs).

Run: `python3 -m pytest tests/test_real_claude_team_contract.py -q`
"""

from pathlib import Path

# --- EDIT THIS BLOCK PER PROJECT -------------------------------------------

# Files to audit. Paths are relative to the repo root.
FILE_PATHS = [
    ".claude/commands/team-claude.md",
    ".claude/commands/sidekick.md",
    ".claude/skills/sidekick/SKILL.md",
]

# Tokens that MUST appear in at least one of the files. Pin the real
# primitive so a future edit cannot regress to a fictional API.
REQUIRED_TOKENS = [
    "claude --model sonnet --teammate-mode tmux",
    "tmux new-session",
    "tmux capture-pane",
    "Sonnet-only",  # visible-name contract; adjust case if your docs use
                    # a different casing (e.g. "sonnet-only").
]

# Tokens that MUST NOT appear in any of the files. Add to this list
# when you find new pseudo-primitive language creeping back.
FORBIDDEN_TOKENS = [
    # Pseudo-primitive Agent/TaskList pattern.
    "TaskCreate",
    "TaskList",
    "TaskUpdate",
    "SendMessage",
    "TeamCreate",
    "Agent(",
    "team_name=",
    # Historical subagent type names that don't exist in the real CLI.
    "claude-pair-coder",
    "claude-pair-verifier",
    # Other-model scout lanes that violate the Sonnet-only contract.
    'model="haiku"',
    "fable sidekick",
    # Hard-coded model strings that age out when the CLI default rotates.
    "claude-3-5-sonnet",
]

# ---------------------------------------------------------------------------


def read(rel: str, root: Path) -> str:
    return (root / rel).read_text(encoding="utf-8")


def test_required_tokens_present():
    """The real Claude Code teammate primitive must be present in at least
    one of the audited files. This catches full regressions back to the
    pseudo-primitive Agent/TaskList docs."""
    root = Path(__file__).resolve().parents[1]
    combined = "\n".join(read(p, root) for p in FILE_PATHS)
    missing = [t for t in REQUIRED_TOKENS if t not in combined]
    assert not missing, (
        "Production docs are missing the real Claude Code teammate "
        f"primitives: {missing}. Restore `claude --model sonnet "
        "--teammate-mode tmux` and the four-check verification recipe "
        "per skill `real-claude-teammate-tmux`."
    )


def test_forbidden_tokens_absent():
    """The pseudo-primitive Agent/TaskList pattern must not appear in any
    audited file. This catches partial regressions (e.g. someone adds a
    fallback lane or a `team_name=` line)."""
    root = Path(__file__).resolve().parents[1]
    violations = []
    for rel in FILE_PATHS:
        text = read(rel, root)
        for token in FORBIDDEN_TOKENS:
            if token in text:
                violations.append((rel, token))
    assert not violations, (
        "Production docs still contain pseudo-primitive language. "
        "Replace with the real `claude --model sonnet --teammate-mode tmux` "
        f"primitive. Violations: {violations}. See skill "
        "`real-claude-teammate-tmux` for the replacement recipe."
    )


def test_each_required_file_exists():
    """The audited files must exist. Drop a row from FILE_PATHS if you
    intentionally delete a command or skill — don't silently let the
    test mask a missing file."""
    root = Path(__file__).resolve().parents[1]
    missing = [p for p in FILE_PATHS if not (root / p).exists()]
    assert not missing, (
        f"Audited files no longer exist: {missing}. Either restore the "
        "files or update FILE_PATHS in this test."
    )
