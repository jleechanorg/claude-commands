"""Journaled, one-canonical-store redirect transactions.

Only fixture adapters can exercise this module today.  The real br adapter has
no writer-exclusion proof and therefore fails before any mutation.  Cooperative
engine concurrency is covered by the canonical-keyed lease; malicious same-UID
replacement in the final syscall window is outside this claim and is never
represented as protected by these helpers.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import stat
import sys
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .adapters import (
    AdapterError,
    BackendAttestation,
    HealthAttestation,
    SourceSnapshot,
    WriterLease,
)
from .approval import ApprovalError, SignedApproval, verify_signed_approval
from .codec import canonical_json_bytes, sha256_hex
from .fsafety import open_descendant, open_trusted_tree
from .models import Manifest, Plan, Registry
from .planner import build_plan


class TransactionError(RuntimeError):
    """A transaction or recovery precondition failed without safe mutation."""


class TransactionCrash(BaseException):
    """Fixture-only crash injection.  Production requests cannot select it."""


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
    apply: bool
    registry: Registry
    manifest: Manifest
    plan: Plan
    adapter: object
    approval: SignedApproval | None
    verifier: object | None
    control: FileControlStore
    now: str
    run_id: str | None = None
    fault_at: str | None = None


@dataclass(frozen=True)
class RecoveryRequest:
    control: FileControlStore
    adapter: object
    run_id: str
    recover: bool = False
    registry: Registry | None = None
    manifest: Manifest | None = None
    plan: Plan | None = None
    approval: SignedApproval | None = None
    verifier: object | None = None
    now: str | None = None
    expected_journal_sha256: str | None = None


class FileControlStore:
    """Fixed-namespace journal/nonce storage; fixtures opt in explicitly."""

    fixture_only = False

    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def _ensure(self) -> None:
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        for child in ("journals", "receipts", "nonces", "locks"):
            (self.root / child).mkdir(mode=0o700, exist_ok=True)

    def journal_path(self, run_id: str) -> Path:
        if not run_id or any(item in run_id for item in ("/", "\\", "\x00", "..")):
            raise TransactionError("run ID is unsafe")
        return self.root / "journals" / f"{run_id}.json"

    def receipt_path(self, run_id: str) -> Path:
        return self.root / "receipts" / f"{run_id}.json"

    def _atomic_json(self, path: Path, value: dict[str, Any]) -> None:
        self._ensure()
        data = canonical_json_bytes(value)
        directory = path.parent
        fd, name = tempfile_name(directory, path.name)
        try:
            os.write(fd, data)
            _durable_fsync(fd)
            os.close(fd)
            fd = -1
            with _open_directory(directory) as directory_fd:
                os.replace(name, path.name, src_dir_fd=directory_fd, dst_dir_fd=directory_fd)
                _durable_fsync(directory_fd)
        finally:
            if fd >= 0:
                os.close(fd)
            try:
                with _open_directory(directory) as directory_fd:
                    os.unlink(name, dir_fd=directory_fd)
            except FileNotFoundError:
                pass

    def load_journal(self, run_id: str) -> dict[str, Any]:
        path = self.journal_path(run_id)
        try:
            raw = path.read_bytes()
            value = json.loads(raw)
        except (OSError, json.JSONDecodeError) as exc:
            raise TransactionError("journal is unavailable or malformed") from exc
        if type(value) is not dict:
            raise TransactionError("journal is malformed")
        return value

    def save_journal(self, journal: dict[str, Any]) -> None:
        self._atomic_json(self.journal_path(str(journal["run_id"])), journal)

    def save_receipt(self, receipt: dict[str, Any]) -> None:
        self._atomic_json(self.receipt_path(str(receipt["run_id"])), receipt)

    def reserve_nonce(self, key: str, nonce: str) -> None:
        self._ensure()
        path = self.root / "nonces" / f"{key}-{nonce}"
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
        except FileExistsError as exc:
            raise ApprovalError("approval nonce already used") from exc
        try:
            os.write(fd, b"reserved\n")
            _durable_fsync(fd)
        finally:
            os.close(fd)
        with _open_directory(path.parent) as directory_fd:
            _durable_fsync(directory_fd)

    def unfinished_journal(self, key: str) -> str | None:
        """Find an unfinished run by canonical identity before consuming a nonce."""

        self._ensure()
        journals = self.root / "journals"
        for path in sorted(journals.glob("*.json")):
            try:
                journal = json.loads(path.read_bytes())
            except (OSError, json.JSONDecodeError):
                raise TransactionError("journal index is malformed") from None
            if (
                type(journal) is dict
                and journal.get("canonical_key") == key
                and journal.get("status") in ("PREPARED", "APPLYING", "RECOVERING")
            ):
                run_id = journal.get("run_id")
                if not isinstance(run_id, str):
                    raise TransactionError("journal index is malformed")
                return run_id
        return None

    @contextmanager
    def lock(self, key: str) -> Iterator[None]:
        self._ensure()
        path = self.root / "locks" / f"{key}.lock"
        fd = os.open(path, os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o600)
        try:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise TransactionError("canonical transaction lock is contended") from exc
            yield
        finally:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                os.close(fd)


class FixtureControlStore(FileControlStore):
    """A disposable-only control store accepted with fixture-only adapters."""

    fixture_only = True


@contextmanager
def _open_directory(path: Path) -> Iterator[int]:
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0))
    try:
        yield fd
    finally:
        os.close(fd)


def tempfile_name(directory: Path, basename: str) -> tuple[int, str]:
    """Create a collision-resistant temporary only in the target directory."""

    with _open_directory(directory) as directory_fd:
        for _ in range(32):
            name = f".{basename}.beads-convergence-{uuid.uuid4().hex}.tmp"
            try:
                return os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600, dir_fd=directory_fd), name
            except FileExistsError:
                continue
    raise TransactionError("redirect temporary name collision")


def _durable_fsync(fd: int) -> None:
    try:
        if sys.platform == "darwin":
            command = getattr(fcntl, "F_FULLFSYNC", None)
            if command is None:
                raise TransactionError("F_FULLFSYNC is unavailable")
            fcntl.fcntl(fd, command)
        else:
            os.fsync(fd)
    except OSError as exc:
        raise TransactionError("durability sync failed") from exc


def _canonical_key(path: Path) -> str:
    info = os.stat(path, follow_symlinks=False)
    if not stat.S_ISDIR(info.st_mode):
        raise TransactionError("canonical Beads authority is not a directory")
    return f"{info.st_dev}-{info.st_ino}"


def _sources(path: Path, expected: list[dict[str, Any]]) -> list[dict[str, Any]]:
    measured: list[dict[str, Any]] = []
    for source in sorted(expected, key=lambda item: str(item["name"])):
        name = source["name"]
        if not isinstance(name, str) or "/" in name or name in ("", ".", ".."):
            raise TransactionError("source name is unsafe")
        member = path / name
        try:
            info = os.stat(member, follow_symlinks=False)
        except OSError as exc:
            raise TransactionError("source family changed") from exc
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise TransactionError("source family changed")
        measured.append({"name": name, "device": info.st_dev, "inode": info.st_ino,
                         "size": info.st_size, "sha256": hashlib.sha256(member.read_bytes()).hexdigest()})
    return measured


def _assert_sources(path: Path, expected: list[dict[str, Any]]) -> None:
    if _sources(path, expected) != sorted(expected, key=lambda item: str(item["name"])):
        raise TransactionError("source family changed")


def _redirect_state(beads: Path) -> dict[str, Any]:
    redirect = beads / "redirect"
    try:
        info = os.lstat(redirect)
    except FileNotFoundError:
        return {"present": False, "mode": None, "bytes": None}
    if not stat.S_ISREG(info.st_mode):
        raise TransactionError("redirect is not a regular file")
    return {"present": True, "mode": stat.S_IMODE(info.st_mode), "bytes": redirect.read_bytes().decode("utf-8")}


def _matches_pre(actual: dict[str, Any], pre: dict[str, Any]) -> bool:
    return all(actual.get(name) == pre.get(name) for name in ("present", "mode", "bytes"))


def _matches_intended(actual: dict[str, Any], intended: str) -> bool:
    return actual["present"] and actual["bytes"] == intended


def _verify_target(action: dict[str, Any]) -> Path:
    worktree = Path(action["worktree_path"])
    info = os.stat(worktree, follow_symlinks=False)
    if (info.st_dev, info.st_ino) != (action["directory_device"], action["directory_inode"]):
        raise TransactionError("worktree identity changed")
    return worktree


def _verify_authority(adapter: object, worktree: Path, canonical: Path, executable: object) -> None:
    resolve = getattr(adapter, "resolve_authority", None)
    if not callable(resolve):
        raise TransactionError("adapter cannot verify redirect authority")
    with open_trusted_tree(Path("/"), worktree) as handle:
        resolved = resolve(handle, executable)
    if not isinstance(resolved, Path) or _canonical_identity(resolved) != _canonical_identity(canonical):
        raise TransactionError("redirect does not resolve one hop to canonical authority")


def _write_redirect(beads: Path, pre: dict[str, Any], intended: str, fault_at: str | None, *, adapter: object, worktree: Path, canonical: Path, executable: object) -> None:
    info = os.stat(beads, follow_symlinks=False)
    if (info.st_dev, info.st_ino) != (pre["parent_device"], pre["parent_inode"]):
        raise TransactionError("redirect parent identity changed")
    actual = _redirect_state(beads)
    if _matches_intended(actual, intended):
        return
    if not _matches_pre(actual, pre):
        raise TransactionError("redirect bytes changed by a third party")
    mode = int(pre["mode"]) if pre["present"] else 0o600
    fd, temp = tempfile_name(beads, "redirect")
    try:
        os.write(fd, intended.encode("utf-8"))
        os.fchmod(fd, mode)
        if fault_at == "before-temp-fsync":
            raise TransactionCrash()
        _durable_fsync(fd)
        if fault_at == "after-temp-fsync":
            raise TransactionCrash()
    finally:
        os.close(fd)
    with _open_directory(beads) as directory_fd:
        if fault_at == "before-rename":
            raise TransactionCrash()
        os.replace(temp, "redirect", src_dir_fd=directory_fd, dst_dir_fd=directory_fd)
        if fault_at == "after-rename":
            raise TransactionCrash()
        _durable_fsync(directory_fd)
        if fault_at == "after-target-fsync":
            raise TransactionCrash()
    if _redirect_state(beads)["bytes"] != intended:
        raise TransactionError("redirect verification failed")
    _verify_authority(adapter, worktree, canonical, executable)


def _journal_action(action: dict[str, Any]) -> dict[str, Any]:
    redirect = dict(action["redirect"])
    return {"worktree_path": action["worktree_path"], "directory_device": action["directory_device"], "directory_inode": action["directory_inode"], "sources": list(action["sources"]),
            "pre": redirect, "intended": redirect["intended_bytes"], "state": "PENDING"}


def _assert_manifest_sources(manifest: Manifest) -> None:
    """A coherent pair of fixture snapshots includes canonical and targets."""

    records = [record for record in manifest.worktrees if record.sources]
    for _ in range(2):
        for record in records:
            _assert_sources(record.path / ".beads", [asdict(item) for item in record.sources])


def _reattest(adapter: object, manifest: Manifest) -> tuple[object, WriterLease]:
    """Run the typed adapter contract against retained directory descriptors."""

    try:
        executable = adapter.verify_binary(manifest.tracker_binary)
        with open_trusted_tree(Path("/"), manifest.canonical_beads) as canonical:
            backend = adapter.attest_backend(canonical)
            if not isinstance(backend, BackendAttestation) or backend.backend != "sqlite":
                raise TransactionError("canonical backend is not positively attested")
            lease = adapter.acquire_writer_exclusion(canonical, executable)
            if not isinstance(lease, WriterLease) or not lease.available:
                raise TransactionError("adapter cannot prove writer exclusion")
            snapshots: list[tuple[tuple[object, ...], ...]] = []
            for _ in range(2):
                current: list[tuple[object, ...]] = []
                for record in manifest.worktrees:
                    if not record.sources:
                        continue
                    with open_trusted_tree(Path("/"), record.path) as worktree:
                        health = adapter.verify_health(worktree, executable)
                        if not isinstance(health, HealthAttestation) or health.workspace_health != "healthy" or health.dirty_count or health.db_newer or health.jsonl_newer:
                            raise TransactionError("worktree health is not attested healthy")
                        with open_descendant(worktree, record.path / ".beads") as beads:
                            source = adapter.fingerprint_sources(beads)
                            if not isinstance(source, SourceSnapshot) or not source.quiescent or not source.lease_proven:
                                raise TransactionError("source snapshot is not lease-proven")
                            current.append((record.path, source.sources))
                snapshots.append(tuple(current))
            if snapshots[0] != snapshots[1]:
                raise TransactionError("source family changed during coherent snapshot")
            return executable, lease
    except (AdapterError, OSError, ValueError) as exc:
        raise TransactionError("typed adapter re-attestation failed") from exc


def _restore_redirect(beads: Path, pre: dict[str, Any], intended: str, *, adapter: object, worktree: Path, canonical: Path) -> None:
    """Reverse only an exactly-recorded intended redirect; preserve other bytes."""

    del adapter, worktree, canonical

    actual = _redirect_state(beads)
    if _matches_pre(actual, pre):
        return
    if not _matches_intended(actual, intended):
        raise TransactionError("redirect bytes changed by a third party")
    if not pre["present"]:
        with _open_directory(beads) as directory_fd:
            os.unlink("redirect", dir_fd=directory_fd)
            _durable_fsync(directory_fd)
        return
    fd, temp = tempfile_name(beads, "redirect")
    try:
        os.write(fd, str(pre["bytes"]).encode("utf-8"))
        os.fchmod(fd, int(pre["mode"]))
        _durable_fsync(fd)
    finally:
        os.close(fd)
    with _open_directory(beads) as directory_fd:
        os.replace(temp, "redirect", src_dir_fd=directory_fd, dst_dir_fd=directory_fd)
        _durable_fsync(directory_fd)
    if not _matches_pre(_redirect_state(beads), pre):
        raise TransactionError("rollback redirect verification failed")


def _rollback(journal: dict[str, Any], control: FileControlStore, adapter: object) -> bool:
    """Restore all recorded pre-states in reverse order, restarting safely."""

    try:
        for action in reversed(journal["actions"]):
            worktree = _verify_target(action)
            beads = worktree / ".beads"
            _restore_redirect(beads, action["pre"], str(action["intended"]), adapter=adapter, worktree=worktree, canonical=Path(journal["canonical_beads"]))
            action["state"] = "ROLLED_BACK"
            control.save_journal(journal)
        journal["status"] = "ROLLED_BACK"
        control.save_journal(journal)
        return True
    except (KeyError, OSError, TransactionError, TypeError, UnicodeError, ValueError):
        journal["status"] = "NEEDS_OPERATOR"
        control.save_journal(journal)
        return False


def _validate_request(request: ApplyRequest) -> tuple[str, str]:
    if request.apply is not True:
        raise TransactionError("explicit --apply is required")
    if not isinstance(request.control, FixtureControlStore) or not getattr(request.adapter, "fixture_only", False):
        raise TransactionError("real Beads apply is unavailable without a production writer lease")
    manifest = request.manifest
    plan = request.plan
    registry_hash = sha256_hex(canonical_json_bytes(request.registry))
    if manifest.registry_sha256 != registry_hash:
        raise TransactionError("registry binding does not match")
    if (manifest.repo_id != plan.repo_id or manifest.adapter != plan.adapter or
            manifest.canonical_beads != plan.canonical_beads or
            plan.manifest_sha256 != sha256_hex(canonical_json_bytes(manifest))):
        raise TransactionError("manifest or plan binding does not match")
    if build_plan(manifest).actions != plan.actions:
        raise TransactionError("plan is not the recomputed manifest plan")
    configs = [item for item in request.registry.repositories if item.repo_id == manifest.repo_id]
    if len(configs) != 1:
        raise TransactionError("registry does not uniquely bind repository")
    config = configs[0]
    if (config.adapter != manifest.adapter or config.canonical_beads != manifest.canonical_beads or
            config.tracker_binary != manifest.tracker_binary or config.git_binary != manifest.git_binary or
            getattr(request.adapter, "adapter_id", None) != manifest.adapter):
        raise TransactionError("registry, adapter, or binary binding does not match")
    identity = _canonical_identity(manifest.canonical_beads)
    fingerprint = verify_signed_approval(
        request.approval, request.verifier, now=request.now, operation="apply", repo_id=manifest.repo_id,
        registry_sha256=registry_hash, manifest_sha256=sha256_hex(canonical_json_bytes(manifest)),
        plan_sha256=plan.sha256, canonical_beads=manifest.canonical_beads, adapter=manifest.adapter,
        tracker_binary=manifest.tracker_binary, git_binary=manifest.git_binary,
        canonical_identity=identity, run_id=None, journal_sha256=None,
    )
    return _canonical_key(manifest.canonical_beads), fingerprint


def _canonical_identity(path: Path) -> tuple[int, int]:
    info = os.stat(path, follow_symlinks=False)
    return info.st_dev, info.st_ino


def _binding_payload(binding: object) -> dict[str, Any]:
    """Compare binary bindings in their durable JSON representation."""

    return json.loads(canonical_json_bytes(asdict(binding)))


def _lease(adapter: object, canonical: Path) -> object:
    acquire = getattr(adapter, "acquire_writer_exclusion", None)
    if not callable(acquire):
        raise TransactionError("adapter cannot prove writer exclusion")
    lease = acquire(canonical)
    if not getattr(lease, "available", False):
        raise TransactionError("adapter cannot prove writer exclusion")
    return lease


def _save_receipt(control: FileControlStore, journal: dict[str, Any]) -> None:
    control.save_receipt({"schema": "beads.redirect-convergence.receipt.v1", "run_id": journal["run_id"],
                          "status": journal["status"], "repo_id": journal["repo_id"],
                          "canonical_key": journal["canonical_key"], "signer_principal": journal["signer_principal"],
                          "signer_fingerprint": journal["signer_fingerprint"],
                          "journal_sha256": sha256_hex(canonical_json_bytes(journal))})


def apply_plan(request: ApplyRequest) -> ApplyReceipt:
    """Apply exactly one recomputed plan, journaling every redirect transition."""

    key, fingerprint = _validate_request(request)
    assert request.approval is not None
    run_id = request.run_id or uuid.uuid4().hex
    with request.control.lock(key):
        if request.fault_at == "before-prepared":
            raise TransactionCrash()
        if request.control.unfinished_journal(key) is not None:
            raise TransactionError("unfinished journal already owns canonical authority")
        request.control.reserve_nonce(key, request.approval.envelope.nonce)
        executable, lease = _reattest(request.adapter, request.manifest)
        if lease is None:
            raise TransactionError("writer exclusion lease disappeared")
        actions = [_journal_action(dict(action)) for action in request.plan.actions]
        for action in actions:
            _assert_sources(Path(action["worktree_path"]) / ".beads", action["sources"])
        journal = {"schema": "beads.redirect-convergence.journal.v1", "run_id": run_id,
                   "status": "PREPARED", "repo_id": request.manifest.repo_id, "canonical_key": key,
                   "canonical_beads": str(request.manifest.canonical_beads), "signer_principal": request.approval.envelope.signer_principal,
                   "signer_fingerprint": fingerprint, "registry_sha256": sha256_hex(canonical_json_bytes(request.registry)),
                   "manifest_sha256": sha256_hex(canonical_json_bytes(request.manifest)), "plan_sha256": request.plan.sha256,
                   "adapter": request.manifest.adapter, "tracker_binary": _binding_payload(request.manifest.tracker_binary),
                   "git_binary": _binding_payload(request.manifest.git_binary), "canonical_device": _canonical_identity(request.manifest.canonical_beads)[0],
                   "canonical_inode": _canonical_identity(request.manifest.canonical_beads)[1], "actions": actions}
        request.control.save_journal(journal)
        if request.fault_at == "after-prepared":
            raise TransactionCrash()
        journal["status"] = "APPLYING"
        request.control.save_journal(journal)
        try:
            for action in journal["actions"]:
                worktree = _verify_target(action)
                beads = worktree / ".beads"
                _assert_sources(beads, action["sources"])
                _write_redirect(beads, action["pre"], str(action["intended"]), request.fault_at, adapter=request.adapter, worktree=worktree, canonical=request.manifest.canonical_beads, executable=executable)
                action["state"] = "APPLIED"
                request.control.save_journal(journal)
                if request.fault_at == "after-progress":
                    raise TransactionCrash()
            if request.fault_at == "before-commit":
                raise TransactionCrash()
            journal["status"] = "COMMITTED"
            _assert_manifest_sources(request.manifest)
            request.control.save_journal(journal)
            if request.fault_at == "after-commit":
                raise TransactionCrash()
            _save_receipt(request.control, journal)
            if request.fault_at == "after-receipt":
                raise TransactionCrash()
        except TransactionCrash:
            raise
        except (KeyError, OSError, TransactionError, TypeError, UnicodeError, ValueError):
            _rollback(journal, request.control, request.adapter)
            raise
    return ApplyReceipt(run_id, "COMMITTED", request.manifest.repo_id, key, request.approval.envelope.signer_principal,
                        fingerprint, sha256_hex(canonical_json_bytes(journal)))


def recover_run(request: RecoveryRequest) -> RecoveryReceipt:
    """Resume a durable journal idempotently; never overwrite third-party bytes."""

    if request.recover is not True:
        raise TransactionError("explicit --recover is required")
    if not isinstance(request.control, FixtureControlStore) or not getattr(request.adapter, "fixture_only", False):
        raise TransactionError("real Beads recovery is unavailable without a production writer lease")
    journal = request.control.load_journal(request.run_id)
    journal_sha = sha256_hex(canonical_json_bytes(journal))
    if request.expected_journal_sha256 != journal_sha:
        raise TransactionError("journal hash does not match")
    if request.registry is None or request.manifest is None or request.plan is None or request.now is None:
        raise TransactionError("recovery bindings are required")
    key = str(journal.get("canonical_key", ""))
    if not key:
        raise TransactionError("journal lacks canonical key")
    with request.control.lock(key):
        registry_sha = sha256_hex(canonical_json_bytes(request.registry))
        if (
            journal.get("registry_sha256") != registry_sha
            or journal.get("manifest_sha256") != sha256_hex(canonical_json_bytes(request.manifest))
            or journal.get("plan_sha256") != request.plan.sha256
            or journal.get("canonical_beads") != str(request.manifest.canonical_beads)
            or journal.get("adapter") != request.manifest.adapter
            or journal.get("tracker_binary") != _binding_payload(request.manifest.tracker_binary)
            or journal.get("git_binary") != _binding_payload(request.manifest.git_binary)
        ):
            raise TransactionError("recovery bindings do not match journal")
        fingerprint = verify_signed_approval(
            request.approval, request.verifier, now=request.now, operation="recover",
            repo_id=request.manifest.repo_id, registry_sha256=registry_sha,
            manifest_sha256=sha256_hex(canonical_json_bytes(request.manifest)),
            plan_sha256=request.plan.sha256, canonical_beads=request.manifest.canonical_beads,
            adapter=request.manifest.adapter, tracker_binary=request.manifest.tracker_binary,
            git_binary=request.manifest.git_binary,
            canonical_identity=_canonical_identity(request.manifest.canonical_beads),
            run_id=request.run_id, journal_sha256=journal_sha,
        )
        if fingerprint != journal.get("signer_fingerprint"):
            raise TransactionError("recovery signer does not match journal")
        request.control.reserve_nonce(key, request.approval.envelope.nonce)
        if journal["status"] == "NEEDS_OPERATOR":
            return RecoveryReceipt(request.run_id, "NEEDS_OPERATOR", sha256_hex(canonical_json_bytes(journal)))
        try:
            _executable, lease = _reattest(request.adapter, request.manifest)
        except TransactionError:
            journal["status"] = "NEEDS_OPERATOR"
            request.control.save_journal(journal)
            return RecoveryReceipt(request.run_id, "NEEDS_OPERATOR", sha256_hex(canonical_json_bytes(journal)))
        if lease is None:
            raise TransactionError("writer exclusion lease disappeared")
        if journal["status"] == "COMMITTED":
            _save_receipt(request.control, journal)
            return RecoveryReceipt(request.run_id, "COMMITTED", sha256_hex(canonical_json_bytes(journal)))
        if journal["status"] not in ("PREPARED", "APPLYING"):
            raise TransactionError("journal has unknown terminal state")
        try:
            for action in reversed(journal["actions"]):
                worktree = _verify_target(action)
                beads = worktree / ".beads"
                _assert_sources(beads, action["sources"])
                _restore_redirect(beads, action["pre"], str(action["intended"]), adapter=request.adapter, worktree=worktree, canonical=request.manifest.canonical_beads)
                action["state"] = "ROLLED_BACK"
                request.control.save_journal(journal)
            journal["status"] = "ROLLED_BACK"
            request.control.save_journal(journal)
            _save_receipt(request.control, journal)
        except (KeyError, OSError, TransactionError, TypeError, UnicodeError, ValueError):
            journal["status"] = "NEEDS_OPERATOR"
            request.control.save_journal(journal)
            return RecoveryReceipt(request.run_id, "NEEDS_OPERATOR", sha256_hex(canonical_json_bytes(journal)))
    return RecoveryReceipt(request.run_id, "ROLLED_BACK", sha256_hex(canonical_json_bytes(journal)))
