"""Tracker adapter boundary and the read-only ``br-sqlite-v1`` adapter."""

from __future__ import annotations

import hashlib
import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .fsafety import (
    DirectoryHandle,
    FsafetyError,
    UnsupportedCapability,
    VerifiedExecutable,
    open_verified_executable,
    run_verified,
)


class AdapterError(RuntimeError):
    """A tracker backend, health result, or pinned executable is unsafe."""


@dataclass(frozen=True)
class BackendAttestation:
    backend: str
    source_names: tuple[str, ...]


@dataclass(frozen=True)
class HealthAttestation:
    dirty_count: int
    db_newer: bool
    jsonl_newer: bool
    workspace_health: str
    raw: dict[str, object]


@dataclass(frozen=True)
class WriterLease:
    available: bool
    reason: str
    version: str

    @property
    def plan_only(self) -> bool:
        return not self.available


@dataclass(frozen=True)
class SourceMember:
    name: str
    device: int
    inode: int
    size: int
    sha256: str


@dataclass(frozen=True)
class SourceSnapshot:
    sources: tuple[SourceMember, ...]
    quiescent: bool = False
    plan_only: bool = True
    lease_proven: bool = False
    reason: str = "writer exclusion is unavailable"


class _DuplicateField(ValueError):
    pass


def _pairs_without_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateField(key)
        result[key] = value
    return result


def _strict_object(
    raw: bytes, allowed: set[str], label: str
) -> dict[str, object]:
    try:
        value = json.loads(
            raw, object_pairs_hook=_pairs_without_duplicates
        )
    except (json.JSONDecodeError, UnicodeDecodeError, _DuplicateField) as exc:
        raise ValueError(f"{label} output is not strict JSON") from exc
    if type(value) is not dict:
        raise ValueError(f"{label} output must be an object")
    unknown = set(value) - allowed
    if unknown:
        raise ValueError(f"{label} output has unknown field")
    return value


class TrackerAdapter(Protocol):
    adapter_id: str
    source_names: tuple[str, ...]

    def verify_binary(self, binding: object) -> VerifiedExecutable: ...

    def attest_backend(self, beads_dir: DirectoryHandle) -> BackendAttestation: ...

    def verify_health(
        self, worktree: DirectoryHandle, executable: VerifiedExecutable
    ) -> HealthAttestation: ...

    def acquire_writer_exclusion(
        self, beads_dir: DirectoryHandle, executable: VerifiedExecutable
    ) -> WriterLease: ...

    def fingerprint_sources(self, beads_dir: DirectoryHandle) -> SourceSnapshot: ...

    def resolve_authority(
        self, worktree: DirectoryHandle, executable: VerifiedExecutable
    ) -> Path: ...


