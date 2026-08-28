---
name: beads-redirect-convergence
description: >-
  Safely inventory and plan repository-local Beads redirect convergence; real
  apply and recovery are one-repository, externally signed, and separately
  authorized.
---

# Beads redirect convergence

Use this skill when an operator needs to discover, inventory, plan, certify, or
explicitly authorize a redirect-only convergence operation for a repository's
own canonical Beads store. The portable engine is shared; data authority is
not. Each application repository keeps its own canonical database and JSONL
export, while a host registry only describes where those stores and their
evidence live.

This skill is an operator contract, not an authorization. Read it before every
operation and keep the registry, manifest, plan, approval, and receipt for the
same repository and run. Machine-readable results are emitted on stdout;
diagnostics belong on stderr. A nonzero exit is a failed operation, even when a
JSON receipt contains partial results.

## Safe operating posture

- Start read-only. Validate the registry, inventory one repository, and plan
  one repository before considering any mutation.
- `plan-all` is read-only and is structurally incapable of applying. There is
  no `apply-all` command, cross-repository apply, automatic recovery, or
  wildcard repository target.
- The portable engine owns schemas, validation, descriptor-bound execution,
  planning, journaling, and transaction invariants. The application repository
  owns its canonical Beads authority, exporter, health policy, and evidence
  interpretation. A registry entry never transfers or merges that authority.
- The only application-repository mutation permitted by the transaction is the
  regular `.beads/redirect` basename. Database, WAL, SHM, JSONL, tracker
  journals, and Git state are never mutation targets.
- Do not execute a command assembled from hashes or paths printed by a prior
  command. Hash output is review evidence only; the human-facing operator must
  independently supply every literal binding to an authorized operation.

The initial adapter is exactly `br-sqlite-v1`. Legacy `bd`, Dolt, mixed, or
unknown backends are unsupported and fail closed. A real repository without a
version-specific writer-exclusion capability is plan-only, even if its health
is clean.

## Public read-only CLI

Use the installed `beads-converge` executable supplied by the package. The
following are copy-paste templates: replace angle-bracket placeholders with
values obtained and independently checked by the operator. Registry paths and
all artifact paths must be absolute; registry data itself does not expand
environment variables, `~`, shell syntax, or command substitution.

Set review inputs in the shell only for the read-only commands:

```bash
REGISTRY="/absolute/path/to/registry.json"
REGISTRY_SHA256="<64-lowercase-hex-registry-sha256>"
REPO_ID="<one-registry-repo-id>"
```

Validate the captured registry before using it:

```bash
beads-converge registry validate \
  --registry "$REGISTRY" \
  --expected-registry-sha256 "$REGISTRY_SHA256"
```

Produce a bounded inventory for exactly one repository. Inventory performs
Git worktree discovery through the pinned descriptor and inspects only the
declared roots, worktrees, `.beads` directory, redirect basename, and adapter
source family. It does not sync, import, export, repair, or mutate a tracker:

```bash
beads-converge inventory \
  --repo "$REPO_ID" \
  --registry "$REGISTRY" \
  --expected-registry-sha256 "$REGISTRY_SHA256"
```

Build a deterministic one-repository plan. A plan may write hash-bound
evidence below the registry-selected evidence root, but it must not write a
repository source or redirect:

```bash
beads-converge plan \
  --repo "$REPO_ID" \
  --registry "$REGISTRY" \
  --expected-registry-sha256 "$REGISTRY_SHA256"
```

Plan every registry entry independently. This remains read-only: each result
has its own repository identity and plan hash, and one failure does not hide
healthy results. The command exits nonzero if any entry cannot be safely
planned, and it has no `--apply` option:

```bash
beads-converge plan-all \
  --registry "$REGISTRY" \
  --expected-registry-sha256 "$REGISTRY_SHA256"
```

Do not infer readiness from a successful registry validation alone. Before
certification, inspect the JSON inventory/plan and verify that the intended
repository is present, the canonical target is physical, every source family
is stable, and the adapter reports supported SQLite-v1, healthy canonical
state, and its redirect codec/oracle attestation.

## Binding and authority model

The registry is configuration, not permission. A manifest records bounded
topology, physical identities, redirect pre-state, source fingerprints, exact
binary bindings, and the registry SHA. A plan is deterministic and bound to
that manifest. Apply recomputes the plan from a fresh descriptor-bound
manifest; a mutable plan file or a copied hash is not an input substitute.

Every future apply or recovery must independently bind all of the following
literal operator arguments to the fresh operation:

