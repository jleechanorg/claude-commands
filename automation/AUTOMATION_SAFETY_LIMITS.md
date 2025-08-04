# PR Automation Safety Limits & Configuration

## 🚨 **Critical Safety Limits**

The PR automation system has built-in safety mechanisms to prevent excessive API usage and maintain system stability:

### **Primary Safety Limits**

| Limit Type | Value | Purpose |
|------------|-------|---------|
| **Max Batch Size** | 5 PRs per run | Prevents overwhelming the system |
| **Max Fix Attempts** | 3 attempts per PR | Prevents infinite retry loops |
| **Run Frequency** | Every 10 minutes | Reasonable processing interval |
| **Processing Timeout** | 20 minutes per PR | Prevents hanging processes |
| **Cooldown Period** | 4 hours after success | Prevents duplicate processing |

### **Daily Run Calculations**

**When automation is enabled**, the system runs every 10 minutes:
- **Runs per hour**: 6 runs
- **Runs per day**: 144 runs (6 × 24 hours)
- **PRs processed per day**: Maximum 720 PRs (144 runs × 5 PRs max per run)

⚠️ **However, practical limits are much lower due to:**
- 4-hour cooldown between successful processing
- 3-attempt limit before email notification and cooldown
- Only processes PRs updated in last 24 hours
- Skips already processed PRs within cooldown period

### **Realistic Daily Processing**

With safety mechanisms in effect:
- **Active PRs per day**: Typically 5-15 PRs
- **Actual processing attempts**: ~10-30 per day
- **Successful completions**: ~5-10 PRs per day
- **Failed PRs**: Stopped after 3 attempts, require manual intervention

## 🔧 **Configuration Details**

### **File Locations**
```bash
# Configuration in script
MAX_BATCH_SIZE=5        # PRs per run
MAX_FIX_ATTEMPTS=3      # Attempts per PR
COPILOT_TIMEOUT=1200    # 20 minutes per PR

# Status tracking files
/tmp/pr_automation_processed.txt    # Successfully processed PRs with timestamps
/tmp/pr_fix_attempts.txt           # Failed attempt counters per PR
/tmp/pr_automation.log             # Comprehensive activity log
```

### **Cron Configuration**
```bash
# ENABLED (processes every 10 minutes)
*/10 * * * * cd ~/projects/worldarchitect.ai/worktree_autofix && ./automation/simple_pr_batch.sh >> /tmp/pr_automation.log 2>&1

# DISABLED (commented out for safety)
# */10 * * * * cd ~/projects/worldarchitect.ai/worktree_autofix && ./automation/simple_pr_batch.sh >> /tmp/pr_automation.log 2>&1
```

## ⚡ **Performance Impact**

### **Resource Usage per Run**
- **Memory**: ~500MB per concurrent PR (isolated workspaces)
- **Storage**: ~500MB temporary per PR (auto-cleaned)
- **Network**: GitHub API calls + git clone operations
- **CPU**: Moderate during /copilot analysis (20 min max)

### **API Usage Limits**
- **GitHub API**: Rate limited by GitHub (5000 requests/hour)
- **Claude API**: Rate limited by Anthropic usage tiers
- **Git Operations**: Limited by network bandwidth

## 🛡️ **Safety Mechanisms**

### **Automatic Safeguards**
1. **Batch Size Limiting**: Never processes more than 5 PRs per run
2. **Attempt Limiting**: Stops after 3 failed attempts per PR
3. **Timeout Protection**: Kills processes after 20 minutes
4. **Cooldown Enforcement**: 4-hour delay between successful processing
5. **Workspace Isolation**: Each PR processed in separate temporary directory
6. **Automatic Cleanup**: Temporary workspaces removed after processing

### **Failure Handling**
1. **Email Notifications**: Sent when PR reaches 3 failed attempts
2. **Graceful Degradation**: Continues with other PRs if one fails
3. **Log Preservation**: All activity logged to `/tmp/pr_automation.log`
4. **Status Tracking**: Maintains state between runs
5. **Manual Override**: Can reset attempt counters or processed status

## 🚨 **Emergency Controls**

### **Disable Automation**
```bash
# Comment out cron job
crontab -e
# Add # at start of automation line

# Or remove entirely
crontab -l | grep -v "simple_pr_batch.sh" | crontab -
```

### **Reset All State**
```bash
# Clear all tracking files
rm -f /tmp/pr_automation_processed.txt
rm -f /tmp/pr_fix_attempts.txt
rm -f /tmp/pr_automation.log

# Clean up any remaining workspaces
rm -rf /tmp/pr-automation-*
```

### **Manual Processing**
```bash
# Run manually for specific PR
cd ~/projects/worldarchitect.ai/worktree_autofix
./automation/simple_pr_batch.sh

# Or process specific PR with copilot
claude '/copilot [PR_NUMBER]'
```

## 📊 **Monitoring**

### **Check Status**
```bash
# View recent activity
tail -20 /tmp/pr_automation.log

# Check processed PRs
cat /tmp/pr_automation_processed.txt

# Check failed attempts
cat /tmp/pr_fix_attempts.txt

# Check active cron job
crontab -l | grep automation
```

### **Health Indicators**
- ✅ **Healthy**: 5-10 successful PR completions per day
- ⚠️ **Warning**: Multiple PRs reaching 3 failed attempts
- 🚨 **Critical**: No successful completions for >24 hours
- 🔥 **Emergency**: Log file growing >100MB or excessive API errors

## 🎯 **Recommendations**

### **For Normal Operation**
- Monitor logs weekly for failure patterns
- Check email notifications for manual intervention needs
- Verify automation is processing recent PRs appropriately

### **For High Activity Periods**
- Consider temporarily increasing cooldown period
- Monitor API rate limit usage
- Watch for excessive temporary workspace creation

### **For Maintenance**
- Disable automation during system updates
- Clean up old log files periodically
- Reset state files if corruption suspected

---

**Last Updated**: 2025-08-04
**Automation Status**: Currently DISABLED for safety during system updates
