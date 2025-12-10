# GitHub PR Automation System

**Autonomous PR fixing and code review automation for the $GITHUB_ORG organization**

## Overview

This automation system provides two core workflows:

1. **@codex Comment Agent** - Monitors PRs and posts intelligent automation comments
2. **FixPR Workflow** - Autonomously fixes merge conflicts and failing CI checks

Both workflows use safety limits, commit tracking, and orchestrated AI agents to process PRs reliably.

---

## 🤖 Workflow 1: @codex Comment Agent

### What It Does

The @codex comment agent continuously monitors all open PRs across the $GITHUB_ORG organization and posts standardized Codex instruction comments when new commits are pushed. This enables AI assistants (@codex, @coderabbitai, @copilot, @cursor) to review and improve PRs automatically.

### How It Works

```
┌─────────────────────────────────────────────────────────────┐
│  1. DISCOVERY PHASE                                         │
│  ───────────────────────────────────────────────────────────│
│  • Scan all repositories in $GITHUB_ORG organization        │
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
│  • Verify PR hasn't exceeded attempt limits (max 5)         │
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
@codex @coderabbitai @copilot @cursor [AI automation] Codex will implement
the code updates while coderabbitai, copilot, and cursor focus on review
support. Please make the following changes to this PR.

Use your judgment to fix comments from everyone or explain why it should
not be fixed. Follow binary response protocol - every comment needs "DONE"
or "NOT DONE" classification explicitly with an explanation. Address all
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
$GITHUB_ORG-pr-monitor

# Monitor specific repository
$GITHUB_ORG-pr-monitor --single-repo your-project.com

# Process specific PR
$GITHUB_ORG-pr-monitor --target-pr 123 --target-repo $GITHUB_ORG/your-project.com

# Dry run (discovery only, no comments)
$GITHUB_ORG-pr-monitor --dry-run

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

# Optional - Safety Limits
export AUTOMATION_PR_LIMIT=5           # Max attempts per PR (default: 5)
export AUTOMATION_GLOBAL_LIMIT=50      # Max global runs (default: 50)
export AUTOMATION_APPROVAL_HOURS=24    # Approval expiry (default: 24)

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
python3 -m $GITHUB_ORG_pr_automation.orchestrated_pr_runner --agent-cli codex
python3 -m $GITHUB_ORG_pr_automation.orchestrated_pr_runner --agent-cli gemini

# List actionable PRs without fixing
$GITHUB_ORG-pr-monitor --fixpr --dry-run
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
$GITHUB_ORG-pr-monitor --fixpr --max-prs 5 --agent-cli claude
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

## Installation

### From PyPI

```bash
# Basic installation
pip install $GITHUB_ORG-pr-automation

# With email notifications
pip install $GITHUB_ORG-pr-automation[email]

# For development
pip install $GITHUB_ORG-pr-automation[dev]
```

### From Source (Development)

```bash
# Clone and install from repository
cd ~/your-project.com/automation
pip install -e .

# With optional dependencies
pip install -e .[email,dev]
```

### macOS Automation (Scheduled Monitoring)

```bash
# Install launchd service
./automation/install_$GITHUB_ORG_automation.sh

# Verify service
launchctl list | grep $GITHUB_ORG

# View logs
tail -f ~/Library/Logs/automation/$GITHUB_ORG_pr_monitor.log
```

---

## Safety System

Both workflows use `AutomationSafetyManager` for rate limiting:

### Dual Limits

1. **Per-PR Limit**: Max 5 consecutive attempts per PR
2. **Global Limit**: Max 50 total automation runs per day

### Safety Data Storage

```
~/Library/Application Support/automation/
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
#   your-project.com-1634: 2/5 (OK)
#   ai_universe-42: 5/5 (BLOCKED)

# Clear all data (reset limits)
automation-safety-cli clear

# Check specific PR
automation-safety-cli check-pr 123 --repo your-project.com
```

---

## Architecture Comparison

| Feature | @codex Comment Agent | FixPR Workflow |
|---------|---------------------|----------------|
| **Trigger** | New commits on open PRs | Merge conflicts or failing checks |
| **Action** | Posts instruction comment | Autonomously fixes code |
| **Execution** | Quick (API calls only) | Long-running (agent in tmux) |
| **Workspace** | None (comment-only) | Isolated git worktree |
| **AI CLI** | N/A (GitHub API) | Claude/Codex/Gemini |
| **Output** | GitHub PR comment | Code commits + JSON report |

---

## Environment Variables

### Required

```bash
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
```

### Optional

```bash
# Safety limits
export AUTOMATION_PR_LIMIT=5           # Default: 5
export AUTOMATION_GLOBAL_LIMIT=50      # Default: 50
export AUTOMATION_APPROVAL_HOURS=24    # Default: 24

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
pytest --cov=$GITHUB_ORG_pr_automation

# Specific test suite
pytest automation/$GITHUB_ORG_pr_automation/tests/test_pr_filtering_matrix.py
```

### Code Quality

```bash
# Format code
black .
ruff check .

# Type checking
mypy $GITHUB_ORG_pr_automation
```

---

## Troubleshooting

### @codex Comment Agent

**Issue**: No PRs discovered
```bash
# Check GitHub authentication
gh auth status

# Verify organization access
gh repo list $GITHUB_ORG --limit 5
```

**Issue**: Duplicate comments on same commit
```bash
# Check commit marker detection
python3 -c "from $GITHUB_ORG_pr_automation.check_codex_comment import decide; print(decide('<!-- codex-automation-commit:', '-->'))"
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

### 0.2.5 (Latest)
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
