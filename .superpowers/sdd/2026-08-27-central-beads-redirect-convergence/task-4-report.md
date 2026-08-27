# Task 4 report: deterministic planning and read-only `plan-all`

## Outcome

Task 4 is complete. The convergence package now builds deterministic,
manifest-bound plans and exposes a structurally read-only `plan_all` function
that keeps per-repository outcomes independent while returning nonzero status
when any repository fails.

## Scope record

- **GOAL:** Build canonical one-repository plans and an independent aggregate
  planning receipt without introducing an apply path.
- **MODIFICATION:** Added `scripts/beads_convergence/planner.py` and focused
  planner tests. Added the required Task 4 report.
- **NECESSITY:** Apply must be able to recompute a stable plan from a bound
  manifest, while dry-run planning must not mutate repository state or let one
  repository failure hide another repository's result.
- **INTEGRATION PROOF:** Planner tests cover deterministic hashes, stable
  ordering, source/redirect/physical-identity binding, eligibility filtering,
  no `apply` parameter, read-only empty-registry planning, and independent
  aggregate failure status.

## Implemented contract

`build_plan(manifest)` returns a frozen `DeterministicPlan`, a `Plan` subtype
whose `sha256` is computed from canonical JSON of the plan fields only. The
manifest digest is computed from the canonical manifest representation. Actions
include the resolved worktree path, directory device/inode, every known source
fingerprint, and the complete redirect pre-state/intended state. Actions are
sorted by resolved worktree path and volatile metadata is not introduced into
the hashed representation.

Only complete `noncanonical` records with the required SQLite source family,
known source names, valid physical identities, and a codec/intended redirect
attestation become actions. Canonical, redirected-canonical, unresolved,
missing, unsupported, newly appeared, and otherwise incomplete entries are
excluded from the executable plan.

`plan_all(registry)` has no `apply` parameter and only validates/inventories
through the read-only repository pipeline before calling `build_plan`. Each
repository is processed independently. Successful plans remain in the receipt
when another repository raises; the receipt status is `0` only when every
repository succeeds, otherwise `1`.

## Verification

Commands run from the repository root:

```text
python3 -m unittest -v tests.test_beads_convergence_planner
# 6 tests, OK

python3 -m unittest -v tests.test_beads_convergence_codec \
  tests.test_beads_convergence_registry \
  tests.test_beads_convergence_adapters \
  tests.test_beads_convergence_planner
# 30 tests, OK

python3 -m py_compile scripts/beads_convergence/planner.py \
  tests/test_beads_convergence_planner.py
# OK

awk 'length($0)>88 {print FNR ":" length($0)}' \
  scripts/beads_convergence/planner.py \
  tests/test_beads_convergence_planner.py
# no output

git diff --check
# clean
```

## Files changed

- `scripts/beads_convergence/planner.py`
- `tests/test_beads_convergence_planner.py`
- `.superpowers/sdd/2026-08-27-central-beads-redirect-convergence/task-4-report.md`

## Residual risk / handoff notes

- `plan_all` delegates manifest generation to Task 3's `inventory.build_manifest`
  and uses Task 2's repository validation and adapter boundary when those
  modules are present.
- Task 4 does not add a CLI, mutable plan-file parser, apply implementation, or
  transaction logic; later apply code must recompute from its bound manifest
  and compare the expected plan digest.
- The pre-existing untracked `tests/test_beads_convergence_inventory.py` and
  `docs/superpowers/` tree were preserved and not staged.

## Review fix round 1

The first review identified that the initial aggregate test mocked the
per-repository planner, that redirect pre-state combinations were not
validated, and that source/physical bindings were too permissive. The planner
now rejects present redirects without both bytes and mode, absent redirects
with either value, duplicate source physical identities, unknown source names,
invalid source digests, and relative worktree paths before emitting actions.

The planner test now exercises a real non-empty `plan_all` call through the
Task 3 inventory module without mocking `_plan_repository`. It uses actual
temporary registry/worktree fixtures and only patches platform-bound binary
execution and Git discovery seams. The same test covers a healthy action-bearing
repository alongside an unhealthy hot-journal repository, and verifies their
plans remain separate with distinct hashes. Additional assertions cover
redirect and directory identity hash binding plus newly appeared and vanished
classification filtering.

Review-fix verification:

```text
python3 -m unittest -v tests.test_beads_convergence_planner
# 8 tests, OK

python3 -m py_compile scripts/beads_convergence/planner.py \
  tests/test_beads_convergence_planner.py
# OK

awk 'length($0)>88 {print FNR ":" length($0)}' \
  scripts/beads_convergence/planner.py \
  tests/test_beads_convergence_planner.py
# no output

git diff --check
# clean
```
