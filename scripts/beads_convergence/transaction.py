"""Fail-closed production boundary for Beads redirect mutation.

The shipped ``BrSqliteV1Adapter`` cannot yet prove a retained writer-exclusion
lease.  Production apply and recovery therefore remain unavailable.  The
disposable mutation/crash harness lives under ``tests/`` and is not importable
from this runtime package.
"""

from __future__ import annotations

from dataclasses import dataclass

from .approval import SignedApproval
from .models import Manifest, Plan, Registry


class TransactionError(RuntimeError):
    """A transaction request failed closed without opening mutation state."""


@dataclass(frozen=True)
class ApplyReceipt:
    run_id: str
    status: str
    repo_id: str
    canonical_key: str
    signer_principal: str
    signer_fingerprint: str
    journal_sha256: str


@dataclass(frozen=True)
class RecoveryReceipt:
    run_id: str
    status: str
    journal_sha256: str


@dataclass(frozen=True)
class ApplyRequest:
    """Caller data only; no adapter, verifier, control, or fault-injection seam."""

    apply: bool
    registry: Registry
    manifest: Manifest
    plan: Plan
    approval: SignedApproval | None
    now: str


@dataclass(frozen=True)
class RecoveryRequest:
    """Caller data only; recovery cannot select an execution authority."""

    run_id: str
    recover: bool = False
    registry: Registry | None = None
    manifest: Manifest | None = None
    plan: Plan | None = None
    approval: SignedApproval | None = None
    now: str | None = None
    expected_journal_sha256: str | None = None


def apply_plan(request: ApplyRequest) -> ApplyReceipt:
    """Reject production apply until the real adapter proves a writer lease."""

    del request
    raise TransactionError(
        "production writer lease is unavailable; apply is disabled before mutation"
    )


def recover_run(request: RecoveryRequest) -> RecoveryReceipt:
    """Reject production recovery until the real adapter proves a writer lease."""

    del request
    raise TransactionError(
        "production writer lease is unavailable; recovery is disabled before mutation"
    )
