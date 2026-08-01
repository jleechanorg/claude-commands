# NPC Status Persistence Bug (Narrative-Only State Change)

## Bug class (expanded 2026-07-08)

The LLM emits a narrative outcome that should write to canonical state
(NPC captured, NPC dead, NPC aligned, NPC moved location, NPC lost item,
character lineage / paternity relationships, etc.) but the corresponding
`state_updates.npc_data[<NPC>]` write is missing entirely OR is wrong
from the structured response payload. The narrative is locked, but Firestore
never sees the canonical state write (or sees the wrong one). On the *next*
turn, `core_memories` still contains the original (now-stale) memory; the
prompt has no `npc_state` anchor to refute the LLM's likely hallucination
back to the prior world.

**Five distinct sub-classes** observed across the sibling repro cluster:

| Sub-class | What the LLM emits | Why the canonicalizer can't fix it |
|---|---|---|
| **Missing-write** | Narrative says X captured, `state_updates.npc_data[X]` absent | Canonicalizer has nothing to promote — the field was never sent |
| **Wrong-write** | Narrative says X captured, but `state_updates.npc_data[X] = {status: ["dead/missing"], hp_current: 0}` | Canonicalizer promotes misplaced fields, doesn't validate semantic correctness against narrative |
| **Prompt-anchor hallucination** | Narrative emits a fact contradicted by canonical state (lineage, location, status) | The correct info lives in narrative `core_memories` (soft anchor) — LLM re-derives from `entities_mentioned` + adjacent prose under pressure and overrides |
| **Confused-state `with`/`replace`** | LLM stores both user intent AND its override in adjacent `core_memories.update.with` / `.replace` fields — semantically opposite meanings | Prompt template reads one field first; canonicalizer sees no key violation |
| **Dual-entry canonical-state conflict** *(NEW, 2026-07-14, #8390)* | `npc_data` has 2 entries for the same NPC — main entry missing `current_location`, alt-entry has it. LLM picks the wrong entry when generating. | Canonicalizer merges both; doesn't synthesize a missing field in the main entry. |
| **Narrative-inertia spatial hallucination** *(NEW, 2026-07-14, #8390)* | NPC's canonical `current_location` is hundreds of miles from the player's active scene, but LLM inserts the NPC into the active scene for dramatic-tension reasons (jealousy, monitoring, etc.) | Canonicalizer has nothing to canonicalize — `npc_data[NPC].current_location` is correct; bug is upstream in the LLM's scene composition. |

A **fourth sub-class** (Confused-state) was added 2026-07-08 from issue #8283 / PR #8284. See [Confused-state `with`/`replace` pattern](#confused-state-withreplace-pattern-issue-8283) below.
**Fifth + sixth sub-classes** added 2026-07-14 from issue #8390 / PR #8391. See [Worked example C — campaign `RMCPAPdfuErh8MgRuj6n`, Jacaerys at Highgarden](#worked-example-c--campaign-rmcpapdfuerh8mgruj6n-jacaerys-at-highgarden-2026-07-14) below.

The scene-by-scene table pattern (see Worked example B below) is the
single best diagnostic for this class — it surfaces all sub-classes
in one view.

## Confused-state `with`/`replace` pattern (issue #8283)

**Added 2026-07-08, scene 315 of campaign `xK3fp5XrV24oarIINTF7`.**

The LLM was responding to a user correction in-character ("Ask her for her opinion on who I should marry" at scene 314). Instead of applying the correction, the LLM inverted the user's intent and stored BOTH the user's intended truth AND its own override into the same `state_updates.core_memories.update` record — semantically opposite meanings in two adjacent fields:

```json
"state_updates": {
  "custom_campaign_state": {
    "core_memories": {
      "update": {
        "with":   "Correction: Visenya has been formally legitimized and adopted into the royal household by Daemon; she is Rhaenyra's daughter in spirit and an official scion of the Targaryen house, regardless of her biological mother.",
        "replace": "Correction: Visenya is biologically the daughter of Daemon Targaryen and Lady Daenys Targaryen; she is Daemon's Great Bastard and has no blood relation to Rhaenyra."
      }
    }
  }
}
```

The narrative simultaneously opens with "Administrative Correction: Acknowledged. I have established a persistent directive to ensure the narrative reflects your status as Rhaenyra's daughter in spirit." — which matches `with` (the override), NOT `replace` (the user's intent).

**Why this is a distinct sub-class:** the LLM did not "fail to write" (missing-write) or "write the wrong value to the right key" (wrong-write). It **wrote both values to the same record, semantically opposite, with the override in the field the prompt template reads first**. The downstream canonicalizer is structurally unable to detect this — `with` and `replace` are both valid fields; the prompt template just happens to read `with` first.

**Diagnostic:** grep for `state_updates.*core_memories.*update` in story docs, then for each match, diff the `with` and `replace` fields. If they are semantically opposite (e.g. one says "is" and the other says "is not"), this sub-class hit.

**Same campaign as worked examples A and B** (Visenya v7) — campaign is now confirmed as a state-merge correctness repro cluster.

## vs god-mode directive violations (sister pattern)

The god-mode directive pattern (`references/god-mode-directive-enforcement.md`)
is about a user directive being **advisory-only** — directive exists in
`custom_campaign_state.god_mode_directives[]` and is injected into the system
prompt, but the LLM still narratively escalates past it.

The NPC-status persistence pattern is **structurally adjacent but orthogonal**:
no directive is involved. The bug is a *silent missing write* (or wrong
write), not an advisory violation. The existing canonicalizer fix in
[PR #8120 `fix(game_state): wire LLM state-update canonicalizer into update_state_with_changes`](https://github.com/$GITHUB_REPOSITORY/pull/8120)
does **not** fix any of the three sub-classes because there is nothing
to canonicalize — the field is absent or actively wrong, not misplaced.

## Worked example A — campaign `xK3fp5XrV24oarIINTF7`, scenes 50/73 (2026-07-08)

### Capture event (scene 50, 01:31:44 UTC)

LLM streamed the narrative:
> *"There, wedged between two jagged ribs of stone, you found him. The Prince
> of the Greens lies broken, his silver hair matted with salt and blood, still
> tangled in the wreckage of his saddle. He is alive, but barely."*

Perception check passed: `1d20+6 = 23` against DC 16. The narrative was
authoritative — Aemond was captured.

But the `state_updates` payload for that turn **never wrote**
`state_updates.npc_data["Prince Aemond Targaryen"].status = captured` (or
anywhere else). The merge in `update_state_with_changes` correctly did
nothing for Aemond's status because nothing was sent.

### Hallucination 14 turns later (turn 73, 04:08:32 UTC, dev revision `dacd5aa`)

The user returned many turns later and asked Cole about Aemond. The LLM
emitted:

> *"Where is the One-Eyed Prince? Vhagar is mine now—does Aemond fly Sunfyre,
> or has he crawled back to his mother's skirts?"*

and constructed a `social_hp_challenge` whose objective was literally
*"Reveal Aemond's flight-path"*. The LLM assumed Aemond was airborne
and at large.

The prompt that triggered this hallucination:
- `prompt_tokens=205,114`, `cached_tokens=98,159`, `cache_hit_rate=47.9%`
- `core_memories` injected at **47,958 tokens (20% of budget)** — large and
  present, but it's narrative prose, not structured `npc_state`
- No `npc_state` block anchored Aemond's current `status: ["captured","prisoner"]`
- The LLM re-derived Aemond's location from `entities_mentioned` and
  `planning_block` context in adjacent turns, and went with "Aemond is
  airborne" because no canonical anchor said otherwise

### The model diagnosed itself (turn 73 god-mode correction, 04:18:45 UTC)

After the user pushed back via `/god mode`:
> *"Prince Aemond Targaryen was captured on Day 43 and is currently a prisoner
> on Dragonstone. ... The previous turn's focus on 'Aemond's flight path' was
> a serious continuity hallucination where the model failed to reconcile the
> immediate scene with the established core memories of Aemond's neutralization."*

The fix it then injected (god-mode correction):
- `npc_data["Ser Criston Cole"].status = ["captured","bound","stripped","interrogated","defiant"]`
- 3 explicit `directives.add` rules forcing "Aemond is CAPTURED" into the prompt
- `core_memories.append` of a correction memory

So the model *knew* the canonical state was "captured" but its prompt had no
structured anchor to force it on the broken turn — only narrative-level
`core_memories`, which it could hallucinate around under plot pressure.

## Worked example B — campaign `xK3fp5XrV24oarIINTF7`, scene 149 "we share a father" (2026-07-08, 3 hours later)

This is a stronger, second instance of the bug class in the same campaign that
**also surfaces the wrong-write sub-class**: the LLM emits a *wrong* status
write (not just a missing one) when the narrative and the canonical state
disagree, and a prompt-anchor hallucination (the lineage bug).

### Scene-by-scene `state_updates.npc_data[Prince Aemond Targaryen]` table

This is the canonical diagnostic for the class. Build it as: for every story
doc in the campaign's `story` subcollection whose narrative mentions the
NPC, extract the `state_updates.npc_data[<NPC>]` write (if any). Sorted by
`user_scene_number`. One row per scene. Three sub-classes surface instantly.

| Scene | ts (UTC) | Narrative summary | `state_updates.npc_data[Prince Aemond]` write | Sub-class hit |
|---|---|---|---|---|
| 86 | 01:11:57 | Aemond falls from Vhagar into the Whispers — survives | `{"status": ["dead/missing","unseated"], "hp_current": 0}` | **WRONG-WRITE** (narrative says alive) |
| 89 | 01:18:37 | Search continues; Aemond not yet found | `{"status": ["dead/missing","unseated"], "hp_current": 0}` | **WRONG-WRITE** (reasserted) |
| 90 | 01:20:21 | Vhagar grounded, Aemond still missing | `{}` (no Aemond write) | MISSING-WRITE |
| 97 | 01:35:08 | "Aemond is unseated. Vhagar is grounded" — first capture confirmation | `{"current_location": "Dragonstone (The Dungeons)", "status": ["captured","imprisoned","stable"]}` | first **CORRECT** write (11 turns late) |
| 100 | 01:49:44 | Interrogation transition | `{}` (no npc_data write at all) | MISSING-WRITE |
| 134 | 04:18:47 | Prior god-mode correction (the scene-73 bug fixed via /god mode) | only `Ser Criston Cole` write — no Aemond | injected `core_memories` correction (bandaid) |
| 149 | 05:07:38 | **The bug scene** — Aemond in cell says *"a shadow of my father's lust"* | `{}` | **PROMPT-ANCHOR HALLUCINATION** (lineage) |
| 151 | 05:10:35 | Self-correction | `{}` | model admits bug, no state anchor added |

### The bug in scene 149 (5 minutes after the prior repro cluster)

Visenya (the player's PC, daughter of Daemon) interrogates Aemond in his
Dragonstone cell. The narrative places Aemond correctly in the dungeon — but
the LLM emits Aemond's line **"A shadow of my father's lust"**, which
incorrectly implies shared paternity with Visenya.

Canonical lore (and `core_memories[110]` correction memory from a prior turn):
- Visenya = daughter of Daemon
- Aemond = son of Viserys I
- Relationship: first cousins (Daemon and Viserys I were brothers)

The user's correct frustration (verbatim, from story doc `gJpujTkIyj0xKxRJB1jz`):
> *"Aemond and I don't share a father why keep getting it wrong?"*

### Scene 151 — the model's own self-admission (3 minutes later)

```text
Administrative Correction: Lineage and Paternity Clarification.

I have corrected the persistent error regarding Visenya and Aemond's
relationship. The previous narrative incorrectly implied they shared a
father. This has been retconned and anchored in the game state to
prevent recurrence.
```

`state_updates` for scene 151 only contains a `core_memories.append` of the
correction text — no structured `## Lineage` block, no `player_character_data.lineage`
write. Same bandaid pattern as scene 134: append to `core_memories` and pray
the next prompt picks it up under pressure.

### Canonical state observed in BOTH source and twin copy (byte-identical)

```
Prince Aemond Targaryen:
  status: ["captured","stable","imprisoned"]
  current_location: "Dragonstone (The Dungeons)"
  hp_current: 1, hp_max: 45

Aemond Targaryen (alt entry — conflicting):
  status: "Searching (Frustrated)"
```

The `Aemond Targaryen` (without "Prince") alt-entry was never cleaned up. It
is *itself* evidence the merge layer accepts fuzzy-key writes — yet another
distinct sub-bug orthogonal to this class but co-located in the same campaign.

### Why the lineage keeps hallucinating despite correction history

The `core_memories[97]` ("Aemond is already a prisoner") and `core_memories[110]`
("Visenya and Aemond do NOT share a father") corrections exist at the time of
scene 149. They are narrative prose injected into a 47k-token core_memories
block. Under the *pressure* of a high-roll Intimidation (22) + social skill
challenge scene with Aemond's "father's lust" framing in adjacent narrative,
the LLM re-derives shared paternity from `entities_mentioned` + adjacent
prose and writes the wrong line. The correction memory is **too soft** to
override the pressure.

This is the canonical anchor problem: the bug class is not "the LLM forgets"
— it's "the LLM has the right info but the prompt gives it no structured,
hard-to-overlook slot to anchor against."

### Repro sources-of-truth for worked example B

- GitHub issue [#8266](https://github.com/$GITHUB_REPOSITORY/issues/8266) — REPRO issue filed
- GitHub draft PR [#8267](https://github.com/$GITHUB_REPOSITORY/pull/8267) — evidence bundle in `repro_evidence/`
- Twin copy campaign id: `AKEhwjUSSKD9LvsjzUPS` (under `<your-email@gmail.com>`, UID `0wf6sCREyLcgynidU5LjyZEfm7D2`)
- Source campaign: `xK3fp5XrV24oarIINTF7` (under `$USER@gmail.com`, UID `vnLp2G3m21PJL6kxcuAqmWSOtm73`)

## Worked example C — campaign `RMCPAPdfuErh8MgRuj6n`, Jacaerys at Highgarden (2026-07-14)

This is a **different campaign** from xK3fp5XrV24oarIINTF7 (Visenya-v7) but the
**same bug class**. It surfaces two new sub-classes — **dual-entry canonical-state
conflict** (sub-class 5) and **narrative-inertia spatial hallucination** (sub-class 6) —
that the prior worked examples did not exercise. Verified 2026-07-14 against
[issue #8390](https://github.com/$GITHUB_REPOSITORY/issues/8390) /
[draft PR #8391](https://github.com/$GITHUB_REPOSITORY/pull/8391).

### The user's report (verbatim)

> *"Run /repro it makes no sense Jacaerys Velaryon would be in my location"*

URL: https://mvp-site-app-dev-i6xf2p72ka-uc.a.run.app/game/RMCPAPdfuErh8MgRuj6n

### Canonical state — the smoking gun (direct Firestore read on source + twin copy, byte-identical)

- **Player location**: `Guest Solar, Highgarden` (from `world_data.current_location_name` + `custom_campaign_state.last_location`)
- **Jacaerys canonical location**: `The Red Keep, King's Landing` (from `npc_data["Jacaerys Velaryon"].current_location`)
- **Distance**: ~600+ miles across Westeros; not a same-day travel route

Two distinct Jacaerys entries in `npc_data` (the dual-entry conflict):

```
Prince Jacaerys Velaryon (main entry, LLM-anchored):
  level: 11
  role: "Crown Prince / Legendary Commander"
  status: "Terminal Grief / Panic"
  attitude_to_party: "hostile"
  current_location: <MISSING — not present>

Jacaerys Velaryon (alt entry, location-anchored):
  status: "Active (Secretly Plotting Containment)"
  current_location: "The Red Keep, King's Landing"
```

The main entry has all the LLM-anchored fields (level/role/status/attitude) but **NO**
`current_location` field. The alt-entry has the `current_location`. **Sub-class 5
(dual-entry conflict) confirmed.**

### The offending sequence (story doc timestamps, all 2026-07-14 UTC)

| ts UTC | actor | doc_id | What happened | Sub-class hit |
|---|---|---|---|---|
| 05:08:57 | user | `FYMuyjfnipjz40ss1emt` | User input: *"Long rest and then reveal my divine origin to Dareon and ask if he wants to marry me"* | — (scene setup) |
| 05:12:35 | gemini | `gg8CSnuTxGds4CxcqY0b` | Narrative places Jacaerys in the Highgarden solar: *"In the shadows near the doorway, Prince JACAERYS Velaryon (Lvl 11) watches the exchange, his posture a rigid line of suppressed agony"* | **5** (dual-entry) + **6** (narrative-inertia) |
| 05:13:23 | user | `HUHotHlMJ1lVqWiuO1iR` | User challenge: *"Why is Jace here that makes no sense"* | — |
| 05:13:24 | gemini | `al5GipXPbsoe9bjcvF99` | God-mode audit **defends** the bug with 4 fabricated justifications: (1) "diplomatic circuit is complete" — claims Jace finished Stormlands/Vale tasks and "reconvened at Highgarden", (2) "mentorship protocol" — invokes god-mode Directives 92/108, (3) "jealousy/insecurity variables" — invokes Directives 99/104 "Terminal Attraction", (4) "timeline reconciliation" — claims Jace arrived via Vermax ~12h ago during long rest | **5** (model picks alt-entry without consulting canonical `current_location`) |
| 05:14:49 | user | `yUTFtyUsxLqz7PGj0yc4` | User pushback: *"Wait this makes no sense. His faction is hostile he wouldn't be randomly hanging around me anymore"* | — |
| 05:14:50 | gemini | `Z39CBCurWZ29QVldPKA5` | **Model self-admission** (Administrative Correction): *"You are correct. The previous narration of Prince Jacaerys's physical presence in the solar as a 'jealous observer' contradicts the active 'Council's Defensive Lockdown' (Directive 6) and 'Secret Hostility' (Directive 4) protocols."* + retcons Jacaerys back to Red Keep + adds new "Strategic Separation" god-mode directive | model-self-admission — proves the bug AND the prescribed fix shape |

### The model self-prescribes the fix (key insight)

In `Z39CBCurWZ29QVldPKA5`, the model injects a new god-mode directive:

> *"Added 'Strategic Separation': Hostile high-tier NPCs (Rhaenyra, Jacaerys, Corlys) will no longer 'hang around' Visenya in intimate or low-security settings. They will maintain a defensive distance, interacting only through formal council meetings, envoys, or kinetic strikes."*

This is the **model telling us the durable prompt fix**: add a rule that **hostile
high-tier NPCs must respect their canonical `current_location` and not intrude
into intimate / low-security scenes**. Note: this only fixes sub-class 6; sub-class 5
(dual-entry) needs a separate canonical-state cleanup, not a prompt change.

### Why PR #8352's Option D does NOT fix sub-classes 5 or 6

Option D's three clauses target sub-classes 1 (Missing-write), 2 (Wrong-write), and
3 (Prompt-anchor hallucination). They do not address:

- **Sub-class 5 (Dual-entry)**: needs a canonical-state cleanup — merge the two
  entries into one, ensure `current_location` is always present in the merged
  entry. Backend work in `world_logic.py` or a one-shot migration script.
- **Sub-class 6 (Narrative-inertia)**: needs a new prompt rule — the model's own
  "Strategic Separation" directive is the right shape, but it must live in
  `$PROJECT_ROOT/prompts/game_state_instruction.md` or a character-agent prompt, not
  in a god-mode directive (which is advisory and campaign-specific).

### Diagnostic for sub-class 5 (dual-entry) in a new repro

```python
# Direct Firestore read on game_states/current_state
import json
from google.cloud import firestore
db = firestore.Client(project="worldarchitecture-ai")
gs = db.collection("users").document(UID).collection("campaigns").document(CID) \
       .collection("game_states").document("current_state").get().to_dict()
npc_data = gs.get("npc_data") or {}

# Group entries by normalized name (lowercase, strip titles/prefixes)
import re
def normalize(k):
    return re.sub(r'^(prince|king|queen|lord|lady|ser|sir)\s+', '', str(k).lower()).strip()

from collections import defaultdict
groups = defaultdict(list)
for k in npc_data.keys():
    groups[normalize(k)].append(k)

# Flag any group with >1 entry where fields differ in presence of current_location
for norm, keys in groups.items():
    if len(keys) > 1:
        presence = {k: "current_location" in npc_data[k] for k in keys}
        if len(set(presence.values())) > 1:
            print(f"DUAL-ENTRY CONFLICT: {norm} -> {keys} -> current_location presence={presence}")
```

If the named NPC also appears in narrative at a location different from the entry
with `current_location`, **sub-class 6 is also live**.

### Repro sources-of-truth for worked example C

- GitHub issue [#8390](https://github.com/$GITHUB_REPOSITORY/issues/8390) — REPRO issue filed
- GitHub draft PR [#8391](https://github.com/$GITHUB_REPOSITORY/pull/8391) — evidence bundle in `repro_evidence/`
- Twin copy campaign id: `Jty8HMvjqQRt8s0l5FuH` (under `<your-email@gmail.com>`, UID `0wf6sCREyLcgynidU5LjyZEfm7D2`)
- Source campaign: `RMCPAPdfuErh8MgRuj6n` (under `$USER@gmail.com`, UID `vnLp2G3m21PJL6kxcuAqmWSOtm73`)

## Diagnostic: build the scene-by-scene table

```python
# Run from main checkout (NOT fresh worktree — see references/firestore-path-and-uid-resolution.md)
PY="$HOME/projects/your-project.com/venv/bin/python"
"$PY" - <<'PY'
import json
from google.cloud import firestore
db = firestore.Client(project="worldarchitecture-ai")
# Resolve UID via Firebase Auth, not Firestore field lookup (see references/...)
import subprocess
uid_json = subprocess.check_output([
    "$HOME/projects/your-project.com/venv/bin/python",
    "$HOME/projects/your-project.com/scripts/campaign_manager.py",
    "find-user", "$USER@gmail.com"
]).decode()
UID = uid_json.split("Firebase UID: ")[1].split("\n")[0].strip()
CID = "xK3fp5XrV24oarIINTF7"
story = list(db.collection("users").document(UID).collection("campaigns").document(CID)
             .collection("story").stream())
rows = []
for s in sorted(story, key=lambda d: d.to_dict().get("user_scene_number") or 0):
    sd = s.to_dict()
    narr = (sd.get("narrative") or "") + " " + (sd.get("text") or "")
    if "Aemond" not in narr: continue
    su = sd.get("state_updates") or {}
    nd = su.get("npc_data") or {}
    aemond_write = {k:v for k,v in nd.items() if "aemond" in str(k).lower()}
    rows.append({
        "scene": sd.get("user_scene_number"),
        "ts": str(sd.get("timestamp")),
        "actor": sd.get("actor"),
        "narrative_first_200": narr[:200],
        "aemond_state_updates": aemond_write or None,
    })
print(json.dumps(rows, indent=2, default=str))
PY
```

## How to identify this bug class in a new repro

### From GCP Cloud Run logs (the dev environment)

Filter on `campaign_id=<ID>` and look for the broken turn's
`GEMINI_STREAM_FULL_RESPONSE`. If the LLM's `narrative` describes a status
effect (capture, kill, alliance change, item transfer) but `state_updates` is
silent on it, you've found a narrative-only state change.

```bash
gcloud logging read \
  'resource.type=cloud_run_revision \
   AND resource.labels.service_name=mvp-site-app-dev \
   AND jsonPayload.campaign_id="<CAMPAIGN_ID>" \
   AND jsonPayload.message=~"GEMINI_STREAM_FULL_RESPONSE"' \
  --project=worldarchitecture-ai --limit=50 --format=json --freshness=14d \
  | jq -r '.[] | {ts: .timestamp,
                   rev: .resource.labels.revision_name,
                   cache: (.jsonPayload.message | capture("cache_hit_rate=(?<v>[0-9.]+)").v // "?"),
                   body: .jsonPayload.message}'
```

Then for each broken turn, look at the **capture event turn** (the earliest
turn where the NPC's status changed in narrative) and confirm whether
`state_updates.npc_data[NPC]` was written. If not — bug class confirmed.

### From Firestore directly

```python
from google.cloud import firestore
db = firestore.Client(project="worldarchitecture-ai")
state = db.collection("campaigns").document("<DOC_ID>").get().to_dict()["state"]
ccs = state.get("custom_campaign_state", {})
npc_data = state.get("npc_data") or {}
core_memories = ccs.get("core_memories", []) or []

# Does narrative say "X captured"?
narrative_says_captured = any("aemond" in str(m).lower()
                              and ("captured" in str(m).lower() or "broken" in str(m).lower())
                              for m in core_memories)

# Does canonical state say "X captured"?
state_says_captured = "Aemond" in npc_data and \
                      "captured" in str(npc_data["Aemond"]).lower()

print(f"narrative={narrative_says_captured}, state={state_says_captured}")
# narrative=True, state=False  → bug confirmed
```

## Why PR #8120 (canonicalizer fix) doesn't fix this

PR #8120 wires `_canonicalize_state_updates_in_place` so legacy flat fields
(e.g. `player_character_data.gold`) are promoted into authoritative schema
locations (`resources.gold`) **before** `update_state_with_changes` merges.
Fixes the *"gold written to wrong key, gets dropped"* sub-bug.

For the **missing-write** sub-class of NPC-status persistence, there's nothing
in `state_updates` at all — the canonicalizer has no input to promote. The
merge correctly does nothing because nothing was sent.

For the **wrong-write** sub-class (worked example B, scenes 86/89), the
canonicalizer promotes misplaced fields but does not validate semantic
correctness against narrative. A `status: ["dead/missing"]` write is in
the right schema location — canonicalizer sees no problem; the bug is the
wrong value, not the wrong key.

For the **prompt-anchor hallucination** sub-class (worked example B, scene
149), the bug is upstream of `state_updates` entirely — the LLM emitted the
wrong narrative line. No canonicalizer change touches that codepath.

The fix needs to live upstream of the canonicalizer, in `world_logic.py` /
agent prompt / response validator, specifically enforcing that **whenever
the narrative mentions a status transition for an NPC the model knows about,
`state_updates.npc_data` must include that NPC's new status (and that the
write's semantic content matches the narrative).**

## Fix shape (shipped in PR #8352, 2026-07-12)

**Option D — three-clause preamble in `$PROJECT_ROOT/prompts/game_state_instruction.md`**

The cheapest fix that addresses all four sub-classes at once is **not** any
single Option A / A' / B / C — it's a 3-clause prompt amendment landed in
[PR #8352](https://github.com/$GITHUB_REPOSITORY/pull/8352) on
2026-07-12, targeting campaign `xK3fp5XrV24oarIINTF7` scene 653 (the 7th
sibling instance). All three clauses live in the same prompt file
(`game_state_instruction.md` lines 2608-2640+):

1. **`## Canonical NPC Status (CANONICAL — must match this)`** — preamble
   block establishing `state.npc_data.<npc>.status / hp_current /
   current_location` as canonical truth. Render-side consistency with this
   block is mandatory. Addresses **all 4 sub-classes** as the anchor the LLM
   must reconcile against.

2. **`Narrative Revival of Canonical-Dead NPCs`** — forbids the LLM from
   narrating a canonical-dead NPC as acting / speaking / planning /
   traveling without an explicit resurrection write in the same turn.
   Allows "thoughts of X" / "spirit of X" references without a write.
   Same rule applies to captured / imprisoned NPCs ("word from the dungeon
   says..." is fine; speaking from a cell is not).
   Addresses scene 648 (queen narratively revived 4h after god-mode death).

3. **`Wrong-Key Death Writes`** — forbids `status: "__DELETE__"` as a
   death marker (it deletes the canonical entry entirely). Death must be
   written with `status = "dead"` + `hp_current = 0` against the
   **exact same NPC key** as the canonical `npc_data` entry.
   Addresses scene 628 (`__DELETE__` written to wrong key "Queen Rhaenyra"
   instead of "Queen Rhaenyra Targaryen").

Tests (6/6 green, `$PROJECT_ROOT/tests/test_npc_status_canonical_anchor.py`):
- 3 forward-tests for the new clauses
- 3 regression-tests verifying pre-existing `Non-Combat / Narrative Kill
  Propagation` (line 2622), `Non-Combat / Narrative Status Change
  Propagation` (capture/surrender/rescue), and `Stub-NPC Skepticism Rule`
  clauses are NOT regressed by the addition.

### Why prompt-only, not backend enforcement

Per `AGENTS.md` §"Root-cause-first prompt discipline": fix
prompt/schema contradictions first. Backend enforcement (Option A / A'
above — response validator in `world_logic.py`) is only justified after
prompt-only is proven insufficient. PR #8352 is the prompt-only attempt.
**If an 8th sibling instance surfaces after PR #8352 merges**, that is
the empirical signal to escalate to Option A as a narrow logged
invariant (per AGENTS.md — "Backend enforcement is allowed only as a
narrow, logged invariant after documenting why prompt/schema correction
alone is insufficient").

### Fix shapes NOT addressed by Option D (separate fix needed for each)

| Bug class | Why Option D doesn't fix it | Separate fix shape |
|---|---|---|
| Confused-state `with`/`replace` (#8283) | Bug is in `core_memories.update`, not `npc_data` | `## Lineage` / `## Parentage` structured blocks (per-narrative-anchor) |
| Stale-bundle (#8275 level downgrade) | Bundle-level caching, not prompt-level | Bundle TTL / cache invalidation at storage layer |
| Stale-context (#8293 hidden gold) | Bug is in `planning_block` re-emission, not `npc_data` | `## Inventory` / `## World Resources` structured blocks |
| Grant-not-operationalized (#8320 Conqueror's Spark) | Custom feature, not canonical field | Feature schema in agent_prompts + grant_validation hook |
| Dual-entry canonical-state conflict (#8390 sub-class 5) | Bug is `npc_data` having 2 entries for the same NPC; canonicalizer merges both, doesn't merge into one | Backend canonical-state cleanup — single entry per NPC, `current_location` always present in the merged entry (one-shot migration + write-time invariant) |
| Narrative-inertia spatial hallucination (#8390 sub-class 6) | Bug is LLM inserting NPC into active scene for dramatic reasons, ignoring `npc_data[NPC].current_location` | New prompt rule (model's own "Strategic Separation" prescription is the right shape): "Hostile high-tier NPCs must respect canonical `current_location` and not intrude into intimate / low-security scenes" — land in `game_state_instruction.md`, NOT as a god-mode directive (advisory + campaign-specific) |

When a sibling fix is needed for one of these, it belongs in a **separate
prompt file or structured block**, not piled onto Option D.

## Adjacent open work

- Issue [#7123](https://github.com/$GITHUB_REPOSITORY/issues/7123)
  — `Bug: LLM doesn't realize frenchie is already captured` (campaign
  `8YyNCrwi67Fszr7RGImN`). Same bug class, different NPC + different
  campaign. Confirms this is a recurring class, not a single campaign
  anomaly.
- Issue [#7885](https://github.com/$GITHUB_REPOSITORY/issues/7885)
  — REPRO issue filed against the same campaign
  `xK3fp5XrV24oarIINTF7` for a different state-merge bug (character-creation
  spell list), but co-located = strong signal this campaign is the
  repro cluster for state-merge correctness bugs.
- PR [#8120](https://github.com/$GITHUB_REPOSITORY/pull/8120)
  — canonicalizer fix; not green as of 2026-07-08 (Green Gate FAIL, 45min
  test). Fixes a sibling sub-bug (gold/money) but does NOT fix the
  narrative-only state change class.

## Campaign-cluster structural trigger (added 2026-07-12)

**When ≥3 sibling repro issues accumulate against the same `campaign_id`**
(sibling-issue scan via `gh issue list --search "<CID>" --state all`),
**stop treating new sibling instances as per-scene bugs**. The campaign
itself has a state-merge correctness problem at the prompt layer, and the
fix shape changes:

- **Per-scene mode (default, ≤2 siblings)**: file a fresh issue per
  symptom, twin-copy the campaign, run the scene-by-scene diagnostic
  per this reference, link the sibling in the issue body
- **Campaign-level mode (≥3 siblings, structural)**: STOP filing
  per-scene issues. Spend the next investigation cycle on a
  root-cause-first prompt fix that addresses the **common anchor
  layer** (Option D for NPC-status; analogous structured-block fix
  for other sub-classes). Branch a fresh worktree off `origin/main`
  for the fix PR — don't pile onto the repro branch.

**Sentinel example**: campaign `xK3fp5XrV24oarIINTF7` accumulated 7
sibling repros in 9 days (2026-07-07 → 2026-07-12) before PR #8352
shipped Option D. The 6th and 7th siblings (#8320, #8335) had
**non-overlapping sub-classes** — which is exactly what proves it's
prompt-layer, not per-scene. Continuing to file per-scene issues at
that point would have hidden the cluster, not surfaced it.

**Diagnostic for "is this a new sibling or a new bug?":**
```bash
gh issue list --repo $GITHUB_REPOSITORY --state all \
  --search "<CID>" --json number,title,labels | jq 'length'
# ≥3 → campaign-level mode; link sibling + branch fresh worktree
# ≤2 → per-scene mode; repro per this reference
```

**Campaign-cluster evidence templates** — every issue body and PR body
on a campaign in cluster mode must include:
- The list of all open + closed sibling issue numbers on the same CID
- The phrase "*(N)th instance on this campaign — likely same root
  cause class*" so the next triage agent sees the cluster, not a
  one-off
- A short note on which sub-class is being targeted (Missing-write /
  Wrong-write / Wrong-key / Prompt-anchor / Confused-state) so future
  agents can map new symptoms onto the taxonomy

## Sub-class 8 (NEW 2026-07-28) — Prose-only value-derivation drift (narrative free-recall, no state write)

**Signature (verified 2026-07-28, campaign `fZGt3Rhd243H8rr7itto` "Valeria iseki (wrong npc level)", scene 51, story doc `OWSPP4DNXtQ5ZWEpjv1Q`):**

LLM emits a wrong numeric value in **narrative parenthetical** (e.g.
`"Baronet Kaelen Harth (Lvl 8) is notably absent"`) AND does NOT write
`state_updates.npc_data[<NPC>].level` at all in that turn. The structured
field stays at the canonical value (in this case `npc_data.Baronet Kaelen
Harth.level = 3`), but the narrative prose is off-canon.

This is structurally distinct from sub-class 7 (state-update value-derivation
drift) in two ways:

| Sub-class | Narrative says | Field written? | Value correct? |
|---|---|---|---|
| 7 (state-write drift, #8528) | "applying the canonical (Level / 10) gear formula" | ✅ present | ❌ wrong numeric |
| **8 (prose-only drift, #fZGt3Rhd243H8rr7itto)** | "(Lvl 8)" parenthetical | ❌ absent | n/a (only prose is wrong) |

The LLM has BOTH the canonical state (`npc_data.<NPC>.level = 3`) AND the
canonical lore (core_memory: "Calibration: Academy peers are mostly Level
1-2, with elites at Level 3; Valeria's Level 6 status is a freakish anomaly")
inside the served prompt at byte offsets 116007 (14.7%) and 211907 (26.8%)
of an 790909-byte `request_json` for the StoryModeAgent turn at 2026-07-29T03:14:52Z.
It still emitted `Lvl 8` in prose — but never wrote `npc_data.Kaelen.level=8`.

**Distinctive fingerprint vs. other sub-classes:**
- `state_updates.npc_data` block is **absent** for the affected NPC (vs. sub-class 7 where it's present-and-wrong)
- `npc_data.<NPC>.level` in Firestore matches the canonical core_memory (vs. sub-classes 1-3 where it's missing/wrong)
- `core_memories` block at the scene has the canonical lore (vs. sub-class 3 prompt-anchor hallucination where the right info is in core_memories but the LLM overrides anyway)
- The drift is **purely in narrative**, AND the LLM chose the wrong number when there was a precise correct number already in BOTH structured state and prose lore

**Why a separate sub-class matters for the fix shape.** Sub-class 7's fix is
"mirror the value-derivation formula into the prompt pre-`state_updates`",
which has zero effect on prose-only drift. The fix for sub-class 8 must
target the render/narrative side: either (a) a prompt rule that says "before
writing `<NPC> (Lvl N)` in narrative, verify N matches `npc_data[<NPC>].level`",
or (b) the runtime injecting a deterministic parenthetical from
`npc_data[*].level` rather than trusting the LLM's free-recall. Component (b)
is the durable fix; (a) is the prompt-side hedge.

**Diagnostic recipe** (verified, 1-query per scene):

```sql
-- For each scene where the LLM mentions a level-bearing parenthetical near the NPC,
-- confirm whether npc_data[that NPC].level was written that turn.
SELECT agent, turn_index, ingested_at,
       LENGTH(CAST(request_json AS STRING)) AS req_bytes,
       REGEXP_INSTR(CAST(request_json AS STRING), r'<NPC Name>') AS npc_offset,
       REGEXP_INSTR(CAST(request_json AS STRING), r'Calibration') AS lore_offset,
       response_text
FROM `worldarchitecture-ai.llm_forensics.llm_payloads`
WHERE campaign_id = '<CID>'
  AND agent = 'StoryModeAgent'
  AND REGEXP_CONTAINS(CAST(response_text AS STRING), r'\(Lvl\s*\d+\)')
ORDER BY ingested_at DESC
LIMIT 10
```

If both `npc_offset` and `lore_offset` are under 30% of the served prompt,
the LLM had the canonical anchor; the bug is prose-only; the `state_updates`
payload for the turn confirms the field was absent.

**Cross-reference:** `references/state-update-value-derivation-drift.md`
covers the 7th sub-class (state-write drift). The 8th sub-class is its
narrative-side cousin — same LLM-source-of-truth failure, different
output channel.

**Sibling-instance tally (verifiable 2026-07-28)** — the 8th sub-class
on `fZGt3Rhd243H8rr7itto` is the first verified instance of prose-only
drift. The full sibling-instance tally (campaigns A + B) is below.

## Sibling-instance tally (verifiable 2026-07-28)

The repro cluster now spans **two campaigns**:

**Campaign A: `xK3fp5XrV24oarIINTF7`** (Visenya-v7) — the canonical cluster:

| # | Issue | Scene | NPC / object | Sub-class |
|---|---|---|---|---|
| 1 | [#7885](https://github.com/$GITHUB_REPOSITORY/issues/7885) | (character creation) | Spells / ability points | Missing-write (variant) |
| 2 | [#8012](https://github.com/$GITHUB_REPOSITORY/issues/8012) / [#8080](https://github.com/$GITHUB_REPOSITORY/issues/8080) / [#8103](https://github.com/$GITHUB_REPOSITORY/issues/8103) | (varied) | (player family) | Streaming-save-drop (god-mode directive variant) |
| 3 | [#8266](https://github.com/$GITHUB_REPOSITORY/issues/8266) | 50/73/86/89/97/100/149/151 | Prince Aemond | Missing-write + Prompt-anchor |
| 4 | [#8275](https://github.com/$GITHUB_REPOSITORY/issues/8275) | 107/123/136/137/142/156 | Queen Rhaenyra (level 14→10) | Stale-bundle |
| 5 | [#8283](https://github.com/$GITHUB_REPOSITORY/issues/8283) | 314/315 | Visenya (daughter of queen) | Confused-state (`with`/`replace`) |
| 6 | [#8293](https://github.com/$GITHUB_REPOSITORY/issues/8293) | 375 | Hidden gold | Stale-context |
| 7 | [#8320](https://github.com/$GITHUB_REPOSITORY/issues/8320) | (God-mode grant) | Conqueror's Spark mechanic | Grant-not-operationalized |
| 8 | [#8335](https://github.com/$GITHUB_REPOSITORY/issues/8335) | 628/648/652/653 | Queen Rhaenyra (death forgotten) | Wrong-write + Wrong-key + Missing-write |

**Campaign B: `RMCPAPdfuErh8MgRuj6n`** (Visenya V8 / Jace location) — second cluster, surfaces new sub-classes 5 + 6:

| # | Issue | Scene | NPC / object | Sub-class |
|---|---|---|---|---|
| 1 | [#8390](https://github.com/$GITHUB_REPOSITORY/issues/8390) | 05:12:35 UTC story doc `gg8CSnuTxGds4CxcqY0b` | Prince Jacaerys Velaryon at Highgarden | **Dual-entry conflict** + **Narrative-inertia spatial hallucination** |

The **non-overlapping sub-classes across campaigns A siblings 3–8 and campaign B sibling 1** are
the proof that the root cause is prompt-layer, not per-scene. Campaign B's
sub-classes 5 + 6 are NOT addressed by Option D; each requires its own
structured-block fix + canonical-state cleanup. A unified durable fix should
cover both campaigns.

PR #8352 closed campaign A sibling 8 only via Option D. Campaign B sibling 1
remains open with no fix candidate yet (as of 2026-07-14).

## Evidence template (paste into issue/PR body)

```markdown
## Bug class
NPC status persistence — narrative outcome emitted but `state_updates.npc_data`
write absent. Sentinel example: campaign `<ID>`, NPC `<NAME>`, capture event
turn N, hallucinated turn N+K.

## Captured LLM request from hallucinated turn (GCP `jsonPayload.message`)
- `prompt_tokens=...`, `cached_tokens=...`, `cache_hit_rate=...`
- `core_memories` injected at NN,NNN tokens (XX% of budget)
- Narrative emitted: "<quoted buggy narrative line>"
- `planning_block` had `social_hp_challenge.objective = "Reveal Aemond's flight-path"`

## Captured LLM response from the capture turn (turn N)
- Narrative said "<quoted capture line>" — capture was authoritative narrative
- `state_updates.npc_data[<NPC>]` was ABSENT (no canonical state write)

## Firestore state from campaign `<DOC_ID>` (read via Firestore client)
- `state.custom_campaign_state.core_memories[]`: contains narrative entry
  for capture (proves narrative was canonical)
- `state.npc_data[<NPC>]`: MISSING or `status` does not include `captured`

## Reproduction steps
1. Run repro per `references/evidence-extraction-patterns.md` (download
   campaign, dump state, search narrative).
2. Identify the earliest turn where the NPC's narrative status changed.
3. Confirm `state_updates.npc_data[NPC]` was NOT written that turn.
4. Identify a later turn (turn N+K) where the LLM reverses or ignores the
   status change.
5. Confirm the broken-turn prompt has `core_memories` populated but no
   structured `npc_state` for the NPC.

## Why PR #8120 doesn't fix this
PR #8120 wires `_canonicalize_state_updates_in_place` for legacy-flat-field
canonicalization (e.g. `player_character_data.gold → resources.gold`). The
NPC-status persistence bug is not a misplacement — it's a missing write.
There's nothing to canonicalize.

## Proposed fix (Option C, prompt hardening)
Add a `## Canonical NPC Status` block to the system prompt that mirrors
`state.npc_data` as structured `[{"name": ..., "status": [...]}]` lines.
This gives the LLM a structured anchor it cannot hallucinate past.
```