- Repository: exactly one `repo_id`; never a list or wildcard.
- Registry: captured bytes and `--expected-registry-sha256`.
- Manifest and plan: apply requires `--manifest`,
  `--expected-manifest-sha256`, and `--expected-plan-sha256`.
- Canonical authority: `--expected-canonical`, plus physical path and
  device/inode identity.
- Adapter: `--expected-adapter br-sqlite-v1`, codec, and oracle receipt.
- Tracker path: `--expected-tracker-path`.
- Tracker version: `--expected-tracker-version`.
- Tracker digest: `--expected-tracker-sha256`.
- Git path: `--expected-git-path`.
- Git version: `--expected-git-version`.
- Git digest: `--expected-git-sha256`.
- Approval: `--approval` envelope and `--approval-signature` paths.
- Mode: literal `--apply` for apply, or literal `--recover` for recovery.

An approval envelope is canonical JSON and is externally signed. It binds the
operation, one repository, registry/manifest/plan digests, canonical path,
adapter, tracker and Git bindings, tool-tree hash, target redirect identities,
signer principal and fingerprint, issue/expiry times, and a single-use nonce.
The process cannot mint an approval, and values found in an artifact never
satisfy a separately required operator argument.

The approval must be separately signed for this exact operation; a signature
copied from another run or artifact is not authorization.

The apply operation is intentionally not shown as a runnable command here.
There must be no reusable example containing a real approval, signature, plan
hash, registry hash, or repository path. An authorized operator supplies every
binding afresh after reviewing the plan; the CLI never prints a command that
could be pasted to apply it.

## One-repository apply boundary (not certification)

Real apply is allowed only after all of these independent gates pass:

1. A fresh read-only inventory and deterministic plan identify exactly one
   repository and no skipped, missing, unsupported, or newly discovered entry.
2. The operator independently supplies every binding in the table above,
   including the fresh registry, manifest, recomputed plan, canonical target,
   adapter, tracker, and Git values.
3. A separately administered signer issues a new, unexpired, single-use,
   detached SSH approval for this exact operation. A prior receipt, registry,
   manifest, plan, or user instruction from another run cannot authorize it.
4. The host passes the required descriptor-execution, `O_NOFOLLOW`, directory
   fsync, and lock capability checks. The adapter proves a retained,
   non-mutating writer-exclusion lease for this exact pinned tracker version.
   Without that proof, the operation remains unavailable on real stores.
5. Before the first redirect write, the engine re-discovers the selected repo,
   revalidates health and source fingerprints, reserves the nonce, acquires
   the canonical physical-identity lock, and durably journals every prior
   redirect state. Any mismatch fails before mutation.

The transaction changes only redirect basenames, writes through retained
directory descriptors, verifies one-hop resolution after each write, and
records `COMMITTED` before producing a receipt. Ordinary failure must prove a
full reverse rollback or leave a durable `NEEDS_OPERATOR` journal. There is no
automatic rollback claim based only on process output.

## One-repository recovery boundary

Recovery is a separate operation, not an automatic continuation of apply. It
names exactly one repository and one run. Recovery requires `--manifest`,
`--expected-manifest-sha256`, and `--expected-plan-sha256`, plus a new signed
recovery approval with `--expected-registry-sha256`, `--run-id`, and
`--expected-journal-sha256`, plus canonical path, adapter, and tracker/Git
bindings, and literal `--recover`. The recovery binding includes the run ID and
journal SHA. It can restore only the recorded
redirect bytes or the recorded absence when the current state is either the
journaled pre-state or this run's intended target.

Recovery repeats bounded discovery, backend and health attestation, source
fingerprinting, and the proven writer-exclusion lease before any mutation. A
third redirect state, topology drift, changed source, unhealthy canonical
store, changed binary, unsafe control root, lock conflict, invalid approval,
or any other mismatch becomes durable `NEEDS_OPERATOR`; recovery does not
overwrite it. Recovery progress is journaled per target and may resume
idempotently after another process death. A committed run without a receipt is
successful and may have its receipt regenerated; it is never rolled back.

## Fixed roots and signer custody

The approval trust root is compiled into the engine and cannot be selected by a
registry, CLI argument, environment variable, or symlink:

- macOS: `/Library/Application Support/Beads Convergence/trust`
- Linux: `/etc/beads-convergence/trust`

The engine checks the root and every ancestor for root ownership and safe
permissions before invoking the fixed `ssh-keygen -Y verify` namespace
`beads-redirect-convergence-v1@jleechan.org`. The allowed-signers file and
verifier binding are part of that root-owned installation.

