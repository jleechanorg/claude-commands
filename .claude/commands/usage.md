# /usage Command

Check Claude API usage and rate limits along with git status.

## Usage
```
/usage
```

## Description
Shows current Claude API usage including:
- Requests remaining vs monthly limit (out of 50)
- Usage percentage with visual indicators
- Rate limit reset times
- Automatic alerts at 75%, 50%, and 25% remaining
- Git branch and PR status for context

## Implementation
**Single Command**: `./claude_command_scripts/git-header.sh --with-api`

This provides the same output as `/header` - combining both git status and API usage in one convenient command.

## Output Format
```
[Local: <branch> | Remote: <upstream> | PR: <number> <url>]
[API: <remaining>/50 requests (<percentage>% remaining) | Reset: <time>]
```

## Alerts
- 🟢 **Above 75%**: Silent operation
- 🟡 **50-75%**: Balloon notification on Windows
- 🔴 **25-50%**: Warning balloon notification  
- ⚠️ **Below 25%**: Critical popup alert

Use `./claude_command_scripts/git-header.sh --monitor` for proactive monitoring with alerts.