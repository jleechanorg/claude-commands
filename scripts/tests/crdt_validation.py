#!/usr/bin/env python3
"""Unified validation harness for the memory backup CRDT implementation.

This tool consolidates the ad-hoc ``test_crdt_*.py`` helpers that previously
lived in ``scripts/`` into a single, data-driven command-line utility.  The
suite is intentionally lightweight – it focuses on representative scenarios for
mathematical properties, edge cases, performance characteristics, production
workflows, and security hardening.  Execute it via::

    python -m scripts.tests.crdt_validation --list
    python -m scripts.tests.crdt_validation --group properties

If the ``memory_backup_crdt`` module is not present (for example, when the
submodule lives in a different repository), scenarios are marked as skipped
rather than raising import errors.  This mirrors the behaviour of the original
scripts while providing a clearer summary at the end of the run.
"""

from __future__ import annotations

import argparse
import importlib.util
import itertools
import statistics
import sys
import time
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers for loading the optional memory_backup_crdt module
# ---------------------------------------------------------------------------


def _load_crdt_module() -> object | None:
    """Attempt to import ``memory_backup_crdt`` from common locations.

    Historically the CRDT module has moved between ``scripts/`` and
    ``scripts/memory_sync/``.  The original helper scripts attempted to import
    it eagerly which caused confusing ``ModuleNotFoundError`` exceptions for
    contributors without the optional component.  We replicate the search logic
    used by ``scripts/tests/test_crdt_integration.py`` but return ``None`` when
    the module cannot be located.
    """

    base_dir = Path(__file__).resolve().parent
    candidate_paths = [
        base_dir / "memory_backup_crdt.py",
        base_dir.parent / "memory_backup_crdt.py",
        base_dir.parent / "memory_sync" / "memory_backup_crdt.py",
        base_dir.parent.parent / "memory_backup_crdt.py",
    ]

    for path in candidate_paths:
        if path.exists():
            spec = importlib.util.spec_from_file_location("memory_backup_crdt", path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return module
    return None


_CRDT_MODULE = _load_crdt_module()
MemoryBackupCRDT = getattr(_CRDT_MODULE, "MemoryBackupCRDT", None) if _CRDT_MODULE else None
crdt_merge = getattr(_CRDT_MODULE, "crdt_merge", None) if _CRDT_MODULE else None
_parse_timestamp = getattr(_CRDT_MODULE, "_parse_timestamp", None) if _CRDT_MODULE else None

CRDT_AVAILABLE = MemoryBackupCRDT is not None and crdt_merge is not None


# ---------------------------------------------------------------------------
# Dataclasses used to model scenarios and results
# ---------------------------------------------------------------------------


@dataclass
class ScenarioResult:
    name: str
    status: str
    details: list[str] = field(default_factory=list)

    def with_prefix(self) -> str:
        icon = {"pass": "✅", "fail": "❌", "skip": "⚠️"}[self.status]
        return f"{icon} {self.name}"


@dataclass
class Scenario:
    name: str
    description: str
    runner: Callable[[], ScenarioResult]


@dataclass
class ScenarioGroup:
    name: str
    description: str
    scenarios: Sequence[Scenario]


def _skip(name: str, reason: str) -> ScenarioResult:
    return ScenarioResult(name=name, status="skip", details=[reason])


def _fail(name: str, *details: str) -> ScenarioResult:
    return ScenarioResult(name=name, status="fail", details=list(details))


def _pass(name: str, *details: str) -> ScenarioResult:
    return ScenarioResult(name=name, status="pass", details=list(details))


# ---------------------------------------------------------------------------
# Shared data factories
# ---------------------------------------------------------------------------


def _entry(entry_id: str, content: str, host: str, timestamp: str, unique_id: str) -> dict[str, object]:
    return {
        "id": entry_id,
        "content": content,
        "_crdt_metadata": {
            "host": host,
            "timestamp": timestamp,
            "version": 1,
            "unique_id": unique_id,
        },
    }


def _run_merge(*datasets: Sequence[Iterable[dict[str, object]]]):
    if not CRDT_AVAILABLE:
        raise RuntimeError("CRDT module not available")
    formatted: list[list[dict[str, object]]] = []
    for dataset in datasets:
        formatted.append(list(dataset))
    return crdt_merge(formatted)


# ---------------------------------------------------------------------------
# Scenario implementations – Properties
# ---------------------------------------------------------------------------


def _scenario_commutativity() -> ScenarioResult:
    if not CRDT_AVAILABLE:
        return _skip("Commutativity", "memory_backup_crdt module is not available")

    entries_a = [_entry("mem_001", "Content A", "host_a", "2025-01-01T00:00:01Z", "host_a_mem_001_1")]
    entries_b = [_entry("mem_001", "Content B", "host_b", "2025-01-01T00:00:02Z", "host_b_mem_001_1")]

    try:
        merge_ab = _run_merge(entries_a, entries_b)
        merge_ba = _run_merge(entries_b, entries_a)
    except Exception as exc:  # pragma: no cover - defensive safeguard
        return _fail("Commutativity", f"Exception during merge: {exc}")

    if merge_ab == merge_ba:
        detail = f"Result entry: {merge_ab[0]['content'] if merge_ab else 'empty'}"
        return _pass("Commutativity", detail)
    return _fail("Commutativity", "merge(A, B) != merge(B, A)")


def _scenario_associativity() -> ScenarioResult:
    if not CRDT_AVAILABLE:
        return _skip("Associativity", "memory_backup_crdt module is not available")

    entries_a = [_entry("mem_001", "A", "host_a", "2025-01-01T00:00:01Z", "host_a_mem_001_1")]
    entries_b = [_entry("mem_001", "B", "host_b", "2025-01-01T00:00:02Z", "host_b_mem_001_1")]
    entries_c = [_entry("mem_001", "C", "host_c", "2025-01-01T00:00:03Z", "host_c_mem_001_1")]

    try:
        left = _run_merge(_run_merge(entries_a, entries_b), entries_c)
        right = _run_merge(entries_a, _run_merge(entries_b, entries_c))
    except Exception as exc:  # pragma: no cover - defensive safeguard
        return _fail("Associativity", f"Exception during merge: {exc}")

    if left == right:
        return _pass("Associativity", "(A∪B)∪C == A∪(B∪C)")
    return _fail("Associativity", "Associativity property violated")


def _scenario_idempotence() -> ScenarioResult:
    if not CRDT_AVAILABLE:
        return _skip("Idempotence", "memory_backup_crdt module is not available")

    entries = [_entry("mem_001", "Stable", "host_a", "2025-01-01T00:00:01Z", "host_a_mem_001_1")]
    try:
        result = _run_merge(entries, entries)
    except Exception as exc:  # pragma: no cover - defensive safeguard
        return _fail("Idempotence", f"Exception during merge: {exc}")

    if len(result) == 1 and result == entries:
        return _pass("Idempotence", "merge(A, A) preserved the entry")
    return _fail("Idempotence", "Idempotence property violated")


def _scenario_formal_verification() -> ScenarioResult:
    if not CRDT_AVAILABLE:
        return _skip("Formal verification", "memory_backup_crdt module is not available")

    datasets = [
        [_entry("mem", "Early", "host_a", "2025-01-01T00:00:01Z", "uuid-early")],
        [_entry("mem", "Later", "host_b", "2025-01-01T00:00:02Z", "uuid-late")],
        [_entry("mem", "Alpha", "host_c", "2025-01-01T00:00:01Z", "uuid-alpha")],
        [_entry("mem", "Zulu", "host_d", "2025-01-01T00:00:01Z", "uuid-zulu")],
    ]

    commutativity_violations = 0
    associativity_violations = 0

    for dataset_a, dataset_b in itertools.permutations(datasets, 2):
        if _run_merge(dataset_a, dataset_b) != _run_merge(dataset_b, dataset_a):
            commutativity_violations += 1

    for dataset_a, dataset_b, dataset_c in itertools.permutations(datasets, 3):
        left = _run_merge(_run_merge(dataset_a, dataset_b), dataset_c)
        right = _run_merge(dataset_a, _run_merge(dataset_b, dataset_c))
        if left != right:
            associativity_violations += 1

    if commutativity_violations == 0 and associativity_violations == 0:
        return _pass("Formal verification", "All pairwise/triple combinations stable")

    return _fail(
        "Formal verification",
        f"Commutativity failures: {commutativity_violations}",
        f"Associativity failures: {associativity_violations}",
    )


# ---------------------------------------------------------------------------
# Scenario implementations – Edge cases
# ---------------------------------------------------------------------------


def _scenario_identical_metadata() -> ScenarioResult:
    if not CRDT_AVAILABLE:
        return _skip("Identical metadata", "memory_backup_crdt module is not available")

    entry_a = _entry("mem", "Alpha", "host_a", "2025-01-01T00:00:01Z", "identical-uuid")
    entry_b = _entry("mem", "Beta", "host_b", "2025-01-01T00:00:01Z", "identical-uuid")

    try:
        merge_ab = _run_merge([entry_a], [entry_b])
        merge_ba = _run_merge([entry_b], [entry_a])
    except Exception as exc:  # pragma: no cover - defensive safeguard
        return _fail("Identical metadata", f"Exception during merge: {exc}")

    deterministic = merge_ab == merge_ba
    winner = merge_ab[0]["content"] if merge_ab else "<empty>"
    detail = f"Deterministic winner: {winner}"

    if deterministic:
        return _pass("Identical metadata", detail)
    return _fail("Identical metadata", "Merges produced different winners", detail)


def _scenario_uuid_uniqueness() -> ScenarioResult:
    if MemoryBackupCRDT is None:
        return _skip("UUID uniqueness", "MemoryBackupCRDT class unavailable")

    generator = MemoryBackupCRDT("edge_host")
    uuids = set()

    for index in range(500):
        entry = {"id": f"mem_{index}", "content": f"Entry {index}"}
        with_meta = generator.inject_metadata(entry)
        uuids.add(with_meta.get("_crdt_metadata", {}).get("unique_id"))

    collisions = 500 - len(uuids)
    detail = f"Generated {len(uuids)} unique IDs, collisions: {collisions}"

    if collisions == 0:
        return _pass("UUID uniqueness", detail)
    return _fail("UUID uniqueness", detail)


def _scenario_timestamp_parsing() -> ScenarioResult:
    if _parse_timestamp is None:
        return _skip("Timestamp parsing", "_parse_timestamp helper unavailable")

    cases = [
        "2025-01-01T00:00:01Z",
        "2025-01-01T00:00:01+00:00",
        "2025-01-01T00:00:01.123456Z",
        "1970-01-01T00:00:00Z",
    ]

    failures: list[str] = []
    for case in cases:
        try:
            parsed = _parse_timestamp(case)
            if getattr(parsed, "tzinfo", None) is None:
                failures.append(f"Timezone info missing for {case}")
        except Exception as exc:  # pragma: no cover - defensive safeguard
            failures.append(f"Failed to parse {case}: {exc}")

    if not failures:
        return _pass("Timestamp parsing", f"Handled {len(cases)} formats")
    return _fail("Timestamp parsing", *failures)


# ---------------------------------------------------------------------------
# Scenario implementations – Performance
# ---------------------------------------------------------------------------


def _generate_entries(count: int, host: str = "perf") -> list[dict[str, object]]:
    return [
        _entry(
            f"perf_{index % 50}",
            f"Content {index}",
            f"{host}_{index % 5}",
            f"2025-01-01T00:00:{index:02d}Z",
            f"uuid-{host}-{index}",
        )
        for index in range(count)
    ]


def _scenario_throughput() -> ScenarioResult:
    if not CRDT_AVAILABLE:
        return _skip("Throughput", "memory_backup_crdt module is not available")

    counts = [200, 400, 800]
    merge_times: list[float] = []

    for count in counts:
        dataset = _generate_entries(count)
        start = time.perf_counter()
        _run_merge(dataset)
        elapsed = time.perf_counter() - start
        merge_times.append(elapsed)

    average = statistics.mean(merge_times)
    detail = ", ".join(f"{c}: {t:.3f}s" for c, t in zip(counts, merge_times))

    if average < 5.0:  # Generous threshold keeps the check informative yet forgiving
        return _pass("Throughput", f"Average merge time {average:.3f}s", detail)
    return _fail("Throughput", f"Average merge time {average:.3f}s exceeds 5s", detail)


def _scenario_concurrent_merge() -> ScenarioResult:
    if not CRDT_AVAILABLE:
        return _skip("Concurrent merge", "memory_backup_crdt module is not available")

    datasets = [_generate_entries(200, host=f"host{i}") for i in range(4)]

    start_sequential = time.perf_counter()
    sequential = _run_merge(*datasets)
    sequential_time = time.perf_counter() - start_sequential

    # Two-stage merge to simulate concurrent batches
    mid_results = []
    start_concurrent = time.perf_counter()
    for left, right in zip(datasets[::2], datasets[1::2]):
        mid_results.append(_run_merge(left, right))
    concurrent = _run_merge(*mid_results)
    concurrent_time = time.perf_counter() - start_concurrent

    if len(sequential) != len(concurrent):
        return _fail("Concurrent merge", "Concurrent merge produced different results")

    detail = f"Sequential {sequential_time:.3f}s vs staged {concurrent_time:.3f}s"
    return _pass("Concurrent merge", detail)


# ---------------------------------------------------------------------------
# Scenario implementations – Production realism
# ---------------------------------------------------------------------------


def _scenario_concurrent_backups() -> ScenarioResult:
    if not CRDT_AVAILABLE:
        return _skip("Concurrent backups", "memory_backup_crdt module is not available")

    hosts = ["web-1", "web-2", "worker-1", "scheduler-1"]
    host_batches: list[list[dict[str, object]]] = []

    for host in hosts:
        batch = []
        for index in range(80):
            batch.append(
                _entry(
                    f"conversation_{index % 20}",
                    f"{host} entry {index}",
                    host,
                    f"2025-08-18T10:00:{index:02d}Z",
                    f"{host}-uuid-{index}",
                )
            )
        host_batches.append(batch)

    merged = _run_merge(*host_batches)
    conversation_ids = {entry["id"] for entry in merged if entry["id"].startswith("conversation_")}

    if len(conversation_ids) == 20:
        return _pass("Concurrent backups", f"Merged {len(merged)} entries across {len(hosts)} hosts")
    return _fail("Concurrent backups", f"Expected 20 conversations, found {len(conversation_ids)}")


def _scenario_high_volume() -> ScenarioResult:
    if not CRDT_AVAILABLE:
        return _skip("High-volume dataset", "memory_backup_crdt module is not available")

    total_entries = 1500
    entries = _generate_entries(total_entries, host="highvolume")
    batches = [entries[i:i + 500] for i in range(0, total_entries, 500)]

    start = time.perf_counter()
    merged = _run_merge(*batches)
    elapsed = time.perf_counter() - start

    if len(merged) == len(entries):
        return _pass("High-volume dataset", f"Merged {len(entries)} entries in {elapsed:.3f}s")
    return _fail("High-volume dataset", f"Expected {len(entries)} entries, found {len(merged)}")


# ---------------------------------------------------------------------------
# Scenario implementations – Security hardening
# ---------------------------------------------------------------------------


def _scenario_input_sanitization() -> ScenarioResult:
    if MemoryBackupCRDT is None:
        return _skip("Input sanitization", "MemoryBackupCRDT class unavailable")

    backup = MemoryBackupCRDT("security_host")
    malicious_payloads = [
        {"id": "'; DROP TABLE users; --", "content": "sql"},
        {"id": "../../../etc/passwd", "content": "path traversal"},
        {"id": "test; rm -rf /", "content": "command injection"},
        {"id": "dos", "content": "X" * 50000},
    ]

    issues: list[str] = []
    for payload in malicious_payloads:
        try:
            enriched = backup.inject_metadata(payload)
            merged = _run_merge([enriched])
            if len(merged) != 1 or "_crdt_metadata" not in enriched:
                issues.append(f"Metadata missing or merge failed for id={payload['id']}")
        except Exception as exc:  # pragma: no cover - defensive safeguard
            issues.append(f"Exception processing id={payload['id']}: {exc}")

    if not issues:
        return _pass("Input sanitization", f"Processed {len(malicious_payloads)} payloads safely")
    return _fail("Input sanitization", *issues)


# ---------------------------------------------------------------------------
# Registry of scenario groups
# ---------------------------------------------------------------------------


SCENARIO_GROUPS: dict[str, ScenarioGroup] = {
    "properties": ScenarioGroup(
        name="CRDT mathematical properties",
        description="Core algebraic guarantees that the merge function must satisfy.",
        scenarios=[
            Scenario("Commutativity", "merge(A,B) should equal merge(B,A)", _scenario_commutativity),
            Scenario("Associativity", "merge(merge(A,B),C) == merge(A,merge(B,C))", _scenario_associativity),
            Scenario("Idempotence", "merge(A,A) should equal A", _scenario_idempotence),
            Scenario("Formal verification", "Pairs/triples across representative datasets", _scenario_formal_verification),
        ],
    ),
    "edge_cases": ScenarioGroup(
        name="Edge cases",
        description="Determinism and correctness under tricky metadata and parsing conditions.",
        scenarios=[
            Scenario("Identical metadata", "Deterministic winner selection when metadata matches", _scenario_identical_metadata),
            Scenario("UUID uniqueness", "Ensure metadata injection produces unique IDs", _scenario_uuid_uniqueness),
            Scenario("Timestamp parsing", "Verify helper handles common timestamp formats", _scenario_timestamp_parsing),
        ],
    ),
    "performance": ScenarioGroup(
        name="Performance & scalability",
        description="Light-weight performance probes for local validation.",
        scenarios=[
            Scenario("Throughput", "Measure merge throughput across data sizes", _scenario_throughput),
            Scenario("Concurrent merge", "Compare staged merges with sequential merge", _scenario_concurrent_merge),
        ],
    ),
    "production": ScenarioGroup(
        name="Production realism",
        description="Scenario-based checks that mimic operational workloads.",
        scenarios=[
            Scenario("Concurrent backups", "Multiple hosts writing overlapping conversations", _scenario_concurrent_backups),
            Scenario("High-volume dataset", "Large batch merge without data loss", _scenario_high_volume),
        ],
    ),
    "security": ScenarioGroup(
        name="Security hardening",
        description="Defensive checks against malicious or malformed input.",
        scenarios=[
            Scenario("Input sanitization", "Ensure metadata injection handles adversarial payloads", _scenario_input_sanitization),
        ],
    ),
}


# ---------------------------------------------------------------------------
# Command-line interface
# ---------------------------------------------------------------------------


def _list_groups() -> None:
    print("Available scenario groups:\n")
    for key, group in SCENARIO_GROUPS.items():
        print(f"- {key}: {group.name}")
        print(f"    {group.description}")
        for scenario in group.scenarios:
            print(f"    * {scenario.name} – {scenario.description}")
        print()


def _run_group(group_key: str) -> list[ScenarioResult]:
    group = SCENARIO_GROUPS[group_key]
    print(f"\n=== {group.name} ===")
    print(group.description)

    results: list[ScenarioResult] = []
    for scenario in group.scenarios:
        try:
            result = scenario.runner()
        except Exception as exc:  # pragma: no cover - defensive safeguard
            result = _fail(scenario.name, f"Unhandled exception: {exc}")
        print(result.with_prefix())
        for detail in result.details:
            print(f"   {detail}")
        results.append(result)
    return results


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Unified CRDT validation harness")
    parser.add_argument(
        "--group",
        action="append",
        choices=list(SCENARIO_GROUPS.keys()),
        help="Scenario group(s) to execute. Defaults to all groups.",
    )
    parser.add_argument("--list", action="store_true", help="List available scenario groups and exit")

    args = parser.parse_args(argv)

    if args.list:
        _list_groups()
        return 0

    groups_to_run = args.group or list(SCENARIO_GROUPS.keys())

    all_results: list[ScenarioResult] = []
    for group_key in groups_to_run:
        all_results.extend(_run_group(group_key))

    failures = [r for r in all_results if r.status == "fail"]
    skipped = [r for r in all_results if r.status == "skip"]
    passed = [r for r in all_results if r.status == "pass"]

    print("\n=== Summary ===")
    print(f"Passed: {len(passed)}")
    print(f"Failed: {len(failures)}")
    print(f"Skipped: {len(skipped)}")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
