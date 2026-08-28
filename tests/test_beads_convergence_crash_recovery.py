"""Crash boundaries use an injected fixture fault only; production has no hook."""

from __future__ import annotations

import os
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from scripts.beads_convergence.approval import SignedApproval
from scripts.beads_convergence.codec import canonical_json_bytes, sha256_hex
from scripts.beads_convergence.models import RedirectState, WorktreeRecord
from scripts.beads_convergence.planner import build_plan
from tests.beads_convergence_fixture_harness import (
    ApplyRequest,
    FixtureControlStore,
    RecoveryRequest,
    TransactionCrash,
    apply_plan,
    recover_run,
)
from tests.test_beads_convergence_transaction import (
    _source,
    make_recovery_request,
    make_request,
)

APPLY_FAULT_BOUNDARIES = (
    "before-prepared",
    "after-prepared",
    "before-temp-fsync",
    "after-temp-fsync",
    "before-rename",
    "after-rename",
    "after-target-fsync",
    "after-progress",
    "before-commit",
    "after-commit",
    "after-receipt",
)


class RecoveryProcessDeathControlStore(FixtureControlStore):
    """Exit the child after one recovery journal transition is durable."""

    def __init__(self, root: Path, exit_code: int) -> None:
        super().__init__(root)
        self.exit_code = exit_code
        self.die_after_rollback = False

    def save_journal(self, journal: dict[str, object]) -> None:
        super().save_journal(journal)
        if (
            self.die_after_rollback
            and journal.get("status") == "APPLYING"
            and any(
                action.get("state") == "ROLLED_BACK" for action in journal["actions"]
            )
        ):
            os._exit(self.exit_code)


def _fork_apply(request: ApplyRequest, exit_code: int) -> int:
    """Run an injected apply crash in a child with no Python unwinding."""

    child_pid = os.fork()
    if child_pid == 0:
        from tests import beads_convergence_fixture_harness as transaction_module

        class ProcessCrash(BaseException):
            def __init__(self) -> None:
                os._exit(exit_code)

        transaction_module.TransactionCrash = ProcessCrash
        apply_plan(request)
        os._exit(250)
    _, status = os.waitpid(child_pid, 0)
    if not os.WIFEXITED(status):
        return -1
    return os.WEXITSTATUS(status)


def _fork_recovery(request: RecoveryRequest) -> int:
    """Run a recovery interruption in a child that exits from its test seam."""

    child_pid = os.fork()
    if child_pid == 0:
        recover_run(request)
        os._exit(250)
    _, status = os.waitpid(child_pid, 0)
    if not os.WIFEXITED(status):
        return -1
    return os.WEXITSTATUS(status)


def _multi_target_request(root: Path) -> ApplyRequest:
    """Extend the shared fixture to two eligible targets with distinct pre-bytes."""

    request = make_request(root, pre_redirect="local-authority-a\n")
    target = root / "target-2"
    beads = target / ".beads"
    beads.mkdir(parents=True)
    (beads / "beads.db").write_bytes(b"SQLite format 3\x00fixture-target-2")
    (beads / "issues.jsonl").write_bytes(b'{"id":"fixture-target-2"}\n')
    (beads / "redirect").write_bytes(b"local-authority-b\n")
    target_info = target.stat()
    parent = beads.stat()
    template = request.manifest.worktrees[1]
    health = template.health
    assert health is not None
    redirect = RedirectState(
        True,
        0o644,
        "local-authority-b\n",
        parent.st_dev,
        parent.st_ino,
        "fixture-redirect-v1",
        str(root / "canonical" / ".beads") + "\n",
        "b" * 64,
    )
    extra = WorktreeRecord(
        target,
        "noncanonical",
        target_info.st_dev,
        target_info.st_ino,
        (_source(beads, "beads.db"), _source(beads, "issues.jsonl")),
        redirect,
        "sqlite",
        health,
    )
    manifest = replace(request.manifest, worktrees=(*request.manifest.worktrees, extra))
    plan = build_plan(manifest)
    assert request.approval is not None
    envelope = replace(
        request.approval.envelope,
        manifest_sha256=sha256_hex(canonical_json_bytes(manifest)),
        plan_sha256=plan.sha256,
    )
    return replace(
        request,
        manifest=manifest,
        plan=plan,
        approval=SignedApproval(envelope, request.approval.signature),
    )


