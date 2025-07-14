# Slash Command Scripts

## Overview

These scripts provide **deterministic, reliable implementations** of Claude Code slash commands. Instead of Claude interpreting commands differently each time, these scripts ensure consistent behavior.

## Problem Solved

Claude often:
- Forgets steps in complex workflows
- Executes commands differently each time
- Misses error checking
- Provides inconsistent output

These scripts fix that by providing exact, tested implementations.

## Available Command Scripts

### 🔄 `/integrate` → `integrate.sh`
**Purpose**: Reliable integration workflow
```bash
./claude_command_scripts/commands/integrate.sh [--help]
```
- Stashes uncommitted changes
- Updates main branch
- Creates new dev[timestamp] branch
- Shows clear next steps

### 📤 `/push` → `push.sh`
**Purpose**: Complete push workflow with PR management
```bash
./claude_command_scripts/commands/push.sh [--help]
```
- Pre-push validation
- Runs tests (if available)
- Pushes to remote
- Updates PR description
- Shows test server instructions

### 🧹 `/bclean` → `branch-cleanup.sh`
**Purpose**: Safe branch cleanup
```bash
./claude_command_scripts/commands/branch-cleanup.sh [--dry-run] [--force] [--help]
```
- Checks for associated PRs
- Identifies unpushed commits
- Only deletes truly safe branches
- Dry-run mode for safety

### 🌿 `/nb` → `new-branch.sh`
**Purpose**: Consistent branch creation
```bash
# Create dev branch
./claude_command_scripts/commands/new-branch.sh [--help]

# Create feature branch
./claude_command_scripts/commands/new-branch.sh feature user-auth

# Create and push with PR
./claude_command_scripts/commands/new-branch.sh fix login-bug --pr
```
- Consistent naming conventions
- Optional PR creation
- Stash handling
- Clear next steps

### 🌐 `/testui` → `test-ui.sh`
**Purpose**: Run browser tests with mock APIs
```bash
./claude_command_scripts/commands/test-ui.sh [--help]
./claude_command_scripts/commands/test-ui.sh --specific test_homepage.py
```
- Uses Playwright for browser automation
- Mock APIs to avoid costs
- Screenshots on failures
- Test server on port 6006

### 🌐 `/testuif` → `test-ui-full.sh`
**Purpose**: Run browser tests with REAL APIs (costs money!)
```bash
./claude_command_scripts/commands/test-ui-full.sh --confirm [--help]
```
- ⚠️ WARNING: Makes real API calls
- Full end-to-end browser testing
- Requires --confirm flag
- Use sparingly

### 🔌 `/testhttp` → `test-http.sh`
**Purpose**: Run HTTP/API tests with mock responses
```bash
./claude_command_scripts/commands/test-http.sh [--help]
./claude_command_scripts/commands/test-http.sh --port 8090
```
- Direct HTTP endpoint testing
- No browser overhead
- Fast API contract validation
- Custom port support

### 🔌 `/testhttpf` → `test-http-full.sh`
**Purpose**: Run HTTP tests with REAL APIs (costs money!)
```bash
./claude_command_scripts/commands/test-http-full.sh --confirm [--help]
```
- ⚠️ WARNING: Makes real API calls
- Tests real API behavior
- Requires --confirm flag

### 🔗 `/testi` → `test-integration.sh`
**Purpose**: Run integration tests
```bash
./claude_command_scripts/commands/test-integration.sh [--help]
./claude_command_scripts/commands/test-integration.sh --real-apis
```
- End-to-end workflow testing
- Multiple component validation
- Optional real API mode
- Default uses mocks

## Installation

No installation needed! These scripts are part of the repository.

1. Scripts are in `claude_command_scripts/commands/`
2. Make them executable (already done)
3. Claude Code will use them automatically

## How It Works

Instead of Claude interpreting:
```
/integrate
```

Claude simply runs:
```bash
./claude_command_scripts/commands/integrate.sh
```

This ensures the EXACT same behavior every time.

## Benefits

1. **Reliability**: Same result every time
2. **Speed**: No thinking required, just execution
3. **Safety**: Built-in error checking and validation
4. **Clarity**: Clear output and next steps
5. **Testability**: Scripts can be tested independently

## Adding New Command Scripts

1. Create script in `claude_command_scripts/commands/`
2. Make it executable: `chmod +x script.sh`
3. Follow the pattern:
   - Clear output with colors
   - Error checking
   - Help text
   - Next steps

## Usage in Claude Code

When these scripts are integrated into Claude's slash commands, you'll just type:
- `/integrate` - Claude runs integrate.sh
- `/push` - Claude runs push.sh
- `/bclean` - Claude runs branch-cleanup.sh
- `/nb feature auth` - Claude runs new-branch.sh with arguments

## Testing

### Testing Individual Scripts
Test any script directly:
```bash
# Test integration workflow
./claude_command_scripts/commands/integrate.sh

# Test branch cleanup in dry-run mode
./claude_command_scripts/commands/branch-cleanup.sh --dry-run

# Test new branch creation
./claude_command_scripts/commands/new-branch.sh feature test-feature

# Get help for any script
./claude_command_scripts/commands/test-ui.sh --help
```

### Validating All Scripts
Run the validation test suite to ensure all scripts are working:
```bash
# Validate all command scripts
./claude_command_scripts/test_command_scripts.sh
```

This validation suite checks:
- ✓ Scripts are executable
- ✓ Bash syntax is valid
- ✓ Help flags work correctly
- ✓ Error handling is enabled
- ✓ Naming conventions are followed

### 📤 `/handoff` → `handoff.sh`
**Purpose**: Structured task handoff with complete documentation
```bash
./claude_command_scripts/commands/handoff.sh task_name "description"
./claude_command_scripts/commands/handoff.sh logging_fix "Add file logging configuration"
```
- Creates handoff-[task] branch with analysis
- Generates complete scratchpad with implementation plan
- Creates GitHub PR with ready-to-implement status
- Updates roadmap.md with task tracking
- Provides copy-paste worker prompt
- Returns you to your original working branch

## Future Commands

Planned scripts for other commands:
- `/review` → `pr-review.sh` - Extract all PR comments
- `/test*` → Test runner scripts
- `/ghfix` → `fix-github-tests.sh`
- `/learn` → `capture-learning.sh`

## Contributing

When adding new scripts:
1. Keep them focused on one task
2. Use clear output with colors
3. Include error handling
4. Provide --help option
5. Show next steps
6. Make them idempotent (safe to run multiple times)