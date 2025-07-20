#!/bin/bash
# Anti-Speculation Hook for Claude Code
# Detects when Claude speculates about command execution instead of observing results

# Find project root by looking for .git directory
find_project_root() {
    local dir="$PWD"
    while [[ "$dir" != "/" ]]; do
        if [[ -d "$dir/.git" ]] || [[ -f "$dir/CLAUDE.md" ]]; then
            echo "$dir"
            return 0
        fi
        dir=$(dirname "$dir")
    done
    echo "$PWD"  # Fallback to current directory
}

PROJECT_ROOT=$(find_project_root)
LOG_FILE="/tmp/claude_speculation_log.txt"

# Read Claude's response text
RESPONSE_TEXT="${1:-$(cat)}"

# Color codes
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Speculation patterns
declare -A SPECULATION_PATTERNS=(
    ["[Ll]et me wait"]="Waiting assumption"
    ["[Ww]ait for.*complet"]="Command completion speculation"
    ["command.*running"]="Running state assumption"
    ["I'll wait for"]="Future waiting speculation"
    ["[Ww]aiting for.*finish"]="Finish waiting assumption"
    ["[Tt]he command.*execut"]="Execution state speculation"
    ["[Ll]et.*finish"]="Finish assumption"
    ["[Rr]unning.*complet"]="Running completion speculation"
)

FOUND_SPECULATION=false
SPECULATION_COUNT=0

# Check for speculation patterns
for pattern in "${!SPECULATION_PATTERNS[@]}"; do
    if echo "$RESPONSE_TEXT" | grep -i -E "$pattern" > /dev/null 2>&1; then
        FOUND_SPECULATION=true
        ((SPECULATION_COUNT++))
        
        description="${SPECULATION_PATTERNS[$pattern]}"
        matching_text=$(echo "$RESPONSE_TEXT" | grep -i -E "$pattern" | head -1)
        
        echo -e "${YELLOW}⚠️  SPECULATION DETECTED${NC}: $description"
        echo -e "   ${RED}Pattern${NC}: $pattern"
        echo -e "   ${RED}Match${NC}: $matching_text"
        echo ""
    fi
done

if [ "$FOUND_SPECULATION" = true ]; then
    echo -e "\n${RED}🚨 CRITICAL INSIGHT${NC}: Commands have already completed!"
    echo -e "${YELLOW}Instead of waiting or speculating:${NC}"
    echo "   1. Check actual command output/results"
    echo "   2. Look for error messages or completion status"
    echo "   3. Proceed based on observable facts"
    echo "   4. Never assume execution state"
    
    # Log speculation incidents
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Speculation detected: $SPECULATION_COUNT patterns" >> "$LOG_FILE"
    
    exit 1  # Block response to force correction
else
    exit 0  # Allow response
fi