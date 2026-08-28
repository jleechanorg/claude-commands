"""Load and validate the host registry using retained filesystem descriptors."""

from __future__ import annotations

import hashlib
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Self

from .codec import ContractError, canonical_json_bytes, decode_registry, sha256_hex
from .fsafety import (
    DirectoryHandle,
    FsafetyError,
    open_descendant,
    open_trusted_tree,
)
from .models import Registry, RepositoryConfig


class RegistryError(ValueError):
    """Registry data cannot be safely used."""


KNOWN_ADAPTERS = frozenset({"br-sqlite-v1"})


@dataclass
class PhysicalIdentityClaims:
    """Track physical Beads stores claimed by registry repository identities."""

    _claims: dict[tuple[int, int], tuple[str, str]]
    _canonical_claims: set[tuple[int, int]]

    def __init__(self) -> None:
        self._claims = {}
        self._canonical_claims = set()

    def claim(
        self,
        repo_id: str,
        path: Path,
        identity: tuple[int, int],
        *,
        canonical: bool = False,
    ) -> None:
        owner = (repo_id, os.path.normpath(os.fspath(path)))
        previous = self._claims.get(identity)
        if previous is not None and previous != owner:
            if canonical and identity in self._canonical_claims:
                raise RegistryError("duplicate canonical authority")
            raise RegistryError("duplicate managed .beads identity")
        self._claims[identity] = owner
        if canonical:
            self._canonical_claims.add(identity)


@dataclass
class ValidatedRepository:
    """A repository config accompanied by retained authority-bearing handles."""

    config: RepositoryConfig
    seed: DirectoryHandle
    canonical: DirectoryHandle
    evidence: DirectoryHandle
    allowed_roots: tuple[DirectoryHandle, ...]
    registry_sha256: str | None = None
    identity_guard: PhysicalIdentityClaims | None = None

    @property
    def physical_identity(self) -> tuple[int, int]:
        return (self.canonical.device, self.canonical.inode)

    def close(self) -> None:
        self.seed.close()
        self.canonical.close()
        self.evidence.close()
        for root in self.allowed_roots:
            root.close()

    def __enter__(self) -> Self:
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
    identity_guard = PhysicalIdentityClaims()
    registry_sha256 = sha256_hex(canonical_json_bytes(registry))
    validated: list[ValidatedRepository] = []
    try:
        for config in registry.repositories:
            if config.repo_id in seen_ids:
                raise RegistryError("repositories contains duplicate repo_id")
            seen_ids.add(config.repo_id)
            if config.adapter not in KNOWN_ADAPTERS:
                raise RegistryError(f"unknown adapter ID: {config.adapter}")
            item = validate_repository(config, _identity_guard=identity_guard)
            if item.physical_identity in seen_authorities:
                item.close()
                raise RegistryError("duplicate canonical authority")
            seen_authorities.add(item.physical_identity)
            try:
                _claim_managed_beads(item, identity_guard)
            except BaseException:
                item.close()
                raise
            item.registry_sha256 = registry_sha256
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


def _managed_beads_identities(
    repository: ValidatedRepository,
) -> tuple[tuple[Path, tuple[int, int]], ...]:
    """Collect declared seed/extra stores through retained root descriptors."""

    config = repository.config
    paths = (config.repository_seed, *config.additional_worktrees)
    identities: list[tuple[Path, tuple[int, int]]] = []
    for path in paths:
        root = next(
            (
                candidate
                for candidate in repository.allowed_roots
                if _under(candidate.display_path, path)
            ),
            None,
        )
        if root is None:
            raise RegistryError("managed worktree is outside allowed roots")
        try:
            worktree = open_descendant(root, path)
        except FileNotFoundError:
            continue
        try:
            try:
                beads = open_descendant(worktree, path / ".beads")
            except FileNotFoundError:
                continue
            try:
                identities.append((path / ".beads", (beads.device, beads.inode)))
            finally:
                beads.close()
        finally:
            worktree.close()
    identities.append(
        (
            config.canonical_beads,
            (repository.canonical.device, repository.canonical.inode),
        )
    )
    return tuple(identities)


def _claim_managed_beads(
    repository: ValidatedRepository, identity_guard: PhysicalIdentityClaims
) -> None:
    for path, identity in _managed_beads_identities(repository):
        identity_guard.claim(
            repository.config.repo_id,
            path,
            identity,
            canonical=path == repository.config.canonical_beads,
        )


def validate_repository(
    config: RepositoryConfig,
    *,
    _identity_guard: PhysicalIdentityClaims | None = None,
) -> ValidatedRepository:
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
    roots: list[DirectoryHandle] = []
    seed: DirectoryHandle | None = None
    canonical: DirectoryHandle | None = None
    evidence: DirectoryHandle | None = None
    try:
        roots = [_open_any(root) for root in config.allowed_worktree_roots]
        if not roots:
            raise RegistryError("at least one allowed worktree root is required")
        seed_root = next(
            (
                root
                for root in roots
                if _under(root.display_path, config.repository_seed)
            ),
            None,
        )
        if seed_root is None:
            raise RegistryError("repository seed is outside allowed worktree roots")
        seed = open_descendant(seed_root, config.repository_seed)
        canonical_root = next(
            (
                root
                for root in roots
                if _under(root.display_path, config.canonical_beads)
            ),
            None,
        )
        if canonical_root is None:
            canonical_root = seed_root
        canonical = open_descendant(canonical_root, config.canonical_beads)
        evidence = _open_any(config.evidence_root)
    except (FsafetyError, OSError) as exc:
        for root in roots:
            root.close()
        raise RegistryError(str(exc)) from exc
    except RegistryError:
        for root in roots:
            root.close()
        raise
    try:
        if not _under(config.repository_seed, config.canonical_beads) and not any(
            _under(root.display_path, config.canonical_beads) for root in roots
        ):
            raise RegistryError("canonical directory is outside declared roots")
        if _under(config.repository_seed, config.evidence_root) or _under(
            config.canonical_beads, config.evidence_root
        ):
            raise RegistryError(
                "evidence root is inside a worktree or canonical directory"
            )
        # Physical equality catches spelling aliases without using string prefixes.
        for protected in (seed, canonical):
            if (
                evidence.device == protected.device
                and evidence.inode == protected.inode
            ):
                raise RegistryError("evidence root overlaps authority")
        for worktree in config.additional_worktrees:
            worktree_root = next(
                (root for root in roots if _under(root.display_path, worktree)),
                None,
            )
            if worktree_root is None:
                raise RegistryError("additional worktree is outside allowed roots")
            worktree_handle = open_descendant(worktree_root, worktree)
            try:
                if _under(worktree, config.evidence_root) or (
                    evidence.device == worktree_handle.device
                    and evidence.inode == worktree_handle.inode
                ):
                    raise RegistryError(
                        "evidence root is inside an additional worktree"
                    )
            finally:
                worktree_handle.close()
        identity_guard = _identity_guard or PhysicalIdentityClaims()
        validated = ValidatedRepository(
            config,
            seed,
            canonical,
            evidence,
            tuple(roots),
            identity_guard=identity_guard,
        )
        _claim_managed_beads(validated, identity_guard)
        return validated
    except BaseException:
        if seed is not None:
            seed.close()
        if canonical is not None:
            canonical.close()
        if evidence is not None:
            evidence.close()
        for root in roots:
            root.close()
        raise
