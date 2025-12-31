# Merge Decision: Campaign Integrity + Meta-Instruction Separation

**Date:** 2025-12-30
**Branch:** `claude/fix-alexiel-campaign-x6tpx`
**Merged From:** origin/main
**PR:** #2561

## Conflicts Resolved

### Conflict 1: `mvp_site/prompts/narrative_system_instruction.md` - ESSENTIALS Section

**From Main:** New ESSENTIALS block with Living World, NPC autonomy, and Meta-Instruction Separation summaries

**From Feature Branch:** Nothing (no ESSENTIALS existed)

**Resolution:** KEPT MAIN'S ESSENTIALS and added Campaign Integrity summaries:

```markdown
<!-- ESSENTIALS (token-constrained mode)
- LIVING WORLD: NPCs approach player with missions...
- Superiors GIVE orders...
- NPC autonomy: independent goals...
- META-INSTRUCTION SEPARATION: Player OOC instructions are INVISIBLE to NPCs...
- SOCIAL HP: Major NPCs require multi-roll skill challenges. Kings=8-12 HP, Gods=15+...  ← ADDED
- NPC HARD LIMITS: Every major NPC has inviolable limits. No roll bypasses character agency. ← ADDED
- Complication system...
/ESSENTIALS -->
```

**Rationale:** Main's ESSENTIALS provides token-constrained summaries for LLMs. Our Social HP and Hard Limits guidelines should be represented there for consistency.

---

### Conflict 2: `mvp_site/prompts/narrative_system_instruction.md` - NPC Behavior Section

**From Main:** Added "Meta-Instruction Separation (CRITICAL)" subsection explaining OOC directive handling

**From Feature Branch:** Added Social HP System and NPC Hard Limits sections

**Resolution:** KEPT BOTH - They are complementary NPC behavior guidelines:

| Section | Purpose | Source |
|---------|---------|--------|
| Social HP System | Prevents single-roll NPC conversions | Feature Branch |
| NPC Hard Limits | Defines inviolable NPC constraints | Feature Branch |
| Meta-Instruction Separation | Prevents NPCs from acting on OOC info | Main |

**Final Section Order:**
1. NPC Autonomy & Agency (common baseline)
2. **Social HP System** (from PR #2561)
3. **NPC Hard Limits** (from PR #2561)
4. **Meta-Instruction Separation** (from main)
5. Narrative Consistency (common)

---

## Additional Fix Applied

### ESSENTIALS Tier Encounter Count Correction

**Issue:** CodeRabbit/Cursor flagged that ESSENTIALS said `T1=5-7 encounters/day` but detailed section said T1=3-4 encounters.

**Fix Applied:**

```markdown
# Before (incorrect):
- HIGH-MAGIC BALANCE: T1=5-7 encounters/day, T2=elite groups+counter-buffs, T3=set-pieces+artifact-level enemies

# After (correct):
- HIGH-MAGIC BALANCE: T1=3-4 encounters/day, T2=5-7 encounters+resource pressure, T3=elite groups+counter-buffs, T4=set-pieces+artifact-level enemies
```

Now matches the detailed HIGH-MAGIC CAMPAIGN BALANCE section with correct tier assignments.

---

## Impact Assessment

| Metric | Value |
|--------|-------|
| Token increase | ~20 tokens (2 ESSENTIALS lines) |
| Semantic conflicts | None |
| Test coverage | Validated by `test_campaign_integrity_real_api.py` and `test_campaign_balance_real_api.py` |

## Rationale Summary

Both feature sets improve NPC behavior quality from different angles:

1. **Social HP + Hard Limits** → Prevents "paper tiger" NPCs that fold to single rolls
2. **Meta-Instruction Separation** → Prevents NPCs from acting on player OOC instructions

Together, they create more realistic, consistent NPC behavior while respecting both game balance and narrative agency.
