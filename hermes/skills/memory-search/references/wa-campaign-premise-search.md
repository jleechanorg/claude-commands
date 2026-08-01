---
title: "WA campaign premise search — wiki companion (2026-07-28)"
type: reference
date: 2026-07-28
author: hermes-agent
companion_to: memory-search
cross_skill: wa-prod-data-query
---

# Companion to `memory-search`: WorldArchitect campaign premise search lives in TWO stores

## Why this reference exists

`memory-search` already covers the 9-store fan-out (including `~/llm_wiki/` as source #7). The wiki store works fine for general premise text. The gap is that the WA premise-search workflow is **not a single-store search** — it spans Firestore (live data) AND the LLM wiki (ingested snapshots), and the user's words live in the wiki transcripts' opening God Mode prompt, NOT in the Firestore description block. Without the wiki step, premise-only queries hit a 14-match false-positive rate and require a second user turn to recover.

## The dual-store data model

| Store | Path | Holds |
|---|---|---|
| Firestore (live) | `users/{uid}/campaigns/{campaign_id}/story/{entry_id}` | LLM-generated description blocks for first ~5 entries; premise paraphrased |
| Wiki raw transcripts | `~/llm_wiki/raw/campaigns/<campaign_id>/<Title>_<id>.md` / `.txt` / `_game_state.json` | Full session transcripts — premise in opening God Mode prompt + first 1-3 scenes |
| Wiki source summaries | `~/llm_wiki/wiki/sources/<slug>.md` | Curated one-paragraph summary per ingested campaign |
| Wiki catalog index | `~/llm_wiki/wiki/index.md` | One-line entry per campaign — fastest signal |

## The companion recipe

When `memory-search` fan-out turns up Firestore matches but none describe the user's premise, AND the user hints "the wiki" / "I think the campaign might be in the LLM wiki":

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

If the wiki grep surfaces a campaign ID, cross-reference back to Firestore (use `wa-prod-data-query` skill, or call `firestore.client()` directly) to confirm it exists and pull live metadata.

## Keyword expansion matrix

Run multiple keyword sets in a SINGLE grep with `|` alternation:

| User phrasing | Wiki keyword regex |
|---|---|
| "demon lord" / "demon king" | `demon[- ]?lord\|demon[- ]?king\|demonlord\|demonking` |
| "reincarnation" / "reborn" | `reincarnat\|reborn\|past[- ]life\|previous[- ]life\|isekai\|transmigrat\|woke up as` |
| "isekai" / "anime reborn" | `isekai\|anime[- ]?style[- ]?reborn\|reborn in a new world` |
| "daughter from past life" | `daughter.*past\|daughter.*previous\|child.*past\|your daughter survives\|my child.*past` |
| "investigate" + entity | `investigat\|discover\|uncover\|search\|detect\|trace` + target keyword |
| "past life memories" | `past[- ]life\|memories.*life\|remember.*life\|previous[- ]life` |

## Worked example — 2026-07-28 finding Iseki v1

User said (turn 1): "Find the campaign where I was reincarnated and investigating my daughter from a past life."

Firestore-only scan via `wa-prod-data-query` skill (over 1,116 campaigns at `users/vnLp2G3m21PJL6kxcuAqmWSOtm73/campaigns/`): 14 false-positive matches across 9 distinct titles. Top scorer: `Aristocrat reborn V2` (Sylphina — reincarnated as the seventh daughter of a margrave, but premise is "magic researcher reborn in noble family," NOT "investigating daughter from past life"). Other matches: Gaia Julia v3 (Caesarion "thinks he is the reincarnation of Horus"), Alexiel/Larion (absorbs a demon king's heart), Visenya v5/v6, Sariel-Alexiel — none actually describe the user's premise.

User said (turn 2): "I was a demon lord or demon king reincarnation I think the campaign might be in the LLM wiki."

Wiki fan-out:

```bash
grep -lir -E "reincarnat|reborn|iseki" ~/llm_wiki/wiki/ 2>/dev/null
# → $HOME/llm_wiki/wiki/sources/iseki-v1-dUfl4Adb.md
```

`iseki-v1-dUfl4Adb.md` source page opening: God Mode prompt is "I wanna play a character who's strong or special like one of those iseki reborn anime characters but not too OP. Can make me 16 and a level 6" followed by Scene 3 player input: "Let's make me a reincarnation of a great demon lord. However make me grey rather black and white evil morally. Let's assume I killed half the worlds population but I had a good reason and I was level 25 but a band of heroes finally defeated me but I only lost because my child's life was in danger during battle."

Confirmed match. Cross-referenced back to Firestore:

- Campaign ID: `dUfl4Adb3oH6foczNFSZ`
- Title: `Iseki v1`
- Created: 2026-06-19, last played 2026-06-27, 112 story entries
- Character: Renjiro, 16yo, Sorcerer (Sovereign Blade → Sovereign Apostle), House Vane (5th son), Kingdom of Solis (Forgotten Realms, 1492 DR)
- Daughter from past life: **Lysandra Vane**, set up in Scene 19 as a future antagonist, Level 20 Tier 4 threat. "Current location remains hidden from your character for now."

## Decision rule

When `memory-search` fan-out (or any Firestore-only search) returns >5 matches AND NONE describes the user's premise, AND the user mentions the wiki, switch to wiki fan-out immediately. Do not re-scan Firestore with broader keywords; the data is correct, your keyword set is wrong for that store.

## Anti-patterns

- **DO** include `~/llm_wiki/raw/campaigns/` in the search path when premise-only Firestore search returns false positives.
- **DO** grep the user's opening God Mode prompt verbatim — that's where their words live.
- **DO** run multiple keyword sets in a single grep with `|` alternation to avoid running the full scan twice.
- **DO NOT** trust the LLM-rewritten description block as authoritative for the user's intent — it paraphrases.
- **DO NOT** declare "not found" without checking the wiki; many campaigns only exist as ingested transcripts, not in live Firestore.

## Cross-references

- `memory-search/SKILL.md` § "Pitfall — WorldArchitect campaign search by premise lives in TWO stores" — same pitfall documented inline.
- `wa-prod-data-query/references/2026-07-28-premise-search-wiki-companion.md` — same reference from the Firestore-side umbrella.
- `download-campaign/SKILL.md` — populates the wiki raw transcripts and source summaries that this reference relies on.