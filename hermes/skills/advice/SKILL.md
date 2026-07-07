---
name: advice
version: 1.1.0
description: "Hermes wrapper for the `/advice` token-efficient second-opinion slash command. Canonical source is `~/.claude/skills/advice/SKILL.md` (Claude Code user-scope). For Hermes users, this overlay adapts the Reviewer A fallback chain to what is actually installed locally (subagent → agy → codex) since `cursor` is not installed on this machine. Invoke by calling this skill directly OR by reading the canonical Claude file at `~/.claude/skills/advice/SKILL.md` for the full text. Adds the docs-accuracy review template (verified 2026-07-06) — use it when the question is 'are these merged docs accurate against source X' instead of the generic Decision + Artifact pattern."
---

# /advice — Token-Efficient Second Opinion (Hermes overlay)

**This is the Hermes-side wrapper.** The canonical skill lives at:
- `~/.claude/skills/advice/SKILL.md` — full pattern, all 3 reviewers, fallback chain

**Read the canonical file for the full procedure.** This overlay exists so that:
1. `skill_view(name='advice')` works from the Hermes session (the canonical Claude skill is not registered in the Hermes skill registry).
2. Future agents learn to **search both `~/.hermes/skills/` AND `~/.claude/skills/`** when a user invokes a `/slash` command — slash commands are not Hermes-native; they are Claude Code constructs.

## When to use

User says `/advice [optional question]`, or you reach a decision point that needs a second opinion without shipping the full conversation uncached.

## Review types (added 2026-07-06)

The canonical `/advice` SKILL.md describes the general-purpose "extract decision + artifact, fan out 3 reviewers, synthesize" pattern. For docs-accuracy reviews (e.g. "are these merged docs accurate against the source?"), use this specialized template — it produces far more useful verdicts than the generic one:

### Docs-accuracy review template

```markdown
# /advice Decision + Artifact

## DECISION (3-5 sentences)
[What specifically needs review — be concrete. For docs-accuracy:
"docs X/Y/Z were merged in PR #N; need a second opinion on whether
the claims match the actual `src/` code, whether the terminology
is consistent across files, and whether anything was fabricated."]

## ARTIFACT (≤150 lines, claim-bearing excerpts only)
[Paste ONLY the claim-bearing sections from each doc, plus the
load-bearing source files. Drop boilerplate, drop "Install" sections,
drop Config tables — they don't bear accuracy claims. If the docs
total 800+ lines, summarize to ≤150 lines.]

### Doc §"<section name>" — claim-bearing excerpts
> [quote 1-3 sentences that make a verifiable claim]

### Doc §"<section name>" — claims under review
**L1 ...**: enforces X
**L2 ...**: enforces Y
**L3 ...**: enforces Z

### Source: `src/<file>.rs::<fn>()`
```rust
[the actual source code that backs the claim]
```

## QUESTIONS FOR THE REVIEWER

1. **[Specific factual claim]**: does doc say X? does code do X?
2. **[Terminology consistency]**: are the terms used consistently?
3. **[Missing callout]**: is there a case the doc should surface that
   it doesn't? (e.g. macOS short-circuit, sudo escalation wording)
4. **[Fabrication check]**: does any claim in the doc contradict
   actual source?

## DELIVERABLE

Return exactly:
VERDICT: [docs accurate / docs need fixes (list) / docs misleading (explain)]
REASONING: [3-4 sentences citing file:line evidence]
RISK: [main risk if docs are wrong, one sentence]
CONFIDENCE: [high / medium / low]

Plus a numbered list of every inaccurate claim you found, each with:
doc-file:line, source-file:line, what the doc says vs what the code
actually does.
```

