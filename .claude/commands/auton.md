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
4. `~/.openclaw/SOUL.md` — openclaw decision-making policy

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
  # Guard: skip sessions with empty tmuxName (old metadata files) — avoids false positives
  [ -n "$tmux_name" ] || continue
  # Check if the tmux session is still alive
  if tmux has-session -t "$tmux_name" 2>/dev/null; then
    pr=$(grep "^pr=" "$sfile" | cut -d= -f2 | grep -oE "[0-9]+$")
    echo "  ZOMBIE: $s (tmux=$tmux_name, PR=#$pr) — AO=killed but tmux still running"
  fi
done

# A4. Is the orchestrator launchd service running? (ao-pr-poller is DEPRECATED — check ai.agento.orchestrators instead)
echo "=== Orchestrator launchd service ==="
launchctl print gui/$(id -u)/ai.agento.orchestrators 2>/dev/null | grep -E "state|PID" | head -5 || echo "ai.agento.orchestrators: NOT REGISTERED"
tail -5 /tmp/ao-orchestrators.log 2>/dev/null || echo "No orchestrator log"

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

### Step 3b: Stalled PR detection (>1hr gap, not 6-green)

For every open PR, check last commit date and compare to current UTC time. Flag any PR that:
- Is NOT at 6-green (any of: CI failing, merge conflict, CR not APPROVED, unresolved comments, Bugbot blocking)
- Has >1 hour since the last commit with no visible progress

```bash
# Stall detection — REST API (works even when GraphQL=0)
current_epoch=$(date -u +%s)
echo "=== STALLED PR DETECTION (>1hr gap, not 6-green) ==="
for pr_json in $(gh api "repos/jleechanorg/agent-orchestrator/pulls?state=open" --jq '.[] | @base64' 2>/dev/null); do
  pr=$(echo "$pr_json" | base64 -d 2>/dev/null || echo "$pr_json" | base64 -D 2>/dev/null)
  number=$(echo "$pr" | jq -r '.number')
  title=$(echo "$pr" | jq -r '.title[0:60]')
  mergeable=$(echo "$pr" | jq -r '.mergeable_state')
  branch=$(echo "$pr" | jq -r '.head.ref')

  # Get last commit date
  last_commit=$(gh api "repos/jleechanorg/agent-orchestrator/pulls/$number/commits" --jq '.[-1].commit.committer.date' 2>/dev/null)
  commit_epoch=$(date -u -j -f "%Y-%m-%dT%H:%M:%SZ" "$last_commit" +%s 2>/dev/null \
                 || date -u -d "$last_commit" +%s 2>/dev/null \
                 || echo 0)
  gap_mins=$(( (current_epoch - commit_epoch) / 60 ))

  # Get review state
  review_state=$(gh api "repos/jleechanorg/agent-orchestrator/pulls/$number/reviews" --jq '[.[] | select(.state != "COMMENTED")] | last | .state // "NONE"' 2>/dev/null)

  # Skip if already green enough (Gate 2 & 3 pass) — skeptic-cron should handle these
  if [ "$review_state" = "APPROVED" ] && [ "$mergeable" = "CLEAN" ]; then
    continue
  fi

  # Flag if >60 min gap
  if [ "$gap_mins" -gt 60 ]; then
    # Check if worker session exists for this branch
    has_worker="no"
    for s in $(tmux list-sessions 2>/dev/null | grep -E "ao-[0-9]+|jc-[0-9]+" | cut -d: -f1); do
      s_branch=$(tmux capture-pane -t "$s" -p 2>/dev/null | grep -oE "Branch: [^ ]+" | tail -1 | sed 's/Branch: //')
      [ "$s_branch" = "$branch" ] && has_worker="$s" && break
    done
    gap_hrs=$((gap_mins / 60))
    gap_min_rem=$((gap_mins % 60))
    echo "STALLED #$number | ${gap_hrs}h${gap_min_rem}m | review=$review_state | mergeable=$mergeable | worker=$has_worker | $title"
  fi
done
```

### Step 3c: 6-Green Rate — Zero-Touch PR Measurement

Measure how many merged PRs were truly autonomous. A PR is "zero-touch" ONLY if `merged_by` is `github-actions[bot]` (skeptic-cron auto-merge). Manual merges are NOT zero-touch.

