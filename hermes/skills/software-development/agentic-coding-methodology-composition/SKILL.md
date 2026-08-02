---
name: agentic-coding-methodology-composition
description: When the user asks to compare, evaluate, or compose AI coding agent methodologies and skills frameworks (Superpowers, GSD Core, grill-me, OpenSpec, BMAD, Spec-Kit, Kiro, gstack, GSTACK, custom /skill packs). Use for "should we install X?", "how do X and Y differ?", "can we combine Z with W?", "is there a methodology for X?", or any question about how multiple AI-tooling philosophies interact. Class-level umbrella covering methodology profiling, installation status verification, composition pattern analysis, and anti-pattern documentation.
---

# Agentic Coding Methodology Composition

Compare, evaluate, and compose AI coding agent methodologies and skills frameworks. Class of work: "should we use methodology X?" / "how do X and Y compare?" / "can Z and W coexist?" / "why is my agent misbehaving in a way that maps to a methodology design?".

## When to load this skill

- User asks about a specific AI coding methodology (Superpowers, GSD Core, grill-me, OpenSpec, BMAD, Spec-Kit, Kiro, gstack, GSTACK, custom /skill packs).
- User asks "should we install X?" / "is X worth it?" / "how do X and Y differ?".
- User asks for a combo analysis ("can we run X with Y?" / "what's the best of both worlds?").
- User asks about an emerging methodology and wants to know how it relates to existing ones.
- User reports an agent failure that maps to a methodology design (e.g., "it skipped TDD" → check Superpowers' HARD-GATE; "context bloat after 2 hours" → check GSD Core's context-engineering rationale).

## Methodology landscape (snapshot 2026-07-30)

| Methodology | Author | Canonical source | Local status |
|---|---|---|---|
| Superpowers | Jesse Vincent (obra) | https://github.com/obra/superpowers | Installed v6.2.0 |
| GSD Core | TÂCHES | https://github.com/open-gsd/gsd-core | Installed v1.9.0 (`--profile=full`) — see `--profile` pitfall |
| grill-me / grilling | Matt Pocock | https://github.com/mattpocock/skills | Installed (21 Matt Pocock skills at `~/.claude/skills/{grill-me,...}`) |
| OpenSpec | Fission-AI | https://github.com/Fission-AI/OpenSpec | Not installed |
| BMAD Method | bmadcode | https://github.com/bmadcode/BMAD-METHOD | Not installed |
| Spec-Kit | GitHub | https://github.com/github/spec-kit | Not installed |
| Kiro Specs | AWS | https://kiro.dev | Not installed |
| GSTACK | garrytan | https://github.com/garrytan/gstack | Not installed |

(See `references/` for per-methodology profiles with verified installation paths, distinctive features, and source-of-truth URLs.)

## Workflow — methodology-composition analysis

### Phase 0: clarify scope

Single-methodology or comparison? If comparison, name candidates or "compare all major frameworks" (≥3).

### Phase 1: canonical-source verification

For each methodology:
1. **Find the canonical repo** — GitHub org, official docs site, npm package, plugin marketplace. Reject mirrors/forks unless explicit.
2. **Verify recency** — confirm the canonical repo is still maintained. Watch for "this repo has moved" redirects (e.g., `gsd-build/get-shit-done` archived → `open-gsd/gsd-core`).
3. **Verify local install** — see `references/installation-check.md`.

### Phase 2: profile each methodology

