# ezgha Fleet Failure Classes — Verified 2026-07-11

When the sweep sees `ezgha` CRITICAL alerts in `#mcp-mail` (`C0A0AG6EELB`), the `fail_class` field in the webhook payload tells you which fix layer to dispatch an AO worker to. Don't treat all INV-1 violations as the same bug — the same fleet has manifested two distinct failure classes on different days.

## Observed failure classes

### Class A — `missing-registration`

- **Symptom**: `busy=X/22 registered=Y queued=Z` where `registered < 22` (expected fleet size). Specific runner names like `ez-runner-c-3` or `ez-mac-runner-b-3` are listed as `missing expected runners`.
- **Cause**: Runner pool self-registration broken on a subset of nodes. Runners either never registered or fell off the registry.
- **Fix layer**: runner-pool registration / cloud-init sidecar / VM lifecycle. NOT a scheduler bug.
- **First seen in sweep**: 2026-07-09 09:24 PT in prior brief.

### Class B — `genuinely-idle` (verified 2026-07-11)

- **Symptom**: `busy=0/22 registered=22 queued=2`. All 22 runners are registered and "online" but `busy=false` for all of them. Queued jobs sit unpicked (`oldest_queued=208m` against 20m threshold).
- **Cause**: Scheduling/claim layer bug — runners are healthy but the claim pathway isn't routing work to them. Sometimes called "queue starvation" in the same webhook payload (`INV-2 duration violated`).
- **Fix layer**: scheduler/claim-layer code path. NOT a runner-count problem.
- **Critical distinction**: backend restart attempts (e.g. 2026-07-10 18:40 PT) DO NOT fix this because the runners themselves are fine. Restarting the backend reloads the scheduler config; if the bug is in the claim handler itself, a restart with the same code does nothing.
- **First seen in sweep**: 2026-07-11 12:00 PT.

### Class C — `runner-offline` (subset of A)

- A specific runner is `offline` in the per-runner status block (`ez-runner-c-6 online false`). Often coexists with Class A — a runner that was online yesterday is offline today, dropping registered count.

## Webhook payload shape (verbatim)

```
ez-gh-actions:CRITICAL ezgha fleet invariant violation E1
INV-1 utilization violated: busy=X/22 registered=Y queued_jobs=Z fail_class=<class> INV-2 duration violated: oldest_queued=M.Nm oldest_running=A.Bm threshold=20m
```

The `fail_class=` is the SINGLE most important field for triage. Always quote it verbatim in the System alerts section of the brief — paraphrasing ("runner bug", "scheduling issue") loses the class signal and the dispatch lands on the wrong layer.

## Recommended brief phrasing

| `fail_class` | Brief label | AO dispatch target |
|---|---|---|
| `missing-registration` | "ezgha fleet CRITICAL — missing-registration" | runner-pool / cloud-init / VM lifecycle layer |
| `genuinely-idle` | "ezgha fleet CRITICAL — genuinely-idle scheduling bug" | scheduler / claim-layer code |
| `runner-offline` (in per-runner status block) | "ezgha runner `<name>` offline — pool re-registration needed" | runner lifecycle / VM restart |
| (multi-class overlap) | "ezgha fleet CRITICAL — `<class A>` + `<class B>` (worst case, dispatch both)" | two parallel AO workers |

## Companion observations from 2026-07-11 sweep

- **Canary SLO breach pattern correlates**: when the fleet hits `genuinely-idle`, `ez-gh-actions selftest.yml` posts `:warning: canary SLO breach` every ~21min with `conclusion=None time_to_start=None slo=90s`. The canary's `None` status means the runner didn't even pick up the canary job — same root cause. Surface both alerts in the brief, link them as one symptom.
- **Longest-running queued job (`oldest_queued`) is the smoking gun**: 2026-07-11 hit 208.2m vs 20m threshold. Always include this number. If it's the same `feat/issue-8118` PR Coverage Report job for >3h, that's a developer-blocked-merge signal, not just a fleet bug.