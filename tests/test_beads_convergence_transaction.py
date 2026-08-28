"""Fixture-only contract tests for journaled redirect application.

The fixture adapter is deliberately not a Beads adapter.  It creates disposable
SQLite-shaped files and proves the transaction engine never needs a real store.
"""

from __future__ import annotations

import hashlib
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from scripts.beads_convergence.adapters import (
    BackendAttestation,
    HealthAttestation,
    SourceMember,
    SourceSnapshot,
    WriterLease,
)
from scripts.beads_convergence.approval import (
    ApprovalError,
    SignedApproval,
    tool_tree_sha256,
)
from scripts.beads_convergence.codec import canonical_json_bytes, sha256_hex
from scripts.beads_convergence.fsafety import DirectoryHandle
from scripts.beads_convergence.models import (
    ApprovalEnvelope,
    BinaryBinding,
    HealthFingerprint,
    Manifest,
    RedirectState,
    Registry,
    RepositoryConfig,
    SourceFingerprint,
    WorktreeRecord,
)
from scripts.beads_convergence.planner import build_plan
from scripts.beads_convergence.transaction import (
    ApplyRequest,
    FixtureControlStore,
    RecoveryRequest,
    TransactionCrash,
    TransactionError,
    apply_plan,
)


class FixtureVerifier:
    """An independently-owned test trust oracle; it is not production signing."""

    fixture_only = True
    fingerprint = "SHA256:fixture-external-key"

    def verify(self, envelope: bytes, signature: bytes, **bindings: object) -> bool:
        return (
            signature == b"fixture-external-signature"
            and bindings["namespace"] == "beads-redirect-convergence-v1@jleechan.org"
            and bindings["principal"] == "ops@example.test"
            and envelope.startswith(b'{"adapter"')
        )


class FixtureAdapter:
    """Disposable filesystem adapter with a proven fixture writer lease."""

    adapter_id = "br-sqlite-v1"
    fixture_only = True

    def __init__(self, canonical: Path | None = None) -> None:
        self.lease_available = True
        self.canonical = canonical
        self.backend = "sqlite"
        self.healthy = True
        self.source_proven = True
        self.authority_calls: list[tuple[object, object, bytes]] = []

    def verify_binary(self, binding: BinaryBinding) -> object:
        del binding
        return object()

    def attest_backend(self, beads: object) -> BackendAttestation:
        del beads
        return BackendAttestation(self.backend, ("beads.db", "issues.jsonl"))

    def verify_health(self, worktree: object, executable: object) -> HealthAttestation:
        del worktree, executable
        return HealthAttestation(0 if self.healthy else 1, False, False, "healthy", {})

    def acquire_writer_exclusion(self, canonical: object, executable: object) -> WriterLease:
        self.canonical = Path(canonical.display_path)
        del executable
        return WriterLease(self.lease_available, "fixture", "fixture")

    def fingerprint_sources(self, beads: object) -> SourceSnapshot:
        path = Path(beads.display_path)
        members = tuple(
            SourceMember(item.name, item.device, item.inode, item.size, item.sha256)
            for item in (_source(path, "beads.db"), _source(path, "issues.jsonl"))
        )
        return SourceSnapshot(members, True, False, self.source_proven, "fixture lease")

    def resolve_authority(self, worktree: object, executable: object) -> Path:
        path = Path(worktree.display_path)
        assert self.canonical is not None
        redirect = path / ".beads" / "redirect"
        self.authority_calls.append((worktree, executable, redirect.read_bytes()))
        if redirect.is_file() and redirect.read_text() == str(self.canonical) + "\n":
            return self.canonical
        return path / ".beads"


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source(path: Path, name: str) -> SourceFingerprint:
    member = path / name
    info = member.stat()
    return SourceFingerprint(name, info.st_dev, info.st_ino, info.st_size, _digest(member))


