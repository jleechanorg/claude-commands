"""External, SHA-bound approval verification for redirect transactions.

The public key's custody is an out-of-band provisioning gate: a verifier cannot
infer that a key is hardware-held, off-host, or separately administered merely
from an SSH public key.  Callers must provide a verifier installed by that
independent control; readable registry/plan files never authorize an apply.
"""

from __future__ import annotations

import base64
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
from .fsafety import CHILD_ENV, open_trusted_tree, open_verified_executable
from .models import ApprovalEnvelope, BinaryBinding

SSH_NAMESPACE = "beads-redirect-convergence-v1@jleechan.org"
APPROVAL_SCHEMA = "beads.redirect-convergence.approval.v1"
_ALLOWED_SIGNERS_MAX_BYTES = 1024 * 1024


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


def tool_tree_sha256() -> str:
    """Bind the exact shipped transaction contract, never a caller-supplied path."""

    import hashlib

    root = Path(__file__).resolve().parents[2]
    files = (
        root / "scripts/beads_convergence/approval.py",
        root / "scripts/beads_convergence/transaction.py",
        root / ".claude/skills/beads-redirect-convergence/references/approval-v1.schema.json",
        root / ".claude/skills/beads-redirect-convergence/references/journal-v1.schema.json",
        root / ".claude/skills/beads-redirect-convergence/references/receipt-v1.schema.json",
    )
    digest = hashlib.sha256()
    for path in files:
        digest.update(os.fspath(path.relative_to(root)).encode() + b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


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
    canonical_identity: tuple[int, int],
    run_id: str | None,
    journal_sha256: str | None,
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
        ("canonical_device", canonical_identity[0]),
        ("canonical_inode", canonical_identity[1]),
        ("run_id", run_id),
        ("journal_sha256", journal_sha256),
    )
    for name, value in expected:
        if getattr(envelope, name) != value:
            raise ApprovalError(f"approval {name} does not match")
    if envelope.tool_tree_sha256 != tool_tree_sha256():
        raise ApprovalError("approval tool tree does not match")
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

    def __init__(self, verifier_binary: BinaryBinding) -> None:
        self._binding = verifier_binary
        self.fingerprint = ""

    @staticmethod
    def _fingerprint(allowed_fd: int, principal: str) -> str:
        os.lseek(allowed_fd, 0, os.SEEK_SET)
        info = os.fstat(allowed_fd)
        if info.st_size > _ALLOWED_SIGNERS_MAX_BYTES:
            raise ApprovalError("allowed signers exceeds size limit")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(allowed_fd, 64 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > _ALLOWED_SIGNERS_MAX_BYTES:
                raise ApprovalError("allowed signers exceeds size limit")
            chunks.append(chunk)
        try:
            raw = b"".join(chunks).decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ApprovalError("allowed signers is not UTF-8") from exc
        keys: list[bytes] = []
        for line in raw.splitlines():
            fields = line.split()
            if len(fields) >= 3 and fields[0] == principal and fields[1].startswith("ssh-"):
                try:
                    keys.append(base64.b64decode(fields[2], validate=True))
                except ValueError as exc:
                    raise ApprovalError("allowed signers key is malformed") from exc
        if len(keys) != 1:
            raise ApprovalError("allowed signers must admit exactly one key for principal")
        import hashlib

        return "SHA256:" + base64.b64encode(hashlib.sha256(keys[0]).digest()).decode().rstrip("=")

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
            with open_trusted_tree(Path("/"), compiled_trust_root()) as trust:
                allowed_fd = os.open("allowed_signers", os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0), dir_fd=trust.fd)
                info = os.fstat(allowed_fd)
                if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or stat.S_IMODE(info.st_mode) & 0o022:
                    os.close(allowed_fd)
                    raise ApprovalError("allowed signers file is unsafe")
                self.fingerprint = self._fingerprint(allowed_fd, principal)
            with tempfile.NamedTemporaryFile(prefix="beads-signature-", delete=False) as handle:
                handle.write(signature)
                signature_path = Path(handle.name)
            try:
                executable = open_verified_executable(self._binding)
                try:
                    result = subprocess.run(
                        (f"/dev/fd/{executable.fd}", "-Y", "verify", "-n", SSH_NAMESPACE, "-I", principal,
                         "-f", f"/dev/fd/{allowed_fd}", "-s", os.fspath(signature_path)),
                        input=envelope, capture_output=True, check=False, timeout=30,
                        env=CHILD_ENV, pass_fds=(executable.fd, allowed_fd),
                    )
                    return result.returncode == 0
                finally:
                    executable.close()
            finally:
                signature_path.unlink(missing_ok=True)
                os.close(allowed_fd)
        except (ApprovalError, OSError, subprocess.SubprocessError):
            return False
