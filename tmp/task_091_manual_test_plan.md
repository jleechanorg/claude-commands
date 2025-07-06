# TASK-091: Manual Test Plan for Unchecked Checkboxes

**Test Date:** 2025-07-05  
**Objective:** Verify campaign creation and functionality with unchecked checkboxes

## Test Environment Setup

1. **Start Flask Application**
   ```bash
   cd /home/jleechan/projects/worldarchitect.ai/worktree_roadmap
   source ../venv/bin/activate
   python3 mvp_site/main.py serve
   ```

2. **Access Application**
   - Open browser to: http://localhost:8080
   - Sign in with test credentials

## Test Cases

### Test Case 1: Both Checkboxes Unchecked
**Steps:**
1. Navigate to "Start New Campaign"
2. Enter campaign title: "Test - Both Unchecked"
3. Enter campaign prompt: "A simple adventure in a forest"
4. **UNCHECK** both checkboxes:
   - [ ] Jeff's Narrative Flair (Storytelling & Character)
   - [ ] Jeff's Mechanical Precision (Rules & Protocols)
5. Keep custom options as default
6. Click "Begin Adventure!"

**Expected Results:**
- ✅ Campaign should be created successfully
- ✅ No errors or crashes
- ✅ Initial story should be generated
- ✅ UI should remain responsive

### Test Case 2: Only Narrative Checked
**Steps:**
1. Create new campaign: "Test - Only Narrative"
2. Campaign prompt: "A magical quest in ancient ruins"
3. Check only: ✅ Jeff's Narrative Flair
4. Uncheck: ⬜ Jeff's Mechanical Precision
5. Click "Begin Adventure!"

**Expected Results:**
- ✅ Campaign creation successful
- ✅ Story should focus more on narrative elements
- ✅ Reduced mechanical precision expected

### Test Case 3: Only Mechanics Checked
**Steps:**
1. Create new campaign: "Test - Only Mechanics"
2. Campaign prompt: "A tactical combat scenario"
3. Uncheck: ⬜ Jeff's Narrative Flair  
4. Check only: ✅ Jeff's Mechanical Precision
5. Click "Begin Adventure!"

**Expected Results:**
- ✅ Campaign creation successful
- ✅ Story should focus more on rules and mechanics
- ✅ Reduced narrative flair expected

### Test Case 4: Multiple Interactions Test
**For each test case above, perform 5-10 interactions:**

1. "I look around carefully."
2. "I examine my equipment."
3. "I move forward cautiously."
4. "I try to find shelter."
5. "I search for useful items."
6. "I listen for any sounds."
7. "I check my current status."
8. "I plan my next move."
9. "I explore a different direction."
10. "I rest and think about my situation."

**Expected Results:**
- ✅ All interactions should complete successfully
- ✅ No crashes or errors
- ✅ Story should continue logically
- ✅ Game state should persist correctly
- ✅ UI should remain responsive throughout

## Technical Verification

### Frontend Code Review
- ✅ Checkboxes properly configured in HTML
- ✅ JavaScript form handler processes unchecked boxes correctly
- ✅ Selected prompts array is empty when both unchecked

### Backend Code Review
- ✅ `selected_prompts` parameter defaults to empty array
- ✅ `gemini_service.get_initial_story()` handles empty prompts
- ✅ Warning logged when no prompts selected
- ✅ Campaign creation continues normally

## Test Results Template

| Test Case | Status | Notes |
|-----------|--------|-------|
| Both Unchecked | ⬜ | |
| Only Narrative | ⬜ | |
| Only Mechanics | ⬜ | |
| Multiple Interactions | ⬜ | |

## Issues Found

*(To be filled during testing)*

## Recommendations

*(To be filled after testing)*

## Conclusion

*(To be filled after testing)*