# ez-gh-actions canary / SLO / fleet-watchdog diagnostic reference

Canonical investigation recipe for `[ez-gh-actions:WARNING]` and `[ez-gh-actions:ERROR]` alerts posted by the `jleechanorg/ez-gh-actions` Rust daemon + bash fleet watchdog.

## System architecture

| Component | What it does | Where the artifact lives |
|---|---|---|
| Rust daemon (`org.jleechanorg.ezgha`) | Owns the GitHub App token, dispatches `ezgha-selftest` via workflow_dispatch on a schedule, polls runs, computes SLO breach, sends Slack alerts | `$HOME/.local/bin/ezgha` (or the launchd-loaded binary). `launchctl list \| grep ezgha` |
| `ezgha-selftest` workflow | The canary itself — `workflow_dispatch`-only, runs the 4-step "prove execution environment" job on an ephemeral self-hosted runner, then deregisters | `.github/workflows/selftest.yml` in `jleechanorg/ez-gh-actions` |
| `ezgha-fleet-watchdog.sh` (launchd) | Separate bash watchdog — enforces configured runner count on mac and Linux hosts, restarts the supervisor when below target for `consecutive >= 2` ticks | `~/.hermes/launchd/org.jleechanorg.ezgha-watchdog.plist` + `~/.claude-wa/skills/ezgha-watchdog/scripts/ezgha-fleet-watchdog.sh` |
| `ezgha-token-refresh` (launchd) | Re-mints the GitHub App installation token every 45 min, also kicked on event-driven 401 storms | `launchctl list \| grep ezgha-token-refresh` |
| `ezgha-queue-reaper-stopgap` (launchd) | Drains stuck queue entries | `launchctl list \| grep ezgha-queue-reaper-stopgap` |

## Alert payload formats (copy these patterns when matching log entries)

```
[ez-gh-actions:WARNING] ezgha canary SLO breach
jleechanorg/ez-gh-actions selftest.yml nonce=ezgha-canary-1783664131-96768 status=completed conclusion=Some("success") runner=None time_to_start=Nones slo=90s url=Some("https://github.com/jleechanorg/ez-gh-actions/actions/runs/29073358437")
```

