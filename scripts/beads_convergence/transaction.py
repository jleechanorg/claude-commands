"""Journaled, one-canonical-store redirect transactions.

Only fixture adapters can exercise this module today.  The real br adapter has
no writer-exclusion proof and therefore fails before any mutation.  Cooperative
engine concurrency is covered by the canonical-keyed lease; malicious same-UID
replacement in the final syscall window is outside this claim and is never
represented as protected by these helpers.
"""

from __future__ import annotations

import errno
import fcntl
import hashlib
import json
import os
import pwd
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
from .fsafety import DirectoryHandle, FsafetyError, open_descendant, open_trusted_tree
from .inventory import InventoryError, build_manifest
from .models import Manifest, Plan, Registry
from .planner import build_plan
from .registry import RegistryError, validate_registry


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


@dataclass
class RetainedTopology:
    """Directory descriptors held from re-attestation through mutation."""

    canonical: DirectoryHandle
    targets: dict[tuple[int, int], tuple[DirectoryHandle, DirectoryHandle]]

    def action_target(self, action: dict[str, Any]) -> tuple[DirectoryHandle, DirectoryHandle]:
        key = (int(action["directory_device"]), int(action["directory_inode"]))
        target = self.targets.get(key)
        if target is None:
            raise TransactionError("retained worktree is unavailable")
        worktree, beads = target
        worktree.verify_identity()
        beads.verify_identity()
        return target

    def close(self) -> None:
        for worktree, beads in self.targets.values():
            beads.close()
            worktree.close()
        self.targets.clear()
        self.canonical.close()


