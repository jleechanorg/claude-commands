# Aizen god-mechanics pattern — quantified-stat-table + 3-layer reconciliation

The user has asked twice (2026-07-20 redesign, prior god-campaign work) for god mechanics "as good as the old Aizen god-of-tyranny campaign." This reference is the durable knowledge that answers WHY the Aizen pattern is better, and HOW to reconcile it with the current production system.

## Why Aizen worked (Jeffrey's preference signal)

The `world_reference/aizen_god_mechanics.md` file (11,449 bytes, May 29 2026 in the active worktree, replicated across ~50 worktrees — same content in `world_reference/aizen_god_mechanics.md` across `~/projects/*`, `~/repos/jleechanorg/*`, `~/your-project.com_rate_25/`, etc.) defines a Nascent Greater Deity with **hard numbers the LLM can ground combat output in**:

| Stat | Nascent Greater (Aizen) | Transcendent Greater (Ultimate Aizen) | Ao (Overgod) |
|---|---|---|---|
| DR (HP for gods) | 750 | 1750 | Infinite |
| DAC (AC) | 25 | 25 | Infinite |
| DPP/day (resource pool) | 825 | 1825 | Infinite |
| DAIR Mod (attack) | +31 | +56 | Infinite |
| DLR (legendary actions) | 4 | 9 | Infinite |
| Primary Damage | 80 + (1d20×5) | 110 + (1d20×10) | Infinite |

Compare to the current `$PROJECT_ROOT/prompts/divine/divine_leverage_system.md` which uses:

```
Divine Leverage = Highest Ability Modifier + Divine Rank Bonus
Risk Multiplier: Rank 1 ×2.0 | Rank 2 ×1.5 | Rank 3 ×1.0 | Rank 4 ×0.75 | Rank 5 ×0.5 | Rank 6+ ×0.25
Dissonance Cost = max(0, Leverage − Safe Limit) × Risk Multiplier
```

The Aizen pattern gives the LLM **concrete values to put in combat output**: "DR 750, primary damage 80 + (1d20×5)". The production pattern forces the LLM to **derive per-roll**: "DL 9, risk mult 0.75, dissonance cost 0.75×(9-15)". Same LLM, same input — Aizen produces more combat-grounded prose. **This is the regression the user is pointing at when they say "newer god campaigns got less challenging."**

## The 3-layer framing duplication

Two different schemes exist, both in active use:

**Production scheme** (`divine_leverage_system.md`):
- Layer 0 = The Mask (mortal interface, public face)
- Layer 1 = The Persona (fabricated god, L31+ unlock)
- Layer 2 = The Source (true self, never revealed unless Drop the Mask)

**Aizen scheme** (`aizen_god_mechanics.md`):
- Layer 1 = Ambiguous aura (what most gods see — confused, can't tell what's real)
- Layer 2 = Kyōka Suigetsu projected stat block (300 DR / 350 DPP/day / +24 DAIR / 4 DLR — false stats for specific targets like Mystra)
- Layer 3 = "Protective measure" cover story (caps at 750 DR if follower-scaling is uncovered)

The two schemes disagree on:
- **Numbering** (production starts at 0, Aizen starts at 1)
- **What's at the bottom** (production's Layer 0 is the mortal Mask — no deception, just public face; Aizen's Layer 1 is already a deception)
- **Total layer count** (production caps at 3 layers; Aizen has 3 layers ALL of which are deception)

