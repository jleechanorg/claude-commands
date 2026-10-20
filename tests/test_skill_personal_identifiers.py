"""Personal-identifier check for skill packages.

Repo-wide scrubbing is out of scope (older skills still carry personal emails), so
the repository test is scoped to skill files changed by this branch relative to
origin/main (`git diff origin/main...HEAD`). It skips when that ref is unavailable.
"""

import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.skill_portability_scan import find_personal_identifiers, scan_personal  # noqa: E402

SKILL_ROOTS = (".claude/skills", "shared/aliases", "portable/skills")


class PersonalIdentifierTest(unittest.TestCase):
    def test_detects_personal_values(self):
        text = "/home/alice/x /Users/bob/y me@gmail.com C0ABCDEFGHJ 192.168.1.5"
        kinds = {k for k, _ in find_personal_identifiers(text)}
        self.assertEqual(kinds, {"home path", "email", "slack id", "private lan ip"})

    def test_placeholders_are_allowed(self):
        text = "$HOME /home/user/x /Users/<user>/y a@example.com <slack-channel>"
        self.assertEqual(find_personal_identifiers(text), [])

    def test_scan_personal_reports_file(self, ):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "SKILL.md"
            f.write_text("ssh 192.168.0.9\n", encoding="utf-8")
            self.assertIn(str(f), scan_personal([f]))

    def test_changed_skill_files_have_no_personal_identifiers(self):
        probe = subprocess.run(["git", "-C", str(REPO_ROOT), "rev-parse", "--verify", "origin/main"],
                               capture_output=True)
        if probe.returncode:
            self.skipTest("origin/main not available")
        names = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "diff", "--name-only", "--diff-filter=AM", "origin/main...HEAD"],
            capture_output=True, text=True, check=True).stdout.splitlines()
        paths = [REPO_ROOT / n for n in names if n.startswith(SKILL_ROOTS)]
        self.assertEqual(scan_personal(paths), {})


if __name__ == "__main__":
    unittest.main()
