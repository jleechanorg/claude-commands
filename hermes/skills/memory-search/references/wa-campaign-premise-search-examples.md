# Worked examples — WA premise search

This file extends the dual-store pitfall in `memory-search/SKILL.md` with concrete
case studies from the 2026-07-28 session. Each example shows the user query, the
trap the wiki-only search has to avoid, and the verified answer.

## Example 1 — "female resurrected OP person" (2026-07-28)

**User prompt (verbatim):**
> "Let's /skillify this process for finding campaigns and then find the campaign
> where I am a female resurrected OP person I believe there may be multiple"

**Trope signals (3):**
1. female PC
2. resurrected
3. overpowered (OP)

**Wiki fan-out result:** 130 campaigns matched at least one keyword.

**Hand-classification result:** 24 candidates matched `female + OP`. **Zero
candidates matched all three signals exactly.** The "resurrected" angle is rare
in user's WA corpus; the "female + OP" combination is widespread.

**Top 5 candidates by trope overlap:**

- Re:Zero Natsumi (`2NldINv7kbIseLP7m8vV`) — female + OP + reincarnation (Return-by-Death loop)
- Nocticula v2 frieren (`RDPEQnDmrUP9NbW3H0A2`) — female + OP + demon-heritage
- Aizen thay v1 (`RtLrlAudz2ME4Hms7vck`) — female + OP + demon-heritage
- Luna post bg3 (`yvkGUlbBJ90zrjivwn7r`) — female + OP + "Resurrected" NPC companion (not PC)
- Sentenced Hero Nocturne (`BZe1LT37gAKnCZmO2yeq`) — female + OP + demon-heritage + goddess-blood

**Lesson learned:** When the user asks for a 3-signal trope combination and the
corpus has no exact match, the right answer is to deliver the 24-candidate
partial list and explicitly state "no exact match" — NOT to fabricate a
"resurrected" angle that isn't there.

## Example 2 — "demon lord reincarnation + daughter from past life" (2026-07-28, prior thread)

**User prompt (verbatim):**
> "Find the campaign where I was reincarnated and investigating my daughter from
> a past life. I was a demon lord or demon king reincarnation I think the
> campaign might be in the LLM wiki."

**This is the canonical match that established the dual-store rule.** Confirmed:

- Campaign: Iseki v1
- CID: `dUfl4Adb3oH6foczNFSZ`
- Character: Renjiro, 16yo Sorcerer, House Vane 5th son
- God Mode excerpt: "Let's make me a reincarnation of a great demon lord. ...
  I killed half the worlds population but I had a good reason and I was level 25
  but a band of heroes finally defeated me but I only lost because my child's
  life was in danger during battle."
- Daughter subplot: Lysandra Vane, set up in Scene 19 as a future antagonist

**Firestore Firestore-side session context:**
- UID: `vnLp2G3m21PJL6kxcuAqmWSOtm73`
- Project: `worldarchitecture-ai`
- URL pattern: `https://console.firebase.google.com/project/worldarchitecture-ai/firestore/data/users/{UID}/campaigns/{CID}`

## Female-PC disambiguation in user's WA corpus

**Lesson (2026-07-28):** The user's WA playthroughs render canonical-male
characters as female. Always check the `Character:` field AND `she/her/female`
pronoun counts in the opening God Mode prompt — do NOT apply external canon.

| Character | External canon | WA user's version |
|---|---|---|
| Aizen Sosuke | Male (Bleach) | Female (WA: Aizen bg3, Aizen thay v1, Aizen godhood continued) |
| Nocturne | Male (final-fantasy) | Female (WA: Nocturne bg3 series, Nocturne Old Republic) |
| Nocturna | Female (DC) | Female (WA: Nocturna good) |
| Astarion | Male (Baldur's Gate 3) | Mixed (WA: astarion post bg3 — check each variant) |
| Vesperian Thul | Male (WA-original) | MALE (WA: 20 Vespera Thul variants — see attached note) [^mie] |
| Alexiel | Female (WA-original) | Female (WA: Alexiel V2, Alexiel assiah) |

**Pitfall:** `Aizen bg3` series has BOTH male and female variants. The pattern
for testing is:

```python
text = primary_file.read_text()[:3000]
she_count = len(re.findall(r"\b(she|her|hers|female)\b", text, re.IGNORECASE))
he_count = len(re.findall(r"\b(he|him|his|male)\b", text, re.IGNORECASE))
is_female = she_count > he_count
```

## Disqualified candidates (looked promising, weren't actually female-PC)

These came up in keyword scans but their God Mode prompt describes a **male** PC:

- `Vesperian Thul` (`0Lb9YSywhmJciZCNPZHX`) — 16yo MALE dark paladin "The Prodigal Executioner"
- `Aizen bg3` (`2Ivu5p5OcXkkgyoytzGy`) — Sosuke Aizen MALE wizard
- `Aizen bg3 v2` (`ADCwQxVeXIrMXdLDSDVf`) — same character
- `Aurelius julius caesar v1/v2` — MALE youngest son of Caesar
- `Astarion post bg3` — MALE vampire lord
- `evil pally` (Ser Arion) — MALE knight
- `Shadow Weaver` (Vaelin Thorne farmer) — MALE farmer

## Cross-references

- `memory-search/SKILL.md` § "Pitfall — WorldArchitect campaign search by premise lives in TWO stores"
- `wa-campaign-premise-find/SKILL.md` — the class-level skill that operationalizes this dual-store rule
- `wa-campaign-premise-find/references/worked-example-2026-07-28.md` — the same lesson documented in the new skill
</content>
</invoke>