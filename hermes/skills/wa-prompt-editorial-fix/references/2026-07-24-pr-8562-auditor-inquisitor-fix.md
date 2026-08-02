# Reference: PR #8562 — "fix(prompts): spawn canonical lore characters, not generic auditors"

Date: 2026-07-24
Repo: `$GITHUB_REPOSITORY`
Branch: `fix/spawn-canonical-lore-characters-not-auditors` (off `origin/main` @ `5285322aa1`)
PR: <https://github.com/$GITHUB_REPOSITORY/pull/8562>
Diff: `$PROJECT_ROOT/prompts/living_world_instruction.md`, +2/-0, 1 file

## Symptom

User read LLM-wiki campaign transcripts and kept seeing "auditors and inquisitors spawning" — investigators that sound like accounting, not lore. User wanted: when an NPC comes to investigate the player, it should be a **canonical character from the active setting** (Harpers, Zhentarim, Flaming Fist, City Watch, Night's Watch, Sith, etc.), not a generic placeholder.

User constraint (verbatim): *"Make a PR to change the prompts and try not to add a ton of content or delete some content we don't need fo make space code directly"*

## Diagnosis path (what made this a prompt-discipline fix, not a code fix)

```
grep -rn -E "auditor|inquisitor" $PROJECT_ROOT/prompts
```

Hits returned **zero** archetype-defining prompts. All hits were either:
- `audit_events`, `audit_flags`, `dice_audit_events`, `player_declared_outcome` → audit-trail **JSON schema** (totally different meaning)
- `Prince Caius` / `caius_auditor_arrival` / "the Reaper" / `Aethelgard Vanguard` → an **in-world canonical NPC** used as a JSON payload example in `living_world_instruction.md` lines 177–178 and `god_mode_instruction.md` line 332

Conclusion: the LLM was **inventing** "auditor"/"inquisitor" archetypes on its own. The existing in-world payload is a named character (Prince Caius, the Reaper), not a generic — and must be left alone.

## The fix

Added **rule #5** to the existing `## Lore-Appropriate Enemy Detection` section in `living_world_instruction.md` (between the Self-audit block and the `### PC-Private Knowledge Isolation` section). Verbatim text:

> **5. Spawn canonical lore characters, not generic archetypes.** When the world needs an investigator, agent, enforcer, official, or rival to come at the player, name a real faction/character from the active setting's lore — not a generic "auditor", "inquisitor", "inspector", "tax collector", or accountant-flavored NPC. A D&D Forgotten Realms campaign should send a Harper, Zhentarim spy, Flaming Fist captain, Lords' Alliance envoy, Order of the Gauntlet adherent, Red Wizard of Thay, or named in-world official — never a faceless "auditor arrives to investigate". A Game of Thrones-style setting should send a City Watch captain, a maester, a Littlefinger-style informant, a Night's Watch ranger, a Gold Cloak, or a named house agent. The same rule applies to every setting: name the actual in-world body that would plausibly investigate (the Sept, the Mage's Guild, the Sith, the Corps of Discovery, the in-world equivalent). Generic modern-day investigator roles are only acceptable when the campaign is set in a literal modern setting that has them. An NPC whose entire purpose is "come investigate the player" must still be factioned, named where lore permits, and motivated by an in-world trigger from rule #1 — never spawned as a placeholder antagonist.

## What I deliberately did NOT do

- **No backend enforcement.** `root-cause-first` discipline says: prompt/schema fix first, server guard only as a narrow logged invariant after explicit human approval for level-up work or documented insufficiency for other work.
- **No new prompt file.** Adding `living_world_canonical_npc_rules.md` would break the Gemini implicit-cache discipline (`your-project.com/AGENTS.md` "Prompt Duplication & Compression").
- **No lore dump.** Two lines of named factions is sufficient — the LLM has the canonical knowledge already.
- **No deletion of the `caius_auditor_arrival` example payload.** It is canonical in-world NPC content; cleaning it up would have inflated the diff and broken the existing worked example.
- **No `/es` capture.** I called this out honestly in the PR body: +2 lines of natural-language instruction, no test harness asserts on spawned NPC identity, capturing a before/after real-server comparison would be disproportionate to the change. Offered to spin one up if the user wants it.

## PR body (verbatim, evidence section)

> ## Why no `/es` evidence
>
> Per AGENTS.md: prompt-only changes still technically change model-side behavior. I did **not** generate a real-server / real-LLM capture here because:
>
> - The change is **+2 lines** of natural-language instruction; there is no test harness in this repo that asserts on spawned NPC identity during living-world turns.
> - Producing a real capture would require running a full backend, an LLM call, and inspecting ~50KB of model output to demonstrate the absence of one word — disproportionate to the change.
>
> If you want a follow-up real-server capture that contrasts 'spawn investigator → output before vs. after this PR', say the word and I'll spin one up and attach it here. Otherwise, the rule is model-side and CI lint doesn't exercise it.

## Why this skill was created from this session

The recipe (grep prompts → distinguish archetype-invention from canonical examples → add a single rule inside the existing section → minimal-diff PR from origin/main → honest evidence disclosure) recurs. There was no umbrella capturing it; `wa-mvp-site-settings-local-evidence` is the wrong neighbor (settings, not behavior discipline). Created `wa-prompt-editorial-fix` as the class-level umbrella.