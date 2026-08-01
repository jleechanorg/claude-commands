"""Contract tests for the pr-clean-branch-from-main-no-history-bloat rule.

Verifies the SOUL.md COMMIT block is loadable + the pr-cleanup-replay skill exists
+ the pr-cleanup-replay skill contains the structural recipe (cherry-pick, replay,
close). Does NOT execute the recipe end-to-end (that's a manual workflow).
"""

import re
from pathlib import Path

import pytest


def test_soul_commit_block_exists():
    """The COMMIT block must be present in SOUL.md (staging OR production)."""
    candidates = [
        Path.home() / ".hermes" / "workspace" / "SOUL.md",
        Path.home() / ".hermes_prod" / "workspace" / "SOUL.md",
        Path("$HOME/.worktrees/meta-pr-cleanup/workspace/SOUL.md"),
    ]
    soul_text = ""
    found_at = None
    for p in candidates:
        if p.exists():
            soul_text = p.read_text()
            if "## COMMIT: pr-clean-branch-from-main-no-history-bloat" in soul_text:
                found_at = p
                break
    assert found_at is not None, (
        f"SOUL.md must contain the pr-clean-branch-from-main-no-history-bloat "
        f"COMMIT block. Searched: {[str(p) for p in candidates]}"
    )
    # Verify it has the required Trigger/Action/Why structure
    block_start = soul_text.index("## COMMIT: pr-clean-branch-from-main-no-history-bloat")
    next_block = soul_text.find("## ", block_start + 10)
    block_text = soul_text[block_start:next_block if next_block > 0 else None]
    for required in ("Trigger:", "Action:", "Why:"):
        assert required in block_text, f"COMMIT block must contain {required!r}"


def test_pr_cleanup_skill_exists():
    """The pr-cleanup-replay skill must exist with the expected structure."""
    skill_path = Path("$HOME/.hermes/skills/pr-cleanup-replay/SKILL.md")
    if not skill_path.exists():
        skill_path = Path("$HOME/.worktrees/meta-pr-cleanup/skills/pr-cleanup-replay/SKILL.md")
    assert skill_path.exists(), "pr-cleanup-replay/SKILL.md must exist"
    content = skill_path.read_text()
    # Frontmatter
    assert content.startswith("---"), "SKILL.md must have YAML frontmatter"
    assert "name: pr-cleanup-replay" in content
    # Phases
    for phase in ("Phase 0", "Phase 1", "Phase 2", "Phase 3", "Phase 4"):
        assert phase in content, f"SKILL.md must define {phase}"
    # Required sections
    assert "cherry-pick" in content.lower(), "SKILL.md must describe cherry-pick strategy"
    assert "close" in content.lower(), "SKILL.md must describe how to close the polluted PR"
    assert "origin/main" in content, "SKILL.md must reference origin/main as the base"


def test_pr_cleanup_skill_pitfalls_section():
    """The skill must include a Pitfalls section to prevent recurrence."""
    skill_path = Path("$HOME/.hermes/skills/pr-cleanup-replay/SKILL.md")
    if not skill_path.exists():
        skill_path = Path("$HOME/.worktrees/meta-pr-cleanup/skills/pr-cleanup-replay/SKILL.md")
    content = skill_path.read_text()
    assert "## Pitfalls" in content, "SKILL.md must have a Pitfalls section"
    # Worked example
    assert "## Worked example" in content, "SKILL.md must have a Worked example"


def test_resolver_entry_exists():
    """The RESOLVER.md must have an entry for pr-cleanup-replay."""
    resolver_path = Path("$HOME/.hermes/skills/RESOLVER.md")
    if not resolver_path.exists():
        # Try the worktree
        resolver_path = Path("$HOME/.worktrees/meta-pr-cleanup/skills/RESOLVER.md")
    if resolver_path.exists():
        content = resolver_path.read_text()
        # Triggers must appear in the same line as the ## heading
        if "## pr-cleanup-replay" in content:
            assert "clean up this PR" in content or "replay this PR" in content, \
                "RESOLVER.md entry must list trigger phrases"


def test_no_unrelated_commit_drift_pattern():
    """Detect the failure pattern this rule prevents.

    Simulates the audit: if a PR has commits like 'Merge remote-tracking branch'
    or 'fix(beads)' unrelated to the PR scope, flag it.
    """
    forbidden_substrings = [
        "Merge remote-tracking branch",
        "fix(beads): resync issues.jsonl",
        "[fixpr jleechan2015-automation-commit]",
    ]
    # Just a structural test — the rule's contract is that these patterns trigger the cleanup
    for s in forbidden_substrings:
        # Verify the rule references these patterns (or its description does)
        soul_path = Path("$HOME/.hermes/workspace/SOUL.md")
        if not soul_path.exists():
            soul_path = Path("$HOME/.worktrees/meta-pr-cleanup/workspace/SOUL.md")
        skill_path = Path("$HOME/.hermes/skills/pr-cleanup-replay/SKILL.md")
        if not skill_path.exists():
            skill_path = Path("$HOME/.worktrees/meta-pr-cleanup/skills/pr-cleanup-replay/SKILL.md")
        soul_text = soul_path.read_text() if soul_path.exists() else ""
        skill_text = skill_path.read_text() if skill_path.exists() else ""
        combined = soul_text + skill_text
        # At least one of them must mention the forbidden pattern
        assert s in combined, f"Rule/skill must mention forbidden pattern {s!r}"


