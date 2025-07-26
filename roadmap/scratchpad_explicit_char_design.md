# Division by Zero Fix Plan - HP Percentage Calculation

## Root Cause Analysis

### 1. The Error Location
- **File**: `game_state.py`, line 102
- **Code**: `hp_percentage = (hp_current / hp_max) * 100`
- **Context**: This occurs in the `validate_narrative_consistency()` method during character creation with "ApproveFoundation" command

### 2. Why hp_max is 0
During character creation flow:
- User submits "ApproveFoundation: Approve these choices and proceed to ability scores"
- At this stage, the character is partially created - foundation choices are made but HP hasn't been calculated yet
- The character exists in the system but with incomplete data (hp_max = 0)
- The narrative consistency checker runs before HP initialization is complete

### 3. Current Safeguards That Failed
- `DefensiveNumericConverter` should enforce hp_max >= 1, but it only applies during Pydantic validation
- The check `if hp_current is not None and hp_max is not None:` (line 92) doesn't protect against hp_max = 0
- The division happens without checking for zero value

## Comprehensive Fix Strategy

### 1. Immediate Fix - Add Zero Check
```python
# In game_state.py, line 92-102
if hp_current is not None and hp_max is not None and hp_max > 0:
    hp_percentage = (hp_current / hp_max) * 100
    # ... rest of the logic
```

### 2. All Division Locations to Fix
Based on grep analysis, these locations need protection:
- `game_state.py:102` - Main division in validate_narrative_consistency
- String formatting with hp_current/hp_max in lines 96, 100, 107, 110

### 3. Similar Issues to Check
Other potential division by zero risks:
- XP calculations (if xp_to_next_level could be 0)
- Damage/healing percentages
- Any other stat ratios

### 4. Root Cause Solutions

#### Option A: Skip Validation During Character Creation
```python
# Early return if character is being created
if self.world_data.get('character_creation_in_progress'):
    return []  # No discrepancies during creation
```

#### Option B: Default Values for Incomplete Characters
```python
# Use defensive defaults
hp_max = pc_data.get('hp_max', 1)  # Default to 1 if missing
hp_current = pc_data.get('hp_current', hp_max)  # Default to max if missing
```

#### Option C: Comprehensive Guard Clause
```python
# Ensure we have valid data before any calculations
if hp_current is not None and hp_max and hp_max > 0:
    hp_percentage = (hp_current / hp_max) * 100
else:
    # Skip HP-based validation if data is incomplete
    continue
```

### 5. Implementation Plan

1. **Immediate Hotfix** (game_state.py):
   - Add `hp_max > 0` check before division
   - Add similar checks for all hp_max usages

2. **Defensive Improvements**:
   - Update get() calls to use defensive defaults: `pc_data.get('hp_max', 1)`
   - Add early return for character creation state

3. **Systematic Fix**:
   - Create a helper method for safe percentage calculation
   - Use throughout codebase

4. **Test Coverage**:
   - Add test for character creation with incomplete data
   - Add test for hp_max = 0 scenario
   - Add test for other edge cases (None, negative, etc.)

## Recommended Fix Implementation

### Step 1: Immediate Hotfix
```python
# game_state.py - Update validate_narrative_consistency method
hp_current = pc_data.get('hp_current')
hp_max = pc_data.get('hp_max', 1)  # Default to 1

if hp_current is not None and hp_max > 0:
    # Safe to calculate percentage
    hp_percentage = (hp_current / hp_max) * 100
    # ... rest of validation logic
```

### Step 2: Add Helper Method
```python
def calculate_hp_percentage(hp_current, hp_max):
    """Safely calculate HP percentage with zero division protection."""
    if hp_current is None or hp_max is None or hp_max <= 0:
        return None
    return (hp_current / hp_max) * 100
```

### Step 3: Character Creation Detection
```python
# Early in validate_narrative_consistency
if any(phrase in narrative_lower for phrase in ['approve foundation', 'character creation', 'ability scores']):
    # Character is being created, skip validation
    return []
```

## Testing Strategy

1. **Unit Tests**:
   - Test hp_max = 0
   - Test hp_max = None
   - Test negative hp_max
   - Test during character creation

2. **Integration Tests**:
   - Test full character creation flow
   - Test ApproveFoundation command
   - Test incomplete character data

3. **Edge Cases**:
   - Both hp_current and hp_max are 0
   - hp_current > hp_max
   - String values that convert to 0
