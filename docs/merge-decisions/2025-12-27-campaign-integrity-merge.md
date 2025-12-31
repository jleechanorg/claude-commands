# Merge Decision: Campaign Integrity Guidelines + Non-Combat XP

**Date:** 2025-12-27
**Branch:** `claude/fix-alexiel-campaign-x6tpx`
**Merged From:** origin/main

## Conflict Location

`mvp_site/prompts/mechanics_system_instruction.md` - ESSENTIALS section

## Changes Being Merged

### From Feature Branch (Campaign Integrity PR #2561)

Added LLM-driven campaign balance guidelines:

```
- MILESTONE LEVELING: Recommend +1-3 levels per arc. Epic/mythic campaigns may exceed Level 20.
- ATTUNEMENT: Configurable (Standard=3, Loose=5-6, None=unlimited). High-magic balance via encounter design + enemy parity.
- HIGH-MAGIC BALANCE: T1=5-7 encounters/day, T2=elite groups+counter-buffs, T3=set-pieces+artifact-level enemies
- RESOURCES: Track spell slots per cast. Forced march = exhaustion consideration.
```

These prevent:
- "Speedrun" progression (Level 1 to Level 50 in one session)
- "Christmas Tree" effect (unlimited magic item attunement)
- "Infinite Ammo" problem (no resource tracking)

### From Main Branch (Combat-Focused Agent PR #2553)

Added XP/reward transparency rules:

```
- NON-COMBAT KILLS: Executions, ambushes, trap kills MUST award XP + loot (same CR table)
- NARRATIVE EVENTS: Quests, milestones, social victories MUST display XP + rewards
```

These ensure:
- XP is awarded for narrative kills (executions, ambushes, trap kills)
- Non-combat achievements display rewards visibly

## Resolution Decision

**KEPT BOTH SETS OF RULES** - They are semantically complementary:

1. **Main's rules** focus on XP/reward **transparency** (display rewards visibly)
2. **Our rules** focus on campaign **pacing and balance** (prevent power creep)

Neither conflicts with the other. Both improve the player experience from different angles.

## Final ESSENTIALS Section

```markdown
- NON-COMBAT KILLS: Executions, ambushes, trap kills MUST award XP + loot (same CR table)
- NARRATIVE EVENTS: Quests, milestones, social victories MUST display XP + rewards
- MILESTONE LEVELING: Recommend +1-3 levels per arc. Epic/mythic campaigns may exceed Level 20.
- ATTUNEMENT: Configurable (Standard=3, Loose=5-6, None=unlimited). High-magic balance via encounter design + enemy parity.
- HIGH-MAGIC BALANCE: T1=5-7 encounters/day, T2=elite groups+counter-buffs, T3=set-pieces+artifact-level enemies
- RESOURCES: Track spell slots per cast. Forced march = exhaustion consideration.
```

Main's rules placed first (preserving their order from the incoming commit), followed by our Campaign Integrity additions.

## Impact Assessment

- **Token increase:** ~6 lines added to ESSENTIALS (~60 tokens)
- **Compatibility:** Full - no semantic conflicts
- **Testing:** Campaign integrity tests in `testing_mcp/test_campaign_integrity_real_api.py` validate the guidelines

## Rationale Summary

| Rule Source | Purpose | Kept? |
|------------|---------|-------|
| Main: Non-Combat Kills | Award XP for narrative kills | Yes |
| Main: Narrative Events | Display rewards visibly | Yes |
| Ours: Milestone Leveling | Prevent speedrun progression | Yes |
| Ours: Attunement | Configurable item limits | Yes |
| Ours: High-Magic Balance | Tier-based encounter design | Yes |
| Ours: Resources | Track spell slots/exhaustion | Yes |
