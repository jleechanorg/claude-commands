"""Bounded, read-only topology discovery for Beads convergence."""

from __future__ import annotations

import hashlib
import os
import stat
from pathlib import Path
from typing import Any

from .adapters import AdapterError, TrackerAdapter
from .codec import canonical_json_bytes
from .fsafety import (
    DirectoryHandle,
    FsafetyError,
    UnsupportedCapability,
    open_descendant,
    open_verified_executable,
    run_verified,
)
from .models import (
    Manifest,
    RedirectState,
    SourceFingerprint,
    WorktreeRecord,
)


class InventoryError(RuntimeError):
    """The bounded topology cannot be safely represented."""


_GIT_WORKTREE_COMMAND = ("worktree", "list", "--porcelain")
_REDIRECT_NAME = "redirect"
_GIT_RECORD_FIELDS = ("HEAD ", "branch ", "detached", "locked", "prunable ")


def _path_is_under(root: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return False


def _root_for(repository: Any, path: Path) -> DirectoryHandle | None:
    for root in repository.allowed_roots:
        if _path_is_under(root.display_path, path):
            return root
    return None


def _parse_git_porcelain(raw: bytes) -> tuple[Path, ...]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InventoryError("malformed Git porcelain output") from exc
    paths: list[Path] = []
    current: Path | None = None
    for line in text.splitlines(keepends=True):
        if line.endswith("\r\n") or line.endswith("\r") or "\x00" in line:
            raise InventoryError("malformed Git porcelain output")
        value = line[:-1] if line.endswith("\n") else line
        if not value:
            current = None
            continue
        if value.startswith("worktree "):
            if current is not None:
                raise InventoryError("malformed Git porcelain output")
            path = Path(value[9:])
            if not path.is_absolute() or any(
                part in (".", "..") for part in path.parts
            ):
                raise InventoryError("malformed Git porcelain worktree path")
            current = path
            paths.append(path)
        elif current is None:
            raise InventoryError("malformed Git porcelain output")
        elif not value.startswith(_GIT_RECORD_FIELDS):
            raise InventoryError("malformed Git porcelain output")
    if current is not None and not text.endswith("\n"):
        # A final record without a separator is valid porcelain, but only when
        # it contains a worktree header and no partial line.
        return tuple(paths)
    if not paths:
        raise InventoryError("malformed Git porcelain output")
    return tuple(paths)


def _git_worktrees(repository: Any) -> tuple[Path, ...]:
    executable = None
    try:
        executable = open_verified_executable(repository.config.git_binary)
        result = run_verified(executable, _GIT_WORKTREE_COMMAND, repository.seed)
    except (FsafetyError, UnsupportedCapability, OSError, TimeoutError) as exc:
        raise InventoryError(f"Git worktree discovery failed: {exc}") from exc
    finally:
        if executable is not None:
            executable.close()
    if result.returncode != 0:
        raise InventoryError("Git worktree discovery failed")
    return _parse_git_porcelain(result.stdout)


def discover_worktrees(repository: Any) -> tuple[Path, ...]:
    """Return only Git-listed worktrees plus explicitly registered extras."""

    configured = tuple(Path(item) for item in repository.config.additional_worktrees)
    discovered = _git_worktrees(repository)
    merged: set[Path] = set()
    for path in (*discovered, *configured):
        if not path.is_absolute() or any(part in (".", "..") for part in path.parts):
            raise InventoryError("worktree path must be absolute and traversal-free")
        if _root_for(repository, path) is None:
            raise InventoryError(f"worktree is outside allowed roots: {path}")
        merged.add(path)
    return tuple(sorted(merged, key=os.fspath))


def _read_redirect(beads: DirectoryHandle) -> RedirectState:
    try:
        fd = os.open(
            _REDIRECT_NAME,
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=beads.fd,
        )
    except FileNotFoundError:
        return RedirectState(False, None, None, beads.device, beads.inode, None, None)
    except OSError as exc:
        raise InventoryError("redirect cannot be opened safely") from exc
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            raise InventoryError("redirect is not a regular file")
        chunks: list[bytes] = []
        while chunk := os.read(fd, 1024 * 1024):
            chunks.append(chunk)
        after = os.fstat(fd)
        if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        ):
            raise InventoryError("redirect changed while being read")
        raw = b"".join(chunks)
        try:
            value = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise InventoryError("redirect is not UTF-8") from exc
        _validate_redirect_text(value)
        return RedirectState(
            True,
            stat.S_IMODE(before.st_mode),
            value,
            beads.device,
            beads.inode,
            None,
            None,
        )
    finally:
        os.close(fd)


