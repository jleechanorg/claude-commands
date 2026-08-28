"""Crash boundaries use an injected fixture fault only; production has no hook."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.beads_convergence.transaction import (
    ApplyRequest,
    RecoveryRequest,
    TransactionCrash,
    apply_plan,
    recover_run,
)
from tests.test_beads_convergence_transaction import make_recovery_request, make_request


class CrashRecoveryTest(unittest.TestCase):
    def test_recovery_without_literal_authorization_cannot_commit_crashed_apply(self) -> None:
        """Recovery is a separately-authorized rollback, never an apply resume."""

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            request = make_request(root)
            request = ApplyRequest(**{**request.__dict__, "fault_at": "after-rename"})
            with self.assertRaises(TransactionCrash):
                apply_plan(request)
            with self.assertRaisesRegex(Exception, "recover"):
                recover_run(RecoveryRequest(request.control, request.adapter, "fixture-run"))
            self.assertEqual(
                (root / "target" / ".beads" / "redirect").read_text(),
                str(root / "canonical" / ".beads") + "\n",
            )

    def test_recovery_refuses_third_party_bytes_and_records_needs_operator(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            request = make_request(root)
            request = ApplyRequest(**{**request.__dict__, "fault_at": "after-rename"})
            with self.assertRaises(TransactionCrash):
                apply_plan(request)
            redirect = root / "target" / ".beads" / "redirect"
            redirect.write_bytes(b"third-party\n")
            recovery = recover_run(make_recovery_request(request))
            self.assertEqual(recovery.status, "NEEDS_OPERATOR")
            self.assertEqual(redirect.read_bytes(), b"third-party\n")

    def test_committed_journal_without_receipt_is_repaired_idempotently(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            request = make_request(Path(temp))
            request = ApplyRequest(**{**request.__dict__, "fault_at": "after-commit"})
            with self.assertRaises(TransactionCrash):
                apply_plan(request)
            first = recover_run(make_recovery_request(request, nonce="recover-one"))
            second = recover_run(make_recovery_request(request, nonce="recover-two"))
            self.assertEqual(first.status, "COMMITTED")
            self.assertEqual(second.status, "COMMITTED")


if __name__ == "__main__":
    unittest.main()
