# GitHub PR Automation System

**Autonomous PR fixing and code review automation for the jleechanorg organization**

## 🚀 Quick Start

```bash
# 1. Install the automation packages from PyPI
pip install jleechanorg-orchestration jleechanorg-pr-automation

# 2. Install cron entries (sets up automated workflows)
cd automation
./install_cron_entries.sh
```

> **Important:** Ensure `MINIMAX_API_KEY` is set in your environment for MiniMax CLI support.

## Overview

This automation system provides three core workflows:

1. **@codex Comment Agent** - Monitors PRs and posts intelligent automation comments
2. **FixPR Workflow** - Autonomously fixes merge conflicts and failing CI checks
3. **Codex GitHub Mentions** - Processes OpenAI Codex tasks via browser automation

All workflows use safety limits, commit tracking, and orchestrated AI agents to process PRs reliably.

---

## 🤖 Workflow 1: @codex Comment Agent

### What It Does

The @codex comment agent continuously monitors all open PRs across the jleechanorg organization and posts standardized Codex instruction comments when new commits are pushed. This enables AI assistants (@codex, @coderabbitai, @cursor) to review and improve PRs automatically.

### How It Works

```
┌─────────────────────────────────────────────────────────────┐
│  1. DISCOVERY PHASE                                         │
│  ───────────────────────────────────────────────────────────│
│  • Scan all repositories in jleechanorg organization        │
│  • Find open PRs updated in last 24 hours                   │
│  • Filter to actionable PRs (new commits, not drafts)       │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  2. COMMIT TRACKING                                         │
│  ───────────────────────────────────────────────────────────│
│  • Check if PR has new commits since last processed         │
│  • Skip if already commented on this commit SHA             │
│  • Prevent duplicate comments on same commit                │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  3. SAFETY CHECKS                                           │
│  ───────────────────────────────────────────────────────────│
│  • Verify PR hasn't exceeded attempt limits (max 10)        │
│  • Check global automation limit (max 50 runs)              │
│  • Skip if safety limits reached                            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  4. POST COMMENT                                            │
│  ───────────────────────────────────────────────────────────│
│  • Post standardized @codex instruction comment             │
│  • Include hidden commit marker: <!-- codex-automation-     │
│    commit:abc123def -->                                     │
│  • Record processing in commit history                      │
└─────────────────────────────────────────────────────────────┘
```

### Comment Template

The agent posts this standardized instruction:

```markdown
@codex @coderabbitai @cursor [AI automation] Codex will implement
the code updates while coderabbitai and cursor focus on review
support. Please make the following changes to this PR.

Use your judgment to fix comments from everyone or explain why it should
not be fixed. Use /commentreply to post ONE consolidated summary with all
responses (avoids GitHub rate limits from individual replies). Address all
comments on this PR. Fix any failing tests and resolve merge conflicts.
Push any commits needed to remote so the PR is updated.

<!-- codex-automation-commit:abc123def456 -->
```

### Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **PR Discovery** | GitHub GraphQL API | Organization-wide PR search |
| **Commit Detection** | `check_codex_comment.py` | Prevents duplicate comments |
| **Comment Posting** | GitHub REST API (`gh pr comment`) | Posts automation instructions |
| **Safety Manager** | `AutomationSafetyManager` | File-based rate limiting |
| **Scheduling** | launchd/cron | Runs every 10 minutes |

### Usage

#### CLI Commands

```bash
# Monitor all repositories (posts comments to actionable PRs)
jleechanorg-pr-monitor

# Monitor specific repository
jleechanorg-pr-monitor --single-repo your-project.com

# Process specific PR
jleechanorg-pr-monitor --target-pr 123 --target-repo $GITHUB_REPOSITORY

# Dry run (discovery only, no comments)
jleechanorg-pr-monitor --dry-run

# Check safety status
automation-safety-cli status

# Clear safety data (resets limits)
automation-safety-cli clear
```

#### Slash Command Integration

```bash
# From Claude Code
/automation status        # View automation state
/automation monitor       # Process actionable PRs
/automation safety check  # View safety limits
```

### Configuration