class FileControlStore:
    """Fixed-namespace journal/nonce storage; fixtures opt in explicitly."""

    fixture_only = False
    _CHILDREN = ("journals", "receipts", "nonces", "locks")

    def __init__(self, root: Path | None = None) -> None:
        if self.fixture_only:
            if root is None:
                raise TransactionError("fixture control root is required")
            self.root = Path(root)
            self._protected_start = len(self.root.parts) - 2
            self._create_start = self._protected_start
        else:
            home = Path(pwd.getpwuid(os.geteuid()).pw_dir)
            self.root = home / ".local/state/beads-convergence/control"
            if root is not None and Path(root) != self.root:
                raise TransactionError("control root is fixed by the effective user")
            self._protected_start = len(home.parts) - 2
            self._create_start = len(home.parts) - 1
        self._root_fd = -1
        self._root_identity: tuple[int, int] | None = None
        self._ancestors: dict[int, tuple[int, int, int]] = {}
        self._directories: dict[str, tuple[int, int, int]] = {}
        self._active_locks: list[tuple[str, int, int, int]] = []

    @staticmethod
    def _directory_flags() -> int:
        nofollow = getattr(os, "O_NOFOLLOW", None)
        directory = getattr(os, "O_DIRECTORY", None)
        if not isinstance(nofollow, int) or nofollow == 0:
            raise TransactionError("O_NOFOLLOW is unavailable")
        if not isinstance(directory, int) or directory == 0:
            raise TransactionError("O_DIRECTORY is unavailable")
        return os.O_RDONLY | directory | getattr(os, "O_CLOEXEC", 0) | nofollow

    @staticmethod
    def _artifact_flags(flags: int) -> int:
        nofollow = getattr(os, "O_NOFOLLOW", None)
        if not isinstance(nofollow, int) or nofollow == 0:
            raise TransactionError("O_NOFOLLOW is unavailable")
        return flags | getattr(os, "O_CLOEXEC", 0) | nofollow

    def _open_control_component(self, directory_fd: int, component: str) -> int:
        try:
            return os.open(component, self._directory_flags(), dir_fd=directory_fd)
        except OSError as exc:
            if (
                sys.platform == "darwin"
                and component in {"var", "tmp"}
                and exc.errno in (errno.ELOOP, errno.ENOTDIR)
            ):
                alias_root = os.open("private", self._directory_flags(), dir_fd=directory_fd)
                try:
                    return os.open(component, self._directory_flags(), dir_fd=alias_root)
                finally:
                    os.close(alias_root)
            raise

    @staticmethod
    def _token(value: str, label: str) -> str:
        if not isinstance(value, str) or not value or any(
            item in value for item in ("/", "\\", "\x00", "..")
        ):
            raise TransactionError(f"{label} is unsafe")
        return value

    @staticmethod
    def _directory_info(fd: int) -> os.stat_result:
        info = os.fstat(fd)
        if (
            not stat.S_ISDIR(info.st_mode)
            or info.st_uid != os.geteuid()
            or stat.S_IMODE(info.st_mode) != 0o700
        ):
            raise TransactionError("unsafe control directory")
        return info

    @staticmethod
    def _artifact_info(fd: int) -> os.stat_result:
        info = os.fstat(fd)
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_nlink != 1
            or info.st_uid != os.geteuid()
            or stat.S_IMODE(info.st_mode) != 0o600
        ):
            raise TransactionError("unsafe control artifact")
        return info

    def _verify_control_path(self) -> None:
        """Bind and re-open every effective-user control ancestor by identity."""

        parts = self.root.parts
        if not self.root.is_absolute() or not parts or parts[0] != os.sep:
            raise TransactionError("control hierarchy is unavailable")
        initial = self._root_fd < 0
        current = os.open(os.sep, self._directory_flags())
        try:
            for index, component in enumerate(parts[1:]):
                try:
                    nxt = self._open_control_component(current, component)
                except FileNotFoundError:
                    if not initial or index < self._create_start:
                        raise
                    os.mkdir(component, 0o700, dir_fd=current)
                    _durable_fsync(current)
                    nxt = self._open_control_component(current, component)
                if index >= self._protected_start:
                    info = self._directory_info(nxt)
                    retained = self._ancestors.get(index)
                    identity = (info.st_dev, info.st_ino)
                    if retained is None:
                        self._ancestors[index] = (os.dup(nxt), *identity)
                    else:
                        retained_fd, device, inode = retained
                        retained_info = self._directory_info(retained_fd)
                        if (
                            (retained_info.st_dev, retained_info.st_ino) != (device, inode)
                            or identity != (device, inode)
                        ):
                            raise TransactionError("retained control directory changed")
                if index == len(parts) - 2:
                    info = self._directory_info(nxt)
                    identity = (info.st_dev, info.st_ino)
                    if self._root_fd < 0:
                        self._root_fd = os.dup(nxt)
                        self._root_identity = identity
                    elif self._root_identity != identity:
                        raise TransactionError("retained control directory changed")
                os.close(current)
                current = nxt
        except (OSError, TransactionError) as exc:
            if initial:
                self._close_retained()
            if isinstance(exc, TransactionError):
                raise
            raise TransactionError("control hierarchy is unavailable") from exc
        finally:
            os.close(current)

    def _close_retained(self) -> None:
        for fd, _device, _inode in self._ancestors.values():
            os.close(fd)
        self._ancestors.clear()
        if self._root_fd >= 0:
            os.close(self._root_fd)
            self._root_fd = -1
        self._root_identity = None

    def _open_child_directory(self, child: str) -> int:
        try:
            return os.open(child, self._directory_flags(), dir_fd=self._root_fd)
        except OSError as exc:
            raise TransactionError("control hierarchy is unavailable") from exc

    def _ensure(self) -> None:
        self._verify_control_path()
        root_info = self._directory_info(self._root_fd)
        if self._root_identity != (root_info.st_dev, root_info.st_ino):
            raise TransactionError("retained control directory changed")
        for child in self._CHILDREN:
            retained = self._directories.get(child)
            if retained is None:
                try:
                    os.mkdir(child, 0o700, dir_fd=self._root_fd)
                    _durable_fsync(self._root_fd)
                except FileExistsError:
                    pass
                fd = self._open_child_directory(child)
                info = self._directory_info(fd)
                self._directories[child] = (fd, info.st_dev, info.st_ino)
            else:
                fd, device, inode = retained
                info = self._directory_info(fd)
                reopened = -1
                try:
                    reopened = self._open_child_directory(child)
                    reopened_info = self._directory_info(reopened)
                finally:
                    if reopened >= 0:
                        os.close(reopened)
                if (
                    (info.st_dev, info.st_ino) != (device, inode)
                    or (reopened_info.st_dev, reopened_info.st_ino) != (device, inode)
                ):
                    raise TransactionError("retained control directory changed")

    def _directory(self, name: str) -> int:
        self._ensure()
        return self._directories[name][0]

    def _open_artifact(self, directory: str, name: str, flags: int) -> int:
        name = self._token(name, "control artifact name")
        try:
            fd = os.open(
                name,
                self._artifact_flags(flags),
                0o600,
                dir_fd=self._directory(directory),
            )
        except FileExistsError:
            raise
        except OSError as exc:
            raise TransactionError("control artifact is unavailable") from exc
        try:
            self._artifact_info(fd)
            return fd
        except BaseException:
            os.close(fd)
            raise

    def journal_path(self, run_id: str) -> Path:
        self._token(run_id, "run ID")
        return self.root / "journals" / f"{run_id}.json"

    def receipt_path(self, run_id: str) -> Path:
        self._token(run_id, "run ID")
        return self.root / "receipts" / f"{run_id}.json"

    def _atomic_json(self, directory: str, name: str, value: dict[str, Any]) -> None:
        data = canonical_json_bytes(value)
        directory_fd = self._directory(directory)
        temporary = f".{name}.beads-convergence-{uuid.uuid4().hex}.tmp"
        fd = self._open_artifact(
            directory,
            temporary,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
        )
        try:
            os.write(fd, data)
            _durable_fsync(fd)
            os.close(fd)
            fd = -1
            os.replace(temporary, name, src_dir_fd=directory_fd, dst_dir_fd=directory_fd)
            _durable_fsync(directory_fd)
        finally:
            if fd >= 0:
                os.close(fd)
            try:
                os.unlink(temporary, dir_fd=directory_fd)
            except FileNotFoundError:
                pass

    def load_journal(self, run_id: str) -> dict[str, Any]:
        name = f"{self._token(run_id, 'run ID')}.json"
        try:
            fd = self._open_artifact("journals", name, os.O_RDONLY)
            try:
                raw = _read_control_fd(fd)
            finally:
                os.close(fd)
            value = json.loads(raw)
        except (OSError, json.JSONDecodeError, TransactionError) as exc:
            raise TransactionError("journal is unavailable or malformed") from exc
        if type(value) is not dict:
            raise TransactionError("journal is malformed")
        return value

    def save_journal(self, journal: dict[str, Any]) -> None:
        self._atomic_json("journals", f"{self._token(str(journal['run_id']), 'run ID')}.json", journal)

    def save_receipt(self, receipt: dict[str, Any]) -> None:
        self._atomic_json("receipts", f"{self._token(str(receipt['run_id']), 'run ID')}.json", receipt)

    def reserve_nonce(self, key: str, nonce: str) -> None:
        name = f"{self._token(key, 'canonical key')}-{self._token(nonce, 'approval nonce')}"
        try:
            fd = self._open_artifact("nonces", name, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
        except FileExistsError as exc:
            raise ApprovalError("approval nonce already used") from exc
        try:
            os.write(fd, b"reserved\n")
            _durable_fsync(fd)
        finally:
            os.close(fd)
        _durable_fsync(self._directory("nonces"))

    def unfinished_journal(self, key: str) -> str | None:
        """Find an unfinished run by canonical identity before consuming a nonce."""

        journals = self._directory("journals")
        for name in sorted(os.listdir(journals)):
            if not name.endswith(".json"):
                raise TransactionError("journal index is malformed")
            try:
                fd = self._open_artifact("journals", name, os.O_RDONLY)
                try:
                    journal = json.loads(_read_control_fd(fd))
                finally:
                    os.close(fd)
            except (OSError, json.JSONDecodeError, TransactionError):
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
        name = f"{self._token(key, 'canonical key')}.lock"
        fd = self._open_artifact("locks", name, os.O_RDWR | os.O_CREAT)
        try:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise TransactionError("canonical transaction lock is contended") from exc
            info = self._artifact_info(fd)
            retained = (name, fd, info.st_dev, info.st_ino)
            self._active_locks.append(retained)
            yield
        finally:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                if self._active_locks and self._active_locks[-1][1] == fd:
                    self._active_locks.pop()
                os.close(fd)

    def verify_before_redirect_mutation(self) -> None:
        """Reject namespace replacement before redirect apply or rollback writes."""

        self._ensure()
        if not self._active_locks:
            raise TransactionError("redirect mutation requires a retained control lock")
        lock_directory = self._directories["locks"][0]
        for name, fd, device, inode in self._active_locks:
            info = self._artifact_info(fd)
            if (info.st_dev, info.st_ino) != (device, inode):
                raise TransactionError("retained control lock changed")
            try:
                current = os.open(name, self._artifact_flags(os.O_RDONLY), dir_fd=lock_directory)
            except OSError as exc:
                raise TransactionError("retained control lock changed") from exc
            try:
                current_info = self._artifact_info(current)
                if (current_info.st_dev, current_info.st_ino) != (device, inode):
                    raise TransactionError("retained control lock changed")
            finally:
                os.close(current)


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


def _read_control_fd(fd: int, limit: int = 64 * 1024 * 1024) -> bytes:
    """Read one retained regular control artifact under a finite cap."""

    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = os.read(fd, 1024 * 1024)
        if not chunk:
            return b"".join(chunks)
        total += len(chunk)
        if total > limit:
            raise TransactionError("control artifact exceeds size limit")
        chunks.append(chunk)


def _canonical_key(path: Path) -> str:
    info = os.stat(path, follow_symlinks=False)
    if not stat.S_ISDIR(info.st_mode):
        raise TransactionError("canonical Beads authority is not a directory")
    return f"{info.st_dev}-{info.st_ino}"


def _sources(beads: DirectoryHandle, expected: list[dict[str, Any]]) -> list[dict[str, Any]]:
    measured: list[dict[str, Any]] = []
    for source in sorted(expected, key=lambda item: str(item["name"])):
        name = source["name"]
        if not isinstance(name, str) or "/" in name or name in ("", ".", ".."):
            raise TransactionError("source name is unsafe")
        try:
            fd = os.open(name, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0), dir_fd=beads.fd)
        except OSError as exc:
            raise TransactionError("source family changed") from exc
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise TransactionError("source family changed")
            measured.append({"name": name, "device": info.st_dev, "inode": info.st_ino,
                             "size": info.st_size, "sha256": hashlib.sha256(_read_control_fd(fd)).hexdigest()})
        finally:
            os.close(fd)
    return measured


