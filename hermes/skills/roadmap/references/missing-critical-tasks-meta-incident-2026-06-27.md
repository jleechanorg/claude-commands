# Missing critical tasks — meta-incident 2026-06-27

**Verified 2026-06-27 03:42 PT (this session).** The 0228 PT `/roadmap`
run classified three high-priority threads as `Defer (in-flight)` —
even though the diagnostic work was done, the GitHub issues were filed,
and the one-line fixes were waiting to be implemented. This document is
the durable record of what went wrong and how to keep it from
happening again.

## The trigger

Jeffrey's meta-question at 03:40 PT:

> "Arent there some high pri tasks like the mobile latency stuff?
> Why did /roadmap miss this?"

The bot reply at 03:41 PT (`C09GRLXF9GR / 1782531667`) acknowledged the
failure but then *attempted to drive the tasks immediately* — which is
the opposite of what Jeffrey asked. He said **"Meta investigation …
Fix the roadmap skill don't do the actual tasks."**

This is the pattern: when a meta-question arrives, the right answer is
**fix the system, not the symptoms**. The next two sections are the
fix.

## The 3 critical threads that 0228 missed

All three are in `C0AH3RY3DK6` (your-project.com companion channel),
which IS in the cron scope — so channel scoping was not the bug.

### Thread 1 — `C0AH3RY3DK6 / 1782335045` (cold-start, 28-44s on /)

**State at 0228 PT:** classified `Defer (in-flight)`.
**Reality at 0228 PT:**
- 8+ bot diagnostic messages in the thread with a finished root-cause
  analysis: `infrastructure/worker_config.py:23` has buggy
  `2 * cpu_count() + 1 = 17 workers` formula on 4-vCPU with
  `startup-cpu-boost=true`.
- One-line fix `GUNICORN_WORKERS=1` had been recommended in 3 prior
  sessions but never applied.
