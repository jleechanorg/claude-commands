# v2.5.9 — Inline `/advice` Gate-3 substitute + rebase-onto-`origin/main` for fork-divergent patch anchors

Verified 2026-07-21 on jleechanorg/dark-factory PR #407 (`receipt-gate-reviewer` branch at `f461f93da3c5a68397272f00a361d1defa218dfe`).

## Why this addendum

The session the user invoked was: "Read this for factory patch" (port a Slack-attached `.patch` to a PR — covered by `github/patch-port-protocol`) followed by "Lets iterate until /green and /er and /advice approved fullrun" (drive the PR to N-green — THIS skill).

The bring-to-green phase hit two failure modes that v2.5.0-v2.5.8 do not cover:

1. **All 3 official review bots unavailable** (CodeRabbit org-wide rate-limited per `codex-path-deletion-guard` SOUL.md note + Cursor usage-limited + Codex code-review quota exhausted). v2.5.7's babysit-cron path is correct but adds 51-55 min latency; an inline `/advice` subagent fan-out can satisfy Gate-3 in <60 sec when the user is waiting in the thread.
2. **PR head branch was created from a fork-divergent HEAD** (`eae7413` in `~/repos/jleechanorg/dark-factory` vs `origin/main` at `8fc167899`, 39 commits ahead). The patch's context drifted between those two anchors because the fork HEAD pre-dates two helper-relocation commits (#297 moved `_enforce_outcome_verdict_consistency` from `handler_parallel_reviewer.py` to `handler_verdict.py`; #301 broke a circular import). Force-pushing-without-rebase left the PR `mergeable=CONFLICTING`; rebasing required resolving 2 conflict zones in each of 2 files.

## (a) Inline /advice Gate-3 substitute recipe

### Pre-flight: verify all 3 bots are unavailable

```bash
gh pr checks N --repo OWNER/REPO
# Look for the triple-failure signature:
#   CodeRabbit    fail    "Review rate limited"
#   Cursor Bugbot skipping "usage limit reached"
#   chatgpt-codex-connector skipping "Codex usage limits"
```

When all three are unavailable, the v2.5.7 babysit cron recipe (`hermes cron create "55m" --name babysit-pr-N-...`) is the production-correct path — but it adds 55 min of cron-wait latency. For a single PR being driven in-thread with the user waiting, an inline `/advice` fan-out is faster and still satisfies `green.md` Step 3.4's Gate-3 substitute policy.

### Recipe

```bash
# 1. Capture the diff + the working-tree state
gh pr diff N --repo OWNER/REPO > /tmp/pr-N.diff
git -C /tmp/<repo>-worktree rev-parse HEAD  # for the artifact
git -C /tmp/<repo>-worktree log --oneline origin/main..HEAD

# 2. Fan out 2-3 subagents in parallel. The Hermes /advice overlay
#    (skill_view name='advice') provides the templates. At minimum:
#    - Reviewer A (source-accuracy): verify regex/wiring/calls, cite file:line
#    - Reviewer B (architecture): verify opt-in patterns match sibling attrs,
#      ordering, audit-chain semantics
#    Optional: Reviewer C (adversarial: 9-vector probe for sandbox/fork/edge cases)

# For dark-factory PR #407 the prompt template (verbatim) was:
delegate_task(goal='Reviewer A: source-accuracy review of PR #407 ...',
              context='Patch at /tmp/df-pr-407.diff (15KB), working tree at /tmp/df-receipt-gate-worktree, branch receipt-gate-reviewer at 863f357 on origin/main 8fc167899. Changed files: runner/handler_verdict.py (regexes + _reproduction_receipt_gap), runner/handler_parallel_reviewer.py (new helpers + wiring), tests/test_reviewer_reproduction_receipt.py (34 cases). Pre-flight: md5 + ast.parse each file. Deliver: VERDICT + REASONING + RISK + CONFIDENCE + NUMBERED FINDINGS (file:line + problem + fix).',
              toolsets=['terminal','file','search_files'])

# 3. Synthesize verdict per advice SKILL.md "Pinned synthesis output format" (added 2026-07-15):
#
#    ### Recommended next action (one tap)
#    [one shell command OR "no action — PR is ready at the standard green gate"]
#    ### Evidence table
#    | Bug-report claim (file:line) | PR/fix evidence (file:line) | Test coverage |
#    ### Reviewers consulted
#    - Reviewer A (source accuracy, model X): verdict + confidence
#    - Reviewer B (external docs, model Y): verdict + confidence
#    - Reviewer C (adversarial, model Z): verdict + confidence
#    ### Disagreements not resolved
#    🧠 Memories used: [...]
#
# 4. If verdict is NEEDS-FIXES (cosmetic/clarity, not blocking) — apply inline
#    as a follow-up commit on the same PR branch per advice SKILL.md
#    "middle-ground" pattern (proven PR #8467 2026-07-20):
#    - Most-impactful findings first (boundary mismatches → duplicate labels
#      → terminology drift → ortho/canon notes)
#    - Each finding = <10 line inline patch
#    - Run pytest on the affected test files BEFORE committing
#    - Document the rest as known follow-ups in a PR comment
#    - DO NOT spin up a fresh AO worker for these — the PR already exists,
#      the work is in-place, an AO spawn burns quota on a duplicate diff
#    - Re-push (NOT force-push if the original commits survived; force-push
#      with --force-with-lease only if you rebased)
```