```bash
# 6-Green rate + merge quality — last 7 days
echo "=== MERGE QUALITY AUDIT (last 7 days) ==="
cutoff=$(date -u -v-7d +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -d "7 days ago" +%Y-%m-%dT%H:%M:%SZ)
auto=0; manual=0; total=0
for pr_json in $(gh api "repos/jleechanorg/agent-orchestrator/pulls?state=closed&sort=updated&direction=desc&per_page=50" --jq "[.[] | select(.merged_at != null) | select(.merged_at > \"$cutoff\")] | .[] | @base64" 2>/dev/null); do
  pr=$(echo "$pr_json" | base64 -D 2>/dev/null || echo "$pr_json" | base64 -d 2>/dev/null)
  number=$(echo "$pr" | jq -r '.number')
  title=$(echo "$pr" | jq -r '.title[0:50]')
  merged_by=$(echo "$pr" | jq -r '.merged_by.login')
  total=$((total + 1))
  if [ "$merged_by" = "github-actions[bot]" ]; then
    auto=$((auto + 1))
    echo "  AUTO-MERGED #$number (by $merged_by) $title"
  else
    manual=$((manual + 1))
    echo "  MANUAL #$number (by $merged_by) $title"
  fi
done
echo ""
echo "TOTAL MERGED: $total | AUTO (skeptic-cron): $auto | MANUAL: $manual"
if [ "$total" -gt 0 ]; then
  rate=$((auto * 100 / total))
  echo "ZERO-TOUCH RATE: ${rate}% ($auto/$total auto-merged by skeptic-cron)"
fi
```

### Step 3d: Skeptic-cron correctness spot-check

Pick one APPROVED PR (if any exist) and verify skeptic-cron's gate checks agree with reality:

```bash
echo "=== SKEPTIC-CRON CORRECTNESS SPOT-CHECK ==="
# Find an APPROVED PR
APPROVED_PR=$(gh api "repos/jleechanorg/agent-orchestrator/pulls?state=open" --jq '.[] | select(.draft == false) | .number' 2>/dev/null | while read num; do
  state=$(gh api "repos/jleechanorg/agent-orchestrator/pulls/$num/reviews" --jq '[.[] | select(.user.login == "coderabbitai[bot]") | select(.state == "APPROVED")] | length' 2>/dev/null)
  if [ "$state" -gt 0 ]; then
    echo "$num"
    break
  fi
done)
if [ -n "$APPROVED_PR" ]; then
  echo "Spot-checking PR #$APPROVED_PR"

  # Gate 3: CR state — must filter to actionable reviews (APPROVED/CHANGES_REQUESTED), not COMMENTED
  CR_ACTIONABLE=$(gh api "repos/jleechanorg/agent-orchestrator/pulls/$APPROVED_PR/reviews" \
    --jq '[.[] | select(.user.login == "coderabbitai[bot]") | select(.state == "APPROVED" or .state == "CHANGES_REQUESTED")] | sort_by(.submitted_at) | last | .state // "none"' 2>/dev/null)
  CR_LATEST=$(gh api "repos/jleechanorg/agent-orchestrator/pulls/$APPROVED_PR/reviews" \
    --jq '[.[] | select(.user.login == "coderabbitai[bot]")] | sort_by(.submitted_at) | last | .state // "none"' 2>/dev/null)
  if [ "$CR_ACTIONABLE" != "$CR_LATEST" ]; then
    echo "  MISMATCH Gate 3: actionable=$CR_ACTIONABLE vs latest=$CR_LATEST (skeptic-cron uses latest — BUG)"
  else
    echo "  Gate 3 OK: $CR_ACTIONABLE"
  fi

  # Gate 5: Unresolved comments — REST has no isResolved
  REST_COMMENTS=$(gh api "repos/jleechanorg/agent-orchestrator/pulls/$APPROVED_PR/comments" \
    --jq '[.[] | select(.in_reply_to_id == null)] | length' 2>/dev/null)
  GQL_UNRESOLVED=$(gh api graphql -f query='query($owner:String!,$repo:String!,$pr:Int!){repository(owner:$owner,name:$repo){pullRequest(number:$pr){reviewThreads(first:100){nodes{isResolved}}}}}' \
    -f owner="jleechanorg" -f repo="agent-orchestrator" -F pr="$APPROVED_PR" \
    --jq '[.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved == false)] | length' 2>/dev/null || echo "graphql_failed")
  if [ "$REST_COMMENTS" != "$GQL_UNRESOLVED" ]; then
    echo "  MISMATCH Gate 5: REST root comments=$REST_COMMENTS vs GraphQL unresolved=$GQL_UNRESOLVED (skeptic-cron uses REST — BUG if REST>0)"
  else
    echo "  Gate 5 OK: $GQL_UNRESOLVED unresolved"
  fi

  # Check last skeptic-cron run
  LAST_CRON=$(gh api "repos/jleechanorg/agent-orchestrator/actions/workflows/skeptic-cron.yml/runs?per_page=3" \
    --jq '.workflow_runs[] | "\(.conclusion) \(.created_at[0:16])"' 2>/dev/null)
  echo "  Last skeptic-cron runs: $LAST_CRON"
fi
```

