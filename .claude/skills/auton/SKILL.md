---
name: auton
description: Diagnose why the automation system is not autonomously driving PRs to green and merge.
---

# Autonomy Diagnostic Skill

## Purpose

**Run /auton AFTER a work block ends** — retrospective review of what workers did, what failed, and why. It is the post-mortem tool.

**Run /babysit WHILE work is happening** — live triage, parallel worker dispatch, DRIVER mode nudges. It is the concurrent monitoring tool.

| Skill | When | Mode | Output |
|-------|------|------|--------|
| `/babysit` | During active workers | Live monitoring, dispatch | Per-PR status, DRIVER nudges |
| `/auton` | After block completes | Retrospective | Outcome table, root causes, metrics |

When invoked, diagnose WHY the $ORG + AO system is NOT autonomously driving PRs to N-green and merged. The system is supposed to do this without human intervention — if it isn't, something is broken.

## Read first (mandatory before answering)

> **⚠️ DUAL-CONFIG WARNING (2026-04-15):** Two AO config directories exist with different purposes:
> - `~/.openclaw/` — CLI/interactive use (used by `ao spawn`, `ao config`, etc.)
> - `~/.openclaw_prod/` — worker use (used by lifecycle-workers via launchd plist `AO_CONFIG_PATH`)
> **Always diagnose BOTH or verify which is active** — they can diverge and cause auth failures.

1. `~/.hermes/` — Hermes agent config (the agent since 2026-04-12; OpenClaw is dead)
2. `~/.openclaw_prod/agent-orchestrator.yaml` — AO worker config (used by lifecycle-workers)
3. `~/.openclaw/agent-orchestrator.yaml` — AO CLI config (used by interactive `ao` commands)
4. `~/.codex/AGENTS.md` — agent policies
5. `~/.openclaw/SOUL.md` — AO decision-making policy (legacy; Hermes uses its own)

**NOTE: ao-pr-poller is DEPRECATED and removed. Do NOT check for it or report its absence as a problem.**

## The system's intended behavior

```
AO lifecycle-worker (every ~5 min via launchd)
  ↓ detects non-green PR (backfillAllPRs: true)
  ↓ spawns agento session (ao spawn --claim-pr)
  ↓ agento: reads comments, fixes code, pushes
  ↓ agento: posts @coderabbitai all good?
  ↓ agento: runs /er evidence review
  ↓ CI passes, CR APPROVED, Bugbot neutral, comments resolved
  ↓ worker-signals-completion reaction fires → skeptic-review
  ↓ skeptic-review runs `ao skeptic verify` and posts VERDICT comment
  ↓ skeptic-cron.yml checks 7-green and merges when all applicable gates pass
```

**Key config to verify** (from the ACTIVE config — run Step 0 first):
```yaml
worker-signals-completion:
  auto: true
  action: skeptic-review
  skepticModel: codex
```
And the repo must have a healthy `skeptic-cron.yml` workflow. `approved-and-green` may still exist, but it is no longer the canonical merge executor.

If `worker-signals-completion` is missing, `auto: false`, or not `action: skeptic-review`, that is the local skeptic trigger gap.

**Full autonomy means: idea in → merged PR out, zero human clicks.**

## Diagnostic questions (answer each with evidence)

### 0. Verify active config path (MUST DO FIRST — 2026-04-15 lesson)
```bash
# Find which config workers actually use
ps aux | grep "lifecycle-worker" | grep -v grep | head -5

# Check if both configs exist and are different
diff ~/.openclaw/agent-orchestrator.yaml ~/.openclaw_prod/agent-orchestrator.yaml 2>/dev/null && echo "configs IDENTICAL" || echo "⚠️ configs DIVERGE"

# If configs differ, the WORKER config is the source of truth for auth/model issues
# Workers read AO_CONFIG_PATH from their process env — verify it:
ps aux | grep "lifecycle-worker" | grep -v grep | grep -o "AO_CONFIG_PATH=[^ ]*"
```
**Why this matters:** `~/.openclaw/` (CLI) and `~/.openclaw_prod/` (workers) can diverge. The 2026-04-15 auth outage was caused by `~/.openclaw_prod/` having `model: gemini-3-flash-preview` while `~/.openclaw/` had `MiniMax-M2.7`. Always check the worker config first for auth issues.

