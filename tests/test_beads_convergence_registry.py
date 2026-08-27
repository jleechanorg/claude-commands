"""Focused tests for captured registry loading and descriptor-anchored validation."""

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from scripts.beads_convergence.codec import canonical_json_bytes
from scripts.beads_convergence.models import BinaryBinding, Registry, RepositoryConfig
from scripts.beads_convergence.registry import (
    RegistryError,
    load_registry,
    validate_registry,
)
from scripts.beads_convergence.fsafety import (
    FsafetyError,
    open_descendant,
    open_trusted_tree,
    validate_fixed_control_root,
)


def _config(root: Path, repo_id: str = "repo-one") -> RepositoryConfig:
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
        BinaryBinding(Path("/bin/echo"), "0.4.0", "0" * 64),
        BinaryBinding(Path("/bin/echo"), "2.0", "0" * 64),
        evidence,
    )


class RegistryTest(unittest.TestCase):
    def test_load_registry_hashes_and_decodes_one_captured_buffer(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "registry.json"
            payload = {
                "schema": "beads.redirect-convergence.registry.v1",
                "host_id": "host",
                "repositories": [],
            }
            raw = canonical_json_bytes(payload)
            path.write_bytes(raw)
            result = load_registry(path, hashlib.sha256(raw).hexdigest())
            self.assertIsInstance(result, Registry)
            self.assertEqual(result.repositories, ())

    def test_duplicate_canonical_physical_identity_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = _config(root, "first")
            (root / "first" / ".beads").mkdir(parents=True)
            (root / "first").mkdir(exist_ok=True)
            (root / "evidence" / "first").mkdir(parents=True)
            second = RepositoryConfig(
                "second", first.adapter, root / "first", first.canonical_beads,
                first.allowed_worktree_roots, (), first.tracker_binary,
                first.git_binary, root / "evidence" / "second",
            )
            (root / "evidence" / "second").mkdir(parents=True)
            with self.assertRaisesRegex(RegistryError, "duplicate canonical authority"):
                validate_registry(
                    Registry(
                        "beads.redirect-convergence.registry.v1", "h", (first, second)
                    )
                )

    def test_unknown_adapter_fails_before_opening_or_running_anything(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            config = _config(Path(temp))
            config = RepositoryConfig(
                config.repo_id, "unknown", config.repository_seed,
                config.canonical_beads, config.allowed_worktree_roots,
                config.additional_worktrees, config.tracker_binary,
                config.git_binary, config.evidence_root,
            )
            with self.assertRaisesRegex(RegistryError, "unknown adapter"):
                validate_registry(
                    Registry("beads.redirect-convergence.registry.v1", "h", (config,))
                )

    def test_component_walk_rejects_symlink_and_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "safe").mkdir()
            (root / "outside").mkdir()
            (root / "safe" / "link").symlink_to(
                root / "outside", target_is_directory=True
            )
            with self.assertRaises((FsafetyError, OSError)):
                open_trusted_tree(root, root / "safe" / "link")
            with self.assertRaises(FsafetyError):
                open_trusted_tree(root, root / "safe" / ".." / "outside")

    def test_membership_stays_descriptor_anchored_after_root_rename(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            parent = Path(temp)
            root = parent / "root"
            target = root / "target"
            target.mkdir(parents=True)
            with open_trusted_tree(parent, root) as retained:
                root.rename(parent / "replaced")
                with open_descendant(retained, target) as child:
                    self.assertEqual(child.display_path, target)

    def test_fixed_control_root_has_no_caller_path_override(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            control = home / ".local/state/beads-convergence/control"
            control.mkdir(parents=True)
            for path in (
                home,
                home / ".local",
                home / ".local/state",
                control.parent,
                control,
            ):
                path.chmod(0o700)
            fake_pwd = SimpleNamespace(pw_dir=str(home))
            with mock.patch("pwd.getpwuid", return_value=fake_pwd):
                with validate_fixed_control_root() as handle:
                    self.assertEqual(handle.display_path, control)
            (home / ".local/state").chmod(0o755)
            with mock.patch("pwd.getpwuid", return_value=fake_pwd):
                with self.assertRaisesRegex(FsafetyError, "unsafe fixed"):
                    validate_fixed_control_root()


if __name__ == "__main__":
    unittest.main()
