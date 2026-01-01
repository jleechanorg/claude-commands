# Combat Ally Turns & Resource Visibility Test

## Issue Summary

Based on the user's combat log (`Dragon knight (1).txt`), two critical issues were identified:

### Issue 1: Allies Don't Take Automatic Turns

**Evidence from log:**
- Lines 389-410: Player takes multiple consecutive turns (Divine Smite attack, then Shove attempt) without any ally or enemy turns between them
- Line 413: User had to use **god mode** to remind the LLM: "make sure my team is also taking combat turns automatically"
- Lines 417-420: Only AFTER god mode intervention did retainer/Lady Ashwood/Shadow-born take their turns

**Expected Behavior:**
In D&D 5E combat, all combatants take turns according to initiative order. After the player acts, the next combatant in initiative should automatically take their turn.

**Actual Behavior:**
The LLM allowed the player to take multiple consecutive turns without processing ally or enemy turns. This violates basic combat flow and makes combat unplayable.

### Issue 2: No Combat Resource Visibility

**Evidence from log:**
Throughout the entire combat (lines 389-420), there was **NO display** of:
- Player's remaining actions/bonus actions this turn
- Player's current HP vs max HP
- Enemy HP, levels, or AC
- Ally HP or status

**Expected Behavior (per `combat_system_instruction.md:534-542`):**
```
**ROUND 3 - Initiative Order:**
🗡️ Kira (PC) - HP: 28/35 - [ACTIVE]
⚔️ Goblin Boss - HP: 22/45 - [Bloodied]
🐺 Wolf Companion - HP: 8/11 - [OK]
💀 Goblin 1 - HP: 0/7 - [Defeated]
⚔️ Goblin 2 - HP: 4/7 - [Wounded]
```

**Actual Behavior:**
No combat status display. Player has to guess what resources they have and can't make informed tactical decisions.

## Test File: `test_combat_ally_turns.py`

The test harness runs an end-to-end scenario focused on the two reported issues:

- **Automatic ally turns:** Confirms that at least one ally turn appears in the Round 2 narrative and that combat remains active.
- **Combat status visibility:** Requires both a round header and an initiative display plus at least one combatant status line (HP/AC/status) in the Round 2 narrative.

## Running the Test

```bash
# From project root
TESTING=true PYTHONPATH=$(pwd) python3 -m pytest testing_mcp/test_combat_ally_turns.py -v -s
```

**Note:** These tests require a running MCP server with real LLM calls. They will:
1. Start a local MCP server
2. Create a test campaign
3. Execute combat actions
4. Save evidence under `/tmp/evidence/` in test-specific directories

## Evidence Collection

All test runs save evidence to structured directories:
- `/tmp/evidence/combat_ally_turns_status/`

Evidence includes:
- Request/response JSON with full narrative
- Analysis JSON with extracted data (participants, actions, etc.)
- Timestamps and provenance info

## Next Steps

After running these tests and confirming they reproduce the issues:

1. **Fix 1: Automatic Ally Turn Management**
   - Update `combat_system_instruction.md` to explicitly mandate ally turn processing
   - Add validation in combat agent to ensure non-PC combatants act each round
   - Possibly add tool/function that forces initiative advancement

2. **Fix 2: Combat Status Display**
   - Update `combat_system_instruction.md` to make status block MANDATORY
   - Add template/example that LLM must follow
   - Consider adding a combat status tool that formats the display
   - Ensure HP/AC display requirements are enforced

3. **Verification**
   - Re-run these tests after fixes
   - All three tests should pass
   - Combat should feel playable and tactical

## Related Files

- **Combat prompt:** `mvp_site/prompts/combat_system_instruction.md`
- **Combat agent:** `mvp_site/agents.py` (CombatAgent class)
- **User log (example reference):** `test_data/combat_logs/Dragon knight (1).txt`
- **Test utilities:** `testing_mcp/lib/`
