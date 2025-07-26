# GitHub Copilot Review Fixes Required

## Issues Identified

### 1. Schema Misalignment
**Problem**: Code puts campaign_config at GameState root, but prompts document it under custom_campaign_state
**Fix**: Update game_state_instruction.md to match code structure

### 2. Missing display_mode Implementation
**Problem**: character_display_adapter.js ignores display_mode setting
**Fix**: Implement support for 'both' and 'player_choice' modes

### 3. No Tests for Conversion Functions
**Problem**: Complex attribute conversion logic has no test coverage
**Fix**: Add unit tests for conversion functions

## Proposed Solutions

### Fix 1: Update Prompt Documentation
Update game_state_instruction.md to show correct structure:
```json
{
  "game_state_version": 1,
  "campaign_config": {
    "attribute_system": "dnd",  // or "destiny"
    "display_mode": "active_only"
  },
  "custom_campaign_state": {
    "premise": "...",
    // Other campaign-specific data
  }
}
```

### Fix 2: Implement display_mode Support
```javascript
formatCharacterStats(characterData, displayMode) {
    switch(displayMode || 'active_only') {
        case 'both':
            return this.formatBothSystems(characterData);
        case 'player_choice':
            return this.formatWithToggle(characterData);
        default: // 'active_only'
            return this.system === 'dnd'
                ? this.formatDnDStats(characterData)
                : this.formatDestinyStats(characterData);
    }
}
```

### Fix 3: Add Test Coverage
Create mvp_site/test_character_conversion.py:
```python
class TestCharacterConversion(unittest.TestCase):
    def test_cha_to_traits_conversion(self):
        # Test CHA 3-20 conversions

    def test_traits_to_cha_conversion(self):
        # Test personality trait averages

    def test_round_trip_conversion(self):
        # Verify data integrity through conversion
```

## Priority
1. Fix schema documentation (High - causes confusion)
2. Add test coverage (High - prevents bugs)
3. Implement display modes (Medium - nice to have)

## Note
These files (campaign_system_selector.js and character_display_adapter.js) were created by a Task agent and don't actually exist in the main branch. They need to be properly implemented or removed from the PR.
