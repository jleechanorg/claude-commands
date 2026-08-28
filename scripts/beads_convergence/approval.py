"""External, SHA-bound approval verification for redirect transactions.

The public key's custody is an out-of-band provisioning gate: a verifier cannot
infer that a key is hardware-held, off-host, or separately administered merely
from an SSH public key.  Callers must provide a verifier installed by that
independent control; readable registry/plan files never authorize an apply.
"""

from __future__ import annotations

import datetime as dt
import os
import stat
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol

from .codec import canonical_json_bytes
from .models import ApprovalEnvelope

SSH_NAMESPACE = "beads-redirect-convergence-v1@jleechan.org"
APPROVAL_SCHEMA = "beads.redirect-convergence.approval.v1"


class ApprovalError(RuntimeError):
    """The independently-controlled approval is absent, stale, or mismatched."""


def compiled_trust_root() -> Path:
    """Return the only allowed trust root; there is intentionally no override."""

    if sys.platform == "darwin":
        return Path("/Library/Application Support/Beads Convergence/trust")
    return Path("/etc/beads-convergence/trust")


@dataclass(frozen=True)
class SignedApproval:
    envelope: ApprovalEnvelope
    signature: bytes


class ApprovalVerifier(Protocol):
    fingerprint: str

    def verify(
        self, envelope: bytes, signature: bytes, **bindings: object
    ) -> bool: ...


def envelope_bytes(envelope: ApprovalEnvelope) -> bytes:
    """Return the exact canonical bytes which must be passed to SSH on stdin."""

    return canonical_json_bytes(asdict(envelope))


def _parse_time(value: str) -> dt.datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ApprovalError("approval timestamps must be UTC RFC3339")
    try:
        return dt.datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ApprovalError("approval timestamp is malformed") from exc


def verify_signed_approval(
    signed: SignedApproval | None,
    verifier: ApprovalVerifier | None,
    *,
    now: str,
    operation: str,
    repo_id: str,
    registry_sha256: str,
    manifest_sha256: str,
    plan_sha256: str,
    canonical_beads: Path,
    adapter: str,
    tracker_binary: object,
    git_binary: object,
) -> str:
    """Verify all semantic bindings before reserving an approval nonce."""

    if signed is None or verifier is None:
        raise ApprovalError("external approval is required")
    envelope = signed.envelope
    if envelope.schema != APPROVAL_SCHEMA:
        raise ApprovalError("approval schema is unsupported")
    if not isinstance(signed.signature, bytes) or not signed.signature:
        raise ApprovalError("external approval signature is required")
    if envelope.operation != operation:
        raise ApprovalError("approval operation does not match")
    expected = (
        ("repo_id", repo_id),
        ("registry_sha256", registry_sha256),
        ("manifest_sha256", manifest_sha256),
        ("plan_sha256", plan_sha256),
        ("canonical_beads", canonical_beads),
        ("adapter", adapter),
        ("tracker_binary", tracker_binary),
        ("git_binary", git_binary),
    )
    for name, value in expected:
        if getattr(envelope, name) != value:
            raise ApprovalError(f"approval {name} does not match")
    issued, expires, current = map(_parse_time, (envelope.issued_at, envelope.expires_at, now))
    if issued > current or expires <= current:
        raise ApprovalError("approval is expired or not yet valid")
    if not envelope.nonce:
        raise ApprovalError("approval nonce is required")
    if not envelope.signer_principal:
        raise ApprovalError("approval signer principal is required")
    if not envelope.signer_fingerprint:
        raise ApprovalError("approval signer fingerprint is required")
    # The verifier chooses the compiled trust root and fixed namespace.  The
    # envelope is deliberately unable to select any verifier input.
    if not verifier.verify(
        envelope_bytes(envelope),
        signed.signature,
        namespace=SSH_NAMESPACE,
        principal=envelope.signer_principal,
        trust_root=compiled_trust_root(),
    ):
        raise ApprovalError("external approval signature did not verify")
    fingerprint = getattr(verifier, "fingerprint", None)
    if not isinstance(fingerprint, str) or not fingerprint:
        raise ApprovalError("external approval verifier has no signer fingerprint")
    if envelope.signer_fingerprint != fingerprint:
        raise ApprovalError("approval signer fingerprint does not match")
    return fingerprint


def _verify_root_owned_tree(root: Path) -> None:
    """Reject unsafe trust-root ancestors before invoking ssh-keygen."""

    if root != compiled_trust_root():
        raise ApprovalError("trust root override is forbidden")
    current = Path("/")
    for part in root.parts[1:]:
        current /= part
        try:
            info = os.stat(current, follow_symlinks=False)
        except OSError as exc:
            raise ApprovalError("compiled trust root is unavailable") from exc
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != 0:
            raise ApprovalError("trust root is not root-owned")
        if stat.S_IMODE(info.st_mode) & 0o022:
            raise ApprovalError("trust root has unsafe mode")


class SshApprovalVerifier:
    """Production SSH verifier with fixed signer identity, namespace and root."""

    def __init__(self, fingerprint: str) -> None:
        self.fingerprint = fingerprint

    def verify(self, envelope: bytes, signature: bytes, **bindings: object) -> bool:
        root = bindings.get("trust_root")
        namespace = bindings.get("namespace")
        principal = bindings.get("principal")
        if root != compiled_trust_root() or namespace != SSH_NAMESPACE:
            return False
        if not isinstance(principal, str) or not principal:
            return False
        try:
            _verify_root_owned_tree(compiled_trust_root())
            allowed = compiled_trust_root() / "allowed_signers"
            info = os.stat(allowed, follow_symlinks=False)
            if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or stat.S_IMODE(info.st_mode) & 0o022:
                raise ApprovalError("allowed signers file is unsafe")
            with tempfile.NamedTemporaryFile(prefix="beads-signature-", delete=False) as handle:
                handle.write(signature)
                signature_path = Path(handle.name)
            try:
                result = subprocess.run(
                    ("ssh-keygen", "-Y", "verify", "-n", SSH_NAMESPACE, "-I", principal,
                     "-f", os.fspath(allowed), "-s", os.fspath(signature_path)),
                    input=envelope, capture_output=True,
                    check=False, timeout=30,
                )
                return result.returncode == 0
            finally:
                signature_path.unlink(missing_ok=True)
        except (ApprovalError, OSError, subprocess.SubprocessError):
            return False