def make_request(root: Path, *, apply: bool = True, pre_redirect: str | None = None) -> ApplyRequest:
    canonical = root / "canonical" / ".beads"
    target = root / "target"
    evidence = root / "evidence"
    for beads in (canonical, target / ".beads"):
        beads.mkdir(parents=True)
        (beads / "beads.db").write_bytes(b"SQLite format 3\x00fixture")
        (beads / "issues.jsonl").write_bytes(b'{"id":"fixture"}\n')
    evidence.mkdir()
    binding = BinaryBinding(Path("/bin/true"), "fixture", "a" * 64)
    config = RepositoryConfig(
        "repo-a", "br-sqlite-v1", root / "canonical", canonical, (root,), (),
        binding, binding, evidence,
    )
    registry = Registry("beads.redirect-convergence.registry.v1", "fixture", (config,))
    target_beads = target / ".beads"
    if pre_redirect is not None:
        (target_beads / "redirect").write_text(pre_redirect)
    parent = target_beads.stat()
    target_info = target.stat()
    redirect = RedirectState(
        pre_redirect is not None, 0o644 if pre_redirect is not None else None, pre_redirect, parent.st_dev, parent.st_ino,
        "fixture-redirect-v1", str(canonical) + "\n", "b" * 64,
    )
    health = HealthFingerprint(0, False, False, "healthy", "c" * 64)
    manifest = Manifest(
        "beads.redirect-convergence.manifest.v1", sha256_hex(canonical_json_bytes(registry)),
        "repo-a", "br-sqlite-v1", canonical, binding, binding,
        (
            WorktreeRecord(canonical.parent, "canonical", canonical.parent.stat().st_dev,
                           canonical.parent.stat().st_ino, (_source(canonical, "beads.db"), _source(canonical, "issues.jsonl")), None, "sqlite", health),
            WorktreeRecord(target, "noncanonical", target_info.st_dev, target_info.st_ino,
                           (_source(target_beads, "beads.db"), _source(target_beads, "issues.jsonl")), redirect, "sqlite", health),
        ),
        "fixture-redirect-v1", str(canonical) + "\n", "b" * 64,
    )
    plan = build_plan(manifest)
    approval = ApprovalEnvelope(
        "beads.redirect-convergence.approval.v1", "apply", "repo-a", "nonce-1",
        "2026-08-27T00:00:00Z", "2026-08-28T00:00:00Z",
        sha256_hex(canonical_json_bytes(registry)), sha256_hex(canonical_json_bytes(manifest)),
        plan.sha256, canonical, "br-sqlite-v1", binding, binding,
        canonical.stat().st_dev, canonical.stat().st_ino, tool_tree_sha256(), None, None,
        "ops@example.test",
        "SHA256:fixture-external-key",
    )
    return ApplyRequest(
        apply=apply, registry=registry, manifest=manifest, plan=plan,
        adapter=FixtureAdapter(), approval=SignedApproval(approval, b"fixture-external-signature"),
        verifier=FixtureVerifier(), control=FixtureControlStore(root / "control"),
        now="2026-08-27T12:00:00Z", run_id="fixture-run",
    )


def make_recovery_request(request: ApplyRequest, *, nonce: str = "recover-nonce") -> RecoveryRequest:
    """Create a separate fixture-only recovery capability from durable journal bytes."""

    journal = request.control.load_journal(str(request.run_id))
    approval = request.approval
    assert approval is not None
    envelope = replace(
        approval.envelope,
        operation="recover",
        nonce=nonce,
        run_id=request.run_id,
        journal_sha256=sha256_hex(canonical_json_bytes(journal)),
    )
    return RecoveryRequest(
        request.control, request.adapter, str(request.run_id), True, request.registry,
        request.manifest, request.plan, SignedApproval(envelope, approval.signature),
        request.verifier, request.now, sha256_hex(canonical_json_bytes(journal)),
    )


