---
title: Character Evolution & Mystery Architecture (v1.2.0 reference)
skill: campaign-creation
version: 1.2.0
date: 2026-07-28
---

# Character Evolution & Mystery Architecture — Reference

This is the full schema + operational contract for v1.2.0's internal-drive engine.
The SKILL.md gives the rules; this file gives the templates and examples you can
copy into a new bible. **All content here is LLM-internal** unless explicitly
noted as bible-resident.

## 1. The Want / Fear / Boundary triple

The minimum viable state for any NPC (protagonist, retinue, family, faction
leader, named antagonist). Three strings, one NPC, updated on trigger.

```yaml
npc: <name>
want: "To be the only one her father ever trusted."
fear: "Being abandoned by the people she chose."
boundary: "She will never lie to a child."
```

The triple is the **structural seed** of every other evolution mechanic. Without
it, mystery design and personal-growth design have nothing to attack.

## 2. The [character_state_update] log format

When a game event fulfills, negates, or mutates any field, log it in DM notes.
Never in the bible body.

```
[character_state_update]
  npc: <name>
  field: Want | Fear | Boundary
  transition: fulfilled | negated | mutated
  trigger_event: <scene or event reference — e.g. "Act II Scene 7: <name> revealed the ledger to the Council">
  new_value: <post-transition value — for mutated, the new framing>
  old_value: <archived for mutated>
  evidence: <1-2 sentences justifying the transition>
  downstream_behavior_shift: <what changes in NPC scenes from this update onward>
```

The `downstream_behavior_shift` field is **critical** — without it, the LLM
will re-read the same Want/Fear/Boundary as if no transition happened.

## 3. Stress arc — full 16-type stress catalog

Under sustained pressure (3+ consecutive high-stress scenes, a critical failure,
or a betrayal by a trusted ally), the character drifts toward their type's
**stress pattern**. The drift is a 1-3 scene window; it is **not** a permanent
shift. After the trigger resolves, the character either returns to baseline or
grows into a new baseline if the personal-growth direction was advanced.

Reference each type's canonical stress pattern at `~/llm_wiki/wiki/concepts/mbti/`
(one page per code: INTJ, INFJ, INTP, INFP, ISTJ, ISFJ, ISTP, ISFP, ENTJ, ENFJ,
ENTP, ENFP, ESTJ, ESFJ, ESTP, ESFP). The page locations are wikilinks so LLM
context retrieval can surface them on demand — **do not paste the type code or
its category label into the bible**.

Quick reference (partial; full table lives in the per-type pages):

| Dominant function | Typical stress drift | Typical growth direction |
|---|---|---|
| Ni-dominant (INFJ, INTJ) | Withdrawal; hyper-critical inner tribunal; door-slam cuts | Trust the present; release the need for absolute foresight |
| Ne-dominant (ENFP, ENTP) | Scattered focus; broken promises; people-pleasing collapse | Sustain commitment through dullness; honor the constraint |
| Ti-dominant (INTP, ISTP) | Paralysis; withdrawal into analysis; silent correction of others | Act on incomplete information; permit imperfection |
| Fi-dominant (INFP, ISFP) | Emotional flooding; values martyrdom; sudden exit | Separate self-worth from values-stance; let others carry weight |
| Te-dominant (ENTJ, ESTJ) | Micromanagement; command-by-fiat; contempt for slower allies | Lead by outcome, not process; trust the chain |
| Si-dominant (ISTJ, ISFJ) | Rigid re-enactment; procedural cruelty; nostalgic freeze | Update the playbook; accept that what worked once may not work again |
| Fe-dominant (ENFJ, ESFJ) | Image-management overdrive; conflict-avoidance; approval-seeking | Tolerate disapproval; name the shadow need |
| Se-dominant (ESTP, ESFP) | Risk escalation; provocative humor; present-tense numbness | Pause for the future; bear the boring work |