Field semantics:
- `nonce` = `ezgha-canary-<unix_secs>-<pid>` (e.g. `ezgha-canary-1783664131-96768` was dispatched by the daemon at unix epoch 1783664131 = 2026-07-10T06:15:31Z)
- `status` = the canary's view of the run lifecycle (`dispatched`, `started`, `completed`, `slo_timeout_waiting_for_start`, `slo_timeout_waiting_for_run`, `timeout_after_run_seen`, `timeout_waiting_for_run`)
- `conclusion` = GitHub's `jobs.<job>.conclusion` (None while running, `"success"`, `"failure"`, `"cancelled"`, etc.)
- `runner` = the runner name that picked up the job (None = runner prefix didn't match the configured `runner.name_prefix`)
- `time_to_start=Nones` = **the false-positive signature** (None serialized with Rust's `{:?}` Debug format). Real values are `Some(NNs)` like `Some(50s)`.

## Source code landmarks (jleechanorg/ez-gh-actions)

| File | What's there | Why you care |
|---|---|---|
| `src/canary.rs` | The `CanaryResult` struct, the polling loop in `run_once()`, the `result_from_run_jobs()` SLO computation, the `should_alert()` predicate, the `alert_canary()` Slack post formatter | The `slo_breached = time_to_start_seconds.map(\|s\| s > 90).unwrap_or(run.status == "completed")` line at ~L303 is the false-positive race |
| `src/queue_monitor.rs` | `parse_github_timestamp_secs()` (strict 20-char `YYYY-MM-DDTHH:MM:SSZ` parser) and the queue-monitoring logic | If the canary logs `time_to_start=None`, the parser rejected one of the timestamps — usually because `started_at` was null in that snapshot, not because the timestamp was malformed |
| `src/github.rs` | `run_gh_with_backoff()`, `extract_retry_after_secs()`, rate-limit classification (primary vs secondary), event-driven token refresh | When the daemon is hitting secondary rate limits, canary polls slow down and you get "could not measure" alerts that are rate-limit-induced, not SLO-induced |
| `src/alert.rs` | `alert::notify()` and `Severity::{Info,Warning,Error}` | Severity mapping for canary alerts: `Warning` for SLO breach, `Error` for fleet below target |
| `scripts/ezgha-fleet-watchdog.sh` | Bash loop checking `slot_count` for both mac and linux hosts, with `consecutive <= 2` guard before supervisor restart | The bash watchdog is independent of the Rust canary — its Slack posts (when configured to Slack) come from this script, not from the daemon |

## Log format (bash fleet watchdog, `/tmp/ezgha-watchdog.log`)

```
[2026-07-10T04:40:43Z] MAC: configured=6, managed=6
[2026-07-10T04:40:43Z] OK: both hosts at configured count
[2026-07-10T04:40:43Z] COLIMA: VM state=Stopped — auto-starting colima
[2026-07-10T04:40:43Z] MAC: cannot read state (config=6 actual=) — supervisor may be unable to spawn (check stderr for isolation policy errors)
[2026-07-10T04:40:43Z] LINUX: configured=16, managed=0
[2026-07-10T04:40:43Z] LINUX: BELOW TARGET (0 < 16) — consecutive=1
[2026-07-10T04:40:43Z] LINUX: within normal churn window (consecutive=1 <= 2) — not restarting yet
[2026-07-10T04:40:43Z] WARN: one or more hosts missing ezgha or unreachable — manual intervention needed
```

Read the log top-to-bottom in time order; the cadence is one line per `evaluate_host` call (roughly every 15 min). The `consecutive` counter increments only when BELOW TARGET persists across ticks — if the COLIMA auto-start resets the supervisor and briefly makes the count read 0 for a different reason, the counter resets.

## 90-second root-cause decision tree

```
Alert received
├─ Body has time_to_start=Nones
│  ├─ Run actually completed successfully? (check jobs.conclusion)
│  │  ├─ YES → FALSE POSITIVE (the .unwrap_or race in canary.rs:303)
│  │  │        Patch target: src/canary.rs:303-305
│  │  └─ NO  → Real failure, but canary couldn't measure start latency
│  │           Check runner_name — if None, runner prefix mismatch
│  └─ Real time-to-start value (Some(NNs))
│     ├─ N > 90 → REAL SLO BREACH (slow runner pickup / queue starvation)
│     └─ N <= 90 → Daemon miscounted; check clock skew between daemon and GitHub
└─ Body has runner=None
   └─ Run completed but daemon's runner.name_prefix didn't match
      Check WorkflowJob.runner_name — common cause: new runner joined without prefix update
```

## Real incident (2026-07-10) — example case for reference

- **Alert:** `[ez-gh-actions:WARNING] ezgha canary SLO breach ... nonce=ezgha-canary-1783664131-96768 status=completed conclusion=Some("success") runner=None time_to_start=Nones slo=90s`
- **Investigation:** Run `29073358437` was clean. `created_at=2026-07-10T06:15:32Z`, job `started_at=2026-07-10T06:16:22Z` → **50s real start latency** (under SLO). Runner `ez-mac-runner-b-5` on the **mac fleet** (healthy).
- **Diagnosis:** Classic false-positive race. `time_to_start=Nones` signature + `conclusion=success` + real data showing 50s start = the `.unwrap_or(run.status == "completed")` bug firing.
- **Hidden finding:** While validating, discovered `/tmp/ezgha-watchdog.log` showed `LINUX: configured=16, managed=0` for 95+ minutes with `consecutive=1` never incrementing past the guard. The mac canary alerts were masking a **real** Linux fleet drain (supervisor can't read state on `jeff-ubuntu`, COLIMA auto-start keeps resetting the consecutive counter).
- **Lesson:** Don't stop at "the canary alert was a false positive" — read the bash watchdog log too. The two systems cover different failure modes and either can be the real incident.
