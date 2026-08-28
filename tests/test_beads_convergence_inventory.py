"""Focused tests for bounded topology discovery and manifest generation."""

from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts.beads_convergence.adapters import (
    BackendAttestation,
    BrSqliteV1Adapter,
    RedirectOracle,
    SourceMember,
    SourceSnapshot,
)
from scripts.beads_convergence.inventory import InventoryError, build_manifest
from scripts.beads_convergence.models import BinaryBinding, Registry, RepositoryConfig
from scripts.beads_convergence.registry import validate_registry


class FakeAdapter:
    adapter_id = "br-sqlite-v1"
    source_names = ("beads.db", "beads.db-wal", "beads.db-shm", "issues.jsonl")

    def verify_git_binary(self, binding: object) -> object:
        return SimpleNamespace(binding=binding, close=lambda: None)

    def redirect_oracle(
        self, canonical: Path, worktree: object, executable: object
    ) -> RedirectOracle:
        return RedirectOracle(
            "br-sqlite-v1-redirect-v1",
            b"/canonical/.beads\n",
            "c" * 64,
        )

    def verify_health(self, worktree: object, executable: object) -> object:
        return SimpleNamespace(
            dirty_count=0,
            db_newer=False,
            jsonl_newer=False,
            workspace_health="healthy",
            raw={"workspace_health": "healthy"},
        )

    def verify_binary(self, binding: object) -> object:
        return SimpleNamespace(binding=binding, close=lambda: None)

    def attest_backend(self, beads_dir: object) -> BackendAttestation:
        return BackendAttestation("sqlite", self.source_names)

    def fingerprint_sources(self, beads_dir: object) -> SourceSnapshot:
        return SourceSnapshot(
            tuple(
                SourceMember(name, 1, index + 1, index, "a" * 64)
                for index, name in enumerate(self.source_names)
            )
        )

    def resolve_authority(self, worktree: object, executable: object) -> Path:
        return Path("/canonical/.beads")


def _repository(
    root: Path,
    *,
    extras: tuple[Path, ...] = (),
    tracker_binary: BinaryBinding | None = None,
) -> object:
    seed = root / "seed"
    canonical = seed / ".beads"
    evidence = root / "evidence"
    seed.mkdir(parents=True, exist_ok=True)
    canonical.mkdir(parents=True, exist_ok=True)
    evidence.mkdir(parents=True, exist_ok=True)
    config = RepositoryConfig(
        "repo-one",
        "br-sqlite-v1",
        seed,
        canonical,
        (root,),
        extras,
        tracker_binary
        or BinaryBinding(Path("/bin/br"), "0.4.0", "a" * 64),
        BinaryBinding(Path("/bin/git"), "2.0", "b" * 64),
        evidence,
    )
    return validate_registry(
        Registry("beads.redirect-convergence.registry.v1", "test", (config,))
    )[0]


