# Design: Integrate `automation/` Cron Jobs with OpenClaw Mission Control

## Context
The current `automation/` system in `your-project.com` uses local cron + shell/python scripts to run PR automation and watchdog tasks. OpenClaw now provides Mission Control + agent orchestration that can supervise long-running flows, route messages, and coordinate multi-model review.

Goal: preserve existing cron reliability while adding Mission Control as the control plane for visibility, approvals, and model-assisted review.

---

## Objectives

1. Keep existing automation jobs working with minimal breakage.
2. Add a Mission Control orchestration layer for:
   - job dispatch
   - health/status visibility
   - structured alerts and retry policy
   - model-based PR review passes (Claude Opus + Codex)
3. No phased migration: add Mission Control as a thin bridge over existing cron jobs without a cutover plan.

## Non-Goals

- Rewriting all automation scripts in this phase.
- Removing cron immediately.
- Changing core branch/PR policies.

---

## Current State (as-is)

- Scheduling: `crontab.template`, `install_cron_entries.sh`
- Executors: shell scripts + `orchestrated_pr_runner.py`
- Per-PR cooldown enforcement via `AutomationSafetyManager` (global run limit 50/day, per-PR attempt limits)
- Limited centralized observability; status largely from logs and ad-hoc checks

Pain points:
- Difficult to coordinate retries/backoff across scripts
- Weak cross-job dependency management
- Manual effort to run multi-model design review consistently

---

## Proposed Hybrid Architecture

```text
[cron tick] --> [OpenClaw trigger wrapper]
                  |
                  v
        [Mission Control Job Router]
          |         |         |
          v         v         v
      PR prep   Validation   Review swarm
                                 |
                                 +--> Claude Opus reviewer
                                 +--> Codex reviewer

Outputs:
- PR comment summary
- structured artifacts in automation/evidence/
- Slack/thread update (placeholder; Slack webhook not yet implemented in automation/)
```

### Components

1. **Cron Trigger Wrapper** (thin)
   - Existing cron entries call a wrapper script (`automation/openclaw_mission_control_entry.sh`)
   - Wrapper sends structured job request to OpenClaw Mission Control (job type + repo + branch + PR id + mode).

2. **Mission Control Job Router**
   - Canonical state machine for job lifecycle:
     - `queued -> running -> review_pending -> completed|failed`
   - Persists artifacts and emits periodic heartbeat/status.

3. **Model Review Swarm (design-review mode)**
   - Runs two independent review agents:
     - Claude Opus: architecture clarity, risk, policy/safety concerns
     - Codex: implementation feasibility, edge-case coverage, testability
   - Produces merged review report with explicit disagreements.
   - **Conflict resolution policy**: findings are merged by (file, line-range, finding-hash). Where both models flag the same location, the finding with the higher severity wins. Where findings conflict (e.g., one model says "safe", the other flags a risk), both findings are included verbatim under a "Disagreement" section, and the PR author must resolve manually. Pure duplicates (same text, same location) are deduplicated to one entry.

4. **PR Feedback Publisher**
   - Posts concise PR comment containing:
     - top findings by severity
     - actionable next steps
     - links to full artifacts

---

## Execution Flow

1. Cron runs at existing cadences (every 30 min for fix-pr/comment-validation, hourly at :15/:30/:45 for codex/minimax lanes, every 2h for PR monitor, every 4h for backup).
2. Wrapper sends Mission Control job request.
3. Mission Control decides whether to:
   - skip (cooldown/no-op)
   - run full design review
   - run targeted delta review (if small diff)
4. For review jobs:
   - gather changed files + existing design docs
   - run Claude Opus reviewer
   - run Codex reviewer
   - synthesize and dedupe comments
5. Publish:
   - update PR comment
   - write evidence bundle (`automation/evidence/mission_control/run_<random>/`)
   - send Slack thread status update (future: Slack integration not yet implemented; channel is a placeholder in the design)

