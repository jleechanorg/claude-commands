# Guardrail-Mapping Template

The non-obvious durable technique from the Visenya v9 session: **map the new campaign spec to specific open WA prompt-layer PRs/issues as anti-invention guardrails.**

A campaign bible that says "Visenya must never be magically detected" without referencing the open PR that fixes that bug is just vibes. A campaign bible that says "Guardrail G1: Anti-scrying — invariant: no NPC may learn Apex lineage via magic; affects `narrative_system_instruction.md`; reference PR #8469" is actionable spec.

## Why this pattern exists

The user recycles complaints:

- "The LLM keeps giving NPCs forbidden knowledge"
- "Random antagonistic events that don't fit"
- "Campaign became frictionless"
- "NPCs collapse into silent monologues"

Each complaint is a **recurring prompt-side anti-pattern** with concrete open PRs in flight. The campaign bible is the right place to *anchor* the campaign to that work so the prompt-side fixes have a fixed target to ship against.

## Template (use verbatim)

For each recurring user complaint:

```
### Guardrail G<N> — *<one-line name>*
**Reference:** <PR 1>, <Issue 2>, <PR 3>...
**Invariant:** No <thing> may <bad behavior>. Specifically:
- <bullet 1>
- <bullet 2>
- <bullet 3>

**Prompt-Layer Implementation:**
- `<file>.md`: Add §"<section>" — <does what>
- `<file>.md`: Add §"<section>" — <does what>

**Audit hook:** <concrete check, e.g. post-emit token scan, friction watchdog, capability-lock scan>.
```

## Discovery recipe (how to find the PRs/issues)

```bash
# Avoid GraphQL rate-limit. Use REST API directly.
TOKEN=$(gh auth token)
curl -s -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/$GITHUB_REPOSITORY/pulls?state=open&per_page=50" | jq '.[] | {number, title, head_ref: .head.ref}'

# Same for issues
curl -s -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/$GITHUB_REPOSITORY/issues?state=open&per_page=50" | jq '.[] | {number, title}'
```

See `gh-rate-limit-and-transient-failures` skill for the full rate-limit playbook.

## Cluster by user-visible symptom class

Sort the open issues/PRs by what the *user would feel*. v9 mapped 11 issues to 7 symptom classes:

| Symptom class | Open PRs |
|---|---|
| NPC knowledge forbidden (anti-scrying) | #8469, #8468 |
| Canonical state anchoring (no canonical-dead-NPC revival, no identity contradiction) | #8473, #8469, #8336 |
| No out-of-lore antagonistic events | #8443, #8439, #8441, #8452 |
| Anti-frictionless / cost discipline | #8387, #8384, #8386, #8395, #8400 |
| NPC dialogue discipline (no silent monologues) | #8382 |
| God-mode / Apex capability lock | (none open — uncovered) |
| Reputation die audit | (none open — uncovered) |

## Where to put the table in the bible

Two locations:

1. **Inside the doc**, at the end as **Section 10: Hard Guardrails (the "Don't" List)** and **Section 11: Open PRs Already in Flight**. The doc is the human-facing spec.

2. **In the wiki source page**, as a one-row-per-guardrail summary at the top so the next iteration's brainstorm sees it without scrolling.

## Anti-patterns

- **Don't fabricate PR numbers.** Use only open PRs/issues you actually loaded via `gh api` or `gh pr list`. If you can't load them (rate-limited), say so in the doc and ship without the audit anchor — don't fake the audit.
- **Don't include closed PRs in the guardrail table.** Closed = shipped. The whole point of the table is *work still to be done*.
- **Don't reference issues/PRs from other repos.** Different prompt layer, different audit. Stay inside the campaign's home prompt layer.
- **Don't map a guardrail to a single PR.** Cluster. v9 referenced 11 PRs/issues across 7 guardrails.

## How to track as work ships

When a fix-PR merges, the next-iteration's doc should:

1. Update the **Status** column for that guardrail (e.g. "Partial fix shipped in #8469").
2. Add a new bullet under the guardrail invariant describing what's now possible.
3. If the guardrail is fully satisfied, move it to a "Fulfilled Guardrails" appendix at the bottom of Section 10.

This makes the vN+1 docs a *living* trace of the prompt layer's hardening progress.

## Reference

- Visenya v9 (2026-07-20): 7 guardrails G1–G7, 11 open WA PRs/issues, doc at https://docs.google.com/document/d/11HohncqogJHQtIk0_JwsEuz7IsaLolFw1rM1mePM3Bw. Status table shows 3/7 partial-fixes-in-flight and 4/7 uncovered.
