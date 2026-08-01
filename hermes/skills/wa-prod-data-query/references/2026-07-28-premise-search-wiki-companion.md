---
title: "WA campaign premise search — wiki companion (2026-07-28)"
type: reference
date: 2026-07-28
author: hermes-agent
companion_to: wa-prod-data-query
cross_skill: memory-search
---

# Companion to `wa-prod-data-query`: premise-only search must hit the wiki too

## Why this reference exists

`wa-prod-data-query` is the canonical skill for reading Your Project live Firestore data at `users/{uid}/campaigns/{cid}/story/{entry_id}`. It is correct for **counting** campaigns and **walking** a known campaign. It is NOT sufficient for **finding a campaign by premise** because:

1. The LLM-rewritten `description` block paraphrases the premise; the user's own words only live in the **God Mode opening prompt** inside the full transcript.
2. The user's first turn is often classified as a `description` block, not as the premise — regex over the description blob may miss the trope entirely.
3. False-positive rate is high: any campaign that uses "reincarnated" or "daughter" as throwaway worldbuilding lore (e.g., Sylphina IS a seventh daughter in her new life; Caesarion "thinks he is the reincarnation of Horus") will match, but does not describe the user's premise.

## The dual-store data model

| Store | Path | Holds |
|---|---|---|
| Firestore (live) | `users/{uid}/campaigns/{campaign_id}/story/{entry_id}` | LLM-generated description blocks for first ~5 entries; premise paraphrased |
| Wiki raw transcripts | `~/llm_wiki/raw/campaigns/<campaign_id>/<Title>_<id>.md` / `.txt` / `_game_state.json` | Full session transcripts — premise in opening God Mode prompt + first 1-3 scenes |
| Wiki source summaries | `~/llm_wiki/wiki/sources/<slug>.md` | Curated one-paragraph summary per ingested campaign |
| Wiki catalog index | `~/llm_wiki/wiki/index.md` | One-line entry per campaign — fastest signal for "do we have anything on this trope?" |

## The companion recipe

When the user asks "find my WA campaign where [premise]" and the Firestore scan returns >0 matches but none describe the premise:

```bash
# 1. Wiki catalog index — fastest (curated one-liners)
grep -i -E "<user-trope-keywords>" ~/llm_wiki/wiki/index.md

# 2. Wiki source summaries — paraphrased premise per campaign
grep -lir -E "<user-trope-keywords>" ~/llm_wiki/wiki/sources/ 2>/dev/null

# 3. Wiki raw transcripts — full text (premise in opening God Mode prompt)
grep -lir -E "<user-trope-keywords>" ~/llm_wiki/raw/campaigns/ 2>/dev/null

# 4. Wiki concepts/entities — cross-refs (faction, character, setting pages)
grep -lir -E "<user-trope-keywords>" ~/llm_wiki/wiki/concepts/ ~/llm_wiki/wiki/entities/ 2>/dev/null
```

If the wiki grep surfaces a campaign ID, cross-reference back to Firestore to confirm it exists and pull live metadata (created_at, last_played, entry count):

```bash
cd ~/your-project.com
WORLDAI_DEV_MODE=true .venv/bin/python -c "
import os, sys, firebase_admin
from firebase_admin import credentials, firestore
if not firebase_admin._apps:
    firebase_admin.initialize_app(credentials.Certificate('$HOME/serviceAccountKey.json'))
db = firestore.client()
uid = 'vnLp2G3m21PJL6kxcuAqmWSOtm73'
cid = '<campaign_id>'
doc = db.collection('users').document(uid).collection('campaigns').document(cid).get()
print(doc.exists, doc.to_dict() if doc.exists else None)
"
```

## Decision rule

If Firestore returns >5 matches AND NONE describes the user's premise → switch to wiki fan-out immediately. Do not re-scan Firestore with broader keywords; the data is correct, your keyword set is wrong for that store.

## Keyword expansion matrix for premise tropes

When the user's description is vague ("demon lord reincarnation," "investigating daughter from past life"), use multiple keyword sets in parallel:

| User phrasing | Wiki keyword regex |
|---|---|
| "demon lord" / "demon king" | `demon[- ]?lord\|demon[- ]?king\|demonlord\|demonking` |
| "reincarnation" / "reborn" | `reincarnat\|reborn\|past[- ]life\|previous[- ]life\|isekai\|transmigrat\|woke up as` |
| "isekai" / "anime reborn" | `isekai\|anime[- ]?style[- ]?reborn\|reborn in a new world` |
| "daughter from past life" | `daughter.*past\|daughter.*previous\|child.*past\|your daughter survives\|my child.*past` |
| "investigate" + entity | `investigat\|discover\|uncover\|search\|detect\|trace` + target keyword |
| "past life memories" | `past[- ]life\|memories.*life\|remember.*life\|previous[- ]life` |

