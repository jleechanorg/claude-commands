"""Skill contract tests for god-mode-generic-mechanic-handoff.

Each test maps to a section in SKILL.md. Failures point to specific
checklist items so an operator can re-read the matching section.
"""
from __future__ import annotations
from pathlib import Path
import unittest


SKILL_PATH = Path(__file__).resolve().parent.parent / "SKILL.md"


class SkillContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = SKILL_PATH.read_text()

    def test_yaml_frontmatter_present(self) -> None:
        self.assertRegex(
            self.text,
            r"^---\nname: god-mode-generic-mechanic-handoff",
            "frontmatter must declare name",
        )

    def test_required_sections_present(self) -> None:
        required = [
            "When to use",
            "Generic framing rules",
            "Branching & clean-replay contract",
            "Spawn the right worker",
            "TDD contract tests",
            "/es real-server + real-LLM evidence",
            "Failures the agent WILL hit",
            "Verification checklist",
            "Out-of-scope",
        ]
        for section in required:
            self.assertIn(section, self.text, f"missing section: {section}")

    def test_four_intended_files_listed(self) -> None:
        paths = [
            "$PROJECT_ROOT/agent_prompts.py",
            "$PROJECT_ROOT/prompts/god_mode_instruction.md",
            "$PROJECT_ROOT/tests/test_god_mode_formula_registry_contract.py",
            "testing_mcp/test_god_mode_avatar_partition_contract_real_api.py",
        ]
        for path in paths:
            self.assertIn(path, self.text, f"missing required file reference: {path}")

    def test_grep_helper_pattern_in_skill(self) -> None:
        self.assertIn("_row_string_fields", self.text, "must include the recursive JSONL string-field walker")
        self.assertIn("_grep_all_jsonl", self.text, "must include the grep helper for /es evidence")

    def test_no_secrets_in_skill(self) -> None:
        self.assertNotRegex(self.text, r"xox[bp]-[A-Za-z0-9-]{20,}", "xoxp/xoxb token leaked into skill body")
        self.assertNotRegex(self.text, r"ghp_[A-Za-z0-9]{30,}", "github PAT leaked into skill body")

    def test_drift_files_listed_for_audit(self) -> None:
        for path in ("bq_logging.py", "world_logic.py", "roadmap/"):
            self.assertIn(path, self.text, f"missing drift-file sentinel: {path}")

    def test_recovery_pattern_documented(self) -> None:
        self.assertIn("--force-with-lease", self.text, "must document force-with-lease recovery push")
        self.assertIn("git apply --include", self.text, "must document the apply --include recovery pattern")


if __name__ == "__main__":
    unittest.main(verbosity=2)
