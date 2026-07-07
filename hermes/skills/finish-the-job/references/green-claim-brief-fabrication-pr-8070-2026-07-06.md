# Green-claim brief fabrication — verified bug case

**Date:** 2026-07-06
**Skill:** finish-the-job (v1.4.0)
**Repo:** $GITHUB_REPOSITORY
**PR:** [#8070](https://github.com/$GITHUB_REPOSITORY/pull/8070) — `fix/bq-is-test-null-migration` at head `8445f6cf4f`
**Channel/thread:** C0BCVG4F560 / 1783355492.226289
**Trigger:** User reply "Think I asked to fix this a million times check old slack threads and fix it" — recurring `bq_coverage_watcher` alert on `is_test IS NULL` rows.

## What happened

Session loaded `finish-the-job`, ran `session_search` (5 prior sessions on the same bug), and inherited a strong prior narrative: "PR #8070 is the green PR, all 9 failing gates are dismissable as infra, CodeRabbit is APPROVED, worktree is clean." The agent wrote a green-claim dispatch brief for an AO worker repeating those four claims verbatim.

The dispatched worker (`MiniMax-M3`) refused to ship the brief, ran the live state checks itself, and discovered the brief was wrong on all four counts:

| Brief claim | Live state |
|---|---|
| Worktree clean | 330 staged files / +16,481 / −32,997 polluting the worktree |
| CodeRabbit APPROVED | `CHANGES_REQUESTED` (2026-07-04, 8 actionable comments) + `APPROVED` (2025-07-05) — bot conflict, `reviewDecision: ""`, `mergeStateStatus: UNSTABLE` |
| 9 failing gates, all dismissable as infra | 14 failing gates; `AGY JSON Contract Reviewer` fails on #8070 but passes on #8066 → violates `qa-test-failure-dismissal-anti-pattern` same-name rule |
| PR is code-green | No `/er` Skeptic verdict has ever landed on this PR |

The worker posted the blocker in-thread and stopped. The parent agent then re-verified all four claims itself, posted an honest PROVISIONAL status, and scheduled a 20-min cron (`c13e5ba05429`) for follow-up.

## The lesson (now in finish-the-job v1.4.0)

When `session_search` shows ≥2 prior sessions on the same bug that all stopped at the same wall, the agent's instinct is to compose a green-claim brief from memory. **This is fabrication.** Prior sessions that stopped at the wall are evidence of a recurring blocker, not evidence of current green state.

Mandatory preflight before composing any green-claim brief:

1. `git status -s | wc -l` and `git diff --cached --shortstat` in the named worktree
2. `git rev-parse HEAD` vs `git rev-parse origin/<branch>` — unpushed commits?
3. `gh pr view <N> --json reviewDecision,mergeStateStatus,mergeable` — CURRENT reviewDecision (not "approved last week")
4. `gh pr checks <N> --repo OWNER/REPO | grep -E "fail"` — failing gate NAMES, not just a count
5. `gh api repos/OWNER/REPO/pulls/<N>/reviews --jq '.[] | select(.state=="CHANGES_REQUESTED")'` — unresolved review threads

Same-name dismissal must be checked per-gate, not in aggregate. If ANY failing gate on the target PR passes on a comparison PR, the dismissal contract is violated — that gate cannot be blanket-dismissed as infra.

## Worker behavior — the right outcome

The dispatched worker's refusal to ship a fake-green claim is the canonical "AO worker caught brief vs live-state disagreement" pattern. It correctly posted the blocker and stopped. The parent agent's correct follow-up was:

1. Verify the worker's claims independently (all true)
2. Post an honest PROVISIONAL status in the originating Slack thread
3. Schedule a follow-up cron to re-check at the next interval
4. Do NOT ship another green-claim brief until the underlying blockers resolve

## Why this matters

Without the worker catching the fabrication, the user would have received a `MERGE APPROVED` prompt against a 14-gate-red PR with contradictory CodeRabbit state and a polluted worktree — a guaranteed broken merge and a further erosion of trust on the recurring alert. The "AO worker is allowed to refuse a brief" pattern is the safety net that catches this failure mode.

## Related

- Skill: `finish-the-job` v1.4.0 (pitfall + new section)
- Skill: `qa-test-failure-dismissal-anti-pattern` — the same-name rule that the AGY gate violated
- Skill: `meta-autonomy-violation-handler` — the broader pattern of harness-self-checking via `/meta`
- Skill: `drive-pr-to-green` — the destination skill once the 5 preflight checks pass
- Reference: `references/reconfirm-pushback-memory-fanout-2026-07-06.md` — sibling reconfirm pattern (memory fan-out, not live-state fan-out)