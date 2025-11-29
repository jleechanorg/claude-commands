# jleechanorg-pr-automation

A comprehensive GitHub PR automation system with safety limits, actionable counting, and intelligent filtering.

## ⚠️ CRITICAL: Orchestration Dependency Required

**This package requires the `orchestration` module to function correctly.**

The automation system uses `orchestration.task_dispatcher.TaskDispatcher` for orchestrated PR processing. This means:

- ✅ **For Development/Internal Use**: Clone the full WorldArchitect.AI repository where both `automation/` and `orchestration/` are available
- ❌ **Standalone PyPI Installation**: Will fail with `ModuleNotFoundError: No module named 'orchestration'` when using CLI commands
- 🔧 **Solution**: Use within the project repository where `orchestration/` is in the Python path, or wait for the package flattening refactor (tracked in issue worktree_auto3-g7h)

**Installation Context:**
```bash
# For standalone use (CLI WILL FAIL - orchestration not available):
pip install jleechanorg-pr-automation  # ❌ CLI commands fail

# For development within WorldArchitect.AI project (WORKS):
cd ~/worldarchitect.ai
pip install -e ./automation  # ✅ Full functionality
```

### Multi-CLI Agent Support

The orchestration system supports multiple AI CLI backends for autonomous PR fixing. When using the `--fixpr` mode, you can select which AI CLI handles the PR processing:

**Supported AI CLIs:**
- **Claude** (default): Anthropic's Claude Code CLI
- **Codex**: OpenAI's Codex CLI
- **Gemini**: Google's Gemini CLI (gemini-3-pro-preview model only)

**CLI Selection Methods:**

1. **Explicit Flag** (recommended for consistency):
```bash
# Force Gemini CLI for all PR fixes
jleechanorg-pr-monitor --fixpr --max-prs 5 --agent-cli gemini

# Use Codex instead
jleechanorg-pr-monitor --fixpr --max-prs 5 --agent-cli codex
```

2. **Keyword Detection** (automatic based on task description):
```bash
# Orchestration auto-detects "use gemini" keyword
# This is handled internally by the TaskDispatcher
```

3. **Default Behavior** (Claude if available):
```bash
# Uses Claude CLI by default when multiple CLIs installed
jleechanorg-pr-monitor --fixpr --max-prs 5
```

**Prerequisites for Multi-CLI:**
- For Claude: Install Claude Code CLI (see main README)
- For Codex: Ensure `codex` binary is in PATH
- For Gemini: `pip install google-gemini-cli` + `GOOGLE_API_KEY` environment variable

**Model Restrictions:**
- Gemini CLI is configured to use **ONLY gemini-3-pro-preview** model
- No other Gemini models are supported in the orchestration system