### PR #407 outcome from this recipe

- Reviewer A (MiniMax-M3, source-accuracy): APPROVED-as-is @confidence high
- Reviewer B (MiniMax-M3, architecture): NEEDS-FIXES @confidence high (3 numbered findings, 1 substantive)
- Findings applied as commit `f461f93`:
  1. `_receipt_required_flag` now accepts `int 1` (mirrored `_gate_strict_flag` exactly)
  2. `_enforce_reproduction_receipt` no longer clobbers pre-existing `original_verdict` set by `_enforce_outcome_verdict_consistency`
  3. Two new tests added (int=1 case + audit-chain preservation case)
- Final test count: 70/70 (was 68 pre-/advice; +2 from the new test cases)
- Final diff: `+331/-2` across 3 files

## (b) Rebase-onto-`origin/main` for fork-divergent patch anchors

### Pre-flight: detect the drift

```bash
# Check whether the PR's head branch is on the same SHA as origin/main
git -C /tmp/<repo>-worktree merge-base HEAD origin/main
git -C /tmp/<repo>-worktree log --oneline origin/main..HEAD | wc -l  # > 0 means drift
gh pr view N --repo OWNER/REPO --json mergeable --jq '.mergeable'
# "MERGEABLE" = no conflict (rebase not strictly needed, but base-SHA note still goes in PR body)
# "CONFLICTING" = rebase required
```

For PR #407, the head branch was anchored at `eae7413` (39 commits behind `origin/main` `8fc167899`). The 5 commits between them included:

- `#297 — relocate _enforce_outcome_verdict_consistency into handler_verdict` — moved the helper from `handler_parallel_reviewer.py` to `handler_verdict.py` (the canonical home)
- `#301 — break handler_parallel_reviewer circular import` — added the `_handlers_shim` re-export pattern

These two commits directly conflict with the patch's intent (the patch was authored against the pre-#297 layout).

### Recipe (verified on PR #407)

