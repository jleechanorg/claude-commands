# Code Review Command

**Purpose**: Process ALL PR comments systematically

**Action**: List EVERY comment individually, apply changes, commit

**Usage**: `/review` or `/copilot`

**Implementation**: 
1. Use `gh pr view <PR#> --comments` to get ALL comments
2. Use `gh api repos/owner/repo/pulls/<PR#>/comments` for inline comments
3. List each comment with:
   - Author (user vs bot)
   - File:Line if applicable
   - Full comment text
   - Status: ✅ Addressed / ❌ Not addressed / 🔄 Partially addressed
4. Include "suppressed" and "low confidence" comments
5. Apply changes and commit with descriptive messages