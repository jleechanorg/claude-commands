# BQ-runnable-diagnostic-first anti-pattern (verified 2026-07-23, issue #8528)

## The pattern

When a user reports a problem AND the problem class is in a known
taxonomy AND a runnable diagnostic exists for that class, the agent
must run the diagnostic in the first tool call of the session — not
post a clarifying menu of fix directions.

## The verbatim incident

**User's message** (Slack, $GITHUB_REPOSITORY thread,
campaign `wc2BBcSgOljiU3vJ160A`):

> Maybe we should stop trimming god mode player commands and LLM
> response and always return their full text until we run out of
> context? Seeing so many bugs where god mode commands ignored.
> Look at this latest one where LLM ignoring formula for the gear
> when gods got turned into mortals — run /repro <url>
> and its scene 454

**Agent's first response:** Posted an A/B/C menu:
- A — Concur with the Factor H diagnosis, add `select_directives_by_budget()`
- B — Stop trimming, render god-mode commands verbatim until context fills (literal proposal)
- C — Hybrid: A primary + B as a dev-mode escape hatch

**User's verbatim pushback:**

> Read the actual raw LLM request in BQ did the LLM even see the
> directive for scaling the equipment? If so paste the full text here

That is a direct BQ-runnable-diagnostic request and a direct complaint
about the menu that preceded it.

## What the diagnostic actually returned (run after the pushback)

`bq query` against `worldarchitecture-ai.llm_forensics.llm_payloads`
for `campaign_id='wc2BBcSgOljiU3vJ160A'`, recent 4 god-mode turns:

| UTC | User command | LLM response confirmed formula applied? | npc_data.equipment_bonus written? |
|---|---|---|---|
| 16:08:39 | "No one else should have +10 gear..." | ✅ | ✅ Bane=2, Myrkul=2, Gale=2 |
| 16:10:24 | "No you forgot the whole formula double check it" | ❌ | ❌ |
| 16:11:33 | "No look the formula for the special god gear..." | ✅ | ✅ Ao=**2 (wrong, should be 4)** etc. |
| 16:14:37 | "No you use their original levels" | ✅ | ✅ Ao=**9 ✓** Bane=**4 ✓** Myrkul=**4 ✓** Gale=**4 ✓** |

The actual diagnosis surfaced was **state-update value-derivation drift** —
LLM correctly applied the formula in narrative prose + correctly wrote the
`npc_data.<NPC>.equipment_bonus` field + but wrote the wrong numeric value
(~50% under/over the canonical derivation). The user's literal
"stop trimming" hypothesis was wrong; the LLM response was not being
trimmed; the user command had been received; the bug lived in a
different layer entirely.

The A/B/C menu proposed fixes that were structurally wrong for the actual
bug class. The cost of that wrong direction was:

- ~1 wasted turn (the menu itself).
- ~1 wasted turn (user pushback that the menu was the wrong shape).
- An issue body that needed to be rewritten with the corrected diagnosis.

Total cost: 2-3 turns before the diagnostic ran.

## When this pattern applies — 6-bullet heuristic

If ALL SIX are true, run the diagnostic first, do NOT post a menu:

1. The bug class is in a known taxonomy (e.g. `npc-status-persistence-bug`,
   `god-mode-directive-missing`, `cache-invalidation-churn`,
   `state-update-value-derivation-drift`).
2. A runnable diagnostic exists for that class (specific `bq query`,
   Firestore read, code grep, etc.).
3. The diagnostic does NOT require user input to run (you can run it
   with the campaign_id + turn-range you've already extracted from the
   user's message).
4. The diagnostic will distinguish between the most likely competing
   sub-classes (e.g. the 7-factor god-mode-directive matrix is
   resolvable by reading 3 turns of `request_json` + `response_text`).
5. The user's symptom description is concrete enough that you can scope
   the diagnostic to specific turns / state fields / table rows.
6. The user's instinct ("is it X?") maps to a yes/no answer from the
   diagnostic — and the diagnostic is faster than asking the user to
   verify.

If any of 1-6 is ambiguous, ask ONE question. If all 6 are true,
do not.

## Why this anti-pattern eats turns

The "fix-direction menu" template (A: option 1, B: option 2, C: hybrid)
feels helpful but:

- Loads the user's turn budget without producing evidence
- Misroutes the diagnosis if the user picks an option that turns out
  to be the wrong sub-class
- Trades 1 turn of clarification (a question the user can answer) for
  1 turn of analyst work you should have done
- The user CANNOT evaluate the options without the same evidence the
  diagnostic would produce — so the menu often produces
  low-information responses from the user ("just do something") that
  don't narrow the bug class

The runnable diagnostic:

- Produces evidence in 1 tool call vs 1 turn of menu + 1 turn of
  user-response + 1 turn of follow-up
- Lets the user evaluate the diagnosis against their actual symptoms
  ("yes that's the same gear I was asking about")
- Surfaces sub-classes the menu didn't enumerate (state-update-value-
  derivation drift was not in the menu because the agent hadn't seen
  it yet)
- The user can say "yes that's the right class" or "no it's
  something else, here's what I observed"

## Companion rules

- **Don't run the diagnostic blindly.** If the diagnostic is expensive
  (multi-table BQ query, Cloud Logging walk across multiple filters)
  AND the user's report is genuinely vague, ask one clarifying
  question FIRST to scope the diagnostic. The 6-bullet heuristic
  covers this — item 5 requires "symptom description is concrete
  enough that you can scope the diagnostic to specific turns / state
  fields / table rows."
- **Don't paste the entire raw diagnostic output** (~350KB-cap
  `request_json` per turn is too big for Slack). Grep for the diagnostic
  markers, paste the offsets + a 200-char excerpt per match.
- **Pair the diagnostic with `repro` skill Step 0.77.** That step
  codifies the BQ-runnable-diagnostic discipline for the specific
  worldarchitect bug class. This reference file codifies the GENERAL
  anti-pattern class — any domain, any session type, any agent.

## Cross-references

- `finish-the-job` changelog 1.7.4 (2026-07-23) — this entry.
- `finish-the-job` pitfall "Stalled on a preflight menu" extension —
  BQ-runnable-diagnostic sub-case, in the SKILL.md.
- `finish-the-job` anti-pattern "Stalled on a preflight menu when the
  goal had 3+ clear verbs" — extended with the BQ-runnable-diagnostic
  sub-case in the SKILL.md.
- `repro` changelog 3.7.0 (2026-07-23) — Step 0.77 BQ-first diagnostic
  for directive-loss reports (the domain-specific codification).
- `repro` Step 0.77 in SKILL.md — the workflow position in the
  /repro skill.
- Verified issue: [#8528](https://github.com/$GITHUB_REPOSITORY/issues/8528)
  on campaign `wc2BBcSgOljiU3vJ160A`.
