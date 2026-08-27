"""Load and validate the host registry using retained filesystem descriptors."""

from __future__ import annotations

import hashlib
import os
import stat
from dataclasses import dataclass
from pathlib import Path

from .codec import ContractError, decode_registry
from .fsafety import DirectoryHandle, FsafetyError, open_trusted_tree
from .models import Registry, RepositoryConfig


class RegistryError(ValueError):
    """Registry data cannot be safely used."""


KNOWN_ADAPTERS = frozenset({"br-sqlite-v1"})


@dataclass
class ValidatedRepository:
    """A repository config accompanied by retained authority-bearing handles."""

    config: RepositoryConfig
    seed: DirectoryHandle
    canonical: DirectoryHandle
    evidence: DirectoryHandle

    @property
    def physical_identity(self) -> tuple[int, int]:
        return (self.canonical.device, self.canonical.inode)

    def close(self) -> None:
        self.seed.close()
        self.canonical.close()
        self.evidence.close()

    def __enter__(self) -> "ValidatedRepository":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def _captured_bytes(path: Path) -> bytes:
    try:
        fd = os.open(
            os.fspath(path),
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0),
        )
    except OSError as exc:
        raise RegistryError(f"cannot open registry: {path}") from exc
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise RegistryError("registry must be a regular file")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(fd)
        if (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        ):
            raise RegistryError("registry changed while being read")
        return b"".join(chunks)
    finally:
        os.close(fd)


def load_registry(path: Path, expected_sha256: str) -> Registry:
    """Hash and decode one captured registry buffer."""

    if len(expected_sha256) != 64 or expected_sha256 != expected_sha256.lower():
        raise RegistryError("expected registry SHA-256 must be lowercase 64-hex")
    try:
        raw = _captured_bytes(Path(path))
        measured = hashlib.sha256(raw).hexdigest()
        if measured != expected_sha256:
            raise RegistryError("registry SHA-256 does not match expected digest")
        return decode_registry(raw)
    except ContractError as exc:
        raise RegistryError(str(exc)) from exc


def _under(parent: Path, child: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def _open_any(path: Path) -> DirectoryHandle:
    return open_trusted_tree(Path("/"), path)


def validate_registry(registry: Registry) -> tuple[ValidatedRepository, ...]:
    """Validate all entries and reject duplicate physical authorities."""

    if registry.schema != "beads.redirect-convergence.registry.v1":
        raise RegistryError("unsupported registry schema")
    seen_ids: set[str] = set()
    seen_authorities: set[tuple[int, int]] = set()
    validated: list[ValidatedRepository] = []
    try:
        for config in registry.repositories:
            if config.repo_id in seen_ids:
                raise RegistryError("repositories contains duplicate repo_id")
            seen_ids.add(config.repo_id)
            if config.adapter not in KNOWN_ADAPTERS:
                raise RegistryError(f"unknown adapter ID: {config.adapter}")
            item = validate_repository(config)
            if item.physical_identity in seen_authorities:
                raise RegistryError("duplicate canonical authority")
            seen_authorities.add(item.physical_identity)
            validated.append(item)
        return tuple(validated)
    except (FsafetyError, OSError) as exc:
        for item in validated:
            item.close()
        raise RegistryError(str(exc)) from exc
    except BaseException:
        for item in validated:
            item.close()
        raise


def validate_repository(config: RepositoryConfig) -> ValidatedRepository:
    """Retain and validate seed, canonical Beads, and external evidence dirs."""

    if config.adapter not in KNOWN_ADAPTERS:
        raise RegistryError(f"unknown adapter ID: {config.adapter}")
    for label, value in (
        ("repository_seed", config.repository_seed),
        ("canonical_beads", config.canonical_beads),
        ("evidence_root", config.evidence_root),
        ("tracker binary", config.tracker_binary.path),
        ("Git binary", config.git_binary.path),
        *(("allowed worktree root", root) for root in config.allowed_worktree_roots),
        *(("additional worktree", root) for root in config.additional_worktrees),
    ):
        value = Path(value)
        if not value.is_absolute() or any(part in (".", "..") for part in value.parts):
            raise RegistryError(f"{label} must be an absolute, traversal-free path")
    try:
        seed = _open_any(config.repository_seed)
        canonical = _open_any(config.canonical_beads)
        evidence = _open_any(config.evidence_root)
    except (FsafetyError, OSError) as exc:
        raise RegistryError(str(exc)) from exc
    try:
        if not _under(config.repository_seed, config.canonical_beads) and not any(
            _under(root, config.canonical_beads) for root in config.allowed_worktree_roots
        ):
            raise RegistryError("canonical directory is outside declared roots")
        if _under(config.repository_seed, config.evidence_root) or _under(
            config.canonical_beads, config.evidence_root
        ):
            raise RegistryError("evidence root is inside a worktree or canonical directory")
        # Physical equality catches spelling aliases without using string prefixes.
        for protected in (seed, canonical):
            if evidence.device == protected.device and evidence.inode == protected.inode:
                raise RegistryError("evidence root overlaps authority")
        for root in config.allowed_worktree_roots:
            if not _under(root, config.repository_seed):
                raise RegistryError("repository seed is outside allowed worktree roots")
        for worktree in config.additional_worktrees:
            if not any(_under(root, worktree) for root in config.allowed_worktree_roots):
                raise RegistryError("additional worktree is outside allowed roots")
            worktree_handle = _open_any(worktree)
            try:
                if _under(worktree, config.evidence_root) or (
                    evidence.device == worktree_handle.device
                    and evidence.inode == worktree_handle.inode
                ):
                    raise RegistryError("evidence root is inside an additional worktree")
            finally:
                worktree_handle.close()
        return ValidatedRepository(config, seed, canonical, evidence)
    except BaseException:
        seed.close()
        canonical.close()
        evidence.close()
        raise