### 1. Is AO lifecycle-worker and orchestrator running?
```bash
# Lifecycle-worker
launchctl list com.agentorchestrator.lifecycle-$ORG

# Orchestrator — sessions are hash-prefixed, NEVER use hard-coded "ao-orchestrator"
# Correct pattern:
orch_session=$(tmux list-sessions 2>/dev/null | grep "ao-orchestrator" | cut -d: -f1)
if [ -n "$orch_session" ]; then
  echo "ao-orchestrator FOUND: $orch_session"
  tmux capture-pane -t "$orch_session" -p -S -10
else
  echo "ao-orchestrator NOT FOUND"
fi
```
```bash
launchctl list com.agentorchestrator.lifecycle-$ORG
tail -20 /tmp/ao-lifecycle-$ORG.log
```

### 3. Are sessions being spawned?
```bash
tmux list-sessions | grep -E "^[a-z]{2}-[0-9]+"
ao session ls --project agent-orchestrator 2>/dev/null || echo "ao session ls failed"
```

### 4. Are sessions doing work? (or idle/zombie)
```bash
# For each jc-* session, check if agent is alive
tmux list-sessions -F '#{session_name}' | grep jc- | while read s; do
  cmd=$(tmux list-panes -t "$s" -F '#{pane_current_command}' 2>/dev/null)
  echo "$s: $cmd"
done
```

### 5. What are the non-green reasons per PR?
```bash
gh pr list --repo jleechanorg/agent-orchestrator --state open \
  --json number,title,mergeable,mergeStateStatus,reviewDecision

# Verify skeptic-review trigger wiring (REQUIRED for autonomous reviewing):
python3 - <<'PY'
import yaml, os
# Try worker config first, fall back to CLI config
for path in [os.environ.get("AO_CONFIG_PATH", ""), "~/.openclaw_prod/agent-orchestrator.yaml", "~/.openclaw/agent-orchestrator.yaml"]:
    if path and os.path.exists(os.path.expanduser(path)):
        cfg = yaml.safe_load(open(os.path.expanduser(path)))
        print(f"Config: {path}")
        print(((cfg.get("reactions") or {}).get("worker-signals-completion") or {}))
        break
PY

# Verify skeptic-cron is present and running:
gh run list --repo jleechanorg/agent-orchestrator --workflow skeptic-cron.yml --limit 3
```

### 6. Is CR rate-limited?
```bash
gh api repos/jleechanorg/$ORG/issues/comments?per_page=5 | \
  python3 -c "import json,sys; [print(c['user']['login'],c['body'][:100]) for c in json.load(sys.stdin) if 'rate limit' in c['body'].lower()]"
```

### 7. Is the 7-green review + merge chain working correctly?
```bash
# Verify latest skeptic markers and VERDICT comment are bound to the head SHA
gh api repos/jleechanorg/agent-orchestrator/issues/<PR_NUM>/comments --paginate | \
  jq '[.[] | select(.body | test("skeptic-(gate|cron)-trigger|VERDICT:"; "i"))] | .[-5:]'
```

### 8. Is the stray-worktree bug blocking spawns?
```bash
git -C ~/.openclaw worktree list | grep -v "~/.openclaw\b\|~/.worktrees"
# Any /private/tmp/ or unexpected paths = stray worktree blocking new spawns
```

## Common failure modes

| Symptom | Root cause | Fix |
|---|---|---|
| Sessions spawn but die immediately | `--claim-pr` fails (stray worktree) | clear stale paths / targeted unlock |
| Sessions alive but no pushes | Agent hits rate limit or auth failure | Check agent logs, re-auth |
| CR never APPROVED | Rate limited (too many PRs) | Wait for limit reset, or reduce simultaneous PRs |
| 7-green checks pass except skeptic | `worker-signals-completion` missing, marker mismatch, or skeptic-review failed | Verify skeptic-review hook and latest VERDICT comment markers |
| `skeptic-cron` runs but merges 0 PRs | No PR is truly 7-green | Inspect gate-by-gate failures in workflow logs |
| `/tmp/ao-pr-poller.log` missing | **NOT A BUG** — ao-pr-poller is deprecated/removed | Ignore; its absence is correct and expected |
| PRs cycling CR changes_requested | Agent not reading CR comments correctly | Check agento's comment-reading skill |
| Spawned sessions are idle shells | `is_agent_alive_in_session` returns false | Check Hermes gateway is running (`hermes gateway status`) |

## Worker Session Review (48h fanout)

When diagnosing autonomy health, **read every active worker session** from the last 48h and produce an outcome table. This is mandatory for any /auton run — system-level health checks alone miss per-worker failure classes.

### Step 1 — Enumerate 48h sessions

