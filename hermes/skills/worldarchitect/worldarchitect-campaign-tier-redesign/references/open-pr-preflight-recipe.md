# Open-PR preflight — recipe + decision matrix (v0.6.0)

Always run BEFORE Phase 0 inventory. Catches the most common failure mode: the agent proposes "open a new PR" or "rewrite the contract" when an existing open PR already covers the ask.

## Why this exists

Verified 2026-07-28: user asked *"Lets modify the prompts to encourage creation of mysteries in the plot line too. Like there should be a few mysteries or backstories not revealed to the player until later in the campaign. Either make a new PR or add this so an existing PR that fits."*

The agent had to discover [PR #8662](https://github.com/$GITHUB_REPOSITORY/pull/8662) (`feat(prompts): generic shared contracts + AI mystery/internal-drive arcs + campaign_overlays loader`, open at the time) after multiple skill loads + git checks + gh API calls. The right answer was **amend PR #8662**, not open a new one. The preflight would have surfaced this in one REST call.

## The 4-step recipe

```bash
cd ~/projects/your-project.com && git fetch origin 2>&1 | tail -3

# 1. List every feat/* branch on origin (covers branches with or without PRs)
git branch -r | grep -E 'origin/feat/' | sort -u

# 2. Search open PRs by the user's keyword (REST, not GraphQL — bypasses rate limits)
gh api 'search/issues?q=repo:$GITHUB_REPOSITORY+is:pr+is:open+mystery+OR+secret+OR+reveal+OR+plot+OR+foreshadow' \
  --jq '.items[] | {number,state,title,url,head_ref:.head.ref}' 2>&1

# 3. Search by the umbrella-PR keyword (catches the v0.5.0 / v0.6.0 shared-contracts PRs)
gh api 'search/issues?q=repo:$GITHUB_REPOSITORY+is:pr+is:open+shared-contracts+OR+internal-drive+OR+mbti+OR+overlays' \
  --jq '.items[] | {number,state,title,url,head_ref:.head.ref}' 2>&1

# 4. For each candidate branch, check whether it already contains the contract file
#    (saves re-reading the diff — just check the tree)
git ls-tree -r origin/<branch> -- $PROJECT_ROOT/prompts/shared/ 2>&1 | grep -E 'mystery|internal_drive|plot_arc'
```

**Total runtime: ~30 seconds.** No LLM calls, no browser, no delegated tasks.

## Decision matrix

| What the preflight found | Action |
|---|---|
| Open PR already has the contract file | **Strengthen / amend that PR** — push to the same branch. Don't open a new PR. |
| Open PR covers a related ask (e.g. shared contracts umbrella) but missing the specific rule | **Add the rule to that PR** as a new commit on the same branch. Reference the umbrella PR's compatibility section. |
| Multiple candidate branches (umbrella PR + companion campaign PR like #8662 + #8661) | **Push to the umbrella PR** (the shared contract), not the campaign-specific PR. Per `no-campaign-hardcoding` rule, the contract belongs in `$PROJECT_ROOT/prompts/shared/`. |
| No matching open PR | **Proceed to Phase 0** inventory + Phase 2 proposal. Branch from `origin/main`. |

## Anti-patterns

- **Don't propose a new PR** before running this preflight. The user's "make a new PR or add this so an existing PR that fits" (verified 2026-07-28 Slack phrasing) explicitly invites the agent to join an existing PR when one fits — default to that path.
- **Don't skip the preflight even if the user's ask sounds new.** "Mystery/secrets/plot" phrasing in 2026-07-28 mapped to PR #8662 verbatim. Future phrasings ("add foreshadowing", "add plot twists", "keep the player guessing", "hidden lore", "secret antagonist") will likely map to the same contract.
- **Don't re-inventory Phase 0 items just because Phase -1 found an existing PR.** Phase 0 is for designing new work; if you're amending an existing PR, read its current diff and identify the gap, not start over.
- **Don't delegate this preflight to a subagent.** It's 4 REST calls — faster and cheaper inline than spinning up a worker. Reserve `delegate_task` for Phase 0's parallel fan-out (file audit + memory search + campaign corpus).

## Case study — PR #8662 (2026-07-28)

**User ask:** *"Lets modify the prompts to encourage creation of mysteries in the plot line too. Like there should be a few mysteries or backstories not revealed to the player until later in the campaign. Either make a new PR or add this so an existing PR that fits."*

**What the preflight surfaced:**

- PR #8662 — `feat(prompts): generic shared contracts + AI mystery/internal-drive arcs + campaign_overlays loader` — **OPEN** — head `8b984ce4ee2`
- Branch: `feat/shared-contracts-mbti-internal-drive`
- Files: 13 changed, +1473/-16
- Critical file: `$PROJECT_ROOT/prompts/shared/ai_generated_mystery_and_internal_drive_plot_arc.md` (99 lines) — **already contains**:
  - Hidden fact (one fact, not three) reachable by investigation but not surface observation
  - Clue trail (3-5 clues, internally consistent, no dead ends)
  - 3 suspect branches: red herring / partial truth / real answer
  - Personal-cost requirement (mystery must change something for the character)
  - "MUST seed at least one active mystery before the player explicitly asks"
  - Internal-drive surfacing (hidden want / hidden fear / hidden insecurity)
  - Anti-pattern: mystery-without-cost, arc-without-interior

**What the preflight would have shown in 30 seconds:**

The user's exact ask ("mysteries or backstories not revealed to the player until later in the campaign") maps verbatim to PR #8662's existing AI-mystery shared contract. The right answer was **amend PR #8662** by adding an explicit "mystery density" or "staggered reveal cadence" rule to the existing contract, push to the same branch, do NOT open a new PR.

## What "amend" looks like in practice

1. **Identify the gap** in the existing contract. Read the current `$PROJECT_ROOT/prompts/shared/ai_generated_mystery_and_internal_drive_plot_arc.md` and look for:
   - Missing rule the user named ("density" / "staggered reveal" / "mystery density per campaign")
   - Existing rule that's underspecified (e.g. "personal-cost" — does it say how *often* the cost must escalate?)
   - Anti-pattern that's missing (e.g. no rule against "mystery dumps at the end")

2. **Add the new rule** as a numbered subsection matching the existing tone (short, declarative, named examples). Reference canonical lore factions/characters so the LLM has concrete substitutes.

3. **Update the test file** (`$PROJECT_ROOT/tests/test_shared_contracts_and_internal_drive_mysteries.py`) with assertions for the new keywords. The 28-test base is the contract — every addition needs a matching assertion.

4. **Update the PR body** — keep the existing summary, add the new rule to the "Six shared contracts" list (now seven) + note the addition in the changelog/commit body.

5. **Branch hygiene** — the existing branch is `feat/shared-contracts-mbti-internal-drive`; stay on it. Do NOT create a new branch like `feat/mystery-density-addition` — that defeats the purpose.

6. **Push** — `git push origin feat/shared-contracts-mbti-internal-drive`. The PR #8662 head advances. CI re-runs.

## When to OVERRIDE the "amend existing" default

Only override when:

- The existing PR is in a clearly different domain (e.g. PR #8661 Spellblade Valeria prompts — adding "no campaign hardcoding" rules there would be wrong; that's PR #8662's territory).
- The existing PR has been blocked/closed and is unlikely to merge in the user's timeline.
- The new ask is genuinely orthogonal to anything in the existing PR and the diff would be cleaner as its own atomic commit.

In all three cases, the new PR should still **reference the existing one** in its body: *"Companion to PR #8662; this PR adds the X-specific overlay while #8662 carries the shared contract."* — keeps the dependency graph explicit.

## Companion references

- `~/.hermes/skills/finish-the-job/SKILL.md` — the push-PR-and-merge discipline that applies once you've decided to amend vs open new.
- `~/.hermes/skills/workflow/always-pr-never-local-edit/SKILL.md` — never just make local edits and stop; even an amendment is a `git push origin` away.
- `~/.claude/skills/zero-touch.md` — 6-green gate per PR (must re-pass after amendment).
- `references/ai-mystery-internal-drive-plot-recipe.md` — the existing v0.5.0 contract that PR #8662 already covers; read first to avoid duplicating rules.
- `references/no-campaign-hardcoding-and-shared-prompts.md` — the umbrella-no-hardcoding invariant that any amendment must respect.