```bash
# Required
export GITHUB_TOKEN="your_github_token_here"

# Safety limits (defaults shown). Override via CLI flags (not environment variables):
# - jleechanorg-pr-monitor --pr-limit 10 --global-limit 50 --approval-hours 24
# - jleechanorg-pr-monitor --pr-automation-limit 10 --fix-comment-limit 10 --fixpr-limit 10
# Or persist via `automation-safety-cli` which writes `automation_safety_config.json` in the safety data dir.

# Optional - Email Notifications
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT=587
export EMAIL_USER="your-email@gmail.com"
export EMAIL_PASS="your-app-password"
export EMAIL_TO="recipient@example.com"
```

### Key Features

- ✅ **Commit-based tracking** - Only comments when new commits appear
- ✅ **Hidden markers** - Uses HTML comments to track processed commits
- ✅ **Safety limits** - Prevents automation abuse with dual limits
- ✅ **Cross-repo support** - Monitors entire organization
- ✅ **Draft PR filtering** - Skips draft PRs automatically

---

## 🔧 Workflow 2: FixPR (Autonomous PR Fixing)

### What It Does

The FixPR workflow autonomously fixes PRs that have merge conflicts or failing CI checks by spawning AI agents in isolated workspaces. Each agent analyzes the PR, reproduces failures locally, applies fixes, and pushes updates.

### How It Works

```
┌─────────────────────────────────────────────────────────────┐
│  1. PR DISCOVERY & FILTERING                                │
│  ───────────────────────────────────────────────────────────│
│  • Query PRs updated in last 24 hours                       │
│  • Filter to PRs with:                                      │
│    - mergeable: CONFLICTING                                 │
│    - failing CI checks (FAILURE, ERROR, TIMED_OUT)          │
│  • Skip PRs without blockers                                │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  2. WORKSPACE ISOLATION                                     │
│  ───────────────────────────────────────────────────────────│
│  • Clone base repository to /tmp/pr-orch-bases/             │
│  • Create worktree at /tmp/{repo}/pr-{number}-{branch}      │
│  • Checkout PR branch in isolated workspace                 │
│  • Clean previous tmux sessions with matching names         │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  3. AI AGENT DISPATCH                                       │
│  ───────────────────────────────────────────────────────────│
│  • Create TaskDispatcher with workspace config              │
│  • Spawn agent with:                                        │
│    - CLI: claude/codex/gemini (configurable)                │
│    - Task: Fix PR #{number} - resolve conflicts & tests     │
│    - Workspace: Isolated worktree path                      │
│  • Agent runs autonomously in tmux session                  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  4. AGENT WORKFLOW (Autonomous)                             │
│  ───────────────────────────────────────────────────────────│
│  • Checkout PR: gh pr checkout {pr_number}                  │
│  • Analyze failures: gh pr view --json statusCheckRollup    │
│  • Reproduce locally: Run failing tests                     │
│  • Apply fixes: Code changes to resolve issues              │
│  • Verify: Run full test suite                              │
│  • Commit & Push: git push origin {branch}                  │
│  • Write report: /tmp/orchestration_results/pr-{num}.json   │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  5. VERIFICATION                                            │
│  ───────────────────────────────────────────────────────────│
│  • Agent monitors GitHub CI for updated status              │
│  • Verifies mergeable: MERGEABLE                            │
│  • Confirms all checks passing                              │
│  • Logs success/failure to results file                     │
└─────────────────────────────────────────────────────────────┘
```

### Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **PR Query** | GitHub GraphQL API | Find PRs with conflicts/failures |
| **CI Checks** | `gh pr checks` JSON output | Detect failing tests |
| **Worktree Isolation** | `git worktree add` | Isolated PR workspaces |
| **Agent Orchestration** | `TaskDispatcher` | Spawn AI agents in tmux |
| **AI CLI** | Claude/Codex/Gemini | Execute fixes autonomously |
| **Workspace Management** | `/tmp/{repo}/{pr-branch}/` | Clean isolated environments |

### Usage

#### CLI Commands

```bash
# Fix PRs with default settings (last 24h, max 5 PRs, Claude CLI)
python3 -m orchestrated_pr_runner

# Custom time window and PR limit
python3 -m orchestrated_pr_runner --cutoff-hours 48 --max-prs 10

# Use different AI CLI
python3 -m jleechanorg_pr_automation.orchestrated_pr_runner --agent-cli codex
python3 -m jleechanorg_pr_automation.orchestrated_pr_runner --agent-cli gemini

# List actionable PRs without fixing
jleechanorg-pr-monitor --fixpr --dry-run
```