def _source_bytes(request: ApplyRequest) -> dict[Path, bytes]:
    root = request.manifest.canonical_beads.parents[1]
    snapshot: dict[Path, bytes] = {}
    for record in request.manifest.worktrees:
        beads = record.path / ".beads"
        for source in record.sources:
            snapshot[beads.relative_to(root) / source.name] = (beads / source.name).read_bytes()
    return snapshot


def _redirect_bytes(request: ApplyRequest) -> dict[Path, bytes]:
    root = request.manifest.canonical_beads.parents[1]
    snapshot: dict[Path, bytes] = {}
    for record in request.manifest.worktrees:
        if record.classification != "noncanonical":
            continue
        redirect = record.path / ".beads" / "redirect"
        snapshot[redirect.relative_to(root)] = redirect.read_bytes()
    return snapshot


class CrashRecoveryTest(unittest.TestCase):
    def test_apply_fault_matrix_recovers_exact_bytes_across_two_targets(self) -> None:
        """Every declared apply crash point leaves a durable recovery decision."""

        for fault_at in APPLY_FAULT_BOUNDARIES:
            with self.subTest(fault_at=fault_at), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                request = _multi_target_request(root)
                source_before = _source_bytes(request)
                pre_redirects = _redirect_bytes(request)
                intended = {
                    path: (str(root / "canonical" / ".beads") + "\n").encode()
                    for path in pre_redirects
                }
                crashed = replace(request, fault_at=fault_at)
                exit_code = 101 + APPLY_FAULT_BOUNDARIES.index(fault_at)
                self.assertEqual(_fork_apply(crashed, exit_code), exit_code)
                request = replace(request, control=FixtureControlStore(root / "control"))
                self.assertEqual(_source_bytes(request), source_before)

                if fault_at == "before-prepared":
                    self.assertFalse(request.control.journal_path("fixture-run").exists())
                    self.assertEqual(_redirect_bytes(request), pre_redirects)
                    receipt = apply_plan(replace(request, fault_at=None))
                    self.assertEqual(receipt.status, "COMMITTED")
                    self.assertEqual(_redirect_bytes(request), intended)
                    self.assertEqual(
                        request.control.load_journal("fixture-run")["status"], "COMMITTED"
                    )
                    continue

                journal = request.control.load_journal("fixture-run")
                self.assertEqual(
                    journal["status"],
                    "COMMITTED"
                    if fault_at in ("after-commit", "after-receipt")
                    else "PREPARED"
                    if fault_at == "after-prepared"
                    else "APPLYING",
                )
                redirects_after_crash = (
                    intended
                    if fault_at in (
                        "before-commit",
                        "after-commit",
                        "after-receipt",
                    )
                    else pre_redirects
                )
                if fault_at in (
                    "after-rename",
                    "after-target-fsync",
                    "after-progress",
                ):
                    first_target = min(pre_redirects)
                    redirects_after_crash = {
                        **pre_redirects,
                        first_target: intended[first_target],
                    }
                self.assertEqual(_redirect_bytes(request), redirects_after_crash)
                if fault_at == "after-commit":
                    self.assertFalse(request.control.receipt_path("fixture-run").exists())
                elif fault_at == "after-receipt":
                    self.assertTrue(request.control.receipt_path("fixture-run").exists())

                if fault_at == "after-prepared":
                    with self.assertRaisesRegex(Exception, "unfinished journal"):
                        apply_plan(replace(request, fault_at=None))
                recovery = recover_run(make_recovery_request(request))
                expected_status = (
                    "COMMITTED"
                    if fault_at in ("after-commit", "after-receipt")
                    else "ROLLED_BACK"
                )
                self.assertEqual(recovery.status, expected_status)
                self.assertEqual(
                    request.control.load_journal("fixture-run")["status"], expected_status
                )
                self.assertEqual(
                    _redirect_bytes(request),
                    intended if expected_status == "COMMITTED" else pre_redirects,
                )
                self.assertEqual(_source_bytes(request), source_before)

    def test_recovery_interruption_restarts_from_durable_mid_recovery_journal(self) -> None:
        """A crash between rollback actions retries idempotently from its journal."""

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            request = _multi_target_request(root)
            source_before = _source_bytes(request)
            control = RecoveryProcessDeathControlStore(root / "control", 190)
            request = replace(request, control=control, fault_at="after-progress")
            self.assertEqual(_fork_apply(request, 180), 180)
            request = replace(request, control=FixtureControlStore(root / "control"))
            self.assertEqual(_source_bytes(request), source_before)
            interrupted_control = RecoveryProcessDeathControlStore(root / "control", 190)
            interrupted_control.die_after_rollback = True
            interrupted_request = replace(request, control=interrupted_control)
            self.assertEqual(
                _fork_recovery(
                    make_recovery_request(interrupted_request, nonce="recover-interrupted")
                ),
                190,
            )
            reopened = FixtureControlStore(root / "control")
            interrupted = reopened.load_journal("fixture-run")
            self.assertEqual(interrupted["status"], "APPLYING")
            self.assertEqual(
                sum(action["state"] == "ROLLED_BACK" for action in interrupted["actions"]),
                1,
            )
            request = replace(request, control=reopened)
            retry = recover_run(make_recovery_request(request, nonce="recover-retry"))
            self.assertEqual(retry.status, "ROLLED_BACK")
            self.assertEqual(reopened.load_journal("fixture-run")["status"], "ROLLED_BACK")
            self.assertEqual(
                _redirect_bytes(request),
                {
                    path: value
                    for path, value in {
                        Path("target/.beads/redirect"): b"local-authority-a\n",
                        Path("target-2/.beads/redirect"): b"local-authority-b\n",
                    }.items()
                },
            )

    def test_third_party_redirect_durably_needs_operator_without_source_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            request = _multi_target_request(root)
            source_before = _source_bytes(request)
            with self.assertRaises(TransactionCrash):
                apply_plan(replace(request, fault_at="after-rename"))
            changed = root / "target" / ".beads" / "redirect"
            changed.write_bytes(b"third-party\n")
            recovery = recover_run(make_recovery_request(request))
            self.assertEqual(recovery.status, "NEEDS_OPERATOR")
            self.assertEqual(
                request.control.load_journal("fixture-run")["status"], "NEEDS_OPERATOR"
            )
            self.assertEqual(changed.read_bytes(), b"third-party\n")
            self.assertEqual(_source_bytes(request), source_before)

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

    def test_recovery_backend_mismatch_durably_needs_operator(self) -> None:
        """Typed recovery preconditions fail closed before restoring a redirect."""

        with tempfile.TemporaryDirectory() as temp:
            request = make_request(Path(temp))
            request = ApplyRequest(**{**request.__dict__, "fault_at": "after-rename"})
            with self.assertRaises(TransactionCrash):
                apply_plan(request)
            request.adapter.backend = "dolt"
            recovery = recover_run(make_recovery_request(request))
            self.assertEqual(recovery.status, "NEEDS_OPERATOR")
            self.assertEqual(request.control.load_journal("fixture-run")["status"], "NEEDS_OPERATOR")

    def test_rollback_restores_noncanonical_prior_redirect_without_oracle(self) -> None:
        """Rollback restores journaled bytes even when prior authority is noncanonical."""

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            request = make_request(root, pre_redirect="local-authority\n")
            request = ApplyRequest(**{**request.__dict__, "fault_at": "after-rename"})
            with self.assertRaises(TransactionCrash):
                apply_plan(request)
            calls_before = len(request.adapter.authority_calls)
            recovery = recover_run(make_recovery_request(request))
            self.assertEqual(recovery.status, "ROLLED_BACK")
            self.assertEqual((root / "target" / ".beads" / "redirect").read_text(), "local-authority\n")
            self.assertEqual(len(request.adapter.authority_calls), calls_before)


if __name__ == "__main__":
    unittest.main()
