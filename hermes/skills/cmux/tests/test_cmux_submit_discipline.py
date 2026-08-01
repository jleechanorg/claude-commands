"""
test_cmux_submit_discipline.py

Regression test for the 2026-07-16 "you always forget to send" incident:
every cmux-touching SKILL.md must carry the 4-step send→submit→proof ritual
AND the mandatory echo-back proof section. This is the contract the user
demanded after the fable iOS pivot bootstrap.

Source thread: C0AJQ5M0A0Y / 1784185650.528089
Rule author: 2026-07-16, branch feat/cmux-must-submit-and-echo-proof

Tested invariants:
  1. Each skill file contains the "Submit Discipline" section heading
  2. Each skill file contains all 4 step labels (STEP 1, STEP 2, STEP 3, STEP 4)
  3. Each skill file contains the "Echo-back proof" section heading
  4. Each skill file names the canonical reference (send-submit-proof-2026-06-25.md)
  5. Each skill file mentions `cmux send-key` (the Enter primitive)
"""

from __future__ import annotations

import os
import sys
import glob
import unittest


# Skills that steer cmux — every one MUST carry the submit discipline rule.
SKILL_PATHS = [
    # ~/.hermes staging
    "$HOME/.hermes/skills/cmux/SKILL.md",
    "$HOME/.hermes/skills/bidi-cmux-alignment/SKILL.md",
    "$HOME/.hermes/skills/cmux-codex-autoapprove/SKILL.md",
    "$HOME/.hermes/skills/cmux-find-workspace-by-topic/SKILL.md",
    "$HOME/.hermes/skills/cmux-mcp-server-options/SKILL.md",
    "$HOME/.hermes/skills/cmux-surface-report-4h/SKILL.md",
    "$HOME/.hermes/skills/test-tui-claude-feature-via-cmux/SKILL.md",
    # ~/.hermes_prod mirror
    "$HOME/.hermes_prod/skills/cmux/SKILL.md",
    "$HOME/.hermes_prod/skills/bidi-cmux-alignment/SKILL.md",
    "$HOME/.hermes_prod/skills/cmux-codex-autoapprove/SKILL.md",
    "$HOME/.hermes_prod/skills/cmux-find-workspace-by-topic/SKILL.md",
    "$HOME/.hermes_prod/skills/cmux-mcp-server-options/SKILL.md",
    "$HOME/.hermes_prod/skills/cmux-surface-report-4h/SKILL.md",
    "$HOME/.hermes_prod/skills/test-tui-claude-feature-via-cmux/SKILL.md",
    # ~/.claude user-scope (not git-tracked but operator-visible)
    "$HOME/.claude/skills/cmux-backup/SKILL.md",
    "$HOME/.claude/skills/cmux-codex-autoapprove/SKILL.md",
    "$HOME/.claude/skills/cmux-goal/SKILL.md",
    "$HOME/.claude/skills/cmux-socket-control/SKILL.md",
    "$HOME/.claude/skills/cmux-steer/SKILL.md",
    "$HOME/.claude/skills/test-tui-claude-feature-via-cmux/SKILL.md",
]

# Required fragments (each must appear at least once in the file body)
REQUIRED_FRAGMENTS = [
    "Submit Discipline",
    "STEP 1",
    "STEP 2",
    "STEP 3",
    "STEP 4",
    "Echo-back proof",
    "send-submit-proof-2026-06-25.md",
    "cmux send-key",
    "1784185650.528089",
]


class TestCmuxSubmitDiscipline(unittest.TestCase):
    """Every cmux-steering skill must carry the submit discipline rule."""

    def test_all_skill_files_exist(self):
        missing = [p for p in SKILL_PATHS if not os.path.exists(p)]
        self.assertFalse(missing, f"Missing skill files: {missing}")

    def test_every_skill_has_submit_discipline_section(self):
        offenders = []
        for path in SKILL_PATHS:
            if not os.path.exists(path):
                continue
            with open(path) as f:
                content = f.read()
            if "Submit Discipline" not in content:
                offenders.append(path)
        self.assertFalse(
            offenders,
            f"Missing 'Submit Discipline' section in: {offenders}"
        )

    def test_every_skill_has_four_step_ritual(self):
        offenders = []
        for path in SKILL_PATHS:
            if not os.path.exists(path):
                continue
            with open(path) as f:
                content = f.read()
            missing = [s for s in ("STEP 1", "STEP 2", "STEP 3", "STEP 4")
                       if s not in content]
            if missing:
                offenders.append((path, missing))
        self.assertFalse(
            offenders,
            f"Skills missing 4-step ritual: {offenders}"
        )

    def test_every_skill_has_echo_back_proof_section(self):
        offenders = []
        for path in SKILL_PATHS:
            if not os.path.exists(path):
                continue
            with open(path) as f:
                content = f.read()
            if "Echo-back proof" not in content:
                offenders.append(path)
        self.assertFalse(
            offenders,
            f"Missing 'Echo-back proof' section in: {offenders}"
        )

    def test_every_skill_cites_canonical_reference(self):
        offenders = []
        for path in SKILL_PATHS:
            if not os.path.exists(path):
                continue
            with open(path) as f:
                content = f.read()
            if "send-submit-proof-2026-06-25.md" not in content:
                offenders.append(path)
        self.assertFalse(
            offenders,
            f"Skills missing canonical reference citation: {offenders}"
        )

    def test_every_skill_uses_send_key_enter(self):
        offenders = []
        for path in SKILL_PATHS:
            if not os.path.exists(path):
                continue
            with open(path) as f:
                content = f.read()
            if "send-key" not in content:
                offenders.append(path)
        self.assertFalse(
            offenders,
            f"Skills missing 'send-key' Enter primitive: {offenders}"
        )

    def test_every_skill_cites_incident_source_thread(self):
        offenders = []
        for path in SKILL_PATHS:
            if not os.path.exists(path):
                continue
            with open(path) as f:
                content = f.read()
            if "1784185650.528089" not in content:
                offenders.append(path)
        self.assertFalse(
            offenders,
            f"Skills missing incident source thread citation: {offenders}"
        )

    def test_submit_section_is_near_top(self):
        """The rule must appear BEFORE the main body content, not as a footnote."""
        offenders = []
        for path in SKILL_PATHS:
            if not os.path.exists(path):
                continue
            with open(path) as f:
                content = f.read()
            idx = content.find("Submit Discipline")
            if idx < 0:
                continue
            # Should appear in the first 4000 chars (top of file)
            if idx > 4000:
                offenders.append((path, idx))
        self.assertFalse(
            offenders,
            f"Submit Discipline section is too far down (>4000 chars): {offenders}"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