def _assert_sources(beads: DirectoryHandle, expected: list[dict[str, Any]]) -> None:
    if _sources(beads, expected) != sorted(expected, key=lambda item: str(item["name"])):
        raise TransactionError("source family changed")


def _redirect_state(beads: DirectoryHandle) -> dict[str, Any]:
    try:
        fd = os.open("redirect", os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0), dir_fd=beads.fd)
    except FileNotFoundError:
        return {"present": False, "mode": None, "bytes": None}
    except OSError as exc:
        raise TransactionError("redirect is not a regular file") from exc
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise TransactionError("redirect is not a regular file")
        return {"present": True, "mode": stat.S_IMODE(info.st_mode), "bytes": _read_control_fd(fd).decode("utf-8")}
    finally:
        os.close(fd)


def _matches_pre(actual: dict[str, Any], pre: dict[str, Any]) -> bool:
    return all(actual.get(name) == pre.get(name) for name in ("present", "mode", "bytes"))


def _matches_intended(actual: dict[str, Any], intended: str) -> bool:
    return actual["present"] and actual["bytes"] == intended


def _verify_authority(adapter: object, worktree: DirectoryHandle, canonical: DirectoryHandle, executable: object, expected: tuple[int, int]) -> None:
    resolve = getattr(adapter, "resolve_authority", None)
    if not callable(resolve):
        raise TransactionError("adapter cannot verify redirect authority")
    if (worktree.device, worktree.inode) != expected:
        raise TransactionError("retained worktree identity changed")
    resolved = resolve(worktree, executable)
    if not isinstance(resolved, Path) or resolved != canonical.display_path:
        raise TransactionError("redirect does not resolve one hop to canonical authority")


