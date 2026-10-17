"""Bounded, read-only topology discovery for Beads convergence."""

from __future__ import annotations

import os
import stat
from pathlib import Path
from typing import Any

from .adapters import AdapterError, BrSqliteV1Adapter, RedirectOracle, TrackerAdapter
from .codec import canonical_json_bytes, sha256_hex
from .fsafety import (
    DirectoryHandle,
    FsafetyError,
    GitProbe,
    UnsupportedCapability,
    open_descendant,
    run_verified_git_probe,
)
from .models import (
    HealthFingerprint,
    Manifest,
    RedirectState,
    SourceFingerprint,
    WorktreeRecord,
)


class InventoryError(RuntimeError):
    """The bounded topology cannot be safely represented."""


_REDIRECT_NAME = "redirect"
_MAX_REDIRECT_BYTES = 4096
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
        if line.endswith(("\r\n", "\r")) or "\x00" in line:
            raise InventoryError("malformed Git porcelain output")
        value = line.removesuffix("\n")
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
        elif current is None or not value.startswith(_GIT_RECORD_FIELDS):
            raise InventoryError("malformed Git porcelain output")
    if current is not None and not text.endswith("\n"):
        # A final record without a separator is valid porcelain, but only when
        # it contains a worktree header and no partial line.
        return tuple(paths)
    if not paths:
        raise InventoryError("malformed Git porcelain output")
    return tuple(paths)


def _common_dir_identity(
    repository: Any, executable: object, path: Path, worktree: DirectoryHandle
) -> tuple[int, int]:
    result = run_verified_git_probe(executable, GitProbe.COMMON_DIR, worktree)
    if result.returncode != 0:
        raise InventoryError("Git common-dir query failed")
    try:
        raw = result.stdout.decode("utf-8").strip()
    except UnicodeDecodeError as exc:
        raise InventoryError("Git common-dir output is malformed") from exc
    if not raw or "\x00" in raw or "\n" in raw or "\r" in raw:
        raise InventoryError("Git common-dir output is malformed")
    common = Path(raw)
    if not common.is_absolute():
        common = path / common
    if not common.is_absolute() or any(part in (".", "..") for part in common.parts):
        raise InventoryError("Git common-dir output escapes the worktree")
    try:
        handle = open_verified_tree(common)
    except (OSError, FsafetyError) as exc:
        raise InventoryError("Git common-dir cannot be opened safely") from exc
    try:
        return handle.device, handle.inode
    finally:
        handle.close()


def _git_worktrees(
    repository: Any, adapter: TrackerAdapter | None = None
) -> tuple[Path, ...]:
    executable = None
    try:
        verifier = adapter
        if verifier is None:
            verifier = BrSqliteV1Adapter()
        executable = verifier.verify_git_binary(repository.config.git_binary)
        result = run_verified_git_probe(
            executable, GitProbe.WORKTREE_LIST, repository.seed
        )
        if result.returncode != 0:
            raise InventoryError("Git worktree discovery failed")
        discovered = _parse_git_porcelain(result.stdout)
        seed_common = _common_dir_identity(
            repository, executable, repository.config.repository_seed, repository.seed
        )
        for path in discovered:
            root = _root_for(repository, path)
            if root is None:
                raise InventoryError(f"worktree is outside allowed roots: {path}")
            try:
                handle = open_descendant(root, path)
            except (FileNotFoundError, NotADirectoryError):
                continue
            except (OSError, FsafetyError) as exc:
                raise InventoryError(
                    f"worktree cannot be opened safely: {path}"
                ) from exc
            try:
                if (
                    _common_dir_identity(repository, executable, path, handle)
                    != seed_common
                ):
                    raise InventoryError("Git common-dir mismatch")
            finally:
                handle.close()
        return discovered
    except (
        AdapterError,
        FsafetyError,
        UnsupportedCapability,
        OSError,
        TimeoutError,
    ) as exc:
        raise InventoryError(f"Git worktree discovery failed: {exc}") from exc
    finally:
        if executable is not None:
            executable.close()


def discover_worktrees(
    repository: Any, *, _adapter: TrackerAdapter | None = None
) -> tuple[Path, ...]:
    """Return only Git-listed worktrees plus explicitly registered extras."""

    configured = tuple(Path(item) for item in repository.config.additional_worktrees)
    discovered = _git_worktrees(repository, _adapter)
    merged: set[Path] = set()
    for path in (*discovered, *configured):
        if not path.is_absolute() or any(part in (".", "..") for part in path.parts):
            raise InventoryError("worktree path must be absolute and traversal-free")
        if _root_for(repository, path) is None:
            raise InventoryError(f"worktree is outside allowed roots: {path}")
        if path in configured and path not in discovered:
            raise InventoryError("independent-clone extras are not registry-bound")
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
        if before.st_size > _MAX_REDIRECT_BYTES:
            raise InventoryError("redirect exceeds size limit")
        chunks: list[bytes] = []
        total = 0
        while chunk := os.read(fd, min(1024 * 1024, _MAX_REDIRECT_BYTES - total + 1)):
            total += len(chunk)
            if total > _MAX_REDIRECT_BYTES:
                raise InventoryError("redirect exceeds size limit")
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


