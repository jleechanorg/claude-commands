# WorldArchitect PR Automation with Safety Limits

## 🎯 Overview

A robust, safety-first automation system for processing GitHub PRs with configurable limits and manual approval gates.

## 🛡️ Safety Features

- **PR Limits**: Max 5 attempts per PR before blocking
- **Global Limits**: Max 50 total automation runs before requiring manual approval
- **Thread-Safe**: Concurrent-safe operations with file locking
- **Email Notifications**: Automatic alerts when limits are reached
- **Persistence**: State maintained across system restarts
- **Configurable**: Environment variable configuration

## 🚀 Quick Start

### macOS launchd Installation (Recommended)

```bash
# Install the automation system
./automation/install_launchd_automation.sh

# Check status
python3 automation/automation_safety_manager.py --status

# View logs
tail -f ~/Library/Logs/worldarchitect-automation/automation_safety.log
```

### Manual Management

```bash
# Check if PR can be processed
python3 automation/automation_safety_manager.py --check-pr 1001

# Record PR attempt
python3 automation/automation_safety_manager.py --record-pr 1001 failure

# Check global run status
python3 automation/automation_safety_manager.py --check-global

# Grant manual approval (when needed)
python3 automation/automation_safety_manager.py --approve user@example.com

# View complete status
python3 automation/automation_safety_manager.py --status
```

## 📊 Configuration

### Environment Variables

```bash
export AUTOMATION_PR_LIMIT=5        # Max attempts per PR (default: 5)
export AUTOMATION_GLOBAL_LIMIT=50   # Max total runs (default: 50)

# Email notifications (optional)
export SMTP_SERVER=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USERNAME=your_email@gmail.com
export SMTP_PASSWORD=your_app_password
export MEMORY_EMAIL_FROM=automation@worldarchitect.ai
export MEMORY_EMAIL_TO=admin@worldarchitect.ai
```

### launchd Schedule

Default: Every 10 minutes (600 seconds)

To modify, edit `automation/com.worldarchitect.pr-automation.plist`:

```xml
<key>StartInterval</key>
<integer>600</integer>  <!-- 10 minutes -->
```

## 🔧 Architecture

### Components

1. **AutomationSafetyManager** (`automation_safety_manager.py`)
   - Core safety logic with thread-safe operations
   - JSON-based persistence with atomic file operations
   - CLI interface for management

2. **Safety Wrapper** (`automation_safety_wrapper.py`)
   - launchd entry point with safety checks
   - Logging and error handling
   - Integration with existing `simple_pr_batch.sh`

3. **launchd Plist** (`com.worldarchitect.pr-automation.plist`)
   - macOS background service configuration
   - Environment setup and logging

4. **Installation Script** (`install_launchd_automation.sh`)
   - One-command setup with path resolution
   - User-specific configuration

### Data Files

```
~/Library/Application Support/worldarchitect-automation/
├── pr_attempts.json      # Per-PR attempt tracking
├── global_runs.json      # Total automation runs
└── manual_approval.json  # Approval status and expiry
```

### Logs

```
~/Library/Logs/worldarchitect-automation/
├── automation_safety.log  # Safety wrapper logs
├── launchd.out            # launchd stdout
└── launchd.err            # launchd stderr
```

## 🧪 Testing

The system was built using Test-Driven Development with comprehensive matrix testing:

```bash
# Run safety tests
TESTING=true python3 tests/test_automation_safety_limits.py

# Test basic functionality
python3 automation/automation_safety_manager.py --data-dir /tmp/test --status
```

### Test Coverage

- ✅ PR attempt limits (max 5 per PR)
- ✅ Global run limits (max 50 total)
- ✅ Manual approval system with 24-hour expiry
- ✅ Thread-safe concurrent operations
- ✅ Email notifications at limits
- ✅ State persistence across restarts
- ✅ Configuration via environment variables

## 🚨 Safety Scenarios

### Scenario 1: PR Reaches Attempt Limit

1. PR fails 5 times
2. System blocks further attempts on that PR
3. Email notification sent to admin
4. Other PRs continue processing normally

### Scenario 2: Global Limit Reached

1. System reaches 50 total automation runs
2. All automation blocked until manual approval
3. Email notification sent requesting approval
4. Admin grants approval: system continues for 24 hours

### Scenario 3: Manual Approval Expires

1. 24 hours pass since approval granted
2. System blocks automation again
3. New approval required to continue

## 🔄 Migration from Cron

### Old cron setup:
```bash
*/10 * * * * cd ~/projects/worldarchitect.ai && ./automation/simple_pr_batch.sh
```

### New launchd setup:
1. Remove cron entry: `crontab -e`
2. Install launchd: `./automation/install_launchd_automation.sh`
3. Verify: `launchctl list | grep worldarchitect`

### Benefits of launchd vs cron:

- ✅ Better environment variable handling
- ✅ Automatic restart on failure
- ✅ User session awareness
- ✅ Detailed logging integration
- ✅ Resource limits and process management
- ✅ No missed executions on system sleep

## 📈 Monitoring

### Check Service Status

```bash
# Service status
launchctl list | grep worldarchitect

# Recent logs
tail -f ~/Library/Logs/worldarchitect-automation/automation_safety.log

# Automation status
python3 automation/automation_safety_manager.py --status
```

### Restart Service

```bash
# Unload and reload
launchctl unload ~/Library/LaunchAgents/com.worldarchitect.pr-automation.plist
launchctl load ~/Library/LaunchAgents/com.worldarchitect.pr-automation.plist
```

## 🆘 Troubleshooting

### Service Not Running

```bash
# Check plist syntax
plutil ~/Library/LaunchAgents/com.worldarchitect.pr-automation.plist

# Check logs for errors
cat ~/Library/Logs/worldarchitect-automation/launchd.err
```

### Permissions Issues

```bash
# Make scripts executable
chmod +x automation/*.py automation/*.sh

# Check file ownership
ls -la automation/
```

### Email Notifications Not Working

```bash
# Test email configuration
python3 -c "
import os
print('SMTP Config:')
print(f'  Server: {os.environ.get(\"SMTP_SERVER\", \"NOT SET\")}')
print(f'  Username: {os.environ.get(\"SMTP_USERNAME\", \"NOT SET\")}')
print(f'  From: {os.environ.get(\"MEMORY_EMAIL_FROM\", \"NOT SET\")}')
print(f'  To: {os.environ.get(\"MEMORY_EMAIL_TO\", \"NOT SET\")}')
"
```

## 📚 Development

### Adding New Safety Features

1. Add tests to `tests/test_automation_safety_limits.py`
2. Run tests to confirm failure (RED)
3. Implement minimal code to pass (GREEN)
4. Refactor and optimize (REFACTOR)

### Extending Limits

```bash
# Temporary increase
export AUTOMATION_PR_LIMIT=10
export AUTOMATION_GLOBAL_LIMIT=100

# Permanent: Update environment in plist or shell profile
```

This system provides robust automation with multiple safety nets, ensuring reliable PR processing while preventing runaway automation that could overwhelm the system or API limits.
