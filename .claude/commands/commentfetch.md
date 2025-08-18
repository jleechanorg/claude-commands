# /commentfetch Command

**Usage**: `/commentfetch <PR_NUMBER>`

**Purpose**: Fetch UNRESPONDED comments from a GitHub PR including inline code reviews, general comments, review comments, and Copilot suggestions. Also fetches GitHub CI status using /fixpr methodology. Always fetches fresh data from GitHub API - no caching.

## 🚨 CRITICAL: Comprehensive Comment Detection Function

**MANDATORY**: Fixed copilot skip detection bug that was ignoring inline review comments:
```bash
# 🚨 COMPREHENSIVE COMMENT DETECTION FUNCTION 
# CRITICAL FIX: Include ALL comment sources (inline review comments were missing)
get_comprehensive_comment_count() {
    local pr_number=$1
    local owner_repo=$(gh repo view --json owner,name | jq -r '.owner.login + "/" + .name')
    
    # Get all three comment sources
    local general_comments=$(gh pr view $pr_number --json comments | jq '.comments | length')
    local review_comments=$(gh pr view $pr_number --json reviews | jq '.reviews | length')
    # Robust pagination-safe counting for inline comments
    local inline_comments=$(gh api "repos/$owner_repo/pulls/$pr_number/comments" --paginate --jq '.[].id' 2>/dev/null | wc -l | tr -d ' ')
    inline_comments=${inline_comments:-0}
    
    local total=$((general_comments + review_comments + inline_comments))
    
    # Debug output for transparency
    echo "🔍 COMPREHENSIVE COMMENT DETECTION:" >&2
    echo "  📝 General comments: $general_comments" >&2
    echo "  📋 Review comments: $review_comments" >&2  
    echo "  💬 Inline review comments: $inline_comments" >&2
    echo "  📊 Total: $total" >&2
    
    echo "$total"
}
```

**Usage**: Call `get_comprehensive_comment_count <PR_NUMBER>` from any command that needs accurate comment counting for skip conditions or processing decisions.

## Description

Pure Python implementation that collects UNRESPONDED comments from all GitHub PR sources AND GitHub CI status. Uses GitHub API `in_reply_to_id` field analysis to filter out already-replied comments. Implements /fixpr CI status methodology with defensive programming patterns. Always fetches fresh data on each execution and saves to `/tmp/{branch_name}/comments.json` for downstream processing by `/commentreply`.

## Output Format

Saves structured JSON data to `/tmp/{branch_name}/comments.json` with:

```json
{
  "pr": "820",
  "fetched_at": "2025-01-21T12:00:00Z",
  "comments": [
    {
      "id": "12345",
      "type": "inline|general|review|copilot",
      "body": "Comment text",
      "author": "username",
      "created_at": "2025-01-21T11:00:00Z",
      "file": "path/to/file.py",  // for inline comments
      "line": 42,                  // for inline comments
      "already_replied": false,
      "requires_response": true
    }
  ],
  "ci_status": {
    "overall_state": "FAILING|PASSING|PENDING|ERROR",
    "mergeable": true,
    "merge_state_status": "clean",
    "checks": [
      {
        "name": "test",
        "status": "FAILURE",
        "description": "Process completed with exit code 1",
        "url": "https://github.com/owner/repo/actions/runs/123"
      }
    ],
    "summary": {"total": 4, "passing": 2, "failing": 1, "pending": 1},
    "failing_checks": [...],
    "pending_checks": [...],
    "fetched_at": "2025-01-21T12:00:00Z"
  },
  "metadata": {
    "total": 17,
    "by_type": {
      "inline": 8,
      "general": 1,
      "review": 2,
      "copilot": 6
    },
    "unresponded_count": 8,
    "repo": "owner/repo"
  }
}
```

## Comment Types

- **inline**: Code review comments on specific lines
- **general**: Issue-style comments on the PR
- **review**: Review summary comments
- **copilot**: GitHub Copilot suggestions (including suppressed)

## Unresponded Comment Filtering

🚨 **CRITICAL EFFICIENCY ENHANCEMENT**: The command automatically identifies and filters unresponded comments:

### 1. Already-Replied Detection (PRIMARY FILTER)
- **Method**: Analyze GitHub API `in_reply_to_id` field to identify threaded responses
- **Logic**: If comment #12345 has any replies with `in_reply_to_id: 12345`, mark as ALREADY_REPLIED
- **Efficiency**: Skip already-replied comments from downstream processing entirely

### 2. Response Requirement Analysis (SECONDARY FILTER)
For comments that are NOT already replied, determine if they need responses based on:
- Question marks in the comment text
- Keywords like "please", "could you", "fix", "issue", "suggestion"
- Review states (CHANGES_REQUESTED, COMMENTED)
- Bot comments (Copilot, CodeRabbit) - ALWAYS require responses
- Human reviewer feedback - ALWAYS require responses

### 3. Output Optimization
- **JSON field**: `"already_replied": false` (only unresponded comments included)
- **Metadata**: `"unresponded_count": X` for quick verification
- **Fresh Data**: Always fetches current GitHub state, no stale cache issues
- **Efficiency**: Downstream commands process only comments needing responses

## Implementation

The command runs the Python script directly:
```bash
python3 .claude/commands/_copilot_modules/commentfetch.py <PR_NUMBER>
```

## Examples

```bash
# Fetch all fresh comments for PR 820
/commentfetch 820
# Internally runs: python3 .claude/commands/_copilot_modules/commentfetch.py 820

# Saves comments to /tmp/{branch_name}/comments.json
# Downstream commands read from the saved file
```

## Integration

This command is typically the first step in the `/copilot` workflow, providing fresh comment data AND CI status to `/tmp/{branch_name}/comments.json` for other commands like `/fixpr` and `/commentreply`. Uses /fixpr methodology for authoritative GitHub CI status with defensive programming patterns. Always fetches current data and overwrites the comments file.

## CI Status Integration

**Enhanced with /fixpr methodology**: 
- Uses `gh pr view --json statusCheckRollup,mergeable,mergeStateStatus` for authoritative GitHub CI data
- Implements defensive programming patterns (statusCheckRollup is a LIST, safe access)
- Provides overall state assessment (FAILING/PASSING/PENDING/ERROR)
- Categorizes checks for quick analysis (failing_checks, pending_checks)
- Includes merge status and detailed check information
- Fetched in parallel with comments for optimal performance