#### Slash Command Integration

```bash
# Fix specific PR (from Claude Code)
/fixpr 123

# With auto-apply for safe fixes
/fixpr 123 --auto-apply

# Pattern detection mode (fixes similar issues)
/fixpr 123 --scope=pattern
```

#### Integration with PR Monitor

```bash
# Monitor and fix in one command
jleechanorg-pr-monitor --fixpr --max-prs 5 --cli-agent claude
```

### Agent CLI Options

The FixPR workflow supports multiple AI CLIs for autonomous fixing:

| CLI | Model | Best For | Configuration |
|-----|-------|----------|---------------|
| **claude** | Claude Sonnet 4.5 | Complex refactors, multi-file changes | Default |
| **codex** | OpenAI Codex | Code generation, boilerplate fixes | Requires `codex` binary in PATH |
| **gemini** | Gemini 3 Pro | Large codebases, pattern detection | `pip install google-gemini-cli` + `GOOGLE_API_KEY` |

**Usage:**
```bash
# Explicit CLI selection
python3 -m orchestrated_pr_runner --agent-cli gemini

# Via environment variable
export AGENT_CLI=codex
python3 -m orchestrated_pr_runner
```

### Workspace Structure

```
/tmp/
├── pr-orch-bases/              # Base clones (shared)
│   ├── your-project.com/
│   └── ai_universe/
└── {repo}/                     # PR workspaces (isolated)
    ├── pr-123-fix-auth/
    ├── pr-456-merge-conflict/
    └── pr-789-test-failures/
```

### Key Features

- ✅ **Autonomous fixing** - AI agents work independently
- ✅ **Worktree isolation** - Each PR gets clean workspace
- ✅ **Multi-CLI support** - Claude, Codex, or Gemini
- ✅ **Tmux sessions** - Long-running agents in background
- ✅ **Result tracking** - JSON reports in `/tmp/orchestration_results/`
- ✅ **Safety limits** - Respects global and per-PR limits

---

## 🤝 Workflow 3: Codex GitHub Mentions Automation

### What It Does

The Codex GitHub Mentions automation processes "GitHub Mention:" tasks from OpenAI's Codex interface via browser automation. When GitHub issues or PRs are mentioned in Codex conversations, they appear as actionable tasks that require manual approval to update the branch. This workflow automates clicking the "Update branch" button for each task.

### How It Works

```
┌─────────────────────────────────────────────────────────────┐
│  1. AUTHENTICATION                                          │
│  ───────────────────────────────────────────────────────────│
│  • Connect to existing Chrome via CDP (port 9222)           │
│  • Load saved auth state from Storage State API             │
│  • Skip login if cookies/localStorage already exist         │
│  • Auth persisted to ~/.chatgpt_codex_auth_state.json       │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  2. TASK DISCOVERY                                          │
│  ───────────────────────────────────────────────────────────│
│  • Navigate to https://chatgpt.com/codex/tasks              │
│  • Find all task links matching "GitHub Mention:"           │
│  • Collect task URLs and metadata                           │
│  • Filter to first N tasks (default: 50)                    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  3. TASK PROCESSING                                         │
│  ───────────────────────────────────────────────────────────│
│  • Navigate to each task page                               │
│  • Wait for page to fully load                              │
│  • Search for "Update branch" button                        │
│  • Click button if present                                  │
│  • Log success/failure for each task                        │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  4. STATE PERSISTENCE                                       │
│  ───────────────────────────────────────────────────────────│
│  • Save cookies and localStorage to auth state file         │
│  • Auth persists across runs (no manual login required)     │
│  • Browser context reusable for future runs                 │
└─────────────────────────────────────────────────────────────┘
```

### Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Browser Automation** | Playwright (Python) | Controls Chrome via CDP |
| **CDP Connection** | Chrome DevTools Protocol | Connects to existing browser on port 9222 |
| **Auth Persistence** | Storage State API | Saves/restores cookies and localStorage |
| **Cloudflare Bypass** | Existing browser session | Avoids rate limiting by appearing as normal user |
| **Task Selection** | CSS selector `a:has-text("GitHub Mention:")` | Finds GitHub PR tasks |
| **Scheduling** | cron | Runs every hour at :15 past the hour |

### Usage

#### Prerequisites