## 4. Mystery schema — full `mystery_state` block

```yaml
mystery_state:
  id: <slug, e.g. "who-killed-the-archon">
  active:
    - id: <sub-mystery-slug, e.g. "ledger-forgery">
      hidden_fact: <the truth the players must uncover, e.g. "The Archon's signature on the war-decree was forged by her Chancellor 3 weeks before her death">
      discovery_order_recommended:
        - 1: <first clue the player should plausibly encounter, e.g. "The Archon's steward claims she never signed the decree; the wax seal is wrong">
        - 2: <second clue, e.g. "The Chancellor's handwriting on the back of the decree matches the inner margin notes">
        - 3: <third clue, e.g. "The Chancellor's apprentice is wearing a brooch that belongs to the Archon's family vault">
      clue_trail:
        - clue_1:
            name: <display name>
            where: <location / scene / NPC drop>
            what's_required_to_notice: <a perception check, an NPC's confession, a document the PC already holds>
            what's_required_to_interpret: <a lore check, an NPC who can decode the cipher>
        - clue_2: {...}
        - clue_3: {...}
      suspect_branches:
        red_herring:
          suspect: <NPC name>
          motive_frame: <how this branch looks true — the reason the player initially suspects this person>
          falsifying_evidence: <a clue that disproves it — usually one of the clue_trail entries>
        partial_truth:
          suspect: <NPC name>
          motive_frame: <how this branch is half-right — what they did, but not why>
          what_it_misses: <the missing half — usually the real_answer's hidden motivation>
        real_answer:
          suspect: <NPC name>
          motive_frame: <the actual answer — the truth the player arrives at>
      hits_vulnerability:
        # This is the most important field. The mystery is designed to attack
        # an NPC's Want/Fear/Boundary. Without a targeting linkage, the mystery
        # is decorative — cut it.
        npc: <name>
        field: Want | Fear | Boundary
        attack_vector: <how the mystery's resolution would mutate the field, e.g. "forc[es] the NPC to break their own boundary by publicly accusing their mentor">
      cost_if_missed: <what happens to the campaign's stakes / the NPC's state if the player never solves the mystery>
  resolved:
    - id: <sub-mystery-slug>
      real_answer: <confirmed truth (after PC investigation)>
      cost_to_npc: <how the resolution mutated the NPC's Want/Fear/Boundary triple>
      scene_where_resolved: <scene reference>
      pantheon_temperature_delta: <if the mystery affected a god-campaign Pantheon Temperature tracker>
```

### Why 3 clues, 3 branches

- **3 clues**: enough to triangulate; not so many that a single missed clue
  ends the investigation. The discovery_order_recommended field guides the LLM
  but the player can find them out of order — that's the system playing the
  player, not the other way around.
- **3 branches**: red herring (cheap read), partial truth (reward for solid
  work), real answer (the full reveal). Without all three, the player either
  gets the answer in clue 1 (no investigation) or has nothing to test
  hypotheses against (no accountability).

### Mystery density rule

A 100-scene arc should carry roughly **8-12 active mysteries** at any time,
with the average mystery resolving 1-3 scenes after the player unlocks its
final clue. Mysteries that stay active longer than 5 scenes without
advancing should be **cut or merged** — stale mysteries rot the campaign.

## 5. Personal-Growth Direction schema

The Personal-Growth Direction is loaded as sub-section 10 of the Personality
Template Part 1.VI Psychological Deep Dive. It is the engine the LLM uses
when checking whether an act satisfies the internal-drive plot arc rule
("advance growth direction OR confront insecurity OR reframe Want").