def _write_redirect(beads: DirectoryHandle, pre: dict[str, Any], intended: str, fault_at: str | None, *, control: FileControlStore, adapter: object, worktree: DirectoryHandle, canonical: DirectoryHandle, executable: object, expected: tuple[int, int]) -> None:
    control.verify_before_redirect_mutation()
    info = os.fstat(beads.fd)
    if (info.st_dev, info.st_ino) != (pre["parent_device"], pre["parent_inode"]):
        raise TransactionError("redirect parent identity changed")
    actual = _redirect_state(beads)
    if _matches_intended(actual, intended):
        return
    if not _matches_pre(actual, pre):
        raise TransactionError("redirect bytes changed by a third party")
    mode = int(pre["mode"]) if pre["present"] else 0o600
    temp = f".redirect.beads-convergence-{uuid.uuid4().hex}.tmp"
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600, dir_fd=beads.fd)
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
    if fault_at == "before-rename":
        raise TransactionCrash()
    os.replace(temp, "redirect", src_dir_fd=beads.fd, dst_dir_fd=beads.fd)
    if fault_at == "after-rename":
        raise TransactionCrash()
    _durable_fsync(beads.fd)
    if fault_at == "after-target-fsync":
        raise TransactionCrash()
    if _redirect_state(beads)["bytes"] != intended:
        raise TransactionError("redirect verification failed")
    _verify_authority(adapter, worktree, canonical, executable, expected)


