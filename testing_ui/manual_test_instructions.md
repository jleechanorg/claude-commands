# Manual Test Instructions for Campaign Wizard Fixes

## Test 1: Custom Character Display Fix

### Steps:
1. Open the application in your browser
2. Click "Create New Campaign" to open the wizard
3. In Step 1 (Basic Info):
   - Enter any campaign title
   - **Enter a custom character name** (e.g., "Lady Moonwhisper" or "Bob the Mighty")
   - Enter any setting
4. Click "Next" through steps 2 and 3
5. On Step 4 (Launch/Confirmation screen):
   - **VERIFY**: The "Character:" field shows your custom character name
   - **VERIFY**: It does NOT show "dragon knight" or "Ser Arion" unless you explicitly typed that
   - **VERIFY**: The description does NOT show "Ser Arion Dragon Knight Campaign"

### Expected Result:
- ✅ Your custom character name appears in the confirmation
- ✅ No hardcoded "dragon knight" text appears

## Test 2: Campaign Page Loading Fix

### Steps:
1. Create a new campaign (using wizard or regular form)
2. Wait for the campaign creation to complete
3. You should be automatically navigated to the campaign page

### Expected Result:
- ✅ The campaign page loads with BOTH:
  - Your initial prompt/description
  - The AI's opening story response (e.g., "Scene #1")
- ✅ No error messages appear
- ✅ If the story takes a moment to load, you should see retry messages in the console

### What Was Fixed:

1. **Character Display Issue**:
   - Added character preview element to confirmation screen HTML
   - Updated preview logic to show actual character input
   - Removed hardcoded "Ser Arion Dragon Knight Campaign" text
   - Added real-time preview updates as you type

2. **Story Loading Issue**:
   - Added 500ms delay after campaign creation to handle Firestore consistency
   - Added retry logic (up to 3 attempts) if story data is incomplete
   - Better error messages if story fails to load
   - Console logging to help debug loading issues

### Console Debugging:
Open browser DevTools console to see:
- "Loading campaign X - Story entries: Y, Debug mode: Z"
- "Displayed X story entries out of Y total"
- Retry messages if story is incomplete
- Any error messages about missing data