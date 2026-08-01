# Personal-Scale Challenge Pattern (PC-Scaling Past Parity Band)

**Class-level prompt-design pattern.** Discovered 2026-07-26 from Visenya v9 campaign analysis (campaign_id `qoQtHsU7DxZnR24VNU9w`, 412 scenes, levels 6-21, 47 named NPCs).

## Definition

**Personal-scale challenge** is the dramatic register in which the player character and named NPCs stand *close enough in narrative power* that a single player choice (a disguise, a lie, a withheld word, a deferred payment) can resolve or doom the immediate situation. The pattern problem is: as the PC scales past the *parity band* (the level range the campaign established at character creation), the LLM **auto-escalates to mythic-tier antagonists** because peer-tier NPCs no longer threaten the PC. The high-tier game becomes abstract empire-scale politics, losing the personal-zero-sum register that gave the early game its dramatic edge.

## Symptom signature (verified on Visenya v9)

| Metric | Pre level-15 | Post level-15 |
|---|---:|---:|
| Two-way dialog % | **23.6** | 18.0 |
| PC-silent % | 76.4 | **82.0** |
| Median named NPCs per dynamic scene | 3-4 | 1-2 |
| Tier of NPCs | peer (L4-L8) | mythic (L20+) |
| Deferred consequence scale | personal (courier chain) | cosmic (world war) |

The pattern holds across the long campaign: level 8 (42% two-way) and level 10 (27% two-way) are the dynamic peaks; level 14 (100% PC-silent) is the collapse; post-level-15 stays in the 80%+ silent range because the LLM defaults to narrative-monologue mythic encounters.

## Why the prompt architecture's existing safety features don't catch this

The runtime prompt files already encode the relevant mechanics:

- **`narrative_system_instruction.md` §NPC Autonomy & Agency** (L304-316): NPCs have independent goals, refuse requests, may have hidden agendas.
- **§Victory Ripple** (L739): "After a surrender, the next 1-2 turns MUST introduce exactly ONE durable consequence" — three forms (splinter group / power vacuum / concrete cost).
- **`living_world_instruction.md` §Momentum Counterpressure** (L218): hidden events sit in the queue and surface via natural triggers.

These mechanics produce **forward pressure inside a stable power band**. They do NOT solve the structural problem that:

- At low-mid levels, the PC is *in* the parity band; Social HP, disguises, faction politics all work natively.
- At high levels, the PC is *above* the parity band; every surviving NPC is either a minion or a mythic-tier antagonist. There is no middle ground where personal zero-sum choices still bite.

## Regex classifiers (for raw `.txt` analysis)

The user-perceived dramatic intensity comes from cues that don't always keyword-match, but the following heuristic density counts (per 1k words) captured the broad pattern:

