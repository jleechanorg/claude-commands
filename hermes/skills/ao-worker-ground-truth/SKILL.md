---
name: ao-worker-ground-truth
version: 1.0.0
description: |
  Diagnose "is AO actually working?" by cross-referencing live OS processes,
  the AO database (`~/.ao/data/ao.db`), and GitHub PR commit history — bypassing
  the `ao-progress-reporter.sh` and MCP Agent Mail daily report, both of which
  can show stale or fabricated session data. Use when user asks "is AO working?",
  "are AO workers finishing?", or "the daily report shows N stalled".
---

# AO Worker Ground Truth — bypassing stale reports to verify real progress

## Why this skill exists

There are **three independent sources** for "what AO workers are doing," and
each can lie in a different way:

| Source | Can be wrong because |
|---|---|
| `~/.hermes/scripts/ao-progress-reporter.sh` daily Slack report | Only classifies sessions with `branch` + `repo` recorded. Sessions with `branch=""` fall through invisibly and aren't reported. |
| MCP Agent Mail `U0A4G7LDJ4R` "AO Progress Report" thread | Uses fabricated `wa-NNNN` IDs that don't match any row in `~/.ao/data/ao.db`. Verified 2026-07-23 — bead `orch-1oli`. |
| `ao session ls` (canonical AO DB) | Has real session IDs but lacks `branch`/`prNumber` for most sessions. |

When the user asks "is AO working?" or "is PR #N actually being driven?", the
right move is **don't trust any of those three alone**. Instead, triangulate
from a 4th source: **the actual OS processes running on the machine**, plus
the **GitHub PR commit history** for the PRs those processes reference.

## The 4-step ground-truth recipe

### Step 1 — Count live AO workers by project

```bash
ao session ls --json | python3 -c "
import json, sys
d = json.load(sys.stdin)
sessions = d.get('data', [])
live = [s for s in sessions if not s.get('isTerminated')]
print(f'Live AO workers: {len(live)}')
by_proj = {}
for s in live:
    p = s.get('projectId', '?')
    by_proj.setdefault(p, []).append(s['id'])
for p, ids in sorted(by_proj.items()):
    print(f'  {p}: {len(ids)} ({ids[:5]}{\"...\" if len(ids) > 5 else \"\"})')
"
```

### Step 2 — Map live OS processes to PR/bead IDs (THE KEY STEP)

```bash
ps aux | grep -E "(claude|agy|codex).*--prompt-interactive" | grep -v grep \
  | grep -oE 'PR #[0-9]+|$USER-[a-z0-9]+|feat/[a-zA-Z0-9_-]+|fix/[a-zA-Z0-9_-]+' \
  | sort | uniq -c | sort -rn
```

This is the diagnostic that bypasses the AO DB's `branch=""` gap entirely.
Every long-running AO worker has a `--prompt-interactive` invocation whose
embedded brief names the target PR + bead. Pulling the strings out of `ps aux`
gives you the **actual current work assignments** without depending on AO's
session-tracking state.

If the user asked "is PR #8178 being driven?" and this command shows a
`PR #8178` token in some process's args, the answer is **yes, right now**.

### Step 3 — Cross-reference with GitHub PR commit history

For each PR the user cares about:

```bash
for pr in 8178 8177 8511 8428; do
  echo "=== PR #$pr ==="
  gh api "repos/jleechanorg/<repo>/pulls/$pr/commits" | python3 -c "
import json, sys, datetime
d = json.load(sys.stdin)
now = datetime.datetime.now(datetime.timezone.utc)
for c in d[-5:]:
    sha = c.get('sha', '')[:10]
    date = c.get('commit', {}).get('author', {}).get('date', '')
    msg = (c.get('commit', {}).get('message', '') or '').split('\n')[0][:80]
    if date:
        dt = datetime.datetime.fromisoformat(date.replace('Z', '+00:00'))
        age_h = (now - dt).total_seconds() / 3600
        print(f'  {sha} {age_h:7.1f}h ago  {msg}')
"
done
```

This is the second half of the triangulation: even if `ps aux` shows nothing
(the worker was killed, or is between spawn and first prompt), a fresh commit
on `origin/<branch>` proves the worker was active minutes ago.

