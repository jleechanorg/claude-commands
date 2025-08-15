# /commentfetch Command

**Usage**: `/commentfetch <PR_NUMBER>`

**Purpose**: Fetch fresh comments (all sources) from a GitHub PR including inline code reviews, general comments, review comments, and Copilot suggestions. ALWAYS fetches fresh data from GitHub API - NEVER reads from existing cached /tmp files. Filtering/triage is performed downstream.

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

Pure Python implementation that collects comments from all GitHub PR sources. ALWAYS fetches fresh data from GitHub API on each execution (NEVER reads from existing files) and saves to `/tmp/{branch_name}/comments.json` for downstream processing by `/commentreply`. The payload includes fields (e.g., `in_reply_to_id`) enabling downstream filtering of already-replied threads.

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

This command is typically the first step in the `/copilot` workflow, providing fresh comment data to `/tmp/{branch_name}/comments.json` for other commands like `/fixpr` and `/commentreply`. ALWAYS fetches current data from GitHub API (NEVER reads from cache) and overwrites the comments file completely.