Run all keyword sets in a SINGLE grep with `|` alternation to avoid running the full scan twice.

## Worked example — 2026-07-28 finding Iseki v1

User said (turn 1): "Find the campaign where I was reincarnated and investigating my daughter from a past life."

Firestore scan over Jeffrey's 1,116 campaigns at `users/vnLp2G3m21PJL6kxcuAqmWSOtm73/campaigns/`:

- Regex: `reincarnat|reborn|past[- ]life|demon (lord|king)|daughter|child` over first 5 story entries' description blocks
- Result: 14 false-positive matches across 9 distinct titles
- Top scorer: `Aristocrat reborn V2` (Sylphina — reincarnated as the seventh daughter of a margrave, but premise is "magic researcher reborn in noble family," NOT "investigating daughter from past life")
- Other matches: Gaia Julia v3 (Caesarion "thinks he is the reincarnation of Horus" — throwaway), Alexiel/Larion (absorbs a demon king's heart — not reincarnation as one), Visenya v5/v6 (Targaryen daughter in diverging timeline, no reincarnation premise), Sariel-Alexiel (daughter-of-Alexiel, no reincarnation)

User said (turn 2): "I was a demon lord or demon king reincarnation I think the campaign might be in the LLM wiki."

Wiki fan-out:

```bash
grep -lir -E "reincarnat|reborn|iseki" ~/llm_wiki/wiki/ 2>/dev/null
# → $HOME/llm_wiki/wiki/sources/iseki-v1-dUfl4Adb.md (and ~25 other source files)
```

`iseki-v1-dUfl4Adb.md` source page first 100 lines: opening God Mode prompt is "I wanna play a character who's strong or special like one of those iseki reborn anime characters but not too OP. Can make me 16 and a level 6" followed by Scene 3 player input: "Let's make me a reincarnation of a great demon lord. However make me grey rather black and white evil morally. Let's assume I killed half the worlds population but I had a good reason and I was level 25 but a band of heroes finally defeated me but I only lost because my child's life was in danger during battle."

Confirmed match. Cross-referenced back to Firestore:

- Campaign ID: `dUfl4Adb3oH6foczNFSZ`
- Title: `Iseki v1`
- Created: 2026-06-19
- Last played: 2026-06-27
- 112 story entries
- Character: Renjiro, 16yo, Sorcerer (Sovereign Blade → Sovereign Apostle), House Vane (5th son), Kingdom of Solis (Forgotten Realms, 1492 DR)

The daughter from a past life is **Lysandra Vane** — set up in Scene 19 as a future antagonist, Level 20 Tier 4 threat. Her "current location remains hidden from your character for now."

## Anti-patterns to avoid

- **DO** start with wiki grep when user says "in the wiki" / "I think it's in the wiki."
- **DO** include `~/llm_wiki/raw/campaigns/` in the search path when premise-only Firestore search returns false positives.
- **DO** grep the user's opening God Mode prompt verbatim — that's where their words live.
- **DO NOT** retry Firestore with broader keywords when the Firestore-only result returned false positives; the data is right, your keyword set is wrong.
- **DO NOT** trust the LLM-rewritten description block as authoritative for the user's intent — it paraphrases.
- **DO NOT** declare "not found" without checking the wiki; many campaigns only exist as ingested transcripts, not in live Firestore.

## Test

If you find yourself running the Firestore-only premise scan more than 3 times in a row without success, run the wiki fan-out before the 4th attempt. Time saved: typical case is 30-90s of Firestore scans compressed into a 5-10s wiki grep.

## Cross-references

- `memory-search/SKILL.md` § "Pitfall — WorldArchitect campaign search by premise lives in TWO stores" — same pitfall documented from the memory-search side.
- `download-campaign/SKILL.md` — populates the wiki raw transcripts and source summaries that this reference relies on.
- `wiki/concepts/NocturneBg3*.md`, `wiki/entities/Malcanthet.md`, `wiki/entities/Nocticula.md` — examples of entity pages that contain demon-lord lore without being "demon lord reincarnation" campaigns.