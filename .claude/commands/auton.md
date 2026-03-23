# /auton — Autonomy Diagnostic

## Purpose

Diagnose WHY the jleechanclaw + AO system is NOT autonomously driving PRs to 6 green and merged. The system is supposed to do this without human intervention — if it isn't, something is broken.

**Skill reference**: `~/.claude/skills/auton.md`
**Session monitor skill**: `~/.claude/skills/ao-session-monitor.md`

## Usage

- `/auton` — Run full autonomy diagnostic
- `/auton <description>` — Focus on a specific failure mode

## Execution

**YOU (Claude) must execute the following steps immediately.**

### Step 1: Read the goals and system design (mandatory)

Before answering, read these files to understand what "working" means:

1. `~/.openclaw/CLAUDE.md` — repo goals, PR green definition, autonomy target
2. `~/.codex/AGENTS.md` — agent policies
3. `~/.openclaw/agent-orchestrator.yaml` — AO project config
4. `~/.openclaw/scripts/ao-pr-poller.sh` — the polling loop
5. `~/.openclaw/SOUL.md` — openclaw decision-making policy

### Step 2: Run diagnostics (parallel group A + B)

Run **Group A** and **Group B** in parallel for speed.

#### Group A — Infrastructure & Session State

Run all of these together:

```bash
# A1. Orchestrator session — what is it doing?
tmux capture-pane -t ao-orchestrator -p -S -20 2>/dev/null || echo "ORCHESTRATOR SESSION NOT FOUND"

# A2. Worker session inventory with activity detection (30 lines each)
# Uses ao-session-monitor skill: capture 30 lines, look for Unicode activity indicators
for s in $(tmux list-sessions 2>/dev/null | grep -E "ao-[0-9]|jc-" | cut -d: -f1); do
  echo "=== SESSION: $s ==="
  last=$(tmux capture-pane -t "$s" -p -S -30 2>/dev/null)
  echo "$last" | tail -5
  echo "---"
  # Detect state via activity indicators (✻✶✳✽✾✢)
  activity=$(echo "$last" | grep -oE "[✻✶✳✽✾✢] [A-Za-z]+…[^)]*\)" | tail -1)
  pr=$(echo "$last" | grep -oE "#[0-9]+" | head -1)
  uc=""; echo "$last" | grep -q "uncommitted" && uc="+uncommitted"
  if [ -n "$activity" ]; then
    echo "STATE: WORKING $pr $uc ($activity)"
  elif echo "$last" | grep -qE "Running…|timeout"; then
    echo "STATE: WORKING (shell command) $pr $uc"
  elif echo "$last" | grep -qE "Baked|Sautéed"; then
    echo "STATE: COMPLETED $pr"
  elif echo "$last" | grep -q "queued"; then
    echo "STATE: QUEUED $pr"
  else
    echo "STATE: IDLE $pr $uc"
  fi
  echo ""
done

# A3. Is AO lifecycle-worker running? Check for duplicates.
lw_count=$(ps aux | grep -c "[l]ifecycle-worker")
echo "Lifecycle-worker process count: $lw_count"
if [ "$lw_count" -gt 3 ]; then
  echo "⚠️  DUPLICATE LIFECYCLE-WORKERS DETECTED ($lw_count > 3) — kill extras!"
  ps aux | grep "[l]ifecycle-worker"
fi

# A4. Is the poller running?
launchctl list ai.ao-pr-poller 2>/dev/null || echo "Poller not registered"
tail -20 /tmp/ao-pr-poller.log 2>/dev/null || echo "No poller log"

# A5. Stray worktrees blocking spawns?
git -C ~/.openclaw worktree list 2>/dev/null | grep -v "~/.openclaw\b\|~/.worktrees" || true
```

#### Group B — GitHub & Rate Limits

Run all of these together:

```bash
# B1. Rate limits — check before making API calls
gh api rate_limit --jq '.resources | {core: .core.remaining, graphql: .graphql.remaining}'

# B2. Open PRs with status
gh pr list --repo jleechanorg/agent-orchestrator --state open --json number,title,mergeable,reviewDecision,statusCheckRollup --jq '.[] | {number, title, mergeable, reviewDecision, ci: (.statusCheckRollup // [] | map(select(.conclusion != "")) | map(.conclusion) | unique)}'

# B3. Non-green reasons from poller log
tail -100 /tmp/ao-pr-poller.log 2>/dev/null | grep -E "not green|SKIP|WARNING|ERROR" | tail -20

# B4. Recent spawning activity
tail -50 /tmp/ao-pr-poller.log 2>/dev/null | grep -E "Spawning|SUCCESS" | tail -10
```

### Step 3: Cross-reference — CHANGES_REQUESTED gap detection

After both groups complete, cross-reference:
1. List PRs with `reviewDecision: CHANGES_REQUESTED`
2. Check if each CR_REQ PR has an active worker session (from Group A2)
3. If a CR_REQ PR has **no active session**, flag it as a gap — the orchestrator should be addressing it

### Step 4: Output diagnostic report

```
## Autonomy Diagnostic — <date>

### System health
- Poller: RUNNING / STOPPED / ERRORING
- AO lifecycle-worker: RUNNING / STOPPED (count: N) ⚠️ if >3
- Orchestrator session: SPAWNING / IDLE / STUCK / NOT FOUND
- Active worker sessions: N (M working, K idle, J completed)
- Rate limits: core=N, graphql=N
- Open PRs: N total, N non-green

### Orchestrator state
<What the orchestrator is doing based on tmux capture — spawning new sessions? idle? stuck on error?>

### Per-PR status
| PR | Non-green reason | Session | Session state | Activity |
|---|---|---|---|---|
| #NNN | <reason> | ao-NNN / none | WORKING/IDLE/COMPLETED/QUEUED | <indicator or "—"> |

### CHANGES_REQUESTED gaps
<List PRs with CR CHANGES_REQUESTED that have NO active session — these need attention>
(If none, say "All CR_REQ PRs have active sessions ✓")

### Duplicate lifecycle-worker check
<OK if ≤3, WARNING with PIDs if >3>

### Root cause
<Primary reason the system is not progressing PRs autonomously>

### Recommended fix
<Concrete next step>
```

## Input

$ARGUMENTS