**Start Chrome with remote debugging:**
```bash
# Kill existing Chrome instances
killall "Google Chrome" 2>/dev/null

# Start Chrome with CDP enabled (custom profile to avoid conflicts)
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/.chrome-cdp-debug" \
  > /dev/null 2>&1 &

# Verify CDP is accessible
curl -s http://localhost:9222/json/version | python3 -m json.tool

# IMPORTANT: Log in to chatgpt.com manually in the Chrome window
# The automation will save your auth state for future runs
```

#### CLI Commands

```bash
# Run automation (connects to existing Chrome on port 9222)
python3 -m jleechanorg_pr_automation.openai_automation.codex_github_mentions \
  --use-existing-browser \
  --cdp-port 9222 \
  --limit 50

# Debug mode with verbose logging
python3 -m jleechanorg_pr_automation.openai_automation.codex_github_mentions \
  --use-existing-browser \
  --cdp-port 9222 \
  --limit 50 \
  --debug

# Process only first 10 tasks
python3 -m jleechanorg_pr_automation.openai_automation.codex_github_mentions \
  --use-existing-browser \
  --cdp-port 9222 \
  --limit 10
```

#### Cron Job Integration

The automation runs automatically via cron every hour at :15 past the hour (offset from PR monitor):

```bash
# Cron entry (installed via install_jleechanorg_automation.sh)
15 * * * * jleechanorg-pr-monitor --codex-update >> \
  $HOME/Library/Logs/worldarchitect-automation/codex_automation.log 2>&1
```

**Note:** The `--codex-update` flag internally calls:
```bash
python3 -m jleechanorg_pr_automation.openai_automation.codex_github_mentions \
  --use-existing-browser --cdp-host 127.0.0.1 --cdp-port 9222 --limit 50
```

**Self-healing:** If Chrome CDP is not reachable, `--codex-update` will auto-start Chrome
using the settings below before retrying.

#### Slash Command Integration

```bash
# From Claude Code (manual run)
python3 -m jleechanorg_pr_automation.openai_automation.codex_github_mentions \
  --use-existing-browser --cdp-port 9222 --limit 50
```

### Configuration

```bash
# Required: Chrome with remote debugging on port 9222
# (See "Prerequisites" section above)

# Optional: Customize task limit (used by `jleechanorg-pr-monitor --codex-update`)
# Default: 50 (matches CLI default; max 200). Override to keep evidence/test runs fast.
# Use: `jleechanorg-pr-monitor --codex-update --codex-task-limit 200`

# Optional: Auth state file location
# Default: ~/.chatgpt_codex_auth_state.json

# Optional: CDP self-heal controls (used by jleechanorg-pr-monitor --codex-update)
export CODEX_CDP_AUTO_START=1            # default: 1 (auto-start Chrome if needed)
export CODEX_CDP_HOST=127.0.0.1          # default: 127.0.0.1
export CODEX_CDP_PORT=9222               # default: 9222
export CODEX_CDP_USER_DATA_DIR="$HOME/.chrome-automation-profile"
export CODEX_CDP_START_TIMEOUT=20        # seconds to wait for CDP after start
# Optional: custom launcher (script path). Port is appended as final arg.
export CODEX_CDP_START_SCRIPT="/path/to/start_chrome_debug.sh"
```

### Key Features

- ✅ **CDP-based automation** - Connects to existing Chrome to bypass Cloudflare
- ✅ **Persistent authentication** - Storage State API saves cookies/localStorage
- ✅ **No manual login** - Auth state persists across runs
- ✅ **Cloudflare bypass** - Appears as normal user browsing, not a bot
- ✅ **Configurable limits** - Process 1-N tasks per run
- ✅ **Robust task detection** - Handles dynamic page loading

### Troubleshooting

**Issue**: Cloudflare rate limiting (0 tasks found)
```bash
# Solution: Use existing browser via CDP instead of launching new instances
# The CDP approach connects to your logged-in Chrome session, avoiding detection

# Verify Chrome is running with CDP enabled
curl -s http://localhost:9222/json/version

# Expected output:
# {
#   "Browser": "Chrome/131.0.6778.265",
#   "Protocol-Version": "1.3",
#   "webSocketDebuggerUrl": "ws://localhost:9222/..."
# }
```

**Issue**: Auth state not persisting
```bash
# Check auth state file exists
ls -lh ~/.chatgpt_codex_auth_state.json

# Expected: ~5-6KB JSON file
# If missing: Log in manually to chatgpt.com in the CDP Chrome window
# The script will save auth state on first successful run
```

