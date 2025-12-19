# Storage State Testing Protocol
## Codex Branch Updater - Production Readiness Validation

**AI Consensus Recommendation:** Storage State API with self-healing login flow (Gemini Pro, Gemini Flash, Perplexity consulted)

**Decision Date:** 2025-12-10
**Target Production:** Cron job every 4 hours

---

## Implementation Summary

### What Changed
1. **Immediate auth state save after re-authentication** (line 104-105)
2. **Clear logging for session validation** (lines 89, 92)
3. **BrowserContext passed to ensure_logged_in()** (line 263)
4. **Dual save strategy**: Immediate save after re-auth + final save after tasks

### Self-Healing Flow
```
1. Load storage_state.json (if exists)
2. Navigate to chatgpt.com/codex
3. Check if task list visible (implicit session check)
4. IF NOT LOGGED IN:
   a. Execute manual login flow
   b. IMMEDIATELY save new auth state
   c. Log success
5. Execute task processing
6. Save final auth state (redundant but safe)
```

---

## Testing Phase 1: Local Validation (Days 1-2)

### Pre-Test Setup
```bash
# Delete existing auth state to start fresh
rm ~/.chatgpt_codex_auth_state.json

# Run first time (will require manual login)
python automation/jleechanorg_pr_automation/codex_branch_updater.py
```

**Expected Output:**
```
ℹ️  No saved authentication state found. Fresh login required.
🔐 ChatGPT Codex credentials not found...
✅ Credentials saved locally (chmod 600).
[Login flow executes]
💾 New authentication state saved immediately to ~/.chatgpt_codex_auth_state.json.
[Tasks processed]
💾 Final authentication state saved to ~/.chatgpt_codex_auth_state.json.
```

### Test Cases

#### TC1: Fresh Auth State Persistence
```bash
# Run 1: Manual login
python automation/jleechanorg_pr_automation/codex_branch_updater.py

# Run 2: Should use saved state
python automation/jleechanorg_pr_automation/codex_branch_updater.py
```

**Expected:**
- Run 1: Creates `~/.chatgpt_codex_auth_state.json`
- Run 2: Loads state, logs "✅ Session still valid"

**Failure Mode:** If Run 2 requires login, OAuth session didn't persist (critical issue).

#### TC2: Session Expiration Handling
```bash
# Manually corrupt the auth state to simulate expiration
echo '{"cookies": [], "origins": []}' > ~/.chatgpt_codex_auth_state.json

# Run automation
python automation/jleechanorg_pr_automation/codex_branch_updater.py
```

**Expected:**
```
🔄 Loading saved authentication state from ~/.chatgpt_codex_auth_state.json
⚠️  Session expired. Re-authenticating...
[Login flow executes]
💾 New authentication state saved immediately to ~/.chatgpt_codex_auth_state.json.
```

**Failure Mode:** If automation crashes instead of re-authenticating, self-healing failed.

#### TC3: Browser Crash Recovery
```bash
# Run automation, kill browser mid-process
python automation/jleechanorg_pr_automation/codex_branch_updater.py &
PID=$!
sleep 10
kill -9 $PID

# Verify auth state wasn't corrupted
ls -la ~/.chatgpt_codex_auth_state.json
cat ~/.chatgpt_codex_auth_state.json | jq .

# Re-run automation
python automation/jleechanorg_pr_automation/codex_branch_updater.py
```

**Expected:** Auth state remains valid from last successful save.

---

## Testing Phase 2: Cron Simulation (Days 3-9)

### Setup 4-Hour Cron Job
```bash
# Create test cron script
cat > /tmp/test_codex_automation.sh << 'EOF'
#!/bin/bash
# Define PROJECT_ROOT - adjust to your project location
PROJECT_ROOT="${PROJECT_ROOT:-$HOME/projects/your-project}"
LOG_DIR="$HOME/tmp/automation_tests"
mkdir -p "$LOG_DIR"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/codex_run_${TIMESTAMP}.log"

cd "$PROJECT_ROOT"
python automation/jleechanorg_pr_automation/codex_branch_updater.py > "$LOG_FILE" 2>&1
EXIT_CODE=$?

echo "Exit Code: $EXIT_CODE" >> "$LOG_FILE"
echo "Timestamp: $(date)" >> "$LOG_FILE"
EOF

chmod +x /tmp/test_codex_automation.sh

# Add to crontab (every 4 hours)
crontab -l > /tmp/current_cron
echo "0 */4 * * * /tmp/test_codex_automation.sh" >> /tmp/current_cron
crontab /tmp/current_cron
```

### Monitoring Script
```bash
#!/bin/bash
# monitor_auth_state.sh - Track session persistence

LOG_DIR="$HOME/tmp/automation_tests"
REPORT_FILE="$LOG_DIR/session_health_report.txt"

echo "=== Session Health Report - $(date) ===" > "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Count total runs
TOTAL_RUNS=$(ls -1 "$LOG_DIR"/codex_run_*.log 2>/dev/null | wc -l)
echo "Total Runs: $TOTAL_RUNS" >> "$REPORT_FILE"

# Count re-authentications
REAUTH_COUNT=$(grep -l "Session expired. Re-authenticating" "$LOG_DIR"/codex_run_*.log 2>/dev/null | wc -l)
echo "Re-authentications: $REAUTH_COUNT" >> "$REPORT_FILE"

# Calculate success rate
if [ "$TOTAL_RUNS" -gt 0 ]; then
    REAUTH_RATE=$(awk "BEGIN {printf \"%.2f\", ($REAUTH_COUNT / $TOTAL_RUNS) * 100}")
    echo "Re-authentication Rate: ${REAUTH_RATE}%" >> "$REPORT_FILE"
fi

# Count failures
FAILURE_COUNT=$(grep -l "Exit Code: [^0]" "$LOG_DIR"/codex_run_*.log 2>/dev/null | wc -l)
echo "Failures: $FAILURE_COUNT" >> "$REPORT_FILE"

# Find last successful run
LAST_SUCCESS=$(grep -l "Exit Code: 0" "$LOG_DIR"/codex_run_*.log 2>/dev/null | tail -1)
if [ -n "$LAST_SUCCESS" ]; then
    echo "Last Success: $(basename "$LAST_SUCCESS")" >> "$REPORT_FILE"
fi

cat "$REPORT_FILE"
```

