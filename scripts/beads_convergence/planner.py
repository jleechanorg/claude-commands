"""Deterministic, read-only planning for redirect convergence."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .codec import canonical_json_bytes, sha256_hex
from .models import Manifest, Plan, RedirectState, Registry, RepositoryConfig
from .registry import (
    PhysicalIdentityClaims,
    ValidatedRepository,
    validate_registry,
    validate_repository,
)


_PLAN_SCHEMA = "beads.redirect-convergence.plan.v1"
_REQUIRED_SOURCES = frozenset({"beads.db", "issues.jsonl"})
_KNOWN_SOURCES = frozenset(
    {"beads.db", "beads.db-wal", "beads.db-shm", "issues.jsonl"}
)
_HEX_DIGITS = frozenset("0123456789abcdef")


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
        "oracle_receipt_sha256": redirect.oracle_receipt_sha256,
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
    if worktree.backend != "sqlite" or worktree.health is None:
        return False
    health = worktree.health
    if (
        health.dirty_count != 0
        or health.db_newer
        or health.jsonl_newer
        or health.workspace_health != "healthy"
        or len(health.receipt_sha256) != 64
        or not set(health.receipt_sha256).issubset(_HEX_DIGITS)
    ):
        return False
    names = [source.name for source in worktree.sources]
    if (
        len(names) != len(set(names))
        or not _REQUIRED_SOURCES.issubset(names)
        or not set(names).issubset(_KNOWN_SOURCES)
    ):
        return False
    source_identities: set[tuple[int, int]] = set()
    for source in worktree.sources:
        if (
            source.device < 0
            or source.inode < 0
            or source.size < 0
            or len(source.sha256) != 64
            or not set(source.sha256).issubset(_HEX_DIGITS)
            or (source.device, source.inode) in source_identities
        ):
            return False
        source_identities.add((source.device, source.inode))
    redirect = worktree.redirect
    if redirect is None:
        return False
    if (
        redirect.codec is None
        or not redirect.codec
        or redirect.intended_bytes is None
        or not redirect.intended_bytes
        or redirect.oracle_receipt_sha256 is None
        or len(redirect.oracle_receipt_sha256) != 64
        or not set(redirect.oracle_receipt_sha256).issubset(_HEX_DIGITS)
        or redirect.parent_device < 0
        or redirect.parent_inode < 0
    ):
        return False
    if redirect.present:
        return (
            redirect.bytes is not None
            and bool(redirect.bytes)
            and redirect.mode is not None
        )
    return redirect.bytes is None and redirect.mode is None


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

    manifest_attested = (
        manifest.redirect_codec is not None
        and bool(manifest.redirect_codec)
        and manifest.redirect_intended_bytes is not None
        and bool(manifest.redirect_intended_bytes)
        and manifest.redirect_oracle_receipt_sha256 is not None
        and len(manifest.redirect_oracle_receipt_sha256) == 64
        and set(manifest.redirect_oracle_receipt_sha256).issubset(_HEX_DIGITS)
    )
    eligible = [
        worktree
        for worktree in manifest.worktrees
        if manifest_attested and _complete_noncanonical(worktree)
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


def _plan_validated_repository(repository: ValidatedRepository) -> Plan:
    """Build a plan from retained validation authority without reopening it."""

    from .adapters import BrSqliteV1Adapter
    from .inventory import build_manifest

    adapter = BrSqliteV1Adapter()
    manifest = build_manifest(repository, adapter)
    return build_plan(manifest)


def _plan_repository(
    config: RepositoryConfig,
    registry_sha256: str,
    identity_guard: PhysicalIdentityClaims | None = None,
) -> Plan:
    """Validate, inventory, and plan one repository without a mutation path."""

    repository = validate_repository(config, _identity_guard=identity_guard)
    repository.registry_sha256 = registry_sha256
    try:
        return _plan_validated_repository(repository)
    finally:
        repository.close()


def plan_all(registry: Registry) -> PlanAllReceipt:
    """Plan each registry entry independently and return a process-style status.

    This function intentionally has no ``apply`` parameter and performs no
    writes.  One repository failure does not suppress plans for other entries.
    """

    results: list[PlanResult] = []
    registry_sha256 = sha256_hex(canonical_json_bytes(registry))

    try:
        validated = validate_registry(registry)
    except Exception as exc:
        del exc
        identity_guard = PhysicalIdentityClaims()
        for config in sorted(registry.repositories, key=lambda item: item.repo_id):
            try:
                results.append(
                    PlanResult(
                        config.repo_id,
                        _plan_repository(
                            config, registry_sha256, identity_guard
                        ),
                    )
                )
            except Exception as exc:  # isolate one repository's failure
                results.append(PlanResult(config.repo_id, error=str(exc)))
    else:
        for repository in sorted(validated, key=lambda item: item.config.repo_id):
            try:
                results.append(
                    PlanResult(
                        repository.config.repo_id,
                        _plan_validated_repository(repository),
                    )
                )
            except Exception as exc:  # isolate one repository's failure
                results.append(
                    PlanResult(repository.config.repo_id, error=str(exc))
                )
            finally:
                repository.close()
    status = 0 if all(result.ok for result in results) else 1
    return PlanAllReceipt(tuple(results), status)
