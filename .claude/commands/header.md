# Header Command

**Purpose**: Generate mandatory branch header AND detect if previous response was missing it

**Usage**: `/header` or `/usage`

**Action**: 
1. Check if previous response was missing the mandatory header (compliance violation)
2. If violation detected, save to Memory MCP for learning
3. Generate the required branch header with API usage statistics

## Implementation

**Enhanced Process**:
1. **Python script** checks for missing header in previous response
2. **Memory MCP** saves violation if detected  
3. **Shell script** generates the required header

**Commands**:
- Check & save violation: `python3 .claude/commands/header_check.py`
- Generate header: `./claude_command_scripts/git-header.sh --with-api`

This automatically:
1. Gets local branch name
2. Gets remote upstream info  
3. Gets PR information
4. Gets Claude API usage statistics (remaining sessions out of 50)
5. Formats everything into the required header

**Benefits**:
- ✅ **One command with usage info** - Shows sessions remaining out of monthly 50
- ✅ **Automatic formatting** - Prevents formatting errors
- ✅ **Error handling** - Gracefully handles missing upstreams/PRs
- ✅ **Usage awareness** - Never run out of sessions unexpectedly
- ✅ **Consistent output** - Same format every time

## Output Format

Generates the mandatory header format with API usage:
```
[Local: <branch> | Remote: <upstream> | PR: <number> <url>]
[API: <remaining>/<limit> requests (<percentage>% remaining) | Reset: <time>]
```

Examples:
- `[Local: main | Remote: origin/main | PR: none]`
- `[API: 49/50 requests (98% remaining) | Reset: 15:08:12]`
- `[Local: feature-x | Remote: origin/main | PR: #123 https://github.com/user/repo/pull/123]`
- `[API: 25/50 requests (50% remaining) | Reset: 08:30:45]`

## Usage in Workflow

**Best Practice**: Use `/header` before ending responses to:
- Generate the required header with **one command**
- Create a reminder checkpoint to include it
- Ensure consistent formatting with zero effort
- Remove all friction in compliance

**Automated Memory Aid**:
- The single command `./claude_command_scripts/git-header.sh` makes header generation effortless
- No need to remember 3 separate commands
- Consistent, reliable output every time
- Perfect for developing muscle memory

**Integration**: 
- End every response with the header (one simple command)
- Use when switching branches or tasks
- Make it a habit: "content first, header last"

## Compliance Note

This command helps fulfill the 🚨 CRITICAL requirement in CLAUDE.md that EVERY response must end with the branch header. The header provides essential context about:
- Current working branch
- Remote tracking status  
- Associated pull request (if any)

Using this command makes compliance easier and helps maintain the required workflow discipline.