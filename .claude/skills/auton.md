# Autonomy Diagnostic Skill

## Purpose

When invoked, diagnose WHY the jleechanclaw + AO system is NOT autonomously driving PRs to 6 green and merged. The system is supposed to do this without human intervention — if it isn't, something is broken.

## Read first (mandatory before answering)

1. `~/.openclaw/CLAUDE.md` — repo goals, PR green definition, autonomy target
2. `~/.codex/AGENTS.md` — agent policies
3. `~/.openclaw/agent-orchestrator.yaml` — AO project config (worktreeDir, backfillAllPRs, notifiers)
4. `~/.openclaw/scripts/ao-pr-poller.sh` — the polling loop (spawn, green-check, merge)
5. `~/.openclaw/SOUL.md` — openclaw decision-making policy

## The system's intended behavior

```
ao-pr-poller (every 5 min)
  ↓ detects non-green PR
  ↓ spawns agento session (ao spawn --claim-pr)
  ↓ agento: reads comments, fixes code, pushes
  ↓ agento: posts @coderabbitai all good?
  ↓ agento: runs /er evidence review
  ↓ CI passes, CR APPROVED, Bugbot neutral, comments resolved
  ↓ poller detects all 6 green → gh pr merge --squash --auto
```

**Full autonomy means: idea in → merged PR out, zero human clicks.**

## Diagnostic questions (answer each with evidence)

### 1. Is the poller running?
```bash
launchctl list ai.ao-pr-poller
tail -20 /tmp/ao-pr-poller.log
```

### 2. Is AO lifecycle-worker running?
```bash
launchctl list com.agentorchestrator.lifecycle-jleechanclaw
tail -20 /tmp/ao-lifecycle-jleechanclaw.log
```

### 3. Are sessions being spawned?
```bash
tmux list-sessions | grep -E "^[0-9a-f]+-jc-"
tail -50 /tmp/ao-pr-poller.log | grep -E "Spawning|SUCCESS|WARNING|SKIP"
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
tail -100 /tmp/ao-pr-poller.log | grep "not green"
```

### 6. Is CR rate-limited?
```bash
gh api repos/jleechanorg/jleechanclaw/issues/comments?per_page=5 | \
  python3 -c "import json,sys; [print(c['user']['login'],c['body'][:100]) for c in json.load(sys.stdin) if 'rate limit' in c['body'].lower()]"
```

### 7. Is the 6-green check working correctly?
```bash
PYTHONPATH=~/.openclaw/src python3 -m orchestration.merge_gate jleechanorg jleechanclaw <PR_NUM> --json
```

### 8. Is the stray-worktree bug blocking spawns?
```bash
git -C ~/.openclaw worktree list | grep -v "~/.openclaw\b\|~/.worktrees"
# Any /private/tmp/ or unexpected paths = stray worktree blocking new spawns
```

## Common failure modes

| Symptom | Root cause | Fix |
|---|---|---|
| Sessions spawn but die immediately | `--claim-pr` fails (stray worktree) | `git worktree prune`, clear stale paths |
| Sessions alive but no pushes | Agent hits rate limit or auth failure | Check agent logs, re-auth |
| CR never APPROVED | Rate limited (too many PRs) | Wait for limit reset, or reduce simultaneous PRs |
| 6-green check passes but no merge | `gh pr merge` cmd failing or auto-merge disabled | Check poller merge logic + branch protection |
| PRs cycling CR changes_requested | Agent not reading CR comments correctly | Check agento's comment-reading skill |
| Spawned sessions are idle shells | `is_agent_alive_in_session` returns false | Check openclaw gateway is running on port 18789 |

## Output format

```
## Autonomy Diagnostic — <date>

### System health
- Poller: RUNNING / STOPPED / ERRORING
- AO lifecycle-worker: RUNNING / STOPPED
- Active jc-* sessions: N (M with live agents)
- Open PRs: N total, N non-green

### Per-PR status
| PR | Non-green reason | Session | Session state |
|---|---|---|---|
| #NNN | <reason from log> | jc-NNN | alive/zombie/none |

### Root cause
<Primary reason the system is not progressing PRs autonomously>

### Recommended fix
<Concrete next step>
```
