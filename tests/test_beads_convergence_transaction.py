"""Fixture-only contract tests for journaled redirect application.

The fixture adapter is deliberately not a Beads adapter.  It creates disposable
SQLite-shaped files and proves the transaction engine never needs a real store.
"""

from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from scripts.beads_convergence.approval import (
    ApprovalError,
    SignedApproval,
)
from scripts.beads_convergence.codec import canonical_json_bytes, sha256_hex
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

    def __init__(self) -> None:
        self.lease_available = True

    def acquire_writer_exclusion(self, canonical: Path) -> object:
        del canonical
        return type("Lease", (), {"available": self.lease_available})()


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source(path: Path, name: str) -> SourceFingerprint:
    member = path / name
    info = member.stat()
    return SourceFingerprint(name, info.st_dev, info.st_ino, info.st_size, _digest(member))


def make_request(root: Path, *, apply: bool = True) -> ApplyRequest:
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
    parent = target_beads.stat()
    target_info = target.stat()
    redirect = RedirectState(
        False, None, None, parent.st_dev, parent.st_ino,
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
        plan.sha256, canonical, "br-sqlite-v1", binding, binding, "ops@example.test",
        "SHA256:fixture-external-key",
    )
    return ApplyRequest(
        apply=apply, registry=registry, manifest=manifest, plan=plan,
        adapter=FixtureAdapter(), approval=SignedApproval(approval, b"fixture-external-signature"),
        verifier=FixtureVerifier(), control=FixtureControlStore(root / "control"),
        now="2026-08-27T12:00:00Z", run_id="fixture-run",
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


if __name__ == "__main__":
    unittest.main()