**Issue**: "Update branch" button not found
```bash
# Run with debug logging
python3 -m jleechanorg_pr_automation.openai_automation.codex_github_mentions \
  --use-existing-browser \
  --cdp-port 9222 \
  --debug

# Check if tasks are actually "GitHub Mention:" type
# Only GitHub PR tasks have "Update branch" buttons
```

**Issue**: Chrome CDP connection fails
```bash
# Verify Chrome is running with correct flags
ps aux | grep "remote-debugging-port=9222"

# If not running, start Chrome with CDP:
killall "Google Chrome" 2>/dev/null
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/.chrome-cdp-debug" &
```

**Issue**: Cron job failing with "unrecognized arguments: --codex-update"
```bash
# This happens when installed PyPI package is older than source code
# DO NOT use editable install (pip install -e .) for cron jobs - breaks in multi-worktree setups

# Option 1: Install from git (pin to tag or commit for reproducibility)
pip install "git+https://github.com/$GITHUB_REPOSITORY.git@<tag-or-commit>#subdirectory=automation"

# Option 2: Build and install from source (NOT editable - safe for cron)
cd automation && pip install .

# Option 3: Wait for PyPI package update (safest)
# Check your installed version:
pip show jleechanorg-pr-automation
# See latest releases on PyPI: https://pypi.org/project/jleechanorg-pr-automation/

# Verify flag exists
jleechanorg-pr-monitor --help | grep codex-update
```

---

## Installation

### Production / Cron Jobs / Normal Usage (RECOMMENDED)

```bash
# Basic installation from PyPI (stable, production-ready)
pip install jleechanorg-pr-automation

# With email notifications
pip install jleechanorg-pr-automation[email]
```

✅ **Use this for:**
- Cron jobs and scheduled automation
- Production deployments
- Multi-worktree development
- Any system where code stability matters

### Development Only (Active Code Changes)

```bash
# Install in editable mode (links to local source)
cd automation && pip install -e .

# With optional dependencies
cd automation && pip install -e .[email,dev]
```

⚠️ **ONLY use editable installs when:**
- You are actively modifying the package source code
- You need immediate reflection of code changes without reinstalling
- You are working in a single worktree

🚫 **DO NOT use editable installs for:**
- Cron jobs (will break when source directory changes)
- Production deployments (unstable source code)
- Multi-worktree setups (editable install points to single worktree)
- Scheduled automation (no control over which worktree is active)

### When PyPI Package is Outdated

If you need features not yet in PyPI:

```bash
# Option 1: Install from git (pin to tag or commit for reproducibility)
pip install "git+https://github.com/$GITHUB_REPOSITORY.git@<tag-or-commit>#subdirectory=automation"

# Option 2: Build and install from source (NOT editable)
cd automation
pip install .  # Note: NOT pip install -e .

# Option 3: Wait for PyPI package update (safest)
# Check your installed version: pip show jleechanorg-pr-automation
# See latest releases on PyPI: https://pypi.org/project/jleechanorg-pr-automation/
```

### Native Scheduler Installation

```bash
# Install native schedulers from the repo root
./automation/install.sh

# Preview without mutating schedulers
./automation/install.sh --dry-run

# Validate native services after install
launchctl print "gui/$(id -u)/ai.worldarchitect.pr-automation.pr-monitor"   # macOS
systemctl --user status worldarchitect-pr-automation-pr-monitor.timer        # Linux

# Inspect OpenClaw cron state after migration
openclaw cron list --all --json
```

`./automation/install.sh` installs exactly five PR automation jobs as native schedulers:
- `pr-monitor`
- `fix-comment`
- `comment-validation`
- `codex-api`
- `fixpr`

It does not install or modify the Slack check-in jobs or `ai-orch-session-keepalive`.
After the native scheduler verifies successfully, it disables matching OpenClaw cron
jobs by exact name so the same automation does not run twice.

### Crontab Management

Use the `restore_crontab.sh` script to manage cron jobs for all three automation workflows:

```bash
# Dry run (preview what will be restored)
cd automation
./restore_crontab.sh --dry-run

# Interactive restore (prompts for confirmation)
./restore_crontab.sh

# Force restore (no prompts)
./restore_crontab.sh --force

# View current crontab
crontab -l

# Restore from backup (if needed)
crontab ~/.crontab_backup_YYYYMMDD_HHMMSS
```

