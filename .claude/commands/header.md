# Header Command

**Purpose**: Generate and display the mandatory branch header for CLAUDE.md compliance

**Usage**: `/header`

**Action**: Execute single script to generate the required branch header

## Implementation

**Single Command**: `./claude_command_scripts/git-header.sh`

This script automatically:
1. Gets local branch name
2. Gets remote upstream info  
3. Gets PR information
4. Formats everything into the required header

**Benefits**:
- ✅ **One command instead of three** - Reduces cognitive load
- ✅ **Automatic formatting** - Prevents formatting errors
- ✅ **Error handling** - Gracefully handles missing upstreams/PRs
- ✅ **Consistent output** - Same format every time

## Output Format

Generates the mandatory header format:
```
[Local: <branch> | Remote: <upstream> | PR: <number> <url>]
```

Examples:
- `[Local: main | Remote: origin/main | PR: none]`
- `[Local: feature-x | Remote: origin/main | PR: #123 https://github.com/user/repo/pull/123]`

## Usage in Workflow

**Best Practice**: Use `/header` at the start of responses to:
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
- Start every response with `/header` (one simple command)
- Use when switching branches or tasks
- Make it a habit: "header first, then respond"

## Compliance Note

This command helps fulfill the 🚨 CRITICAL requirement in CLAUDE.md that EVERY response must start with the branch header. The header provides essential context about:
- Current working branch
- Remote tracking status  
- Associated pull request (if any)

Using this command makes compliance easier and helps maintain the required workflow discipline.