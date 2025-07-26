# Scratchpad: Banned Names Integration

## Project Goal
Integrate the banned names list into the WorldArchitect.AI system to prevent AI from using overused LLM names.

## Implementation Completed

### 1. World Loader Integration ✅
- Modified `mvp_site/world_loader.py` to load `banned_names.md`
- Added `load_banned_names()` function
- Integrated banned names into world content with "CRITICAL NAMING RESTRICTIONS" section
- Banned names now loaded automatically when world content is used

### 2. System Instructions Updated ✅
- **Master Directive** (`prompts/master_directive.md`):
  - Added "Universal Naming Rules" section
  - Added to CRITICAL REMINDERS (#7)
  - Version updated to 1.2

- **Narrative System Instruction** (`prompts/narrative_system_instruction.md`):
  - Added rule to Companion Generation Rules
  - Fixed example that used banned name "Aria" → "Lysandra"

### 3. Testing ✅
- Created and ran `test_banned_names.py` to verify:
  - Banned names file loads correctly (923 characters)
  - Names are included in world content
  - Enforcement instructions are present
  - All test banned names found in combined content

## How It Works

1. When world content is loaded (default world setting enabled), the system:
   - Loads `celestial_wars_alexiel_book.md`
   - Loads `world_assiah.md`
   - Loads `banned_names.md`
   - Combines all with clear hierarchy

2. The AI receives:
   - Full banned names list in "CRITICAL NAMING RESTRICTIONS" section
   - Enforcement instructions to never use those names
   - Instructions in master directive (highest authority)
   - Specific rules in companion generation

3. Authority hierarchy:
   - Master Directive declares banned names have ABSOLUTE AUTHORITY
   - No other instruction can override this restriction
   - Applies to all named entities (NPCs, locations, items, etc.)

## Files Modified
- `mvp_site/world_loader.py` - Added banned names loading
- `mvp_site/prompts/master_directive.md` - Added universal naming rules
- `mvp_site/prompts/narrative_system_instruction.md` - Fixed companion generation

## Next Steps
- Monitor AI behavior to ensure compliance
- Consider adding validation in game_state.py to reject banned names
- Update any other examples that might use banned names

## Branch Info
- Branch: test-sariel-full
- Status: Ready to commit
- Changes: Banned names integration complete
