# PR Automation Safety Limits & Configuration

## 🚨 **Critical Safety Limits**

The PR automation system has built-in safety mechanisms to prevent excessive API usage and maintain system stability:

### **Primary Safety Limits**

| Limit Type | Value | Purpose |
|------------|-------|---------|
| **Daily Run Limit** | 50 runs per day | Prevents excessive API usage, resets at midnight |
| **Max Batch Size** | 5 PRs per run | Prevents overwhelming the system |
| **Max Fix Attempts** | 3 attempts per PR | Prevents infinite retry loops |
| **Run Frequency** | Every 10 minutes | Reasonable processing interval |
| **Processing Timeout** | 20 minutes per PR | Prevents hanging processes |
| **Cooldown Period** | 4 hours after success | Prevents duplicate processing |

### **Workflow-Specific Comment Limits**

Each workflow type has its own configurable limit for automation comments per PR (some workflows may not currently post comments, but have limits reserved for future compatibility):

| Workflow Type | Default Limit | CLI Flag | Description |
|---------------|---------------|----------|-------------|
| **PR Automation** | 10 comments | `--pr-automation-limit` | Default PR monitoring workflow (posts codex comments) |
| **Fix-Comment** | 10 comments | `--fix-comment-limit` | Fix-comment workflow (addresses review comments) |
| **Codex Update** | 10 comments | (reserved) | Codex update workflow (browser automation; does not currently post PR comments—limit reserved for future compatibility) |
| **FixPR** | 10 comments | `--fixpr-limit` | FixPR workflow (resolves conflicts/failing checks) |

**Note**: Defaults are hardcoded in the automation package; override via CLI flags (or via `automation-safety-cli` which writes `automation_safety_config.json` in the safety data dir).

**Note**: Workflow comment counting is marker-based:
- PR automation comments: `codex-automation-commit`
- Fix-comment queued runs: `fix-comment-automation-run` (separate from completion marker)
- Fix-comment completion/review requests: `fix-comment-automation-commit`
- FixPR queued runs: `fixpr-automation-run`

### **Daily Run Calculations**

**When automation is enabled**, the system runs every 30 minutes with a **50 runs per day limit**:
- **Maximum runs per day**: 50 runs (resets at midnight)
- **PRs processed per day**: Maximum 250 PRs (50 runs × 5 PRs max per run)
- **Actual scheduling**: Every 30 minutes (48 possible slots), but limited to 50 successful runs

⚠️ **Practical limits are lower due to:**
- Daily 50-run limit (automatic reset at midnight)
- 4-hour cooldown between successful processing
- 3-attempt limit before email notification and cooldown
- Only processes PRs updated in last 24 hours
- Skips already processed PRs within cooldown period

### **Realistic Daily Processing**

With safety mechanisms in effect:
- **Daily run limit**: 50 runs maximum (resets at midnight)
- **Active PRs per day**: Typically 5-15 PRs
- **Actual processing attempts**: Up to 50 runs per day
- **Successful completions**: ~10-25 PRs per day (depending on batch sizes)
- **Failed PRs**: Stopped after 3 attempts, require manual intervention
- **Auto-reset**: Counter resets to 0 at midnight daily

## 🔧 **Configuration Details**

### **File Locations**
```bash
# Configuration in script
MAX_BATCH_SIZE=5        # PRs per run
MAX_FIX_ATTEMPTS=3      # Attempts per PR
COMMENT_TIMEOUT=1200    # 20 minutes per Codex comment attempt

# Status tracking files
/tmp/pr_automation_processed.txt    # Successfully processed PRs with timestamps
/tmp/pr_fix_attempts.txt           # Failed attempt counters per PR
/tmp/pr_automation.log             # Comprehensive activity log
```

### **Cron Configuration**
```bash
# ENABLED (processes every 10 minutes)
*/10 * * * * cd ~/projects/worldarchitect.ai && ./automation/simple_pr_batch.sh >> /tmp/pr_automation.log 2>&1

# DISABLED (commented out for safety)
# */10 * * * * cd ~/projects/worldarchitect.ai/worktree_autofix && ./automation/simple_pr_batch.sh >> /tmp/pr_automation.log 2>&1
```

## ⚡ **Performance Impact**

### **Resource Usage per Run**
- **Memory**: Minimal (gh CLI comment invocation)
- **Storage**: Negligible temporary data
- **Network**: GitHub API call to post comment
- **CPU**: Minimal during Codex comment posting (CLI invocation only)

### **API Usage Limits**
- **GitHub API**: Rate limited by GitHub (5000 requests/hour)
- **Git Operations**: Limited by network bandwidth (light usage)

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
cd ~/projects/worldarchitect.ai
./automation/simple_pr_batch.sh

# Or trigger the orchestrator to post a Codex instruction for a specific PR
# (see automation/JLEECHANORG_AUTOMATION.md for the /commentreply command summary)
   /commentreply [PR_NUMBER] "$CODEX_COMMENT"
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
