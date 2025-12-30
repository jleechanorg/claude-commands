# jleechanorg Cross-Organization PR Automation

## 🎯 Overview

A sophisticated automation system that monitors **ALL open PRs across the entire jleechanorg organization** using isolated worktrees and comprehensive safety limits.

## 🏢 Organization Coverage

**Monitors ALL repositories in jleechanorg:**
- ai_universe (4 open PRs)
- ai_universe_frontend (2 open PRs)
- worldarchitect.ai (30 open PRs)
- claude-commands (1 open PR)
- projects_fake_repo (1 open PR)
- ai_web_crawler (1 open PR)
- claude-commands-deprecated (3 open PRs)
- enhanced-claude-cli (1 open PR)
- claude_llm_proxy (1 open PR)
- **Total: 44 open PRs discovered**

## 🔄 Worktree Isolation Architecture

### Independent Processing
Each PR gets its own isolated environment:

```
~/tmp/jleechanorg-pr-workspaces/
├── ai_universe-pr-11/           # Isolated worktree for PR #11
├── worldarchitect-ai-pr-1634/   # Isolated worktree for PR #1634
├── claude-commands-pr-42/       # Isolated worktree for PR #42
└── [repo-name]-pr-[number]/     # Pattern for all PRs
```

### Branch Management
- **Existing Local Branch**: Checks out existing local branch
- **Remote Branch Only**: Creates local branch tracking remote
- **Automatic Sync**: Ensures remote target matches local branch
- **Clean Workspace**: Fresh worktree per processing cycle

## 🛡️ Enhanced Safety System

### Multi-Level Protection
1. **Per-PR Limits**: Max 10 attempts per `repo-pr` combination
2. **Global Limits**: Max 50 total automation runs across all repos
3. **Manual Approval**: Required after global limit reached
4. **Email Notifications**: Automatic alerts at safety thresholds

### Safety Tracking
```bash
# Check overall automation status
python3 automation/automation_safety_manager.py --status

# Example output:
# Global runs: 23/50
# Requires approval: False
# Has approval: False
# PR attempts:
#   ai_universe-11: 2/10 (OK)
#   worldarchitect-ai-1634: 1/10 (OK)
#   claude-commands-42: 10/10 (BLOCKED)
```

## 🚀 Installation & Setup

### Prerequisites
```bash
# GitHub CLI with organization access
brew install gh
gh auth login

# Verify organization access
gh repo list jleechanorg --limit 5
```

### Installation
```bash
# One-command setup
./automation/install_jleechanorg_automation.sh

# Verify service
launchctl list | grep jleechanorg
```

## ⚙️ Processing Workflow

### Discovery Phase (Every 10 minutes)
1. **Organization Scan**: `gh repo list jleechanorg` discovers all repositories
2. **PR Discovery**: `gh pr list --repo [repo]` finds open PRs per repository
3. **Safety Check**: Validates global and per-PR attempt limits
4. **Priority Queue**: Orders PRs for processing (max 10 per cycle)

### Processing Phase (Per PR)
1. **Worktree Creation**: `git worktree add [workspace] [branch]`
2. **Branch Sync**: Ensures local branch tracks correct remote
3. **Codex Instruction Comment**: Posts the Codex directive once per head commit, appending a hidden commit marker so future automation passes only re-request help after new commits are pushed.
4. **Result Tracking**: Records success/failure for safety counters
5. **Workspace Cleanup**: `git worktree remove [workspace]`

### Safety Recording
1. **Attempt Tracking**: Records success/failure per PR
2. **Global Counter**: Tracks total automation runs
3. **Limit Enforcement**: Blocks processing when limits reached
4. **Notification System**: Emails when manual approval needed

## 🔧 Configuration

### Environment Variables
```bash
# Optional: Custom workspace location
export PR_AUTOMATION_WORKSPACE=/custom/path/to/workspaces

# Safety limits (defaults shown)
export AUTOMATION_PR_LIMIT=10       # Max attempts per PR
export AUTOMATION_GLOBAL_LIMIT=50   # Max total runs

# Email notifications
export SMTP_SERVER=smtp.gmail.com
export SMTP_USERNAME=your_email@gmail.com
export SMTP_PASSWORD=your_app_password
export MEMORY_EMAIL_FROM=automation@jleechanorg.com
export MEMORY_EMAIL_TO=admin@jleechanorg.com
```

