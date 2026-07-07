---
name: ao-spawn-safety
description: "Use BEFORE bulk/iterative AO spawns (>3). **Hard cap 30 AO workers** — that is the ONLY spawn limit. Batch up to 15 at a time. Never use loadavg as the gate."
---

# AO spawn safety — resource check before bulk spawning


**Scope: AO worker spawning only.** Do NOT apply these checks to Hermes's own incoming message handling — that blocks Hermes from responding when AO workers are running.

Before issuing any bulk or iterative AO spawn sequence (more than 3 spawns in a loop or in response to an open-ended instruction like "do all" / "take it all the way"):

1. **Hard cap at 30 AO workers — the ONLY cap.** If `ao list` shows <30 active sessions total, spawning is allowed (subject to per-batch limits). If ≥30, decline to spawn and report the count instead. There is no lower "soft pause" threshold. The cap is on **AO worker count**, not system load average — do NOT use `sysctl vm.loadavg` as the spawn gate.
2. **Batch up to 15 at a time**: Spawn ≤15 workers per batch; wait for completions (or explicit progress signals) before the next batch. Smaller batches (3-5) remain acceptable for resource-constrained hosts; 15 is the upper bound.

**Why**: 2026-05-15 incident — "take it all the way" spawned 517 sessions, loadavg=205, DNS starved, gateway down 2h. The 30-worker hard cap is the guard. (Earlier revisions also carried a soft "pause and ask at 8" rung tied to a `kanban.max_spawn` config that was never actually set in `config.yaml` or `agent-orchestrator.yaml` — removed 2026-06-12 as redundant friction. Cap history: 20→30 and batch 10→15 on 2026-07-03 by user directive, aligning with the auto-factory-daemon spec §4.2.8.)

## backfillAllPRs — separate per-project cap

`backfillAllPRs: true` spawns via `backfillUncoveredPRs` each health-cron cycle (every 3600s by default). Its cap is `project.spawnQueue.maxActiveSessions` — default **30** (independent of the interactive 30-worker cap above).

**Always set this companion when enabling backfill:**
```yaml
backfillAllPRs: true
spawnQueue:
  enabled: true
  maxActiveSessions: 5  # prevents zombie accumulation from dead-tmux sessions
```

`maxConcurrentSessions` is NOT a valid config field and is silently ignored by Zod. Using it instead of `spawnQueue.maxActiveSessions` has no effect.

**Why 9 zombies accumulated (2026-06-18)**: Dead tmux sessions → `hasSession()=false` → PR marked "uncovered" → new worker spawned each cycle. Without a per-project cap (or with a silently-ignored field), the default 30-cap was never hit and accumulation continued unchecked.
