# Claude Commands Export for Cursor

This document contains shell script equivalents of Claude slash commands for use in Cursor. Note that some Claude-specific features (like TodoWrite, sequential thinking, and subagents) cannot be directly replicated in shell scripts, but the core functionality has been approximated where possible.

## Installation

1. Copy all shell scripts from this directory to a location in your PATH
2. Make them executable: `chmod +x *.sh`
3. Use this document as a reference for command usage in Cursor

## Command Conversion Notes

- Commands that rely on Claude's AI capabilities have been converted to interactive prompts or simplified workflows
- Git operations, test runs, and file operations have been preserved
- Some commands provide templates or guidelines rather than full automation

## Commands

### Git & Workflow Commands

#### header.sh
Generate the mandatory branch header showing current git status.
```bash
./header.sh
```
Output format: `[Local: branch | Remote: upstream | PR: #123 url]`

#### newbranch.sh (alias: nb.sh)
Create a new branch from latest main. Ensures clean working directory.
```bash
./newbranch.sh [branch-name]  # Custom branch name
./newbranch.sh                # Auto-generated dev{timestamp}
./nb.sh feature-xyz           # Using alias
```

#### integrate.sh
Create fresh branch from main and cleanup test servers. Stops current branch's test server and creates new branch.
```bash
./integrate.sh                # Creates dev{timestamp} branch
./integrate.sh feature-name   # Creates custom branch
./integrate.sh --force        # Override uncommitted changes check
```

#### push.sh
Pre-push review, validation, and PR update. Checks for untracked files, runs tests, pushes changes, and updates PR.
```bash
./push.sh
```
Features:
- Prompts to add untracked files
- Runs test suite before push
- Creates PR if none exists
- Shows test server startup info

#### pr.sh
Create a pull request from the current branch with automatic test validation.
```bash
./pr.sh "Add dark mode toggle to settings"
./pr.sh "Fix user validation bug"
```
Requirements:
- Must be on feature branch (not main)
- All tests must pass
- No uncommitted changes

### Testing Commands

#### test.sh
Run full test suite and check GitHub CI status.
```bash
./test.sh
```
Runs local tests and checks PR's CI status if available.

#### testui.sh
Run browser UI tests with mock APIs (no costs).
```bash
./testui.sh
```
Uses Puppeteer/Playwright for real browser automation.

#### testhttp.sh
Run HTTP API tests with mock APIs.
```bash
./testhttp.sh
```
Tests HTTP endpoints without browser automation.

#### coverage.sh
Generate test coverage report.
```bash
./coverage.sh       # HTML format (default)
./coverage.sh text  # Text format
```
Report location: `/tmp/worldarchitectai/coverage/index.html`

### AI-Assisted Commands

#### think.sh
Sequential thinking command (requires AI assistant).
```bash
./think.sh "What's wrong with this code?"
./think.sh light "Quick bug analysis"
./think.sh deep "Complex architecture design"
```
Thinking levels: light (3-4), medium (5-6), deep (7-8), ultra (10+)

#### execute.sh (aliases: e.sh, plan.sh)
Strategic task execution (requires AI assistant).
```bash
./execute.sh "Implement JSON backend support"
./e.sh "Refactor authentication system"
./plan.sh "Design new feature architecture"
```
Provides manual checklist for complex task execution.

### Utility Commands

#### learn.sh
Document learnings and improvements.
```bash
./learn.sh "Always validate user input before processing"
./learn.sh "Use constants instead of magic strings"
```
Appends to learnings.md with timestamp and branch info.

## Quick Reference

| Command | Purpose | Usage |
|---------|---------|-------|
| `header.sh` | Git branch header | `./header.sh` |
| `nb.sh` | New branch from main | `./nb.sh [name]` |
| `integrate.sh` | Fresh branch + cleanup | `./integrate.sh [name]` |
| `push.sh` | Validate & push changes | `./push.sh` |
| `pr.sh` | Create pull request | `./pr.sh "description"` |
| `test.sh` | Run all tests | `./test.sh` |
| `testui.sh` | Browser UI tests | `./testui.sh` |
| `testhttp.sh` | HTTP API tests | `./testhttp.sh` |
| `coverage.sh` | Test coverage report | `./coverage.sh` |
| `think.sh` | AI thinking mode | `./think.sh [level] "query"` |
| `execute.sh` | Task execution | `./execute.sh "task"` |
| `learn.sh` | Document learnings | `./learn.sh "learning"` |

## Integration with Cursor

1. **Add scripts to PATH**: 
   ```bash
   export PATH="$PATH:/path/to/cursor_commands_export"
   ```

2. **Create aliases in .bashrc/.zshrc**:
   ```bash
   alias claude-header="/path/to/cursor_commands_export/header.sh"
   alias claude-test="/path/to/cursor_commands_export/test.sh"
   alias claude-pr="/path/to/cursor_commands_export/pr.sh"
   ```

3. **AI-Dependent Commands**: For think.sh and execute.sh, use Cursor's AI assistant with the provided prompts.

## Additional Scripts Needed

Some Claude commands don't have direct shell equivalents:
- **/tdd**, **/rg**, **/4layer** - Development methodologies (use as guidelines)
- **/handoff** - Requires AI analysis 
- **/milestones**, **/roadmap** - Project management (manual process)
- **Test variants** (teste, tester, testerc, testuif, testhttpf, testi) - Can be created as variations of test scripts

## Extending the Scripts

Feel free to modify these scripts to match your workflow:
- Add project-specific test commands
- Customize PR templates
- Add pre-push hooks
- Integrate with your CI/CD pipeline