class InventoryTest(unittest.TestCase):
    def test_shared_registry_guard_rejects_git_discovered_cross_repo_store(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shared = root / "shared-worktree"
            (shared / ".beads").mkdir(parents=True)
            configs = []
            for repo_id in ("repo-one", "repo-two"):
                seed = root / repo_id / "seed"
                (seed / ".beads").mkdir(parents=True)
                evidence = root / repo_id / "evidence"
                evidence.mkdir(parents=True)
                configs.append(
                    RepositoryConfig(
                        repo_id,
                        "br-sqlite-v1",
                        seed,
                        seed / ".beads",
                        (root,),
                        (),
                        BinaryBinding(Path("/bin/br"), "0.4.0", "a" * 64),
                        BinaryBinding(Path("/bin/git"), "2.0", "b" * 64),
                        evidence,
                    )
                )
            repositories = validate_registry(
                Registry(
                    "beads.redirect-convergence.registry.v1", "test", tuple(configs)
                )
            )
            try:
                results = [
                    SimpleNamespace(
                        stdout=(
                            f"worktree {config.repository_seed}\n"
                            f"\nworktree {shared}\n\n"
                        ).encode(),
                        stderr=b"",
                        returncode=0,
                    )
                    for config in configs
                ]
                with patch(
                    "scripts.beads_convergence.inventory.run_verified_git_probe",
                    side_effect=results,
                ), patch(
                    "scripts.beads_convergence.inventory._common_dir_identity",
                    return_value=(1, 1),
                ), patch.object(
                    FakeAdapter,
                    "verify_git_binary",
                    return_value=SimpleNamespace(close=lambda: None),
                ):
                    build_manifest(repositories[0], FakeAdapter())
                    with self.assertRaisesRegex(
                        InventoryError, r"duplicate managed \.beads identity"
                    ):
                        build_manifest(repositories[1], FakeAdapter())
            finally:
                for repository in repositories:
                    repository.close()

    def test_discovery_uses_git_porcelain_and_explicit_extras_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            extra = root / "explicit worktree"
            (extra / ".beads").mkdir(parents=True)
            with _repository(root, extras=(extra,)) as repository:
                porcelain = (
                    f"worktree {repository.config.repository_seed}\n"
                    "HEAD 0123456789abcdef0123456789abcdef01234567\n\n"
                    f"worktree {extra}\n"
                    "HEAD 0123456789abcdef0123456789abcdef01234567\n\n"
                ).encode()
                result = SimpleNamespace(stdout=porcelain, stderr=b"", returncode=0)
                with patch(
                    "scripts.beads_convergence.inventory.run_verified_git_probe",
                    return_value=result,
                ), patch(
                    "scripts.beads_convergence.inventory._common_dir_identity",
                    return_value=(repository.seed.device, repository.seed.inode),
                ):
                    from scripts.beads_convergence.inventory import build_manifest

                    manifest = build_manifest(repository, FakeAdapter())
            self.assertEqual(
                tuple(record.path for record in manifest.worktrees),
                (extra, root / "seed"),
            )
            self.assertEqual(manifest.redirect_codec, "br-sqlite-v1-redirect-v1")
            self.assertEqual(manifest.redirect_oracle_receipt_sha256, "c" * 64)
            self.assertTrue(
                all(record.health is not None for record in manifest.worktrees)
            )
            self.assertTrue(
                all(record.backend == "sqlite" for record in manifest.worktrees)
            )

    def test_inventory_does_not_change_source_or_redirect_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "seed" / ".beads" / "beads.db").mkdir(parents=True)
            source = root / "seed" / ".beads" / "beads.db" / "payload"
            source.write_bytes(b"source")
            before = tuple(
                (path.relative_to(root), path.read_bytes())
                for path in root.rglob("*")
                if path.is_file()
            )
            with _repository(root) as repository:
                result = SimpleNamespace(
                    stdout=(
                        f"worktree {repository.config.repository_seed}\n"
                        "HEAD 0123456789abcdef0123456789abcdef01234567\n\n"
                    ).encode(),
                    stderr=b"",
                    returncode=0,
                )
                with patch(
                    "scripts.beads_convergence.inventory.run_verified_git_probe",
                    return_value=result,
                ), patch(
                    "scripts.beads_convergence.inventory._common_dir_identity",
                    return_value=(repository.seed.device, repository.seed.inode),
                ):
                    from scripts.beads_convergence.inventory import build_manifest

                    build_manifest(repository, FakeAdapter())
            after = tuple(
                (path.relative_to(root), path.read_bytes())
                for path in root.rglob("*")
                if path.is_file()
            )
            self.assertEqual(before, after)

    def test_malformed_git_porcelain_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with _repository(root) as repository:
                result = SimpleNamespace(
                    stdout=b"HEAD missing-worktree\n", returncode=0
                )
                with patch(
                    "scripts.beads_convergence.inventory.run_verified_git_probe",
                    return_value=result,
                ), patch(
                    "scripts.beads_convergence.inventory._common_dir_identity",
                    return_value=(repository.seed.device, repository.seed.inode),
                ):
                    from scripts.beads_convergence.inventory import (
                        InventoryError,
                        discover_worktrees,
                    )

                    with self.assertRaisesRegex(InventoryError, "malformed Git"):
                        discover_worktrees(repository, _adapter=FakeAdapter())

    def test_source_only_manifest_preserves_live_evidence_without_tracker_exec(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            tracker_path = Path("/bin/echo")
            tracker = BinaryBinding(
                tracker_path,
                "0.4.0",
                hashlib.sha256(tracker_path.read_bytes()).hexdigest(),
            )
            with _repository(root, tracker_binary=tracker) as repository:
                beads = repository.config.canonical_beads
                payloads = {
                    "beads.db": b"SQLite format 3\x00" + b"\0" * 32,
                    "beads.db-wal": b"wal",
                    "beads.db-shm": b"shm",
                    "issues.jsonl": b"{}\n",
                }
                for name, content in payloads.items():
                    (beads / name).write_bytes(content)
                (beads / "redirect").write_text(
                    "/unattested/.beads\n", encoding="utf-8"
                )
                monitored = tuple(beads / name for name in payloads)
                before = tuple(
                    (path.stat().st_ino, path.stat().st_mtime_ns, path.read_bytes())
                    for path in monitored
                )
                git_result = SimpleNamespace(
                    stdout=(
                        f"worktree {repository.config.repository_seed}\n"
                        "HEAD 0123456789abcdef0123456789abcdef01234567\n\n"
                    ).encode(),
                    stderr=b"",
                    returncode=0,
                )
                adapter = BrSqliteV1Adapter()
                with patch.object(
                    adapter,
                    "verify_git_binary",
                    return_value=SimpleNamespace(close=lambda: None),
                ), patch(
                    "scripts.beads_convergence.inventory.run_verified_git_probe",
                    return_value=git_result,
                ), patch(
                    "scripts.beads_convergence.inventory._common_dir_identity",
                    return_value=(repository.seed.device, repository.seed.inode),
                ), patch(
                    "scripts.beads_convergence.fsafety.os.fork",
                    side_effect=AssertionError("tracker execution is forbidden"),
                ):
                    manifest = build_manifest(repository, adapter)
                after = tuple(
                    (path.stat().st_ino, path.stat().st_mtime_ns, path.read_bytes())
                    for path in monitored
                )
            self.assertEqual(before, after)
            self.assertIsNone(manifest.redirect_codec)
            self.assertEqual(len(manifest.worktrees), 1)
            record = manifest.worktrees[0]
            self.assertEqual(record.classification, "unsupported")
            self.assertEqual(record.backend, "sqlite")
            self.assertIsNone(record.health)
            self.assertEqual(tuple(item.name for item in record.sources), tuple(sorted(payloads)))
            self.assertIsNotNone(record.redirect)
            self.assertEqual(record.redirect.bytes, "/unattested/.beads\n")


if __name__ == "__main__":
    unittest.main()
