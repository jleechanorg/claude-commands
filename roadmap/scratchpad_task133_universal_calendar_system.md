# TASK-133: Universal Calendar System - Requirements & Implementation

## Task Overview
Create a simple universal calendar system that uses consistent backend numbers but lets the LLM handle narrative conversion for different fictional universes (Star Wars, Modern Earth, Fantasy, Sci-Fi).

## Current Implementation Analysis
- **Primary calendar logic:** `mvp_site/prompts/game_state_instruction.md` (lines 622, 792, 803, 814-843, 1019)
- **World-specific dates:** `mvp_site/world/world_assiah_compressed.md` (lines 12, 21-22)
- **Time calculations:** `mvp_site/game_state.py` (lines 282-374)
- **System:** Uses Forgotten Realms Calendar of Harptos with fantasy month names like "Ches", "Mirtul", "Kythorn"

## Autonomous Implementation Requirements

### 1. Simple Backend Consistency
- **Keep existing world_time JSON structure:**
  ```json
  {
    "world_time": {
      "year": 1492,
      "month": "Ches",
      "day": 20,
      "hour": 9,
      "minute": 51,
      "second": 10,
      "time_of_day": "Morning"
    }
  }
  ```
- **Add universe field:** `"calendar_universe": "fantasy"` to campaign data
- **Backend uses numbers internally** but stores string templates for LLM conversion

### 2. Universe Configuration System
- **Location:** Add universe presets directly in prompt templates (not separate files)
- **Presets to include:**
  - `"fantasy"` - Current Forgotten Realms system (default)
  - `"modern"` - Gregorian calendar (January, February, etc.)
  - `"starwars"` - Star Wars calendar (First Moon, Second Moon, etc., ABY/BBY years)
  - `"scifi"` - Generic futuristic (Cycle 1, Cycle 2, etc.)
  - `"custom"` - User-defined template

### 3. LLM-Driven Calendar Conversion
- **Prompt Instructions:** Add calendar conversion rules to `game_state_instruction.md`
- **Template System:** LLM uses universe templates to convert backend dates to narrative
- **Example conversion:**
  - Backend: `{"year": 1492, "month": "Ches", "day": 20}`
  - Fantasy: "Ches 20, 1492 DR"
  - Modern: "March 20, 2024"
  - Star Wars: "Second Moon 20, 22 ABY"
  - Sci-Fi: "Cycle 3, Day 20, Standard 2387"

### 4. Campaign Integration
- **Universe Selection:** Add to campaign creation wizard
- **DM Inference:** LLM should infer universe from campaign setting if not specified
- **User Prompt:** Ask user to clarify if universe is ambiguous
- **Storage:** Add `calendar_universe` field to campaign data in Firestore

### 5. Backward Compatibility
- **Existing Campaigns:** Auto-assign "fantasy" universe to existing campaigns
- **Migration Logic:** Add check in game_state.py to ensure calendar_universe exists
- **User Prompt:** For ambiguous existing campaigns, prompt user to select universe
- **No Data Loss:** Existing dates remain valid, just get new display format

### 6. Elements Made Configurable
- **Month Names:** LLM converts based on universe template
- **Day Names:** LLM handles day-of-week naming per universe
- **Year Systems:** LLM converts year numbering (DR, CE, ABY, etc.)
- **Seasons:** LLM adapts seasonal references per universe
- **Holidays:** LLM creates appropriate holidays/events per universe
- **NOT Configurable:** Days per month, months per year (keep 12 months, ~30 days)

## Implementation Plan

### Phase 1: Prompt Template Updates (45 min)
1. **Update `game_state_instruction.md`:**
   - Add universe template definitions
   - Add calendar conversion instructions for LLM
   - Add examples for each universe type

2. **Add universe field validation:**
   - Ensure `calendar_universe` is included in campaign data schema
   - Add default fallback to "fantasy"

### Phase 2: Campaign Integration (30 min)
1. **Update campaign creation:**
   - Add universe selection dropdown/option
   - Include in campaign data structure

2. **Add DM inference logic:**
   - Prompt instructions for LLM to detect universe from setting
   - Fallback to asking user if unclear

### Phase 3: Migration & Compatibility (30 min)
1. **Update `game_state.py`:**
   - Add check for missing `calendar_universe` field
   - Auto-assign "fantasy" to existing campaigns
   - Add migration logging

2. **Error handling:**
   - Crash program on invalid date configurations
   - Clear error messages for missing universe data

### Phase 4: Testing & Validation (15 min)
1. **Test universe conversion:**
   - Create test campaigns in each universe
   - Verify LLM correctly converts dates
   - Test existing campaign compatibility

## Success Criteria
- [ ] Backend maintains consistent numeric date structure
- [ ] LLM correctly converts dates to appropriate universe format
- [ ] Campaign creation includes universe selection
- [ ] Existing campaigns auto-migrate to "fantasy" universe
- [ ] All universe presets work correctly (fantasy, modern, starwars, scifi, custom)
- [ ] DM can infer universe from campaign setting or prompt user
- [ ] Month names, years, seasons, holidays adapt per universe
- [ ] No data loss during migration
- [ ] Clear error handling for invalid configurations

## Files to Modify
1. **`mvp_site/prompts/game_state_instruction.md`** - Add universe templates and conversion rules
2. **`mvp_site/game_state.py`** - Add migration logic and universe validation
3. **Campaign creation templates** - Add universe selection UI
4. **Firestore schema** - Include `calendar_universe` field

## Dependencies
- Existing world_time structure in game state
- Campaign creation workflow
- LLM prompt processing system
- Firestore campaign data structure

## Estimated Time: 2 hours
- Prompt updates: 45 minutes
- Campaign integration: 30 minutes
- Migration logic: 30 minutes
- Testing: 15 minutes

## Testing Plan
1. Create new campaigns in each universe type
2. Verify date conversion accuracy in narrative
3. Test existing campaign migration
4. Verify error handling for edge cases
5. Test DM universe inference and user prompting