### Step 3e: Merged-PR zombie detection

For every active worker session, check if its associated PR is merged/closed. Workers on merged PRs are zombies burning tokens.

```bash
echo "=== MERGED-PR ZOMBIE DETECTION ==="
for sess in $(tmux list-sessions -F '#{session_name}' 2>/dev/null | grep -E '(ao|jc|wa|wc)-[0-9]+'); do
  pr_num=$(tmux capture-pane -t "$sess" -p 2>/dev/null | grep -oE "PR: #[0-9]+" | head -1 | grep -oE "[0-9]+")
  [ -z "$pr_num" ] && continue
  # Detect repo from session prefix
  case "$sess" in
    ao-*) repo="jleechanorg/agent-orchestrator" ;;
    jc-*) repo="jleechanorg/jleechanclaw" ;;
    wa-*) repo="$GITHUB_REPOSITORY" ;;
    wc-*) repo="jleechanorg/worldai_claw" ;;
    *) continue ;;
  esac
  merged=$(gh api "repos/$repo/pulls/$pr_num" --jq '.merged' 2>/dev/null)
  if [ "$merged" = "true" ]; then
    echo "  ZOMBIE: $sess on PR #$pr_num ($repo) — PR is MERGED, kill this session"
  fi
done
```

If zombies are found, kill them immediately — they waste tokens and block worker capacity.

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

### Stalled PRs (>1hr gap, not 6-green)
| PR | Gap | Review state | Mergeable | Worker | Title |
|---|---|---|---|---|---|
<List each stalled PR. If worker=no, this is a coverage gap requiring ao spawn.>
(If none, say "No stalled PRs ✓")

### Zombie session check
<Sessions where AO status=killed but tmux still alive — lifecycle-worker is NOT managing these>
| Session | AO status | tmux alive | PR | Action needed |
(If none, say "No zombie sessions ✓")

### AO session store vs tmux desync
<"ao session ls" result vs tmux count — if AO says 0 active but tmux has sessions, flag as desync>

### Lifecycle-worker duplicate check
<Count per project — only flag if SAME PROJECT has >1 worker. Multi-project = expected.>

### Recent Merge Quality (last 7 days)
For each recently merged PR, check and report:
| PR | merged_by | 6-green at merge? | Failing gates | Skeptic verdict |
|---|---|---|---|---|
| #NNN | github-actions[bot] / jleechan2015 | YES/NO | gates X,Y | PASS/FAIL/MISSING/SKIPPED |

- **merged_by=github-actions[bot]** = skeptic-cron auto-merged (true zero-touch)
- **merged_by=jleechan2015** = manual merge (NOT zero-touch regardless of commit prefixes)
- Always check 6-green (gates 1-6) separately from gate 7 (skeptic may be structurally impossible)

### 6-Green Rate (last 7 days)
| Metric | Value |
|---|---|
| Total merged | N |
| Auto-merged (merged_by=github-actions[bot]) | N (NN%) |
| Manual-merged (merged_by=human) | N (NN%) |
| Zero-touch (canonical: merged_by=github-actions[bot]) | N (NN%) |
<List zero-touch PRs by number>

### Root cause
<Primary reason the system is not progressing PRs autonomously>

### Recommended fix
<Concrete next step>
```

## Input

$ARGUMENTS
