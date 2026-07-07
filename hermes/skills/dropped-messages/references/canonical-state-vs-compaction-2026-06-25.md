# Canonical state vs compaction — when "the LLM is aware of X" is NOT a bug

**Class:** your-project.com `/repro` diagnosis
**Date:** 2026-06-25
**Incident thread:** `C0AH3RY3DK6/1782032160.683689` (sibling message `1782033618.587949`)
**Campaign:** `btF3Nu4mqQRTVLG6F7tu` (owner `vnLp2G3m21PJL6kxcuAqmWSOtm73` = `$USER@gmail.com`)

## The user's claim (verbatim)

> "Read the latest responses from the LLM here it seems to be aware of the first horgus event so pretty sure you are wrong that it's due to compaction"

## Why this is correct and the prior diagnosis (2026-06-21) was wrong

The 2026-06-21 prior agent conflated two distinct bugs and labelled both as "compaction":

1. **Lifecycle staleness** (REAL bug, fixed): stale `horgus_scornubel_approach` background events surviving past `STALE_EVENT_TURN_THRESHOLD = 80`. Fixed by PRs #7766, #7774, #7790, #7800, #7822. This was a Firestore lifecycle-ownership bug, not a compaction bug.
2. **Awareness of the first Horgus event** (NOT a bug): canonical persistence in `custom_campaign_state.core_memories[]`. Sent in full every turn.

The user is asserting #2 is canonical state, and they are right.

## Evidence pulled directly from Firestore (dev env, 2026-06-25)

```
custom_campaign_state.core_memories: 246 entries
  → 34 mention Horgus or Hellrider (13.8%)
  → Entries [14]-[20] are the very first Horgus arc (Elturgard roadside intercept)
  → idx=31, 2026-06-15 19:55:30 was the LLM's first intro of Horgus in narrative

Story subcollection: 875 entries
  → 134 mention Horgus or Hellrider (15.3%)
  → First mention idx=31, latest mention idx=792 (2026-06-23 07:04:29)
  → Last 5 entries (June 24 Level 100 Crimson Vortex) have ZERO Horgus
    → LLM correctly drops it when contextually irrelevant

world_events.background_events: 14 entries
  → NO horgus_scornubel_approach — the lifecycle fix from #7766 worked
  → this is independent evidence that #2 was never a lifecycle-staleness bug

current planning_block: "Post-ascension inspection of the Faerûn substrate"
  → no Horgus mention — also not a planning_block leak
```

## Why "compaction" is the wrong default

Compaction would mean: the LLM has a compressed summary artifact from a prior session, and is using that to recall a past entity. This implies:

1. The entity is NOT in canonical state
2. The recall is fuzzy / gestalt
3. The artifact persists across session boundaries

In `btF3Nu4mqQRTVLG6F7tu`, none of those are true:

1. ✅ Horgus IS in canonical state — 34 mentions across `core_memories[]`
2. ❌ Recall is not fuzzy — 134 specific contextual references, often with full name + level ("Sergeant Horgus (Lvl 5)")
3. ✅ The persistence is via Firestore state continuity, not across-session artifacts

Compaction would predict recall *despite* canonical state being absent. Here recall happens *because* canonical state is present. The two are opposite diagnoses.

## Diagnostic recipe (use this BEFORE saying "compaction")

```python
# Inline, never subprocess. Worldarchitect.ai Firestore pull.
import os, sys
sys.path.insert(0, '/path/your-project.com/mvp_site')
sys.path.insert(0, '/path/your-project.com')
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.expanduser('~/serviceAccountKey.json')
os.environ['WORLDAI_DEV_MODE'] = 'true'
from clock_skew_credentials import apply_clock_skew_patch
apply_clock_skew_patch()
import firebase_admin
from firebase_admin import credentials, firestore
if not firebase_admin._apps:
    firebase_admin.initialize_app(credentials.Certificate(os.path.expanduser('~/serviceAccountKey.json')))
db = firestore.client()

# 1. Pull game_state
gs = db.collection('users').document(<uid>).collection('campaigns').document(<cid>).collection('game_states').document('current_state').get()
gsd = gs.to_dict()

# 2. Check core_memories
cms = gsd.get('custom_campaign_state', {}).get('core_memories', [])
entity_count = sum(1 for m in cms if '<entity_name>'.lower() in str(m).lower())
print(f'core_memories: {len(cms)} total, {entity_count} mention <entity_name>')

# 3. Check world_events.background_events
bge = gsd.get('world_events', {}).get('background_events', [])
entity_bge = [e for e in bge if '<entity_name>'.lower() in str(e).lower()]
print(f'background_events: {len(bge)} total, {len(entity_bge)} mention <entity_name>')

# 4. Check planning_block
pb = gsd.get('planning_block', {})
pb_str = str(pb).lower()
print(f'planning_block mentions <entity_name>: {"<entity_name>" in pb_str}')

# 5. If entity_count > 0 in core_memories: NOT compaction.
#    If entity_count == 0 AND bge empty: maybe compaction (rare).
#    If entity_count == 0 AND bge non-empty: lifecycle staleness (the OTHER bug).
```

## Redrive reply shape (when this comes back as a dropped-thread followup)

When a user says "you're wrong about compaction," the reply must:

1. **Acknowledge the misdiagnosis explicitly** — do NOT defend the prior "compaction" framing
2. **Show the canonical-state evidence** — `core_memories` count + `world_events` state
3. **Distinguish from the lifecycle-staleness bug** — those WERE real and are fixed by #7766+; don't fold them into the "compaction" frame either
4. **Offer 2-4 next steps** — none of them are "fix compaction"; they're either: no-action-needed (ack + memory note), regression test for `core_memory` continuity, or audit the prior diagnosis chain

See `references/2026-06-21-redrive-reply-mcp-mail-bot.md` for the 3-article recipe (identity = MCP mail bot, ack-log entry, skill gotcha patch). This reference is the third article (skill gotcha patch) for the 2026-06-25 incident.

## Token math (why compaction is implausible here)

246 `core_memories` × ~150 tokens avg = ~37k tokens. Inside the 72k LLM context budget with room to spare. There is no compaction-driven summarization happening — the FULL `core_memories[]` list is in the prompt verbatim every turn. Verified by `core-memories-coherence-check.md` reference in `download-campaign` skill (BQL query against `llm_forensics.llm_payloads` for the `CORE MEMORY LOG` block).

If `core_memories` size ever exceeds the budget, THEN compaction becomes a real candidate. For typical 246-entry campaigns, it is not.