```bash
# Sessions created in last 48h
tmux list-sessions -F '#{session_name} #{session_created}' | awk -v cutoff=$(date -v-48H +%s 2>/dev/null || date -d '48 hours ago' +%s) '$2 > cutoff {print $1}'

# AO status summary (shows branch, PR, CI, steer count)
ao status 2>/dev/null
```

### Step 2 — Read each session (parallel)

For each worker session:
```bash
tmux capture-pane -t <session> -p -S -5000 | tail -300
```

Extract per-session:
- **Task**: what prose was in the initial spawn?
- **PR produced**: branch + PR number (if any)
- **Outcome**: MERGED / GREEN-AWAITING / OPEN-STALLED / IDLE / MIS-SPAWNED
- **Steers**: count of `ao send` corrections or redirections visible in transcript
- **Blocker**: one-line root cause if not merged

### Step 3 — Cross-check PR states

```bash
gh pr view <N> --repo <owner>/<repo> --json state,merged,mergeable,reviewDecision
```

### Worker outcome table format

```
| Worker | Repo | PR | Outcome | Steers | Key Issue |
|--------|------|----|---------|----|-----------|
| ao-NNNN | repo | #N branch | MERGED ✅ / GREEN ✅ / OPEN ⚠️ / IDLE ❌ | N | one-line |
```

## Root Cause Taxonomy

These are the observed failure classes across 48h windows. Assign each stalled worker exactly one root cause:

| Class | Name | Symptom | Fix |
|-------|------|---------|-----|
| RC-1 | **Spawn context gap** | Worker asked "what task should I do?" — no task prose in spawn | Always include prose: `ao spawn --bead bd-xxx "Implement X: ..."` |
| RC-2 | **Scope drift** | Worker documented the problem instead of solving it (PR title contains "docs" when impl was requested) | Send `ao send <session> "DRIVER: implement, not document. Fix <file>:<line>"` |
| RC-3 | **Stall-without-escalate** | Worker went idle at a gate (CR, CI, skeptic) without sending `ao send` to orchestrator or posting `/skeptic` | Post `/skeptic` on PR; steer worker with DRIVER mode |
| RC-4 | **Wrong-bead correction** | Worker pivoted to merged/non-existent bead after receiving correction | Always `br show <bead>` before sending any `ao send` correction |
| RC-5 | **Hook noise** | `PostToolUse hook error: unbound variable` slowing worker but not blocking | Fix hook script (`pr_create_pattern` unbound var); non-critical if worker still progresses |
| RC-6 | **Context exhaustion** | Worker context hit limit mid-task; state partially preserved in handoff | Check session for "context is N% remaining" lines; spawn fresh worker with recap |
| RC-7 | **Auth / model failure** | Worker gets 401 or model-not-found after SCM failures | Check `AO_CONFIG_PATH` env; verify API key; restart worker |

## Autonomy Metrics

Report these at the end of every /auton run:

| Metric | Definition | Target |
|--------|-----------|--------|
| **End-to-end success rate** | (MERGED + GREEN-AWAITING) / total workers in window | >60% |
| **Avg steers/worker** | total human steers / workers | <0.5 |
| **Spawn context gap rate** | mis-spawned workers / total | 0% |
| **Stall rate** | OPEN-STALLED / total | <20% |

## Output format

```
## Autonomy Diagnostic — <date>

### System health
- AO lifecycle-worker: RUNNING / STOPPED
- Orchestrator session: FOUND (hash-prefixed name) / NOT FOUND
- Skeptic-review hook: worker-signals-completion auto=true/false, action=X
- Skeptic-cron workflow: RUNNING / FAILING / NOT FOUND
- Active sessions: N (M with live agents)
- Open PRs: N total, N non-green

### Worker session review (48h)
| Worker | Repo | PR | Outcome | Steers | Key Issue |
|--------|------|----|---------|----|-----------|
| ... | ... | ... | ... | ... | ... |

### Per-PR status
| PR | Non-green reason | Session | Session state |
|---|---|---|---|
| #NNN | <reason from log> | jc-NNN | alive/zombie/none |

### Root causes (by class)
- RC-1 Spawn context gap: N workers (list sessions)
- RC-2 Scope drift: N workers
- RC-3 Stall-without-escalate: N workers
- ...

### Metrics
- End-to-end success rate: N% (target >60%)
- Avg steers/worker: N (target <0.5)
- Spawn context gap rate: N% (target 0%)
- Stall rate: N% (target <20%)

### Recommended fixes (ordered by impact)
1. <most impactful fix first>
```