```yaml
personal_growth_direction:
  lesson:
    statement: <the cognitive/emotional insight the character must integrate, e.g. "Letting go of control is not the same as losing love">
    evidence_threshold: <what kind of scene would prove the character has integrated it, e.g. "scene where <name> delegates a critical decision without intervening">
  healing:
    wound: <the wound or pattern, e.g. "the abandonment they keep re-enacting with every trusted ally">
    target: <what healing looks like, e.g. "<name> stays in the room when the lover walks out, without chasing">
  confrontation:
    lie_they_believe: <the truth they refuse to face, e.g. "their mentor was right that they are unremarkable">
    truth_they_must_face: <what must replace it, e.g. "their mentor was wrong; their power is not derived from approval">
```

A character may have **multiple active growth directions** if the campaign
is dual-protagonist or if they are a faction leader who must grow alongside
their policies. Cap at 2-3 per character to keep the LLM's attention usable.

## 6. Stress Arc & Insecurity Map schema

Loaded as sub-section 11 of the Personality Template Part 1.VI. Tracks what
fires under pressure, what it looks like in scene, and which mystery is
positioned to hit each insecurity.

```yaml
stress_arc_and_insecurity_map:
  stress_pattern:
    trigger_conditions:
      - <what kind of scene kicks off the drift, e.g. "3+ consecutive high-stakes negotiations">
      - <e.g. "a betrayal by an ally the character chose, not assigned">
    behavior_drift:
      - surface: <observable behavior, e.g. "Voice flattens; long silences between sentences">
      - surface: <e.g. "Stops attending meetings; cancels one-on-ones">
      - surface: <e.g. "Substitutes family for official ties in conversation">
    duration: "<n>-scene window"
    resolution_condition: <what ends the drift, e.g. "confession from the ally, time skip of 2 weeks, or a scene where the character names the wound aloud">
  insecurities:
    - id: <slug>
      label: <display name, e.g. "replaceability">
      trigger_cue: <specific situational trigger, e.g. "PC publicly praises a rival with more institutional authority">
      narrative_tell: <what the player sees, e.g. "stops eating at meals; voice flattens; retreats to the study">
      surface_response:
        most_likely: <e.g. "withdrawal">
        risk_of_escalation: <e.g. "self-sabotage that frames the abandonment as a choice">
      mystery_targeted: <which active mystery is positioned to hit this insecurity, by sub-mystery id>
    - id: <slug>
      ...
  # 3-5 insecurities; cap at 5 so the LLM doesn't lose track.
```

## 7. Internal-drive plot arc check

Each act must do at least one of:

1. **Advance the personal-growth direction** for the protagonist or a key NPC.
2. **Confront an insecurity** from the Stress Arc & Insecurity Map.
3. **Reframe a long-held Want** from the Want/Fear/Boundary triple.

If an act does none of the three, it is filler — rewrite. A 3-act campaign
typically has 1-2 advancing + 1 confronting + 1 reframing events distributed
across the acts, weighted earlier toward confronting and reframing, weighted
later toward advancing.

**Per-act checklist (paste into your planning notes):**

```
Act <N> internal-drive check:
  [ ] Advances protagonist Personal-Growth Direction?
  [ ] Advances any key NPC Personal-Growth Direction?
  [ ] Forces an insecurity to fire in scene?
  [ ] Presents evidence that reframes a long-held Want?
  [ ] Mystery resolved this act hits its targeted Want/Fear/Boundary?
  [ ] Starting Scene of this act surfaces the next clue?
If 0 boxes are checked: rewrite the act.
```

## 8. Panoply–Retinue binding examples

For at least 1 of the 3-5 panoply items, document an inline binding in the
panoply item's Sub-Template C Tier III (Mythic Origin):

