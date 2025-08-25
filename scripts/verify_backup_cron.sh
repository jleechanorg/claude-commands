#!/bin/bash

# Backup Cron Entry Verification Script
# Verifies that claude_backup cron entries are properly configured and running

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Backup Cron Verification ===${NC}"
echo ""

# Function to check cron entry exists
check_cron_entry() {
    echo -e "${BLUE}🔍 Checking for backup cron entries...${NC}"
    
    if crontab -l 2>/dev/null | grep -q "claude_backup"; then
        echo -e "${GREEN}  ✅ Found backup cron entries:${NC}"
        crontab -l 2>/dev/null | grep "claude_backup" | while read -r line; do
            echo -e "${GREEN}     $line${NC}"
        done
        return 0
    else
        echo -e "${RED}  ❌ No backup cron entries found${NC}"
        return 1
    fi
}

# Function to verify backup script accessibility
check_backup_script() {
    echo -e "\n${BLUE}🔍 Verifying backup script...${NC}"
    
    local backup_script="$SCRIPT_DIR/claude_backup.sh"
    if [[ -x "$backup_script" ]]; then
        echo -e "${GREEN}  ✅ Backup script is executable: $backup_script${NC}"
        
        # Test help function
        if "$backup_script" --help >/dev/null 2>&1; then
            echo -e "${GREEN}  ✅ Backup script responds to --help${NC}"
        else
            echo -e "${YELLOW}  ⚠️ Backup script --help failed${NC}"
        fi
        return 0
    else
        echo -e "${RED}  ❌ Backup script not executable or not found: $backup_script${NC}"
        return 1
    fi
}

# Function to check recent backup activity
check_backup_activity() {
    echo -e "\n${BLUE}🔍 Checking recent backup activity...${NC}"
    
    local backup_log="/tmp/claude_backup_cron.log"
    if [[ -f "$backup_log" ]]; then
        echo -e "${GREEN}  ✅ Backup log exists: $backup_log${NC}"
        
        local file_size=$(stat -c %s "$backup_log" 2>/dev/null || stat -f %z "$backup_log" 2>/dev/null)
        echo -e "${BLUE}     Log size: $file_size bytes${NC}"
        
        # Show last few lines if log has content
        if [[ $file_size -gt 0 ]]; then
            echo -e "${BLUE}     Last few log entries:${NC}"
            tail -3 "$backup_log" 2>/dev/null | while IFS= read -r line; do
                echo -e "${BLUE}       $line${NC}"
            done
        fi
        return 0
    else
        echo -e "${YELLOW}  ⚠️ No backup log found (cron job may not have run yet)${NC}"
        echo -e "${YELLOW}     Expected location: $backup_log${NC}"
        return 1
    fi
}

# Function to verify claude_mcp.sh integration
check_mcp_integration() {
    echo -e "\n${BLUE}🔍 Verifying claude_mcp.sh integration...${NC}"
    
    local claude_mcp="$PROJECT_ROOT/claude_mcp.sh"
    if [[ -f "$claude_mcp" ]]; then
        if grep -q "verify_backup_system\|backup.*verify" "$claude_mcp"; then
            echo -e "${GREEN}  ✅ claude_mcp.sh has backup verification integration${NC}"
            return 0
        else
            echo -e "${RED}  ❌ claude_mcp.sh missing backup verification${NC}"
            return 1
        fi
    else
        echo -e "${RED}  ❌ claude_mcp.sh not found: $claude_mcp${NC}"
        return 1
    fi
}

# Run all checks
TOTAL_CHECKS=0
PASSED_CHECKS=0

echo -e "${BLUE}Running comprehensive backup verification...${NC}"
echo ""

# Check 1: Cron entry
((TOTAL_CHECKS++))
if check_cron_entry; then
    ((PASSED_CHECKS++))
fi

# Check 2: Backup script
((TOTAL_CHECKS++))
if check_backup_script; then
    ((PASSED_CHECKS++))
fi

# Check 3: Backup activity
((TOTAL_CHECKS++))
if check_backup_activity; then
    ((PASSED_CHECKS++))
fi

# Check 4: MCP integration
((TOTAL_CHECKS++))
if check_mcp_integration; then
    ((PASSED_CHECKS++))
fi

# Summary
echo ""
echo -e "${BLUE}=== Verification Summary ===${NC}"
echo -e "${BLUE}Passed: $PASSED_CHECKS/$TOTAL_CHECKS checks${NC}"

if [[ $PASSED_CHECKS -eq $TOTAL_CHECKS ]]; then
    echo -e "${GREEN}🎉 All backup system checks passed!${NC}"
    exit 0
elif [[ $PASSED_CHECKS -ge $((TOTAL_CHECKS - 1)) ]]; then
    echo -e "${YELLOW}⚠️ Backup system mostly functional with minor issues${NC}"
    exit 1
else
    echo -e "${RED}❌ Backup system has significant issues${NC}"
    echo -e "${RED}Run: ./scripts/claude_backup.sh --setup-cron to fix${NC}"
    exit 2
fi