"""Approval tool-tree release coverage and fail-closed hashing tests."""

from __future__ import annotations

import shutil
import subprocess
import sys
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
    "skills/beads-redirect-convergence/references/approval-v1.schema.json",
    "skills/beads-redirect-convergence/references/journal-v1.schema.json",
    "skills/beads-redirect-convergence/references/manifest-v1.schema.json",
    "skills/beads-redirect-convergence/references/plan-v1.schema.json",
    "skills/beads-redirect-convergence/references/receipt-v1.schema.json",
    "skills/beads-redirect-convergence/references/registry-v1.schema.json",
}


def _release_copy(root: Path) -> Path:
    for relative in EXPECTED_RELEASE_FILES:
        source_relative = relative.replace(
            "skills/beads-redirect-convergence/",
            ".claude/skills/beads-redirect-convergence/",
            1,
        )
        source = ROOT / source_relative
        target = root / relative
        target_relative = relative
        if relative.startswith("skills/"):
            target_relative = relative.replace(
                "skills/", ".claude/skills/", 1
            )
            target = root / target_relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    return root


def _installed_release_copy(root: Path) -> Path:
    source = _release_copy(root / "source")
    installed = root / "installed"
    for relative in EXPECTED_RELEASE_FILES:
        source_relative = relative.replace(
            "skills/beads-redirect-convergence/",
            ".claude/skills/beads-redirect-convergence/",
            1,
        )
        source_file = source / source_relative
        target_file = installed / relative
        target_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_file, target_file)
    return installed


class ToolTreeTest(unittest.TestCase):
    def test_release_manifest_covers_launcher_runtime_package_and_schemas(self) -> None:
        self.assertEqual(set(approval.TOOL_TREE_RELEASE_FILES), EXPECTED_RELEASE_FILES)
        runtime = {
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / "scripts/beads_convergence").glob("*.py")
        }
        schemas = {
            f"skills/beads-redirect-convergence/references/{path.name}"
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

    def test_installed_layout_hash_matches_source_layout(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            installed = _installed_release_copy(root)
            source_file = root / "source/scripts/beads_convergence/approval.py"
            with patch.object(approval, "__file__", str(source_file)):
                source_digest = tool_tree_sha256()
            probe = subprocess.run(
                (
                    sys.executable,
                    "-I",
                    "-c",
                    (
                        "import sys\n"
                        "sys.path.insert(0, sys.argv[1])\n"
                        "from beads_convergence.approval import tool_tree_sha256\n"
                        "print(tool_tree_sha256())\n"
                    ),
                    str(installed / "scripts"),
                ),
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(probe.returncode, 0, probe.stderr)
            self.assertEqual(probe.stdout.strip(), source_digest)

    def test_schema_layout_is_ambiguous_when_source_and_installed_trees_exist(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = _release_copy(Path(temp))
            source = root / ".claude/skills/beads-redirect-convergence/references"
            installed = root / "skills/beads-redirect-convergence/references"
            installed.mkdir(parents=True)
            for schema in source.glob("*.schema.json"):
                shutil.copyfile(schema, installed / schema.name)
            with (
                patch.object(
                    approval,
                    "__file__",
                    str(root / "scripts/beads_convergence/approval.py"),
                ),
                self.assertRaisesRegex(ApprovalError, "ambiguous"),
            ):
                tool_tree_sha256()

    def test_schema_layout_is_missing_when_neither_tree_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = _release_copy(Path(temp))
            shutil.rmtree(root / ".claude/skills")
            with (
                patch.object(
                    approval,
                    "__file__",
                    str(root / "scripts/beads_convergence/approval.py"),
                ),
                self.assertRaisesRegex(ApprovalError, "unavailable"),
            ):
                tool_tree_sha256()

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
