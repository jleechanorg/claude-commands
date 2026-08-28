"""Task 9 fixture certification for multi-repository convergence."""

from __future__ import annotations

import hashlib
import os
import tempfile
import unittest
from dataclasses import dataclass, replace
from pathlib import Path
from unittest.mock import patch

from scripts.beads_convergence import adapters as adapters_module
from scripts.beads_convergence import inventory, planner
from scripts.beads_convergence.adapters import (
    BackendAttestation,
    HealthAttestation,
    RedirectOracle,
    SourceMember,
    SourceSnapshot,
    WriterLease,
)
from scripts.beads_convergence.approval import (
    SignedApproval,
    tool_tree_sha256,
)
from scripts.beads_convergence.codec import canonical_json_bytes, sha256_hex
from scripts.beads_convergence.models import (
    ApprovalEnvelope,
    BinaryBinding,
    Manifest,
    Registry,
    RepositoryConfig,
)
from scripts.beads_convergence.registry import RegistryError, validate_registry
from scripts.beads_convergence.transaction import (
    ApplyRequest,
    FixtureControlStore,
    apply_plan,
)


class _FixtureExecutable:
    def close(self) -> None:
        return None


class _FixtureVerifier:
    fixture_only = True
    fingerprint = "SHA256:fixture-external-key"

    def verify(self, envelope: bytes, signature: bytes, **bindings: object) -> bool:
        return (
            signature == b"fixture-external-signature"
            and bindings["namespace"]
            == "beads-redirect-convergence-v1@jleechan.org"
            and bindings["principal"] == "ops@example.test"
            and envelope.startswith(b'{"adapter"')
        )


class _MultiRepoFixtureAdapter:
    """Disposable adapter that proves the fixture writer-exclusion contract."""

    adapter_id = "br-sqlite-v1"
    fixture_only = True
    source_names = ("beads.db", "beads.db-wal", "beads.db-shm", "issues.jsonl")

    def __init__(self, canonical: Path) -> None:
        self.canonical = canonical

    def verify_binary(self, binding: object) -> _FixtureExecutable:
        del binding
        return _FixtureExecutable()

    def verify_git_binary(self, binding: object) -> _FixtureExecutable:
        del binding
        return _FixtureExecutable()

    def attest_backend(self, beads: object) -> BackendAttestation:
        names = set(os.listdir(beads.fd))
        if not {"beads.db", "issues.jsonl"}.issubset(names):
            raise AssertionError("fixture source family is incomplete")
        return BackendAttestation(
            "sqlite", tuple(name for name in self.source_names if name in names)
        )

    def verify_health(self, worktree: object, executable: object) -> HealthAttestation:
        del worktree, executable
        return HealthAttestation(
            0, False, False, "healthy", {"workspace_health": "healthy"}
        )

    def fingerprint_sources(self, beads: object) -> SourceSnapshot:
        members: list[SourceMember] = []
        for name in self.source_names:
            try:
                fd = os.open(
                    name,
                    os.O_RDONLY | getattr(os, "O_CLOEXEC", 0),
                    dir_fd=beads.fd,
                )
            except FileNotFoundError:
                continue
            try:
                info = os.fstat(fd)
                digest = hashlib.sha256()
                size = 0
                while chunk := os.read(fd, 1024 * 1024):
                    digest.update(chunk)
                    size += len(chunk)
                members.append(
                    SourceMember(name, info.st_dev, info.st_ino, size, digest.hexdigest())
                )
            finally:
                os.close(fd)
        return SourceSnapshot(tuple(members), True, False, True, "fixture lease")

    def redirect_oracle(
        self, canonical: Path, worktree: object, executable: object
    ) -> RedirectOracle:
        del canonical, worktree, executable
        intended = (str(self.canonical) + "\n").encode()
        return RedirectOracle(
            "br-sqlite-v1-redirect-v1", intended, sha256_hex(intended)
        )

    def resolve_authority(self, worktree: object, executable: object) -> Path:
        del executable
        redirect = Path(worktree.display_path) / ".beads" / "redirect"
        if redirect.is_file() and redirect.read_bytes() == (
            str(self.canonical) + "\n"
        ).encode():
            return self.canonical
        return Path(worktree.display_path) / ".beads"

    def acquire_writer_exclusion(
        self, beads: object, executable: object | None = None
    ) -> WriterLease:
        del beads, executable
        return WriterLease(True, "fixture writer lease", "fixture")


