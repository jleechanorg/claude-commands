# Combat Turn Management & Resource Visibility Fix

## Issue Summary

Based on user combat log analysis (`Dragon knight (1).txt`) and test validation (`testing_mcp/test_combat_ally_turns.py`):

### Bug 1: Allies Not Taking Automatic Turns
**Evidence:** Lines 389-410 of combat log - player took consecutive turns (Divine Smite → Shove) without ally/enemy actions. Required god mode intervention at line 413.

**Root Cause:** No explicit requirement in combat instructions to process all combatants in initiative order.

### Bug 2: No Combat Resource Visibility
**Evidence:** Throughout combat (lines 389-420) - no display of HP, AC, actions remaining, enemy stats, or ally status.

**Root Cause:** Combat status display was suggested but not mandatory.

## Fixes Implemented

### 1. Combat System Instruction Updates (`mvp_site/prompts/combat_system_instruction.md`)

#### Added Critical Section: Initiative Order and Turn Processing (Lines 15-61)

**Key Changes:**
- **ABSOLUTE RULE**: ALL combatants must take turns in strict initiative order
- **FORBIDDEN**: Consecutive player turns
- Explicit violation example showing what NOT to do
- Correct example showing proper turn rotation
- Mandatory ally turn processing steps:
  1. Announce ally turn with HP
  2. Choose tactical action
  3. Roll dice via tool_requests
  4. Narrate outcome
  5. Update state
- Player input boundaries: only process player actions on their turn

#### Enhanced Section: Combat Status Display (Lines 585-644)

**Key Changes:**
- **CRITICAL REQUIREMENT**: Display status block at START of EVERY round
- Formatted status block template with all required info:
  ```
  ═══════════════════════════════════════════════════════════════
                           ROUND 3
  ═══════════════════════════════════════════════════════════════
  INITIATIVE ORDER:
  🗡️ Kira (PC, Level 5) - HP: 28/35 | AC: 16 | Actions: 1, Bonus: 1 - [ACTIVE TURN]
  ⚔️ Goblin Boss (CR 1) - HP: 22/45 | AC: 15 - [Bloodied]
  🐺 Wolf Companion (Ally) - HP: 8/11 | AC: 13 - [OK]
  💀 Goblin 1 - HP: 0/7 - [DEFEATED]
  ⚔️ Goblin 2 - HP: 4/7 | AC: 13 - [Wounded]
  ═══════════════════════════════════════════════════════════════
  ```
- Required information by combatant type:
  - **PC**: Name, level, HP, AC, actions remaining, turn indicator
  - **Allies**: Name, type, HP, AC, status
  - **Enemies**: Name, CR, HP, AC, status
- Status indicators: [OK], [Wounded], [Bloodied], [Critical], [DEFEATED], [ACTIVE TURN]
- When to display: start of every round (MANDATORY), after significant HP changes (optional), when player asks

#### Updated ESSENTIALS Header (Lines 3-13)

Added to token-constrained mode summary:
- `CRITICAL: ALL combatants MUST take turns in initiative order - NO consecutive player turns`
- `CRITICAL: Combat status block MUST be displayed at the start of EVERY round`

### 2. Narrative Instruction Updates (`mvp_site/prompts/narrative_system_instruction.md`)

#### Updated ESSENTIALS Header (Line 19)

Added combat flow reminder:
- `🎲 COMBAT: Process ALL combatants in initiative order - NO consecutive player turns. Display status block every round.`

This ensures the rule is visible even in token-constrained contexts.

## Expected Behavior After Fix

### During Combat:

