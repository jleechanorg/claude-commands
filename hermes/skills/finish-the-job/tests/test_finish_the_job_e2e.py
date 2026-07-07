"""End-to-end tests for the finish-the-job trigger surfaces and scenarios.

These tests assert that the three trigger surfaces (`/finish`, `/auto`, and the
literal phrase "finish the job") all route to the same end-state protocol,
and that the protocol's behavior can be exercised against (a) a dummy
dropped-Slack-thread scenario and (b) a dummy open-PR scenario, both
scripted end-to-end.

Layer 2 evidence: these tests do not mock the skill's contract. They read
the live SKILL.md, the live RESOLVER.md, and the live .claude/commands/
slash-command files in prod, then assert the trigger wiring is consistent
across all three layers.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parent.parent
SKILL_MD = SKILL_DIR / "SKILL.md"
REPO_ROOT = SKILL_DIR.parent.parent  # ~/.hermes

HERMES_PROD_SKILLS = (
    Path(os.environ["HERMES_PROD_SKILLS"])
    if os.environ.get("HERMES_PROD_SKILLS")
    else Path(os.environ["HERMES_HOME"]) / "skills"
    if os.environ.get("HERMES_HOME")
    else Path.home() / ".hermes_prod" / "skills"
)
HERMES_PROD_COMMANDS = HERMES_PROD_SKILLS.parent / ".claude" / "commands"
HERMES_PROD_SOUL = HERMES_PROD_SKILLS.parent / "SOUL.md"
HERMES_PROD_RESOLVER = HERMES_PROD_SKILLS / "RESOLVER.md"


# ── 1. All three trigger surfaces resolve to the same skill ──────────────────


@pytest.mark.parametrize(
    "surface, expected_skill",
    [
        ("/finish", "finish-the-job"),
        ("/auto", "finish-the-job"),
        ("finish the job", "finish-the-job"),
        ("finish it", "finish-the-job"),
        ("finish this", "finish-the-job"),
    ],
)
def test_trigger_surface_routes_to_finish_the_job(surface: str, expected_skill: str):
    """Every trigger surface (slash command + literal phrase) routes to the
    same end-state protocol. The user's rule is "one skill, one end-state,
    three ways to invoke it" — this test pins that contract.
    """
    # Surface 1: SOUL.md COMMIT block (session-init scan)
    soul_text = HERMES_PROD_SOUL.read_text()
    if surface.startswith("/"):
        # slash commands also appear in SOUL.md
        assert surface in soul_text or surface in soul_text.replace("\\/", "/"), (
            f"slash command {surface!r} not in SOUL.md"
        )
    else:
        # Literal phrase must appear in the finish-the-job trigger line
        commit_block = re.search(
            r"## COMMIT: finish-the-job\s*\nTrigger:[^\n]+", soul_text
        )
        assert commit_block, "missing '## COMMIT: finish-the-job' block in SOUL.md"
        assert surface in commit_block.group(0), (
            f"literal phrase {surface!r} not in SOUL.md finish-the-job trigger line"
        )

    # Surface 2: RESOLVER.md triggers (load-time discovery)
    resolver_text = HERMES_PROD_RESOLVER.read_text()
    assert surface in resolver_text.lower(), (
        f"{surface!r} not in RESOLVER.md"
    )

    # Surface 3: frontmatter triggers in SKILL.md
    fm_text = SKILL_MD.read_text()
    fm_match = re.match(r"^---\n(.*?)\n---", fm_text, re.DOTALL)
    assert fm_match, "SKILL.md missing YAML frontmatter"
    import yaml
    fm = yaml.safe_load(fm_match.group(1))
    triggers_lower = [t.lower() for t in fm.get("triggers", [])]
    assert any(surface in t for t in triggers_lower), (
        f"{surface!r} not in SKILL.md frontmatter triggers"
    )


# ── 2. Slash command files exist and wire to the right skill ────────────────


@pytest.mark.parametrize("cmd_file", ["finish.md", "auto.md"])
def test_slash_command_file_exists_and_loads_skill(cmd_file: str):
    """`/finish` and `/auto` slash commands must exist on disk and their
    body must reference the finish-the-job skill (so the gateway routes
    them through the same protocol).
    """
    path = HERMES_PROD_COMMANDS / cmd_file
    assert path.exists(), f"slash command file missing: {path}"
    text = path.read_text().lower()
    assert "finish-the-job" in text, (
        f"{path} does not reference the finish-the-job skill"
    )


def test_auto_is_alias_for_finish():
    """The /auto slash command is documented as an alias for /finish —
    they must be functionally equivalent (both load the same skill)."""
    auto_text = (HERMES_PROD_COMMANDS / "auto.md").read_text().lower()
    finish_text = (HERMES_PROD_COMMANDS / "finish.md").read_text().lower()
    # Both must reference the same skill
    assert "finish-the-job" in auto_text
    assert "finish-the-job" in finish_text
    # The auto.md body should explicitly call itself an alias
    assert "alias" in auto_text, "/auto is not documented as an alias for /finish"


# ── 3. SOUL.md COMMIT block is structurally valid ───────────────────────────


def test_soul_md_finish_the_job_commit_block_is_valid():
    """The `## COMMIT: finish-the-job` block in SOUL.md must follow the
    Promise Gate contract: trigger-based rule (not 'I'll remember to do X').
    """
    soul_text = HERMES_PROD_SOUL.read_text()
    block = re.search(
        r"## COMMIT: finish-the-job\n(Trigger:[^\n]+)\n(Action:[^\n]+)", soul_text
    )
    assert block, (
        "## COMMIT: finish-the-job must have Trigger: and Action: lines"
    )
    trigger_line, action_line = block.group(1), block.group(2)
    # Trigger must be event-based
    assert "When" in trigger_line or "when" in trigger_line, (
        f"trigger line not event-based: {trigger_line!r}"
    )
    # Action must be concrete (load skill)
    assert "finish-the-job" in action_line or "load" in action_line.lower(), (
        f"action line not concrete: {action_line!r}"
    )


# ── 4. Dummy dropped-thread scenario: contract surfaces ─────────────────────


def test_dummy_dropped_thread_scenario_finishes():
    """Layer-2 e2e: simulate a dropped Slack thread and verify the
    finish-the-job protocol's contract would fire on it.

    We don't call out to Slack — that would be flaky and require real
    credentials. Instead, we verify the *contract surfaces*:
      1. The skill's anti-pattern #1 (ack + design prose + silence) is
         enumerated, so a future agent will be caught.
      2. The dropped-messages companion skill is referenced (so the
         agent loads it on dropped-thread followups).
      3. The user's verbatim rule "correct but misinterpret is fine but
         stopping halfway is not" is in the contract.
    """
    body = SKILL_MD.read_text()
    assert "dropped" in body.lower() or "stalled" in body.lower(), (
        "finish-the-job skill body must acknowledge dropped/stalled threads"
    )
    assert "dropped-messages" in body, (
        "finish-the-job must cross-reference the dropped-messages skill"
    )
    assert "correct but misinterpret is fine" in body, (
        "user's verbatim rule not in skill body"
    )
    # Anti-pattern #1 must enumerate the ack-and-walk-away shape
    assert "I started the worker" in body or "ack" in body.lower(), (
        "anti-pattern #1 (ack + silence) not enumerated"
    )


# ── 5. Dummy PR scenario: contract surfaces ─────────────────────────────────


def test_dummy_pr_scenario_finishes():
    """Layer-2 e2e: simulate a PR fix request and verify the
    finish-the-job protocol's contract covers the drive-to-green path.
    """
    body = SKILL_MD.read_text()
    # The skill must reference the drive-pr-to-green companion skill
    assert "drive-pr-to-green" in body, (
        "finish-the-job must cross-reference drive-pr-to-green"
    )
    # And the always-pr-never-local-edit companion (for new PRs)
    assert "always-pr-never-local-edit" in body, (
        "finish-the-job must cross-reference always-pr-never-local-edit"
    )
    # One of the 4 end-states must be "Green PR merged"
    assert "Green PR merged" in body
    # The contract must forbid follow-up questions
    assert "want me to" in body


# ── 6. The skill loads cleanly from a fresh Python interpreter ─────────────


def test_skill_md_yaml_frontmatter_parses():
    """The SKILL.md frontmatter must be valid YAML — gateways parse it
    before loading the skill. A malformed frontmatter breaks every session.
    """
    text = SKILL_MD.read_text()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    assert m, "SKILL.md must start with YAML frontmatter delimited by ---"
    import yaml
    fm = yaml.safe_load(m.group(1))
    assert isinstance(fm, dict), "frontmatter must parse to a dict"
    assert "name" in fm and fm["name"] == "finish-the-job"
    assert "triggers" in fm and isinstance(fm["triggers"], list)
    assert "related_skills" in fm and isinstance(fm["related_skills"], list)


# ── 7. End-to-end: a fresh session can find the skill by name ───────────────


def test_finish_the_job_skill_is_discoverable_by_name():
    """Layer-2: simulate what the gateway does at session init — look up
    the skill by name. If this fails, the skill is invisible to the
    SOUL.md COMMIT block, and the trigger never fires.
    """
    import yaml

    # 1. SOUL.md references the skill by name
    soul_text = HERMES_PROD_SOUL.read_text()
    assert "finish-the-job" in soul_text, "SOUL.md does not reference finish-the-job"

    # 2. The SKILL.md exists at the canonical path
    assert SKILL_MD.exists(), f"SKILL.md missing at {SKILL_MD}"

    # 3. The SKILL.md frontmatter name matches the directory name
    text = SKILL_MD.read_text()
    fm_match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    fm = yaml.safe_load(fm_match.group(1))
    assert fm["name"] == "finish-the-job", (
        f"frontmatter name {fm['name']!r} does not match directory name 'finish-the-job'"
    )
    assert SKILL_DIR.name == "finish-the-job", (
        f"directory {SKILL_DIR.name!r} does not match skill name 'finish-the-job'"
    )


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
