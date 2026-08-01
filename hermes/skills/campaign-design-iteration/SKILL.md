---
name: campaign-design-iteration
description: |
  Design a new version (vN+1) of a recurring user campaign by re-reading every
  prior version in Google Docs and the wiki, extracting the user's 3 recurring
  taste-pillars, picking ONE pivot variable per version, writing the new
  campaign bible to Google Doc AND wiki repo with cross-linked concept/entity
  stubs, then mapping the spec to specific open WA prompt-layer PRs/issues as
  **anti-invention guardrails**.

  Trigger phrases: "design Visenya v<N+1>", "new campaign iteration",
  "pivot the campaign", "redesign [character]", "predict my taste", "did
  you actually read X".

  Distinct from `wa-campaign-content-analysis` (existing-campaign audit) and
  `download-campaign` (export existing campaign to wiki). This skill is the
  *forward* design workflow when the user wants a NEW iteration.

  v1.0.6 (2026-07-21) P28-P30.
  v1.0.5 (2026-07-21) P21-P27 god-mechanics layer.
  v1.0.7 (2026-07-21) P31-P32 + load-bearing-math-design reference created.
---

# Campaign Design Iteration — vN to vN+1

The class of work this skill covers: **redesigning a recurring user campaign character across many versions** (Visenya v1→v9 is the canonical case; the user has iterated on this character at least 8 times). Each iteration reads prior versions from Google Docs and the wiki, identifies the user's recurring taste pillars, picks a single pivot variable, writes the new bible to Google Doc + wiki, and ties the new spec to the WA prompt layer's open issues.

The skill is **forward** (create a new vN+1) — not backward (audit an existing campaign; see `wa-campaign-content-analysis`).

## When to load

Load this skill when ANY of the following signals fire:

| Signal | Example |
|---|---|
| User says "design v(N+1) of [campaign]", "next iteration of Visenya/Daenerys/Sariel" | "design Visenya v9" |
| User says "redesign/pivot the campaign" | "pivot v9 to your new direction" |
| User says "what if [character] was [different pivot]?" | "what if Visenya was a proper Targaryen?" |
| User references prior versions explicitly | "I want it to be like v6's Blood Dragon but for Dunk & Egg" |
| User asks to brainstorm new directions | "brainstorm a way to make them more interesting" |
| User names explicit guardrails mid-design | "add strict guardrails against scrying detection and out-of-lore events" |
| User asks for an open-PR audit alongside the design | "see if we made any PRs yet to fix this stuff" |

## Workflow — 8 Phases

### Phase 1: Ingest prior versions
- `gog drive search "<character-name>"` → list prior campaign docs (titles, dates).
- `gog docs cat <DOC_ID> > /tmp/<campaign>-v<N>.txt` for each prior version. Cache to /tmp so you can re-read without hitting Drive.
- `gog docs info <DOC_ID>` for metadata (last edit, owner) — useful for chronological ordering.
- **Local wiki version:** `ls ~/llm_wiki/wiki/campaigns/<character>/`, `ls ~/llm_wiki/wiki/sources/ | grep -i <character>`, `ls ~/llm_wiki/raw/campaigns/`.
- **Goal:** build a summary table mapping version → setting/year → age → class → pivot-twist. See reference template in `references/version-comparison-template.md`.

### Phase 2: Extract the 3 recurring taste pillars

Across all prior versions, identify the **3 pillars that show up in nearly every iteration**. For Visenya they were:

1. **Hidden Apex bloodline** — mathematically outclasses everyone, not louder/faster, *unfair by design*
2. **Moral/mortal anchor** — a character who keeps her from drifting into pure villain-fantasy
3. **Scaling tension mechanic** — Heat System, Ascension Meter, Entropy Toll, Sovereign Power, Reputation Die

A good vN+1 preserves all 3 pillars and changes *one pivot variable* per version. The pillars are durable; the pivot is what makes each version feel new.

The **CHA-substitution trick** is a meta-pattern that recurs: each version picks a different stat-as-CHA-substitution. v1 used INT/WIS (charisma through intellect). v9 uses DEX/WIS (you do not charm, you arrive uninvited). The pivot is in what *channel* the power flows through.

**Pillar catalogue (verified pillar-vs-pivot distinction across 9 versions + the God of Murder branch, 2026-07-20; + Spellblade/Mortal Blade branch 2026-07-28):**

| Pillar | What it looks like across versions | When to KEEP vs when to PIVOT |
|---|---|---|
| Hidden Apex bloodline | Apex-tier power hidden by mundane presentation | KEEP in EVERY iteration. Pivot is the *application channel* (social geometry ↔ physical geometry ↔ dragon-rider ↔ ruler-of-shadow-kings) |
| Mortal anchor | Companion/lover/parent who grounds the protagonist | KEEP. Pivot is the *who* (Dunk ↔ Daenerys ↔ Davos ↔ Rhaenys) |
| Scaling-tension mechanic | Heat / Ascension / Entropy / Sovereign Power / Rep die | KEEP the existence of a tension mechanic. Pivot is the *currency* (social exposure ↔ resource drain ↔ casualty count ↔ reputation weight) |
| **Quantified Mechanical Engine** *(added 2026-07-20, God of Murder branch)* | Per-phase stat blocks (DR/DPP/DAIR), follower-scaling formulas, per-faction portfolio tension — **system-agnostic god mechanics** that work in any setting (D&D, Cyberpunk, Wuxia, Naruto, Marvel) | KEEP for any vN+1 where the protagonist ascends past mortal tier. Pivot is the *system*: 5e-ported ↔ narrative-only ↔ homebrew-agnostic |
| Trajectory of cost *(added 2026-07-20)* | Each major choice accrues an irreversible debt | KEEP for villain-protagonist arcs. Pivot is the *cost unit* (death count ↔ reputation ↔ selfhood ↔ time) |
| **Consequence-as-cost discipline** *(added 2026-07-28, Spellblade/Mortal Blade branch)* | Failures of explicit responsibility produce a *named, in-system* mechanical cost (e.g. exhaustion level); opaque meters, repeated surprise arrests, and "you become ruler of X" auto-escalations are FORBIDDEN | KEEP whenever the protagonist has *people they are responsible for*. Pivot is the *cost shape*: exhaustion level ↔ reputation bond ↔ divine debt ↔ mortal injury. Default-cost rule: **gain one level of exhaustion when ALL of (a) the PC was officially responsible for the people involved, (b) had a plausible opportunity to prevent the harm, (c) knowingly chose another priority OR failed through avoidable negligence, AND (d) the harm is serious enough to matter.** Do NOT charge exhaustion for good-faith attempts, overwhelming opponent action, non-responsible NPC deaths, reasonable tactical tradeoffs in combat, or shock-value deaths. |

NOTE: Pillars 4, 5, and 6 are **branch pillars** — they're mandatory when the protagonist is post-mortal/superpowered/god-tier (P4) OR has villain-arc costs (P5) OR has people in their care (P6), but they can be SKIPPED in low-power / solo-rogue iterations. The other 3 are core pillars for ALL versions of this class.

**The 4-pillar `campaign-creation` skill (canonical reference for from-scratch designs):** When the user asks for a brand-new campaign (not a vN+1 iteration), use the `campaign-creation` skill instead. That skill encodes the 9-section bible structure + Character Personality Template + Sub-Templates A/B/C, and references `references/god_mechanics_general.md` for the Quantified Mechanical Engine pillar's math.

### Phase 3: Pick the ONE pivot variable
Do not change multiple axes in one iteration — the user wants to feel the *contrast* between versions. Common pivot variables for this class:

- **Setting** (Dunk & Egg ↔ HotD Sowing ↔ Rhaegar-wins ↔ House of the Dragon)
- **Lineage** (House Targaryen proper ↔ House Belaerys cadet ↔ bastard of Daemon)
- **Age** (12 ↔ 14 ↔ 16 — the "level-6 sweet spot" range)
- **Class gestalt** (Bard/Mastermind ↔ Ranger/Rogue ↔ Sorcerer)
- **Power source application** (social geometry ↔ physical geometry ↔ dragon-rider)
- **Moral anchor** (Ser Duncan ↔ Daenerys ↔ Ser Davos ↔ Rhaenys)
- **Reputation mechanic** (Heat System ↔ Ascension Meter ↔ Reputation Die)
- **Endgame cost mechanic** (Entropy Toll ↔ Wound Ledger ↔ Sovereign Burnout)

A vN+1 changes ONE. If the user mid-session pivots a second variable (e.g. "Make me a proper Targaryen" when current version is House Belaerys), that's the pivot — delete-and-recreate the Google Doc to reflect cleanly, don't try to patch the inherited structure.

### Phase 4: Mid-turn pivot handling (delete-and-recreate vs patch)
When the user issues a pivot message after the doc is already drafted:

| Pivot type | Action |
|---|---|
| Changes a major *section* (lineage, setting, moral anchor) | **Delete the Google Doc and recreate with new title.** Inherited structure will mislead the LLM on later reads. The 30-second delete-and-recreate is cheaper than patching inconsistencies out. |
| Adds a *new* dimension (tier-above beauty, new guard rails) | **Patch** the existing doc — append or edit the affected section. |
| Mid-turn addition about open-PR audit | **Read in parallel** (`gh api` REST endpoint, see `gh-rate-limit-and-transient-failures`). Don't bottleneck the design on the audit. |

When pivoting lineage, character sheet fields (DEX, level, class) and the entire **Family / Setting / Gazetteer** sections become wrong — patch alone leaks the old version everywhere. Delete-and-recreate is the right move.

### Phase 5: Write the vN+1 bible
Structure that scales across versions (used in v9, would also fit v3/v6):

1. **Campaign Intro** — concept + hook + why this version is different from v1–vN
2. **Character Personality** — name, archetype, 2-face mask, visual signature, core compulsion, inner monologue
3. **Character Class** — full stat block + level features + 3-5 custom vN+1 homebrew features
4. **Assets & Retinue** — panoply, retinue, inner circle (≥3 NPCs)
5. **Family** — parents + siblings in order of age
6. **The Setting** — canonical-world year, geographic anchors
7. **World Lore — Why She Is The Way She Is** — lineage explanation that canon-fits
8. **Gazetteer & Mechanics** — locations, custom systems, loot table
9. **Starting Scene** — the dramatic opening beat
10. **Hard Guardrails (the "Don't" List)** — see Phase 7
11. **Open PRs Already in Flight Against vN+1** — see Phase 8

Use `gog docs create "<title>"` for the doc shell, then `gog docs write <DOC_ID> < /tmp/<bible>.md` for the body. The bible is one large append (`mode: appended`). For next iteration, **always** start by reading the prior doc's last edit + body so you don't re-invent sections.

### Phase 6: Cross-link the wiki
Two complementary surfaces. Do both:

**Google Doc** = the canonical narrative bible (long-form, prose, design intent). Lives in `gog drive`. Authoritative for humans + LLM-narrative-emit when the campaign runs.

**Wiki page** = the canonical concept index (sections, stat blocks, references, version-comparison table). Lives in `~/llm_wiki/wiki/sources/<campaign>-v<N+1>-<slug>.md`. Authoritative for grep/search and for the LLM that pulls wiki into its system prompt.

The wiki page should NOT mirror the doc 1:1. It's a **pointer**: the vN+1 spec, the 7-guardrail summary table (Phase 7), the 11-PR-link table (Phase 8), the cross-references to existing entity/concept stubs (e.g. [[ApexWeaver]], [[RooksRest]], [[BloodDragonReputationDie]]).

When the vN+1 introduces NEW concepts (e.g. v9 introduced `BloodDragonReputationDie`, `WoundLedger`, `StressLineSight`, `RooksRest`), create **supporting stubs** under `wiki/concepts/` (mechanics) and `wiki/entities/` (locations/NPCs). They're 1-2 KB each, cross-linked, and they prevent the next-version brainstorm from re-deriving the same concept.

