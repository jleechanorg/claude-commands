# Brainstorming-Handoff Contract

The `brainstorming` skill is a **bundled skill** shipped with the `claude-plugins-official/superpowers` plugin (v5.0.7 verified 2026-07-20). It is **protected** — we cannot edit it. Instead, this reference defines the *handoff contract* between this skill (the iteration design workflow) and the brainstorming skill (the derivation workflow) when the user names a reference shape in their design brief.

---

## When this reference fires

The handoff fires when **any** of these signals are present in the user message:

- The user names a specific reference campaign ("like BG3", "like God of Murder", "like the Dark Urge", "like Berserk", "like Mistborn's Lord Ruler", "like Cosmere's Shards", etc.)
- The user names a specific module from an open PR (`"see if we made any PRs"` or `"see PR #8483"` or `"see the Sanguine Architecture module"`)
- The user wants the vN+1 to **rival a reference** ("do it like the Avengers", "do it like Cosmere")
- The user wants a **class of mechanic** applied to the vN+1 setting ("add an ascension track", "add a god-mode endgame")

The handoff does NOT fire for:

- Pure iteration over the user's own prior versions (the 8-phase workflow handles this)
- New content not derived from a reference (e.g. "design v10 from scratch")
- A small adjustment / patch (Phase 0 question first, then patch — no brainstorm needed)

---

## The Handoff Protocol (5 steps)

### Step 1 — Resolve the brainstorming skill from a Hermes session

The `brainstorming` skill is **not loaded into Hermes by default**. From a Hermes session:

```bash
# 1. Try skill_view first
skill_view(name='brainstorming')   # may return "not found" — that's expected

# 2. Fallback: read from the plugin cache directly
read_file(path=~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/skills/brainstorming/SKILL.md)
```

From a Claude Code session, type `/superpowers-brainstorm` (the slash command is auto-resolved). For Codex sessions, the command mapping is at `~/.claude/commands/superpowers-brainstorm.md`.

Do NOT skip this step if `skill_view(name='brainstorming')` returns "not found." The skill lives in the plugin cache, not in Hermes's skill namespace. Skill_not_found on `brainstorming` is not authorization to skip — it's a routing problem.

### Step 2 — Run the brainstorming protocol verbatim

Follow `~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/skills/brainstorming/SKILL.md` exactly. The protocol has a **HARD-GATE**:

> Do NOT invoke any implementation skill, write any code, scaffold any project, or take any implementation action until you have presented a design and the user has approved it.

This means: **stop all 8-phase iteration work the moment the handoff triggers.** Do NOT start patching the Google Doc, do NOT start drafting the wiki, do NOT start sketching the section 3. The brainstorming skill's job is to derive *what the user wants from the reference as a class*, and then design from that derivation. Renaming a reference's mechanic into Visenya's setting without running brainstorm is the failure mode P11 documents.

### Step 3 — Produce the brainstorming deliverables

The brainstorming skill produces:

1. **Exit criteria section** — binary, executable, externally anchored checks for "what's DONE."
2. **Spec at `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`** — committed to git, with Provenance.
3. **Architecture / components / data flow** — broken into small, testable units.
4. **User-approval gate** — present sections one by one, get approval between each.

For this skill's handoff specifically, the **spec must cover**:

- The 3 recurring taste pillars for the user's character (e.g. Visenya: hidden Apex blood / mortal anchor / scaling tension). These are NOT to be re-derived in brainstorming — they are pre-established facts from prior v(N-1) iterations.
- The **4-part mechanic stack** for the vN+1 endgame (Anchor / Trigger / Aspect Shift / Successor — see Pitfall P12 in SKILL.md).
- The **derivation target** — what vN+1's endgame question is (different from the reference's).
- The **specific open WA PRs/issues** that the vN+1 spec guards against (the G1–GN guardrail mapping — Phase 7 of the 8-phase flow).

### Step 4 — Handoff back to the iteration workflow