**Round Start:**
```
═══════════════════════════════════════════════════════════════
                         ROUND 1
═══════════════════════════════════════════════════════════════
INITIATIVE ORDER:
🗡️ Ser Marcus (PC, Level 2) - HP: 23/23 | AC: 19 | Actions: 1, Bonus: 1 - [ACTIVE TURN]
⚔️ Gareth (Ally, Level 1) - HP: 11/11 | AC: 16 - [OK]
💀 Bandit 1 (CR 1/8) - HP: 11/11 | AC: 13 - [OK]
💀 Bandit 2 (CR 1/8) - HP: 11/11 | AC: 13 - [OK]
═══════════════════════════════════════════════════════════════

**Marcus's Turn**
You attack the first bandit with your longsword.
[DICE: Attack roll 1d20+5 = 18 vs AC 13 (HIT)]
[DICE: Damage 1d8+3 = 9 slashing]
Your blade strikes true, cutting deep into the bandit's shoulder.

**Gareth's Turn - HP: 11/11**
Your retainer Gareth moves to engage the second bandit.
[DICE: Attack roll 1d20+3 = 14 vs AC 13 (HIT)]
[DICE: Damage 1d8+1 = 6 slashing]
His sword finds its mark, drawing blood.

**Bandit 1's Turn - HP: 2/11 [Critical]**
The wounded bandit swings wildly at you.
[DICE: Attack roll 1d20+3 = 9 vs AC 19 (MISS)]
His scimitar glances off your armor.

**Bandit 2's Turn - HP: 5/11 [Bloodied]**
The second bandit attacks Gareth.
[DICE: Attack roll 1d20+3 = 16 vs AC 16 (HIT)]
[DICE: Damage 1d6+1 = 4 slashing]
His blade cuts into Gareth's side.

═══════════════════════════════════════════════════════════════
                         ROUND 2
═══════════════════════════════════════════════════════════════
INITIATIVE ORDER:
🗡️ Ser Marcus (PC, Level 2) - HP: 23/23 | AC: 19 | Actions: 1, Bonus: 1 - [ACTIVE TURN]
⚔️ Gareth (Ally, Level 1) - HP: 7/11 | AC: 16 - [Wounded]
💀 Bandit 1 (CR 1/8) - HP: 2/11 | AC: 13 - [Critical]
💀 Bandit 2 (CR 1/8) - HP: 5/11 | AC: 13 - [Bloodied]
═══════════════════════════════════════════════════════════════

**Marcus's Turn**
What do you do?
```

## Validation

### Test Suite: `testing_mcp/test_combat_ally_turns.py`

Three tests validate the fixes:

1. **`test_allies_take_automatic_turns`**
   - ✅ Should now PASS
   - Verifies allies/enemies act between player turns
   - No more consecutive player turns allowed

2. **`test_combat_resources_are_visible`**
   - ✅ Should now PASS
   - Verifies HP/AC displayed for all combatants
   - Checks narrative contains required combat info

3. **`test_combat_status_displayed_each_round`**
   - ✅ Should now PASS
   - Verifies "ROUND X" or "INITIATIVE ORDER" header present
   - Confirms status block formatting

### Running Tests

```bash
TESTING=true PYTHONPATH=/Users/jleechan/projects/worktree_worker2 \
  python3 -m pytest testing_mcp/test_combat_ally_turns.py -v -s
```

**Note:** Real API tests are slow (~2-5 minutes per test). Increase pytest timeout if needed:
```bash
pytest testing_mcp/test_combat_ally_turns.py --timeout=600
```

## Files Modified

1. **`mvp_site/prompts/combat_system_instruction.md`**
   - Added Initiative Order and Turn Processing section (lines 15-61)
   - Enhanced Combat Status Display section (lines 585-644)
   - Updated ESSENTIALS header (lines 11-12)

2. **`mvp_site/prompts/narrative_system_instruction.md`**
   - Added combat reminder to ESSENTIALS (line 19)

3. **Test Files Created:**
   - `testing_mcp/test_combat_ally_turns.py` - Test suite
   - `testing_mcp/test_combat_ally_turns_README.md` - Test documentation

## Rollback Instructions

If these changes cause issues:

```bash
git diff mvp_site/prompts/combat_system_instruction.md
git diff mvp_site/prompts/narrative_system_instruction.md

# Revert if needed
git checkout HEAD -- mvp_site/prompts/combat_system_instruction.md
git checkout HEAD -- mvp_site/prompts/narrative_system_instruction.md
```

## Success Criteria

- ✅ Players never experience consecutive turns without other combatants acting
- ✅ Combat status block appears at start of every round
- ✅ HP/AC visible for all combatants (PC, allies, enemies)
- ✅ Player can see actions remaining (action, bonus action)
- ✅ Status indicators ([OK], [Wounded], [Bloodied], etc.) displayed
- ✅ Turn indicator shows whose turn it is
- ✅ No need for god mode to remind LLM about ally turns

## Next Steps

1. Commit these changes to `combat_turns` branch
2. Test in a real campaign to verify fixes work
3. If successful, merge to main
4. Monitor future combat sessions for any regressions