**Key sanity check:** if the daily report says "PR #8511 idle 49h21m" but this
command shows the head commit is 1.0h old, the daily report is wrong. Do not
trust the report — trust GitHub.

### Step 4 — Cross-check the AO DB's `pr` table for canonical state

```bash
sqlite3 ~/.ao/data/ao.db \
  "SELECT number, pr_state, ci_state, mergeability, source_branch, updated_at
   FROM pr WHERE number IN (8178, 8177, 8511, 8428) ORDER BY updated_at DESC;"
```

If the PR is in the `pr` table, AO has attached itself to it (`ao claim-pr`
was called at some point). If the PR is NOT in the table but appears in
`ps aux` Step 2 output, the worker is mid-flight on a fresh PR without a prior
`claim-pr`. That's normal and expected.

## Worked example — 2026-07-23 incident

**User asked in thread C0ALSKLU9KM/p1784792447.282019:**

> "Is AO actually working? Look at slack history and see if these AO
> dispatches ever finished their work."

**MCP Mail report said:**
- `wa-3359`: PR open @ `72b4a1a`, off-track, idle 65h48m
- `wa-3361`: PR open @ `aa92321`, Green Gate FAILURE, idle 63h3m
- `wa-3364`: PR #8511, off-track, idle 49h21m
- `wa-3365`: PR #8428, on-track, beads-jsonl-validation IN_PROGRESS

**Ground truth recipe output:**

| Source | Result |
|---|---|
| Step 1 (`ao session ls`) | 32 live workers; `worldarchitect-79`, `-88`, `-89` all `no_signal` with `branch=""` |
| Step 2 (`ps aux`) | 15+ processes with `--prompt-interactive` containing `PR #8178`, `PR #8177`, `PR #8428`, `PR #8466`, `PR #8477`, `PR #8527`, `PR #8529`, `PR #8530`, `PR #63`, `PR #8116` |
| Step 3 (GitHub) | PR #8511 last commit **1.0h ago**; PR #8428 last 3 commits **1.5–1.6h ago** |
| Step 4 (`pr` table) | PRs #8178, #8177, #8511, #8428 are **NOT in the `pr` table** — AO never `claim-pr`'d them |

**Verdict:** AO IS working. 15+ workers are actively pushing commits to the
PRs the daily report called "stalled." The daily report is wrong because:
1. MCP Mail uses fabricated `wa-NNNN` IDs that don't map to real sessions.
2. The local reporter falls through on `branch=""` workers.
3. The AO `pr` table is empty for in-flight PRs (AO never claimed them).

## Anti-patterns

- **Do NOT trust `wa-NNNN` IDs from MCP Mail.** Verify against `ao session ls`
  and the SQLite `sessions.issue_id` column first. If the ID isn't in either,
  it's fabricated.
- **Do NOT trust "idle N hours" claims without checking GitHub.** Green Gate
  workflow idle time is NOT worker idle time — a PR at head SHA `X` for 7 days
  is **waiting for CI**, not stalled.
- **Do NOT spawn a new worker when the diagnostic shows the existing one is
  alive and pushing.** "Idle in MCP report" + "fresh commits in git log"
  means the report is wrong, not the worker. Fix the report; don't dispatch.
- **Do NOT depend on the AO `pr` table for in-flight PRs.** AO workers
  routinely push to PRs without `claim-pr` first; the `pr` table only
  reflects explicit claims, which is a strict subset of real work.

## Related skills

- `agento` — how to dispatch + monitor AO workers (canonical CLI surface).
- `agento_report` — getting a PR-status snapshot; doesn't validate against
  live processes (use this skill instead when the user says "really" or
  "actually").
- `mcp-agent-mail-no-slack-bridge/references/two-identity-slack-routing.md` —
  documents the `wa-NNNN` fabrication specifically; this skill documents the
  ground-truth recipe that bypasses it.
- `slack-thread-routing-investigation` — Failure 5 (wrong thread_ts from
  session context header) compounds with this: the same header that misroutes
  your reply can also be the source of the `wa-NNNN` data you're verifying.