Locks, active journals, and the nonce ledger use one fixed control namespace
derived from the effective user's passwd home, never from `HOME` or a
registry field:

```text
<getpwuid(geteuid()).pw_dir>/.local/state/beads-convergence/control
```

The control root and ancestors must be non-symlink directories owned by the
effective user with mode `0700`; control artifacts are `0600`. A changed or
unsafe control namespace is a hard failure. Evidence (manifests, plans,
backups, and receipts) stays in the registry-selected evidence root, outside
the worktree, canonical `.beads`, and control namespace.

Signer custody is an operational security boundary. The allowed private key
must be hardware-held, off-host, or controlled by a separately administered
principal, and it must never be installed in the applying account, its
process, its filesystem, environment, or SSH agent. The CLI verifies a
root-owned trust tree, signature, principal, fingerprint, and nonce; it does
not and cannot prove private-key custody. A user-writable custody file,
checkbox, registry value, or receipt is not evidence of custody. Independent
certification owns that gate, and installing trust or issuing a real approval
does not happen as part of routine planning.

## Authority classes

Keep these classes separate in reports and approvals:

- Fixture apply: disposable fixture mutation and rollback; fixture-only
  authority, never production.
- Real dry-run: validation, inventory, plan, and `plan-all`; read-only with no
  approval or mutation.
- Trust-root provisioning: root-owned trust/verifier installation; a separate
  host operation.
- Offline approval issuance: signing one exact envelope; separate signer
  custody and human approval.
- Real apply/recovery: one-repository transaction or recovery; new
  authorization and proven capabilities.

Passing fixture apply or real dry-run proves implementation readiness only. It
does not authorize a real repository mutation. Production has no test-authority
flag, custody-evidence switch, approval bypass, automatic recovery, or
environment override.

## Real read-only certification

Certification of real repositories is dry-run only. For each separately
authoritative repository:

1. Run registry validation, inventory, and plan with a fresh captured registry.
2. Repeat inventory/plan and compare deterministic manifest/plan digests,
   classifications, physical identities, source hashes, redirect bytes/modes,
   adapter oracle receipt, and health receipt.
3. Confirm DB, WAL, SHM, JSONL, redirect, and tracker state are unchanged.
4. Run `plan-all` only as an aggregate read-only check; retain each per-repo
   result and its nonzero status if any repository is unsupported or unhealthy.

Real certification must report unavailable capabilities explicitly. In
particular, clean health, two unleased hash passes, a status command, or an
`lsof` snapshot is not writer exclusion and cannot promote a real plan to
real apply. Certification never installs trust, issues an approval, or runs
`--apply`/`--recover`.

## Fail-closed conditions

The engine must fail before mutation on malformed or unknown schemas, missing
operator bindings, stale or replayed approvals, signature/namespace/principal
mismatch, unsafe trust/control roots, binary version or digest mismatch,
unknown adapters, unsupported or mixed backends, unhealthy canonical state,
symlink/nonregular source or redirect files, path escape, duplicate physical
canonical authority, topology or source drift, missing worktrees, lock
contention, unfinished journals, unknown redirect codec, absent writer lease,
malformed adapter output, or any nonzero descriptor-bound Git/`br`/verifier
status.

An unsuccessful `plan-all` still reports healthy repository results but exits
nonzero. An apply/recovery failure either proves complete rollback or leaves a
durable `NEEDS_OPERATOR` journal and a nonzero exit. Do not retry by changing
paths, hashes, trust roots, environment variables, or artifact contents; make
a fresh read-only plan and obtain new authorization when the operator-directed
resolution requires another attempt.

## Operator checklist

Before calling the work complete, record:

- the exact registry path and captured SHA (without treating it as permission);
- selected `repo_id`, manifest and plan digests, and all independent binary
  bindings;
- read-only evidence paths and unchanged source/redirect hashes;
- adapter health, backend, redirect-oracle, and writer-lease capability;
- trust-root/control-root checks and the independent custody certification;
- whether the result is fixture apply, real dry-run, trust provisioning,
  offline approval issuance, or real apply/recovery;
- explicit `applied` or `recovered` status from the receipt, or the exact
  fail-closed reason and durable journal state.

Never describe a plan as applied, a fixture as real, a signature as custody
proof, or a registry as authority. Real apply or recovery requires a new explicit
operator instruction against a fresh manifest and proven capabilities.
