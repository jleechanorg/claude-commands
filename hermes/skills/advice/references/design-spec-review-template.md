# Design-spec review template (added 2026-07-30)

Use this template when the artifact is a **fresh design specification** (new feature, new product, system redesign) — not a merged doc and not a patch. The user is asking "review this design before implementation" rather than "review the accuracy of these merged docs" or "review this diff."

The generic `Decision + Artifact` pattern from the canonical `/advice` SKILL.md still applies; this template adds the two reviewer roles that emerged as load-bearing in the 2026-07-30 browserclaw design review:

- **Reviewer D — Operator-intent fidelity**: did the design answer the operator's actual goal, or did the author over-design around adjacent concerns? Common symptom: the doc grew components, env vars, and decision points the operator never asked for.
- **Reviewer E — Scope-supersession check**: does the new design contradict an existing CLAUDE.md, README, or contract in the same repo? The browserclaw review caught this — design said "automatic auth" but `projects/browserclaw/CLAUDE.md` said "Manual auth only. No auth bypass." That's a silent contradiction, not a tunable.

## Template

```markdown
# /advice Decision + Artifact — Design-Spec Review

## DECISION (3-5 sentences)
[What specifically needs review. For a design spec: "Design doc <name> at <path>
proposes <scope>. Need a second opinion on whether the operator's actual goal
is answered, whether the components are load-bearing vs decorative, whether
the design silently contradicts existing contracts in the same repo, and
whether the cited external claims are verifiable."]

## ARTIFACT (≤150 lines, claim-bearing excerpts only)
[Same distillation rule as docs-accuracy: drop boilerplate, drop install
sections, drop config tables — they don't bear accuracy claims. For a
design spec, the load-bearing sections are usually: Executive summary,
Goals, Non-goals, Component descriptions, Architecture diagram, State
machine (if any), Approval/Escalation policy (if any), Final design
decisions.]

### Doc §"<section>" — claim-bearing excerpts
> [quote 1-3 sentences that make a verifiable claim]

### Doc §"<section>" — claims under review
**L1 ...**: enforces X
**L2 ...**: enforces Y
**L3 ...**: enforces Z

### Source: <existing contract path>:<line>
> [the existing CLAUDE.md / README / SOUL.md commitment that the design
> must not contradict]

## QUESTIONS FOR THE REVIEWER

1. **[Operator-intent fidelity]**: does the design answer the user's stated
   goal, or has it grown scope into adjacent concerns the user didn't ask for?
2. **[Scope-supersession]**: does the design contradict any existing
   CLAUDE.md, README, contract, or SOUL.md commitment in the same repo or
   operator profile? Name the file:line being contradicted.
3. **[Component load-bearing]**: which components in the architecture diagram
   are doing real work vs which are decorative (mentioned but never
   referenced by any flow)? A component with no caller is usually over-design.
4. **[State machine completeness]**: if the design names a state machine +
   failure classifications, do all classifications have a corresponding
   transition / terminal node?
5. **[External-claim verifiability]**: which cited external claims (vendor
   docs, OSS projects, security assertions) are actually verifiable, vs
   which are restated marketing copy? Per `research-integrity.mdc`, proving
   presence needs only one hit, proving absence requires exhausting sources.
6. **[Fabrication check]**: does any claim in the design contradict the
   existing source contracts?

## DELIVERABLE — 5 reviewers (not 3)

| Reviewer | Verdict | Confidence |
|---|---|---|
| A — Source accuracy (existing contracts vs design claims) | NEEDS-FIXES | high/medium/low |
| B — External docs (vendor + cited OSS) | UNVERIFIED | medium |
| C — Adversarial (boundary cases, state-machine completeness) | NEEDS-FIXES | high |
| **D — Operator-intent fidelity (does it answer the actual goal?)** | NEEDS-FIXES / APPROVED-as-is | medium |
| **E — Scope-supersession (does it contradict existing contracts?)** | NEEDS-FIXES / PASS | high |

## Evidence table (5 columns is fine for design specs)
| # | Doc claim (file:line) | Source/external conflict | Severity | Reviewer |
|---|---|---|---|---|
| 1 | "automatic auth, manual fallback as exception" (Doc §Goals L74) | `projects/<repo>/CLAUDE.md` L3: "Manual auth only. No stealth, evasion, or auth bypass features." | HIGH | E |
| 2 | "NotificationRouter default: hermes-dm:<operator_id>" (Doc §NotificationRouter L327) | <operator_id> source not named — implementable default unclear | MEDIUM | D |
| ... | | | | |

## Reviewers consulted
- Reviewer A (source accuracy, model X): verdict + confidence
- Reviewer B (external docs, model Y): verdict + confidence
- Reviewer C (adversarial, model Z): verdict + confidence
- Reviewer D (operator-intent fidelity, model W): verdict + confidence — **NEW**
- Reviewer E (scope-supersession, model V): verdict + confidence — **NEW**

## Disagreements not resolved
[Same shape as the canonical SKILL.md]

## Specific fixes the design doc needs (numbered list)
1. ...
2. ...

🧠 Memories used: [source:..., ids_or_labels:..., effect:...]
```