**Update the entry points** in the wiki:
- `wiki/index.md` — prepend a Sources entry (one liner + relevant PR links) and prepend any new entity/concept entries
- `wiki/log.md` — add an ingest entry with date, source paths, line count

Follow `wiki-vault-safeguards` for the append-not-overwrite + git push flow.

### Phase 7: Map the spec → open WA prompt-layer PRs as guardrails
The user's complaint about "random antagonistic events that don't fit lore" or "NPCs knowing things they shouldn't" is a **recurring prompt-side anti-pattern** with concrete open PRs already in flight. Don't write a campaign bible that *implicitly* assumes the LLM will behave — wire the spec to the open issues that already exist.

For each user complaint pattern, do this:

1. `gh api repos/$GITHUB_REPOSITORY/issues?state=open&per_page=50` (or use REST directly when GraphQL hits rate limit — see `gh-rate-limit-and-transient-failures`).
2. Cluster the issues/PRs by *user-visible symptom class* (anti-scrying, anti-frictionless, NPC-dialogue-discipline, no-out-of-lore, canonical-state-anchor, etc.).
3. Map each cluster to a **durable guardrail identifier** (G1, G2, …).
4. State the invariant (in human + LLM-prompt-layer terms).
5. Cite the prompt files affected (`narrative_system_instruction.md`, `dialog_system_instruction.md`, `planning_protocol.md`).
6. Cite the audit hook (post-emit token scan, friction watchdog, capability-lock scan).
7. Reference the open PRs/issues at the bottom of the section.

The user does NOT want prompt-engineering principles in the campaign bible — they want a **traceable spec**: "if this issue fires in vN+1, here's the PR/issue that addresses it, here's the invariant, here's where it lives in the prompt." This makes the bible actionable for the WA team: they can grep the bible for `G1`, find the matching PRs, and ship or extend the work.

Verified pattern: v9 mapped to **11 open WA PRs/issues** across **7 guardrails**. Of the 7 guardrails, 3 had partial fixes in flight (#8469, #8443, #8473) and 4 were uncovered (G3 NPC-dialogue, G6 capability-lock, G7 reputation-disciplined, plus the canonical-state-anchor surface).

### Phase 8: Commit cleanly from origin/main (NOT from a polluted branch)
The wiki repo has concurrent agent activity. Before committing:

```bash
cd ~/llm_wiki
git fetch origin main
git rev-parse origin/main     # record baseline SHA
git rev-parse HEAD            # confirm local = origin/main
git status --short            # confirm clean except intended changes
git diff --stat HEAD           # confirm only the intended files are touched
```

**Pitfall:** if `git diff origin/main..HEAD` shows `Merge remote-tracking branch`, unrelated `fixpr` commits, or `.beads/issues.jsonl` drift, the local branch has been polluted. `git reset --hard origin/main` is the recovery BEFORE adding the new files.

Then stage ONLY the intended files, commit, and push:
```bash
git add wiki/index.md wiki/log.md wiki/sources/<new>.md wiki/concepts/<new>*.md wiki/entities/<new>*.md
git commit -m "feat(campaign): <name> v<N+1> — <one-line pivot>"
git push origin HEAD:refs/heads/main
```

Follow `pr-branch-from-main` discipline: every wiki push should be a fresh branch (or fast-forward) from `origin/main`. See `pr-clean-branch-from-main-no-history-bloat` for the rule. The llm_wiki repo has no branch protection (verified 2026-07-20), so direct `main` push is allowed — but you still want a clean history.

### Pitfalls

**P36 — Mid-campaign mechanic invention is the recurring failure. Define mechanics at campaign creation; default is D&D 5e; lore-specific exceptions are only valid when explicitly introduced.** (added 2026-07-29, cross-campaign audit of 230 LLM-wiki transcripts / 12,498 God Mode messages)

The user's repeated corrections across unrelated campaigns: *"Signatures are forbidden"*, *"The inquisition shouldn't know about my magic"*, *"What magic residue would [NPC] see? I didn't use any magic"*. The failure mode is the LLM inventing remote-sensing channels, signature-based detection, or institutional jurists that D&D 5e does not have. Not even low-level spells from far away should summon an "auditor / inquisitor / planar watcher" with no written range or target.

**Default ruleset assumption (D&D 5e unless overridden at campaign creation):**

| D&D 5e bounded detection/divination spell | Range / Limit |
|---|---|
| `Detect Magic` (1st-level ritual) | Active concentration; senses magic within **30 feet** of the caster; aura revealed only on visible creature/object in the 30-ft radius |
| `Detect Thoughts` (2nd-level) | Caster sees a creature within **30 feet**; deeper probing requires a Wisdom save; returns surface thoughts by default |
| `Clairvoyance` (3rd-level) | Sensor at a familiar or obvious location within **1 mile**; one sense at a time; **not** an omniscient remote viewer |
| `Scrying` (5th-level) | Same plane; target gets Wisdom save; -5/+0/+5 by familiarity; -2/-4/-10 by physical connection; blocked by `Mind Blank` / `Nondetection` |
| `Locate Creature` (4th-level) | Self; **1,000-foot** direction-only; target must be *familiar*; blocked by running water ≥10 ft wide |
| `Nondetection` / `Mind Blank` | Explicit protection against divination and magical scrying sensors |

Anything else — a "god watching the weave" detection plan, a private investigator whose jurisdiction extends into neighboring cities, an institution that *anticipates* an action before it happens — is a prompt-side invention unless the campaign manifest defines it.

**Required patterns at campaign design time:**

1. **Campaign Mechanics Manifest** — declarative list of every mechanic the LLM may use. D&D 5e is the default; lore-specific exceptions (Force push, Dune prescience, Spellblade Nullification Field, Nocturne auditor-thief) are explicitly named. Anything not on the list, the LLM does not invent.
2. **Information Provenance Gate** — before an NPC "knows" or "detects" anything, the narrator must identify the channel: perception / witness / physical evidence / written spell/feature / established surveillance asset / named lore capability. Spell text governs range, target, duration, save.
3. **Causal Consequence Gate** — consequences require both a cause and a delivery path. Murder summons investigators through bodies, witnesses, evidence, missing appointments. Severity cannot exceed what the evidence supports.
4. **Setting Exception Registry** — every lore-specific mechanic (Star Wars Force abilities, Dune prescience, Stellaris psionics, god-tier portfolios) is named with source, scope, users, trigger, range, cost, limits, counters, observability.
5. **No hidden patching** — if an undefined mechanic would be necessary, pause and ask one concrete question or apply rules-as-written.

**Anti-patterns to avoid:**

1. Treating any casting of magic as auto-leaving a remotely detectable signature. The SRD does not say this.
2. Materializing a "planar auditor / inquisition / world-rule god" without a manifest-defined trigger, range, jurisdiction.
3. Renaming forbidden mechanics ("resonance," "aura sense," "magical taint," "world-rule judge," "spiritual audit") to bypass the gate — synonyms for scrying still require provenance.
4. Smealing mask mechanics across campaigns (Vespera's 4-layer mask, Nocturne's Soul Thief, Alexiel's Nullification Field, Visenya's Ascension Meter are manifest-bound, never defaults).
5. NPCs knowing player-only state (secret identity, hidden lineage, mortal-mask level, future plot points) without a written channel.

**Synthesis contract (full version in `references/p36-stable-universe-contract.md`):**

When the user says "I want stable universe mechanics / no more magical signatures / default D&D 5e":

- Run the brainstorming skill (5+ rounds, three proposal trades, then write `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`). Do **not** ship a prompt patch before spec approval (per `references/brainstorming-handoff.md`).
- Spec must contain: (a) D&D 5e edition decision; (b) default vs exception mechanics list with one-line triggers; (c) Information Provenance Gate wording; (d) Causal Consequence Gate wording; (e) per-campaign manifest contract fields (id, source, scope, users, trigger, range, cost, limits, counters, observability); (f) ≥10 SHALL/SHALL NOT clauses (the full text lives in `references/p36-stable-universe-contract.md`).
- Spec is self-contained per P30; delivered both to Slack thread + `~/roadmap/docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md` per P28.
- Sub-task: open WA prompt-layer PRs/issues per Phase 7 so the spec references real PR surface.

**Bound:** ≤10 short, repeatedly-invoked clauses. P19 bounds stat trackers; P36 bounds prompt-level mechanics. The Information Provenance Gate is the single-gate: cite the channel (perception / witness / evidence / written spell / named lore) before claiming an NPC knows something. Do not bloat the system prompt into a 200-line rule book.

**Companion file:** `references/p36-stable-universe-contract.md` holds the full spell-range table, verbatim user-correction catalog, the synthesized SHALL/SHALL NOT clause set, and the SRD 5.1 fact pack verified on 2026-07-29.

**P1 — Replaying the prior version's "claim a dragon at level 6" beat.** Every prior iteration wants *some* apex-pivot. Don't reuse the previous one — pick a *different* application of the same lineage. v1 used *social geometry* (Dragon Scholar). v9 pivoted to *physical geometry* (Apex Stalker). Same lineage, different channel.

**P2 — Patching instead of recreating on lineage/setting pivots.** When the pivot changes a *major section* (lineage, setting, family) the inherited doc structure actively misleads. Delete-and-recreate is faster than patching out inconsistency.

**P3 — Mid-turn pivot without an audit-then-design handoff.** When the user adds "make guard rails against scrying" or "see if we made any PRs yet to fix this stuff" mid-design, do the audit FIRST and in parallel with the design-drafting — not as a blocking gate. Use `gh api` REST endpoint directly when GraphQL hits rate limits.

**P4 — Stale doc read on next iteration.** The user's "use [prior campaign]'s Blood Dragon but for Dunk & Egg" type request implies the prior version's doc text was already in their head. Always `gog docs cat` the latest doc body — the doc on disk may have changed since the local wiki version.

**P5 — Writing the doc as a 1:1 mirror of the wiki.** Doc = prose narrative + design intent. Wiki = structured spec + cross-links + audit anchors. Different roles, different artifacts. Don't duplicate.

**P6 — Skipping the cross-linked stubs.** When vN+1 introduces new mechanics (e.g. v9's `WoundLedger`, `BloodDragonReputationDie`, `StressLineSight`), each must be its own stub. The next iteration's brainstorm will grep `wiki/concepts/` for these — if they don't exist, the brainstorm reinvents them.

**P7 — Wiki push without origin/main sync.** The wiki repo has concurrent agent pushes. Always `git fetch origin main && git rev-parse origin/main` BEFORE adding files. Local-commits-on-wrong-base → chain-of-unrelated-commits on `main` (per `pr-clean-branch-from-main-no-history-bloat`).

**P8 — Mid-turn pivot paragraph injection.** When the user pivots mid-design with a paragraph like "Make me the youngest daughter of the youngest son…", DO NOT split the response into "Design v9" + "Wait, here's the pivot". Treat the pivot as the new design brief and rewrite Sections 1, 2, 5, 6 (Lineage, Setting, Family). The braid-and-scroll work of v9's *youngest-Maekar-daughter* answer took the same single doc, not a second.

**P9 — Confusing "scrying detection" with "anti-detection."** The user's "guard rails against magical scrying detection" means NPCs may NOT detect the Apex lineage through magic. It does NOT mean the Apex lineage gains a detect-magic-blocking buff. The guard rail is *against the LLM inventing magical-detection tropes*, not *the PC gaining anti-detection*.

**P10 — Generating the doc without a separate Phase 0/1.** Ask the user the *one* genuinely-blocking question up front (e.g. "should vN+1 be a true continuation or a fresh slate?") and pick a default for everything else. The skill is for forward design; if the user wants a small adjustment, just patch.

**P11 — Importing the structure of an open PR/module verbatim, even renamed.** When the user names a reference shape ("like BG3", "like the Dark Urge", "like Mistborn", "like God of Murder PR #8483") the design must **derivate a new mechanic stack**, not copy the reference mechanic stack. The distinction matters:

- **Citation** — using the reference's *category* (e.g. "this campaign has a 4-phase cosmic escalation, like BG3") is fine.
- **Importation** — copying the reference's *mechanic shape* (e.g. "Mantle of the Radiant Slayer → Mantle of the Sanguine Slayer," "Sanguine Sovereign / Chitinous Ruin → Sanguine Sovereign / Chitinous Ruin," "5-Pillar Dread Court → 5-Pillar Dread Court") is wrong. The user will catch this and pivot immediately. Verified incident: Visenya v9 session 2026-07-20 imported PR #8483's BG3 endgame shape verbatim and the user pivoted with *"Wait w shouldn't just copy the bhaal god of murder thjng it's just an example"*.

The test before committing any mechanic: **can you write the mechanic name in the reference campaign's terminology without it reading naturally?** If yes, you've imported. Derive, rename, and rebuild.

When the user explicitly invokes `/superpowers-brainstorm` to derive a mechanic (mid-session or up front), **follow the brainstorming protocol — do not skip to the 8-phase iteration workflow**. The brainstorming skill has a hard-gate: no implementation before design approval. See `references/brainstorming-handoff.md` for the detailed handoff contract.

**P12 — Endgame mechanics from a god-tier reference need an extra derivation pass.** When the vN+1 has a god-tier / immortal-tier / post-mortal endgame (BG3 God of Murder, Mistborn Lord Ruler, Cosmere Shards, Berserk Eclipse/God Hand, Wuxia ascension, Naruto chakra-mode, etc.), don't apply the reference's *bundle* as a single block. Decompose into the **4-part mechanic stack**, derive each part against the vN+1's setting, and rebuild:

| Stack component | What it does | Derivation test |
|---|---|---|
| **The Anchor** | The mechanic that ties the protagonist's *current level* to their *endgame form*. (e.g. Wound Ledger → Book of the Blood Dragon → Mantle of the Sanguine Slayer → Thread Eternal) | Does the anchor's tier-by-tier *object* change, not just its *name*? If it's the same object at all tiers with a renamed label, you imported. |
| **The Trigger Threshold** | The event / level / role that signals the protagonist's *first ascension step*. (e.g. Divine Rank 1 at Level 20) | Is the trigger's level anchored in the vN+1's class table, not borrowed from the reference's class table? |
| **The Aspect Shift at Threshold** | The *visual / mechanical consequence* of crossing the threshold. (e.g. Sanguine Sovereign / Chitinous Ruin visual aspects, Mantle of the Radiant Slayer 2-form toggle) | Does the aspect shift tie to *this* protagonist's lore (e.g. Visenya's blood-dragon silhouette, her dragonglass cloak), not the reference's lore (e.g. Bhaal's chitinous murderer aesthetic)? |
| **The Successor Mechanic** | The *post-protagonist* question that defines the "interesting endgame." (e.g. 3-Generation Power Lineage — G0 architect / G1 rejector / G2 confronter; *what do successors do with the architecture?*) | Does the successor mechanic pose a *new* moral / structural / cosmic question, not the same one the reference asked? Visenya v9 question: *"what does a sovereign god leave behind, and is that inheritance worth wanting?"* — different from BG3's "is the architecture good?" — different from Cosmere's "how do other gods react to a new shard?" |