**Recommended canonical scheme for the redesign** — adopt Aizen's three-layer scheme because:
1. The user prefers it (it's the pattern they keep asking for).
2. It's symmetric (all three layers are the same KIND of thing — deception with different audiences).
3. It generalizes better across settings (no implicit "mortal face" assumption).

Renumber to Layer 1/2/3 to match Aizen. Production's Layer 0 becomes "the mortal face" — a separate concept (a meta-layer the PC projects, not a deception layer).

## The DPP (Divine Power Points) overload

Three different semantics in active use:

| Where | Semantics | Refresh |
|---|---|---|
| `divine_ascension_ceremony.md` | Finite pool (5/5), consumed on divine actions | Per Tier (per rest) |
| `divine_leverage_system.md` | "Dissonance IS the cost" — no pool, the resource is the dissonance percentage | Per scene/long-rest |
| `aizen_god_mechanics.md` | Daily-replenishing pool (825/day) | Per day |

**Recommended canonical semantics** for the redesign — daily-replenishing pool with explicit cap (Aizen pattern). Reasoning:
- The LLM can write "Aizen burns 100 DPP to manifest Divine Shield" without re-deriving cost tables every turn.
- Daily replenishment is consistent with how every other D&D-flavored divine stat works (spell slots refresh per day, legendary actions refresh per day, etc.).
- Per-scene semantics force the LLM to track dissonance percentage AND divine power separately, which fragments combat output.

## Follower-scaling formula (Aizen's other good idea)

`aizen_god_mechanics.md` defines:

```
Current_Stat_Value = Stat_Nascent + ((F / 1,000,000) × (Stat_Transcendent − Stat_Nascent))
```

Where F = active follower count, goal = 1,000,000 followers in 1 year → Transcendent Greater Deity.

This is **mechanically novel** — no other tier system uses worshipper-count as a stat scalar. The user has explicitly named this as something they want to keep in the redesign. Implementation: include it in the new divine tier as the default Greater-Deity-to-Greater-Deity-with-Ascension progression axis.

## 3-Generation Power Lineage (from God of Murder PR #8483)

A separate but related pattern — **don't ship a tier redesign without a G0/G1/G2 fork structure**:

- **G0 — Origin** (the protagonist who establishes the system). Believes the architecture is complete.
- **G1 — Rejecter** (the antagonist who rejects the architecture on principle). Forces a re-evaluation.
- **G2 — NEW choice** (the protagonist's successor, presented with the mature system). The fork is "is this architecture *good*?" — not "rule harder" vs "rule softer." Reject the optimization entirely.

This was the 3-Generation pattern from `world_reference/campaign_module_god_of_murder.md` (PR #8483, 2026-07-20). It gives the user a reason to **play a campaign under a new tier** rather than just **read about it**.

## Mechanical preferences the user has confirmed across the redesign ask

- **Setting-agnostic core** — the user has explicitly said "general, not Faerun/D&D" twice. Default to Prime Mover / Apex Powers / reality fabric / Power Tier terminology.
- **Quantified stat table > formula-only** — see above.
- **3-layer deception that is symmetric** (Aizen-style, not production-style).
- **Daily-replenishing DPP** (Aizen-style).
- **Follower-scaling as a stat axis** (Aizen innovation).
- **3-Generation fork structure** (God of Murder PR #8483 innovation).
- **Capture the "I liked the older ones better" sentiment** by referencing real doc IDs (the `aizen campaign summarized` doc 1L1sOStC7rVjCzE8KHhpMf55TarmvNXNuEx-RH2vwO-0 is the canonical origin; the 4-part `Aizen god campaign chat 1-1-300` through `1-901-1147` is the canonical god-campaign run; `aizen_god_mechanics.md` is the codified cheat-sheet).

## Source pointers (verified 2026-07-20)

- Local mechanics file: `$HOME/projects/your-project.com/world_reference/aizen_god_mechanics.md` (11,449 bytes, May 29 2026)
- Google Doc origin: `1L1sOStC7rVjCzE8KHhpMf55TarmvNXNuEx-RH2vwO-0` (9.4 KB, modified 2025-06-18, $USER@gmail.com)
- God-campaign chat 1-1147: 4 Google Docs `1_cwZPJWV-…`, `171UytT10…`, `1lQ3TchAi…`, `1haLKJCGQ…` (Jun 14 2025, 89.8–99.4 KB each)
- God-campaign continuation: `1HnRXmsl8rcB5_ZNmO7WkDIxhTTZCZw0n` (1.2 MB .txt, Jun 18 2025) — wiki source `aizen-godhood-continued`
- User's codified PDF: `13uLZFIlU_oOBSus2PEX2SXw_34hwhFox` (111.3 KB, Jun 14 2025)
- Nocturne Sosuke personality stack: `17nbIhrvo_R4G_k-vh8Dn98Qu1Rw4IF7Il0IIdvgP3ew` (9.4 KB, Dec 11 2025) — Tywin + Griffith + Aizen + Johan Liebert archetype
- Tyranny-world Nocturne: `1sVa4faSAohOtUUKBl2OC1fbVPNwW3lJ2fpQTzAGM4Co` (11.9 KB, Dec 11 2025)
- Modern Nocturne bg3 v7: `14RF0NkIl2cauWl0pmVYQk1WK6DuE7nxoouH4FRAwf70` (55.9 KB, Feb 9 2026) — the user's "newer" favorite they're comparing to

## Cited in this skill from

- SOUL.md `## COMMIT: proof-before-claim` — every claim about a doc ID above is verified against `gog drive search --json` output, not paraphrased.
- `memory-search` skill — the 9-store fan-out was the source for the wiki + roadmap + history cross-references.
- `google-credentials-fallback` §5 — the `gog drive search` recipe that produced the doc IDs.