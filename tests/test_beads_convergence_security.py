"""Security regressions for descriptor-bound convergence mutation."""

from __future__ import annotations

import base64
import os
import tempfile
import unittest
from pathlib import Path

from scripts.beads_convergence.approval import ApprovalError, SshApprovalVerifier
from scripts.beads_convergence.transaction import (
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