class BrSqliteV1Adapter:
    adapter_id = "br-sqlite-v1"
    source_names = ("beads.db", "beads.db-wal", "beads.db-shm", "issues.jsonl")

    def verify_binary(self, binding: object) -> VerifiedExecutable:
        try:
            executable = open_verified_executable(binding)
        except (FsafetyError, OSError) as exc:
            raise AdapterError(str(exc)) from exc
        # The binding is already the version pin. Probe it through its retained
        # descriptor so a version mismatch cannot be hidden by PATH.
        try:
            from .fsafety import open_trusted_tree

            with open_trusted_tree(Path("/"), Path("/")) as root:
                result = run_verified(executable, ("version", "--json"), root)
            if result.returncode != 0:
                raise AdapterError("tracker version probe failed")
            payload = _strict_object(
                result.stdout,
                {
                    "version",
                    "build",
                    "commit",
                    "branch",
                    "rust_version",
                    "target",
                    "features",
                },
                "version",
            )
            if payload["version"] != getattr(binding, "version"):
                raise AdapterError("tracker version does not match binding")
        except UnsupportedCapability as exc:
            executable.close()
            raise AdapterError(
                "descriptor execution is unsupported; tracker is unverified"
            ) from exc
        except AdapterError:
            executable.close()
            raise
        except (ValueError, TypeError, json.JSONDecodeError, KeyError) as exc:
            executable.close()
            raise AdapterError("tracker version output is malformed") from exc
        except (FsafetyError, OSError) as exc:
            executable.close()
            raise AdapterError(str(exc)) from exc
        return executable

    def verify_git_binary(self, binding: object) -> VerifiedExecutable:
        """Verify and probe a pinned Git executable through its descriptor."""

        executable: VerifiedExecutable | None = None
        try:
            executable = open_verified_executable(binding)
            from .fsafety import open_trusted_tree

            with open_trusted_tree(Path("/"), Path("/")) as root:
                result = run_verified(executable, ("--version",), root)
            if result.returncode != 0:
                raise AdapterError("Git version probe failed")
            line = result.stdout.decode("utf-8").strip()
            expected = f"git version {getattr(binding, 'version')}"
            if line != expected:
                raise AdapterError("Git version does not match binding")
            return executable
        except UnsupportedCapability as exc:
            if executable is not None:
                executable.close()
            raise AdapterError(
                "descriptor execution is unsupported; Git is unverified"
            ) from exc
        except (AdapterError, FsafetyError, OSError, UnicodeError) as exc:
            if executable is not None:
                executable.close()
            if isinstance(exc, AdapterError):
                raise
            raise AdapterError(str(exc)) from exc

    def attest_backend(self, beads_dir: DirectoryHandle) -> BackendAttestation:
        beads_dir.verify_identity()
        names = set(os.listdir(beads_dir.fd))
        if "beads.db-journal" in names:
            raise AdapterError("hot beads.db-journal is not safe")
        if "dolt" in names or "embeddeddolt" in names or any(
            name.startswith("beads.db-") and name not in self.source_names
            for name in names
        ):
            raise AdapterError("unsupported or mixed tracker backend")
        if "beads.db" not in names or "issues.jsonl" not in names:
            raise AdapterError("SQLite source family is incomplete")
        for name in self.source_names:
            if name not in names:
                continue
            fd = os.open(
                name,
                os.O_RDONLY
                | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=beads_dir.fd,
            )
            try:
                info = os.fstat(fd)
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                    raise AdapterError(f"unsafe source member: {name}")
                if name == "beads.db":
                    header = os.read(fd, 16)
                    if header != b"SQLite format 3\x00":
                        raise AdapterError("beads.db is not SQLite")
            finally:
                os.close(fd)
        # Explicit metadata markers used by known legacy stores.
        for name in ("metadata.json", "backend.json"):
            if name in names:
                fd = os.open(
                    name,
                    os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
                    dir_fd=beads_dir.fd,
                )
                try:
                    if b"dolt" in os.read(fd, 256).lower():
                        raise AdapterError("metadata declares Dolt backend")
                finally:
                    os.close(fd)
        return BackendAttestation(
            "sqlite", tuple(name for name in self.source_names if name in names)
        )

    def verify_health(
        self, worktree: DirectoryHandle, executable: VerifiedExecutable
    ) -> HealthAttestation:
        try:
            result = run_verified(
                executable,
                (
                    "sync",
                    "--status",
                    "--json",
                    "--no-auto-flush",
                    "--no-auto-import",
                    "--no-daemon",
                ),
                worktree,
                timeout=30,
            )
        except (FsafetyError, TimeoutError, UnsupportedCapability) as exc:
            raise AdapterError(str(exc)) from exc
        if result.returncode != 0:
            raise AdapterError("tracker health probe failed")
        try:
            payload = _strict_object(
                result.stdout,
                {
                    "dirty_count",
                    "last_export_time",
                    "last_import_time",
                    "jsonl_content_hash",
                    "jsonl_exists",
                    "jsonl_newer",
                    "db_newer",
                    "workspace_health",
                    "reliability_audit",
                    "coverage",
                    "coverage_drift",
                    "git_export",
                },
                "health",
            )
            dirty = payload["dirty_count"]
            db_newer = payload["db_newer"]
            jsonl_newer = payload["jsonl_newer"]
            health = payload["workspace_health"]
            if (
                type(dirty) is not int
                or dirty < 0
                or type(db_newer) is not bool
                or type(jsonl_newer) is not bool
                or health != "healthy"
            ):
                raise ValueError
        except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            raise AdapterError("malformed or unhealthy tracker status") from exc
        if dirty != 0 or db_newer or jsonl_newer:
            raise AdapterError("tracker workspace is not healthy")
        return HealthAttestation(dirty, db_newer, jsonl_newer, health, payload)

    def acquire_writer_exclusion(
        self, beads_dir: DirectoryHandle, executable: VerifiedExecutable
    ) -> WriterLease:
        del beads_dir, executable
        return WriterLease(
            False,
            "br 0.4.0 does not prove a universal read-only writer lease",
            "0.4.0",
        )

    def fingerprint_sources(self, beads_dir: DirectoryHandle) -> SourceSnapshot:
        beads_dir.verify_identity()
        initial_names = set(os.listdir(beads_dir.fd))
        members: list[SourceMember] = []
        for name in self.source_names:
            try:
                fd = os.open(
                    name,
                    os.O_RDONLY
                    | getattr(os, "O_CLOEXEC", 0)
                    | getattr(os, "O_NOFOLLOW", 0),
                    dir_fd=beads_dir.fd,
                )
            except FileNotFoundError:
                continue
            try:
                before = os.fstat(fd)
                if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
                    raise AdapterError(f"unsafe source member: {name}")
                digest = hashlib.sha256()
                size = 0
                while chunk := os.read(fd, 1024 * 1024):
                    digest.update(chunk)
                    size += len(chunk)
                after = os.fstat(fd)
                path_info = os.stat(
                    name, dir_fd=beads_dir.fd, follow_symlinks=False
                )
                if (
                    before.st_dev,
                    before.st_ino,
                    before.st_size,
                    before.st_mtime_ns,
                ) != (
                    after.st_dev,
                    after.st_ino,
                    after.st_size,
                    after.st_mtime_ns,
                ) or size != before.st_size or (
                    path_info.st_dev,
                    path_info.st_ino,
                ) != (before.st_dev, before.st_ino):
                    raise AdapterError(f"source changed during fingerprint: {name}")
                members.append(
                    SourceMember(
                        name, before.st_dev, before.st_ino, size, digest.hexdigest()
                    )
                )
            finally:
                os.close(fd)
        beads_dir.verify_identity()
        final_names = set(os.listdir(beads_dir.fd))
        if any(
            (name in initial_names) != (name in final_names)
            for name in self.source_names
        ):
            raise AdapterError("source family changed during fingerprint")
        return SourceSnapshot(tuple(members))

    def resolve_authority(
        self, worktree: DirectoryHandle, executable: VerifiedExecutable
    ) -> Path:
        try:
            result = run_verified(
                executable,
                ("where", "--json", "--no-auto-flush", "--no-auto-import"),
                worktree,
                timeout=30,
            )
        except (FsafetyError, TimeoutError, UnsupportedCapability) as exc:
            raise AdapterError(str(exc)) from exc
        if result.returncode != 0:
            raise AdapterError("tracker authority probe failed")
        try:
            payload = json.loads(result.stdout)
            path = payload["path"]
            if type(path) is not str or not Path(path).is_absolute() or "\x00" in path:
                raise ValueError
            return Path(path)
        except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            raise AdapterError("malformed tracker authority output") from exc