```yaml
- item: The Iron Locket of Halvar
  classification: amulet / keepsake / relic
  tier: IV
  mythic_origin: |
    Gift from Halvar's grandmother on the eve of his mother's funeral.
    She told him: "Carry this when you doubt the woman you chose."
    The locket binds to one of <PC name>'s retinue NPCs: when the NPC
    is asked by the PC to cross the boundary they swore in their
    Stress Arc, the locket vibrates — a warning that the player's
    request is asking too much. This is the campaign's primary
    mechanism for forcing the player to confront the NPC's Want/Fear
    /Boundary triple.
  system_metrics:
    passive_property: "+1 to Persuasion checks when speaking to <retinue NPC>"
    active_feature:
      action_economy: "reaction"
      trigger: "when the PC issues a command that targets the bound NPC's Want / Fear / Boundary"
      effect: "the locket vibrates; the bound NPC rolls a DC 15 Wisdom save — on a fail, they confide the field they're protecting"
      daily_uses: "unlimited"
  narrative_side_effect: |
    First use of the locket triggers the bound NPC's "replaceability"
    insecurity. The scene is the player's first signal that NPCs are
    not interchangeable even in a high-stakes campaign.
  personalization_binding:
    bound_to: <retinue NPC name>
    binds_to_growth_direction: <which Personal-Growth Direction sub-field — lesson/healing/confrontation>
    binds_to_insecurity: <which Stress Arc & Insecurity Map entry>
```

## 9. Verification recipes

After writing the bible, run these locally:

### Verify no MBTI leaks to player-facing prose

```bash
grep -nE '\b(INTJ|INFJ|INTP|INFP|ISTJ|ISFJ|ISTP|ISFP|ENTJ|ENFJ|ENTP|ENFP|ESTJ|ESFJ|ESTP|ESFP|Analyst|Diplomat|Sentinel|Explorer)\b' <bible>.md
```

Should match only inside explicit DM-notes fenced blocks, never in the main
body. If any match appears in the body, move it to DM notes or rewrite the
sentence as a behavior/narrative description.

### Verify every retinue NPC has Personal-Growth Direction + Stress Arc + Want/Fear/Boundary

```bash
grep -nE '^### <NPC name>$|^  - \*\*(Want|Fear|Boundary|Personal-Growth|Stress Arc)' <bible>.md
```

### Verify the Mystery Tracker is present in Section 8

```bash
grep -nE '^## Section 8|mystery_state:|hits_vulnerability:' <bible>.md
```

### Verify the Starting Scene surfaces a clue

```bash
grep -nE 'first clue of an active mystery|surface.*clue|overheard|letter delivered|visible anomaly' <bible>.md
```

### Verify internal-drive plot arc check passes per act

Spot-check each act's planning notes against the per-act checklist in §7.

## 10. Cross-references in the skill

- **SKILL.md** → "## Character Evolution & Mystery Architecture (v1.2.0)"
  (rules + table summarizing where this machinery lives).
- **SKILL.md** → "Pitfall P23" (the no-MBTI-leak contract + grep recipe).
- **SKILL.md** → Personality Template Part 1.VI sub-sections 10 + 11 (the
  Psychological Deep Dive extension).
- **SKILL.md** → Step 5 Retinue requirements (Personal-Growth + Stress +
  Want/Fear/Boundary + Panoply–Retinue binding).
- **SKILL.md** → Step 9 Section 8 Mechanics (Mystery Tracker option).
- **SKILL.md** → Step 10 Starting Scene (first clue required).
- **SKILL.md** → Provenance v1.2.0 (changelog entry).
- **External** → `~/llm_wiki/wiki/concepts/mbti/` (16 MBTI type pages,
  wikilink-only — ingested by sibling worker D; if unavailable at write
  time, fall back to the 16-type stress catalog table in §3 above).

## 11. Provenance of this reference

- v1.2.0 (2026-07-28): Created alongside the v1.2.0 SKILL.md update. Holds
  the full schemas (`mystery_state`, Personal-Growth Direction, Stress Arc &
  Insecurity Map, Want/Fear/Boundary triple, `[character_state_update]` log,
  Panoply–Retinue binding example) so future sessions can copy them into a
  new bible without re-deriving the contract. Companion to the
  "Character Evolution & Mystery Architecture" section in SKILL.md.
