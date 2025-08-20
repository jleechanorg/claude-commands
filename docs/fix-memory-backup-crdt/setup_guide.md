# Memory Synchronization Setup Guide

## Quick Start for New Machines

### Prerequisites
- Git installed and configured
- jq (JSON processor): `brew install jq` or `sudo apt-get install jq`
- Cron service running (usually default on Unix systems)
- Access to GitHub repository: `https://github.com/jleechanorg/worldarchitect-memory-backups.git`

### One-Command Setup
```bash
cd /path/to/worldarchitect.ai/worktree_human
./scripts/setup_memory_sync.sh
```

The setup script will:
1. ✅ Check all dependencies
2. 📁 Create necessary directories
3. 🔄 Clone/update backup repository
4. 📄 Create initial memory file if needed
5. 🔧 Install sync scripts with proper permissions
6. ⏰ Configure automated cron jobs
7. 🧪 Test the synchronization system
8. 🚀 Run initial sync (optional)

### Manual Verification
```bash
# Check cron jobs are installed
crontab -l | grep memory

# Verify directory structure
ls -la ~/.cache/mcp-memory/
ls -la ~/.cache/memory-backup-repo/

# Test manual sync
scripts/fetch_memory.sh --test
scripts/memory_backup_crdt.sh --test
```

## How It Works

### Automatic Synchronization
- **Frequency**: Every 15 minutes automatically
- **Fetch**: Downloads latest changes from other machines
- **Merge**: Uses CRDT logic to resolve conflicts automatically
- **Backup**: Uploads your changes to shared repository

### Manual Synchronization
```bash
# Fetch latest changes from other machines
scripts/fetch_memory.sh

# Backup your changes to shared repository
scripts/memory_backup_crdt.sh

# The backup script automatically fetches first (bi-directional sync)
```

### Conflict Resolution
The system uses CRDT (Conflict-free Replicated Data Type) principles:
- **Last-Write-Wins**: If same entity modified on multiple machines, newest wins
- **Union Merge**: Different entities from different machines are combined
- **Device Isolation**: Each machine's changes are uniquely identifiable
- **No Data Loss**: All changes are preserved in Git history

## Using Across Multiple Machines

### Setting Up Machine #1 (First Machine)
```bash
# Run setup on your primary development machine
./scripts/setup_memory_sync.sh

# Use Memory MCP normally - it will sync automatically
# Your memory data will be backed up every 15 minutes
```

### Setting Up Machine #2, #3, etc.
```bash
# On each additional machine, run the same setup
./scripts/setup_memory_sync.sh

# The system will automatically:
# 1. Download existing memory data from other machines
# 2. Merge with any local memory data
# 3. Start syncing every 15 minutes
```

### Workflow Example
```bash
# Machine A: Add memory via Claude Code
# Memory MCP stores new data in ~/.cache/mcp-memory/memory.json
# After 15 minutes: Data automatically synced to GitHub

# Machine B: Work continues
# Fetch runs automatically, downloads Machine A's changes
# Memory MCP now has combined data from both machines
# New changes on Machine B get synced back

# Result: Both machines have identical, up-to-date memory data
```

## Monitoring and Troubleshooting

### Check Sync Status
```bash
# View recent sync activity
tail -20 ~/.cache/mcp-memory/logs/memory_sync.log

# Monitor real-time sync (Ctrl+C to exit)
tail -f ~/.cache/mcp-memory/logs/memory_sync.log

# Check memory file contents
cat ~/.cache/mcp-memory/memory.json | jq .
```

### Common Issues and Solutions

#### 1. No Internet Connection
```bash
# Symptoms: Sync logs show fetch/push failures
# Solution: System gracefully handles offline mode
# Memory MCP continues working with local data
# Sync resumes automatically when connection returns
```

#### 2. Git Authentication Issues
```bash
# Symptoms: "Permission denied" or "Authentication failed"
# Solution: Configure Git credentials
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# For SSH access (recommended)
ssh-keygen -t rsa -b 4096 -C "your.email@example.com"
# Add ~/.ssh/id_rsa.pub to GitHub account
```

