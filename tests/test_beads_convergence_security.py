"""Security regressions for descriptor-bound convergence mutation."""

from __future__ import annotations

import base64
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from scripts.beads_convergence.approval import ApprovalError, SshApprovalVerifier
from scripts.beads_convergence.transaction import (
    FileControlStore,
    FixtureControlStore,
    TransactionError,
    apply_plan,
)
from tests.test_beads_convergence_transaction import make_request


class ConvergenceSecurityTest(unittest.TestCase):
    def test_stale_source_topology_fails_before_nonce_consumption(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            request = make_request(root)
            (root / "target" / ".beads" / "issues.jsonl").write_bytes(b"drift\n")

            with self.assertRaisesRegex(TransactionError, "source family changed"):
                apply_plan(request)

            nonce_directory = root / "control" / "nonces"
            self.assertFalse(nonce_directory.exists() and any(nonce_directory.iterdir()))

    def test_control_root_rejects_unsafe_existing_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "control"
            root.mkdir(mode=0o755)
            os.chmod(root, 0o755)

            with self.assertRaisesRegex(TransactionError, "unsafe control directory"):
                FixtureControlStore(root).reserve_nonce("1-2", "fixture")

    def test_control_root_rejects_unsafe_effective_home_ancestor(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "home"
            local = home / ".local"
            local.mkdir(parents=True, mode=0o700)
            os.chmod(local, 0o755)
            with (
                mock.patch(
                    "scripts.beads_convergence.transaction.pwd.getpwuid",
                    return_value=SimpleNamespace(pw_dir=str(home)),
                ),
                self.assertRaisesRegex(TransactionError, "unsafe control directory"),
            ):
                FileControlStore().reserve_nonce("1-2", "fixture")

    def test_control_root_rejects_replaced_ancestor_after_retention(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "home"
            (home / ".local").mkdir(parents=True, mode=0o700)
            with mock.patch(
                "scripts.beads_convergence.transaction.pwd.getpwuid",
                return_value=SimpleNamespace(pw_dir=str(home)),
            ):
                store = FileControlStore()
                store.reserve_nonce("1-2", "first")
                original = home / ".local"
                replacement = home / ".local-replacement"
                original.rename(replacement)
                (home / ".local").mkdir(mode=0o700)
                with self.assertRaisesRegex(TransactionError, "control.*changed"):
                    store.reserve_nonce("1-2", "second")

    def test_control_root_rejects_replaced_child_after_retention(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "control"
            store = FixtureControlStore(root)
            store.reserve_nonce("1-2", "first")
            journals = root / "journals"
            journals.rename(root / "journals-replaced")
            journals.mkdir(mode=0o700)
            with self.assertRaisesRegex(TransactionError, "control.*changed"):
                store.save_journal({"run_id": "fixture-run"})

    def test_control_root_rejects_replaced_lock_path_before_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "control"
            store = FixtureControlStore(root)
            with store.lock("1-2"):
                lock = root / "locks" / "1-2.lock"
                lock.rename(root / "locks" / "first.lock")
                lock.write_bytes(b"replacement")
                os.chmod(lock, 0o600)
                with self.assertRaisesRegex(TransactionError, "control lock.*changed"):
                    store.verify_before_redirect_mutation()

    def test_control_root_requires_o_nofollow(self) -> None:
        with (
            tempfile.TemporaryDirectory() as temp,
            mock.patch.object(os, "O_NOFOLLOW", 0),
            self.assertRaisesRegex(TransactionError, "O_NOFOLLOW is unavailable"),
        ):
            FixtureControlStore(Path(temp) / "control").reserve_nonce("1-2", "fixture")

    def test_allowed_signers_rejects_file_larger_than_cap(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "allowed_signers"
            key = base64.b64encode(b"fixture-key").decode()
            path.write_text("ops@example.test ssh-ed25519 " + key + "\n" + "#" * (1024 * 1024))
            fd = os.open(path, os.O_RDONLY)
            try:
                with self.assertRaisesRegex(ApprovalError, "size limit"):
                    SshApprovalVerifier._fingerprint(fd, "ops@example.test")
            finally:
                os.close(fd)

    def test_allowed_signers_rejects_multiple_matching_keys(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "allowed_signers"
            path.write_text(
                "ops@example.test ssh-ed25519 " + base64.b64encode(b"one").decode() + "\n"
                "ops@example.test ssh-ed25519 " + base64.b64encode(b"two").decode() + "\n"
            )
            fd = os.open(path, os.O_RDONLY)
            try:
                with self.assertRaisesRegex(ApprovalError, "exactly one key"):
                    SshApprovalVerifier._fingerprint(fd, "ops@example.test")
            finally:
                os.close(fd)


if __name__ == "__main__":
    unittest.main()
