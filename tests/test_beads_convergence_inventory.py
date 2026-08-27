"""Focused tests for bounded topology discovery and manifest generation."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts.beads_convergence.adapters import (
    BackendAttestation,
    SourceMember,
    SourceSnapshot,
)
from scripts.beads_convergence.models import BinaryBinding, RepositoryConfig
from scripts.beads_convergence.registry import validate_repository


class FakeAdapter:
    adapter_id = "br-sqlite-v1"
    source_names = ("beads.db", "beads.db-wal", "beads.db-shm", "issues.jsonl")
    redirect_codec_id = "br-sqlite-v1-redirect-v1"
    intended_redirect_bytes = "/canonical/.beads\n"

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


def _repository(root: Path, *, extras: tuple[Path, ...] = ()) -> object:
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
        BinaryBinding(Path("/bin/br"), "0.4.0", "a" * 64),
        BinaryBinding(Path("/bin/git"), "2.0", "b" * 64),
        evidence,
    )
    return validate_repository(config)


class InventoryTest(unittest.TestCase):
    def test_discovery_uses_git_porcelain_and_explicit_extras_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            extra = root / "explicit worktree"
            (extra / ".beads").mkdir(parents=True)
            with _repository(root, extras=(extra,)) as repository:
                porcelain = (
                    f"worktree {repository.config.repository_seed}\n"
                    "HEAD 0123456789abcdef0123456789abcdef01234567\n\n"
                ).encode()
                result = SimpleNamespace(stdout=porcelain, stderr=b"", returncode=0)
                with patch(
                    "scripts.beads_convergence.inventory.run_verified",
                    return_value=result,
                ), patch(
                    "scripts.beads_convergence.inventory.open_verified_executable",
                    return_value=SimpleNamespace(close=lambda: None),
                ):
                    from scripts.beads_convergence.inventory import build_manifest

                    manifest = build_manifest(repository, FakeAdapter())
            self.assertEqual(
                tuple(record.path for record in manifest.worktrees),
                (extra, root / "seed"),
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
                    "scripts.beads_convergence.inventory.run_verified",
                    return_value=result,
                ), patch(
                    "scripts.beads_convergence.inventory.open_verified_executable",
                    return_value=SimpleNamespace(close=lambda: None),
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
                    "scripts.beads_convergence.inventory.run_verified",
                    return_value=result,
                ), patch(
                    "scripts.beads_convergence.inventory.open_verified_executable",
                    return_value=SimpleNamespace(close=lambda: None),
                ):
                    from scripts.beads_convergence.inventory import (
                        InventoryError,
                        discover_worktrees,
                    )

                    with self.assertRaisesRegex(InventoryError, "malformed Git"):
                        discover_worktrees(repository)


if __name__ == "__main__":
    unittest.main()