```bash
cd /tmp/<repo>-worktree
git fetch origin main
git rebase origin/main
# → CONFLICT blocks in 2 files (handler_verdict.py + handler_parallel_reviewer.py)

# Step 1: handle the helper module that RECEIVED the relocation (handler_verdict.py)
# The patch's `_reproduction_receipt_gap` belongs HERE, alongside the moved helper.
# Keep HEAD's full `_enforce_outcome_verdict_consistency` AND add the patch's new code.
# Conflict zone shape: <<< HEAD / === / >>> bcfa629 (the patch's commit)
# Resolution: keep both sides (HEAD's relocated function + bcfa629's receipt gap logic).

# Step 2: handle the helper module that ORIGINALLY contained the function
# (handler_parallel_reviewer.py).
# The patch's local copy of `_enforce_outcome_verdict_consistency` is now a DUPLICATE
# and must be DROPPED. KEEP the patch's NEW helpers (`_receipt_required_flag`,
# `_enforce_reproduction_receipt`) and their call sites.
# At every call site that USED to invoke the local copy: switch to the shim form
# `_handlers_shim._enforce_outcome_verdict_consistency(...)` instead of the
# unqualified name. The shim re-exports from `handler_verdict` so the
# unqualified name still resolves.

# Step 3: verify conflict markers are gone
for f in runner/handler_verdict.py runner/handler_parallel_reviewer.py; do
  python3 -c "import ast; ast.parse(open('$f').read()); print('$f syntax OK')"
  grep -c '<<<<<<<\|=======\|>>>>>>>' $f  # MUST return 0
done

# Step 4: complete the rebase
git add runner/handler_verdict.py runner/handler_parallel_reviewer.py
git rebase --continue

# Step 5: re-run tests (this catches wiring mistakes from the resolution)
python3 -m pytest tests/test_reviewer_reproduction_receipt.py \
    tests/test_reviewer_outcome_verdict_consistency.py \
    tests/test_verdict_parsing.py -v
# 70/70 pass expected

# Step 6: force-push (lease) the rebased branch
git push --force-with-lease origin receipt-gate-reviewer
```

### Wiring ordering rule (encoded from PR #407)

When a new helper is called AFTER `_enforce_outcome_verdict_consistency`, the audit metadata chain works as follows:

- Consistency runs first: if a contradiction is detected, it rewrites `metadata["verdict"]` to canonical AND sets `metadata["original_verdict"]` to the RAW reviewer output (so audit readers can see what the reviewer actually said).
- Receipt gate runs second: it MUST check `if "original_verdict" not in new_md:` before writing — otherwise it clobbers the more truthful pre-consistency value with the post-consistency canonical token, hiding the actual reviewer output from audit.

Without this guard, audit consumers see `original_verdict = "pass"` (canonical) when the reviewer actually said `"approve"` (raw) — a loss of truth that no comment in the code surfaced.

**Test for this**: `test_does_not_clobber_pre_existing_original_verdict` at `tests/test_reviewer_reproduction_receipt.py:156-180` (PR #407). Verifies the chain semantics explicitly.

## Anti-patterns (forbidden, verified to bite)

1. **Force-pushing without rebase first** when `gh pr view --json mergeable` returns `CONFLICTING`. The push will succeed but the PR remains unmergeable — the user's `/green` gate will FAIL on Gate 2 forever.
2. **Force-pushing without `--force-with-lease`** — overwrites the remote branch unconditionally. If a sibling process pushed between your fetch and your push, you clobber them.
3. **Resolving conflict markers manually without `ast.parse` verification** — leaves behind malformed Python that pytest may not catch (it depends on import order). Always run `python3 -c "import ast; ast.parse(open(f).read())"` on each resolved file before `git add`.
4. **Spinning up an AO worker for "Needs fixes (not blocking)" findings** — per advice SKILL.md middle-ground pattern: the PR already exists, the work is in-place, an AO spawn burns quota on a duplicate diff. Inline patches are faster + deterministic.
5. **Treating inline `/advice` substitute as a permanent replacement for the v2.5.7 babysit cron** — inline is fine for in-thread drives; for unattended overnight drives, the cron is correct because the user may not be around to push fixes.

## Skill pair

- `github/patch-port-protocol` Phase 1c — multi-canonical-repo discovery (the phase that found the fork-divergent `eae7413` HEAD in this session)
- `advice` (Hermes overlay) — the fan-out pattern + pinned synthesis format
- `qa-test-failure-dismissal-anti-pattern` — for the pre-existing skeptic-gate infra failure attribution
- `drive-pr-to-green` v2.5.6 — for the GitHub Actions 503 transient-failure trap (sibling concern)