The vN+1's stack must answer the *Visenya-shaped* (or new-character-shaped) question, not the *reference-shaped* question. If they answer the same question with renamed labels, you've imported.

**P13 — Brainstorm-before-design when the user names a reference shape.** If the user names a reference shape in the design brief ("make her like BG3 God of Murder but for Westeros", "make it a Sacrifice Mechanism like Berserk", "do a Schaffarnias Effect like Mistborn's Lord Ruler"), Phase 0 of this skill is to run brainstorming **before** the 8 phases. The brainstorming skill's job is to derive what the user actually wants from the reference, *as a class*, and then design. See `references/brainstorming-handoff.md` for the protocol.

**P14 — Campaign design = system design, not story design; do NOT force the user to pick canonical endings.** The user will say *"I should get to decide whatever I want"* / *"don't make me pick an ending, just save possibilities, we're designing the campaign not a fully decided story"* if the design converges on a single plot line. The campaign spec must be designed as a **system that produces multiple emergent endings at the table** — never as a single canon ending. Concretely:

- **Forbidden pattern:** "Visenya ascends, meets her older self, they fight, Visenya wins and becomes the new apex." — that is a *story*, not a *campaign*.
- **Required pattern:** "The First Song confronts Visenya at L20+. Resolution A (Joining) / Resolution B (Replacement) / Resolution C (Refusal) / Resolution D+ (player-defined) — each is mechanically distinct, all are supported by the system, the player picks at the table. No ending is canonical." — that is a *system*.

The four-mode resolution pattern (Joining / Replacement / Refusal / Player-defined) is the durable shape. Mirror mechanics across versions (V6 Entropy Toll → v9 Reputation Die; V6 BORROWS → v9 SAREDESIGNS), but the four-mode resolution ladder stays the same across iterations.

When the brainstorming derivation produces a single resolution, you shipped a story, not a campaign. Reopen the design and derive at least one additional resolution that exercises a *different* verb (accept / destroy / break) on the L20+ encounter.

Also holds for: full-edit mode (player picks the path), hub-and-spoke staging (player picks which hub to revisit), reputation-gated endings (player picks which reputation to cultivate). All are system-level choices; never collapse them to a single canon ending.

Verified incident 2026-07-20: Visenya v9 brainstorming produced three endings (Joining / Replacement / Refusal) — the user's *"don't make me pick an ending, just save possibilities"* correction fired *because the brainstorm framing was still presenting the three options as "the endings"* rather than as a system that supports multiple. The fix was rewording Section 14 as "player picks at the table, no canonical resolution."

**P15 — Take inspiration, NEVER copy, even when the user names the reference.** The user will say *"don't directly copy X, take inspiration"* (or the more colloquial *"wait w shouldn't just copy the Bhaal god of murder thing it's just an example"*). This is P11's punchline — but P11 is structural (do not import mechanic shapes); P15 is the *user-facing wording*. When the brainstorm asks the user "who from the prior versions is the First Song?" and the user names a specific campaign (V6, V8, V2), the SPEC must:

- Take the *category* the user wants (mechanic shape, personality trait, framing).
- Build a Visenya-shaped version that *answers a different question* than the reference answered.
- Add new lore, new consequences, new tensions — not just rename the reference's mechanics.

Verified incident 2026-07-20: Visenya v9 brainstorm produced "First Song = V6-Visenya" with *the same sadism-from-boredom personality* as V6 — that part is fine (it's a *category*, V6's category is reuse-preserving). But the lineage mechanic descended from V6 (Sanguine Thread / Book of the Blood Dragon) was *copy-pasted* from PR #8483 (BG3 God of Murder module), not derived. The user caught it. P15 prevents the same behavior in the future by distinguishing category-borrow (OK) from mechanic-import (NOT-OK).

The test: **does the borrowed mechanic answer a question that only the borrowed campaign's lore can answer, or does it answer a question this campaign's lore could answer just as well?** If the latter, the mechanic is too generic to be specifically imported. Derive against the vN+1's setting.

**P16 — When the user explicitly invokes `/superpowers brainstorm`, the brainstorming skill is authoritative — bypass the 8-phase "just ship it" workflow.**

The `/superpowers-brainstorm` command at `~/.claude/commands/superpowers-brainstorm.md` is a *meta-instruction*: "Invoke the superpowers:brainstorming skill and follow it exactly as presented." Underlying skill at `~/.codex/superpowers/skills/brainstorming/SKILL.md` (164 lines) has a HARD-GATE — *do not write code, do not invoke implementation skills, do not take implementation action until the user approves a written spec*. The skill enforces a 9-item checklist (explore context → visual-companion offer → ONE clarifying question at a time → 2-3 approaches → present design → write spec → spec self-review → user reviews → invoke writing-plans).

When the user types `/superpowers brainstorm` (or `/super`) in a campaign-design context:

1. **Recognize** — search the user message for `brainstorm` (case-insensitive) as a trigger. Same signal fires for `/super` (the orchestrator command at `~/.claude/commands/super.md` which auto-picks brainstorm→plan→execute).
2. **Load the brainstorming skill** via `skill_view(name='tessl:brainstorming')` OR fall back to `read_file ~/.codex/superpowers/skills/brainstorming/SKILL.md`. (The `tessl:brainstorming` qualified name may resolve as "not found" depending on how the plugin is named in the active runtime; the unset path is `~/.codex/superpowers/skills/brainstorming/SKILL.md`.)
3. **Switch to ONE-question-at-a-time mode.** Do NOT bundle multiple choice options into one reply. Ask the *single most blocking* question; then the next; then the next. The user has explicitly opted into this slower, more deliberate shape.
4. **Probe design source carefully.** This is the difference between "use V9 as inspiration" (allowed, derived) and "directly copy BG3 god of murder mechanics" (forbidden, P11/P15). When proposing 2-3 approaches, name the references *by category* (e.g. "Reputation-Die → Divine-Rank coupling pattern") not by copyable shape (e.g. "Book of the Blood Dragon → Mantle of the Sanguine Slayer").
5. **Write the spec to `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`** per the brainstorming skill's flow. The user must approve the written spec before any code/scaffold/dispatch action.

Anti-pattern: when brainstorming is invoked, do not pre-fetch `gog docs export`, do not spin up `worktree`, do not start the wiki push. The brainstorming skill forbids all of these until the spec is approved.

Verified incident 2026-07-21: God of Murder v2 (user → "Full redesign but don't just copy elements without me approving, just use it for ideas / the enemies should be other gods not my future self / Name my char nocturne" + slash command `/superpowers brainstorm`). Brainstorming skill honored: scope question first (A mechanic-only patch / B full redesign / C hybrid), then setting question (A BG3 keep / B existing Nocturne canon / C setting-agnostic / D user-picks), then portfolio question (A murder / B inversion / C new synthesis / D user-picks). Three questions, three post-in-thread replies, zero implementation until user picks the portfolio.

**P17 — When the iteration changes the protagonist (different name, same setting), the Quantified Mechanical Engine (Pillar 4) stays; pivot the wiki source page to a NEW page per protagonist (no rename, no supersede).**