For complete CLI configuration and usage details, see the [orchestration README](../orchestration/README.md#cli-selection-methods).

## Features

- **Actionable PR Counting**: Only processes PRs that need attention, excluding already-processed ones
- **Safety Limits**: Built-in rate limiting and attempt tracking to prevent automation abuse
- **Cross-Process Safety**: Thread-safe operations with file-based persistence
- **Email Notifications**: Optional SMTP integration for automation alerts
- **Commit-Based Tracking**: Avoids duplicate processing using commit SHAs
- **Orchestrated PR Runner**: Autonomous agent-based PR fixing using TaskDispatcher
- **Multi-CLI Support**: Works with Claude, Codex, or Gemini AI agents (via orchestration)
- **Comprehensive Testing**: 200+ test cases with matrix-driven coverage

## Installation

```bash
pip install jleechanorg-pr-automation
```

### Optional Dependencies

For email notifications:
```bash
pip install jleechanorg-pr-automation[email]
```

For development:
```bash
pip install jleechanorg-pr-automation[dev]
```

## Quick Start

### Basic PR Monitoring

```python
from jleechanorg_pr_automation import JleechanorgPRMonitor

# Initialize monitor
monitor = JleechanorgPRMonitor()

# Process up to 20 actionable PRs
result = monitor.run_monitoring_cycle_with_actionable_count(target_actionable_count=20)

print(f"Processed {result['actionable_processed']} actionable PRs")
print(f"Skipped {result['skipped_count']} non-actionable PRs")
```

### Safety Management

```python
from jleechanorg_pr_automation import AutomationSafetyManager

# Initialize safety manager with data directory
safety = AutomationSafetyManager(data_dir="/tmp/automation_safety")

# Limits are configured via automation_safety_config.json inside the data directory
# or the AUTOMATION_PR_LIMIT / AUTOMATION_GLOBAL_LIMIT environment variables.

# Check if PR can be processed
if safety.can_process_pr(pr_number=123, repo="my-repo"):
    # Process PR...
    safety.record_pr_attempt(pr_number=123, result="success", repo="my-repo")
```

## Configuration

### Environment Variables

- `GITHUB_TOKEN`: GitHub personal access token (required)
- `PR_AUTOMATION_WORKSPACE`: Custom workspace directory (optional)
- `AUTOMATION_PR_LIMIT`: Maximum attempts per PR (default: 5)
- `AUTOMATION_GLOBAL_LIMIT`: Maximum global automation runs (default: 50)
- `AUTOMATION_APPROVAL_HOURS`: Hours before approval expires (default: 24)

### Email Configuration (Optional)

- `SMTP_SERVER`: SMTP server hostname
- `SMTP_PORT`: SMTP server port (default: 587)
- `EMAIL_USER`: SMTP username
- `EMAIL_PASS`: SMTP password
- `EMAIL_TO`: Notification recipient
- `EMAIL_FROM`: Sender address (defaults to EMAIL_USER)

## Command Line Interface

### PR Monitor

```bash
# Monitor all repositories
jleechanorg-pr-monitor

# Process specific repository
jleechanorg-pr-monitor --single-repo worldarchitect.ai

# Process specific PR
jleechanorg-pr-monitor --target-pr 123 --target-repo jleechanorg/worldarchitect.ai

# Dry run (discovery only)
jleechanorg-pr-monitor --dry-run
```

### Safety Manager CLI

```bash
# Check current status
automation-safety-cli status

# Clear all safety data
automation-safety-cli clear

# Check specific PR
automation-safety-cli check-pr 123 --repo my-repo
```

## Architecture

### Actionable PR Logic

The system implements intelligent PR filtering:

1. **State Check**: Only processes open PRs
2. **Commit Tracking**: Skips PRs already processed with current commit SHA
3. **Safety Limits**: Respects per-PR and global automation limits
4. **Ordering**: Processes most recently updated PRs first

### Safety Features

- **Dual Limiting**: Per-PR consecutive failure limits + global run limits
- **Cross-Process Safety**: File-based locking for concurrent automation instances
- **Attempt Tracking**: Full history of success/failure with timestamps
- **Graceful Degradation**: Continues processing other PRs if one fails

### Testing

The library includes comprehensive test coverage:

- **Matrix Testing**: All PR state combinations (Open/Closed × New/Old Commits × Processed/Fresh)
- **Actionable Counting**: Batch processing with skip exclusion
- **Safety Limits**: Concurrent access and edge cases
- **Integration Tests**: Real GitHub API interactions (optional)

## Development

```bash
# Clone repository
git clone https://github.com/jleechanorg/worldarchitect.ai.git
cd worldarchitect.ai/automation

# Install in development mode
pip install -e .[dev]

# Run tests
pytest

# Run tests with coverage
pytest --cov=jleechanorg_pr_automation

# Format code
black .
ruff check .
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## Claude Code Integration

### Slash Command Plugin

This automation system is integrated with Claude Code through a custom slash command plugin located at `.claude/commands/automation.md`. This allows seamless PR automation directly from your Claude Code sessions.

#### Installation

**Option 1: Via `/exportcommands` (Recommended)**

If you're using the WorldArchitect.AI command system, the automation command is automatically exported:

```bash
/exportcommands
```

**Option 2: Manual Installation**

Copy the automation command from this repository to your Claude Code commands directory:

```bash
# From the worldarchitect.ai repository root
# For project-specific installation
cp .claude/commands/automation.md <your-project>/.claude/commands/

# For user-wide installation (available across all projects)
cp .claude/commands/automation.md ~/.claude/commands/
```

#### Usage in Claude Code

Once installed, you can use the `/automation` command directly in Claude Code:

```bash
# Check automation status
/automation status

# Process PRs for a specific repository
/automation monitor worldarchitect.ai

# Process a specific PR
/automation process 123 --repo jleechanorg/worldarchitect.ai

# Check safety limits and configuration
/automation safety check

# Clear safety data (resets limits)
/automation safety clear
```

#### Features Available Through Claude Code

- **PR Monitoring**: Automatically discover and process actionable PRs
- **Safety Management**: Built-in safety limits prevent automation abuse
- **Actionable Counting**: Only processes PRs that need attention
- **Cross-Process Safety**: Thread-safe operations with file-based persistence
- **Email Notifications**: Optional SMTP integration for automation alerts

#### Configuration for Claude Code

The automation system uses environment variables for configuration. Set these in your shell profile or `.env` file:

```bash
# Required
export GITHUB_TOKEN="your_github_token_here"

# Optional - Customize safety limits
export AUTOMATION_PR_LIMIT=5           # Max attempts per PR (default: 5)
export AUTOMATION_GLOBAL_LIMIT=50      # Max global runs (default: 50)
export AUTOMATION_APPROVAL_HOURS=24    # Approval expiry (default: 24)

# Optional - Custom workspace
export PR_AUTOMATION_WORKSPACE="/custom/path"

# Optional - Email notifications
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT=587
export EMAIL_USER="your-email@gmail.com"
export EMAIL_PASS="your-app-password"
export EMAIL_TO="recipient@example.com"
```

#### Plugin Architecture

The automation plugin follows Claude Code's plugin architecture:

- **Slash Commands**: `.claude/commands/automation.md` - Main automation interface
- **Hooks Integration**: Can be triggered via Claude Code hooks for automated workflows
- **MCP Integration**: Compatible with Memory MCP for learning from automation patterns
- **TodoWrite Integration**: Tracks automation tasks in Claude Code's todo system

#### Advanced: Automation Hooks

You can create Claude Code hooks to automatically trigger PR automation:

**Example: Post-Push Hook** (`.claude/hooks/post-push.sh`)

```bash
#!/bin/bash
# Automatically check for PRs after pushing

# Get current repo and branch
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
BRANCH=$(git branch --show-current)

# Check if there's an open PR for this branch
PR_NUMBER=$(gh pr list --head "$BRANCH" --json number -q '.[0].number')

if [[ -n "$PR_NUMBER" ]]; then
    echo "🤖 PR #$PR_NUMBER detected - triggering automation check"
    jleechanorg-pr-monitor --target-pr "$PR_NUMBER" --target-repo "$REPO"
fi
```

**Example: Scheduled Monitoring** (Cron Job)

```bash
# Add to crontab for hourly PR monitoring
0 * * * * cd ~/worldarchitect.ai && jleechanorg-pr-monitor
```

#### Slash Command Documentation

The `/automation` slash command provides a multi-phase execution workflow:

**Phase 0: Preflight Installation & Token Check**
- Verifies `jleechanorg-pr-automation` package is installed
- Checks GitHub token environment variable
- Validates dependencies before execution

**Phase 1: Parse Action and Arguments**
- Extracts action (status, monitor, process, safety) from command
- Validates action type and parameters
- Sets defaults for missing values

**Phase 2: STATUS Action** - `/automation status`
- Displays global automation runs vs limits
- Shows per-PR attempt counts
- Reports safety configuration and active PRs

**Phase 3: MONITOR Action** - `/automation monitor [repository]`
- Discovers and processes actionable PRs
- Respects safety limits
- Reports results and skip reasons

**Phase 4: PROCESS Action** - `/automation process <pr_number> --repo <repository>`
- Processes a specific PR
- Initializes safety manager
- Records attempt results

**Phase 5: SAFETY Action** - `/automation safety <subaction>`
- `check`: Display safety limits and status
- `clear`: Reset all safety data (with warning)
- `check-pr`: Check specific PR's processability

**Phase 6: TodoWrite Integration**
- Tracks complex operations as todo items
- Updates progress in real-time
- Maintains error context

For complete execution workflow details, see `.claude/commands/automation.md` in this repository.

#### Plugin Export

When you run `/exportcommands`, the automation slash command (`.claude/commands/automation.md`) is automatically included in the export to the `jleechanorg/claude-commands` repository. This allows others to install the automation plugin in their Claude Code environments.

The export process:
1. Copies `.claude/commands/automation.md` to the commands export
2. Includes automation documentation in the exported README
3. Provides installation instructions for end users
4. Transforms project-specific paths to generic placeholders

## License

MIT License - see LICENSE file for details.

## Changelog

### 0.1.1 (2025-10-06)

- Fix daily reset of global automation limit so automation never stalls overnight
- Track latest reset timestamp in safety data for observability
- Expand safety manager tests to cover daily rollover behaviour

### 0.1.0 (2025-09-28)

- Initial release
- Actionable PR counting system
- Safety management with dual limits
- Cross-process file-based persistence
- Email notification support
- Comprehensive test suite (200+ tests)
- CLI interfaces for monitoring and safety management