@dataclass(frozen=True)
class _FixtureRepository:
    repo_id: str
    root: Path
    canonical: Path
    targets: tuple[Path, ...]
    config: RepositoryConfig


def _write_store(path: Path, marker: str) -> None:
    beads = path / ".beads"
    beads.mkdir(parents=True)
    (beads / "beads.db").write_bytes(b"SQLite format 3\x00" + marker.encode())
    (beads / "issues.jsonl").write_bytes(
        ("{\"fixture\":\"" + marker + "\"}\n").encode()
    )


def _fixture_repository(root: Path, repo_id: str, target_count: int) -> _FixtureRepository:
    repository_root = root / repo_id
    seed = repository_root / "seed"
    canonical = seed / ".beads"
    _write_store(seed, repo_id + "-canonical")
    targets = tuple(
        repository_root / f"target-{index}" for index in range(target_count)
    )
    for index, target in enumerate(targets):
        _write_store(target, f"{repo_id}-target-{index}")
    if repo_id == "repo-a":
        (targets[-1] / ".beads" / "redirect").write_bytes(
            (str(canonical) + "\n").encode()
        )
    evidence = root / "evidence" / repo_id
    evidence.mkdir(parents=True)
    binding = BinaryBinding(Path("/bin/true"), "fixture", "a" * 64)
    config = RepositoryConfig(
        repo_id,
        "br-sqlite-v1",
        seed,
        canonical,
        (repository_root,),
        targets,
        binding,
        binding,
        evidence,
    )
    return _FixtureRepository(repo_id, repository_root, canonical, targets, config)


def _registry(repositories: tuple[_FixtureRepository, ...]) -> Registry:
    return Registry(
        "beads.redirect-convergence.registry.v1",
        "fixture-host",
        tuple(repository.config for repository in repositories),
    )


def _monitored_bytes(repositories: tuple[_FixtureRepository, ...]) -> dict[str, bytes]:
    paths: list[Path] = []
    for repository in repositories:
        for worktree in (repository.canonical.parent, *repository.targets):
            beads = worktree / ".beads"
            paths.extend(beads / name for name in ("beads.db", "issues.jsonl"))
            redirect = beads / "redirect"
            if redirect.exists():
                paths.append(redirect)
    return {os.fspath(path): path.read_bytes() for path in paths}


def _run_plan_all(
    registry: Registry, repositories: tuple[_FixtureRepository, ...]
) -> tuple[planner.PlanAllReceipt, dict[str, Manifest]]:
    adapters = {
        repository.repo_id: _MultiRepoFixtureAdapter(repository.canonical)
        for repository in repositories
    }
    manifests: dict[str, Manifest] = {}
    real_build_manifest = inventory.build_manifest

    def capture_manifest(repository: object, adapter: object) -> Manifest:
        manifest = real_build_manifest(repository, adapter)
        manifests[manifest.repo_id] = manifest
        return manifest

    def fixture_worktrees(repository: object, adapter: object = None) -> tuple[Path, ...]:
        del adapter
        config = repository.config
        return (config.repository_seed, *config.additional_worktrees)

    adapter_order = iter(adapters[repository.repo_id] for repository in repositories)
    with patch.object(
        adapters_module,
        "BrSqliteV1Adapter",
        side_effect=lambda: next(adapter_order),
    ), patch.object(
        inventory, "_git_worktrees", side_effect=fixture_worktrees
    ), patch.object(
        inventory, "build_manifest", side_effect=capture_manifest
    ):
        receipt = planner.plan_all(registry)
    return receipt, manifests


def _apply_request(
    repository: _FixtureRepository,
    registry: Registry,
    manifest: Manifest,
    plan: object,
    control_root: Path,
) -> ApplyRequest:
    registry_sha = sha256_hex(canonical_json_bytes(registry))
    manifest_sha = sha256_hex(canonical_json_bytes(manifest))
    identity = repository.canonical.stat()
    envelope = ApprovalEnvelope(
        "beads.redirect-convergence.approval.v1",
        "apply",
        repository.repo_id,
        f"nonce-{repository.repo_id}",
        "2026-08-27T00:00:00Z",
        "2026-08-28T00:00:00Z",
        registry_sha,
        manifest_sha,
        plan.sha256,
        manifest.canonical_beads,
        manifest.adapter,
        manifest.tracker_binary,
        manifest.git_binary,
        identity.st_dev,
        identity.st_ino,
        tool_tree_sha256(),
        None,
        None,
        "ops@example.test",
        "SHA256:fixture-external-key",
    )
    return ApplyRequest(
        True,
        registry,
        manifest,
        plan,
        _MultiRepoFixtureAdapter(repository.canonical),
        SignedApproval(envelope, b"fixture-external-signature"),
        _FixtureVerifier(),
        FixtureControlStore(control_root),
        "2026-08-27T12:00:00Z",
        f"run-{repository.repo_id}",
    )


