"""Focused tests for deterministic convergence planning."""

from __future__ import annotations

import inspect
import hashlib
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts.beads_convergence.adapters import BrSqliteV1Adapter, HealthAttestation
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

        redirect = _worktree("/fixtures/repo-one").redirect
        assert redirect is not None
        redirect_changed = RedirectState(
            redirect.present,
            redirect.mode,
            redirect.bytes,
            redirect.parent_device,
            redirect.parent_inode,
            redirect.codec,
            "/fixtures/another/.beads",
        )
        with_redirect = _worktree("/fixtures/repo-one")
        with_redirect = WorktreeRecord(
            with_redirect.path,
            with_redirect.classification,
            with_redirect.directory_device,
            with_redirect.directory_inode,
            with_redirect.sources,
            redirect_changed,
        )
        self.assertNotEqual(
            baseline.sha256,
            build_plan(_manifest(worktrees=(with_redirect,))).sha256,
        )

        identity_changed = _worktree("/fixtures/repo-one")
        identity_changed = WorktreeRecord(
            identity_changed.path,
            identity_changed.classification,
            identity_changed.directory_device + 1,
            identity_changed.directory_inode,
            identity_changed.sources,
            identity_changed.redirect,
        )
        self.assertNotEqual(
            baseline.sha256,
            build_plan(_manifest(worktrees=(identity_changed,))).sha256,
        )

    def test_incomplete_redirect_pre_state_is_not_an_action(self) -> None:
        worktree = _worktree("/fixtures/incomplete-redirect")
        invalid_present = RedirectState(
            True,
            None,
            "canonical",
            1,
            3,
            "br-sqlite-v1-redirect-v1",
            "/fixtures/repo-one/.beads",
        )
        invalid_absent = RedirectState(
            False,
            0o644,
            None,
            1,
            3,
            "br-sqlite-v1-redirect-v1",
            "/fixtures/repo-one/.beads",
        )
        for redirect in (invalid_present, invalid_absent):
            invalid = WorktreeRecord(
                worktree.path,
                worktree.classification,
                worktree.directory_device,
                worktree.directory_inode,
                worktree.sources,
                redirect,
            )
            self.assertEqual(
                build_plan(_manifest(worktrees=(invalid,))).actions,
                (),
            )

    def test_duplicate_source_physical_identity_is_not_an_action(self) -> None:
        worktree = _worktree("/fixtures/duplicate-source")
        duplicate = SourceFingerprint(
            "issues.jsonl",
            worktree.sources[0].device,
            worktree.sources[0].inode,
            worktree.sources[1].size,
            worktree.sources[1].sha256,
        )
        invalid = WorktreeRecord(
            worktree.path,
            worktree.classification,
            worktree.directory_device,
            worktree.directory_inode,
            (worktree.sources[0], duplicate),
            worktree.redirect,
        )
        self.assertEqual(build_plan(_manifest(worktrees=(invalid,))).actions, ())

    def test_only_complete_noncanonical_entries_are_actions(self) -> None:
        manifest = _manifest(
            worktrees=(
                _worktree("/fixtures/zeta"),
                _worktree("/fixtures/canonical", "canonical"),
                _worktree("/fixtures/missing", "missing"),
                _worktree("/fixtures/unsupported", "unsupported"),
                _worktree("/fixtures/incomplete", "unresolved_noncanonical"),
                _worktree("/fixtures/vanished", "missing"),
                _worktree("/fixtures/new", "newly_appeared"),
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

    def test_plan_all_runs_task3_for_nonempty_registry_and_keeps_hashes_separate(
        self,
    ) -> None:
        from scripts.beads_convergence import inventory

        def make_config(
            root: Path, repo_id: str, *, unhealthy: bool = False
        ) -> RepositoryConfig:
            seed = root / repo_id / "seed"
            canonical = seed / ".beads"
            extra = root / repo_id / "extra"
            evidence = root / repo_id / "evidence"
            for beads in (canonical, extra / ".beads"):
                beads.mkdir(parents=True)
                (beads / "beads.db").write_bytes(b"SQLite format 3\x00" + b"x" * 32)
                (beads / "issues.jsonl").write_bytes(b"{}\n")
            if unhealthy:
                (extra / ".beads" / "beads.db-journal").write_bytes(b"hot")
            evidence.mkdir()
            def digest(path: Path) -> str:
                return hashlib.sha256(path.read_bytes()).hexdigest()
            return RepositoryConfig(
                repo_id,
                "br-sqlite-v1",
                seed,
                canonical,
                (root / repo_id,),
                (extra,),
                BinaryBinding(Path("/bin/echo"), "0.4.0", digest(Path("/bin/echo"))),
                BinaryBinding(
                    Path("/usr/bin/git"), "2.0", digest(Path("/usr/bin/git"))
                ),
                evidence,
            )

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            configs = (
                make_config(root, "repo-a"),
                make_config(root, "repo-b", unhealthy=True),
            )
            registry = Registry("beads.redirect-convergence.registry.v1", "h", configs)
            git_results = [
                SimpleNamespace(
                    stdout=f"worktree {config.repository_seed}\n\n".encode(),
                    stderr=b"",
                    returncode=0,
                )
                for config in configs
            ]
            with patch.object(
                inventory,
                "run_verified",
                side_effect=git_results,
            ), patch.object(
                inventory,
                "_codec_metadata",
                return_value=("br-sqlite-v1-redirect-v1", "/canonical/.beads"),
            ), patch.object(
                BrSqliteV1Adapter,
                "verify_binary",
                return_value=SimpleNamespace(close=lambda: None),
            ), patch.object(
                BrSqliteV1Adapter,
                "verify_health",
                return_value=HealthAttestation(0, False, False, "healthy", {}),
            ):
                receipt = plan_all(registry)
            self.assertEqual(receipt.status, 0, receipt.errors)
            self.assertEqual(len(receipt.results), 2)
            self.assertTrue(all(result.ok for result in receipt.results))
            self.assertEqual(len(receipt.plans), 2)
            self.assertEqual(len(receipt.results[0].plan.actions), 1)
            self.assertEqual(len(receipt.results[1].plan.actions), 0)
            self.assertNotEqual(
                receipt.results[0].plan.sha256,
                receipt.results[1].plan.sha256,
            )


if __name__ == "__main__":
    unittest.main()
