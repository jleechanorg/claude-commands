# /commentfetch Command

**Usage**: `/commentfetch <PR_NUMBER> [--output FILE]`

**Purpose**: Fetch all comments from a GitHub PR including inline code reviews, general comments, review comments, and Copilot suggestions.

## Description

Pure Python implementation that collects comments from all GitHub PR sources. This is a mechanical data collection command with no intelligence - it simply fetches and standardizes comment data.

## Output Format

Creates a JSON file at `/tmp/copilot-$(git branch --show-current)/comments.json` (or specified output) with:

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
    "needs_response": 8,
    "repo": "owner/repo"
  }
}
```

## Comment Types

- **inline**: Code review comments on specific lines
- **general**: Issue-style comments on the PR
- **review**: Review summary comments
- **copilot**: GitHub Copilot suggestions (including suppressed)

## Response Detection

The command automatically determines if comments need responses based on:
- Question marks in the comment
- Keywords like "please", "could you", "fix", "issue"
- Review states (CHANGES_REQUESTED, COMMENTED)
- Bot comments are usually skipped unless they contain questions

## Examples

```bash
# Fetch all comments for PR 820
/commentfetch 820

# Fetch with custom output file
/commentfetch 820 --output pr820_comments.json

# Check results
cat /tmp/copilot-$(git branch --show-current)/comments.json | jq '.metadata'
```

## Integration

This command is typically the first step in the `/copilot` workflow, providing comment data to other commands like `/fixpr` and `/commentreply`.