```python
# Personal-scale structural markers — these are what users feel as "dynamic"
CONCEALED_RE = re.compile(
    r"(?i)(?:you (?:don't|do not) (?:see|notice|realize|know|hear (?:about)?)|"
    r"no one (?:mentions?|tells? you)|that will matter later|to your knowledge|"
    r"the bruise fades|silently,? without (?:fanfare|comment|hint)|"
    r"seeds? of|the cost is not yet|a name (?:is added|will be remembered)|"
    r"she (?:will not|won't) (?:know|see) until|silently (?:added|witnessed)|"
    r"a debt is (?:created|silently)|the (?:Sanguine Thread|wound ledger)|"
    r"promised (?:unto|to)|filed for later collection|witnesses? were watching|"
    r"to no (?:notice|comment))"
)

ZERO_SUM_RE = re.compile(
    r"(?i)(?:you cannot please both|sacrifice (?:is required|must be made)|"
    r"they will hate you|a cost must be paid|cannot save (?:them|both|everyone)|"
    r"the other (?:side|faction)|mortal enemies|burn (?:a|the) bridge|no clean win|"
    r"price must be paid|the wound ledger|he does not (?:approve|forgive)|"
    r"she will not forget|you have made (?:an? )?enemy)"
)

# Distinct-personal-NPC density (more reliable than keyword counts)
# Per-scene count of `<Name> (<Level>, ...>` and `<Name> (Age N) ...` patterns
# NPCs with distinct private agendas each get their own descriptive paragraph
```

Density thresholds (from the Visenya v9 baseline):

| Metric | Pre L15 | Post L15 | Notes |
|---|---|---|---|
| Concealed-consequence / 1k words | 0.072 | 0.050 | Slight drop-off |
| Zero-sum / 1k words | 0.056 | 0.037 | Slight drop-off |
| **Distinct-NPC paragraphs / scene** | 3-4 | 1-2 | Strong signal |

**Caveat**: PC-silent %, zero-sum, concealed-consequence densities are heuristic. The user's qualitative perception of "more dynamic" correlates with cues the simple classifiers miss — NPC body-language shifts (e.g. "frequency", "Discordant", "rising panic"), dice rolls named in passing (e.g. `1d20+6 = 23 vs DC 18`), explicit cooldowns (e.g. "the 48-hour cooldown protects your identity"). Per-scene NPC density is the strongest single signal.

## Five prompt-only fixes to preserve personal-scale challenge at high tier

All setting-agnostic; all in currently-loaded runtime prompts. Setting-agnostic edits go in `narrative_system_instruction.md`, `dialog_system_instruction.md`, `living_world_instruction.md`. Setting-specific implementations map via `{{TEMPLATE_HOOKS}}` per `$PROJECT_ROOT/prompts/AGENTS.md`.

### Fix 1 — Tier Compression (anti-scaling-whiff)

**Where**: new section in `narrative_system_instruction.md` after the existing `§NPC Autonomy & Agency`.

**Why**: Explicitly forbid the LLM from auto-scaling the parity-band NPCs away. The original peer-tier NPCs (level 4-8 in Visenya's case) should *retain* their level range across the campaign, not drift up mechanically with the PC.

**Pattern text**:

> **Tier Compression (Anti-Scaling Whiff)**
>
> When the player character's level (or narrative power) approaches or exceeds the historical NPC "tier band" the campaign started in, **do not collapse to mythic antagonists.** Compress the encounter space so personal-scale zero-sum trade-offs remain available:
>
> 1. **Preserve the original-tier peer band.** If the campaign began at level 6 with level-4-to-8 NPCs as peer tier, retain 3-5 named NPCs at that level range across the entire campaign, *level-locked or -banded*, not auto-scaling with the PC. These are the people whose lives the PC once held in her hands — their grudges, marriages, recoveries, and quiet betrayals should still matter.
>
> 2. **Maintain the disguise / concealment game.** When the PC's standing would let her resolve situations instantly with reputation, she should still face scenes where a *peer* NPC holds information she lacks, and a Persona (disguise, frame, social mask) converts that information gap into advantage.
>
> 3. **Inject "long-tail consequences" at parity band.** Player actions during the parity band create enemies, debts, and confidants. These NPCs keep acting across levels — visiting a farm you once burned; producing a child you once orphaned; calling in a favor ten years late.
>
> 4. **Choose PERSONAL pressure over MYTHIC pressure when both are possible.** A disinherited elder cousin suing for the barony over a procedural flaw is preferred to a "world-war alliance against you" — unless the world-war is genuinely called for by state logic.

### Fix 2 — Consequence-Hiding Heuristic

**Where**: rewrite the second paragraph of §NPC Autonomy & Agency in `narrative_system_instruction.md`. Keep the existing "independent goals / refuse requests / hidden agendas" content above; replace the implicit "consequences are emergent" language with explicit asymmetric-disclosure guidance.

**Why**: User explicitly liked "zero-sum consequences I can't please anyone but the LLM should hide the consequences from me until later." The mechanics exist (`Living World` `hidden: true`, deferred events); what is missing is a *heuristic* that tells the LLM when and how to hide.

**Pattern text**:

> **Consequence-Hiding Heuristic (MANDATORY when stakes warrant it)**
>
> When the player's action produces a *visible* effect but a *hidden* downstream consequence (an NPC's grudge, a faction's quiet counter-move, a financial debt, a vow sworn), do NOT narrate the downstream consequence in the same turn. File it as a deferred, partially-disclosed effect and surface it through:
>
> 1. **Asymmetric disclosure:** the *least informed* NPC in the scene says aloud the part of the consequence they noticed; the rest is filed silently. The player can infer some of it; if they ask "what did she mean?", surface ONE more detail.
> 2. **NPC body-language signal:** an NPC's expression flickers but doesn't speak. Do not editorialize in the player character's POV — let the player's curiosity drive the chase.
> 3. **Ship-named-file on `world_events`:** write the deferred event into state with `hidden: true`. The "Living World" trigger surfaces it on a 1-3 turn delay, *naturally* through messenger, rumor, or NPC return.
> 4. **Mirror the user's instinct:** if the player is *delighted* by not knowing what they did, you are doing it right. If they ask "what happened with X?", reveal what you have filed — but no more.
>
> The user's preference is **zero-sum pressure that resolves asymmetrically across long time horizons** — the player should be told the cost was paid and *not yet* what the cost was.

### Fix 3 — High-tier NPCs are still people

**Where**: `dialog_system_instruction.md` §1.1 (Voice Construction Framework) — add a row to the table.

**Why**: When the LLM renders level-20+ NPCs, it defaults to monolithic-elder-being monologue — cosmic stakes, no domestic interior. That collapses the dramatic register to abstraction.

**Pattern text** (row for the table):

> | **Power standing vs PC** | NPCs whose standing *equals or exceeds* the PC are not monolithic elder beings; they have the same mundane private anxieties as any tier (debts, sick children, lovers, pride, favorite foods). Power does not erase personhood. Render NPCs at the PC's level or above with the same emotional granularity as low-tier NPCs. |

### Fix 4 — Force-a-Trade, not Flat Refusal

**Where**: `dialog_system_instruction.md` §5.3 (Conflict & De-escalation). Replace the section on social outcomes.

**Why**: NPCs that respond to requests with "no, final" are not characters; they are walls. Walls do not advance drama. The user wanted the *no* to come with a *price* — what would the NPC accept instead.

**Pattern text**:

> **Section 5.3 — Conflict & De-escalation**
>
> Verbal conflict can:
>
> 1. **Deny-and-redirect:** the NPC refuses the player's request and offers an alternative that still costs the player something.
> 2. **Conditional acceptance:** the NPC accepts only if the PC first pays something the PC has *already earned* in the campaign (a favor, gold, reputation, time, presence at an event).
> 3. **Accept and betray later:** the NPC accepts now and reveals — three turns later via a messenger or rumor — they have already begun the counter-move. Asymmetric disclosure applies (Fix 2).
> 4. **Force-a-trade:** the NPC offers an exchange the PC didn't ask for. The *cost* is named but the *consequence* of refusal is not. The player must choose with incomplete information.
>
> **Avoid "flat refusal" as a default outcome.** A character who says "no, and that's final" without offering an alternative is not a character — it is a wall. Walls do not advance drama. Where the NPC's Hard Limit applies, they should still offer an alternative path the player can pursue.

### Fix 5 — Anti-Creep on Major Events

**Where**: `living_world_instruction.md` Major Event Rarity Budget (around the `major_event_pressure_budget` object section). Append a rule.

**Why**: The `major_event_pressure_budget` mechanism was designed to *prevent escalation creep*. But it's a budget *count*, not a *tier* check — the LLM can spend its one allowed major event on a cosmic-tier consequence even when the user's preferred register is personal-scale.

**Pattern text**:

> **Major Event Tier Rule (anti-escalation creep).**
>
> When the player character's level exceeds the campaign's parity band, **down-shift the major-event tier by one notch** in personal-scale encounters. A "+5 XP for taking a disinherited cousin to court" is preferred to a "+200 XP for existential epiphany before the mirror enemy." Both are "major events" — but the first keeps the personal-band stakes the user prefers.
>
> Concretely: when the same narrative situation could be resolved at the original-tier band (the cousin who was the PC's level-4 squire ten years ago is now a level-6 lord with a daughter; an old bandit who survived the PC's purges is now a level-7 sellsword captain; a Sept-priest the PC once threatened is now a Septon-Archbishop), prefer that resolution. Reserve mythic-tier for arcs the user explicitly frames as mythic.

## Verification recipe (for post-merge verification)

Run a new campaign to high-tier (level 15+) with the five fixes in place. Then re-run the analyzer at `/tmp/analyze_visenya_v9_v2.py` (or its equivalent against the new campaign's raw `.txt`). Expect:

- Two-way dialog % in high-tier scenes rebounds from 18 → 22+
- Distinct named NPCs per dynamic scene stays ≥3 through level 20+
- Concealed-consequence density in post-L15 scenes approaches pre-L15 baseline (0.05 → 0.07+/1k)
- PC-silent % in high-tier scenes stabilizes near 70-75% (vs 82% baseline)

Compare pre-fix to post-fix using the same regex set above. **Class-level lesson**: the prompt-fix-shipped-but-LLM-ignores-it phase (`wa-campaign-content-analysis` Phase 6) applies here — verify, don't assume.

## Source artifacts

| File | Contents |
|---|---|
| `~/.hermes/visenya_v9_diagnosis_2026-07-26/diagnosis.md` | Full Visenya v9 diagnosis (problem + 5-fix recommendations + verification recipe) |
| `~/.hermes/visenya_v9_diagnosis_2026-07-26/all_scenes.jsonl` | Per-scene structured rows (412 scenes) |
| `~/.hermes/visenya_v9_diagnosis_2026-07-26/scenes_by_level.json` | Per-level bucket histograms |
| `~/.hermes/visenya_v9_diagnosis_2026-07-26/samples.json` | 4 representative scenes (pre-L15 dynamic, pre-L15 quiet, post-L15 dynamic, post-L15 quiet) |
| `~/llm_wiki/wiki/sources/qoqthsu7dxznr24vnu9w-qoQtHsU7.md` | Wiki source page for the campaign |
| `~/llm_wiki/wiki/concepts/high-tier-personal-scale-challenge.md` | Concept page (the durable pattern, abstracted beyond Visenya) |
| `/tmp/analyze_visenya_v9_v2.py` | Reference analyzer (regex classifiers, level buckets, pre/post split) |
