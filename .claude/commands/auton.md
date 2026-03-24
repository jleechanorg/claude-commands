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

# A3. Is AO lifecycle-worker running? Check per-project (7 projects = 7 workers is normal)
lw_count=$(ps aux | grep -c "[l]ifecycle-worker")
lw_per_project=$(ps aux | grep "[l]ifecycle-worker" | awk '{print $NF}' | sort -u | wc -l | tr -d ' ')
echo "Lifecycle-worker process count: $lw_count (unique projects: $lw_per_project)"
# Only flag as duplicate if same project appears more than once
ps aux | grep "[l]ifecycle-worker" | awk '{print $NF}' | sort | uniq -d | while read dup; do
  echo "⚠️  DUPLICATE lifecycle-worker for project: $dup"
  ps aux | grep "[l]ifecycle-worker" | grep "$dup"
done

# A3b. ZOMBIE SESSION DETECTION — cross-reference AO session store vs tmux
# Sessions marked "killed" in AO but still alive in tmux are zombies — lifecycle-worker won't manage them
echo "--- AO session store state (agent-orchestrator project) ---"
ao session ls --project agent-orchestrator 2>/dev/null || echo "ao session ls failed"
echo "--- Zombie check: AO-marked-killed sessions still in tmux ---"
AO_DATA=$(ls ~/.agent-orchestrator/bb5e6b7f8db3-agent-orchestrator/sessions/ 2>/dev/null)
for s in $AO_DATA; do
  sfile=~/.agent-orchestrator/bb5e6b7f8db3-agent-orchestrator/sessions/$s
  [ -f "$sfile" ] || continue
  status=$(grep "^status=" "$sfile" 2>/dev/null | cut -d= -f2)
  tmux_name=$(grep "^tmuxName=" "$sfile" 2>/dev/null | cut -d= -f2)
  [ "$status" = "killed" ] || continue
  # Check if the tmux session is still alive
  if tmux has-session -t "$tmux_name" 2>/dev/null; then
    pr=$(grep "^pr=" "$sfile" | cut -d= -f2 | grep -oE "[0-9]+$")
    echo "  ZOMBIE: $s (tmux=$tmux_name, PR=#$pr) — AO=killed but tmux still running"
  fi
done

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

# B5. PR worker coverage check (deterministic — exits non-zero if uncovered PRs)
$HOME/.openclaw/scripts/check-pr-worker-coverage.sh 2>/dev/null || echo "Coverage script not found or returned non-zero (uncovered PRs exist)"
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

### Zombie session check
<Sessions where AO status=killed but tmux still alive — lifecycle-worker is NOT managing these>
| Session | AO status | tmux alive | PR | Action needed |
(If none, say "No zombie sessions ✓")

### AO session store vs tmux desync
<"ao session ls" result vs tmux count — if AO says 0 active but tmux has sessions, flag as desync>

### Lifecycle-worker duplicate check
<Count per project — only flag if SAME PROJECT has >1 worker. Multi-project = expected.>

### Root cause
<Primary reason the system is not progressing PRs autonomously>

### Recommended fix
<Concrete next step>
```

## Input

$ARGUMENTS
