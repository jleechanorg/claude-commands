---
name: ao-spawn-safety
description: "Use BEFORE bulk or iterative AO spawns over 3 workers. Respect the channel max_spawn setting, enforce the absolute 20-worker cap, spawn at most 5 per batch, and never use load average as the gate."
---

# AO spawn safety — resource check before bulk spawning


**Scope: AO worker spawning only.** Do NOT apply these checks to Hermes's own incoming message handling — that blocks Hermes from responding when AO workers are running.

Before issuing any bulk or iterative AO spawn sequence (more than 3 spawns in a loop or in response to an open-ended instruction like "do all" / "take it all the way"):

1. **Honor the channel admission limit.** If active AO sessions on the target channel exceed its `kanban.max_spawn` setting (default 8), pause and ask the operator before spawning more.
2. **Hard cap at 20 AO workers.** If `ao session ls` shows 20 or more active sessions total, decline to spawn and report the count. This cap is on **AO worker count**, not system load average — do NOT use `sysctl vm.loadavg` as the spawn gate.
3. **Batch at most 5 workers.** Spawn no more than 5 workers in one batch, then wait for completions or explicit progress signals before starting another batch.

**Why**: A 2026-05-15 spawn storm created 517 sessions, starved the host, and interrupted the gateway. The current operator policy deliberately uses three independent controls: channel admission, a 20-worker absolute cap, and 5-worker batches. The old "15" value was a batch-size limit from a superseded revision, never a session-count safety gate.

## backfillAllPRs — separate per-project cap

`backfillAllPRs: true` spawns via `backfillUncoveredPRs` each health-cron cycle (every 3600s by default). Its project cap is `project.spawnQueue.maxActiveSessions` — currently default **20** in the TypeScript implementation. Keep it explicitly lower for backfill workloads.

**Always set this companion when enabling backfill:**
```yaml
backfillAllPRs: true
spawnQueue:
  enabled: true
  maxActiveSessions: 5  # prevents zombie accumulation from dead-tmux sessions
```

`maxConcurrentSessions` is NOT a valid config field and is silently ignored by Zod. Using it instead of `spawnQueue.maxActiveSessions` has no effect.

**Why 9 zombies accumulated (2026-06-18)**: Dead tmux sessions → `hasSession()=false` → PR marked "uncovered" → new worker spawned each cycle. Without a deliberately low per-project cap (or with a silently ignored field), accumulation continued unchecked.
