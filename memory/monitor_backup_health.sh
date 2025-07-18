#!/bin/bash
# Memory Backup Health Monitor
# Version: 1.0.0
# Runs periodic health checks and alerts on issues

set -e

# Configuration
MEMORY_FILE="${MEMORY_FILE:-$HOME/.cache/mcp-memory/memory.json}"
LOG_FILE="${LOG_FILE:-$HOME/.cache/mcp-memory/monitor.log}"
CHECK_INTERVAL=${CHECK_INTERVAL:-3600}  # Default: 1 hour
ALERT_THRESHOLD=10  # Alert if backup differs by more than 10%

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $1" | tee -a "$LOG_FILE"
}

# Send alert (placeholder for future notification system)
send_alert() {
    local severity=$1
    local message=$2
    
    echo -e "${RED}🚨 ALERT [$severity]: $message${NC}" | tee -a "$LOG_FILE"
    
    # Future: Could send email, Slack notification, etc.
    # For now, just log prominently
}

# Check backup freshness
check_backup_freshness() {
    local backup_branch="memory-backup-$(date +%Y-%m-%d)"
    
    # Fetch latest
    git fetch origin "$backup_branch" >/dev/null 2>&1 || {
        send_alert "WARNING" "No backup branch found for today: $backup_branch"
        return 1
    }
    
    # Get last commit time
    local last_commit
    if ! last_commit=$(git log -1 --format=%ct "origin/$backup_branch" 2>/dev/null); then
        last_commit=0
    fi
    local current_time=$(date +%s)
    local age=$((current_time - last_commit))
    
    # Alert if backup is more than 2 hours old
    if [ "$age" -gt 7200 ]; then
        send_alert "WARNING" "Backup is $((age / 3600)) hours old (branch: $backup_branch)"
        return 1
    fi
    
    return 0
}

# Check data integrity
check_data_integrity() {
    local source_lines
    if ! source_lines=$(wc -l < "$MEMORY_FILE" 2>/dev/null); then
        source_lines=0
    fi
    local backup_branch="memory-backup-$(date +%Y-%m-%d)"
    
    if [ "$source_lines" -eq 0 ]; then
        send_alert "CRITICAL" "Memory file is empty or missing: $MEMORY_FILE"
        return 1
    fi
    
    # Check GitHub backup
    local github_lines=$(git show origin/"$backup_branch":memory.json 2>/dev/null | wc -l || echo "0")
    
    if [ "$github_lines" -eq 0 ]; then
        send_alert "CRITICAL" "GitHub backup is empty or missing"
        return 1
    fi
    
    # Calculate difference percentage
    local diff=$((source_lines - github_lines))
    local diff_abs=${diff#-}  # Absolute value
    
    if [ "$source_lines" -gt 0 ]; then
        local diff_percent=$((diff_abs * 100 / source_lines))
        
        if [ "$diff_percent" -gt "$ALERT_THRESHOLD" ]; then
            send_alert "WARNING" "Backup differs by ${diff_percent}% (Source: $source_lines, Backup: $github_lines)"
            return 1
        fi
    fi
    
    return 0
}

# Check JSON validity
check_json_validity() {
    local invalid_count=0
    
    while IFS= read -r line; do
        if [ -n "$line" ] && ! echo "$line" | jq . >/dev/null 2>&1; then
            invalid_count=$((invalid_count + 1))
        fi
    done < "$MEMORY_FILE"
    
    if [ "$invalid_count" -gt 0 ]; then
        send_alert "CRITICAL" "Found $invalid_count invalid JSON lines in memory file"
        return 1
    fi
    
    return 0
}

# Main monitoring loop
main() {
    log "Memory Backup Health Monitor started (PID: $$)"
    log "Monitoring: $MEMORY_FILE"
    log "Check interval: $CHECK_INTERVAL seconds"
    
    # Create PID file
    echo $$ > /tmp/memory_monitor.pid
    
    # Trap to clean up on exit
    trap 'rm -f /tmp/memory_monitor.pid; log "Monitor stopped"' EXIT
    
    while true; do
        log "Running health checks..."
        
        local issues=0
        
        # Run checks
        if ! check_backup_freshness; then
            issues=$((issues + 1))
        fi
        
        if ! check_data_integrity; then
            issues=$((issues + 1))
        fi
        
        if ! check_json_validity; then
            issues=$((issues + 1))
        fi
        
        if [ "$issues" -eq 0 ]; then
            log "✅ All health checks passed"
        else
            log "⚠️  Found $issues issues"
        fi
        
        # Sleep until next check
        sleep "$CHECK_INTERVAL"
    done
}

# Handle command line arguments
case "${1:-}" in
    "start")
        if [ -f /tmp/memory_monitor.pid ]; then
            OLD_PID=$(cat /tmp/memory_monitor.pid)
            if kill -0 "$OLD_PID" 2>/dev/null; then
                echo "Monitor already running (PID: $OLD_PID)"
                exit 1
            fi
        fi
        
        # Start in background
        nohup "$0" run >> "$LOG_FILE" 2>&1 &
        echo "Monitor started in background (PID: $!)"
        ;;
        
    "stop")
        if [ -f /tmp/memory_monitor.pid ]; then
            PID=$(cat /tmp/memory_monitor.pid)
            kill "$PID" 2>/dev/null && echo "Monitor stopped (PID: $PID)"
            rm -f /tmp/memory_monitor.pid
        else
            echo "Monitor not running"
        fi
        ;;
        
    "status")
        if [ -f /tmp/memory_monitor.pid ]; then
            PID=$(cat /tmp/memory_monitor.pid)
            if kill -0 "$PID" 2>/dev/null; then
                echo -e "${GREEN}Monitor running (PID: $PID)${NC}"
                echo "Recent log entries:"
                tail -5 "$LOG_FILE"
            else
                echo -e "${RED}Monitor not running (stale PID file)${NC}"
                rm -f /tmp/memory_monitor.pid
            fi
        else
            echo -e "${YELLOW}Monitor not running${NC}"
        fi
        ;;
        
    "check")
        # Run one-time check
        check_backup_freshness && echo -e "${GREEN}✅ Backup freshness: OK${NC}" || echo -e "${RED}❌ Backup freshness: FAILED${NC}"
        check_data_integrity && echo -e "${GREEN}✅ Data integrity: OK${NC}" || echo -e "${RED}❌ Data integrity: FAILED${NC}"
        check_json_validity && echo -e "${GREEN}✅ JSON validity: OK${NC}" || echo -e "${RED}❌ JSON validity: FAILED${NC}"
        ;;
        
    "run")
        # Run in foreground (internal use)
        main
        ;;
        
    *)
        echo "Usage: $0 {start|stop|status|check}"
        echo ""
        echo "  start  - Start monitor in background"
        echo "  stop   - Stop running monitor"
        echo "  status - Check monitor status"
        echo "  check  - Run one-time health check"
        exit 1
        ;;
esac