# "Green gate passes ≠ PR fixes the right thing" — verified on PR #8531 (2026-07-24)

When a user hands you a PR on `$GITHUB_REPOSITORY` whose claim is
"fixes bug class X", the green gate (7-green) verifies **process correctness**
(CI / mergeable / CodeRabbit APPROVED / Bugbot clean / comments resolved /
evidence-gate / skeptic). It does NOT verify **semantic correctness** —
whether the PR's mechanism actually matches the reported bug.

This reference is the canonical recipe for the second question. It captures
a verified failure mode from PR #8531 / #8532 on 2026-07-24 and generalizes
to any directive-cap / truncation / rendering PR on your-project.com.

## The pattern

1. User reports "LLM ignored directive X" / "commands were truncated" / "stop
   trimming player commands and LLM response."
2. A PR is open with a mechanism that *plausibly* matches (e.g. "cap
   directives at 50 newest", "include full history", "dedupe").
3. Green gate looks healthy: CI green, CodeRabbit APPROVED (or CHANGES_REQUESTED
   on a comment, not a blocker), Bugbot clean, mergeable=true.
4. Agent's instinct: drive it to merge.
5. **Trap:** the PR's mechanism may be wrong. Merging 7-green with the wrong
   mechanism produces a merged main that does not fix the bug. The user comes
   back in a future session with "why is this still happening?"

## The recipe (4 steps, before driving `/green` on a directive-cap PR)

### Step 1 — Classify the PR

`gh api repos/$GITHUB_REPOSITORY/pulls/<N> --jq '{number,title,headRefName,head_sha:.head.sha,baseRefName,mergeable,state,user:.user.login}'`

Capture:
- PR head SHA
- PR author (if it's `jleechan2015` with no recent commit, suspect a closed
  PR from another branch — see Step 2)
- `mergeable` and `mergeable_state`
- `state` (open / closed / merged)

### Step 2 — Mirror the PR locally so you can diff without burning API budget

```bash
cd $HOME/<your-project.com clone>
git fetch --no-tags origin 'refs/pull/<N>/head:tmp-pr-<N>'
git show --stat tmp-pr-<N>
git diff --shortstat origin/main...tmp-pr-<N>
git log --oneline origin/main..tmp-pr-<N>
```

For PRs that touch `$PROJECT_ROOT/agent_prompts.py` or directive rendering,
search the diff for the load-bearing constants:

```bash
git diff origin/main...tmp-pr-<N> -- '$PROJECT_ROOT/agent_prompts.py' | grep -E 'MAX_|rendered_directives|truncated_count|newest.*N|cap.*directive'
```

### Step 3 — Run the BigQuery diagnostic (the actual repro)

The bug class for directive-cap PRs is "the LLM never saw the rule" or
"the LLM saw conflicting versions of the rule." Both are reproducible from
the `worldarchitecture-ai.llm_forensics.llm_payloads` dataset.

Full recipe in `~/.hermes/skills/wa-green-gate-pr-shape/references/llm_forensics-recipe.md`
(companion to this reference). The four numbers that matter:

1. **prompt_tokens distribution** — `min / median / p90 / max` across
   `gemini_provider.stream` rows for the affected campaign. If 100% of rows
   exceed 200k tokens, the prompt IS being compressed, but the renderer is
   not what compresses it (Gemini's upstream limit is).
2. **Active God Mode Directives block size** — count `^\d+\.` entries inside
   the block. If the renderer is already shipping 250+ directives but the PR
   proposes a cap of 50, the cap is the wrong mechanism.
3. **Contradictory rule count** — `re.findall` on the block for rules
   containing keywords from the bug class (e.g. `gear`, `equipment`,
   `original divine`, `level / 10`). If 10+ rules exist with conflicting
   inputs (Original vs Current Level, 45 vs 49 vs 89 for Bane, etc.), the
   bug is contradiction, not truncation.
4. **Rule position** — `req.lower().find(needle) / len(req)` for the
   relevant rule. Median > 85% means the rule is buried near the end and
   competing for attention budget (real bug).

### Step 4 — Verdict

Three outcomes, pick one:

| Measured reality | Verdict |
|---|---|
| Mechanism matches the bug class (e.g. cap N matches actual truncation at N) | Drive the PR to merge per `drive-pr-to-green` |
| Mechanism doesn't match (e.g. cap 50 but renderer ships 293; bug is contradiction; PR hardcodes one campaign) | Halt. Surface the measured numbers in the PR comment + bvr issue. Ask the user which path (revise-in-place / clean-replay / close). Do NOT drive a wrong-mechanism PR to merge just because 7-green passes. |
| Mechanism is partially right + needs adjustment | Revise in place per `pr-cleanup-replay` Strategy B (extract-load-bearing-diff onto a clean branch from `origin/main`) |

## The 2026-07-24 verified case

PR #8531 (head `0390cc201d`, branch `tmp-pr-8531`):
- Title: "fix(8528-a): cap god-mode directives at 50 newest entries; add routing lint"
- Mechanism: cap to `MAX_GOD_MODE_DIRECTIVES_RENDERED = 50` newest
- Measured: renderer was already shipping 293–299 directives (NOT 50);
  the actual bug was 15+ contradictory gear-formula rules stacked in the
  active block (Original Level 45 vs 49 vs 89 vs 95 for Bane, with five
  contradictory `(Level / 10)` rules)
- BQ result: 275 `gemini_provider.stream` rows for `wc2BBcSgOljiU3vJ160A`,
  prompt_tokens min/median/p90/max = 250001/288145/300762/331252, 100%
  over 200k, 11% over 300k
- Verdict: **mechanism doesn't match**. Capping at 50 would have DROPPED the
  newest 243 directives (exactly the gear-rule updates the player was
  pushing), manufacturing the truncation bug the PR claimed to fix.

PR #8532 (head `6be4d5843b`):
- Title: "test(8528-a): contract tests for god-mode directive routing in
  dynamic channel"
- Mechanism: hardcoded one campaign's 5-NPC gear list (`assert bane.equipment_bonus == 4`)
- Verdict: **campaign-specific, reject**. Re-running the BQ scan would
  catch this if the test was named after a specific NPC, but the broader
  rejection is "PR that hardcodes campaign-specific NPCs is the wrong
  shape — open a campaign-agnostic version instead."

## Hard rule (added 2026-07-24)

> Green gate covers the COMMITTED end of the merge path.
> The semantic-correctness end is the agent's responsibility.
> A 7-green PR whose mechanism doesn't match the measured bug is a
> wrong-mechanism PR — halt and surface data before `gh pr merge`,
> regardless of how clean the gate log looks.

## Companion references

- `wa-green-gate-pr-shape/references/llm_forensics-recipe.md` — the
  BigQuery + Python recipe (Step 3 details)
- `wa-green-gate-pr-shape/SKILL.md` PR-shape triage section — the
  per-PR decision matrix
- `finish-the-job/references/bq-runnable-diagnostic-first-2026-07-23.md`
  — the general principle: when bug class is in a known taxonomy AND a
  runnable diagnostic exists, the diagnostic is the first tool call, not
  a fix-direction menu
- `repro/SKILL.md` Step 0.77 — BQ-first diagnostic for directive-loss
  reports specifically
- `pr-cleanup-replay/SKILL.md` — Strategy B (clean branch from
  `origin/main` + cherry-pick / extract-load-bearing-diff) when the
  PR's mechanism is right but the history is wrong