**Why this template works (verified 2026-07-06, ez-gh-actions PR #9 review):**

1. The "QUESTIONS FOR THE REVIEWER" numbered list forces the reviewer to
   address each load-bearing claim explicitly instead of waving a hand
   at "looks accurate".
2. The 3 reviewer roles get differentiated goals:
   - **Reviewer A (source accuracy)**: file:line citations from the docs
     AND the source for each claim — every claim must trace to code.
   - **Reviewer B (public docs)**: cross-reference with Docker/Colima/QEMU
     official docs, GitHub Security Lab research, kernel docs.
   - **Reviewer C (internal consistency)**: terminology drift between
     README/DESIGN/SVG/wiki/roadmap, broken anchor links, jargon overload.
3. The "Plus a numbered list of every inaccurate claim you found"
   output format surfaces EVERY gap in one table — easier to synthesize
   into a follow-up PR than prose paragraphs.
4. The 150-line artifact budget forces distillation: only the claims
   that matter go to the reviewer. Boilerplate config tables and install
   instructions are noise for accuracy review.

**When NOT to use the docs-accuracy template:** use the generic pattern from
the canonical SKILL.md when the question is about code design, an
architecture decision, a trade-off between two approaches, or anything
that doesn't fit "are these docs accurate against source X".

## Hermes-adapted Reviewer A fallback chain

The canonical Claude chain is `subagent → cursor → agy`. On this machine `cursor` is **not installed** (only `claude`, `codex`, `agy` are available). Use this adapted chain:

| Priority | Tool | When |
|---|---|---|
| A1 | `delegate_task` (subagent) | Primary inside Hermes |
| A2 | `agy --print --dangerously-skip-permissions` | subagent unavailable / failed |
| A3 | `codex ...` (headless codex invocation) | agy failed; codex has quota |
| A4 | `claude -p --dangerously-skip-permissions --cwd /tmp` | last resort; requires `claude` login |

## Known pitfalls (learned 2026-06-28)

1. **`/advice` is NOT a PR comment bot.** Posting `/advice` as a PR comment does nothing — the skill is processed locally by the calling LLM, not by a GitHub workflow. Confirm this with `grep -rln "/advice" $HOME/projects_other/your-project.com/.github/workflows/` (returns empty).
2. **The skill is in `~/.claude/skills/`, not `~/.hermes/skills/`.** `skill_view(name='advice')` will fail with "Skill not found" until this overlay exists. After this overlay is loaded, `skill_view(name='advice')` returns this file.
3. **`claude -p` requires login** on this machine (`claude -p` → "Not logged in · Please run /login"). Do not burn time on Reviewer A4 if A1-A3 also fail — just note "Reviewer A unavailable."
4. **No Hermes parallel exists.** `~/.hermes/skills/` has no native `advice` skill; this overlay is the only Hermes-side path.
5. **`/research` and `/secondo` referenced by the canonical skill are also Claude-Code slash commands** — not available in Hermes. Replace them with `delegate_task` (research flavor) and `delegate_task` (multi-model opinion flavor) if needed.

## How to invoke /advice from Hermes

1. **Discover:** Call `skill_view(name='advice')` — returns this overlay. For full text, `cat ~/.claude/skills/advice/SKILL.md`.
2. **Extract:** Decision (3-5 sentences) + Artifact (≤150 lines).
3. **Fan out (parallel):**
   - Reviewer A: `delegate_task(goal="Senior engineer second opinion...", toolsets=["terminal","web"])` — that's the Hermes equivalent of the Claude subagent.
   - Reviewer B: `delegate_task(goal="Research question...", toolsets=["web","search"])`
   - Reviewer C (optional): `delegate_task(goal="Second-opinion from a different model...", toolsets=["terminal","web"])` — note `claude -p` is not logged in.
4. **Synthesize:** Same table format as canonical skill.

## Cross-reference

- Canonical Claude-Code skill: `~/.claude/skills/advice/SKILL.md`
- Hermes skill paths: `~/.hermes/skills/` (staging, git-tracked), `~/.hermes_prod/skills/` (prod runtime)
- Hermes deploy pipeline: `~/.hermes/scripts/deploy.sh --system hermes` syncs this overlay to prod
- Codex canonical mirror: `~/.codex/skills/` archived 2026-06-13; new path is `~/.agents/skills/`