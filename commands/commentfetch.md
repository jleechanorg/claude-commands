# /commentfetch Command

**Usage**: `/commentfetch <PR_NUMBER>`

**Purpose**: Fetch UNRESPONDED comments from a GitHub PR including inline code reviews, general comments, review comments, and Copilot suggestions. Always fetches fresh data from GitHub API - no caching.

## Description

Pure Python implementation that collects UNRESPONDED comments from all GitHub PR sources. Uses GitHub API `in_reply_to_id` field analysis to filter out already-replied comments. Always fetches fresh data on each execution and saves to `/tmp/{branch_name}/comments.json` for downstream processing by `/commentreply`.

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

This command is typically the first step in the `/copilot` workflow, providing fresh comment data to `/tmp/{branch_name}/comments.json` for other commands like `/fixpr` and `/commentreply`. Always fetches current data and overwrites the comments file.
