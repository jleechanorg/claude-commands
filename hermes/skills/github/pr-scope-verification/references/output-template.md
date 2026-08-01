# Output Template — PR Scope Verification JSON

The audit emits a single JSON object. The schema below is the minimum
required for the user to act on the result.

## Schema

```json
{
  "pr_url": "https://github.com/<org>/<repo>/pull/<n>",
  "head_sha": "<40-char hex>",
  "base_sha": "<40-char hex>",
  "covers_<claim_1>": true | false,
  "covers_<claim_2>": true | false,
  "<optional_excerpt_field>": "verbatim quote from PR diff if useful",
  "gaps": [
    "<file_path>:<line_range> — <description of what's missing and why this is a gap>",
    "<file_path>:<line_range> — <another gap>"
  ],
  "recommendation": "push follow-up commit" | "no action needed" | "<other>",
  "blockers": []
}
```

Fields:

- `pr_url` — canonical GitHub PR URL. Pull from `git remote get-url origin`
  plus the PR number the user gave.
- `head_sha` / `base_sha` — exactly 40 hex chars, from `git rev-parse`.
  Never truncate, never guess.
- `covers_<claim>` — one field per user-stated claim, snake_cased.
  Boolean. The claim name should match the user's exact wording.
- `gaps` — ordered array, most-important gap first. Every entry
  cites a specific file path and line range, then explains in one
  sentence why it's a gap.
- `recommendation` — short imperative: what the user should do next.
- `blockers` — empty array unless something prevents action
  (merge conflict, missing dependency, locked branch, etc.).

## Worked example

Real audit: PR #8539 in `$GITHUB_REPOSITORY`. The user
asked "does this PR cover character evolution driven by MBTI internal
drives/goals/insecurities?". The PR's actual scope was prompt
consolidation + leak-plugging.

```json
{
  "pr_url": "https://github.com/$GITHUB_REPOSITORY/pull/8539",
  "head_sha": "da438c16c59b7ad95cb56ba75c0d1dc431482f2b",
  "base_sha": "258075d765a6103c216d022237ad134924fc73b4",
  "covers_internal_only_mbti_rule": true,
  "covers_character_evolution": false,
  "covers_personal_growth_drive": false,
  "covers_goal_evolution_on_player_action": false,
  "evolution_rule_text_excerpt": null,
  "gaps": [
    "$PROJECT_ROOT/prompts/narrative_system_instruction.md:5-11 — new canonical contract section 'INTERNAL-ONLY CHARACTER FIELDS' covers only leak-prevention (MBTI/alignment/big-five disclosure); contains NO mention of stress arcs, unhealthy-mode MBTI shifts, Want/Fear/Boundary mutation, or personal-growth direction",
    "$PROJECT_ROOT/prompts/master_directive.md:147 — the only 'Character Evolution' line in the diff is PRE-EXISTING text ('Alignment/personality can shift through story events. Document changes in DM Notes.'); not added by this PR, has no mechanism, no Wants/Fears/Boundaries, no growth direction, no trigger tied to player actions",
    "$PROJECT_ROOT/prompts/character_template.md:1-3 — pointer-only change; the Character Profile Template has no field for documenting per-NPC growth direction or insecurities"
  ],
  "recommendation": "push follow-up commit on PR #8539",
  "blockers": []
}
```

What this report tells the user:
- The PR does NOT cover character evolution; it only consolidates the
  leak-prevention rule.
- The single "Character Evolution" line in the diff is pre-existing
  content, not new coverage.
- The user should push a follow-up commit that adds the missing
  evolution mechanics.

## Reading the result

The user uses the JSON to decide:
- If all `covers_*` flags are `true` and `gaps` is empty → merge/approve.
- If some are `false` but `recommendation` says "no action needed" →
  the user has already accepted those gaps.
- If `gaps` is non-empty and `recommendation` says "push follow-up" →
  author a follow-up commit that closes each gap.
- If `blockers` is non-empty → cannot decide until they're resolved.

## Validation

Before delivering, confirm:
- All SHA refs are exactly 40 hex characters (run a regex check).
- All gap strings reference real file paths that exist in
  `git diff --stat`.
- All line numbers in gap strings refer to HEAD-side line numbers
  (read the file at HEAD with `git show HEAD:<path>` to verify).
- The JSON parses (no trailing commas, no Python-isms in strings).
- `recommendation` is a concrete next step, not "see above" or
  "TBD".

## Anti-patterns to avoid

- **Vague gaps.** "PR doesn't cover stress arcs" — useless. Always
  cite file:line and explain the missing mechanism.
- **Inferring coverage from related concepts.** "The PR mentions MBTI,
  so it must cover MBTI-driven growth" — wrong. Verify the exact
  concept appears in the diff.
- **Reporting blockers you didn't actually encounter.** An empty
  `blockers` array is the correct default. Only populate it when
  something genuinely prevents action.
- **Treating touch as add.** A file appearing in `git diff --stat`
  means it changed; it does NOT mean the PR added every concept
  in that file. Re-read each diff hunk to confirm.