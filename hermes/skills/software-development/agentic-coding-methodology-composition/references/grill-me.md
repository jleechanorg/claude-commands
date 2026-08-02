# grill-me / grilling

- **Author(s):** Matt Pocock
- **Canonical source:** https://github.com/mattpocock/skills
- **License:** MIT (per repo)
- **Local install status:** Installed at `~/.claude/skills/{grill-me, grilling, grill-with-docs, batch-grill-me, ask-matt, setup-matt-pocock-skills, to-spec, to-tickets, tdd, implement, handoff, teach, research, prototype, code-review, codebase-design, domain-modeling, diagnosing-bugs, improve-codebase-architecture, resolving-merge-conflicts, wayfinder}` (21 Matt Pocock skills installed together by `--skill=grill-me`/`grilling`/etc. selectors that fan in the related family). Grill-me keeps `disable-model-invocation: true` — opt-in only.
- **Mirror entries:** `Jekudy/grillme-skill` (third-party fork), `alirezarezvani/claude-skills/grill-me` (third-party mirror).

## One-line positioning

A relentless Socratic interview primitive — three sentences that force alignment.

## Core question it asks

"Have you actually thought this through?"

## Core contract (verbatim from `skills/productivity/grilling/SKILL.md`)

> Interview me relentlessly about every aspect of this until we reach a shared understanding. Walk down each branch of the decision tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.
>
> Ask the questions one at a time, waiting for feedback on each question before continuing. Asking multiple questions at once is bewildering.
>
> If a *fact* can be found by exploring the environment (filesystem, tools, etc.), look it up rather than asking me. The *decisions*, though, are mine — put each one to me and wait for my answer.
>
> Do not act on it until I confirm we have reached a shared understanding.

## Family (all in `mattpocock/skills/skills/productivity/`)

| Skill | Role |
|---|---|
| `grilling` | Interview primitive — callable by other skills |
| `grill-me` | User-facing front door — pure interview, writes nothing (frontmatter: `disable-model-invocation: true`) |
| `grill-with-docs` | Same interview + writes `CONTEXT.md` glossary / ADRs |

## Distinctive features (what it does that others don't)

- **Pure interview primitive.** Doesn't implement, doesn't write code, doesn't own the process.
- **Stateless by default.** Alignment lives in the chat; durable artifacts require `grill-with-docs`.
- **One question at a time.** Refuses to batch.
- **Recommended answer per question.** Forces the agent to commit, not just list.
- **Anti-framework philosophy.** The broader `mattpocock/skills` README contrasts approaches like GSD / BMAD / Spec-Kit as frameworks that "own the process and take your control."

## Invocation model

**Opt-in only.** The `grill-me` SKILL.md frontmatter explicitly sets `disable-model-invocation: true` — the agent will never auto-fire it. User must type `/grill-me` explicitly.

## Artifact tree

- `grill-me` → nothing
- `grill-with-docs` → `CONTEXT.md` + ADRs

## Multi-harness support

Claude Code (canonical target via `npx skills@latest add mattpocock/skills --skill=grill-me -y -g`). Other harnesses via the `skills` package manager.

## Installation paths (verified)

```bash
# Claude Code / Codex / Cursor etc.
npx skills@latest add mattpocock/skills --skill=grill-me -y -g

# Or just grilling (the primitive)
npx skills@latest add mattpocock/skills --skill=grilling -y -g
```

## Known anti-patterns

- **Don't use `grill-me` during execution.** It's an interview primitive, not an executor. Use it for upstream alignment, not for in-loop debugging.
- **Don't batch questions.** The skill refuses to batch — that's the design.
- **Don't act on partial alignment.** "Do not act on it until I confirm we have reached a shared understanding."
- **Don't use `grill-me` and Superpowers' `brainstorming` simultaneously.** They're both Socratic. Pick one as the per-phase alignment driver.
- **Don't expect grill-me to write code or design docs.** Use `grill-with-docs` if you need a CONTEXT.md artifact.

## Composition with other methodologies

| Combo | Verdict |
|---|---|
| Grill-me → Superpowers brainstorming | ✅ Recommended. Grill-me for raw alignment, then Superpowers' structured design + HARD-GATE. |
| Grill-me → GSD `/gsd-discuss-phase` | ✅ Recommended. Grill-me one-at-a-time → GSD's batched CONTEXT.md as audit trail. |
| Grill-me during Superpowers execution | ❌ Anti-pattern. Interview primitives don't belong in execution loops. |
| Grill-me + GSD + Superpowers all global | ⚠️ Risky. Pick one default per session; bring others in per-phase. |

## Sources

- https://github.com/mattpocock/skills (canonical, verified 2026-07-30)
- https://github.com/Jekudy/grillme-skill (third-party mirror)
- https://skillselion.com/skills/alirezarezvani/claude-skills/grill-me (third-party mirror)
- https://ryanuo.cc/en/posts/grill-me-vs-superpowers (third-party comparison, reviewed 2026-07-30)