### Schedule Modification
Edit launchd plist for different intervals:
```xml
<!-- Every 5 minutes -->
<key>StartInterval</key>
<integer>300</integer>

<!-- Every 30 minutes -->
<key>StartInterval</key>
<integer>1800</integer>
```

## 🧪 Testing & Validation

### Dry Run Testing
```bash
# Test PR discovery only
python3 automation/jleechanorg_pr_monitor.py --dry-run

# Test specific repository
python3 automation/jleechanorg_pr_monitor.py --dry-run --single-repo ai_universe

# Limited PR testing
python3 automation/jleechanorg_pr_monitor.py --dry-run --max-prs 3
```

### Live Processing
```bash
# Single manual run
python3 automation/jleechanorg_pr_monitor.py

# Monitor real-time
tail -f ~/Library/Logs/worldarchitect-automation/jleechanorg_pr_monitor.log
```

## 📊 Monitoring & Management

### Service Status
```bash
# Check service status
launchctl list | grep jleechanorg

# Recent automation logs
tail -f ~/Library/Logs/worldarchitect-automation/jleechanorg_pr_monitor.log

# Safety status across all repos
python3 automation/automation_safety_manager.py --status
```

### Manual Intervention
```bash
# Grant approval for continued automation
python3 automation/automation_safety_manager.py --approve admin@jleechanorg.com

# Check specific PR can be processed
python3 automation/automation_safety_manager.py --check-pr ai_universe-11

# Reset PR attempts (if needed)
python3 automation/automation_safety_manager.py --record-pr ai_universe-11 success
```

### Service Management
```bash
# Stop automation
launchctl unload ~/Library/LaunchAgents/com.jleechanorg.pr-automation.plist

# Start automation
launchctl load ~/Library/LaunchAgents/com.jleechanorg.pr-automation.plist

# Restart automation
launchctl unload ~/Library/LaunchAgents/com.jleechanorg.pr-automation.plist
launchctl load ~/Library/LaunchAgents/com.jleechanorg.pr-automation.plist
```

## 🔍 Troubleshooting

### Common Issues

**No PRs Discovered**
```bash
# Check GitHub authentication
gh auth status

# Verify organization access
gh repo list jleechanorg --limit 1

# Check network connectivity
curl -s https://api.github.com/orgs/jleechanorg
```

**Worktree Creation Fails**
```bash
# Check local repository exists
ls ~/projects/[repo-name]

# Verify git repository
cd ~/projects/[repo-name] && git status

# Clean stale worktrees
git worktree prune
```

**Safety Limits Reached**
```bash
# Check current status
python3 automation/automation_safety_manager.py --status

# Grant manual approval
python3 automation/automation_safety_manager.py --approve admin@email.com

# Reset specific PR if needed
python3 automation/automation_safety_manager.py --record-pr [repo-pr] success
```

### Log Analysis
```bash
# Service logs
cat ~/Library/Logs/worldarchitect-automation/jleechanorg-launchd.out
cat ~/Library/Logs/worldarchitect-automation/jleechanorg-launchd.err

# Application logs
tail -100 ~/Library/Logs/worldarchitect-automation/jleechanorg_pr_monitor.log

# Safety manager logs
grep "automation_safety_manager" ~/Library/Logs/worldarchitect-automation/*.log
```

## 🎯 Key Features

### ✅ **Cross-Organization Coverage**
- Automatically discovers ALL repositories in jleechanorg
- Processes open PRs across multiple projects simultaneously
- No manual repository configuration required

### ✅ **Worktree Isolation**
- Each PR processed in completely isolated environment
- Prevents conflicts between simultaneous PR processing
- Automatic workspace cleanup after processing

### ✅ **Intelligent Branch Management**
- Detects existing local branches vs remote-only branches
- Creates appropriate local tracking branches automatically
- Syncs with correct remote targets

### ✅ **Comprehensive Safety**
- Per-PR attempt limits prevent infinite retry loops
- Global run limits prevent automation runaway
- Manual approval system for oversight
- Email notifications at safety thresholds

### ✅ **macOS Native Integration**
- launchd service for reliable scheduling
- Proper environment variable handling
- User session awareness
- Automatic restart on failure

### ✅ **Production Ready**
- Comprehensive error handling and logging
- Timeout protection for long-running processes
- Resource limits and process management
- Graceful degradation on failures

This system provides enterprise-grade automation for the entire jleechanorg organization while maintaining safety, isolation, and reliability.
