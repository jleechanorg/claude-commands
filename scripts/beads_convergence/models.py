"""Frozen data models shared by the convergence engine and its codecs."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BinaryBinding:
    path: Path
    version: str
    sha256: str


@dataclass(frozen=True)
class RepositoryConfig:
    repo_id: str
    adapter: str
    repository_seed: Path
    canonical_beads: Path
    allowed_worktree_roots: tuple[Path, ...]
    additional_worktrees: tuple[Path, ...]
    tracker_binary: BinaryBinding
    git_binary: BinaryBinding
    evidence_root: Path


@dataclass(frozen=True)
class Registry:
    schema: str
    host_id: str
    repositories: tuple[RepositoryConfig, ...]


@dataclass(frozen=True)
class ApprovalEnvelope:
    schema: str
    operation: str
    repo_id: str
    nonce: str
    issued_at: str
    expires_at: str
    registry_sha256: str
    manifest_sha256: str
    plan_sha256: str
    canonical_beads: Path
    adapter: str
    tracker_binary: BinaryBinding
    git_binary: BinaryBinding
    signer_principal: str
    signer_fingerprint: str


@dataclass(frozen=True)
class SourceFingerprint:
    name: str
    device: int
    inode: int
    size: int
    sha256: str


@dataclass(frozen=True)
class RedirectState:
    present: bool
    mode: int | None
    bytes: str | None
    parent_device: int
    parent_inode: int
    codec: str | None
    intended_bytes: str | None
    oracle_receipt_sha256: str | None = None


@dataclass(frozen=True)
class HealthFingerprint:
    dirty_count: int
    db_newer: bool
    jsonl_newer: bool
    workspace_health: str
    receipt_sha256: str


@dataclass(frozen=True)
class WorktreeRecord:
    path: Path
    classification: str
    directory_device: int
    directory_inode: int
    sources: tuple[SourceFingerprint, ...]
    redirect: RedirectState | None
    backend: str | None = None
    health: HealthFingerprint | None = None


@dataclass(frozen=True)
class Manifest:
    schema: str
    registry_sha256: str
    repo_id: str
    adapter: str
    canonical_beads: Path
    tracker_binary: BinaryBinding
    git_binary: BinaryBinding
    worktrees: tuple[WorktreeRecord, ...]
    redirect_codec: str | None = None
    redirect_intended_bytes: str | None = None
    redirect_oracle_receipt_sha256: str | None = None


@dataclass(frozen=True)
class Plan:
    schema: str
    manifest_sha256: str
    repo_id: str
    adapter: str
    canonical_beads: Path
    actions: tuple[dict[str, object], ...]