### Acceptance Criteria (7-Day Test)
- **Minimum runs:** 42 (7 days × 6 runs/day)
- **Re-authentication rate:** <5% (≤2 re-auths in 42 runs)
- **Failure rate:** 0% (all runs complete successfully)
- **Auth state file size:** >500 bytes (indicates real session data)

**Success Threshold:**
```bash
# Run after 7 days
bash monitor_auth_state.sh

# Expected output:
# Total Runs: 42
# Re-authentications: 0-2
# Re-authentication Rate: 0.00-4.76%
# Failures: 0
```

**Failure Trigger (implement daemon mode if any occur):**
- Re-authentication rate >20% within 7 days
- Any hard failures (non-zero exit codes)
- Session persistence <24 hours consistently

---

## Testing Phase 3: Edge Cases (Day 10)

### EC1: Network Interruption
```bash
# Disconnect Wi-Fi mid-run, reconnect after 30s
# Automation should fail gracefully with clear error
```

### EC2: ChatGPT Service Degradation
```bash
# Monitor behavior during Cloudflare rate limiting
# Should log clear error, not corrupt auth state
```

### EC3: Multi-Day Session Persistence
```bash
# Wait 72 hours without running automation
# Next run should use saved state OR gracefully re-auth
```

---

## Production Deployment Checklist

### Pre-Deployment
- [ ] All Phase 1 test cases pass
- [ ] 7-day cron simulation shows <5% re-auth rate
- [ ] Auth state file permissions verified (600)
- [ ] Logs directory exists with proper permissions
- [ ] Credentials file exists at `~/.chatgpt_codex_credentials.json`

### Deployment
```bash
# Production cron entry
crontab -e

# Add (runs at :00 of every 4th hour: 00:00, 04:00, 08:00, 12:00, 16:00, 20:00)
# NOTE: Replace $PROJECT_ROOT with your actual project path
0 */4 * * * cd $PROJECT_ROOT && python automation/jleechanorg_pr_automation/codex_branch_updater.py >> ~/tmp/automation/codex_automation.log 2>&1
```

### Post-Deployment Monitoring (First 7 Days)
```bash
# Daily health check
tail -n 100 ~/tmp/automation/codex_automation.log

# Look for:
# ✅ "Session still valid" (good - using saved state)
# ⚠️  "Session expired" (acceptable if <20% of runs)
# ❌ Python tracebacks (critical - investigate immediately)
```

### Alerting Setup
```bash
# Add to cron script for email alerts on failure
if [ $EXIT_CODE -ne 0 ]; then
    echo "Codex automation failed. Check log: $LOG_FILE" | mail -s "Codex Automation Failure" your@email.com
fi
```

---

## Rollback Plan

### If Storage State Fails (>20% re-auth rate)
1. Document exact failure pattern from logs
2. Implement daemon mode architecture:
   - Chrome process managed by systemd/launchd
   - CDP reconnection logic
   - Health check endpoint
3. Preserve this implementation as fallback

### If OAuth Fundamentally Incompatible
```bash
# Option: Use Google OAuth2 token refresh
# Requires ChatGPT API key instead of web automation
# Research ChatGPT Codex API availability
```

---

## Success Metrics (Production - First 30 Days)

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Uptime | >95% | TBD | 🟡 |
| Re-auth Rate | <5% | TBD | 🟡 |
| False Positives | 0 | TBD | 🟡 |
| Manual Intervention | <1/week | TBD | 🟡 |
| Auth State File Corruption | 0 | TBD | 🟡 |

**Green Light for Production:** All targets met after 30 days
**Yellow Light (Monitor):** Uptime 90-95%, re-auth 5-10%
**Red Light (Implement Daemon):** Uptime <90%, re-auth >10%

---

## Multi-Model AI Recommendations Summary

### Gemini Pro
- **Stance:** Storage State API is "standard, idiomatic way"
- **Key Insight:** Self-healing flow with immediate auth state save
- **Daemon Mode:** Only if Storage State "completely unworkable"

### Gemini Flash
- **Stance:** Test Storage State first (most elegant)
- **Critical Warning:** Google OAuth may not persist via cookies alone
- **Recommendation:** Rigorous testing required

### Perplexity
- **Stance:** Ship manual login now, defer complexity
- **Concern:** Solo dev maintenance burden
- **Pragmatic View:** Occasional manual login cheaper than daemon infrastructure

### Our Decision
**Implement Storage State API NOW** (Gemini Pro's approach), validate over 7 days, implement daemon mode only if re-auth rate exceeds 20%.

**Rationale:**
- Low risk (graceful degradation)
- High reward (fully autonomous if successful)
- Data-driven decision point (7-day test)
- Incremental path to daemon mode if needed