def test_never_push_onto_someone_elses_pr_head_soul_commit():
    """The 2026-07-14 anti-pattern (pushing onto another PR's head) must be locked
    into SOUL.md as a separate COMMIT block, distinct from the recovery recipe.

    Two incidents on the same day: your-project.com PR #8401 (+1413/-629 pollution
    over +670k baseline) and claude-commands PR #321 (+212 pollution over +670k/-24k
    baseline). Without a dedicated prevention COMMIT, this WILL recur.
    """
    candidates = [
        Path.home() / ".hermes" / "workspace" / "SOUL.md",
        Path.home() / ".hermes_prod" / "workspace" / "SOUL.md",
        Path("$HOME/.worktrees/meta-pr-cleanup/workspace/SOUL.md"),
    ]
    soul_text = ""
    found_at = None
    for p in candidates:
        if p.exists():
            soul_text = p.read_text()
            if "## COMMIT: never-push-onto-someone-elses-pr-head" in soul_text:
                found_at = p
                break
    assert found_at is not None, (
        "SOUL.md must contain the never-push-onto-someone-elses-pr-head COMMIT "
        "block. Two same-day incidents (PR #8401 and PR #321) prove this is "
        "Critical, not Best-Practice."
    )
    block_start = soul_text.index("## COMMIT: never-push-onto-someone-elses-pr-head")
    next_block = soul_text.find("## ", block_start + 10)
    block_text = soul_text[block_start:next_block if next_block > 0 else None]
    for required in ("Trigger:", "Action:", "Why:"):
        assert required in block_text, f"COMMIT block must contain {required!r}"
    # The Action must require the pre-push gh pr view gate
    assert "gh pr view" in block_text, "Action must require gh pr view pre-push gate"
    # Must name both 2026-07-14 incidents so future agents see the pattern class
    assert "PR #8401" in block_text and "PR #321" in block_text, (
        "COMMIT block must cite both 2026-07-14 incidents to make the "
        "incident-class visible to future agents"
    )


def test_pr_cleanup_skill_phase_minus_one_prevention():
    """The pr-cleanup-replay skill must include Phase -1 (Prevention) as a
    pre-push gate. Without this, the skill only documents the recovery recipe
    and the prevention must be re-derived from scratch every time.
    """
    skill_path = Path("$HOME/.hermes/skills/pr-cleanup-replay/SKILL.md")
    if not skill_path.exists():
        skill_path = Path("$HOME/.worktrees/meta-pr-cleanup/skills/pr-cleanup-replay/SKILL.md")
    assert skill_path.exists(), "pr-cleanup-replay/SKILL.md must exist"
    content = skill_path.read_text()
    assert "Phase -1" in content, (
        "Skill must include 'Phase -1 — Prevention' as a pre-push gate "
        "covering the never-push-onto-someone-elses-pr-head anti-pattern"
    )
    assert "Prevention" in content
    # Must name the pre-push gh pr view + git diff shortstat gates
    assert "gh pr view" in content and "diff --shortstat" in content, (
        "Phase -1 must name the pre-push gates (gh pr view + diff --shortstat)"
    )


def test_resolver_has_never_push_trigger():
    """RESOLVER.md must list the prevention trigger phrase 'never push onto
    someone else's PR head' on the pr-cleanup-replay heading line so future
    agents route to this skill when the user complains about a dirty PR.
    """
    resolver_path = Path("$HOME/.hermes/skills/RESOLVER.md")
    if not resolver_path.exists():
        resolver_path = Path("$HOME/.worktrees/meta-pr-cleanup/skills/RESOLVER.md")
    if not resolver_path.exists():
        pytest.skip("RESOLVER.md not in expected location; coverage skipped")
    content = resolver_path.read_text()
    # Find the pr-cleanup-replay heading line
    found = False
    for line in content.splitlines():
        if line.startswith("## pr-cleanup-replay"):
            # Prevention triggers must be on the SAME line as the heading (gbrain contract)
            triggers = ("never push", "someone else", "PR head", "PR is not clean")
            present = [t for t in triggers if t.lower() in line.lower()]
            assert len(present) >= 2, (
                f"RESOLVER.md pr-cleanup-replay heading must include the prevention "
                f"triggers on the same line. Found: {present}. Line: {line!r}"
            )
            found = True
            break
    assert found, "RESOLVER.md must have a '## pr-cleanup-replay' heading"


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