def _journal_action(action: dict[str, Any]) -> dict[str, Any]:
    redirect = dict(action["redirect"])
    return {"worktree_path": action["worktree_path"], "directory_device": action["directory_device"], "directory_inode": action["directory_inode"], "sources": list(action["sources"]),
            "pre": redirect, "intended": redirect["intended_bytes"], "state": "PENDING"}


def _assert_manifest_sources(manifest: Manifest, topology: RetainedTopology) -> None:
    """A coherent pair of fixture snapshots includes canonical and targets."""

    records = [record for record in manifest.worktrees if record.sources]
    for _ in range(2):
        for record in records:
            _worktree, beads = topology.targets[(record.directory_device, record.directory_inode)]
            _assert_sources(beads, [asdict(item) for item in record.sources])


def _reattest(adapter: object, manifest: Manifest) -> tuple[object, WriterLease, RetainedTopology]:
    """Run the typed adapter contract against retained directory descriptors."""

    try:
        executable = adapter.verify_binary(manifest.tracker_binary)
        canonical = open_trusted_tree(Path("/"), manifest.canonical_beads)
        topology = RetainedTopology(canonical, {})
        try:
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
                    target = topology.targets.get((record.directory_device, record.directory_inode))
                    if target is None:
                        worktree = open_trusted_tree(Path("/"), record.path)
                        beads = open_descendant(worktree, record.path / ".beads")
                        topology.targets[(record.directory_device, record.directory_inode)] = (worktree, beads)
                    else:
                        worktree, beads = target
                        health = adapter.verify_health(worktree, executable)
                        if not isinstance(health, HealthAttestation) or health.workspace_health != "healthy" or health.dirty_count or health.db_newer or health.jsonl_newer:
                            raise TransactionError("worktree health is not attested healthy")
                    health = adapter.verify_health(worktree, executable)
                    if not isinstance(health, HealthAttestation) or health.workspace_health != "healthy" or health.dirty_count or health.db_newer or health.jsonl_newer:
                        raise TransactionError("worktree health is not attested healthy")
                    source = adapter.fingerprint_sources(beads)
                    if not isinstance(source, SourceSnapshot) or not source.quiescent or not source.lease_proven:
                        raise TransactionError("source snapshot is not lease-proven")
                    expected = tuple(
                                (item.name, item.device, item.inode, item.size, item.sha256)
                                for item in record.sources
                            )
                    measured = tuple(
                                (item.name, item.device, item.inode, item.size, item.sha256)
                                for item in source.sources
                            )
                    if measured != expected:
                        raise TransactionError("source family changed from manifest")
                    current.append((record.path, measured))
                snapshots.append(tuple(current))
            if snapshots[0] != snapshots[1]:
                raise TransactionError("source family changed during coherent snapshot")
            return executable, lease, topology
        except BaseException:
            topology.close()
            raise
    except (AdapterError, FsafetyError, OSError, ValueError) as exc:
        raise TransactionError("typed adapter re-attestation failed") from exc