Use `references/methodology-profile-template.md` to capture:
- Author + canonical source
- One-line positioning
- Pipeline / loop / workflow
- Distinctive features (what it does that others don't)
- Invocation model (auto-fire vs opt-in)
- Artifact tree (where state lives)
- Multi-harness support
- Known anti-patterns

### Phase 3: composition analysis

Identify:
- **Overlap zones** (where two methodologies do similar things — pick one as authoritative).
- **Complement zones** (where one extends the other).
- **Conflict zones** (where one explicitly fights the other, e.g., Superpowers' HARD-GATE vs opt-in frameworks).
- **Outer-loop / inner-loop splits** (GSD Core for milestone continuity, Superpowers for per-task TDD).

Output: a composition-recommendation matrix with concrete install paths.

### Phase 4: anti-pattern audit

Check against `references/composition-patterns.md` for known anti-patterns. Flag any that apply to the user's setup.

### Phase 5: deliver

Slack-native format per SOUL.md `colored-icons-in-status-reports`:
- 🟢 Healthy (sources confirmed, install status)
- 🔵 What each does that others don't
- 🟡 How they compose
- 🔴 Risky / anti-patterns
- 🟢 Recommended combo
- 🔵 Next actions

Apply LLM-provenance caveat footer per SOUL.md `llm-provenance-caveat`. Hyperlink every URL per `no-trailing-asteri[REDACTED_OPENAI_KEY]` and `pr-hyperlink` rules.

### Phase 5.5: execute the install (don't post the list and stop)

**Load-bearing rule, verified 2026-07-30.** When the recommended-combo or Next-actions section enumerates installable commands (`npx @opengsd/gsd-core@latest --claude --global`, `npx skills@latest add mattpocock/skills --skill=grill-me -y -g`, etc.) AND the user said anything like "install them", "set it up", "go ahead", "ship it", "let's do X" — **execute the install in the same turn**, do not post the list and wait. The user will read the install summary in the next reply, not a static plan.

If the user asked for analysis only ("compare X and Y", "how do they differ"), do not install — analysis-only is a valid request.

If the user gave a guarded install directive ("install them all but don't add default guidance"), execute the install but **honor the guard**:
- Default-install flags that auto-enable hooks → downgrade to lean profile (GSD: `--profile=core` not `full`; grill-me keeps `disable-model-invocation: true`).
- Default guidance files → don't touch (`SOUL.md`, `CLAUDE.md`, plugin enable flags).
- Verify post-install what got auto-configured and call it out honestly in the next reply. Don't hide it.

## Anti-patterns (load-bearing)

1. **Don't recommend installing all global frameworks.** Superpowers' HARD-GATE will fight GSD's `/gsd:*` namespace and grill-me's `disable-model-invocation: true`. Pick one as the per-session default; bring others in explicitly per-phase.
2. **Don't accept GSD's `--profile=full` default when the user said "no default guidance."** Full installs ~15 always-on hooks to `settings.json` (verified v1.9.0). Use `--profile=core` (~700 tokens eager-load) instead. See `references/gsd-core.md` for the full hook table.
3. **Don't duplicate state trees.** GSD → `.planning/`. Superpowers → `docs/superpowers/{specs,plans}/`. grill-me → nothing or CONTEXT.md. Designate one artifact tree as authoritative.
4. **Don't use a pure interview primitive (grill-me) inside an execution loop.** Grill-me is for upstream alignment only.
5. **Don't recommend a framework whose canonical repo has moved without flagging the redirect.** Always verify the live repo.
6. **Don't treat star counts as signal of correctness.** GSD's 48.3k stars ≠ better than Superpowers' smaller community. They solve different problems.
7. **Don't claim a methodology is "installed" without probing the filesystem.** See `references/installation-check.md`.
8. **Don't create status-cron jobs that ping the user about a choice they're still making.** When the user says "install X but don't add default guidance," a 20m cron pinging them about "did you pick a combo?" violates the directive. Wait for the user's own next message; don't schedule a nudge.

## Support files

- `references/methodology-profile-template.md` — capture template for one methodology
- `references/superpowers.md` — Superpowers profile (obra, installed v6.2.0)
- `references/gsd-core.md` — GSD Core profile (TÂCHES, not installed)
- `references/grill-me.md` — grill-me profile (Matt Pocock, not installed)
- `references/composition-patterns.md` — verified combinations with anti-patterns
- `references/installation-check.md` — how to verify local install status per methodology

## How to extend this skill

When a new methodology emerges:
1. Verify the canonical source (live repo, official docs).
2. Add `references/<name>.md` profile using the template.
3. Update `composition-patterns.md` if it composes with existing methodologies.
4. Update the landscape table in this SKILL.md.

When a methodology moves (e.g., `gsd-build/get-shit-done` → `open-gsd/gsd-core`):
1. Update the profile's canonical source.
2. Note the redirect history in the profile.
3. Grep existing references for stale URLs.