The Quantified Mechanical Engine (Pillar 4) is *character-agnostic*. v1 of the God of Murder branch used a "Dark Urge" protagonist; v2 of the same branch uses "Nocturne." Both protagonists can run on the same 6-tier divinity ladder, follower-scaling formulas, and per-faction portfolio tension tables — what changes is the *protagonist identity* and their *portfolio specifics* (which gods are enemies, what their dissonance-gated private revelations are, what their 3-Generation Power Lineage's G0 generation says).

When the pivot is *protagonist-only* (same setting, same mechanic stack, new name):
- DO write a new wiki source page (`wiki/sources/nocturne-god-of-murder-v2-<slug>.md`) — NOT a rename of v1's page. Both pages coexist; v1 stays as the canonical record of the prior iteration.
- DO write a new Google Doc — NOT patch v1's doc. The user's "Name my char nocturne" implies v1's "Dark Urge" content is now wrong.
- DO derive new per-faction dissonance entries that fit Nocturne's perspective. The underlying 6-faction schema can be reused (Kelemvor, Mystra, Cyric, etc.); what changes is the private-revelation content per faction.
- DO scope-check on the four-mode resolution ladder (P14): the new protagonist must support Joining / Replacement / Refusal / Player-defined paths, even if their specific L20+ encounter is different.

When the pivot is *portfolio-only* (same setting, same protagonist, new divine portfolio — e.g. v1 Murder → v2 of the same protagonist now becoming "Goddess of Mercy"), skip wiki source-page rename BUT add a new concept stub for the new portfolio's mechanics.

Verified incident 2026-07-21: God of Murder v2 with protagonist name "Nocturne" (user message). Recognized that Pillar 4 stays constant (the Quantified Mechanical Engine is character-agnostic), but v1's wiki source page in `wiki/sources/` should NOT be renamed — instead create `wiki/sources/nocturne-god-of-murder-v2.md` alongside v1. The wiki's index page gets a second Sources entry pointing to the new page; v1 stays as canonical history.

**P18 — Saving-to-wiki ordering: do NOT save v1 to wiki if v2 is imminent; save v2 directly to skip a redundant wiki supersede.**

Counter-intuitive to the wiki-vault-safeguards pattern (which says "save as you go"). When the user explicitly says *v2 is coming* (e.g. *"save this to wiki AND redesign it"*), the order is:

1. Wait for v2 design approval via `/superpowers brainstorm` → spec review.
2. Write v2 source page directly.
3. v1 doc can then go to wiki (as historical record) OR remain on Drive (also historical) — depends on whether the user wants a full version archive.

The trap: user says "save to wiki" mid-design. Agent saves v1 to wiki. V2 lands. Now wiki has the v1 page as the canonical Sources entry, and the v2 work produces "v2 supersedes v1" semantics that require either deleting v1 (history loss) or keeping v1 archived with a v2 supersession note (clutter).

The fix: when /superpowers brainstorm is in flight and the user says "save to wiki," first ask whether v1 should land on wiki before v2 spec is approved (yes → saves now / no → wait for v2). Default = wait for v2 to avoid the supersede dance.

Verified incident 2026-07-21: user said "save this god murder campaign to llm wiki too" while /superpowers brainstorm was active. Correct decision: wait for v2 spec approval, write v2 to wiki directly, add v1 either as a separate historical archive entry or omit it (based on user's preference after the v2 design lands).

**P19 — Bound the new-resource count for god-tier design. The user is Aizen-loyal and explicitly prefers the Aizen stat sheet, not a fresh engine.**

The user's exact wording (2026-07-21 God of Murder v2 brainstorm): *"...avoid defining too many new resources though, might be annoying to manage."*

When the vN+1's Quantified Mechanical Engine (Pillar 4) is being derived, hard cap the surface area to **≤5 trackers the player has to know per dawn**. Anything beyond that must reuse an existing Aizen-style stat, not introduce a new entity class.

Concrete bound table (verified on God of Murder v2 brainstorm):

| Tracker | Reuse from Aizen? | Why OK |
|---|---|---|
| Divine Resilience / HP | yes — `DR` | Aizen's sheet has it |
| Divine Armor Class | yes — `DAC` | Aizen has it |
| Divine Power Points / day | yes — `DPP` | Aizen has it |
| Divine Attack/Influence Roll modifier | yes — `DAIR` | Aizen has it |
| Divine Legendary Resistances | yes — `DLR` | Aizen has it |
| Follower count → stat scaling | yes — Aizen formula | Aizen's signature shape |
| Reputation / public-perception | yes — Three-Layer Deception-style projection | Aizen has the Three-Layer concept |
| Action economy (1 Major + 3 Legendary) | yes — Aizen has it | — |
| New "Wound" entity class | **no — cut** | The user pushed back on this. Verbatim quote (2026-07-21): *"i don't know about wound ledger maybe remove it"* |
| Per-faction Disposition (6 separate columns) | **no — collapse to 1 dial** | The user pushed back on this. Replace with Pantheon Temperature (0–5) or a single Aizen-style Perception dial |
| Per-Wound HP pool + Active Penalty rolls | **no — cut** | Same reason as Wound above |

The test before adding any new tracker: *can the mechanic reuse an existing Aizen / D&D 5e stat (DR, DPP, DAIR, F, RP, disposition) without renaming it?* If yes, reuse. If no, **either derive against the vN+1's setting or cut it**. Don't ship a brand-new entity class for one campaign.

The "1 Major + 3 Legendary" action economy is canonical and reusable. Reuse it as-is, do not invent a new per-dawn budget.

For each god-tier brainstorm, the spec's *Resource Tracker List* section must:
1. List every tracker the player sees per dawn (max 5).
2. For each: cite which Aizen stat it reuses, and what the re-purposed cost is.
3. Be small enough to fit on one Post-it note. If it doesn't, you have P19 bloat.

Verified incident 2026-07-21: God of Murder v2 brainstorm invented a "Three-Engine Mechanic Stack" (Reputation Die + Wound Ledger + 6-Faction Tithe Multipliers) that produced 10+ trackers. User caught it on the third message. Reverted to 5 trackers (Repr Die / DPP / F / Infamy / Pantheon Temperature), all Aizen-stat-derivations. P19 is the durable rule that prevents the invent-10-trackers error from recurring.

**P20 — When the user prompts "predict my taste" / "did you actually read X," make bets + invite correction. Do NOT pad with explanation.**

The user's prompt shape (2026-07-21): *"Read my other god campaigns and make an educated guess which other ones i liked vs didnt like. Pick top 3 i liked and top 3 i didnt and see if you understand me, ill tell you if right or not."*

This is a *prediction-invitation*. The expected response shape is:

1. State your bets as a numbered list (e.g. "Top 3 LIKED: A / B / C. Top 3 DIDN'T: X / Y / Z.").
2. For each: one-sentence *why* you think so (cite the file or summary that supports it).
3. End with a **confirmation ask**: *"Tell me where I'm wrong."* / *"Which bets did I miss?"* / *"Confirm or correct."*
4. Do NOT explain how you analyzed them. Do NOT cite the methodology. Do NOT add more candidates past 3+3 unless the user asks. Do NOT write a 2KB preamble.

The 3+3 cap is the binding format. The user is testing pattern recognition, not asking for a literature review.

When the user subsequently says *"right"* or *"wrong about [X]"*, log the correction directly into the vN+1 spec — don't just acknowledge it. The correction *is* part of Phase 2 (Extract the 3 recurring taste pillars) output. The "user just told me what they liked" is the missing evidence for the extraction; mine it.

Cross-skill: this is the same shape as `harness-postmortem`'s "state your reading + invite correction" pattern. The failure mode being prevented is *analysis paralysis* — explaining how you arrived at the bets instead of placing them.

Verified incident 2026-07-21: user asked "did you actually read the original aizen campaign in detail" — the trap was to answer with a methodology essay (yes I read it, here are the 12KB references, here's how I deduplicated). The correct response was: "Yes. Top 3 patterns: quantified stat sheet (DR/DPP/DAIR), Three-Layer Deception as your RP mechanic, and 1 Major + 3 Legendary action economy. Tell me which ones I'm missing." P20 makes that the default for any "predict my taste" / "did you actually read X" prompt.

**P21 — Load-bearing math, not decorative math. Calculations must drive decisions, not just appear.**

The user's exact wording (2026-07-21 God of Murder v2): *"I just see calculations which don't mean much to me and usually just win rolls. I sometimes ask the LLM to add more DC, but it has no mechanical meaning to me."*

This is the **central quality bar for god-tier design**. The previous Quantified Mechanical Engine pillar (Pillar 4) was right that the math scaffold must exist. P21 adds the **load-bearing test**:

> The math is *load-bearing* iff the player's optimal choice at dawn depends on what the math says. If the math can be ignored and the prose still resolves the same way, the math is decorative — and the user will (correctly) reject the campaign as "lots of narrative not enough god mechanics."

Concretely, every per-dawn choice menu (P23) must have at least one option where:
1. The DPP cost is visible *and* materially constrains the player's choice (e.g. "you have 75 DPP today, A costs 200 = locked; pick B or C").
2. The Reputation / Apex Attention band change is visible as a *named narrative consequence*, not a hidden number (P24).
3. The math runs deterministically (P22 — OPTIMIZE → ROLL pattern) so the player can verify their optimal play after the fact.

When designing, ask before locking the spec: **"If the player reads the math and picks differently than the LLM would have, can they beat the LLM?"** If no (LLM ignores the math), the math is decorative. If yes (LLM respects the math and the player outplays it), the math is load-bearing.

**Forbidden pattern:** Writing a "Divine Stat Sheet" at the top of the campaign doc, then narrating events that ignore it. The stat sheet becomes wallpaper.
**Required pattern:** Stat sheet *appears every dawn*, *constrains DPP spending*, *drives Reputation / Apex Attention bands*, and the player's math-driven choices *change the outcome* the LLM produces.

Verified incident 2026-07-21: God of Murder v1 had a 156-line §8 "Quantified Divine Engine" with per-phase stat blocks (DR/DPP/DAIR formulas). The narrative events in §1-§7 ignored §8. User caught it on the second turn: *"It doesnt seem to have many god mechanics just lots of narrative?"*. The V2 spec (archived to `~/roadmap/docs/superpowers/specs/2026-07-21-nocturne-v2-god-mechanics-design.md`) restructures the spec so §8's math is the *primary* decision driver every dawn, not a §1-§7 appendix.

**P22 — OPTIMIZE → ROLL is the D&D 5e mental model. Rolls add variance within math-determined brackets, never decide outcomes.**

The user's exact correction (2026-07-21 God of Murder v2, mid-turn after I overcorrected): *"wait i dont think you understand the roll, look at the whoel D&D 5e system. A player will optimize the build/stats/items/startegy and then the roll is the last thing to add excitement and variance. Then look at some of my god campaigns. The first part is missing and i just see calculations which dont mean much to me and usually just win rolls."*

The D&D 5e player loop is **OPTIMIZE → ROLL**. The player first optimizes build / stats / items / strategy. Then the roll is the last thing — adds excitement and variance on top of an already-optimized setup. The roll is the *cherry on top of an already-built sundae*, not the sundae itself.

For god-campaign design, this translates to:

| Phase | Math decides (OPTIMIZE target) | Roll adjusts (variance only) |
|---|---|---|
| 1. Locate | Findability (DPP budget) | — none — |
| 2. Infiltrate | Plane entry (DPP + Avatar HP) | — none — |
| 3. Engage | Major Action feasibility (DPP ≥ Cost) | — none — |
| 4. Counter | God's response (DAIR vs DAC) | — none — |
| 5. Commit | Damage bracket (DAIR differential) | 1d20 within ±5 on damage quantity |
| 6. Absorb | Portfolio integration | 1d20 picks which sub-effect manifests |

**Anti-patterns to avoid:**

1. **"No rolls at climax" overcorrection.** When the user said the rolls felt random, I jumped to designing the god-hunt as a deterministic action chain with no dice at all. User corrected: rolls are fine, just not the *whole* answer.
2. **"Just add more DC" reductionism.** When the math doesn't drive outcomes, asking for higher DC doesn't help — DC is a *threshold the math ignores*. The fix is to make the math load-bearing (P21), not to push DC up.
3. **Roll decides the outcome.** If a d20 determines whether the player wins the god-hunt, the math isn't being used — the player rolls, looks at the number, and the LLM writes from there. This is the failure mode the user explicitly named.

**Per-scene roll cap = 4 maximum** (cultist loyalty × 1, assassination attempt × 1, deception × 1, target's final death save × 1). Beyond that, the math decides.

Verified incident 2026-07-21: in the God of Murder v2 brainstorm I proposed "no rolls at the climax" — the user caught it and corrected with the OPTIMIZE → ROLL framing. The final V2 spec keeps 4 rolls/scene but each roll sits *inside* a math-determined bracket.

**P23 — Per-dawn menu is context-aware (routine / triggered / quiet), NOT formulaic.**

The user's exact wording (2026-07-21): *"Per-dawn menu - this seems too formulaic? I don't think I should get the same menu every day. These are jsut general things. I can do but maybe one day something more important is happening."*

The menu *appears when the world has something to react to*, not every dawn mechanically. Three dawn types:

| Dawn type | Menu shape | When |
|---|---|---|
| **Routine dawn** (default) | 2-3 light options: worship-build, heat-management, RP accumulation | Most dawns |
| **Triggered dawn** (something dramatic) | 4-6 full options: Bhaal-hunt, rival-god confrontation, coalition-formation, etc. | Bhaal-essence surfaces, rival god moves, Apex Attention hits a band, RNG event, player-triggered crisis |
| **Quiet dawn** (post-crisis cooldown) | No menu — narrative + stat updates only | Post-crisis, recovery, mourning |

The LLM (or campaign spec) decides when the menu goes full. The player never sees a *fixed* A/B/C/D/E list that repeats identically dawn after dawn — that *is* the formulaic anti-pattern.

For the V2 spec, the menu is *context-aware*, with explicit trigger conditions:
- Bhaal-essence surfaces in [Region] → triggered dawn
- Apex Attention hits "Noticed" or higher → triggered dawn (a god has noticed)
- Reputation hits a band threshold (e.g. crosses "Open") → triggered dawn (cult mechanics change)
- RNG event roll (1d100 < 10) → triggered dawn
- Player declares "I do X" → triggered dawn if X requires it

The spec's menu should be a *function*, not a *list*. Example: `menu = f(world_state, dawn_type, last_triggered_dawn_age)`.

Verified incident 2026-07-21: God of Murder v2 spec initially proposed a fixed A/B/C/D/E menu every dawn. User caught it on the next message and asked for context-awareness. The V2 spec now includes the three-dawn-type taxonomy above.

**P24 — Hidden mechanics surface as narrative bands, never expose the number.**

The user's exact wording (2026-07-21): *"Lets make all the dissonance / apex attention things hidden, players shouldn't know a number just see narrative consequences."*

When the campaign has a hidden LLM-side mechanic (e.g. Reputation, Apex Attention, Dissonance), the *player* must never see the underlying number. The LLM tracks; the player reads:

1. The **band name** (Unknown / Whispered / Open / Established / Revered / Pantheon-tier)
2. The **narrative consequences** that fall out of the band (e.g. "a coalition of minor gods has formed against you" when Apex Attention hits "Hunted")

The player never sees:
- The numerical value (e.g. "Reputation: 67")
- The band threshold (e.g. "Open at 41")
- The change mechanics (e.g. "+1 per worship-building day")

**Anti-pattern:** Showing the player the band's number on a stat sheet. The instant the player sees "Reputation: 67," the band stops being narrative and becomes a tracking number — the player min-maxes instead of roleplaying.

**Required pattern:**
- LLM maintains the numeric state.
- Player-facing surface = narrative bands + consequences.
- Stat sheets that the player sees show *visible* stats only (DR, DAC, DAIR, DPP per P19) — never hidden mechanics.

For the V2 spec, this means:
- `Reputation: 0-100` (hidden) → `band ∈ {Unknown, Whispered, Open, Established, Revered, Pantheon-tier}` (visible)
- `Apex Attention: 0-100` (hidden) → `band ∈ {Unseen, Whispered, Noticed, Marked, Hunted, Apotheosis-imminent}` (visible)

Verified incident 2026-07-21: God of Murder v2 spec originally had "Reputation Die: d8" as a visible stat. User caught it and asked for hidden mechanics with narrative surfacing. V2 spec now has 4 visible stats (DR/DAC/DAIR/DPP) + 2 hidden (Reputation/Apex Attention) with named bands.

**P25 — Combat ladder: auto-win on mortals, rolls only for Chosen / divine beings.**

The user's exact wording (2026-07-21): *"How about social rolls and stuff? Prob just use the divine mechanics and auto win on mortals? Auto win combat on mortals I guess? Unless it's an avatar or chosen then maybe divine combat to some degree?"*

For god-tier play, mortal combat is the *boring case* — auto-win. The interesting case is *other divine beings* and *Chosen NPCs*. The combat ladder:

| Target | Result |
|---|---|
| Commoner / town guard / random NPC | **Auto-win.** No roll. |
| Named mortal (Cazador, Duke, Bhaalist priest) | **Auto-win.** Divine Save DC vs mortal — mortals can't beat it. |
| **Chosen mortal** (Bane's Chosen, Shar's Chosen) | **Divine combat.** d20+DAIR vs DAC. |
| Avatar of lesser / major god | **Full divine combat.** Major action + d20 roll. |
| Lesser / Intermediate god directly | **Full divine combat.** Major action + d20 roll. |
| Greater god / Apex entity | **Full divine combat.** May require god-hunt action chain. |

The interesting campaign choices live at the *top of the ladder* — the Chosen and the divine. Below that, the player auto-wins; the LLM narrates the kill and moves on. Above the apex-tier threshold, the player must engage the god-hunt action chain (P22).

This is *also* the OPTIMIZE → ROLL pattern at a combat level: the player optimizes their stat block (P19 ≤5 trackers) and the math auto-wins below the divine threshold; rolls only fire where the math can't pre-determine the answer.

Verified incident 2026-07-21: V2 spec originally had a single "combat resolution" section. User explicitly split it into the auto-win ladder above. Without the split, the spec left room for the LLM to over-roll at the mortal tier.

**P26 — Universal god stats apply to ALL setting gods, not just the protagonist.**

The user's exact wording (2026-07-21): *"All gods need to follow these mechanics and not just me"*

The god-mechanics design (Pillar 4 + DR/DAC/DAIR/DPP/Reputation/Apex Attention) must be **system-agnostic across the setting's pantheon**, not just protagonist-local.

| Setting | What "universal god stats" means |
|---|---|
| Faerûn | Bhaal, Shar, Mystra, Kelemvor, Cyric — all computable on the same stat sheet; only numbers differ |
| Westeros | The Old Gods, the Drowned God, R'hllor, the Many-Faced God — same DR/DAC/DAIR formula |
| Marvel | Asgardians, Celestials, Elders — same stat scaffold |
| Cosmere | Shards, Splinters — same formula |

The protagonist's *numbers* are uniquely hers; the *rules* are universal. This matters because:
1. Enemy gods (other gods in the pantheon) become *legible* — the player can compute the math to decide whether to engage or avoid.
2. The campaign's world-building is consistent — every god has a stat sheet, even ones the player never directly confronts.
3. Future iterations in the same setting can reuse the same pantheon scaffolding.

For the V2 spec, the **god-class system** (War / Trickster / Domain / Magic / Death / Skilled) is *the* mechanism for expressing "universal mechanics, unique numbers." Every Faerûn god has a class; their stat biases differ by class; the math is the same.

**God-class stat biases table (verified on V2 spec):**

| Class | DR | DAC | DAIR | DPP | Examples |
|---|---|---|---|---|---|
| War god | High (1100+) | Low (22-) | High (+50+) | Mid (700-) | Tempus, Bane |
| Trickster god | Low (500-) | Low (20-) | Very High (+60+) | High (900+) | Mask, Cyric |
| Domain god | High (1100+) | Mid (24) | Mid (+35+) | Mid (700-) | Chauntea, Silvanus |
| Magic god | High (1100+) | Low (22-) | Mid (+35+) | High (900+) | Mystra, Shar |
| Death god | Very High (1500+) | Mid (24) | Mid (+35+) | Mid (700-) | Kelemvor, Myrkul |
| Skilled god | Mid (750-) | Mid (24) | Very High (+60+) | Mid (700-) | Nocturne (Murder) |

Verified incident 2026-07-21: V2 spec initially had a Nocturne-only stat block. User said "all gods need to follow these mechanics" and the spec grew the 6-class system to make the mechanics universal across Faerûn.

**P28 — When the user asks for the spec to land "here and in ~/roadmap" (Option A: dual-location), write to BOTH surfaces in the same turn. Slack thread is the user's reading surface; `~/roadmap/docs/superpowers/specs/` is the canonical version-controlled home.**

The user's exact wording (2026-07-21 God of Murder v2): *"A) letes do the spec here and in ~/roadmap"*

Two-surface spec delivery:
1. **Slack thread** — split into Part 1/Part 2 if exceeds 4000 chars per message (Slack 4000-char message cap); mark each part's heading so a reader skimming the thread can navigate.
2. **`~/roadmap/docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`** — canonical spec doc, full content, mirrors the Slack thread body. Use `~/roadmap/docs/superpowers/specs/` per the brainstorming skill convention (the directory already exists).

Same content in both places. The Slack thread is the *user-facing deliverable* (Jeffrey reads it where the conversation is happening); the roadmap file is the *agent-searchable canonical* (future brainstorm sessions grep `~/roadmap/docs/superpowers/specs/` for prior art).

When the spec is ≥4000 chars, split Slack delivery into Part 1 + Part 2. NEVER use shell heredoc through terminal — use `write_file` directly for the roadmap file. For Slack delivery, the canonical pattern is two `mcp_slack_conversations_add_message` calls with the same `thread_ts`, each marked Part 1 of 2 / Part 2 of 2 in the heading.

**Anti-pattern:** Posting a Slack message with just a link to the roadmap file (forcing the user to switch contexts to read the spec), OR writing only to roadmap (no Slack delivery). Both surface only — never single-surface.

**Provenance footer for the roadmap file** must cite the Slack thread URL (so a future agent can find the discussion context):
```
**Source thread:** https://slack.com/archives/<channel>/p<ts>
```

Verified 2026-07-21: God of Murder v2 spec (270 lines) was written to both `~/roadmap/docs/superpowers/specs/2026-07-21-nocturne-v2-god-mechanics-design.md` AND the Slack thread C0AH3RY3DK6/p1784585087 in Part 1 (sections 0-5) + Part 2 (sections 6-11) format. The user accepted both without modification.

**P29 — When the user says "show me the gh url and worldai repo world_reference/", give the BOTH the PR URL + the actual file path on the repo, in a single Slack reply with a `MEDIA:`-style link. Don't make them ask twice.**

The user's exact wording (2026-07-21 God of Murder v2): *"show me gh url and worldai repo world_reference/"*

Two things they want in one reply:
1. **`gh pr view <N> --json url`** — the GitHub PR URL.
2. **`world_reference/` repo file path** — the literal repo path on origin (`github.com/$GITHUB_REPOSITORY/blob/main/world_reference/<file>.md` for the canonical main branch; or `<branch>/world_reference/<file>.md` for the active branch).

Format in Slack:
```
✅ **PR #<N>**: <url>
✅ **world_reference/**: github.com/$GITHUB_REPOSITORY/blob/<branch>/world_reference/<file>.md
```

Don't bury the URL in prose. Don't omit the file path. Don't make them click one link to find the other. Both in the same reply.

**Anti-pattern:** Posting only the PR URL and forcing the user to navigate to the Files tab to find world_reference/. Or posting only the file path without the PR URL so they can't find the discussion.

Verified 2026-07-21: PR #8488's reply included both the PR URL and the file paths (`world_reference/nocturne-v2-god-mechanics-design.md`, `world_reference/campaign_module_god_of_murder.md`) — user accepted the pair without asking for either separately.

**P30 — When the user says "self-contained" / "make it self contained" / "everything we discussed in this thread", the spec doc must include ALL discussion threads in ONE document. Don't link to Slack context; embed the substance directly.**

The user's exact wording (2026-07-21 God of Murder v2): *"whichever PR we use for world_reference its hould have everyting we discussed in this thread for murder god campaign and all the god mechanics self contained"*

A "self-contained" spec is one that a future agent can read without the Slack thread and get the full design. No reliance on prior messages, prior decisions, prior context. Every:
- Decision that was made (with status: locked / awaiting / open question)
- Mechanic definition (with formula, table, example)
- Out-of-band correction (e.g. "Repr Die IS god power" — embed the rationale)
- Anti-pattern avoided (e.g. "no Wounds, no Publicity Tax" — embed the why)
- Open question for next iteration (with explicit list)

For God of Murder v2, this meant the spec had to capture:
- 7-tier ladder (P25-A V2 deltas)
- Mortal → Divine multiplier (5.4× DR, +4 DAC, +18 DAIR)
- 6 god-classes (War / Trickster / Domain / Magic / Death / Skilled)
- Hidden Reputation + Apex Attention bands
- Context-aware per-dawn menu (routine / triggered / quiet)
- Auto-win combat ladder
- 4-roll cap per scene
- Deicide-cost = Apex Attention +1 band
- OPTIMIZE → ROLL pattern (P22)

Without the Slack thread, a reader must be able to rebuild the V2 design from the spec doc alone. The Slack thread is a *delivery channel* for the spec — not the spec itself.

**Anti-pattern:** Spec docs that link to "see discussion in <slack thread>" for any design rationale. The Slack thread might disappear; the spec doc should be durable.

Verified 2026-07-21: V2 spec at `~/roadmap/docs/superpowers/specs/2026-07-21-nocturne-v2-god-mechanics-design.md` includes 11 sections (goals, tier structure, multiplier, universal god stats, scaling, hidden mechanics, per-dawn menu, combat ladder, roll-pattern, deicide-cost, sample stat block) + V2 deltas summary table — all embedded inline, no Slack dependency.

**P27 — When the user delivers a multi-decision batch (≥5 sharp decisions in one message), lock all in one decision-stack table and move to spec — bypasses the brainstorming skill's one-question-at-a-time mode.**

The brainstorming skill (P16) defaults to one-question-at-a-time mode: ask the single most blocking question, wait, ask the next. But the user can switch modes by delivering **a batch of sharp decisions in one message**. When that happens:

1. **Recognize** — count the distinct decisions in the user's message. If ≥5, the user has switched to decision-stack mode.
2. **Lock all in one decision-stack table** — produce a single reply with a numbered table listing every decision the user made + the status (locked / awaiting clarification).
3. **Move to spec** — the brainstorming skill's HARD-GATE (no implementation before spec approval) still applies, but the *one-question-at-a-time* protocol is **overridden** by the user's explicit batch mode. Don't ask follow-ups one at a time — move directly to writing the spec.
4. **Spec covers all locked decisions + remaining open questions** in a single document.

**Anti-pattern:** When the user delivers 8 sharp decisions in one message, posting 4 separate Slack messages each asking "and what about X?" or "should we go further on Y?" — that wastes the user's batch mode and forces them to babysit follow-ups they didn't ask for.

**Required pattern:** Single decision-stack table covering all 8 decisions + "open questions" subsection for anything still ambiguous + immediately move to writing the spec.

Verified incident 2026-07-21: God of Murder v2 brainstorm, the user delivered 8 sharp decisions in one message (Q1 Lesser god added, Q2 menu context-aware, Q3 all-gods follow mechanics, Q4 god classes, Q5 social rolls auto-win, Q6 spec workflow, Q7 implementation plan, Q8 /superpowers-brainstorm review). I recognized the batch mode, produced a single decision-stack table covering all 8, and moved to writing the spec to `~/roadmap/docs/superpowers/specs/2026-07-21-nocturne-v2-god-mechanics-design.md` instead of asking 8 follow-ups.

**P31 — When the user says "not enough mechanics" / "lots of narrative not enough god mechanics," iterate the Quantified Mechanical Engine (Pillar 4) from V(n) to V(n+1) by doubling mechanic count without breaking OPTIMIZE → ROLL.**

The user's exact wording (2026-07-21 God of Murder v3): *"keep iterating on this campaign. It doesnt seem to have many god mechanics just lots of narrative?"*

This is the **mechanic-density iteration pattern**, distinct from the *pivot iteration* pattern of P11/P12/P15 (which change one axis). Mechanic-density iteration grows the *count* of explicit mechanics in the same conceptual frame, while keeping the player-facing OPTIMIZE → ROLL experience stable.

The growth pattern (verified V2 → V3, 2026-07-21):

1. **Identify the user's complaint** — "not enough mechanics" usually means: implicit mechanics are present in spirit but not as tables the LLM can apply; the LLM is making narrative decisions the math should drive; per-dawn options collapse because there's no explicit math to constrain them.
2. **Find V(n)'s implicit mechanics** — usually the V(n) spec has a paragraph like *"Repr drives reputation"* but no table, no formula, no band. Convert spirit to table.
3. **Add 2-3 sub-mechanics per concept** — V2's Repr becomes 7 sub-systems; V2's Action Tier becomes AT-0/-1/-2/-3 with explicit DPP costs and per-dawn caps; V2's combat ladder becomes an explicit target → result table; V2's per-dawn menu becomes a 4-6-option template with OPTIMIZE → ROLL narrative.
4. **Add dawn-action archetypes** — let the player pick their first OPTIMIZE decision (Sovereign / Diplomat / Tyrant / Seducer / Hermit), which biases the menu options for the rest of the dawn.
5. **Add worked examples** — at least 2 dawn-by-dawn math walkthroughs so the LLM has a pattern to follow. Examples must show: stat sheet visible to player, menu options, math resolution, roll outcome.
6. **Add a verification standard list** — 8 standards the LLM must check on every dawn (e.g. "every action has a resource cost in DPP/RP/AT/F-tithes," "no wound/curse/penalty mechanics in the player's stat block").

The total mechanic count roughly doubles (V2: 8 → V3: 20) without breaking the player-facing experience.

**Anti-pattern:** Adding 50 new mechanics to "show density" — the user will reject this as P19 bloat. The bound is **the same OPTIMIZE → ROLL surface**, with **2-3x more math to ground it**. Anything beyond 3x density crosses into bloat.

**Test before committing:** *"Can the player still read the per-dawn menu in <10 seconds and identify the OPTIMIZE choice?"* If no, density has crossed into bloat.

The full mechanic library is at `references/load-bearing-math-design.md`. The 20 sub-mechanics (V3.0-V3.20) are the canonical library. When iterating any god-campaign vN+1 to vN+2 with the "not enough mechanics" complaint, start from this library and add 2-3 sub-mechanics per concept, not 50.

Verified incident 2026-07-21: God of Murder V2 had 8 sub-mechanics (V2.1-V2.8). User reply: *"keep iterating on this campaign. It doesnt seem to have many god mechanics just lots of narrative?"* V3 doubled to 20 sub-mechanics (V3.0-V3.20) following the 6-step growth pattern above. Player-facing experience stayed OPTIMIZE → ROLL → NARRATE; the LLM just had more math to ground each scene. P31 is the durable rule that prevents future "not enough mechanics" iterations from re-inventing the V2 → V3 delta table.

**P32 — When introducing new god-mechanics, grep the prior version's term inventory. Don't reintroduce a retired term, even with the same intent.**

Verified incident 2026-07-21: V1's stat sheet explicitly stated *"the previously-separate 'Apex Attention' / 'Apex Predator' mechanic has been **removed**"* (see V1 mechanics at line 287 of `$PROJECT_ROOT/prompts/divine/divine_leverage_system.md`). V2 added a new "Apex Attention bands" sub-mechanic (V2.4) using the same name. The CodeRabbit reviewer flagged this as "Remove the contradictory Apex Attention model" — V1 says Apex Attention was REMOVED, V2 reintroduced it under the same name. The contradiction confused both the LLM and the reviewer.

The fix was to **rename V2's mechanic to "Pantheon Surveillance"** (V2.4 became "Hidden Reputation + Pantheon Surveillance bands"). The narrative semantics (band progression Unseen → Pantheon-tier) were unchanged; only the label differed.

The general rule: when iterating vN to vN+1, before introducing a new mechanic:

1. **Open the prior version's spec doc.**
2. **Grep for any term the new mechanic might use.** Look for terms explicitly marked "removed," "deprecated," "no longer separate," "merged," etc.
3. **If a term was retired in a prior version, pick a new name for the vN+1 mechanic** — even if the new mechanic is functionally identical to the retired one. Reuse the *category* (e.g. "hidden god-tier mechanic") without reusing the *label*.
4. **Document the rename in the V(n+1) changelog.** Future agents need to know that "Pantheon Surveillance" was previously called "Apex Attention" in V2 (and was "Apex Predator" in V1, which V1 then removed).

The naming-collision pattern is *especially* likely for god-mechanics terms because the same concept (how other gods perceive you, hidden bands, follower scaling) recurs across iterations. The temptation is to reuse the label because the concept matches. The fix is to rename every time, so each version has a distinct term inventory that's grep-discoverable.

**Anti-pattern:** *"Apex Attention means the same thing in V2 as it did in V1, so I'll keep the name."* Even if true, the V1 spec's explicit removal note will trip up the LLM. Always rename to a vN+1-specific label.

**Test before committing:** *"Does the prior version's spec explicitly mark this term as removed/deprecated/merged?"* If yes, rename.

**Cross-reference:** This is the same shape as P11/P15 (don't copy mechanics verbatim) but at the *term* level rather than the *concept* level. P11/P15 prevent copying mechanic shapes; P32 prevents copying mechanic labels.

Verified incident 2026-07-21: God of Murder V2 review (PR #8488 commit `2545378048`) by CodeRabbit flagged the Apex Attention naming collision. Resolution: rename V2's "Apex Attention" to "Pantheon Surveillance" in commit `9ab83527a6`. The renamed mechanic appears in V3 as PS (Pantheon Surveillance bands) — distinct from V1's "Apex Attention" (removed) and V2's pre-fix "Apex Attention bands" (renamed).

**P33 — Replace opaque meters with named, in-system consequences. (added 2026-07-28, Spellblade/Mortal Blade branch)**

The user's exact wording: *"lets not have scrutiny just make me get locked up or something generic, scrutiny gives me more responsibilities and since I'm a moral character if i let people die or bad things happen when i am officially responsible i gain one level of exhaustion"*.

When the user rejects a recurring-meter mechanic (scrutiny, infamy clock, suspicion tracker, heat meter variant), the substitute is **NOT** "remove the consequence and let the campaign run consequence-free." It is: **swap the opaque meter for a named, in-system, mechanically load-bearing consequence that fires only when the PC actually does the wrong thing.**

The verified pattern for the exhaustion-as-moral-cost case:

| Element | Rule |
|---|---|
| Trigger | ALL of: (a) PC was officially responsible for the people involved; (b) had a plausible opportunity to prevent the harm; (c) knowingly chose another priority OR failed through avoidable negligence; AND (d) the harm is serious enough to matter. |
| Cost | Named in the existing game system — gain exactly ONE level of exhaustion (D&D 5e mechanic). No new entity, no custom penalty. |
| Non-triggers | Good-faith attempts, overwhelming opponent action, non-responsible NPC deaths, reasonable tactical tradeoffs in combat, or shock-value deaths must NOT charge the cost. |
| Allowed generic substitutes | Custody / arrest / confinement / forced questioning / temporary imprisonment / loss of access / loss of status — anything the campaign system can already express. |
| Forbidden substitute | Auto-promoting the PC to ruler / commander / administrator / public leader "because their power makes them responsible." P34 covers this separately. |

The test before locking the cost design: **can the player read the trigger rule and predict exactly when the cost fires?** If the rule is fuzzy, it becomes arbitrary punishment — which is worse than the meter it replaced.

**Anti-patterns to avoid:**

1. **Removing the meter with no replacement.** "Just don't have scrutiny" leaves a hole — the PC faces no cost for exposure, suspicion, or moral failure, which makes high-tier play feel consequence-free. Always pair the rejection with a named substitute.
2. **Firing exhaustion on every death.** The instant a single preventable death charges 1 level of exhaustion, the next random mook death charges it too. The cost becomes wallpaper or a guilt-trip meter — both worse than the scrutiny meter it replaced.
3. **Hidden judgment calls.** "The GM decides if exhaustion fires" turns the cost into a mood. Either the trigger rule is precise and reproducible, or the campaign ends up with the same "the LLM invents consequences" problem the user was trying to escape.

**Cross-reference:** P5 (Trajectory of cost) and P25 (auto-win combat ladder) — both rely on the same principle that *named, in-system, load-bearing* costs are more durable than arbitrary GM judgment. The exhaustion rule is the canonical instantiation of this principle for moral-responsibility cost.

Verified 2026-07-28 on the Spellblade/Mortal Blade (Valeria Vex) campaign. User rejected the recurring scrutiny-meter mechanic from a prior campaign bible, and explicitly defined exhaustion-as-moral-cost as the replacement.

**P34 — High-tier fantasy must NOT auto-promote the PC to ruler/queen/administrator/public-leader. (added 2026-07-28, Spellblade/Mortal Blade branch)**

The user's exact wording: *"I wanna avoid becoming a warrior queen with lots of responsibilities like my old life"* + earlier *"In my last life, I had to sign tax decrees while my blade gathered dust. In this life, no one gives the orders."*

When a hidden-apex protagonist's lineage / power / reputation scales toward world-power tier, the LLM's default narrative gravity pulls toward "you are now the queen / commander / high lord / public defender." This is the **ruler-of-realm escalation anti-pattern**.

The shape of the failure:

1. The vN+1 spec emphasizes "hidden apex" and "conceal your true nature."
2. Mid-campaign, the PC defeats a major villain, exposes a conspiracy, or wins a battle that visibly affects thousands.
3. The LLM auto-promotes: "the people acclaim you as their new queen / leader / champion" — because the LLM conflates *being powerful* with *being responsible for everyone*.
4. The PC is now stuck running a realm, signing decrees, attending council meetings, and managing subordinates — exactly the administrative burden the player wanted to escape.

**Forbidden patterns:**

- Auto-promotion to leadership of any polity, faction, military unit, or guild.
- Permanent inheritance of a throne, seat, command, or title.
- "You are now the champion of the realm" as a single-scene decision that locks in obligations.
- Coupling "moral character" status (P33) with mandatory administrative duty.

**Required pattern:**

- The PC's *responsibility* is **local and elective**: choose whom to protect (Sarah + a small retinue + whoever they bond with at the table), not everyone the LLM can imagine.
- The PC's *moral cost* (P33) fires only on *actual* failures of explicit responsibility, never as a side-effect of fame or lineage.
- Political consequences of the PC's actions must produce *tactical situations* (combat, duel, escape, rescue, infiltration) — not *administrative obligations* (council meetings, taxation, military logistics).
- The high-tier endgame can include inheriting a *lineage* (relics, techniques, bloodline feats) without inheriting a *role* (ruler, commander, administrator). Pillar 4 + P12 already encode this distinction at the mechanic-stack level — extend it to the *role* layer.

**Cross-reference:** P14 (campaign = system, not story; multiple emergent endings) and Pillar 5 (Trajectory of cost) — both rely on the player choosing the path at the table, not the LLM pre-committing to "you become the new apex ruler" as the campaign's only resolution.

Verified 2026-07-28 on the Spellblade/Mortal Blade (Valeria Vex) campaign. The campaign is set in the same world as a prior iteration where the PC was a "Warrior Queen" who unified the continent — the new version's defining difference is explicitly *not* becoming her past self.

**P35 — Source-character / anime adaptation guardrail: preserve personality + voice + visual identity, FORBID plot / reveals / spoilers. (added 2026-07-28, Spellblade/Mortal Blade branch)**

The user's exact wording: *"lets copy characters from original source anime but dont copy storylines i will read the real manga later and dont want spoilers"*.

When the user names a source-anime (Bleach, Naruto, JJK, MHA, Frieren, etc.) as inspiration for *characters* but explicitly says they want to read the manga later without campaign spoilers, the spec must follow a **two-layer adaptation contract**:

| Layer | Allowed | Forbidden |
|---|---|---|
| Personality / MBTI / voice / speech patterns / inner monologue / temperament | ✓ YES | — |
| Visual signature / appearance / silhouette / weapon / outfit | ✓ YES | — |
| Known backstory up to whatever the user has seen | ✓ YES | Beyond the user's progress |
| Powers / abilities / class identity | ✓ YES (re-skinned to setting) | Direct mechanical import (P11) |
| **Specific plot events** | — | ✗ NO — never transplant a manga chapter as a campaign scene |
| **Reveals / secrets / character deaths / betrayals / future-arc payoffs** | — | ✗ NO — these are spoilers by definition |
| **Relationships / romantic arcs as the user knows them at the user's viewing point** | ✓ YES (electively) | — |
| **Future-arc romances / pairings / hookups the user hasn't read yet** | — | ✗ NO — even if implied by the source, do not commit |
| **Filler arcs / anime-only content** | — | ✗ NO — assume the user hasn't seen it either |

The test before locking a character reference: **would a reader who has finished the manga recognize this character and NOT feel the campaign spoiled the source material?** If yes → keep. If no → strip the spoiler-bearing detail.

**Concrete rules:**

1. **Adapt by category, not by event.** "Aizen-style intellect-and-power channel" is a category; "Aizen's betrayal of the Soul Society + Kyoka Suigetsu reveal sequence" is an event. The first is allowed, the second is a spoiler.
2. **Re-derive every relationship.** Two characters who fall in love in the source can *start* with chemistry and personality in the campaign, but the campaign must NOT pre-commit to the romantic outcome — leave it to the player's choice at the table (P14).
3. **Track the user's viewing point.** Before importing a character's arc, ask or verify how far the user has read in the source. If the user is "currently at episode N of anime / chapter M of manga," the campaign can adapt anything up to that point and nothing after. Beyond that point, the character is purely their personality + voice + visual identity.
4. **Permitted source material is personality-only by default unless the user explicitly OKs more.** When in doubt, default to "personality + voice + visual identity only" — strip everything else.
5. **Forbidden language in the spec:** "the equivalent of [manga arc] happens," "this character will eventually betray the group," "the player learns that X is actually Y's [relation]." These are spoiler-shaped patterns. Use personality-shaded foreshadowing ("X harbors a private ambition that surfaces only when the player pulls on it") instead.

**Cross-reference:** P11 (don't copy mechanic shapes verbatim), P15 (take inspiration, never copy, even when the user names the reference) — both apply to source-anime adaptation but were written for *mechanic* import. P35 is the *plot-and-revel* parallel: even when the user names a specific character, the *events* and *revels* from the source are off-limits unless the user has already seen them.

Verified 2026-07-28 on the Spellblade/Mortal Blade (Valeria Vex) campaign. The user named the source-anime inspiration explicitly and defined the spoiler-avoidance contract in the same message — the prompt must adapt the personalities/voices/visuals while keeping every manga event sealed until the user has read it themselves.

## Verification

After each campaign iteration, the deliverable must satisfy:

- [ ] Google Doc live with new title (matches the vN+1 framework) and full body
- [ ] Wiki source page in `~/llm_wiki/wiki/sources/` with frontmatter, version-comparison summary, and `Provenance` footer
- [ ] All new cross-linked concept stubs created under `wiki/concepts/` (for each new mechanic)
- [ ] All new cross-linked entity stubs created under `wiki/entities/` (for each new location/NPC)
- [ ] `wiki/index.md` updated in 3 sections (Sources / Concepts / Entities) with one-liner entries
- [ ] `wiki/log.md` updated with a dated ingest entry
- [ ] Guardrail table present in the doc with G1–GN identifiers, prompt-layer implementation notes, audit hooks, and open PR references
- [ ] Wiki push to `origin/main` succeeded; `git rev-parse origin/main` shows new SHA
- [ ] No pollution: `git log --oneline origin/main..HEAD` shows exactly the vN+1 commit, nothing else
- [ ] If the design brief named a reference shape (BG3 / Dark Urge / Mistborn / Berserk / Cosmere / etc.): a brainstorming spec was produced FIRST at `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`, the 4-part mechanic stack (P12) was derived against the vN+1's setting, and the Provenance footer cites the brainstorming handoff (per `references/brainstorming-handoff.md`)
- [ ] **God-tier mechanics satisfy P21–P26**: math is load-bearing (P21), rolls sit inside math-determined brackets per OPTIMIZE → ROLL (P22), per-dawn menu is context-aware not formulaic (P23), hidden mechanics surface as narrative bands (P24), combat ladder auto-wins mortals and rolls only for Chosen/divine (P25), and the mechanics apply to ALL setting gods not just the protagonist (P26)
- [ ] **Workflow: spec lands at both Slack thread + `~/roadmap/docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`** when the user picks option A in the brainstorming phase (verified location pattern from Nocturne v2 session 2026-07-21)
- [ ] **Mechanic-density iteration (P31)**: when the user says "not enough mechanics" or "lots of narrative," the vN+1 spec doubles mechanic count (e.g. V2's 8 sub-mechanics → V3's 20 sub-mechanics) following the 6-step growth pattern in `references/load-bearing-math-design.md`. Player-facing OPTIMIZE → ROLL surface stays intact.
- [ ] **Naming-collision check (P32)**: any new god-mechanic label was checked against the prior version's term inventory; retired terms are not reused. Document any renames in the V(n+1) changelog.
- [ ] **Consequence-as-cost discipline (P33)**: if the user rejected an opaque recurring meter (scrutiny / infamy clock / suspicion tracker), the spec replaces it with a NAMED, IN-SYSTEM consequence (e.g. one level of exhaustion per D&D 5e mechanic) and the trigger rule is precise and reproducible — not a GM mood call. Exhaustion / cost must NOT fire on good-faith attempts, overwhelming opponent action, non-responsible NPC deaths, reasonable tactical tradeoffs, or shock-value deaths.
- [ ] **No ruler-of-realm auto-promotion (P34)**: high-tier fantasy specs MUST NOT auto-promote the PC to ruler / queen / commander / administrator / public leader as a side-effect of fame, lineage, or power. Political consequences must produce tactical situations (combat, duel, escape, rescue, infiltration) — never administrative obligations (council meetings, taxation, military logistics).
- [ ] **Source-character spoiler-safety contract (P35)**: if the user names a source-anime / manga / novel for CHARACTER inspiration but plans to read the source later, the spec adapts ONLY personality / MBTI / voice / speech patterns / visual identity / known-backstory up to the user's viewing point. All plot events, reveals, betrayals, deaths, future-arc payoffs, romances, and anime-only / filler arcs from beyond the user's viewing point are FORBIDDEN. Default = personality-only when the user has not specified how far they have read.

## Related references (read before Phase 0)

- `references/version-comparison-template.md` — Phase 1 version summary table
- `references/guardrail-mapping-template.md` — Phase 7 guardrail mapping table
- **`references/brainstorming-handoff.md`** — Phase 0 contract when the user names a reference shape. The brainstorming skill is bundled with `claude-plugins-official/superpowers` v5.0.7 at `~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/skills/brainstorming/SKILL.md` — **NOT** in Hermes's skill namespace. `skill_view(name='brainstorming')` returning "not found" is a routing problem, NOT authorization to skip.
- **`references/load-bearing-math-design.md`** — Reusable god-campaign mechanics library. The 20 sub-mechanics (V3.0-V3.20) — seven-tier ladder, stat conversion formulas, Aizen linear-scaling formula, six god-class stat biases, seven Repr growth sub-systems, Action Tier economy with AT-3 Legendary Actions menu, D-faction response matrix, dawn-action archetypes, V2 → V3 mechanic-density delta table, worked examples, anti-patterns. Use this as the *starting library* when iterating any god-campaign vN+1 to vN+2 with the "not enough mechanics" complaint (P31). Covers the OPTIMIZE → ROLL pattern (P22), context-aware menu (P23), hidden mechanics with narrative bands (P24), combat ladder (P25), universal god stats with class biases (P26).

## Provenance

- v1.0.0 (2026-07-20): Visenya v9 — The Blood Dragon Apex Stalker (Dunk & Egg, 209 AC). 9 prior versions reviewed (v1–v8); 3 pillars preserved (hidden apex blood, mortal anchor, scaling tension); CHA-substitution trick pivoted from INT/WIS (v1 social geometry) to DEX/WIS (v9 physical geometry). 7 guardrails G1–G7 mapped to 11 open WA PRs/issues (#8469, #8473, #8443, #8387, #8468, #8472, #8386, #8382, #8400, #8336, #8335). Source Google Doc: 11HohncqogJHQtIk0_JwsEuz7IsaLolFw1rM1mePM3Bw. Wiki source: `wiki/sources/visenya-v9-blood-dragon-apex-stalker.md`. Brainstorm session Slack: C0AH3RY3DK6/p1784584425.185909.
- v1.0.1 (2026-07-20): Added P11/P12/P13 + `references/brainstorming-handoff.md`. P11 captures the BG3-import failure mode (PR #8483 mechanics copied verbatim into Visenya v9 Sanguine Thread / Mantle of the Sanguine Slayer). P12 introduces the **4-part endgame mechanic stack** (Anchor / Trigger / Aspect Shift / Successor) as the derivation grid for god-tier mechanics. P13 codifies the brainstorming-before-design protocol when the user names a reference shape. Cross-references added to Verification checklist.
- v1.0.2 (2026-07-20): Added P14 + P15.
  - **P14** captures the user's *"don't make me pick an ending, just save possibilities, we're designing the campaign not a fully decided story"* correction. The four-mode resolution ladder (Joining / Replacement / Refusal / Player-defined) becomes a durable shape across iterations — campaign design is *system* design, never *story* design.
  - **P15** is the punchline of P11 in user-facing language: when the user names a reference shape they mean *category*, not *mechanic* — derive against the vN+1's setting; refuse to copy even if the rename sounds plausible. Verified during Visenya v9 finalization when the user explicitly corrected *"don't directly copy Bhaal god of murder, take inspiration."*
  - Both pitfalls encode durable user preferences for this class of work — no longer need to surface in memory; the next design session starts already knowing.
- v1.0.3 (2026-07-21): P16, P17, P18 added.
  - **P16** codifies the `/superpowers brainstorm` slash-command as a binding workflow trigger. Loads the 164-line brainstorming skill at `~/.codex/superpowers/skills/brainstorming/SKILL.md`, switches to one-question-at-a-time mode, defers all implementation (no gog docs, no worktree, no wiki push) until the user approves the written spec at `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`. Verified on the God of Murder v2 brainstorm (2026-07-21 thread C0AH3RY3DK6/1784585087.439909).
  - **P17** captures the protagonist-rename pattern: when the iteration changes protagonist name but keeps setting + Quantified Mechanical Engine (Pillar 4), v1 wiki source page stays as canonical history; v2 gets a new source page alongside v1 (no rename, no supersede). Verified on Nocturne-as-protagonist iteration of God of Murder v2.
  - **P18** reverses the wiki-save ordering when v2 is imminent — wait for v2 spec approval before saving v1, else you create a redundant wiki supersede. Verified on "save this to wiki" mid-brainstorm (2026-07-21).
- v1.0.4 (2026-07-21): P19, P20 added.
  - **P19** captures the user's *"avoid defining too many new resources though, might be annoying to manage"* correction verbatim, and the prior *"i don't know about wound ledger maybe remove it"*. Hard cap of ≤5 trackers the player sees per dawn; anything beyond must reuse an existing Aizen / D&D 5e stat (DR / DPP / DAIR / F / RP / disposition). Includes a bound table of what to keep vs cut.
  - **P20** captures the prompt-shape contract for *"predict my taste" / "did you actually read X"* — make 3+3 bets, invite correction, do NOT pad with methodology. The trap-prevention: avoid analysis-paralysis explanations before placing bets.
  - Both pitfalls encode durable user preferences for this class of work — no longer need to surface in memory; the next design session starts already knowing.
- v1.0.5 (2026-07-21): P21, P22, P23, P24, P25, P26, P27 added + `references/load-bearing-math-design.md`.
  - **P21** captures the user's *"I just see calculations which don't mean much to me and usually just win rolls"* correction. Codifies the **load-bearing math test**: the math is load-bearing iff the player's optimal choice depends on what the math says. Stat sheets that the LLM ignores are decorative; the V2 spec is restructured so §8's math is the primary decision driver, not an appendix.
  - **P22** captures the user's *"look at the whoel D&D 5e system. A player will optimize the build/stats/items/startegy and then the roll is the last thing to add excitement and variance"* — the OPTIMIZE → ROLL pattern. Includes a 6-phase god-hunt action chain where the math decides 4 of 6 phases and rolls only adjust within brackets. Per-scene roll cap = 4.
  - **P23** captures the user's *"per-dawn menu - this seems too formulaic? ... maybe one day something more important is happening"* — context-aware menu (routine / triggered / quiet) instead of fixed A/B/C/D/E.
  - **P24** captures the user's *"players shouldn't know a number just see narrative consequences"* — hidden LLM-side mechanics surface as named narrative bands (Unknown / Whispered / Open / etc.), never expose the number to the player.
  - **P25** captures the user's *"Auto win combat on mortals I guess? Unless it's an avatar or chosen then maybe divine combat"* — combat ladder: auto-win on mortals, rolls only for Chosen / divine.
  - **P26** captures the user's *"All gods need to follow these mechanics and not just me"* — universal god stats apply to ALL setting gods (Faerûn pantheon), not just the protagonist. Includes the 6-class stat-bias system (War / Trickster / Domain / Magic / Death / Skilled) that makes mechanics universal + numbers unique.
  - **P27** captures the workflow improvement when the user delivers a multi-decision batch (≥5 sharp decisions in one message): lock all in one decision-stack table and move to spec, bypasses the brainstorming skill's one-question-at-a-time mode. Verified on the 8-decision batch from God of Murder v2 (2026-07-21).

## Cross-skill notes

- P19 (≤5 trackers) overlaps with `wa-campaign-content-analysis` Pillar 4 derivation. P20 (predict my taste) overlaps with `harness-postmortem` (state your reading + invite correction). The new P21–P26 are all unique to god-campaign design (Pillar 4 territory) and don't overlap with existing skills. P27 is a workflow improvement specific to the brainstorming-handoff → spec transition; it overlaps with the brainstorming skill's one-question-at-a-time default but only as an override. Background curator may want to consolidate at scale — deferred until v1.0.6.
- v1.0.7 (2026-07-21): P31, P32 added + `references/load-bearing-math-design.md` created.
  - **P31** captures the user's *"keep iterating on this campaign. It doesnt seem to have many god mechanics just lots of narrative?"* — the **mechanic-density iteration pattern**. When the complaint is "not enough mechanics," iterate V(n) → V(n+1) by doubling mechanic count via the 6-step growth pattern (find implicit mechanics → add 2-3 sub-mechanics per concept → add archetypes → add worked examples → add verification standards). Verified V2 → V3: 8 sub-mechanics → 20 sub-mechanics on God of Murder branch. Bound: don't cross 3x density or player-facing OPTIMIZE → ROLL surface degrades into bloat.
  - **P32** captures the **naming-collision check across versions**. When introducing new god-mechanics, grep the prior version's term inventory for explicit removal/deprecation markers. Don't reintroduce a retired term even with the same intent — pick a vN+1-specific label. Verified on the V1 "Apex Predator (No-Longer-Separate)" + V2 "Apex Attention bands" collision; resolution renamed V2 → "Pantheon Surveillance" in commit `9ab83527a6`.
  - **`references/load-bearing-math-design.md`** is the canonical god-mechanics library. The 20 V3 sub-mechanics are extracted from the V3 prompt overlay at `$PROJECT_ROOT/prompts/divine/divine_leverage_system.md` Section 9 (commit `1968a9b58e`). Future god-campaign iterations should start from this library and add 2-3 sub-mechanics per concept, not re-invent.
  - Both pitfalls encode durable user preferences for this class of work — no longer need to surface in memory; the next design session starts already knowing.
- v1.0.6 (2026-07-21): P28, P29, P30 added.
- **`references/p36-stable-universe-contract.md`** is the canonical companion for Pitfall P36 — closed-world mechanics. Spell-range table (Detect Magic 30 ft / Detect Thoughts 30 ft / Locate Creature 1,000 ft / Clairvoyance 1 mile / Scrying same plane / Nondetection 8-hour protection), verbatim user-correction catalog mined from 230 LLM-wiki transcripts (12,498 God Mode messages), the synthesized SHALL / SHALL NOT clause set, and the SRD 5.1 fact pack verified on 2026-07-29. Use this when designing the prompt-only closed-world mechanics contract; the umbrella SKILL.md keeps only the visible failure-pattern list.
- v1.0.8 (2026-07-28): P33 (consequence-as-cost discipline: replace opaque meters with named in-system costs like exhaustion-as-moral-cost, with a precise reproducible trigger rule), P34 (no ruler-of-realm auto-promotion: high-tier fantasy must NOT auto-promote the PC to ruler/queen/administrator as a side-effect of fame or power), P35 (source-character spoiler-safety contract: when adapting characters from a source-anime / manga / novel the user plans to read later, adapt personality + voice + visual identity only, never plot events / reveals / future arcs / filler). All three encoded the user's verbatim 2026-07-28 corrections on the Spellblade/Mortal Blade (Valeria Vex) campaign. Pillar 6 added to the catalogue as the "Consequence-as-cost discipline" branch pillar (mandatory whenever the protagonist has people in their care).
- v1.0.9 (2026-07-29): P36 added (closed-world mechanics contract) + `references/p36-stable-universe-contract.md` companion.
  - **P36** encodes the user's cross-campaign stable-universe preference. After auditing all 230 LLM-wiki transcripts (12,498 God Mode messages, 166 MB corpus, 210 exact-unique campaigns) and re-fetching the official WotC SRD 5.1 PDF, the audit established that the LLM repeatedly invents detection channels that D&D 5e does not provide (auditor materializations, magical signatures halfway across the world, synonyms for scrying) and the user repeatedly rejects them. P36 codifies the **default-D&D-5e-ruleset + Campaign Mechanics Manifest + Information Provenance Gate + Causal Consequence Gate + Setting Exception Registry** contract as the load-bearing shape. The user's examples ("Force push in Star Wars", "Dune god emperor could see the future") become the canonical model for lore-specific exceptions: permitted only when explicitly defined at campaign creation.
  - **`references/p36-stable-universe-contract.md`** carries the spell-range table, verbatim user-correction catalog, the synthesized SHALL/SHALL NOT clause set, and the SRD 5.1 fact pack verified on 2026-07-29 (Detect Magic 30 ft; Detect Thoughts 30 ft, surface only; Locate Creature 1,000 ft; Clairvoyance 1 mile; Scrying same-plane save-modified; Nondetection 8-hour protection). The umbrella SKILL.md keeps only the visible failure-pattern list; the companion file carries the full fact pack so P36 stays readable.