Once the spec is committed and the user has approved it, **resume the 8-phase iteration flow**:

- Phase 5 (Write the vN+1 bible) — write the bible to Google Doc + /tmp
- Phase 6 (Cross-link the wiki)
- Phase 7 (Map the spec → open WA PRs) — *this is a checklist at this point, not a derivation*
- Phase 8 (Commit cleanly from origin/main)

The brainstorming spec is the **source of truth** for all 8 phases. Do NOT re-derive the endgame mechanics in Phase 5. Use the spec verbatim.

### Step 5 — Note the handoff in Provenance

In the vN+1's wiki source page Provenance footer, cite:

> Brainstorming handoff from `references/brainstorming-handoff.md` (verified YYYY-MM-DD, [reason]). Source spec: `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`.

This makes the brainstorming artifact grep-able from the wiki next iteration, so the next vN+1 can resolve "what was the brainstorm that produced this design" without re-running.

---

## Anti-pattern: skipping the brainstorm because the reference is "obvious"

The reference is **never** obvious. The user's taste profile is the actual shape; the reference is a prompt. The first turn that says "I want Visenya to ascend to godhood at L20, like BG3 God of Murder" looks like it can be answered by importing PR #8483's structure. It can't. The user will *immediately* notice when Mantle of the Sanguine Slayer replaces Mantle of the Radiant Slayer and the underlying mechanic stack is identical. **The user knows their own prior art well enough to catch a renamed import.**

Verified incident 2026-07-20: Visenya v9 session imported PR #8483's BG3 endgame shape verbatim. User corrected within 22 minutes of doc creation with *"Wait w shouldn't just copy the bhaal god of murder thjng it's just an example."* The fix did not get re-architected — only the doc patches were rolled back. **If a brainstorming spec had been produced first, the design would have derived instead of imported.**

---

## Failure modes this contract prevents

| Failure | Without brainstorm | With brainstorm |
|---|---|---|
| User names BG3 | Mechanic is renamed Mantle of the Sanguine Slayer, same 4-phase cosmic escalation as BG3 | Spec asks "what does a sovereign god *Visenya-shaped* leave behind?" — answers differently |
| User wants v10 to have wings | Add "Mantle of the Radiant Slayer" style wings, copy Bhaal's two visual aspects | Spec derives *Visenya's* silhouette (dragonglass-cloak, braid-locked hair, scar across nose) and builds a different two-aspect toggle around it |
| User wants the campaign difficult at L20 | Add Reputation Die escalating to d20 — same as v9 | Spec asks "what is *interesting* about L20 Visenya that isn't repetition of L6 Visenya" — derives a *new* tension mechanic (e.g. Sanguine Thread page-thresholds) |
| User names three reference campaigns | Three reference mechanics blended with rename | Spec takes the *category* (god-mode endgame with interesting successor question) and rebuilds for vN+1 |

---

## Worked example: Visenya v9 2026-07-20 (this session)

**What actually happened** — three distinct user corrections over ~30 minutes:

1. User asked for "level 20 and then become a Demi god and god and still have an interesting and challenging end game see my attempts with the bg3 god murder campaign." Agent **skipped brainstorming**, jumped straight to patching the doc with PR #8483's mechanics. The doc was uploaded with `Sanguine Thread / Mantle of the Sanguine Slayer / Mantle of the Radiant Slayer / Sanguine Sovereign / Chitinous Ruin / 5-Pillar Dread Court / 3-Generation Power Lineage / Divine Rank 0→16+ / Thread Eternal` — almost all renamed-but-otherwise-imported from PR #8483.
2. ~22 minutes after doc creation, user noticed: *"wait w shouldn't just copy the bhaal god of murder thjng it's just an example"*. Doc patches were rolled back; the brainstorm then ran a clarifying thread and produced spec Section 12 (the 4-phase cosmic escalation, 3-Generation Power Lineage) — *but that section was lifted from PR #8483 verbatim*. The names were locally renamed, but the *shape* was still imported.
3. User then asked *"what is Sanguine Thread? I think that might be too much god of murder?"* — agent had no good answer because the mechanic was imported. User then said *"don't make me pick an ending, just save possibilities, we're designing the campaign not a fully decided story"* and *"I want B) one system multiple emergent endings"* — pivoting from story to system.
4. Brainstorm derived: lineage-not-sin Sanguine Thread, First Song as V6-Visenya, identical-mechanics-not-copy Magic Barrier System, 4 emergent endings (Joining / Replacement / Refusal / Player-defined), Doom-as-apotheosis. Document shipped correctly.

