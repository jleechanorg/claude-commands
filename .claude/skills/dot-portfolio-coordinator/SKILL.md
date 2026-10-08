---
name: dot-portfolio-coordinator
description: Collect declared GitHub and Beads portfolio sources, observe within a bounded run window, and dispatch explicitly authorized pilot events through a receipt-safe sender. Budget, control-journal and publication helpers are not wired into the controller.
---

# Dot Portfolio Coordinator

The controller collects declared GitHub and Beads sources and supports bounded observation. Explicit pilot mode invokes the driver and sender using pinned configuration and grants. It does not maintain roadmap goals, execute budget reservations, mutate the control journal, or publish roadmap dashboards.

Sections 4–7 below describe dormant library components, not capabilities exercised by the controller. `reserve`, `settle`, and `status` return `capability_blocked`; notification resolution is read-only and does not establish authority.

## Architectural Boundaries & Core Invariants

1. **Strict Registry & Host Binding**:
   - Sources are explicitly declared in `references/sources.json`.
   - Identified by composite key `(github_host, owner/repository, source_namespace, bead_id)`.
   - Unregistered repositories discovered during organization scans are flagged as coverage gaps; access is never silently expanded.
2. **Deterministic Collection & Stale Resilience**:
   - Beads stores collected via native `br list --status all --json --limit 0`.
   - GitHub inventories collected with full pagination (including draft PRs, head SHAs, and check statuses).
   - Version-bound cursors committed only upon complete final-page collection.
   - Collection preserves facts authorized for its destination (internal observation or active model packets); packet assembly filters again. A destination change forces a fresh fetch instead of reusing another audience's 304 snapshot. Private task/version bindings remain separate from model facts.
   - Partial or failed collections preserve last-known items as stale/partial rather than erasing unseen work.
3. **Model Admission & Schema-Bound Decision**:
   - Active model execution consults the internally resolved decision-driver admission profile. The supported profile requires a native Claude executable, existing first-party subscription authentication, and the required CLI no-tool flags: empty tools and MCP configuration, restricted/safe mode, disabled slash commands, browser integration and session persistence, and denied permission prompts. Prompts go through stdin in a separate private temporary directory. Provider-routing and tool-injection environment variables are excluded. This is a CLI capability restriction, not an OS sandbox; installed executable and managed policy remain trusted. AGY and Codex are capability-blocked with no fallback. Select `--driver claude` explicitly; the legacy AGY default will fail closed.
   - Driver decisions use `outcome` as the sole dispatch discriminator: `send_proposal`, `no_eligible_task`, or `cycle_complete`. A redundant model `action` field is rejected.
   - Proposals must adhere strictly to the coordination dialogue packet schema, validating candidate bindings, task keys, and grant bindings without claiming sandbox isolation.
4. **Deterministic Structural Proposal Validation (dormant library)**:
   - Validates that every proposed item references a genuine snapshot task key with matching citations and source versions.
   - Rejects invented entities, endpoints, or injected shell commands.
   - Generates deterministic, stable action IDs (`act_<hash>`) for restart idempotence.
5. **Real Beads Control Journal & CAS Protocol (dormant library)**:
   - Designated host sole-writer lock (`fcntl.flock`).
   - Journal reads and writes require one registered `authoritative_control` roadmap binding, the exact store database, explicit `--db`, and matching `br where` resolution.
   - Domain repository task stores are strictly read-only; mutations are permitted ONLY on roadmap control records (`coordinator-control`).
   - Optimistic concurrency control via `--if-unchanged <updated_at>` and `--append-notes`.
   - Compares observed full-record digest immediately before write and rereads post-write state.
6. **Original Authority & Cumulative Budget Ledger (dormant library)**:
   - Binds authenticated human principals to original GitHub comments via immutable comment IDs, versions, and content digests.
   - Unsupported channels (Slack, native conversation) return `capability_blocked`.
   - No keyword consent classifiers: words like "I approve" or "routine" do not bypass principal binding.
   - Reserve and settlement amounts must be finite, nonnegative JSON numbers; malformed values are rejected before ledger mutation.
   - Cumulative budget ledger tracks allocations, idempotently handles repeat reservations, settles verified spend, and blocks overruns.
