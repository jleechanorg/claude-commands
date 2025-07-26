# Push Lite Command

**Purpose**: Simple push to GitHub without test server or additional automation

**Action**: Push current branch to origin and create PR if requested

**Usage**:
- `/pushlite` or `/pushl` - Push current branch to origin
- `/pushlite pr` or `/pushl pr` - Push and create PR
- `/pushlite force` or `/pushl force` - Force push to origin

**Examples**:
- `/pushl` - Pushes current branch to origin/branch-name
- `/pushl pr` - Pushes and creates PR to main
- `/pushl force` - Force pushes current branch (use with caution)

**Implementation**:
Execute: `./claude_command_scripts/commands/pushlite.sh [arguments]`

**Key Features**:
- **Smart Untracked File Handling**: Interactive options for untracked files
- **Lightweight Operation**: No test automation or server management
- **Safety Checks**: Confirms actions before execution
- **PR Integration**: Optional PR creation with auto-generated content
- **Post-Push Linting**: Non-blocking code quality checks after successful push

**Untracked Files Options**:
1. **Add all** - Stages all untracked files with smart commit messages
2. **Select files** - Choose specific files interactively
3. **Continue** - Push without adding untracked files
4. **Cancel** - Abort the push operation

**Smart Commit Messages**:
- Detects file types (tests, docs, scripts, CI tools)
- Suggests appropriate commit messages
- Allows custom messages

**Comparison with /push**:
- **`/push`**: Quality gate workflow (linting BEFORE push, blocks on failures, full automation)
- **`/pushl`**: Fast iteration workflow (push FIRST, linting after, non-blocking)

**Safety Features**:
- Force push confirmation required
- Shows file counts and status
- Validates remote access
- Reports success/failure clearly

**Use Cases**:
- Quick documentation updates
- Small fixes that don't need full test environment
- When you want manual control over automation
- Fast iteration during development
- Adding CI tools, browser dependencies, or supporting files