def _restore_redirect(beads: DirectoryHandle, pre: dict[str, Any], intended: str, *, control: FileControlStore, adapter: object, worktree: DirectoryHandle, canonical: DirectoryHandle) -> None:
    """Reverse only an exactly-recorded intended redirect; preserve other bytes."""

    del adapter, worktree, canonical
    control.verify_before_redirect_mutation()

    actual = _redirect_state(beads)
    if _matches_pre(actual, pre):
        return
    if not _matches_intended(actual, intended):
        raise TransactionError("redirect bytes changed by a third party")
    if not pre["present"]:
        os.unlink("redirect", dir_fd=beads.fd)
        _durable_fsync(beads.fd)
        return
    temp = f".redirect.beads-convergence-{uuid.uuid4().hex}.tmp"
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600, dir_fd=beads.fd)
    try:
        os.write(fd, str(pre["bytes"]).encode("utf-8"))
        os.fchmod(fd, int(pre["mode"]))
        _durable_fsync(fd)
    finally:
        os.close(fd)
    os.replace(temp, "redirect", src_dir_fd=beads.fd, dst_dir_fd=beads.fd)
    _durable_fsync(beads.fd)
    if not _matches_pre(_redirect_state(beads), pre):
        raise TransactionError("rollback redirect verification failed")


def _rollback(journal: dict[str, Any], control: FileControlStore, adapter: object, topology: RetainedTopology) -> bool:
    """Restore all recorded pre-states in reverse order, restarting safely."""

    try:
        for action in reversed(journal["actions"]):
            worktree, beads = topology.action_target(action)
            _restore_redirect(beads, action["pre"], str(action["intended"]), control=control, adapter=adapter, worktree=worktree, canonical=topology.canonical)
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


