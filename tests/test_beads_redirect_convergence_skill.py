"""Contract tests for the portable Beads convergence operator skill."""

import importlib
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL = REPO_ROOT / ".claude/skills/beads-redirect-convergence/SKILL.md"
COMMAND = REPO_ROOT / ".claude/commands/beads-converge.md"
README = REPO_ROOT / "README.md"
SKILLS_ROOT = REPO_ROOT / ".claude/skills"


class BeadsRedirectConvergenceSkillTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SKILL.read_text(encoding="utf-8")
        cls.flat_text = " ".join(cls.text.split())

    def test_skill_has_portable_frontmatter(self):
        self.assertTrue(self.text.startswith("---\n"))
        self.assertIn("name: beads-redirect-convergence", self.text[:512])
        self.assertIn("description:", self.text[:512])

    def test_read_only_cli_surface_is_complete(self):
        for command in (
            "beads-converge registry validate",
            "beads-converge inventory",
            "beads-converge plan \\",
            "beads-converge plan-all",
        ):
            with self.subTest(command=command):
                self.assertIn(command, self.text)
        self.assertIn("--expected-registry-sha256", self.text)
        self.assertIn("no `--apply` option", self.text)
        self.assertIn("no `apply-all` command", self.text)
        self.assertNotIn("beads-converge apply-all", self.text)

    def test_apply_and_recovery_name_every_binding(self):
        required_bindings = (
            "--repo",
            "--expected-registry-sha256",
            "--manifest",
            "--expected-manifest-sha256",
            "--expected-plan-sha256",
            "--expected-canonical",
            "--expected-adapter",
            "--expected-tracker-path",
            "--expected-tracker-version",
            "--expected-tracker-sha256",
            "--expected-git-path",
            "--expected-git-version",
            "--expected-git-sha256",
            "--approval",
            "--approval-signature",
            "--apply",
            "--recover",
            "run ID",
            "journal SHA",
        )
        for binding in required_bindings:
            with self.subTest(binding=binding):
                self.assertIn(binding, self.text)
        self.assertIn("exactly one `repo_id`", self.text)
        self.assertIn("separately signed", self.flat_text)
        self.assertIn(
            "recovery requires `--manifest`, `--expected-manifest-sha256`,",
            self.flat_text.lower(),
        )

    def test_authority_and_certification_boundaries_are_explicit(self):
        text = self.flat_text.lower()
        for phrase in (
            "portable engine owns schemas",
            "application repository owns its canonical beads authority",
            "Fixture apply",
            "Real dry-run",
            "Trust-root provisioning",
            "Offline approval issuance",
            "Real apply/recovery",
            "Certification never",
            "new explicit operator instruction",
            "proven capabilities",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase.lower(), text)
        self.assertIn("fixture-only authority", text)
        self.assertIn("does not authorize a real repository mutation", text)

    def test_fixed_roots_and_custody_boundary_are_named(self):
        text = self.flat_text
        for value in (
            "/Library/Application Support/Beads Convergence/trust",
            "/etc/beads-convergence/trust",
            "getpwuid(geteuid()).pw_dir",
            "never from `HOME`",
            "never be installed in the applying account",
            "SSH agent",
            "cannot prove private-key custody",
            "Independent certification owns that gate",
        ):
            with self.subTest(value=value):
                self.assertIn(value, text)

    def test_skill_is_a_proper_portable_skill(self):
        if str(REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(REPO_ROOT))
        scanner = importlib.import_module("scripts.skill_portability_scan")
        result = scanner.scan(SKILLS_ROOT)
        self.assertIn("beads-redirect-convergence", result["proper"])
        self.assertNotIn("beads-redirect-convergence", result["orphan"])
        self.assertNotIn("beads-redirect-convergence", result["duplicate"])

    def test_command_is_a_thin_pointer_to_the_skill(self):
        command = COMMAND.read_text(encoding="utf-8")
        self.assertIn("description:", command[:512])
        self.assertIn("beads-redirect-convergence/SKILL.md", command)
        self.assertIn("$ARGUMENTS", command)
        self.assertNotIn("beads-converge apply ", command)
        self.assertNotIn("beads-converge recover ", command)

    def test_readme_catalogs_the_command_and_canonical_skill(self):
        readme = README.read_text(encoding="utf-8")
        self.assertIn(
            "`/beads-converge`",
            readme,
        )
        self.assertIn(
            "(.claude/skills/beads-redirect-convergence/SKILL.md)",
            readme,
        )


if __name__ == "__main__":
    unittest.main()