**Three failure modes visible in that sequence** — each captured by a different pitfall:

| Step | Failure | Caught by |
|---|---|---|
| 1 | Skipped brainstorming; jumped to implementation | **P13** (brainstorm-before-design when reference named) |
| 2 | Imported mechanics verbatim even after restarting brainstorm | **P11** (renamed import) + **P12** (4-part stack derivation) |
| 3 | Designed campaign as a *story* with one canonical ending | **P14** (system ≠ story; four-mode resolution ladder) |

Plus the user's *"take inspiration, don't directly copy"* correction is captured by **P15** (refuse to copy even with plausible renames).

**What should have happened** — one coherent path:

1. User named "BG3 god murder campaign" + "interesting endgame" + "level 20 → demi-god → god" — handoff fires (Step 1, this contract).
2. Load `brainstorming` skill from the plugin cache (Step 2) — `read_file` since `skill_view(name='brainstorming')` returns "not found" in Hermes.
3. Run brainstorming protocol — Phase 0 clarifying questions, *including* the four-mode resolution question ("interesting endgame means what? A=morally consequential, B=adversarially matched, C=worldbuilding aftermath, or D=player's choice at the table?"). Do NOT ask "pick the canonical ending."
4. Derive a 4-part mechanic stack for *Visenya* (not BG3). The derivation target for Visenya is: *what does a sovereign god leave behind, and is that inheritance worth wanting?* Write the spec at `docs/superpowers/specs/2026-07-20-visenya-v9-blood-dragon-campaign-design.md` (Step 3).
5. Get user approval (Step 4 of brainstorming protocol).
6. Resume Phase 5 of the 8-phase iteration flow (Step 4 of this contract) using the spec as source of truth.
7. Note the brainstorming handoff in Provenance (Step 5).

The right outcome: same general shape (L20 → demi-god → god, interesting endgame, BG3 reference acknowledged) but **derived mechanic names, derived visual aspects, derived successor question, four-mode resolution ladder** — none of PR #8483's mechanics verbatim, and no single canonical ending.

**Earlier version of this section** (v1.0.0 of `references/brainstorming-handoff.md`) incorrectly described the workaround as a single pivot. The actual session took **three pivots**, each catching a different failure mode. The five-step protocol here would have *prevented all three pivots by running brainstorm first*.

---

## Provenance

- v1.0.0 (2026-07-20): Created in response to Visenya v9 session importing PR #8483's BG3 endgame shape verbatim. The handoff contract documents the protocol that *would have* prevented the import. Verified: brainstorming skill location (`~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/skills/brainstorming/SKILL.md` v5.0.7), slash-command resolution path (`~/.claude/commands/superpowers-brainstorm.md`), hard-gate language ("no implementation before design approval").
- v1.1.0 (2026-07-20): Rewrote the "Worked example: Visenya v9 2026-07-20" section to capture the *actual* session path (three user corrections over 30 minutes, not one). Mapped each correction to a specific pitfall (P11/P12/P13 + new P14 system≠story + new P15 take-inspiration-not-copy) in the umbrella `campaign-design-iteration` SKILL.md. Added explicit guidance: do NOT ask "pick the canonical ending" — campaign design is system design, never story design.