def _codec_metadata(
    adapter: TrackerAdapter,
    canonical: Path,
    worktree: DirectoryHandle,
    executable: object,
) -> tuple[str, str, str]:
    """Consume only the adapter's descriptor-bound oracle result."""

    oracle = adapter.redirect_oracle(canonical, worktree, executable)
    if not isinstance(oracle, RedirectOracle):
        raise InventoryError("redirect codec oracle returned malformed data")
    if not oracle.codec_id or not isinstance(oracle.receipt_sha256, str):
        raise InventoryError("redirect codec oracle returned malformed data")
    if len(oracle.receipt_sha256) != 64 or any(
        char not in "0123456789abcdef" for char in oracle.receipt_sha256
    ):
        raise InventoryError("redirect codec oracle receipt is malformed")
    try:
        intended = oracle.intended_bytes.decode("utf-8")
    except (AttributeError, UnicodeDecodeError) as exc:
        raise InventoryError("oracle redirect bytes are malformed") from exc
    _validate_redirect_text(intended)
    return oracle.codec_id, intended, oracle.receipt_sha256


def _validate_redirect_text(value: str) -> None:
    if (
        not value
        or "\x00" in value
        or "\r" in value
        or value.count("\n") > 1
        or "\n" in value.rstrip("\n")
        or any(
            line.endswith((" ", "\t"))
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
    codec: str,
    intended: str,
    receipt: str,
) -> tuple[str, RedirectState | None]:
    canonical = repository.canonical
    if (beads.device, beads.inode) == (canonical.device, canonical.inode):
        if redirect.present:
            raise InventoryError("canonical store has an unexpected redirect")
        return "canonical", None
    if not redirect.present:
        return "noncanonical", RedirectState(
            False,
            None,
            None,
            beads.device,
            beads.inode,
            codec,
            intended,
            receipt,
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
            receipt,
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
            receipt,
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
        receipt,
    )


def _missing_record(path: Path) -> WorktreeRecord:
    return WorktreeRecord(path, "missing", 0, 0, (), None)


def build_manifest(repository: Any, adapter: TrackerAdapter) -> Manifest:
    """Build a deterministic, read-only manifest from bounded worktree paths."""

    if adapter.adapter_id != repository.config.adapter:
        raise InventoryError("adapter does not match repository registry")
    registry_sha = repository.registry_sha256
    if not isinstance(registry_sha, str) or len(registry_sha) != 64:
        raise InventoryError("validated repository has no registry SHA-256")
    try:
        executable = adapter.verify_binary(repository.config.tracker_binary)
    except Exception as exc:
        raise InventoryError(f"tracker binary verification failed: {exc}") from exc
    records: list[WorktreeRecord] = []
    seen_beads: set[tuple[int, int]] = set()
    try:
        codec: str | None = None
        intended: str | None = None
        oracle_receipt: str | None = None
        try:
            codec, intended, oracle_receipt = _codec_metadata(
                adapter,
                repository.config.canonical_beads,
                repository.seed,
                executable,
            )
        except (
            AdapterError,
            FsafetyError,
            UnsupportedCapability,
            OSError,
            TimeoutError,
        ):
            pass
        for path in discover_worktrees(repository, _adapter=adapter):
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
                    guard = repository.identity_guard
                    if guard is None:
                        raise InventoryError(
                            "validated repository has no identity guard"
                        )
                    try:
                        guard.claim(
                            repository.config.repo_id, path / ".beads", identity
                        )
                    except ValueError as exc:
                        raise InventoryError(str(exc)) from exc
                    classification = "unsupported"
                    backend_name: str | None = None
                    health_record: HealthFingerprint | None = None
                    sources: tuple[SourceFingerprint, ...] = ()
                    redirect: RedirectState | None = None
                    try:
                        backend = adapter.attest_backend(beads)
                        if backend.backend != "sqlite":
                            raise AdapterError("unsupported backend attestation")
                        backend_name = backend.backend
                    except (AdapterError, FsafetyError, OSError):
                        pass
                    try:
                        sources = _source_fingerprints(adapter, beads)
                    except (AdapterError, FsafetyError, InventoryError, OSError):
                        pass
                    try:
                        redirect = _read_redirect(beads)
                    except (FsafetyError, InventoryError, OSError):
                        pass
                    try:
                        health = adapter.verify_health(worktree, executable)
                        if (
                            health.dirty_count != 0
                            or health.db_newer
                            or health.jsonl_newer
                            or health.workspace_health != "healthy"
                        ):
                            raise AdapterError("tracker workspace is not healthy")
                        health_record = HealthFingerprint(
                            health.dirty_count,
                            health.db_newer,
                            health.jsonl_newer,
                            health.workspace_health,
                            sha256_hex(canonical_json_bytes(health.raw)),
                        )
                    except (
                        AdapterError,
                        FsafetyError,
                        UnsupportedCapability,
                        OSError,
                        TimeoutError,
                    ):
                        pass
                    if (
                        backend_name == "sqlite"
                        and health_record is not None
                        and sources
                        and redirect is not None
                        and codec is not None
                        and intended is not None
                        and oracle_receipt is not None
                    ):
                        try:
                            classification, redirect = _classify(
                                repository,
                                adapter,
                                worktree,
                                beads,
                                executable,
                                redirect,
                                codec,
                                intended,
                                oracle_receipt,
                            )
                        except (
                            AdapterError,
                            FsafetyError,
                            UnsupportedCapability,
                            OSError,
                            TimeoutError,
                        ):
                            classification = "unsupported"
                    records.append(
                        WorktreeRecord(
                            path,
                            classification,
                            worktree.device,
                            worktree.inode,
                            sources,
                            redirect,
                            backend_name,
                            health_record,
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
    return Manifest(
        "beads.redirect-convergence.manifest.v1",
        registry_sha,
        config.repo_id,
        config.adapter,
        config.canonical_beads,
        config.tracker_binary,
        config.git_binary,
        tuple(sorted(records, key=lambda item: os.fspath(item.path))),
        codec,
        intended,
        oracle_receipt,
    )
