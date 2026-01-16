# Dice Roll Extraction Test (PR #3588)

## Overview

This test validates the dice roll extraction feature from PR #3588. It ensures that:

1. ✅ Dice rolls are extracted from `action_resolution.mechanics.rolls`
2. ✅ Extracted rolls populate the `dice_rolls` field for UI display
3. ✅ Backward compatibility is maintained for legacy responses
4. ✅ Evidence is properly captured and saved

## Quick Start

### Option 1: Use GCP Preview Server (Easiest)

```bash
cd testing_mcp
python test_dice_roll_extraction_pr.py --use-preview
```

This will connect to the GCP preview server running the latest changes.

### Option 2: Use Local Server

```bash
cd testing_mcp
python test_dice_roll_extraction_pr.py --server-url http://127.0.0.1:8001
```

Requires local MCP server running on port 8001.

### Option 3: Start Local Server Automatically

```bash
cd testing_mcp
python test_dice_roll_extraction_pr.py --start-local
```

This will start a local server and run tests against it.

## Test Scenarios

### 1. Single d20 Combat Roll
- **Action**: "I attack the goblin with my longsword."
- **Expected**: Single d20 roll extracted from action_resolution
- **Validates**: Basic extraction works

### 2. Multiple Rolls (Attack + Damage)
- **Action**: "I attack the goblin with my longsword. Resolve the attack and damage."
- **Expected**: Multiple rolls (attack and damage) extracted
- **Validates**: Multiple roll extraction works

### 3. Skill Check Roll
- **Action**: "I try to sneak past the guards. Make a Stealth check."
- **Expected**: d20 + modifier roll extracted
- **Validates**: Non-combat rolls work

### 4. Backward Compatibility
- **Action**: Various actions
- **Expected**: Either extracted rolls OR legacy dice_rolls present
- **Validates**: Backward compatibility maintained

## Evidence Output

Results are saved to:
```
/tmp/<repo>/<branch>/test_dice_roll_extraction_pr/iteration_NNN/
├── README.md              # Package manifest
├── methodology.md         # Testing approach
├── evidence.md            # Summary with metrics
├── metadata.json          # Machine-readable metadata
├── test_results.json      # Test results and provenance
└── latest -> iteration_NNN (symlink)
```

Each iteration includes:
- Git provenance (branch, commit, origin)
- Server health status
- Full test results per scenario
- Timestamps and run ID

## Interpreting Results

### Success Criteria
- **Passed**: All test cases return 100% success rate
- **Failed**: Any test case has errors

### Common Issues

**No dice rolls extracted:**
- Check that action_resolution.mechanics.rolls is populated
- Verify LLM is configured correctly
- Check server logs for errors

**Backward compatibility fails:**
- Ensure responses include either extracted rolls or legacy dice_rolls
- Check game_state_instruction.md is updated

## Integration with CI

This test is designed to run in CI as part of evidence validation:

```bash
cd testing_mcp
python test_dice_roll_extraction_pr.py --use-preview
```

Results are automatically saved to `/tmp/` structure for CI log capture.

## Manual Testing

### Verify Single Test
```bash
# Test just the combat roll extraction
python -c "
import sys
sys.path.insert(0, '.')
from test_dice_roll_extraction_pr import DiceExtractionTester

tester = DiceExtractionTester('http://127.0.0.1:8001')
result = tester.test_single_combat_roll()
print(f\"Test passed: {result.get('passed')}\")
if result.get('errors'):
    for error in result['errors']:
        print(f\"  - {error}\")
"
```

## Debugging

### Enable Verbose Output
The test prints progress indicators:
- 🎯 Running tests
- ✅ PASS (green)
- ❌ FAIL (red)
- 💾 Saving evidence

### Check Server Health
```bash
curl -s http://127.0.0.1:8001/health | python -m json.tool
```

### Review Provenance
```bash
# View captured git state
cat /tmp/worldarchitect.ai/claude_fix_dice_roll_pr_dfotw/test_dice_roll_extraction_pr/latest/metadata.json | python -m json.tool
```

## Related Files

- **Feature Implementation**: `mvp_site/action_resolution_utils.py`
- **Tests**: `mvp_site/tests/test_action_resolution_utils.py`
- **LLM Instructions**:
  - `mvp_site/prompts/narrative_system_instruction.md`
  - `mvp_site/prompts/game_state_instruction.md`
- **Backward Compatibility Note**: `mvp_site/world_logic.py`

## PR Reference

- **PR #3588**: Fix: Centralize dice rolls and auto-extract to UI field
- **Related PR #3568**: Original PR (archived)