class MultiRepoFixtureTest(unittest.TestCase):
    def test_plan_all_two_repositories_is_deterministic_and_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repositories = (
                _fixture_repository(root, "repo-a", 3),
                _fixture_repository(root, "repo-b", 1),
            )
            registry = _registry(repositories)
            before = _monitored_bytes(repositories)
            first, first_manifests = _run_plan_all(registry, repositories)
            second, second_manifests = _run_plan_all(registry, repositories)

            self.assertEqual(first.status, 0, first.errors)
            self.assertEqual(second.status, 0, second.errors)
            self.assertEqual(
                [result.repo_id for result in first.results], ["repo-a", "repo-b"]
            )
            self.assertEqual([len(plan.actions) for plan in first.plans], [2, 1])
            self.assertEqual(
                [plan.sha256 for plan in first.plans],
                [plan.sha256 for plan in second.plans],
            )
            classes = {
                record.path.name: record.classification
                for record in first_manifests["repo-a"].worktrees
            }
            self.assertEqual(classes["target-2"], "redirected_canonical")
            self.assertEqual(before, _monitored_bytes(repositories))
            self.assertEqual(
                canonical_json_bytes(first_manifests["repo-a"]),
                canonical_json_bytes(second_manifests["repo-a"]),
            )

    def test_fixture_apply_is_separate_and_cannot_change_neighbor_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repositories = (
                _fixture_repository(root, "repo-a", 3),
                _fixture_repository(root, "repo-b", 1),
            )
            registry = _registry(repositories)
            receipt, manifests = _run_plan_all(registry, repositories)
            plans = {result.repo_id: result.plan for result in receipt.results}
            neighbor_before = _monitored_bytes((repositories[1],))

            first_apply = repositories[0]
            first_plan = plans[first_apply.repo_id]
            assert first_plan is not None
            first_receipt = apply_plan(
                _apply_request(
                    first_apply,
                    registry,
                    manifests[first_apply.repo_id],
                    first_plan,
                    root / "control" / first_apply.repo_id,
                )
            )
            self.assertEqual(first_receipt.status, "COMMITTED")
            self.assertEqual(neighbor_before, _monitored_bytes((repositories[1],)))

            second_apply = repositories[1]
            second_plan = plans[second_apply.repo_id]
            assert second_plan is not None
            second_receipt = apply_plan(
                _apply_request(
                    second_apply,
                    registry,
                    manifests[second_apply.repo_id],
                    second_plan,
                    root / "control" / second_apply.repo_id,
                )
            )
            self.assertEqual(second_receipt.status, "COMMITTED")

            for repository in repositories:
                targets = (
                    repository.targets[:-1]
                    if repository.repo_id == "repo-a"
                    else repository.targets
                )
                for target in targets:
                    self.assertEqual(
                        (target / ".beads" / "redirect").read_bytes(),
                        (str(repository.canonical) + "\n").encode(),
                    )

    def test_hostile_cross_registration_is_rejected_by_membership_identity_guard(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repositories = (_fixture_repository(root, "repo-a", 3), _fixture_repository(root, "repo-b", 1))
            hostile_b = replace(
                repositories[1].config,
                allowed_worktree_roots=(root,),
                additional_worktrees=(
                    *repositories[1].config.additional_worktrees,
                    repositories[0].targets[0],
                ),
            )
            hostile = Registry(
                "beads.redirect-convergence.registry.v1",
                "fixture-host",
                (repositories[0].config, hostile_b),
            )
            with self.assertRaisesRegex(
                RegistryError, r"duplicate managed \.beads identity"
            ):
                validate_registry(hostile)


if __name__ == "__main__":
    unittest.main()
