"""Deterministic, read-only planning for redirect convergence."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .codec import canonical_json_bytes, sha256_hex
from .models import Manifest, Plan, RedirectState, Registry, RepositoryConfig


_PLAN_SCHEMA = "beads.redirect-convergence.plan.v1"
_REQUIRED_SOURCES = frozenset({"beads.db", "issues.jsonl"})
_KNOWN_SOURCES = frozenset(
    {"beads.db", "beads.db-wal", "beads.db-shm", "issues.jsonl"}
)


class DeterministicPlan(Plan):
    """A frozen plan whose digest is derived from its canonical contents."""

    @property
    def sha256(self) -> str:
        return sha256_hex(canonical_json_bytes(self))


@dataclass(frozen=True)
class PlanResult:
    """The independent outcome for one registry repository."""

    repo_id: str
    plan: Plan | None = None
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.plan is not None and self.error is None


@dataclass(frozen=True)
class PlanAllReceipt:
    """Aggregate read-only results without combining repository plan hashes."""

    results: tuple[PlanResult, ...]
    status: int

    @property
    def plans(self) -> tuple[Plan, ...]:
        """Return successful plans while preserving per-repository boundaries."""

        return tuple(result.plan for result in self.results if result.plan is not None)

    @property
    def errors(self) -> dict[str, str]:
        """Return repository errors without hiding successful results."""

        return {
            result.repo_id: result.error
            for result in self.results
            if result.error is not None
        }

    @property
    def exit_code(self) -> int:
        """Expose the process-style aggregate status under a descriptive alias."""

        return self.status


def _source_payload(source: object) -> dict[str, object]:
    return {
        "name": source.name,
        "device": source.device,
        "inode": source.inode,
        "size": source.size,
        "sha256": source.sha256,
    }


def _redirect_payload(redirect: RedirectState) -> dict[str, object]:
    return {
        "present": redirect.present,
        "mode": redirect.mode,
        "bytes": redirect.bytes,
        "parent_device": redirect.parent_device,
        "parent_inode": redirect.parent_inode,
        "codec": redirect.codec,
        "intended_bytes": redirect.intended_bytes,
    }


def _resolved_path(path: Path) -> Path:
    """Resolve only for stable ordering; manifest authority remains descriptor-bound."""

    return Path(os.path.realpath(path))


def _complete_noncanonical(worktree: object) -> bool:
    if worktree.classification != "noncanonical":
        return False
    if not worktree.path.is_absolute():
        return False
    if worktree.directory_device < 0 or worktree.directory_inode < 0:
        return False
    names = [source.name for source in worktree.sources]
    if (
        len(names) != len(set(names))
        or not _REQUIRED_SOURCES.issubset(names)
        or not set(names).issubset(_KNOWN_SOURCES)
    ):
        return False
    for source in worktree.sources:
        if (
            source.device < 0
            or source.inode < 0
            or source.size < 0
            or len(source.sha256) != 64
        ):
            return False
    redirect = worktree.redirect
    return (
        redirect is not None
        and redirect.codec is not None
        and redirect.intended_bytes is not None
        and redirect.parent_device >= 0
        and redirect.parent_inode >= 0
    )


def _action(worktree: object) -> dict[str, object]:
    redirect = worktree.redirect
    assert redirect is not None
    return {
        "operation": "redirect",
        "worktree_path": str(_resolved_path(worktree.path)),
        "directory_device": worktree.directory_device,
        "directory_inode": worktree.directory_inode,
        "sources": [
            _source_payload(source)
            for source in sorted(worktree.sources, key=lambda item: item.name)
        ],
        "redirect": _redirect_payload(redirect),
    }


def build_plan(manifest: Manifest) -> Plan:
    """Build a canonical plan from one captured, validated manifest.

    Eligibility is deliberately derived from the manifest's positive
    classification and complete source/redirect attestations.  Missing,
    unsupported, unresolved, canonical, and vanished entries are represented
    by the manifest but never become actions.
    """

    eligible = [
        worktree
        for worktree in manifest.worktrees
        if _complete_noncanonical(worktree)
    ]
    eligible.sort(key=lambda item: str(_resolved_path(item.path)))
    actions = tuple(_action(worktree) for worktree in eligible)
    manifest_sha256 = sha256_hex(canonical_json_bytes(manifest))
    return DeterministicPlan(
        _PLAN_SCHEMA,
        manifest_sha256,
        manifest.repo_id,
        manifest.adapter,
        manifest.canonical_beads,
        actions,
    )


def _plan_repository(config: RepositoryConfig) -> Plan:
    """Validate, inventory, and plan one repository without a mutation path."""

    from .adapters import BrSqliteV1Adapter
    from .inventory import build_manifest
    from .registry import validate_repository

    repository = validate_repository(config)
    try:
        adapter = BrSqliteV1Adapter()
        manifest = build_manifest(repository, adapter)
        return build_plan(manifest)
    finally:
        repository.close()


def plan_all(registry: Registry) -> PlanAllReceipt:
    """Plan each registry entry independently and return a process-style status.

    This function intentionally has no ``apply`` parameter and performs no
    writes.  One repository failure does not suppress plans for other entries.
    """

    results: list[PlanResult] = []
    for config in sorted(registry.repositories, key=lambda item: item.repo_id):
        try:
            results.append(PlanResult(config.repo_id, _plan_repository(config)))
        except Exception as exc:  # isolate one repository's failure
            results.append(PlanResult(config.repo_id, error=str(exc)))
    status = 0 if all(result.ok for result in results) else 1
    return PlanAllReceipt(tuple(results), status)
