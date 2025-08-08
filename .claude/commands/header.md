# Header Command

**Purpose**: Generate and display the mandatory branch header for CLAUDE.md compliance with full git status and intelligent PR inference

**Usage**: `/header` or `/usage`

**Action**: Execute single script to show git status and generate the required branch header with API usage statistics

## Implementation

**Single Command**: `~/projects/worldarchitect.ai/claude_command_scripts/git-header.sh --with-api`

This script automatically:
1. Shows full `git status` output for complete repository context
2. Gets local branch name with sync status
3. Gets remote upstream info
4. Intelligently infers PR information:
   - Primary: Finds PR for current branch
   - Fallback: If no PR for current branch but uncommitted changes exist, suggests related open PRs
5. Gets Claude API usage statistics (remaining sessions out of 50)
6. Formats everything into the required header

**Benefits**:
- ✅ **Complete git context** - Full `git status` output shows working directory state
- ✅ **Intelligent PR inference** - Finds relevant PRs even when branch doesn't have direct PR
- ✅ **One command with usage info** - Shows sessions remaining out of monthly 50
- ✅ **Automatic formatting** - Prevents formatting errors
- ✅ **Error handling** - Gracefully handles missing upstreams/PRs
- ✅ **Usage awareness** - Never run out of sessions unexpectedly
- ✅ **Consistent output** - Same format every time

## Output Format

Shows complete repository context followed by the mandatory header format:

```
=== Git Status ===
On branch dev1754541036
Your branch is ahead of 'origin/main' by 2 commits.
  (use "git push" to publish your local commits)

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git checkout -- <file>..." to discard changes to working directory)

	modified:   claude_command_scripts/git-header.sh

no changes added to commit (use "git add -a" to commit all changes, or "git add <file>..." to update what will be committed)

[Local: <branch> | Remote: <upstream> | PR: <number> <url>]
[API: <remaining>/<limit> requests (<percentage>% remaining) | Reset: <time>]
```

Examples:
- `[Local: main | Remote: origin/main | PR: none]`
- `[API: 49/50 requests (98% remaining) | Reset: 15:08:12]`
- `[Local: feature-x | Remote: origin/main | PR: #123 https://github.com/user/repo/pull/123]`
- `[Local: dev-branch (ahead 2) | Remote: origin/main | PR: (related to #456 https://github.com/user/repo/pull/456)]`
- `[API: 25/50 requests (50% remaining) | Reset: 08:30:45]`

## Usage in Workflow

**Best Practice**: Use `/header` before ending responses to:
- See complete git repository context with **one command**
- Generate the required header with full PR inference
- Create a reminder checkpoint to include it
- Ensure consistent formatting with zero effort
- Remove all friction in compliance

**Automated Memory Aid**:
- The single command `~/projects/worldarchitect.ai/claude_command_scripts/git-header.sh` provides complete context
- Shows git status + intelligently finds relevant PRs
- No need to remember multiple separate commands
- Consistent, reliable output every time
- Perfect for developing muscle memory

**Integration**:
- End every response with the header (one simple command)
- Use when switching branches or tasks
- Make it a habit: "content first, header last"

## Compliance Note

This command helps fulfill the 🚨 CRITICAL requirement in CLAUDE.md that EVERY response must end with the branch header. The enhanced output provides essential context about:
- Complete git repository working directory state
- Current working branch with sync status
- Remote tracking status  
- Intelligently inferred PR context (direct or related)
- API usage monitoring

Using this command makes compliance easier, provides complete repository context, and helps maintain the required workflow discipline.