**Migrated PR Automation Jobs:**

| Schedule | Command | Purpose |
|----------|---------|---------|
| Every hour (`:00`) | `jleechanorg-pr-monitor --max-prs 10` | Workflow 1: PR monitoring |
| Every hour (`:45`) | `jleechanorg-pr-monitor --fix-comment --cli-agent minimax --max-prs 3` | Workflow 2: Fix-comment automation |
| Every 30 minutes | `jleechanorg-pr-monitor --comment-validation --max-prs 10` | Workflow 3: Comment validation |
| Every hour (`:30`) | `jleechanorg-pr-monitor --codex-api --codex-apply-and-push --codex-task-limit 10` | Workflow 4: Codex API automation |
| Every 30 minutes | `jleechanorg-pr-monitor --fixpr --max-prs 10 --cli-agent minimax` | Workflow 5: Fix PRs autonomously |

---

## Safety System

Both workflows use `AutomationSafetyManager` for rate limiting:

### Dual Limits

1. **Per-PR Limit**: Max 10 consecutive attempts per PR (internal safety)
2. **Global Limit**: Max 50 total automation runs per day
3. **Workflow-Specific Comment Limits**: Each workflow has its own limit for automation comments per PR (some workflows may not currently post comments, but have limits reserved for future compatibility):
   - **PR Automation**: 10 comments (default)
   - **Fix-Comment**: 10 comments (default)
   - **Codex Update**: 10 comments (default; does not currently post PR comments—limit reserved for future compatibility)
   - **FixPR**: 10 comments (default)

   These limits prevent one workflow from blocking others. Configure via CLI flags:
   - `--pr-automation-limit`
   - `--fix-comment-limit`
   - `--fixpr-limit`

   **Note**: Workflow comment counting is marker-based:
   - PR automation comments: `codex-automation-commit`
   - Fix-comment queued runs: `fix-comment-automation-run` (separate from completion marker)
   - Fix-comment completion/review requests: `fix-comment-automation-commit`
   - FixPR queued runs: `fixpr-automation-run`

### Safety Data Storage

```
~/Library/Application Support/worldarchitect-automation/
├── automation_safety_data.json    # Attempt tracking
└── pr_history/                     # Commit tracking per repo
    ├── your-project.com/
    │   ├── main.json
    │   └── feature-branch.json
    └── ai_universe/
        └── develop.json
```

### Safety Commands

```bash
# Check current status
automation-safety-cli status

# Example output:
# Global runs: 23/50
# Requires approval: False
# PR attempts:
#   your-project.com-1634: 2/10 (OK)
#   ai_universe-42: 10/10 (BLOCKED)

# Clear all data (reset limits)
automation-safety-cli clear

# Check specific PR
automation-safety-cli check-pr 123 --repo your-project.com
```

---

## Architecture Comparison

| Feature | @codex Comment Agent | FixPR Workflow | Codex GitHub Mentions |
|---------|---------------------|----------------|----------------------|
| **Trigger** | New commits on open PRs | Merge conflicts or failing checks | Codex tasks queue |
| **Action** | Posts instruction comment | Autonomously fixes code | Clicks "Update branch" buttons |
| **Execution** | Quick (API calls only) | Long-running (agent in tmux) | Medium (browser automation) |
| **Workspace** | None (comment-only) | Isolated git worktree | Chrome CDP session |
| **AI CLI** | N/A (GitHub API) | Claude/Codex/Gemini | N/A (Playwright) |
| **Output** | GitHub PR comment | Code commits + JSON report | Browser button clicks |
| **Schedule** | Every hour | Every 30 minutes | Every hour at :15 |

---

## Environment Variables

### Required

```bash
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
```

### Optional

```bash
# Workspace configuration
export PR_AUTOMATION_WORKSPACE="/custom/path"

# Email notifications
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT=587
export EMAIL_USER="your@email.com"
export EMAIL_PASS="app-password"
export EMAIL_TO="recipient@email.com"

# Agent CLI selection (for FixPR)
export AGENT_CLI="claude"              # or "codex" or "gemini"
export GEMINI_MODEL="gemini-3-pro-preview"
```

---

## Development

### Running Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=jleechanorg_pr_automation