#### 3. Cron Jobs Not Running
```bash
# Check if cron service is running
sudo service cron status  # Ubuntu/Debian
sudo launchctl list | grep cron  # macOS

# Verify cron jobs are installed
crontab -l

# Check cron logs
tail -f /var/log/cron.log  # Ubuntu/Debian
tail -f /var/log/system.log | grep cron  # macOS
```

#### 4. JSON Corruption
```bash
# Symptoms: Logs show "invalid JSON" errors
# Solution: System automatically recovers
# Corrupted files backed up with timestamp
# Clean initial state recreated

# Manual recovery if needed
cp ~/.cache/mcp-memory/memory.json.backup.TIMESTAMP ~/.cache/mcp-memory/memory.json
```

#### 5. Disk Space Issues
```bash
# Clean up old logs
rm ~/.cache/mcp-memory/logs/memory_sync.log.old*

# Clean up Git repository (keeps recent history)
cd ~/.cache/memory-backup-repo
git gc --prune=30.days.ago
```

### Performance Optimization

#### Adjust Sync Frequency
```bash
# Edit crontab to change frequency
crontab -e

# Examples:
# Every 5 minutes: */5 * * * * 
# Every 30 minutes: */30 * * * *
# Every hour: 0 * * * *
```

#### Monitor System Resources
```bash
# Check memory usage
ps aux | grep -E "(fetch_memory|memory_backup)"

# Check disk usage
du -sh ~/.cache/mcp-memory/
du -sh ~/.cache/memory-backup-repo/
```

## Advanced Configuration

### Custom Repository URL
```bash
# Edit scripts to use different repository
# Useful for private forks or company instances
sed -i 's|github.com/jleechanorg/worldarchitect-memory-backups.git|your-repo-url|g' scripts/*.sh
```

### Custom Paths
```bash
# Default paths can be customized by editing scripts:
# MEMORY_FILE="$HOME/.cache/mcp-memory/memory.json"
# BACKUP_REPO="$HOME/.cache/memory-backup-repo"
# LOG_FILE="$HOME/.cache/mcp-memory/logs/memory_sync.log"
```

### Development Machine vs Production
```bash
# For development machines (frequent changes)
# Use default 15-minute sync

# For production/CI machines (less frequent changes)
# Consider hourly sync to reduce overhead
crontab -e
# Change to: 0 * * * * /path/to/scripts/...
```

## Security Considerations

### File Permissions
- Memory files: 600 (owner read/write only)
- Directories: 700 (owner access only)
- Scripts: 700 (owner execute only)

### Network Security
- Uses HTTPS for Git operations (secure by default)
- Can be configured for SSH if preferred
- All data encrypted in transit via Git protocols

### Access Control
- Repository access controlled via GitHub permissions
- Local files protected by Unix permissions
- No sensitive data stored in logs

## Backup and Recovery

### Manual Backup
```bash
# Backup memory data
cp ~/.cache/mcp-memory/memory.json ~/memory_backup_$(date +%Y%m%d).json

# Backup entire memory directory
tar -czf ~/memory_full_backup_$(date +%Y%m%d).tar.gz ~/.cache/mcp-memory/
```

### Recovery from Git History
```bash
# View Git history
cd ~/.cache/memory-backup-repo
git log --oneline

# Restore from specific commit
git checkout COMMIT_HASH -- memory.json
cp memory.json ~/.cache/mcp-memory/memory.json
```

### Disaster Recovery
```bash
# Complete reset (destroys local changes!)
rm -rf ~/.cache/memory-backup-repo
rm -rf ~/.cache/mcp-memory
./scripts/setup_memory_sync.sh
```

## Integration with Development Workflow

### Works Seamlessly With
- Claude Code Memory MCP operations
- All existing `/remember` and memory commands
- Memory search and retrieval functions
- Any tools that read/write to Memory MCP

### Best Practices
1. **Let it run automatically** - Don't disable cron jobs
2. **Monitor logs occasionally** - Check for any persistent issues
3. **Keep machines updated** - Ensure Git and jq are current
4. **Test after setup** - Verify sync works between machines
5. **Document machine hostnames** - Helps identify sources in logs

This system provides transparent, reliable memory synchronization that requires minimal maintenance once set up correctly.