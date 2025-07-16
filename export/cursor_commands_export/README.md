# Claude Commands for Cursor

This directory contains shell script equivalents of Claude's slash commands, adapted for use in Cursor or any terminal environment.

## Quick Start

1. **Make scripts executable:**
   ```bash
   chmod +x *.sh
   ```

2. **Add to PATH (recommended):**
   ```bash
   export PATH="$PATH:$(pwd)"
   ```

3. **Or create aliases:**
   ```bash
   source setup-aliases.sh
   ```

## Core Workflow

### Starting a New Feature
```bash
./nb.sh feature-name     # Create new branch
# ... make changes ...
./test.sh               # Run tests
./push.sh               # Push and create/update PR
```

### Daily Development
```bash
./context.sh            # Check current state
./header.sh             # Get branch info
./test.sh               # Run tests
./coverage.sh           # Check test coverage
```

### Completing Work
```bash
./test.sh               # Ensure tests pass
./push.sh               # Final push
./pr.sh "Description"   # Create PR if needed
./integrate.sh          # Start fresh for next task
```

## Command Categories

### Git Workflow
- `header.sh` - Branch status header
- `nb.sh` / `newbranch.sh` - New branch from main
- `push.sh` - Smart push with validation
- `pr.sh` - Create pull request
- `integrate.sh` - Fresh start with cleanup

### Testing
- `test.sh` - Run all tests + CI check
- `testui.sh` - Browser tests (mock)
- `testuif.sh` - Browser tests (real APIs)
- `testhttp.sh` - HTTP API tests
- `testi.sh` - Integration tests
- `coverage.sh` - Coverage report

### Development
- `tdd.sh` - TDD workflow guide
- `rg.sh` - Red-Green methodology
- `context.sh` - Current state info
- `learn.sh` - Document learnings

### AI-Assisted
- `think.sh` - Thinking prompts
- `execute.sh` / `e.sh` - Execution guide
- `plan.sh` - Planning template

## Important Notes

1. **Project Specific**: These scripts assume the WorldArchitect.AI project structure
2. **Dependencies**: Requires `git`, `gh` (GitHub CLI), `python`, test runners
3. **AI Commands**: Some commands provide guides rather than full automation
4. **Customization**: Modify scripts to match your workflow

## See Also

- `export.md` - Detailed documentation for all commands
- Original Claude commands in `.claude/commands/`