# Specific test suite
pytest automation/jleechanorg_pr_automation/tests/test_pr_filtering_matrix.py
```

### Code Quality

```bash
# Format code
black .
ruff check .

# Type checking
mypy jleechanorg_pr_automation
```

---

## Troubleshooting

### @codex Comment Agent

**Issue**: No PRs discovered
```bash
# Check GitHub authentication
gh auth status

# Verify organization access
gh repo list jleechanorg --limit 5
```

**Issue**: Duplicate comments on same commit
```bash
# Check commit marker detection
python3 -c "from jleechanorg_pr_automation.check_codex_comment import decide; print(decide('<!-- codex-automation-commit:', '-->'))"
```

### FixPR Workflow

**Issue**: Worktree creation fails
```bash
# Clean stale worktrees
cd ~/your-project.com
git worktree prune

# Remove old workspace
rm -rf /tmp/your-project.com/pr-*
```

**Issue**: Agent not spawning
```bash
# Check tmux sessions
tmux ls

# View agent logs
ls -la /tmp/orchestration_results/
```

**Issue**: Wrong AI CLI used
```bash
# Verify CLI availability
which claude codex gemini

# Set explicit CLI
export AGENT_CLI=claude
python3 -m orchestrated_pr_runner
```

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass (`pytest`)
5. Format code (`black . && ruff check .`)
6. Submit a pull request

---

## License

MIT License - see LICENSE file for details.

---

## Changelog

### 0.2.21 (Latest)
- Refined Codex updater logging and update-branch click handling.

### 0.2.20
- Stabilized Codex updater tab reuse and recovery when pages close mid-run.
- Added login verification guard and extra diagnostics for tab switching.

### 0.2.19
- Fixed `cleanup()` indentation so `CodexGitHubMentionsAutomation` can release resources.
- Note: version 0.2.18 was intentionally skipped (no public release).

### 0.2.5
- Enhanced @codex comment detection with actor pattern matching
- Improved commit marker parsing for multiple AI assistants
- Added Gemini CLI support for FixPR workflow

### 0.1.1
- Fixed daily reset of global automation limit
- Added last reset timestamp tracking

### 0.1.0
- Initial release with @codex comment agent and FixPR workflow
- Comprehensive safety system with dual limits
- Cross-organization PR monitoring

## OpenClaw Mission Control Integration — Implementation Roadmap

Status: **planned / in-progress**

### Phase 0 — Baseline + scope lock
- Confirm current entrypoint(s) used by OpenClaw for long-running tasks.
- Define the canonical Mission Control task payload shape (`title`, `description`, `status`, metadata fields).
- Document success criteria for "queued" acknowledgment path (<2s return, task ID included).

### Phase 1 — Task creation path
- Add a single hardened shell/Python entrypoint that:
  - validates required env vars (`MISSION_CONTROL_BASE_URL`, `MISSION_CONTROL_TOKEN`, `MISSION_CONTROL_BOARD_ID`),
  - posts to `/api/v1/boards/{board_id}/tasks`,
  - returns normalized output with task ID and board URL.
- Add retry/backoff and clear error taxonomy (auth, network, validation).

### Phase 2 — Context expansion + redaction
- Implement message-history expansion for "as discussed"/"continue" requests before dispatch.
- Add strict redaction pass for secrets/PII prior to writing MC task descriptions.
- Add tests for secret patterns and redaction invariants.

### Phase 3 — Poller + execution bridge
- Ensure Task Poller reliably picks inbox tasks and transitions state (`inbox` → `in_progress` → `done`/`blocked`).
- Emit concise execution logs with task IDs and agent session mappings.
- Add watchdog behavior for stalled tasks.

### Phase 4 — Observability + reliability hardening
- Add health checks for Mission Control API reachability and auth validity.
- Add metrics/log counters: queued count, dispatch latency, success/failure rates.
- Add cron/launchd-safe lock handling for pollers and watchdog scripts.

### Phase 5 — Verification + rollout
- Add end-to-end tests for create-task + poller transitions.
- Validate against real board in staging mode, then production mode.
- Ship runbook: setup, recovery, rollback, and common failure signatures.

### Definition of Done
- A long-running user request is acknowledged in-thread with a real task ID.
- Task appears in Mission Control inbox and is automatically dispatched.
- State transitions are visible and auditable.
- Tests + docs cover normal flow and failure modes.