### AutomationSafetyManager Interaction

Mission Control does not replace the existing safety framework. The wrapper delegates safety decisions to `AutomationSafetyManager` before dispatch:
- Per-PR gate via `--check-pr <pr_number>` for PR attempt limits/cooldowns.
- Global gate via `--check-global` for the shared daily global budget.
- Accounting via `--record-global` before dispatch and `--record-pr <pr_number> <success|failure>` after completion.

In shadow/dry-run mode, Mission Control writes evidence only and must not publish PR comments or Slack updates. Mission Control dry-run MUST NOT publish PR comments or Slack updates; it writes evidence artifacts only.

---

## Data Contracts (v1)

### Job Request

```json
{
  "job_type": "design_review",
  "repo": "jleechanorg/your-project.com",
  "pr_number": 1234,
  "job_id": "mc-2026-1234-abc1234",
  "head_sha": "abc1234def5678",
  "correlation_id": "pr-1234:abc1234def5678:design_review",
  "idempotency_key": "1234|abc1234def5678|design_review",
  "branch": "feature/...",
  "trigger": "cron",
  "requested_models": ["claude_opus", "codex"],
  "dry_run": false
}
```

`pr_number` + `head_sha` + `job_type` together form the idempotency key; duplicate requests with the same key are skipped.

### Job Result

```json
{
  "job_id": "mc-2026-1234-abc1234",
  "pr_number": 1234,
  "head_sha": "abc1234def5678",
  "correlation_id": "pr-1234:abc1234def5678:design_review",
  "idempotency_key": "1234|abc1234def5678|design_review",
  "status": "completed",
  "summary": "2 high, 3 medium findings",
  "model_runs": {
    "claude_opus": {"status": "ok", "artifact": "..."},
    "codex": {"status": "ok", "artifact": "..."}
  },
  "published": {
    "pr_comment_url": "...",
    "slack_thread_ts": "..."
  }
}
```

`job_id`, `pr_number`, `head_sha`, `correlation_id`, and `idempotency_key` let the publisher and evidence writer reliably correlate results to the originating request. `correlation_id` and `idempotency_key` in Job Result MUST echo the exact values from Job Request.

---

## Minimal Integration Scope (requested)

No phased migration. Keep existing cron automation as-is and add only the thinnest Mission Control bridge.

### MVP Integration (single pass)
1. Add `automation/openclaw_mission_control_entry.sh` as a wrapper invoked by existing cron jobs.
2. Wrapper enforces pre-dispatch safety gating via `AutomationSafetyManager` (`can_start_global_run` equivalent) before `ai_orch run` dispatch.
3. Wrapper executes `ai_orch run --agent-cli <cli> [--model <model>] <task>` (no custom model CLI path). `MiniMax-M2.5` is only defaulted when `agent-cli=minimax`; other CLIs do not receive a forced model flag.
4. Wrapper records run metadata + stdout/stderr under `automation/evidence/mission_control/run_<random>/`, including correlation fields (`job_id`, `pr_number`, `head_sha`, `correlation_id`, `idempotency_key`).
5. Mission Control uses wrapper output to trigger Claude Opus + Codex review lanes and merge results.
6. Publish one idempotent PR comment keyed consistently as `pr_number + head_sha + job_type` (same key used in result artifacts).

### Explicitly out of scope
- Rewriting existing `automation/` workflows.
- Creating a new scheduler.
- Multi-phase cutover logic.

---

## Risks & Mitigations

1. **Model flakiness / API limits**
   - Mitigation: per-model retries + degraded mode if one reviewer fails.
2. **Duplicate PR comments**
   - Mitigation: idempotency key per `pr_number + head_sha + job_type`; each composite key is stored and checked before any run is dispatched.