def _source_fingerprints(
    adapter: TrackerAdapter, beads: DirectoryHandle
) -> tuple[SourceFingerprint, ...]:
    snapshot = adapter.fingerprint_sources(beads)
    seen: set[str] = set()
    converted: list[SourceFingerprint] = []
    for member in snapshot.sources:
        if member.name in seen or member.name not in adapter.source_names:
            raise InventoryError("adapter returned an unexpected source member")
        if (
            type(member.device) is not int
            or type(member.inode) is not int
            or type(member.size) is not int
            or member.device < 0
            or member.inode < 0
            or member.size < 0
            or not isinstance(member.sha256, str)
            or len(member.sha256) != 64
            or any(char not in "0123456789abcdef" for char in member.sha256)
        ):
            raise InventoryError("adapter returned an invalid source fingerprint")
        seen.add(member.name)
        converted.append(
            SourceFingerprint(
                member.name,
                member.device,
                member.inode,
                member.size,
                member.sha256,
            )
        )
    return tuple(sorted(converted, key=lambda item: item.name))


def _codec_metadata(adapter: Any, canonical: Path) -> tuple[str | None, str | None]:
    """Read codec data supplied by the adapter's verified oracle only."""

    oracle = getattr(adapter, "redirect_oracle", None)
    if callable(oracle):
        result = oracle(canonical)
        if not isinstance(result, tuple) or len(result) != 2:
            raise InventoryError("redirect codec oracle returned malformed data")
        codec, intended = result
    else:
        codec = getattr(adapter, "redirect_codec_id", None)
        intended = getattr(adapter, "intended_redirect_bytes", None)
        if callable(intended):
            intended = intended(canonical)
    if codec is not None and not isinstance(codec, str):
        raise InventoryError("redirect codec ID is malformed")
    if intended is not None:
        if isinstance(intended, bytes):
            try:
                intended = intended.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise InventoryError("oracle redirect bytes are not UTF-8") from exc
        if not isinstance(intended, str):
            raise InventoryError("oracle redirect bytes are malformed")
        _validate_redirect_text(intended)
    return codec, intended


def _validate_redirect_text(value: str) -> None:
    if (
        not value
        or "\x00" in value
        or "\r" in value
        or value.count("\n") > 1
        or "\n" in value.rstrip("\n")
        or any(
            line.endswith(" ") or line.endswith("\t")
            for line in value.splitlines()
        )
    ):
        raise InventoryError("redirect has forbidden whitespace or control bytes")


def _same_directory(path: Path, expected: DirectoryHandle) -> bool:
    try:
        handle = open_verified_tree(path)
    except (OSError, FsafetyError):
        return False
    try:
        return (handle.device, handle.inode) == (expected.device, expected.inode)
    finally:
        handle.close()


def open_verified_tree(path: Path) -> DirectoryHandle:
    """Open a path through descriptors; this is intentionally not ``resolve``."""

    from .fsafety import open_trusted_tree

    return open_trusted_tree(Path("/"), path)