7. **Audience-Filtered Roadmap Publication (dormant library)**:
   - Renders only two allowlisted derived projections: `coordinator/WORK.md` and `coordinator/COVERAGE.json`.
   - Native `.beads/issues.jsonl`, raw control notes, and private principal IDs are excluded.
   - Publishes via an isolated checkout on dedicated branch `coordinator/portfolio-snapshot` and owned draft PRs.
   - Fast-forward pushes only (never force-pushes, never pushes directly to main).
   - Remote readback verifies file contents at the pushed SHA.
   - Closed-unmerged PRs trigger a publication hold until owner resolution.
8. **Receipt-Safe Sender Subcomponent**:
   - Reuses relative sibling dot transport (`../../dot/scripts/dot.sh`).
   - Quiet exit 0 on empty input.
   - Identical notification registrations are idempotent; changed immutable bindings are refused. Public item IDs obey the destination field policy.
   - Persists pending immutable authorization binding and uncertainty hold before transport invocation.
   - Two-phase interactive prepare/commit/abort protocol: waits for prepared transport context before final source and grant revalidation immediately prior to commit.
   - Requires standalone `DOT_SENT_VERIFIED` and exit 0 for verified delivery.
   - Uncertainty holds block subsequent sends until deliberate operator ledger recovery; `--reconcile-receipt` is unsupported/unavailable.
   - Emits exactly one machine-readable `COORDINATOR_RESULT` JSON line.

## CLI Usage

The controller CLI is located at `scripts/coordinator-portfolio.py`:

```bash
# Resolve notification authorization reference
python3 scripts/coordinator-portfolio.py resolve-notification --ref bd-ctrl-1/act-1/att-1

# Generic observe-only loop (no messages; 12-hour default)
run_dir="$(mktemp -d /tmp/dot-portfolio-observe.XXXXXX)"
python3 scripts/coordinator-portfolio.py observe --duration 43200 --interval 300 --run-dir "$run_dir"
```

Active messaging requires a pinned pilot config, account grants, and an explicitly supplied approved private source registry. The registry must name concrete repositories and provide an exact `host_binding` for every Beads source; the shipped portable `references/sources.json` is a template, not an active registry. Set `run_dir` to the config's `state_dir`, an owner-owned private directory under `/tmp` (mode `0700`). Use a separate directory from an observe-only run; the controller creates it privately if missing.

```bash
# Active current-work check-ins, bounded by the pilot config and grants
run_dir=/tmp/dot-portfolio-pilot
python3 scripts/coordinator-portfolio.py observe --sources /path/to/private-approved-sources.json --interval 300 --driver claude --send-messages --pilot-config /path/to/pilot.json --run-dir "$run_dir"
```

The sender subcomponent is located at `scripts/dot-portfolio-coordinator-sender.sh`:

```bash
# Read-only status query
./scripts/dot-portfolio-coordinator-sender.sh --status --json --account default

# Deliver material event with validated operator grant file and sha256
# (Note: --authorization-ref is inert/unsupported and not used for grant enforcement; --reconcile-receipt is unavailable)
COORDINATOR_CHANGE_ID="ev-001" COORDINATOR_CHANGE_SUMMARY="Update" ./scripts/dot-portfolio-coordinator-sender.sh --account default --state-dir /path/to/state --grant-file /path/to/grant.json --grant-sha256 <sha256> message.txt
```

## Private driver failure diagnostics

Handled nonzero exits, rejected envelopes or decisions, process timeouts, and
exceptions from process execution attempt to write a unique
`.driver-diagnostic-*.json` receipt in the existing driver workspace, separate
from the deleted prompt directory.
Receipts are mode `0600`, at most 2048 UTF-8 bytes each, and contain the driver,
legacy failure reason, distinct failure stage, exit code, and stdout/stderr
`decoded_utf8_bytes`: the UTF-8 re-encoded size of decoded text after subprocess
universal-newline normalization (CRLF and CR become LF), not raw pipe bytes.
All nonempty output text is replaced with `[REDACTED]`: credentials,
private communications, and echoed prompts cannot be reliably removed with
pattern filters. No packet identifiers, prompts, environment, argv, exception
text, output hashes, or raw excerpts are retained. Empty streams remain empty;
timeouts and execution exceptions have null exit/output fields because the process helper does not return
them. Receipts do not diagnose the underlying provider failure.

