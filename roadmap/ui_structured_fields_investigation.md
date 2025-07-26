# UI Structured Fields Investigation Results

**Date**: 2025-07-08
**Issue**: Structured fields (session_header, planning_block, dice_rolls, resources, debug_info) are not displayed in the UI

## Investigation Summary

### 1. Frontend Code Analysis ✅
- The `appendToStory()` function in `app.js` is correctly implemented
- It properly handles all structured fields when `fullData` parameter is provided
- The styling and HTML generation for each field type is correct

### 2. API Response Analysis ✅
- The `/api/campaigns/{id}/interaction` POST endpoint returns all structured fields correctly
- Fields included: session_header, planning_block, dice_rolls, resources, debug_info
- These are returned along with the narrative response

### 3. Root Cause Identified 🔍
**The GET `/api/campaigns/{id}` endpoint does NOT return structured fields**

When a campaign is loaded:
1. Frontend calls GET `/api/campaigns/{id}`
2. API returns only basic story entries with format:
   ```json
   {
     "campaign": {...},
     "story": [
       {"actor": "gemini", "text": "narrative only", "mode": "story", ...}
     ],
     "game_state": {...}
   }
   ```
3. The structured fields are NOT included in the story entries

### 4. Why It Works During Interaction
- During live gameplay, the POST interaction endpoint returns structured fields
- The frontend correctly displays them using `appendToStory(actor, text, mode, debugMode, sequenceId, fullData)`
- But when the page is refreshed or campaign is loaded, only basic story data is available

## Solution Options

### Option 1: Store Structured Fields in Firestore
- Modify story entry storage to include all structured fields
- Update the story schema to include: session_header, planning_block, dice_rolls, etc.
- Pros: Data is preserved and always available
- Cons: Requires database schema change

### Option 2: Enhance GET Campaign Endpoint
- Modify GET endpoint to regenerate or fetch structured fields
- Could reconstruct from game state or stored metadata
- Pros: No database changes needed
- Cons: May be computationally expensive

### Option 3: Lazy Loading
- Keep current GET endpoint minimal
- Add new endpoint to fetch structured data for specific story entries
- Frontend requests details when needed
- Pros: Flexible and efficient
- Cons: Additional API calls needed

## Test Results

Browser test confirmed:
- ✗ session_header NOT displayed
- ✓ narrative displayed (only field shown)
- ✗ dice_rolls NOT displayed
- ✗ resources NOT displayed
- ✗ planning_block NOT displayed
- ✗ debug_info NOT displayed

Screenshots captured show only narrative text in story entries.

## Recommendation

Implement **Option 1** - Store structured fields with story entries in Firestore. This ensures:
1. Complete data persistence
2. Consistent display on page load
3. No additional API calls or processing needed
4. Historical game sessions retain full context

The story entry schema should be updated to include optional fields for all structured response data.
