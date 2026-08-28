"""Approval tool-tree release coverage and fail-closed hashing tests."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.beads_convergence import approval
from scripts.beads_convergence.approval import ApprovalError, tool_tree_sha256

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_RELEASE_FILES = {
    "scripts/beads-converge",
    "scripts/beads_convergence/__init__.py",
    "scripts/beads_convergence/adapters.py",
    "scripts/beads_convergence/approval.py",
    "scripts/beads_convergence/cli.py",
    "scripts/beads_convergence/codec.py",
    "scripts/beads_convergence/fsafety.py",
    "scripts/beads_convergence/inventory.py",
    "scripts/beads_convergence/models.py",
    "scripts/beads_convergence/planner.py",
    "scripts/beads_convergence/registry.py",
    "scripts/beads_convergence/transaction.py",
    ".claude/skills/beads-redirect-convergence/references/approval-v1.schema.json",
    ".claude/skills/beads-redirect-convergence/references/journal-v1.schema.json",
    ".claude/skills/beads-redirect-convergence/references/manifest-v1.schema.json",
    ".claude/skills/beads-redirect-convergence/references/plan-v1.schema.json",
    ".claude/skills/beads-redirect-convergence/references/receipt-v1.schema.json",
    ".claude/skills/beads-redirect-convergence/references/registry-v1.schema.json",
}


def _release_copy(root: Path) -> Path:
    for relative in EXPECTED_RELEASE_FILES:
        source = ROOT / relative
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    return root


class ToolTreeTest(unittest.TestCase):
    def test_release_manifest_covers_launcher_runtime_package_and_schemas(self) -> None:
        self.assertEqual(set(approval.TOOL_TREE_RELEASE_FILES), EXPECTED_RELEASE_FILES)
        runtime = {
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / "scripts/beads_convergence").glob("*.py")
        }
        schemas = {
            path.relative_to(ROOT).as_posix()
            for path in (
                ROOT / ".claude/skills/beads-redirect-convergence/references"
            ).glob("*.schema.json")
        }
        self.assertEqual(
            set(approval.TOOL_TREE_RELEASE_FILES),
            {"scripts/beads-converge", *runtime, *schemas},
        )

    def test_each_representative_runtime_dependency_changes_digest(self) -> None:
        representatives = (
            "scripts/beads_convergence/fsafety.py",
            "scripts/beads_convergence/inventory.py",
            "scripts/beads_convergence/planner.py",
            "scripts/beads_convergence/adapters.py",
        )
        with tempfile.TemporaryDirectory() as temp:
            release = _release_copy(Path(temp))
            fake_file = release / "scripts/beads_convergence/approval.py"
            with patch.object(approval, "__file__", str(fake_file)):
                baseline = tool_tree_sha256()
                for relative in representatives:
                    with self.subTest(relative=relative):
                        path = release / relative
                        original = path.read_bytes()
                        path.write_bytes(original + b"\n# digest regression\n")
                        self.assertNotEqual(tool_tree_sha256(), baseline)
                        path.write_bytes(original)

    def test_symlink_nonregular_unreadable_and_unexpected_runtime_fail_closed(self) -> None:
        cases = ("symlink", "nonregular", "unreadable", "unexpected")
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temp:
                release = _release_copy(Path(temp))
                fake_file = release / "scripts/beads_convergence/approval.py"
                target = release / "scripts/beads_convergence/fsafety.py"
                if case == "symlink":
                    target.unlink()
                    target.symlink_to(release / "scripts/beads_convergence/models.py")
                elif case == "nonregular":
                    target.unlink()
                    target.mkdir()
                elif case == "unreadable":
                    target.chmod(0)
                else:
                    (release / "scripts/beads_convergence/surprise.py").write_text(
                        "raise RuntimeError('unsigned runtime')\n"
                    )
                with (
                    patch.object(approval, "__file__", str(fake_file)),
                    self.assertRaisesRegex(ApprovalError, "tool tree"),
                ):
                    tool_tree_sha256()
                if case == "unreadable":
                    target.chmod(0o644)


if __name__ == "__main__":
    unittest.main()