Receipt writes are best effort; inability to write does not change the failure
result or authorize a send. Preflight failures do not create attempt receipts.
Inherited exceptions outside the handled paths can still escape without a
receipt: deeply nested valid JSON can raise `RecursionError` during envelope
parsing. This change does not harden parsing or make every failure diagnosable.
The containing private run directory owns retention; this adds no global log,
publication, automatic cleanup, or total-run quota. The size bound applies to
the persisted receipt, not the existing subprocess capture buffer.

Retrieve receipts manually at
`<configured state_dir>/driver-<event_id>/.driver-diagnostic-*.json`.
Normal coordinator event IDs bind `run_id` and slot index; the coordinator lock
serializes attempts. No production consumer currently reads these receipts or
returns their paths, so diagnostics are not surfaced automatically. A unique
filename distinguishes each saved occurrence, but repeated standalone adapter
calls sharing a workspace have no explicit attempt ID, timestamp, or returned
receipt path for correlation.

## Execution binding and operation limits

Active startup binds the coordinator source manifest, source registry, pilot configuration, selected driver profile and native executable path/hash, selected transport path/hash, sibling `dot_chrome.mjs` path/hash, and the native Node interpreter selected by the transport before loading run state. The selected Node path is explicitly passed to the sender. Missing dependencies fail closed. Restart with different bindings is refused; unchanged restart retains the original deadline. Checks repeat every cycle, before the decision call, after decision and immediately before transport startup, and before/after the final source revalidation immediately before sender commit. The adapter independently re-admits and compares its profile before launching. Observe-only mode does not invoke model admission.

These checks cover the named application dependencies, not an immutable OS or a complete transitive Chrome/Playwright supply-chain snapshot. Same-user mutation between a check and execution remains outside the guarantee. No claim of production readiness follows from offline profile tests alone.

## Exceptional single delivery

`coordinator-delivery-exception.py` requires a separately approved, pinned private manifest for one fresh event and message. It preserves the existing sender ledger byte-for-byte, copies a read-only historical backup, holds the existing sender lock and durably consumes one claim before transport. It requires a fresh typed identity probe and exact finite one-message grant. An uncertain result remains consumed. It is an exceptional operator operation, not a recurring scheduler or automatic hold reconciliation.

Ongoing scheduling is separate from the finite pilot. Never renew an expired pilot, reuse a consumed delivery exception, or remove an uncertainty hold merely to resume messaging. Cross-host scheduling requires shared hold coordination in addition to local deduplication; local file locks do not coordinate two machines.

## Recurring operation (separate authority from the expired pilot)

`scripts/coordinator-recurring.py` provides a shared admission broker and a finite
host worker. It never installs or starts itself. A separately approved, private,
SHA-pinned schedule grants ongoing recurrence; it does not extend any old grant
or reset an old sender ledger. The operator must explicitly select the admitted
driver; there is no automatic replacement of AGY with Claude.

The designated Linux hostname owns one private durable shared state directory.
Mac accesses its broker using an existing SSH alias and authentication. Both
entry paths enforce the Linux hostname and platform. There is no local fallback
if SSH, source pins, configuration pins or shared state are unavailable.

Each account has its own pending claim and per-host UTC slot watermark. One
atomic claim wins concurrent admission; claim expiry, restart and the next hour
never clear it. Unknown, orphaned or uncertain operations remain held across both
hosts. Verified delivery and proven no-send outcomes finish the claim, but never
permit another attempt in the same slot. A completion written before a settlement
crash remains preserved and held for deliberate recovery. There is no automatic
reconciliation command. Caller tokens correlate claims; existing trusted local
operator/SSH authority is the trust boundary, not cryptographic human approval.

