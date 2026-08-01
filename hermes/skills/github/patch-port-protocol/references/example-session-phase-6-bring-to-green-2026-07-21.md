# Phase 6 — Bring-to-green follow-up (jleechanorg/dark-factory PR #407)

Companion to `example-session-2026-07-20.md`. The same session that produced PR #407 ended with the user typing "Lets iterate until /green and /er and /advice approved fullrun". This reference captures the bring-to-green phase moves that did NOT make it into the SKILL.md itself (they belong in `drive-pr-to-green`).

## Move 1 — Rebase onto `origin/main` from fork-divergent HEAD

PR #407's branch was anchored at `eae7413` (the patch author's working tree in `~/repos/jleechanorg/dark-factory`), 39 commits behind `origin/main` `8fc167899`. The 5 commits between them included two that directly conflicted with the patch's intent:

- **#297** — relocate `_enforce_outcome_verdict_consistency` into `handler_verdict` (the canonical home)
- **#301** — break `handler_parallel_reviewer` circular import (added `_handlers_shim` re-export pattern)

Conflict blocks fired in 2 files: `runner/handler_verdict.py` and `runner/handler_parallel_reviewer.py`.

### Resolution strategy (verified recipe)

1. **In the helper module that RECEIVED the relocation (`handler_verdict.py`)**:
   - Keep HEAD's full `_enforce_outcome_verdict_consistency` (it's the canonical home now).
   - Add the patch's new helpers adjacent to it (`_reproduction_receipt_gap` in this case).
   - KEEP BOTH SIDES of the conflict (HEAD's relocated function + patch's new code).

2. **In the helper module that ORIGINALLY contained the function (`handler_parallel_reviewer.py`)**:
   - DROP the patch's local copy of the relocated function (it's now a duplicate).
   - KEEP the patch's NEW helpers (`_receipt_required_flag`, `_enforce_reproduction_receipt`).
   - At every call site that USED to invoke the local copy: switch to the shim form `_handlers_shim._enforce_outcome_verdict_consistency(...)` instead of the unqualified name. The shim re-exports from `handler_verdict` so the unqualified name still resolves.

3. **Wire the new helpers' calls AFTER the consistency call** (NOT before). Reasoning: consistency normalization operates on outcome↔verdict tokens, not transcript content; receipt-checking AFTER consistency sees the canonicalized verdict which is exactly what we want.

4. **Audit chain correctness**: when helpers run sequentially and both write to `metadata["original_verdict"]`, the LATER writer clobbers the EARLIER one. Fix: each subsequent writer checks `if "original_verdict" not in new_md:` before writing. Test pinned by `test_does_not_clobber_pre_existing_original_verdict`.

### Commands

```bash
cd /tmp/df-receipt-gate-worktree
git fetch origin main
git rebase origin/main  # CONFLICT blocks in 2 files

# resolve per strategy above, then verify:
for f in runner/handler_verdict.py runner/handler_parallel_reviewer.py; do
  python3 -c "import ast; ast.parse(open('$f').read()); print('$f syntax OK')"
  grep -c '<<<<<<<\|=======\|>>>>>>>' $f  # MUST return 0
done

git add runner/handler_verdict.py runner/handler_parallel_reviewer.py
git rebase --continue
python3 -m pytest tests/test_reviewer_reproduction_receipt.py \
    tests/test_reviewer_outcome_verdict_consistency.py \
    tests/test_verdict_parsing.py -q  # 70/70 pass expected
git push --force-with-lease origin receipt-gate-reviewer
```

## Move 2 — Inline `/advice` Gate-3 substitute

When `gh pr checks N` shows:
```
CodeRabbit       fail    "Review rate limited"
Cursor Bugbot    skipping "usage limit reached"
chatgpt-codex-connector skipping "Codex usage limits"
```

…all three official review bots are unavailable. The `green.md` Step 3.4 substitute path is documented but no example existed until now. Recipe:

```bash
gh pr diff N --repo OWNER/REPO > /tmp/pr-N.diff

# Parallel fan-out: Reviewer A (source-accuracy) + Reviewer B (architecture)
delegate_task(goal='Reviewer A: source-accuracy review of PR #N ...',
              context='patch at /tmp/pr-N.diff, working tree at /tmp/<repo>-worktree, branch HEAD <sha>',
              toolsets=['terminal','file','search_files']) &
delegate_task(goal='Reviewer B: architecture review ...',
              context='...', toolsets=['terminal','file','search_files']) &
wait
```

The synthesized verdict (per advice SKILL.md "Pinned synthesis output format"):
- VERDICT: APPROVED-as-is OR NEEDS-FIXES (numbered list) OR REJECT
- REASONING: file:line evidence
- RISK: one sentence
- CONFIDENCE: high/medium/low
- NUMBERED FINDINGS: file:line — what — why — suggested fix

Post the synthesis as a PR comment (`gh pr comment N --body '<synthesis>'`) so the Gate-3 substitute is recorded on the PR thread per `green.md` Step 3.4.

### PR #407 outcome

- Reviewer A (MiniMax-M3, source-accuracy): APPROVED-as-is @confidence high
- Reviewer B (MiniMax-M3, architecture): NEEDS-FIXES @confidence high (3 numbered findings, 1 substantive)
- Findings applied as commit `f461f93`:
  1. `_receipt_required_flag` now accepts `int 1` (mirrored `_gate_strict_flag` exactly)
  2. `_enforce_reproduction_receipt` no longer clobbers pre-existing `original_verdict`
  3. Two new tests added (int=1 case + audit-chain preservation case)
- Final test count: 70/70 (was 68 pre-/advice)
- Final diff: `+331/-2` across 3 files

## Move 3 — Attribute pre-existing infra failure correctly

Gate 7 (skeptic-gate) failed 20/20 times across ALL branches including `main`. Verified via:

```bash
gh run list --repo OWNER/REPO --workflow skeptic-gate.yml --limit 20 \
    --json databaseId,headBranch,conclusion,createdAt | \
    jq '[.[] | {headBranch, conclusion}] | group_by(.headBranch) | map({branch: .[0].headBranch, runs: length, failures: [.[] | select(.conclusion=="failure")] | length})'
# All 10 branches: runs=N, failures=N (0 successes)
```

Per `same-test-name-rule`, this is **NOT a /green-blocker for this PR** because it pre-exists on `main` (3 fails on main). Correct response: open a `br` bead (`$USER-pm8f` for PR #407) to track the infra fix as a separate workstream, post the failure attribution as a known follow-up in the Slack status, and surface the verdict as "N-green for applicable gates" rather than "GREEN".

```bash
br create 'infra: skeptic-gate.yml failing across ALL branches (incl main) per gh run list --workflow skeptic-gate.yml --limit 20 (0/20 success)' \
    --type chore --priority 1 \
    --description 'Reproduced 2026-07-21 in PR #407. ...'
```

## Cross-references

- `~/.hermes/skills/workflow/drive-pr-to-green/SKILL.md` v2.5.9 addendum — full recipe
- `~/.hermes/skills/workflow/drive-pr-to-green/references/advice-substitute-and-fork-divergent-rebase-2026-07-21.md` — same content, canonical location
- `~/.hermes/skills/advice/SKILL.md` — Hermes-side /advice overlay + pinned synthesis format
- `~/.hermes/skills/qa-test-failure-dismissal-anti-pattern/SKILL.md` — the same-name-rule that attributed the skeptic-gate failure to pre-existing infra
- `~/.claude/commands/green.md` — Gate-3 substitute policy (Step 3.4)