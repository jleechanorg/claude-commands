# Task 5 report — journaled redirect transactions

## Delivered

- Added `approval.py` with a fixed SSH namespace, compiled macOS/Linux trust
  roots, root-owned trust-tree checks, exact canonical envelope stdin, and
  binding checks for the operation, artifact digests, canonical authority,
  adapter, binaries, signer principal, and signer fingerprint.
- Added `transaction.py` with explicit `--apply`, canonical `(st_dev, st_ino)`
  control locks, one-use nonce reservation, durable JSON journals, durable
  receipts, redirect-only same-directory rename operations, reverse rollback,
  idempotent recovery, and `NEEDS_OPERATOR` preservation when bytes are no
  longer the journal's recorded pre-state or intended state.
- Added the approval/journal/receipt v1 JSON schemas and made
  `ApprovalEnvelope.signer_fingerprint` mandatory.  The receipt binds the same
  principal and fingerprint.
- Added fixture-only transaction and crash-recovery tests.  They create
  disposable SQLite-shaped stores; no test invokes `br apply`, recovery, or a
  real Beads store.

## Evidence

TDD RED was captured before implementation: both Task 5 test modules failed to
import because `approval.py` and `transaction.py` did not exist.  The final
repeatability command ran three consecutive green iterations:

```bash
python3 -m unittest -v \
  tests.test_beads_convergence_codec.CodecTest.test_approval_envelope_binds_signer_fingerprint \
  tests.test_beads_convergence_transaction \
  tests.test_beads_convergence_crash_recovery
```

Each iteration reported 10 passing tests.  `python3 -m py_compile` passed for
both new modules, and all three new schemas parse with `python3 -m json.tool`.

## Deliberate availability boundary

`BrSqliteV1Adapter.acquire_writer_exclusion()` is currently plan-only and does
not prove a writer-exclusion lease.  Therefore `apply_plan` and `recover_run`
accept only explicitly fixture-only control stores/adapters and reject a real
Beads mutation before any write.  The SSH verifier and fixed trust-root checks
are present for the future production adapter, but signing-key custody remains
an out-of-band provisioning fact (hardware-held, off-host, or separately
administered); a verifier-readable checkbox would not prove custody.

The shared-model addition was authorized after discovering the interface gap:
the previous frozen `ApprovalEnvelope` carried a principal but no fingerprint,
despite Task 5 requiring both in the signed envelope and receipt.