Enrollment reads the three pinned historical ledgers without modifying them,
copies their exact bytes into mode-0400 `historical/<account>.json` snapshots,
verifies the copies, and commits private state. Original-file changes, while the
original exists, block that account. Loss of an old temporary path does not erase
its snapshotted uncertainty hold. A held account does not block other accounts.
Never delete `enrolled.json`, `ledger.json`, historical snapshots or pending claims
to repair a failure; initialization refuses an already enrolled directory.

Mac batches start at :00 UTC and Linux at :30 UTC. Account positions 0, 1 and 2
run at offsets 0, 20 and 40 minutes within each batch, so each account has one slot
per hour per host and Linux is 30 minutes later than Mac. Linux position 2 is at
:10 of the following hour. Wakes more than 120 seconds late skip the slot, with no
catch-up burst. Grants are immutable, expire 20 minutes after the account's due
time, allow one message, and retain the sender's 3600-second interval field.
Cross-grant cadence is enforced by shared UTC slot watermarks, not a claim of a
rolling one-hour limit across both hosts. A batch has a monotonic one-hour wait
limit and a 3600-second outer process bound; systemd adds a 3720-second bound.

Before model execution, the worker checks its hostname/platform, pinned source,
registry, dot configuration, driver and transport dependencies, and a fresh typed
browser probe (matching identity, HTTP 200, available composer and resolved
cleanup). Failed preflight is known no-send; ambiguous execution remains held.
The existing short current-work prompt, audience filtering, source/grant checks
and prepared sender protocol are reused. Shared claim and execution checks repeat
before the model, before transport and in the final source callback. No draft
clearing, credential copying, login automation, account rotation or old service
restart is performed.

The shared root's `STOP` blocks all new operations; `STOP-<account>` blocks one
account across hosts. Each host's private state root also supports `STOP`.
Dangling stop-marker symlinks still stop work. Stops do not erase existing claims
or receipts. Each host retains `<state_dir>/<event_id>/grant.json`, sender state,
result and sanitized session probe; bounded driver diagnostics are copied there
before temporary workspace cleanup. Shared `receipts/<event_id>.json` records
admission/completion. Receipts contain no message text or raw model output and
have no automatic retention deletion.

Machine-local schedule fields (never commit actual values):

- `schema_version: 1`, unique `schedule_id`, short approved `authority`, and
  `source_digest` computed from the frozen installed coordinator tree.
- `shared_state_dir`: existing, private, durable Linux directory, initially empty.
- Exactly three `accounts`, each with `account`, `historical_ledger` and its
  `historical_sha256`.
- `hosts.mac` and `hosts.linux`: `hostname`, private durable `state_dir`, approved
  `driver`, `sources`, `dot_config_file`, `transport_script`, `execution_sha256`.
- `authority_endpoint`: existing `ssh_host` alias, absolute Linux `python`,
  `script` and final private `schedule` path.

Prepare the common schedule privately, obtain each host's execution digest using
`inspect` against its draft schedule hash, then pin the final identical bytes on
both hosts. This is an operator enrollment step; source/configuration changes
require a reviewed migration that preserves existing state, not reinitialization.

```bash
python3 scripts/coordinator-recurring.py --schedule /private/schedule.json --sha256 <pin> --role linux inspect
python3 scripts/coordinator-recurring.py --schedule /private/schedule.json --sha256 <pin> initialize
python3 scripts/coordinator-recurring.py --schedule /private/schedule.json --sha256 <pin> --role linux render
```

`initialize` is only for first enrollment on the designated Linux host. `render`
prints definitions without installing them: Mac label `ai.dot-portfolio-hourly-v1`
and Linux `dot-portfolio-hourly-v1.service` / `.timer`. Generate on each target
host; the Mac calendar minute accounts for that host's current UTC offset. A
change to its minute offset requires regeneration; the UTC gate otherwise skips
misphased wakes. Definitions have no immediate RunAtLoad, KeepAlive, catch-up or
random delay. Keep them disabled until review, installation, source/authentication
and shared-hold gates are verified. Existing pilot and legacy units are separate
and must remain stopped.