## Worked example: browserclaw-autonomous-browser-control-design.md (2026-07-30)

The design proposed expanding `projects/browserclaw/` (a HAR-capture + endpoint-inference + Python-client-generator tool) into an **autonomous, outcome-driven web controller** with durable runs, capability catalog, Aside as browser dependency, dual-channel approval/escalation, and a CLI + service runtime.

The 5-reviewer fan-out caught:

- **Reviewer A (source accuracy, MiniMax-M3)**: NEEDS-FIXES, high — 8 silent conflicts with `projects/browserclaw/CLAUDE.md` L1-7 ("Manual auth only"), `generator.py` (`requests.Session` consumer contract), and four SOUL.md `## COMMIT:` blocks.
- **Reviewer B (external docs, MiniMax-M3)**: UNVERIFIED, medium — Aside password-autofill claim and 4 of 5 OSS citations not fetched.
- **Reviewer C (adversarial, MiniMax-M3)**: NEEDS-FIXES, high — state machine silently omits the `recovery_exhausted` terminal classification that the same document defines; `human_verification_required` boundary undefined.
- **Reviewer D (operator-intent fidelity, MiniMax-M3)**: NEEDS-FIXES, medium — operator said "I dont care about using cookies or copying them" but the design loaded 29 cookie-related bullet points; the design also asked the operator to choose between notification channels when the user explicitly asked for "optional / env variable controlled."
- **Reviewer E (scope-supersession, MiniMax-M3)**: NEEDS-FIXES, high — design said "automatic auth, manual fallback as exception" but `projects/browserclaw/CLAUDE.md` says "Manual auth only. No stealth, evasion, or auth bypass features." Neither side acknowledged the contradiction.

The review surfaced **20 numbered findings**, of which **4 were load-bearing HIGH/MEDIUM** and became the D-patches the user then asked for: state-machine gap (HIGH), `operator_id` source (MEDIUM), cookie storage backend (LOW), fetched Aside password-autofill reference (LOW).

**Lesson:** the docs-accuracy template is right for "are these merged docs accurate against source X?" but wrong for "is this design ready to implement?" The design-spec review adds two reviewers (D + E) that don't exist in the canonical pattern, and they catch different classes of bug:

- Reviewer D catches **over-design and operator-load mismatches** — the agent wrote 800 lines when the operator wanted 200.
- Reviewer E catches **silent contract contradictions** — the design says X but the existing CLAUDE.md says not-X, and neither side mentions it.

## When NOT to use this template

- For "are these merged docs accurate?" → use the docs-accuracy template in canonical SKILL.md §"Docs-accuracy review template".
- For "review this patch / diff / content edit" → use the patch-review template in canonical SKILL.md §"Patch review template" + `references/patch-review-taxonomy.md`.
- For "compare two design options" → use the generic `Decision + Artifact` pattern.
- For "is this PR ready to merge?" → use the `/green` gate-3 substitute recipe in canonical SKILL.md.

Use this template when the artifact is a fresh design specification and the user is asking whether it's ready to implement.