- Codex `/advice` consult was running 25 min before the audit.
- **Issue #7961** had been filed 1h before the audit with full
  reproduction, prior-art (closed-not-merged PRs #7748, #7756, #7727,
  #7728, #7575), and a ranked fix list.
- Same thread had been appearing as `Defer (in-flight)` in 5 consecutive
  reports (`2026-06-24-2005`, `2026-06-25-2041`, `2026-06-26-1856`,
  `2026-06-26-1405`, `2026-06-27-0228`).

### Thread 2 — `C0AH3RY3DK6 / 1782341232` (experience issues)

**State at 0228 PT:** classified `Defer` with "gh issues for all these
items/ideas" as the next step.
**Reality at 0228 PT:**
- Issues **#7963, #7964, #7965, #7966, #7967** were filed 20 min before
  the audit ran (00:45 PT). The "next step" was already done — and the
  next step should have been "spawn a PR-implementation worker for each
  issue," not "defer."
- This thread produced the most actionable retention findings of the
  week: the 20-turn daily cap fires mid-cliffhanger with no in-product
  signal, 8/8 cohort users churned after hitting it, the level-up
  ceremony never fires for real users because the XP curve is too
  steep.

### Thread 3 — `C0AH3RY3DK6 / 1782447664` (chrome incognito login slow)

**State at 0228 PT:** classified `Defer to next cycle (will route to
GCP-logging-triage skill)`.
**Reality:** Same root cause as Thread 1 (cold-start, not login). Routing
to `gcp-logging-triage` would have confirmed this in <2 min via the
cold_start_latency_report.sh diagnostic — but the audit never ran the
diagnostic, it just deferred.

## The 5 failure modes

### 1. Issue + thread JOIN missing

The 0228 run's pipeline (per `skills/roadmap/SKILL.md` step 5) joined
threads to **PRs only**:

```bash
gh pr list --repo <active-repo> --state open --json ...
```

It never joined to **GitHub issues**. Issues #7961 and #7963–7967 were
filed against `$GITHUB_REPOSITORY` but invisible to the audit
because no PR existed.

**Fix:** Step 2.5.a (mandatory issue join before classification).

### 2. `incidental` classification trap

The classification rules let a thread be marked `incidental` (bot-only /
status-ping / no decision content) when:
- The thread had 8+ bot messages
- The thread contained finished diagnostic output
- The thread had a "Root cause:" or "Smoking gun:" line
- The thread referenced a specific file path + line number

All four triggers SHOULD have forbidden `incidental`, but the skill had
no rule against it. The cold-start thread satisfied three of the four.

**Fix:** Step 2.5.b (forbid `incidental` for threads with diagnostic
content).

### 3. `Defer (in-flight)` as a sink

The skill let a thread be marked `Defer (in-flight)` with no in-flight
evidence. The cold-start thread was marked `Defer (in-flight)` while:
- No PR existed
- No AO worker was active on the relevant issue
- No recent commit touched `worker_config.py`

**Fix:** Step 2.5.c (require one of three proofs: PR, active worker, or
recent commit).

### 4. No recurring-stuck alarm

The cold-start thread had been appearing as `Defer (in-flight)` in 5
consecutive reports over 3 days. The skill had no rule to escalate
recurring `Defer` items. The bot treated each run's `Defer` as a fresh
decision rather than as a signal that the previous Defer was wrong.

**Fix:** Step 2.5.d (alarm at ≥ 2 consecutive reports without
resolution, surface as `STUCK` in § C).

### 5. Bot "PR is ready" claim accepted unverified

Multiple bot replies in the audit window contained "✅ PUSHED",
"✅ filed", or "✅ merged" without verifiable artifacts (no commit SHA,
no PR URL, no `git show` output). The skill accepted these at face
value and marked the corresponding threads as `finished` or
`Defer (in-flight)` with "next step already done."

**Fix:** Step 2.5.e (require verifiable artifact or run pre-flight
verification before accepting any "✅" claim).

## The bigger pattern — "investigations without PRs"

This incident surfaced a general class the audit never caught before:
**threads where the agent has finished the investigation but not
shipped the fix**. The audit language is PR-centric (`MERGEABLE`,
`behind_by`, `isDraft`), so investigations without PRs fall through the
classification entirely.

The 5-rule Step 2.5 fix is a partial answer. A deeper fix would be to
add an explicit `INVESTIGATION-COMPLETE-NO-PR` state to the
classification rules, but that's deferred to a follow-up commit.

## Verification — what changed

The fix commit on `jleechanorg/jleechanclaw` `origin/main` adds Step
2.5 (5 sub-rules) to `skills/roadmap/SKILL.md`. Five-rail closure
contract:

1. `~/.hermes/skills/roadmap/SKILL.md` — staging PRESENT
2. `~/.hermes_prod/skills/roadmap/SKILL.md` — prod PRESENT
3. Tracked by git (`git ls-files`)
4. On `origin/main` (`git show origin/main:<path>`)
5. Last commit SHA logged

Cross-references:

- `skills/roadmap/SKILL.md` Step 2.5 — the patch itself
- `skills/roadmap/SKILL.md` "Verified meta-incident instance — 2026-06-27
  03:42 PT" — the durable record in the skill body
- `jleechanorg/roadmap` `2026-06-27-0342-missing-critical-tasks-meta-incident.md`
  — the roadmap-repo copy (next section)

## Roadmap-repo copy

This same writeup is mirrored to `jleechanorg/roadmap` as
`2026-06-27-0342-missing-critical-tasks-meta-incident.md` so the
incident is searchable from the same surface the reports live on.

## Related

- `references/before-nextsteps-verify-current-state.md` — pre-flight
  gate that should have caught this but ran AFTER classification
- `references/iteration-budget-three-field-trap-2026-06-27.md` — a
  sibling incident from the same thread (different trap, same general
  "trust the prior agent's snapshot" failure mode)
- `skills/roadmap/SKILL.md` Step 8.5 — the `/a fullrun` drive phase
  that should have caught the cold-start PR but didn't, because the
  thread wasn't classified as `MERGEABLE` to begin with