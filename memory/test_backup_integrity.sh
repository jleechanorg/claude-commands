#!/bin/bash
# Test Memory Backup Integrity
# Version: 1.0.0

set -e

# Configuration
MEMORY_FILE="${MEMORY_FILE:-$HOME/.cache/mcp-memory/memory.json}"
MEMORY_FILENAME="memory.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔍 Testing Memory Backup Integrity..."
echo ""

# Function to validate NDJSON file
validate_ndjson() {
    local file=$1
    local line_num=0
    local errors=0
    
    while IFS= read -r line; do
        line_num=$((line_num + 1))
        if [ -z "$line" ]; then
            continue
        fi
        
        if ! echo "$line" | jq . >/dev/null 2>&1; then
            echo -e "${RED}❌ Line $line_num: Invalid JSON${NC}"
            echo "   $line" | head -c 80
            echo "..."
            errors=$((errors + 1))
        fi
    done < "$file"
    
    return $errors
}

# Check if memory file exists
if [ ! -f "$MEMORY_FILE" ]; then
    echo -e "${RED}❌ Memory file not found: $MEMORY_FILE${NC}"
    exit 1
fi

echo "📁 Checking: $MEMORY_FILE"
TOTAL_LINES=$(wc -l < "$MEMORY_FILE")
ENTITY_COUNT=$(grep -c '"type":"entity"' "$MEMORY_FILE" 2>/dev/null || echo "0")
RELATION_COUNT=$(grep -c '"type":"relation"' "$MEMORY_FILE" 2>/dev/null || echo "0")

echo "   Total lines: $TOTAL_LINES"
echo "   Entities: $ENTITY_COUNT"
echo "   Relations: $RELATION_COUNT"
echo ""

# Validate JSON integrity
echo "🔧 Validating JSON integrity..."
if validate_ndjson "$MEMORY_FILE"; then
    echo -e "${GREEN}✅ All lines are valid JSON${NC}"
else
    echo -e "${RED}❌ Found $? invalid JSON lines${NC}"
fi

# Check last line
echo ""
echo "📝 Checking last line..."
LAST_LINE=$(tail -1 "$MEMORY_FILE")
if echo "$LAST_LINE" | jq . >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Last line is valid JSON${NC}"
    echo "   Type: $(echo "$LAST_LINE" | jq -r .type)"
else
    echo -e "${RED}❌ Last line is corrupted:${NC}"
    echo "   $LAST_LINE"
fi

# Check backup locations
echo ""
echo "🔄 Checking backup locations..."

# Local backup
if [ -f "memory.json" ]; then
    LOCAL_LINES=$(wc -l < memory.json)
    echo "   Local backup: $LOCAL_LINES lines"
    
    if [ "$LOCAL_LINES" -eq "$TOTAL_LINES" ]; then
        echo -e "${GREEN}   ✅ Local backup matches source${NC}"
    else
        echo -e "${YELLOW}   ⚠️  Local backup differs: $LOCAL_LINES vs $TOTAL_LINES lines${NC}"
    fi
fi

# GitHub backup
CURRENT_BRANCH=$(git branch --show-current)
DATE_STAMP=$(date +"%Y-%m-%d")
BACKUP_BRANCH="memory-backup-${DATE_STAMP}"

if git rev-parse --verify origin/${BACKUP_BRANCH} >/dev/null 2>&1; then
    GITHUB_LINES=$(git show origin/${BACKUP_BRANCH}:$MEMORY_FILENAME 2>/dev/null | wc -l)
    echo "   GitHub backup: $GITHUB_LINES lines (branch: $BACKUP_BRANCH)"
    
    if [ "$GITHUB_LINES" -eq "$TOTAL_LINES" ]; then
        echo -e "${GREEN}   ✅ GitHub backup matches source${NC}"
    else
        echo -e "${YELLOW}   ⚠️  GitHub backup differs: $GITHUB_LINES vs $TOTAL_LINES lines${NC}"
    fi
else
    echo -e "${YELLOW}   ⚠️  No GitHub backup found for today${NC}"
fi

echo ""
echo "✅ Integrity check complete"