class TransactionTest(unittest.TestCase):
    def test_apply_requires_literal_flag_and_all_bindings(self) -> None:
        with (
            tempfile.TemporaryDirectory() as temp,
            self.assertRaisesRegex(TransactionError, "explicit --apply"),
        ):
            apply_plan(make_request(Path(temp), apply=False))

    def test_apply_one_repo_cannot_change_neighbor_repo(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            request = make_request(root)
            neighbor = root / "neighbor"
            (neighbor / ".beads").mkdir(parents=True)
            (neighbor / ".beads" / "third-party").write_bytes(b"unchanged")
            before = _digest(neighbor / ".beads" / "third-party")
            receipt = apply_plan(request)
            self.assertEqual(receipt.status, "COMMITTED")
            self.assertEqual(_digest(neighbor / ".beads" / "third-party"), before)
            self.assertEqual(
                (root / "target" / ".beads" / "redirect").read_bytes(),
                (str(root / "canonical" / ".beads") + "\n").encode(),
            )

    def test_readable_artifacts_cannot_self_authorize_apply(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            request = make_request(Path(temp))
            request = ApplyRequest(**{**request.__dict__, "approval": None})
            with self.assertRaisesRegex(ApprovalError, "external approval"):
                apply_plan(request)

    def test_approval_nonce_is_one_use_and_receipt_names_signer(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            request = make_request(Path(temp))
            receipt = apply_plan(request)
            self.assertEqual(receipt.signer_principal, "ops@example.test")
            self.assertEqual(receipt.signer_fingerprint, "SHA256:fixture-external-key")
            with self.assertRaisesRegex(ApprovalError, "already used"):
                apply_plan(request)

    def test_unfinished_canonical_journal_refuses_new_apply_before_nonce(self) -> None:
        """A crashed run owns its canonical key until separately recovered."""

        with tempfile.TemporaryDirectory() as temp:
            request = make_request(Path(temp))
            crashed = replace(request, fault_at="after-prepared")
            with self.assertRaises(TransactionCrash):
                apply_plan(crashed)
            assert request.approval is not None
            second_approval = SignedApproval(
                replace(request.approval.envelope, nonce="nonce-2"),
                request.approval.signature,
            )
            second = replace(request, run_id="second-run", approval=second_approval)
            with self.assertRaisesRegex(TransactionError, "unfinished journal"):
                apply_plan(second)

    def test_source_drift_before_redirect_leaves_target_untouched(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            request = make_request(root)
            (root / "target" / ".beads" / "issues.jsonl").write_bytes(b"drift\n")
            with self.assertRaisesRegex(TransactionError, "source family changed"):
                apply_plan(request)
            self.assertFalse((root / "target" / ".beads" / "redirect").exists())

    def test_symlink_redirect_is_rejected_without_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            request = make_request(root)
            redirect = root / "target" / ".beads" / "redirect"
            redirect.symlink_to(root / "canonical" / ".beads")
            with self.assertRaisesRegex(TransactionError, "redirect is not a regular file"):
                apply_plan(request)
            self.assertTrue(redirect.is_symlink())

    def test_unavailable_real_style_lease_fails_before_redirect_write(self) -> None:
        """A non-fixture adapter never reaches a redirect mutation without a lease."""

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            request = make_request(root)
            request.adapter.fixture_only = False
            with self.assertRaisesRegex(TransactionError, "real Beads apply"):
                apply_plan(request)
            self.assertFalse((root / "target" / ".beads" / "redirect").exists())

    def test_post_apply_authority_uses_retained_handle_and_redirect_bytes(self) -> None:
        """The authority oracle sees the renamed bytes through a DirectoryHandle."""

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            request = make_request(root)
            apply_plan(request)
            adapter = request.adapter
            assert isinstance(adapter, FixtureAdapter)
            handle, executable, bytes_seen = adapter.authority_calls[-1]
            self.assertIsInstance(handle, DirectoryHandle)
            self.assertIsNotNone(executable)
            self.assertEqual(bytes_seen, (str(root / "canonical" / ".beads") + "\n").encode())


if __name__ == "__main__":
    unittest.main()
