# Scratchpad: Story Mode Improvements

## Project Goal
Enhance the story mode experience by adding sequence tracking and fixing the edit campaign dialog functionality.

## Branch Info
- **Branch**: `story-mode-improvements`
- **Target**: `main`
- **Status**: In development

## Implementation Plan

### Phase 1: Story Sequence Display
1. **Show sequence ID in story mode headers** ✅ Pending
   - Add sequence numbering to story entries
   - Display as "Story #X" instead of just "Story"
   - Make it look cool/engaging for users

2. **Brainstorm cooler name for sequence ID** ✅ Pending
   - Replace "Story #X" with something more engaging
   - Consider: "Chapter", "Act", "Scene", "Tale", "Chronicle", "Verse"
   - Research user-friendly alternatives

### Phase 2: Edit Campaign UX Fix
3. **Fix edit campaign dialog Enter button** ✅ Pending
   - Currently Enter dismisses the dialog
   - Should save changes instead
   - Improve user experience

## Current State
- ✅ Clean branch created from main
- ✅ Scratchpad created
- 🔄 Push branch to GitHub
- ⏳ Implement sequence ID display
- ⏳ Fix edit campaign dialog

## Next Steps
1. Push current branch to GitHub
2. Analyze story entry structure in codebase
3. Implement sequence ID display
4. Fix edit campaign dialog Enter key behavior
5. Test implementations
6. Create PR

## Key Context
- Story entries are tracked in `appendToStory` function in app.js
- Story structure includes: actor, text, mode
- Edit campaign modal is in index.html with ID `editCampaignModal`
- Current label logic: 'Story' for gemini, 'Main Character'/'God'/'You' for user

## Technical Notes
- Frontend: static/app.js handles story rendering
- Backend: main.py handles story entry creation
- Story entries stored in Firestore with actor/text/mode structure
- Edit campaign uses Bootstrap modal with form submission
