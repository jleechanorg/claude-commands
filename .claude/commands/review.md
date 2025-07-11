# Code Review Command

**Purpose**: Process ALL PR comments systematically with proper tracking and replies

**Action**: List EVERY comment individually, apply changes, commit, and post replies to show resolution

**Usage**: `/review [PR#]`

**Enhanced Implementation**: 
1. **Extract ALL Comments**:
   - Use `gh pr view <PR#> --comments` to get general comments
   - Use `gh api repos/owner/repo/pulls/<PR#>/comments` for inline code comments
   - Include "suppressed" and "low confidence" Copilot comments
   - Extract from ALL review sources (user reviews, bot reviews, issue comments)

2. **Categorize and Track**:
   - Group by comment type: User vs Bot vs Copilot
   - Track file:line location for inline comments
   - Assign unique tracking IDs for reference
   - Identify comment priority: Critical, Important, Suggestion, Nitpick

3. **Status Tracking Matrix**:
   ```
   | ID | Author | File:Line | Comment Summary | Status | Reply Link |
   |----|--------|-----------|-----------------|--------|------------|
   | C1 | user   | main.py:655 | Logic fix needed | ❌ Pending | - |
   | C2 | bot    | wizard.js:233 | Remove old wizard | ✅ Fixed | #r2198653108 |
   ```

4. **Apply Changes Systematically**:
   - Process comments by priority (Critical → Important → Suggestions)
   - Make focused commits for each logical group of fixes
   - Update status tracking as changes are applied

5. **Post Replies and Updates**:
   - For each addressed comment, post an inline reply using:
     ```bash
     gh api -X POST repos/owner/repo/pulls/PR#/comments \
       -f body="✅ RESOLVED: [description of fix]" \
       -f commit_id="sha" -f path="file" --field position=N
     ```
   - Reference original comment in reply: "Addressing comment #ID by @author"
   - Post summary comment with status matrix showing all addressed issues

6. **Final Verification**:
   - Run all tests to ensure fixes don't break anything
   - Update PR description with resolution summary
   - Mark PR as ready for re-review if needed

**Comment Reply Protocol**:
- ✅ **RESOLVED**: Issue completely fixed with code changes
- 🔄 **PARTIALLY ADDRESSED**: Some progress made, more work needed  
- 📝 **ACKNOWLEDGED**: Comment noted, will address in future work
- ❌ **DECLINED**: Intentionally not implementing with reasoning
- 🤔 **NEEDS CLARIFICATION**: Requires more information from commenter

**Tracking Features**:
- Maintain comment resolution log in `tmp/review_status_PR#.md`
- Generate before/after summary showing all addressed issues
- Create commit messages that reference specific comment IDs
- Post follow-up summary comment with complete resolution matrix