def _classify(
    repository: Any,
    adapter: TrackerAdapter,
    worktree: DirectoryHandle,
    beads: DirectoryHandle,
    executable: object,
    redirect: RedirectState,
) -> tuple[str, RedirectState | None]:
    canonical = repository.canonical
    if (beads.device, beads.inode) == (canonical.device, canonical.inode):
        if redirect.present:
            raise InventoryError("canonical store has an unexpected redirect")
        return "canonical", None
    codec, intended = _codec_metadata(adapter, repository.config.canonical_beads)
    if not redirect.present:
        return "noncanonical", RedirectState(
            False,
            None,
            None,
            beads.device,
            beads.inode,
            codec,
            intended,
        )
    if codec is None or intended is None:
        return "unsupported", redirect
    try:
        authority = adapter.resolve_authority(worktree, executable)
    except (AdapterError, FsafetyError, UnsupportedCapability, OSError, TimeoutError):
        return "unresolved_noncanonical", RedirectState(
            redirect.present,
            redirect.mode,
            redirect.bytes,
            redirect.parent_device,
            redirect.parent_inode,
            codec,
            intended,
        )
    if not isinstance(authority, Path) or not authority.is_absolute():
        return "unresolved_noncanonical", redirect
    if not _same_directory(authority, canonical):
        return "noncanonical", RedirectState(
            redirect.present,
            redirect.mode,
            redirect.bytes,
            redirect.parent_device,
            redirect.parent_inode,
            codec,
            intended,
        )
    target_redirect = authority / _REDIRECT_NAME
    if target_redirect.exists() or target_redirect.is_symlink():
        raise InventoryError("redirect resolves through multiple hops")
    return "redirected_canonical", RedirectState(
        redirect.present,
        redirect.mode,
        redirect.bytes,
        redirect.parent_device,
        redirect.parent_inode,
        codec,
        intended,
    )


def _missing_record(path: Path) -> WorktreeRecord:
    return WorktreeRecord(path, "missing", 0, 0, (), None)


def build_manifest(repository: Any, adapter: TrackerAdapter) -> Manifest:
    """Build a deterministic, read-only manifest from bounded worktree paths."""

    if adapter.adapter_id != repository.config.adapter:
        raise InventoryError("adapter does not match repository registry")
    try:
        executable = adapter.verify_binary(repository.config.tracker_binary)
    except Exception as exc:
        raise InventoryError(f"tracker binary verification failed: {exc}") from exc
    records: list[WorktreeRecord] = []
    seen_beads: set[tuple[int, int]] = set()
    try:
        for path in discover_worktrees(repository):
            root = _root_for(repository, path)
            if root is None:
                raise InventoryError(f"worktree is outside allowed roots: {path}")
            try:
                worktree = open_descendant(root, path)
            except (FileNotFoundError, NotADirectoryError):
                records.append(_missing_record(path))
                continue
            except (OSError, FsafetyError) as exc:
                raise InventoryError(
                    f"worktree cannot be opened safely: {path}"
                ) from exc
            try:
                try:
                    beads = open_descendant(worktree, path / ".beads")
                except (FileNotFoundError, NotADirectoryError):
                    records.append(_missing_record(path))
                    continue
                except (OSError, FsafetyError) as exc:
                    raise InventoryError(
                        f"Beads directory cannot be opened safely: {path}"
                    ) from exc
                try:
                    identity = (beads.device, beads.inode)
                    if identity in seen_beads:
                        raise InventoryError("duplicate physical .beads identity")
                    seen_beads.add(identity)
                    try:
                        adapter.attest_backend(beads)
                        sources = _source_fingerprints(adapter, beads)
                        redirect = _read_redirect(beads)
                        classification, redirect = _classify(
                            repository, adapter, worktree, beads, executable, redirect
                        )
                    except (AdapterError, FsafetyError, OSError) as exc:
                        classification, sources, redirect = "unsupported", (), None
                        del exc
                    records.append(
                        WorktreeRecord(
                            path,
                            classification,
                            worktree.device,
                            worktree.inode,
                            sources,
                            redirect,
                        )
                    )
                finally:
                    beads.close()
            finally:
                worktree.close()
    finally:
        close = getattr(executable, "close", None)
        if callable(close):
            close()
    config = repository.config
    registry_sha = getattr(repository, "registry_sha256", None)
    if not isinstance(registry_sha, str):
        registry_sha = hashlib.sha256(canonical_json_bytes(config)).hexdigest()
    return Manifest(
        "beads.redirect-convergence.manifest.v1",
        registry_sha,
        config.repo_id,
        config.adapter,
        config.canonical_beads,
        config.tracker_binary,
        config.git_binary,
        tuple(sorted(records, key=lambda item: os.fspath(item.path))),
    )
