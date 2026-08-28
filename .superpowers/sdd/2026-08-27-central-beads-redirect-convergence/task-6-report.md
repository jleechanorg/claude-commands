# Task 6 report — fail-closed convergence CLI

## Delivered

- Added `scripts/beads_convergence/cli.py` with the public `main(argv)` entry
  point and only the `registry validate`, `inventory`, `plan`, `plan-all`,
  one-repository `apply`, and one-repository `recover` commands.
- Added the executable `scripts/beads-converge` as a thin import-only entry
  point.
- Required captured registry/artifact hashes, repository, canonical, adapter,
  tracker, Git, approval, and signature bindings for mutation-shaped commands.
  Apply and recovery require literal `--apply` and `--recover` respectively.
- Kept `plan-all` structurally read-only with no mutation flag or multi-repo
  apply path.  Errors emit one strict JSON object on stdout and a concise
  diagnostic on stderr with stable usage (`2`) and operational (`1`) exits.
- Added parser, binding, output, unknown-command, and fail-closed approval path
  tests in `tests/test_beads_convergence_cli.py`.

## Evidence

```text
python3 -m unittest -v tests.test_beads_convergence_cli
8 tests passed

python3 -m py_compile scripts/beads-converge scripts/beads_convergence/*.py \
  tests/test_beads_convergence_*.py
passed

ruff check scripts/beads_convergence/cli.py \
  tests/test_beads_convergence_cli.py scripts/beads-converge
passed

git diff --check
passed
```

The adjacent convergence discovery/codec/inventory/planner suites pass.  The
existing transaction and crash-recovery tests currently fail during fixture
construction because the shared Task 5 model/API changes require additional
approval-envelope fields; those files are outside this task's ownership and
were not modified here.

## Availability boundary

The CLI delegates apply/recovery to Task 5, whose production boundary rejects
the non-fixture control store and adapter until writer exclusion is proven.
The CLI does not expose a test-authority, approval-bypass, trust-root, or
environment override.  Recovery's full transaction authorization remains
owned by the Task 5 API; this CLI requires and checks its operator-shaped
arguments before delegating.
