---
name: wa-campaign-premise-find
version: 1.0.0
description: |
  Find a specific Your Project campaign by premise — the trope/story the user remembers
  ("female resurrected OP person", "demon lord reincarnation", "where I was a swords bard in Thay", etc.).
  Searches BOTH Firestore (live data, paraphrased descriptions) AND the LLM wiki raw transcripts
  (full God Mode prompts + first scenes — where the user's own words actually live).
  Returns campaign_id + title + character + Firestore URL + verbatim God Mode excerpt.
when_to_use: |
  Use when the user says: "find the campaign where I was [X]", "which campaign had [trope]",
  "I want to revisit the [character type] campaign", "find my [isekai/reincarnation/OP] campaign",
  "show me campaigns with [premise]", "do I have a campaign where [premise]". Also fires for
  "I think the campaign might be in the LLM wiki" (the dual-store decision rule).
allowed-tools:
  - terminal
  - file
  - memory
context: inline
---

# wa-campaign-premise-find — premise-driven WA campaign lookup

## The dual-store problem (this is the whole reason this skill exists)

WA campaign premises are duplicated across **Firestore** AND the **LLM wiki**, but they live in
DIFFERENT forms:

| Store | Path | What you find |
|---|---|---|
| Firestore | `users/{uid}/campaigns/{cid}/story/{entry_id}` | LLM-rewritten description blocks for first ~5 scenes — premise PARAPHRASED |
| Wiki raw transcripts | `~/llm_wiki/raw/campaigns/<cid>/<Title>_<cid>.md` / `.txt` | Full God Mode prompt + first scenes — user's ACTUAL words |
| Wiki source summaries | `~/llm_wiki/wiki/sources/<slug>.md` | Curated one-paragraph summary per ingested campaign |
| Wiki catalog index | `~/llm_wiki/wiki/index.md` | One-line entry per campaign — fastest signal |

**Firestore alone returns 14+ false positives for vague premises** (every campaign has "reincarnation"
or "demon" in its LLM-generated description even when that's not the user's premise).
**The wiki transcripts are where the user's own words live** — the God Mode prompt and Scene 1-3 player
input are unedited.

## Phases — 5 phases total, run in sequence

### Phase 1 — Confirm environment (one-time, ~10 sec)

```bash
ls -1 ~/serviceAccountKey.json \
  && python3 -c "import firebase_admin; print('firestore ok')" \
  && ls -1d ~/llm_wiki/raw/campaigns/ 2>/dev/null | head -1
```

If `serviceAccountKey.json` missing → fall back to wiki-only mode (Phases 3-4 only).

### Phase 2 — Firestore scan (parallel with Phase 3)

```python
import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate(os.path.expanduser("~/serviceAccountKey.json"))
firebase_admin.initialize_app(cred)
db = firestore.client()

UID = "vnLp2G3m21PJL6kxcuAqmWSOtm73"  # $USER's UID; verified 2026-07-28

# Scan all campaigns
camp_list = list(db.collection("users").document(UID).collection("campaigns").stream())

# For each, fetch the description block from the first 5 story entries
for c in camp_list:
    cid = c.id
    cd = c.to_dict() or {}
    title = cd.get("title") or cd.get("name") or "Untitled"
    # Get first 5 story entries — these have the LLM-generated description
    story = (db.collection("users").document(UID)
             .collection("campaigns").document(cid)
             .collection("story")
             .order_by("timestamp")
             .limit(5).stream())
    text = " ".join((s.to_dict() or {}).get("text", "") for s in story)
    # Score against user keywords (simple TF-IDF or keyword overlap)
```

**CRITICAL**: Firestore description blocks are LLM-generated paraphrases. Don't trust them as
authoritative — use Phase 3 wiki transcripts as ground truth.

### Phase 3 — Wiki fan-out (the actual ground truth)

```bash
# 1. Catalog index — fastest, curated one-liners
grep -i -E "<user-trope-keywords>" ~/llm_wiki/wiki/index.md

# 2. Source summaries — paraphrased by the ingest pipeline
grep -lir -E "<user-trope-keywords>" ~/llm_wiki/wiki/sources/

# 3. RAW TRANSCRIPTS — God Mode prompt lives here, user's own words
grep -lir -E "<user-trope-keywords>" ~/llm_wiki/raw/campaigns/

# 4. Concepts + entities — cross-references
grep -lir -E "<user-trope-keywords>" ~/llm_wiki/wiki/concepts/ ~/llm_wiki/wiki/entities/
```

**Keyword expansion matrix** (run multiple sets in ONE grep with `|` alternation):

| User phrasing | Wiki regex |
|---|---|
| "demon lord" / "demon king" | `demon[- ]?lord\|demon[- ]?king\|demonlord\|overlord\|dark lord` |
| "reincarnation" / "reborn" | `reincarnat\|reborn\|past[- ]life\|previous[- ]life\|isekai` |
| "isekai" / "anime reborn" | `isekai\|anime[- ]?style[- ]?reborn\|reborn in a new world` |
| "OP" / "overpowered" | `\bOP\b\|over.?powered\|god.?tier\|level\s*[2-9]\d+\|broken build\|godlike` |
| "resurrected" / "back from dead" | `resurrect\|return(ed)? from (the )?dead\|back from the dead\|raised (from the dead\|back)` |
| "female PC" / "make me female" | `(make me\|i am\|let's make me).{0,30}(female\|woman\|girl\|lady\|witch\|sorceress\|goddess\|succubus\|demoness\|queen\|empress\|princess)` |
| "daughter from past life" | `daughter.*past\|child.*past\|your daughter survives\|my child.*past\|my daughter.*previous life` |

### Phase 4 — Hand-classify candidates (read God Mode openings)

For each top-N wiki match, read the FIRST 4000 chars of the .md or .txt file (God Mode block +
Scene 1 + part of Scene 2). Look for the user's SPECIFIC premise phrases verbatim. Rank by
**how closely the literal text matches what the user described**, not by frequency of trope words.

### Phase 5 — Cross-reference back to Firestore (confirmation + URL)

For each wiki-confirmed match, fetch the Firestore doc to confirm it exists and grab the live
campaign title + character name + entry count + last-played date.

**Firestore URL pattern:**
```
https://console.firebase.google.com/project/worldarchitecture-ai/firestore/data/users/{UID}/campaigns/{cid}
```

## Output format

```
## Confirmed matches

### [title] — campaign_id=[cid]
- **Premise (God Mode verbatim):** "[first 300 chars]"
- **Character:** [name], [age], [class], [level start]
- **Setting:** [setting text]
- **Firestore URL:** https://console.firebase.google.com/project/worldarchitecture-ai/firestore/data/users/{UID}/campaigns/{cid}
- **Entries:** [N]
- **Match confidence:** [STRONG | PARTIAL | SPECULATIVE]

### [title] — campaign_id=[cid]
... (repeat)

## Disqualified candidates (looked promising, but God Mode didn't actually describe user's premise)

- **Aristocrat reborn V2** (cid=B1KlCh8DtmgcCqvp1nOs) — "Sylphina reincarnated as 7th daughter of a margrave"
  ≠ user's "demon lord reincarnation + investigating daughter from past life"
```

## Contract

When this skill is invoked, the agent MUST:

1. **Run BOTH Phase 2 (Firestore) AND Phase 3 (wiki fan-out)** for any premise query with 2+ signal words. Do NOT trust Firestore alone — it returns 14+ false positives.
2. **Hand-classify candidates** by reading the first 4000 chars of each wiki match's primary file (God Mode prompt + Scene 1). Do NOT just count keyword frequency.
3. **Output format**: each match MUST have campaign_id, title, character, Firestore URL, and a verbatim God Mode excerpt (≥200 chars). The URL MUST be the clickable Firestore URL, never bare `#123` or `cid=...`.
4. **Honest gap reporting**: if NO campaign matches all stated signals exactly, say so explicitly and list the partial matches. Do NOT fabricate a "resurrected" angle that isn't there.
5. **De-duplicate by campaign_id**, not by title (Aizen, Nocturne, Nocturna each have 5-20 variants).

## Output Format

A successful `wa-campaign-premise-find` invocation produces this shape:

```json
{
  "user_query": "<the user's premise text>",
  "uid": "vnLp2G3m21PJL6kxcuAqmWSOtm73",
  "matches": [
    {
      "campaign_id": "dUfl4Adb3oH6foczNFSZ",
      "title": "Iseki v1",
      "character": "Renjiro (16yo Sorcerer, House Vane 5th son)",
      "setting": "Kingdom of Solis (Forgotten Realms, 1492 DR)",
      "firestore_url": "https://console.firebase.google.com/project/worldarchitecture-ai/firestore/data/users/vnLp2G3m21PJL6kxcuAqmWSOtm73/campaigns/dUfl4Adb3oH6foczNFSZ",
      "wiki_path": "~/llm_wiki/raw/campaigns/dUfl4Adb3oH6foczNFSZ/Iseki v1_dUfl4Adb.txt",
      "entries": 112,
      "last_played": "2026-06-27",
      "god_mode_excerpt": "Let's make me a reincarnation of a great demon lord...",
      "match_confidence": "STRONG",
      "trope_signals": {
        "demon_lord": true,
        "reincarnation": true,
        "overpowered": true,
        "daughter_past": true
      }
    }
  ],
  "disqualified_candidates": [
    {
      "campaign_id": "B1KlCh8DtmgcCqvp1nOs",
      "title": "Aristocrat reborn V2",
      "reason": "Sylphina reincarnated as 7th daughter of a margrave, but premise is 'magic researcher reborn in noble family' ≠ 'investigating daughter from past life'"
    }
  ],
  "gap_note": "If matches==0: explicit 'No exact match found' + closest partial matches."
}
```

When posting in Slack, render the matches as a markdown table with columns
[Campaign] | [CID] | [Character] | [Entries] | [Confidence] | [Firestore URL].
The URL MUST be a clickable `https://...` — never bare `#123` or `cid=...`.

## Pitfalls (read these before running — most match the user's intent vs not)

1. **The user's words live in wiki transcripts, NOT Firestore descriptions.** Firestore description
   blocks are LLM-rewritten paraphrases. Always read the raw God Mode prompt as ground truth.
2. **Female-PC disambiguation**: many BG3-derived campaigns use female PC names (Shadowheart,
   Nocturne, Luna, Aizen — yes, Aizen Sosuke is rendered female in user's WA playthroughs, despite
   Bleach canon) but the original is male. Always check `Character:` field AND look for
   `she/her/female` markers in the description — do NOT assume gender from the character name.
3. **Resurrected NPC ≠ resurrected PC.** In "Luna post bg3" the player character Luna is female,
   but "Shadowheart (Resurrected)" is an NPC companion — NOT a match for "I am a resurrected..."
4. **Re:Zero "Return by Death" = reincarnation loop.** The PC doesn't literally die and come
   back; they loop on death. Counts as "reincarnation" trope but not "resurrected" — be precise.
5. **"Female resurrected OP" is rare.** Of 230+ campaigns, ZERO match all three exactly. Most
   match female + OP only. Report this honestly — don't invent a "resurrected" angle that isn't
   there. If the user asked for all three and we can't find any, the most likely answer is
   "No exact match — closest candidates are female + OP only, here's the inventory".
6. **Re-running with different tropes requires re-running ALL phases.** Don't cache prior
   results across tropes; the keyword sets are different.
7. **Per-campaign de-duplication**: Aizen, Nocturne, Nocturna, Saita each have 5-20 campaign
   variants (versions, copies, repro tests). Always present the canonical/original first.
8. **Aizen Sosuke in WA = female PC.** User's Aizen Sosuke campaigns are all rendered female
   despite Bleach canon being male. Don't apply canon lore to WA playthroughs.

## Tests

- `tests/test_dual_store_decision_rule.py` — verify "wiki hint" triggers Phase 3 wiki fan-out
- `tests/test_keyword_expansion_matrix.py` — verify each user phrase maps to a working regex
- `tests/test_female_pc_disambiguation.py` — Aizen/NocSosuke must be classified female (WA canon)
  even though Bleach/BG3 canon say male
- `tests/test_resurrected_npc_vs_pc.py` — Luna post bg3 must NOT match "I am resurrected" (the
  resurrected character is Shadowheart NPC, not Luna PC)
- `tests/test_god_mode_is_ground_truth.py` — read raw .md file's God Mode block; verify text
  matches user's premise word-for-word

## Cross-references

- `memory-search/SKILL.md` § "Pitfall — WorldArchitect campaign search by premise lives in TWO stores"
- `memory-search/references/wa-campaign-premise-search.md` — same pitfall, prior worked example (Iseki v1)
- `download-campaign/SKILL.md` — populates the wiki raw transcripts and source summaries
- `wa-campaign-content-analysis/SKILL.md` — analyzes content within a single campaign (Phase 1+
  uses this skill's candidate list)