def _fresh_manifest(request: ApplyRequest) -> None:
    """Re-inventory a bounded registry before consuming an apply capability."""

    # Fixture adapters model the transaction boundary directly.  Production
    # adapters must rediscover through retained registry handles and Git.
    if isinstance(request.control, FixtureControlStore):
        return
    repositories = validate_registry(request.registry)
    selected = [item for item in repositories if item.config.repo_id == request.manifest.repo_id]
    try:
        if len(selected) != 1:
            raise TransactionError("registry does not uniquely bind repository")
        fresh = build_manifest(selected[0], request.adapter)
        if canonical_json_bytes(fresh) != canonical_json_bytes(request.manifest):
            raise TransactionError("fresh topology does not match signed manifest")
        if build_plan(fresh).sha256 != request.plan.sha256:
            raise TransactionError("fresh topology does not match signed plan")
    except (RegistryError, InventoryError, AdapterError, FsafetyError, OSError, ValueError) as exc:
        raise TransactionError("fresh topology re-discovery failed") from exc
    finally:
        for repository in repositories:
            repository.close()


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

    _fresh_manifest(request)
    key, fingerprint = _validate_request(request)
    assert request.approval is not None
    run_id = request.run_id or uuid.uuid4().hex
    with request.control.lock(key):
        if request.fault_at == "before-prepared":
            raise TransactionCrash()
        if request.control.unfinished_journal(key) is not None:
            raise TransactionError("unfinished journal already owns canonical authority")
        executable, lease, topology = _reattest(request.adapter, request.manifest)
        if lease is None:
            raise TransactionError("writer exclusion lease disappeared")
        request.control.reserve_nonce(key, request.approval.envelope.nonce)
        actions = [_journal_action(dict(action)) for action in request.plan.actions]
        for action in actions:
            _worktree, beads = topology.action_target(action)
            _assert_sources(beads, action["sources"])
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
                worktree, beads = topology.action_target(action)
                _assert_sources(beads, action["sources"])
                _write_redirect(beads, action["pre"], str(action["intended"]), request.fault_at, control=request.control, adapter=request.adapter, worktree=worktree, canonical=topology.canonical, executable=executable, expected=(action["directory_device"], action["directory_inode"]))
                action["state"] = "APPLIED"
                request.control.save_journal(journal)
                if request.fault_at == "after-progress":
                    raise TransactionCrash()
            if request.fault_at == "before-commit":
                raise TransactionCrash()
            journal["status"] = "COMMITTED"
            _assert_manifest_sources(request.manifest, topology)
            request.control.save_journal(journal)
            if request.fault_at == "after-commit":
                raise TransactionCrash()
            _save_receipt(request.control, journal)
            if request.fault_at == "after-receipt":
                raise TransactionCrash()
        except TransactionCrash:
            raise
        except (KeyError, OSError, TransactionError, TypeError, UnicodeError, ValueError):
            _rollback(journal, request.control, request.adapter, topology)
            raise
        finally:
            topology.close()
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
    _fresh_manifest(
        ApplyRequest(
            True,
            request.registry,
            request.manifest,
            request.plan,
            request.adapter,
            request.approval,
            request.verifier,
            request.control,
            request.now,
        )
    )
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
        if journal["status"] == "NEEDS_OPERATOR":
            return RecoveryReceipt(request.run_id, "NEEDS_OPERATOR", sha256_hex(canonical_json_bytes(journal)))
        try:
            _executable, lease, topology = _reattest(request.adapter, request.manifest)
        except TransactionError:
            journal["status"] = "NEEDS_OPERATOR"
            request.control.save_journal(journal)
            return RecoveryReceipt(request.run_id, "NEEDS_OPERATOR", sha256_hex(canonical_json_bytes(journal)))
        if lease is None:
            raise TransactionError("writer exclusion lease disappeared")
        request.control.reserve_nonce(key, request.approval.envelope.nonce)
        if journal["status"] == "COMMITTED":
            _save_receipt(request.control, journal)
            topology.close()
            return RecoveryReceipt(request.run_id, "COMMITTED", sha256_hex(canonical_json_bytes(journal)))
        if journal["status"] not in ("PREPARED", "APPLYING"):
            raise TransactionError("journal has unknown terminal state")
        try:
            for action in reversed(journal["actions"]):
                worktree, beads = topology.action_target(action)
                _assert_sources(beads, action["sources"])
                _restore_redirect(beads, action["pre"], str(action["intended"]), control=request.control, adapter=request.adapter, worktree=worktree, canonical=topology.canonical)
                action["state"] = "ROLLED_BACK"
                request.control.save_journal(journal)
            journal["status"] = "ROLLED_BACK"
            request.control.save_journal(journal)
            _save_receipt(request.control, journal)
        except (KeyError, OSError, TransactionError, TypeError, UnicodeError, ValueError):
            journal["status"] = "NEEDS_OPERATOR"
            request.control.save_journal(journal)
            return RecoveryReceipt(request.run_id, "NEEDS_OPERATOR", sha256_hex(canonical_json_bytes(journal)))
        finally:
            topology.close()
    return RecoveryReceipt(request.run_id, "ROLLED_BACK", sha256_hex(canonical_json_bytes(journal)))
