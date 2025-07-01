# Attribute System API Implementation

## Overview
The dual attribute system support requires both backend storage and prompt documentation to function correctly.

## Backend Implementation

### 1. Campaign Creation API
When creating a campaign, the frontend can specify the attribute system:

```javascript
POST /api/campaigns
{
  "title": "My Campaign",
  "prompt": "A brave knight...",
  "attribute_system": "dnd",  // or "destiny" (optional, defaults to "dnd")
  "custom_options": ["companions", "defaultWorld"]
}
```

### 2. GameState Storage
The attribute system is stored in `custom_campaign_state`:
```python
game_state = {
    "custom_campaign_state": {
        "attribute_system": "dnd",  # or "destiny"
        "premise": "...",
        # other campaign data
    }
}
```

### 3. Default Behavior
- If "Use Destiny System" checkbox is checked (default): uses "destiny"
- If checkbox is unchecked: uses "dnd"
- Once set at campaign creation, cannot be changed
- All characters in campaign use the same system

## Frontend Implementation (Future)

### 1. Campaign Creation UI
Add radio buttons or dropdown:
```html
<label>Choose Attribute System:</label>
<select name="attribute_system">
  <option value="dnd" selected>D&D (6 Attributes)</option>
  <option value="destiny">Destiny (5 Aptitudes)</option>
</select>
```

### 2. Character Display
Check `gameState.custom_campaign_state.attribute_system` to determine display:
- If "dnd": Show STR, DEX, CON, INT, WIS, CHA
- If "destiny": Show Physique, Coordination, Health, Intelligence, Wisdom

### 3. Social Mechanics Display
- D&D: Show CHA-based social checks
- Destiny: Show personality trait-based social checks

## Testing

### Manual Test Steps
1. Create campaign with `"attribute_system": "destiny"`
2. Verify it's saved in custom_campaign_state
3. Generate character and verify AI uses Destiny aptitudes
4. Create another campaign without specifying system
5. Verify it defaults to "dnd"

### Unit Test Coverage Needed
```python
def test_campaign_creation_with_attribute_system():
    # Test explicit destiny system
    
def test_campaign_creation_default_system():
    # Test defaults to dnd
    
def test_attribute_system_persistence():
    # Test system is saved and loaded correctly
```

## Migration Considerations
- Existing campaigns have no attribute_system
- Code defaults these to "dnd" automatically
- No migration needed - backward compatible