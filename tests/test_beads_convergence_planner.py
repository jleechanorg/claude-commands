"""Focused tests for deterministic convergence planning."""

from __future__ import annotations

import inspect
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.beads_convergence.models import (
    BinaryBinding,
    Manifest,
    RedirectState,
    Registry,
    RepositoryConfig,
    SourceFingerprint,
    WorktreeRecord,
)
from scripts.beads_convergence.planner import build_plan, plan_all


def _manifest(
    repo_id: str = "repo-one",
    worktrees: tuple[WorktreeRecord, ...] | None = None,
) -> Manifest:
    binary = BinaryBinding(Path("/bin/br"), "0.4.0", "a" * 64)
    return Manifest(
        "beads.redirect-convergence.manifest.v1",
        "b" * 64,
        repo_id,
        "br-sqlite-v1",
        Path("/fixtures") / repo_id / ".beads",
        binary,
        BinaryBinding(Path("/bin/git"), "2.0", "c" * 64),
        worktrees if worktrees is not None else (_worktree("/fixtures/repo-one"),),
    )


def _source(name: str, digest: str) -> SourceFingerprint:
    return SourceFingerprint(name, 1, 10 + len(name), len(name), digest * 64)


def _worktree(path: str, classification: str = "noncanonical") -> WorktreeRecord:
    return WorktreeRecord(
        Path(path),
        classification,
        1,
        2,
        (_source("beads.db", "d"), _source("issues.jsonl", "e")),
        RedirectState(
            False,
            None,
            None,
            1,
            3,
            "br-sqlite-v1-redirect-v1",
            "/fixtures/repo-one/.beads",
        ),
    )


def _config(root: Path, repo_id: str) -> RepositoryConfig:
    seed = root / repo_id
    beads = seed / ".beads"
    evidence = root / "evidence" / repo_id
    return RepositoryConfig(
        repo_id,
        "br-sqlite-v1",
        seed,
        beads,
        (root,),
        (),
        BinaryBinding(Path("/bin/br"), "0.4.0", "a" * 64),
        BinaryBinding(Path("/bin/git"), "2.0", "c" * 64),
        evidence,
    )


class PlannerTest(unittest.TestCase):
    def test_plan_is_deterministic_across_two_runs(self) -> None:
        first = build_plan(_manifest())
        second = build_plan(_manifest())
        self.assertEqual(first.sha256, second.sha256)

    def test_plan_hash_binds_sources_redirect_and_physical_identity(self) -> None:
        baseline = build_plan(_manifest())
        source_changed = _worktree("/fixtures/repo-one")
        source_changed = WorktreeRecord(
            source_changed.path,
            source_changed.classification,
            source_changed.directory_device,
            source_changed.directory_inode,
            (_source("beads.db", "f"), source_changed.sources[1]),
            source_changed.redirect,
        )
        self.assertNotEqual(
            baseline.sha256,
            build_plan(_manifest(worktrees=(source_changed,))).sha256,
        )

    def test_only_complete_noncanonical_entries_are_actions(self) -> None:
        manifest = _manifest(
            worktrees=(
                _worktree("/fixtures/zeta"),
                _worktree("/fixtures/canonical", "canonical"),
                _worktree("/fixtures/missing", "missing"),
                _worktree("/fixtures/unsupported", "unsupported"),
                _worktree("/fixtures/incomplete", "unresolved_noncanonical"),
                _worktree("/fixtures/vanished", "missing"),
            )
        )
        plan = build_plan(manifest)
        self.assertEqual(len(plan.actions), 1)
        self.assertEqual(plan.actions[0]["worktree_path"], "/fixtures/zeta")

    def test_actions_are_sorted_by_resolved_worktree_path(self) -> None:
        plan = build_plan(
            _manifest(
                worktrees=(
                    _worktree("/fixtures/zeta"),
                    _worktree("/fixtures/alpha"),
                )
            )
        )
        self.assertEqual(
            [action["worktree_path"] for action in plan.actions],
            ["/fixtures/alpha", "/fixtures/zeta"],
        )

    def test_plan_all_has_no_apply_parameter_or_mutation_calls(self) -> None:
        signature = inspect.signature(plan_all)
        self.assertNotIn("apply", signature.parameters)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            before = sorted(
                (path.relative_to(root), path.read_bytes())
                for path in root.rglob("*")
                if path.is_file()
            )
            receipt = plan_all(
                Registry("beads.redirect-convergence.registry.v1", "h", ())
            )
            after = sorted(
                (path.relative_to(root), path.read_bytes())
                for path in root.rglob("*")
                if path.is_file()
            )
            self.assertEqual(before, after)
            self.assertEqual(receipt.status, 0)

    def test_plan_all_keeps_successes_when_another_repository_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            good = _config(root, "good")
            bad = _config(root, "bad")
            registry = Registry(
                "beads.redirect-convergence.registry.v1", "h", (good, bad)
            )
            with patch(
                "scripts.beads_convergence.planner._plan_repository",
                side_effect=[build_plan(_manifest("good")), ValueError("broken")],
            ):
                receipt = plan_all(registry)
            self.assertEqual(receipt.status, 1)
            self.assertEqual(len(receipt.results), 2)
            self.assertIsNotNone(receipt.results[0].plan)
            self.assertEqual(receipt.results[1].error, "broken")


if __name__ == "__main__":
    unittest.main()
