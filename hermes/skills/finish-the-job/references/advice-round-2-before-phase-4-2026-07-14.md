# /advice Round 2 — mandatory before Phase 4 on any docs/contract change (2026-07-14)

**Verified incident:** jleechanorg/claude-commands PR #321, commit `7c5031623`
("fix(sidekick,swarm): add mandatory 5-minute checkpoint cadence + safe-commit
contract"), Slack thread C09GRLXF9GR/1784055266.958369.

## The failure pattern

A docs/contract change was shipped to PR #321's head branch with 6/6 contract
tests passing. The tests were presence-only assertions (regex match + token
presence). The contract "passed" without verifying the actual mechanism. A
follow-up `/advice` Round 2 (delegate_task subagent as Reviewer A) caught
**13 issues — 4 of them real shipping blockers**:

| # | Issue | Severity |
|---|-------|----------|
| 1 | `br sync` alone is DB↔JSONL sync — does NOT update the bead body. Docs claimed `br sync` "syncs the P1 resumption bead". Wrong. The correct sequence is `br update <id> --append ...` then `br sync` to flush. | **Blocker** |
| 2 | `tmux respawn-pane -t $SESSION` (without `-k`) only reactivates an exited pane and is not a timer. Docs presented it as a recurring-heartbeat primitive. | **Blocker** |
| 3 | The ≤5-min "crash window" guarantee was unconditional. STATE.md in `/tmp` does not survive host reboot / `/tmp` cleanup / parent-CLI death. Needed scoping to "LIVE session" + a fallback to P1 bead + external AO/launchd supervisor for absolute durability. | **Blocker** |
| 4 | `/team-claude.md` was outside the test's read set. Same crash-window + commit-safety risk; the test would have passed with team-claude carrying zero contract. | **Blocker** (parity gap) |
| 5 | "Sidekick AND every lane" vs "supervisor AND every lane owner" — inconsistent actor naming across the three docs. | Tightening |
| 6 | P1 bead called "resumption bead" in one doc, "mission bead" in another. | Terminology |
| 7 | No single-writer rule — concurrent lane owners could clobber the bead body. | Tightening |
| 8 | Gitignored `.tmp/` caveat present in 2 of 3 docs. | Tightening |
| 9 | Non-repo mission fallback path stated in 1 of 3 docs. | Tightening |
| 10 | Commit-safety escape hatch described in 1 of 3 docs (others linked, didn't inline). | Tightening |
| 11 | Test for /sidekick command accepted any `br` token (`assert "br sync" or "br"`), trivially passable. | Test weakness |
| 12 | Test did not require literal `≤5 min` budget text. | Test weakness |
| 13 | /team-claude parity test missing entirely. | Test weakness |

Each blocker became a real shipping bug if PR #321 had merged without the
follow-up commit. The follow-up commit `1a43307a0` addressed all 13, pushed
2 commits ahead of the original PR head, and 7/7 tests now pass on the
committed + remote state.

## The /advice docs-accuracy template (filled out for the incident)

```markdown
# /advice Decision + Artifact

## DECISION
Docs X/Y/Z were modified in commit <SHA> on PR #<N> at jleechanorg/<REPO>;
need a second opinion on (a) whether the contract is internally consistent
across the docs and the test, (b) whether the contract is achievable as
written, (c) whether anything was fabricated or contradicts existing context.

## ARTIFACT (≤150 lines, claim-bearing excerpts only)
[Paste ONLY the new contract paragraphs from each doc + the load-bearing
source files. Drop boilerplate. Drop "Install" sections. Drop config tables.]

### Doc §"<name>" — claim-bearing excerpts
> [quote 1-3 sentences that make a verifiable claim]

### Source: <path>:<line>
[the actual source code, tmux man page, br --help output, etc.]

## QUESTIONS FOR THE REVIEWER
1. Internal consistency: do the docs use the SAME cadence, sub-actions,
   and escape hatches?
2. Achievability: is the cadence realistically drivable? Identify any step
   that would NOT work as written.
3. Test↔doc consistency: do the test assertions match what the docs say?
4. Missing callout: hazards not surfaced in any of the docs.
5. Fabrication check: parent context — does the doc ELSEWHERE already say
   something CONTRADICTING the new contract?
6. Parity gap: are there sibling files (e.g. /team-claude alongside
   /sidekick) that operate the same machinery and are NOT covered by
   the test?

## DELIVERABLE
Return VERDICT + REASONING + RISK + CONFIDENCE, plus a numbered list of
every inaccurate / inconsistent / fabricated / missing claim with file:line
citations.
```

## The recipe — 4 lines, embedded in Phase 4

1. After pushing the docs/contract commit + verifying tests pass locally,
   run `delegate_task(goal="Senior engineer second opinion — docs accuracy
   against source", toolsets=["terminal","file"])` with the docs-accuracy
   template above. Use `delegate_task` (Hermes-adapted Reviewer A), not
   `claude -p` (not logged in on this machine) or cursor (not installed).
2. Wait for the verdict. If `docs need fixes (list)` — treat each numbered
   item as a real bug, not a stylistic suggestion. The 2026-07-14 incident
   had 4 blockers that would have shipped if /advice Round 2 was skipped.
3. Re-patch the docs/tests, commit + push the follow-up, RE-RUN the contract
   test, then post the Phase 4 reply with the BEFORE/AFTER commit SHAs.
4. Update the bead close-reason with both SHAs and the verdict.

## When to skip /advice Round 2

- Trivial 1-file docs fix where the new paragraph has zero mechanism claims
  (e.g. a typo, a link fix, a rephrasing).
- Pure code changes with no docs added — the contract test IS the review.
- Tests that already cross-reference sibling files AND assert literal
  mechanism strings (not just presence tokens).

When in doubt, run it. /advice Round 2 costs ~5–10 tool calls (one
delegate_task fan-out). Skipping it and shipping a thin contract costs
the user a re-review cycle + the agent's trust.

## Cross-references

- `~/.hermes/skills/advice/SKILL.md` — canonical Reviewer A fallback chain
  (delegate_task → agy → codex → claude). On this machine, A1 = delegate_task
  is the cheap first move.
- `~/.hermes/skills/finish-the-job/SKILL.md` §"Declared done before /advice
  Round 2 caught the contract gaps" — the in-body pitfall this reference
  supports.
- `~/.hermes/SOUL.md` — "Apply /advice Round 2 (independent, no bot cite)
  before declaring done" — the user-preference memory note that prompted
  this skill patch.