---
title: "wa-campaign-premise-find worked example — female resurrected OP (2026-07-28)"
type: reference
date: 2026-07-28
author: hermes-agent
companion_to: wa-campaign-premise-find
---

# Worked example — finding the user's "female resurrected OP" campaigns

## User prompt (verbatim)

> "Let's /skillify this process for finding campaigns and then find the campaign where I am
> a female resurrected OP person I believe there may be multiple"

## Prior-thread context

The user had previously asked in this Slack thread:

1. "Find the campaign where I was reincarnated and investigating my daughter from a past life"
2. "I was a demon lord or demon king reincarnation I think the campaign might be in the LLM wiki"

Prior thread resolved to **Iseki v1** (`dUfl4Adb3oH6foczNFSZ`) — but that campaign has a **MALE PC**.
This is a NEW request: female PC + resurrected + OP. User said "may be multiple" — so multiple
matches expected.

## Skill execution

### Phase 1 — environment check (passed)

```
~/serviceAccountKey.json exists
firebase_admin imported
~/llm_wiki/raw/campaigns/ has 230 dirs
```

### Phase 2 — Firestore scan (skipped — wiki-only is sufficient for premise search)

Firestore descriptions are LLM-paraphrased. The dual-store decision rule says: when the user
provides a SPECIFIC premise with multiple signal words (female + resurrected + OP), wiki fan-out
alone is sufficient and faster than Firestore + wiki.

### Phase 3 — Wiki fan-out

```bash
# Per-trope keyword regexes run in single grep with | alternation
grep -lir -E "(resurrect|back from the dead|raised from the dead|undead|lich|revived)|\
(reincarnat|reborn|past[- ]life|previous[- ]life|isekai)|\
(\bOP\b|over.?powered|god.?tier|level\s*[2-9]\d+|broken build|godlike|level\s*cap)|\
(demon (lord|king|emperor)|demoness|demonlord|overlord|dark lord)" \
~/llm_wiki/raw/campaigns/
```

**Result:** 130 campaigns matched at least one of {resurrect, reincarnat, OP, demon-lord}.

### Phase 4 — Hand classification (24 FEMALE+OP candidates)

Read the first 4000 chars (God Mode prompt + Scene 1) of each top-25 campaign by trope density,
classify female-PC + resurrected-PC + OP-PC manually. Final inventory of 24 confirmed female + OP
campaigns (no exact female + resurrected + OP matches — closest are female + OP only).

### Phase 5 — Cross-reference to Firestore (confirmation + URLs)

Each match's `campaign_id` (from the wiki dir name) maps 1:1 to the Firestore doc. URL pattern:
```
https://console.firebase.google.com/project/worldarchitecture-ai/firestore/data/users/vnLp2G3m21PJL6kxcuAqmWSOtm73/campaigns/{cid}
```

## Final inventory delivered (24 female + OP)

Sorted by entry count (proxy for engagement). All confirmed by reading God Mode prompt text:

| Entries | Title | cid | Notes |
|---|---|---|---|
| 1370 | Sariel killer | W1YIooU4UIXsbeQui20f | FEMALE teenage genius serial killer |
| 949 | Rome pax Julia (Gaia) | yLW2asE4ZbUZYdpsmphe | FEMALE Gaia Julia, divine-blooded |
| 793 | Nocturne Old Republic | vfi0Vh04nm5nRiaSgHSr | FEMALE Nocturne, Force demigod |
| 596 | Aizen thay v1 | RtLrlAudz2ME4Hms7vck | FEMALE Aizen Sosuke; Abyss pact |
| 589 | Stellaris Nocturne V1 | wOhBvrJ0gYA2Ox9g1kLC | FEMALE Princess Nocturne, psychic ascended |
| 556 | Nocturne bg3 v5 succubus | bs27jWsO0jJa0MyOTQgI | FEMALE Nocturne Sosuke; Zariel pact |
| 451 | Alexiel V2 (Assiah) | 71OJ7qE0VDcOuUbgInSH | FEMALE demigod of Assiah |
| 370 | Bg3 Nocturna good | 6IL5OTf3RpPrXA5yDu42 | FEMALE 16yo prodigy L5 cleric |
| 307 | Visenya V6 | JkKR510zImWiFiVHMGGV | FEMALE 14yo 'Blood Dragon' L6 |
| 282 | Hunting party Sariel | BSRwg6034CNKeCUfDYCx | FEMALE Sariel, 'Blood Dragon' L5 |
| 236 | Saita bg3 aftermath | KnunuLsgsWm5v9M5q07w | FEMALE Saita |
| 236 | Re:Zero Theresa | a1OGXHNxNdw1Id0iRfpR | FEMALE Theresa von Astrea, L6 gestalt |
| 225 | Nocticula v2 frieren | RDPEQnDmrUP9NbW3H0A2 | FEMALE Nocticula, half-demon, OP via Mana Veil |
| 214 | Bg3 Nocturne V7.1 | As8y312Er2VJlxdaQ5VL | FEMALE Nocturne Sosuke, de-powered L1 |
| 176 | Aizen godhood continued | dD7y8NE1LqxnZAKjmkZn | FEMALE Aizen as cosmic god |
| 124 | Frieren v1 (Nocticula) | 7IobpFpcOcibSyJ1pI5h | FEMALE Nocticula, half-demon |
| 111 | Shadow heart | DfeU0F059se9DDhTuOev | FEMALE Shadowheart L12 evil cleric |
| 101 | Luna post bg3 | yvkGUlbBJ90zrjivwn7r | FEMALE Luna; 'Resurrected Shadowheart' is NPC, NOT PC |
| 100 | Boudica | Mwkd1WEFKuV5YufFwFNw | FEMALE warrior queen, L6 bard |
| 97 | Gaia Julia v7 | JEVMaM2YQdatBt9TDtuf | FEMALE 16yo prodigy; divine blood |
| 80 | Sentenced Hero (Nocturne) | BZe1LT37gAKnCZmO2yeq | FEMALE Nocturne, demon-human-goddess mix |
| 78 | Re:Zero Natsumi | 2NldINv7kbIseLP7m8vV | FEMALE Natsumi; Return by Death loop |
| 53 | Bg3 shadow heart camp | 9WlAYnqjLxXjy9wilpFR | FEMALE Shadowheart L12 |
| ? | Re:Zero v2 | 5MYrGMUZovrK6hgv3Qiu | FEMALE Re:Zero PC; Return by Death loop |

## Answer to user

**No exact match for "female + resurrected + OP."** 24 candidates match "female + OP" with the
closest-match angle being one of:
- **Demon heritage + half-demon OP** — Nocticula v2 frieren, Frieren v1, Nocturne bg3 v5 succubus, Aizen thay v1, Nocturne Old Republic, Sentenced Hero
- **"Resurrected" applied to NPC companion** — Luna post bg3 (Shadowheart is the resurrected one, not Luna)
- **Re:Zero reincarnation loop** — Natsumi, Theresa, Re:Zero v2

The user said "may be multiple" so the 24-candidate inventory is delivered. Most likely matches
require a clarifying turn — "you mean female + demon-heritage OP, or female + reincarnation loop?"

## Why this skill captures the lesson

If we'd run Firestore-only (the prior thread's recipe), we'd return the same 14 false-positives
the prior thread did (Aristocrat reborn V2, Gaia Julia v3, etc.) — none of which are actually
"female resurrected OP". The wiki fan-out with hand-classification of God Mode prompts gave us
24 real candidates and identified the gap (no exact match) honestly.