3. **Cron overlap race conditions**
   - Mitigation: advisory lock held for the full wrapper lifetime. Use `flock -n` when available; on hosts without `flock` (notably default macOS), use atomic `mkdir` lock-dir fallback at the same lock path. If lock acquisition fails, wrapper exits `0` with a skip log and does not dispatch `ai_orch`. Lock is always released on process exit (success, failure, or signal).
4. **Review noise**
   - Mitigation: severity thresholding + dedupe by file/line/finding hash.
5. **Backpressure / rate-limiting**
   - Mitigation: backpressure is enforced in two layers: (a) wrapper-level single-flight lock prevents overlapping cron-triggered runs on the same host, and (b) Mission Control router in-flight queue limit (default 3) rejects excess requests with `429 TOO_MANY_REQUESTS`; skipped/rejected work is retried on later cron ticks.
6. **Safety limit bypass**
   - Mitigation: The wrapper always runs `AutomationSafetyManager` checks (`check-pr` and `check-global`) before dispatch and records outcomes (`record-global`, `record-pr`) so Mission Control jobs stay inside the same global/per-PR limits as existing `orchestrated_pr_runner.py` flows.

---

## Success Criteria

- 90%+ scheduled design-review jobs complete without manual intervention.
- PR reviewers receive one consolidated comment per run (no spam).
- Mean time to identify design risks decreases (baseline -> target to be measured).
- Teams can inspect artifacts and replay job history from Mission Control logs.

---

## Next Implementation Tasks

1. Add `automation/openclaw_mission_control_entry.sh` wrapper.
2. Add Mission Control job schema + validation.
3. Add model-run adapters for Claude Opus and Codex.
4. Add PR publisher with idempotent update.
5. Add evidence writer + summary index.
6. Add tests for state transitions and failure recovery.

---

## Phase 5 Runbook (Verification + Operations)

### Files emitted per run
- `automation/evidence/mission_control/run_*/run.json`
- `automation/evidence/mission_control/run_*/ai_orch.out.txt`
- `automation/evidence/mission_control/run_*/ai_orch.err.txt`
- `automation/evidence/mission_control/metrics.json`
- `automation/evidence/mission_control/health.json`

### Health contract
- `status=ok`: last run healthy (`dry_run` or successful live dispatch).
- `status=degraded`: last run failed, stalled, or failed preflight checks.
- `detail`: short machine-readable reason (`live_run_success`, `stalled`, `ai_orch_not_found`, etc).

### Counter contract (`metrics.json`)
- `runs_total`
- `runs_ok`
- `runs_failed`
- `runs_stalled`
- `last_status`
- `last_duration_seconds`
- `last_run_at`

### E2E smoke checks
1. **Dry-run contract**
   ```bash
   automation/openclaw_mission_control_entry.sh --dry-run --task "Mission Control dry run"
   ```
   Expect: exit `0`, metadata file path printed, `health.status=ok`.
2. **Live-run happy path**
   ```bash
   automation/openclaw_mission_control_entry.sh --task "Reply with exactly: MISSION_CONTROL_AI_ORCH_OK"
   ```
   Expect: exit `0`, `run.json.status=ok`, `metrics.runs_ok` increments.
3. **Stalled-run handling**
   ```bash
   MISSION_CONTROL_STALL_TIMEOUT_SECONDS=1 automation/openclaw_mission_control_entry.sh --task "..."
   ```
   Expect: wrapper enforces a hard execution timeout around `ai_orch`; timed-out runs exit `124`, `run.json.status=stalled`, `health.status=degraded`, and `metrics.runs_stalled` increments without incrementing `runs_failed`.

### Cron locking behavior
- Wrapper attempts `flock -n` on `.mission_control.lock`; if `flock` is unavailable, it falls back to atomic `mkdir` lock-dir semantics.
- If lock is held, wrapper exits `0` with a skip log line; no concurrent run starts.
- Router `409`/`429` responses represent downstream contention/backpressure and are retried by cron on subsequent ticks.
