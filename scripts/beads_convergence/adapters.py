"""Tracker adapter boundary and the read-only ``br-sqlite-v1`` adapter."""

from __future__ import annotations

import hashlib
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .fsafety import (
    DirectoryHandle,
    FsafetyError,
    GitProbe,
    UnsupportedCapability,
    VerifiedExecutable,
    open_verified_executable,
    run_verified_git_probe,
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


@dataclass(frozen=True)
class _SourceMeasurement:
    source: SourceMember
    mtime_ns: int


@dataclass(frozen=True)
class RedirectOracle:
    codec_id: str
    intended_bytes: bytes
    receipt_sha256: str


class TrackerAdapter(Protocol):
    adapter_id: str
    source_names: tuple[str, ...]

    def verify_binary(self, binding: object) -> VerifiedExecutable: ...

    def verify_git_binary(self, binding: object) -> VerifiedExecutable: ...

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

    def redirect_oracle(
        self,
        canonical: Path,
        worktree: DirectoryHandle,
        executable: VerifiedExecutable,
    ) -> RedirectOracle: ...


class BrSqliteV1Adapter:
    adapter_id = "br-sqlite-v1"
    source_names = ("beads.db", "beads.db-wal", "beads.db-shm", "issues.jsonl")
    supported_version = "0.4.0"

    def verify_binary(self, binding: object) -> VerifiedExecutable:
        if binding.version != self.supported_version:
            raise AdapterError("unsupported tracker version")
        try:
            return open_verified_executable(binding)
        except (FsafetyError, OSError) as exc:
            raise AdapterError(str(exc)) from exc

    def verify_git_binary(self, binding: object) -> VerifiedExecutable:
        """Verify and probe a pinned Git executable through its descriptor."""

        executable: VerifiedExecutable | None = None
        try:
            executable = open_verified_executable(binding)
            from .fsafety import open_trusted_tree

            with open_trusted_tree(Path("/"), Path("/")) as root:
                result = run_verified_git_probe(executable, GitProbe.VERSION, root)
            if result.returncode != 0:
                raise AdapterError("Git version probe failed")
            line = result.stdout.decode("utf-8").strip()
            expected = f"git version {binding.version}"
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

    def redirect_oracle(
        self,
        canonical: Path,
        worktree: DirectoryHandle,
        executable: VerifiedExecutable,
    ) -> RedirectOracle:
        del canonical, worktree, executable
        raise AdapterError(
            "snapshot-backed redirect codec oracle is unavailable"
        )

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
        del worktree, executable
        raise AdapterError("snapshot-backed tracker health is unavailable")

    def acquire_writer_exclusion(
        self, beads_dir: DirectoryHandle, executable: VerifiedExecutable
    ) -> WriterLease:
        del beads_dir, executable
        return WriterLease(
            False,
            "br 0.4.0 does not prove a universal read-only writer lease",
            "0.4.0",
        )

    def _measure_source_family(
        self, beads_dir: DirectoryHandle
    ) -> tuple[_SourceMeasurement, ...]:
        beads_dir.verify_identity()
        initial_names = set(os.listdir(beads_dir.fd))
        present = tuple(name for name in self.source_names if name in initial_names)
        measurements: list[_SourceMeasurement] = []
        for name in present:
            try:
                fd = os.open(
                    name,
                    os.O_RDONLY
                    | getattr(os, "O_CLOEXEC", 0)
                    | getattr(os, "O_NOFOLLOW", 0),
                    dir_fd=beads_dir.fd,
                )
            except FileNotFoundError as exc:
                raise AdapterError("source family changed during fingerprint") from exc
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
                measurements.append(
                    _SourceMeasurement(
                        SourceMember(
                            name,
                            before.st_dev,
                            before.st_ino,
                            size,
                            digest.hexdigest(),
                        ),
                        before.st_mtime_ns,
                    )
                )
            finally:
                os.close(fd)
        beads_dir.verify_identity()
        final_names = set(os.listdir(beads_dir.fd))
        if present != tuple(name for name in self.source_names if name in final_names):
            raise AdapterError("source family changed during fingerprint")
        return tuple(measurements)

    def fingerprint_sources(self, beads_dir: DirectoryHandle) -> SourceSnapshot:
        first = self._measure_source_family(beads_dir)
        second = self._measure_source_family(beads_dir)
        if first != second:
            raise AdapterError("source family changed during fingerprint")
        return SourceSnapshot(tuple(item.source for item in second))

    def resolve_authority(
        self, worktree: DirectoryHandle, executable: VerifiedExecutable
    ) -> Path:
        del worktree, executable
        raise AdapterError("snapshot-backed tracker authority is unavailable")
