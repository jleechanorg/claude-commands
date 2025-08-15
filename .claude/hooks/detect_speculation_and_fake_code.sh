#!/bin/bash
# Advanced Speculation & Fake Code Detection Hook for Claude Code
# Lightweight but comprehensive detection using pattern matching and heuristics

# Color codes (defined early to fix initialization order - addresses CodeRabbit comment #2266139941)
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

# Unicode/emoji support detection (defined early)
USE_EMOJI=true
if ! locale | grep -qi 'utf-8'; then USE_EMOJI=false; fi
emoji() { $USE_EMOJI && printf '%s' "$1" || printf '%s' "$2"; }

# Dynamic project root detection with validation
if PROJECT_ROOT_FROM_GIT=$(git rev-parse --show-toplevel 2>/dev/null); then
    PROJECT_ROOT="$PROJECT_ROOT_FROM_GIT"
    # Validate that the project root contains expected markers
    if [ ! -f "$PROJECT_ROOT/CLAUDE.md" ] || [ ! -d "$PROJECT_ROOT/.claude" ]; then
        echo "Warning: Project root validation failed - missing CLAUDE.md or .claude directory" >&2
        exit 0
    fi
else
    # Use PROJECT_ROOT environment variable if set, otherwise fallback
    if [ -n "$PROJECT_ROOT" ]; then
        # PROJECT_ROOT was set by environment - use it (for testing)
        echo "Using PROJECT_ROOT from environment: $PROJECT_ROOT" >&2
    elif [ -f "/home/user/projects/worldarchitect.ai/worktree_human/CLAUDE.md" ]; then
        PROJECT_ROOT="/home/user/projects/worldarchitect.ai/worktree_human"
    else
        echo "Warning: Cannot determine project root and fallback path invalid" >&2
        exit 0
    fi
fi

# SECURITY: Early path validation to prevent attacks
# Enhanced path validation - reject dangerous patterns (only actual traversal sequences)
case "$PROJECT_ROOT" in
    *'/../'*|*'/..')
        echo "❌ Security error: Path traversal pattern detected: $PROJECT_ROOT" >&2
        exit 1
        ;;
    *) 
        # Path looks safe, continue
        ;;
esac

# Validate PROJECT_ROOT is an absolute path and exists
if [[ ! "$PROJECT_ROOT" =~ ^/ ]] || [[ ! -d "$PROJECT_ROOT" ]]; then
    echo "❌ Error: Invalid project root path: $PROJECT_ROOT" >&2
    exit 1
fi
LOG_FILE="/tmp/claude_detection_log.txt"

# Read response text
RESPONSE_TEXT="${1:-$(cat)}"

# EXCLUSION FILTERS - Prevent recursive detection
# Skip analysis if response contains Claude Code internal metadata
if echo "$RESPONSE_TEXT" | grep -q '"session_id".*"tool_input".*"tool_response"'; then
    echo -e "${GREEN}$(emoji "✅" "OK") Hook running: Skipping Claude Code internal metadata${NC}" >&2
    exit 0
fi

# Skip analysis if response contains hook's own pattern definitions
if echo "$RESPONSE_TEXT" | grep -qE 'FAKE_CODE_PATTERNS|SPECULATION_PATTERNS'; then
    echo -e "${GREEN}$(emoji "✅" "OK") Hook running: Skipping pattern definition analysis${NC}" >&2
    exit 0
fi

# Color codes and emoji function already defined above

# SPECULATION PATTERNS - Enhanced from research
declare -A SPECULATION_PATTERNS=(
    # Temporal Speculation
    ["[Ll]et me wait"]="Waiting assumption"
    ["[Ww]ait for.*complet"]="Command completion speculation"
    ["I'll wait for"]="Future waiting speculation"
    ["[Ww]aiting for.*finish"]="Finish waiting assumption"
    ["[Ll]et.*finish"]="Finish assumption"
    
    # State Assumptions  
    ["command.*running"]="Running state assumption"
    ["[Tt]he command.*execut"]="Execution state speculation"
    ["[Rr]unning.*complet"]="Running completion speculation"
    ["system.*processing"]="System processing assumption"
    ["while.*execut"]="Execution process speculation"
    
    # Outcome Predictions
    ["should.*see"]="Outcome prediction"
    ["will.*result"]="Result prediction"
    ["expect.*to"]="Expectation speculation"
    ["likely.*that"]="Probability speculation"
    
    # Process Speculation
    ["during.*process"]="Process timing assumption"
    ["as.*runs"]="Runtime state assumption"
    ["once.*complete"]="Completion timing speculation"
)

# FAKE CODE PATTERNS - Based on research insights
declare -A FAKE_CODE_PATTERNS=(
    # Placeholder Code
    ["TODO:.*implement"]="Placeholder implementation"
    ["FIXME"]="Incomplete code marker"
    ["placeholder"]="Explicit placeholder"
    ["implement.*later"]="Deferred implementation"
    ["dummy.*value"]="Dummy/hardcoded values"
    
    # Non-functional Logic
    ["return.*null.*#.*stub"]="Stub function"
    ["throw.*NotImplemented"]="Not implemented exception"
    ["console\.log.*test"]="Debug/test code left in"
    ["alert.*debug"]="Debug alert code"
    
    # Template/Demo Code
    ["Example.*implementation"]="Example/demo code"
    ["Sample.*code"]="Sample code pattern"
    ["This.*example"]="Example code indicator"
    ["Basic.*template"]="Template code"
    
    # Duplicate Logic Indicators
    ["copy.*from"]="Copied code indication"
    ["similar.*to"]="Code similarity admission"
    ["based.*on.*existing"]="Duplicate logic pattern"
    
    # Parallel Inferior Systems
    ["create.*new.*instead"]="Parallel system creation"
    ["replace.*existing.*with"]="Unnecessary replacement"
    ["simpler.*version.*of"]="Inferior parallel implementation"
    
    # Advanced Fake Patterns (MCP lesson learned)
    ["[Ss]imulate.*call"]="Simulated function call"
    ["in production.*would"]="Production disclaimer"  
    ["would go here"]="Placeholder location marker"
    ["For now.*return.*None"]="Fake null return"
    ["add.*performance.*marker"]="Fake performance tracking"
    ["theoretical.*performance"]="Theoretical simulation"
)

FOUND_SPECULATION=false
FOUND_FAKE_CODE=false
SPECULATION_COUNT=0
FAKE_CODE_COUNT=0

# Check for speculation patterns
for pattern in "${!SPECULATION_PATTERNS[@]}"; do
    if echo "$RESPONSE_TEXT" | grep -i -E "$pattern" > /dev/null 2>&1; then
        FOUND_SPECULATION=true
        ((SPECULATION_COUNT++))

        description="${SPECULATION_PATTERNS[$pattern]}"
        matching_text=$(echo "$RESPONSE_TEXT" | grep -i -E "$pattern" | head -1)

        echo -e "${YELLOW}$(emoji "⚠️" "!") SPECULATION DETECTED${NC}: $description"
        echo -e "   ${RED}Pattern${NC}: $pattern"
        echo -e "   ${RED}Match${NC}: $matching_text"
        echo ""
    fi
done

# Check for fake code patterns
for pattern in "${!FAKE_CODE_PATTERNS[@]}"; do
    if echo "$RESPONSE_TEXT" | grep -i -E "$pattern" > /dev/null 2>&1; then
        FOUND_FAKE_CODE=true
        ((FAKE_CODE_COUNT++))

        description="${FAKE_CODE_PATTERNS[$pattern]}"
        matching_text=$(echo "$RESPONSE_TEXT" | grep -i -E "$pattern" | head -1)

        echo -e "${RED}$(emoji "🚨" "!") FAKE CODE DETECTED${NC}: $description"
        echo -e "   ${RED}Pattern${NC}: $pattern"
        echo -e "   ${RED}Match${NC}: $matching_text"
        echo ""
    fi
done

# Report results - handle speculation and fake code separately for clarity
if [ "$FOUND_SPECULATION" = true ]; then
    echo -e "\n${YELLOW}$(emoji "✅" "OK") SPECULATION DETECTION ACTIVE${NC}: Found speculation patterns in response"
    echo -e "${YELLOW}$(emoji "💡" "!") Speculation Advisory${NC}: Detected $SPECULATION_COUNT speculation pattern(s)"
    echo -e "${YELLOW}Instead of speculating:${NC}"
    echo "   1. Check actual command output/results"
    echo "   2. Look for error messages or completion status"
    echo "   3. Proceed based on observable facts"
    echo "   4. Never assume execution state"
    echo ""
fi

if [ "$FOUND_FAKE_CODE" = true ]; then
    echo ""
    echo -e "${RED}$(emoji "🚨" "!!!")════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${RED}$(emoji "🚨" "!!!") ██ ███████  █████  ██   ██ ███████      ██████  ██████  ██████  ███████${NC}"
    echo -e "${RED}$(emoji "🚨" "!!!") ██ ██      ██   ██ ██  ██  ██          ██      ██    ██ ██   ██ ██     ${NC}"
    echo -e "${RED}$(emoji "🚨" "!!!") ██ █████   ███████ █████   █████       ██      ██    ██ ██   ██ █████  ${NC}"
    echo -e "${RED}$(emoji "🚨" "!!!") ██ ██      ██   ██ ██  ██  ██          ██      ██    ██ ██   ██ ██     ${NC}"
    echo -e "${RED}$(emoji "🚨" "!!!") ██ ██      ██   ██ ██   ██ ███████      ██████  ██████  ██████  ███████${NC}"
    echo -e "${RED}$(emoji "🚨" "!!!")════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${RED}$(emoji "🛑" "X") CRITICAL VIOLATION: FAKE CODE DETECTED IN RESPONSE${NC}"
    echo -e "${RED}$(emoji "⚠️" "!") Detected $FAKE_CODE_COUNT fake/placeholder code pattern(s) - IMMEDIATE ACTION REQUIRED${NC}"
    echo ""
    echo -e "${YELLOW}$(emoji "🔥" "!") THIS VIOLATES CLAUDE.md PRIMARY RULES:${NC}"
    echo -e "${YELLOW}   • Rule: 'NO FAKE IMPLEMENTATIONS' - Always build real, functional code${NC}"
    echo -e "${YELLOW}   • Rule: 'Real implementation > No implementation > Fake implementation'${NC}"
    echo -e "${YELLOW}   • Rule: 'NEVER create placeholder/demo code or duplicate existing protocols'${NC}"
    echo ""
    echo -e "${RED}$(emoji "🚨" "X") MANDATORY CORRECTIVE ACTIONS:${NC}"
    echo -e "${RED}   1. REMOVE all placeholder comments and TODO markers${NC}"
    echo -e "${RED}   2. IMPLEMENT real, functional code that actually works${NC}"
    echo -e "${RED}   3. ENHANCE existing systems instead of creating parallel fake ones${NC}"
    echo -e "${RED}   4. ENSURE code performs its stated purpose, not simulation${NC}"
    echo ""
    echo -e "${GREEN}$(emoji "🛠️" "T") IMMEDIATE COMMAND TO RUN:${NC} ${YELLOW}/fake${NC}"
    echo -e "${GREEN}$(emoji "💡" "!") This will analyze and fix ALL fake code patterns automatically${NC}"
    echo ""
    echo -e "${RED}$(emoji "🚨" "!!!")════════════════════════════════════════════════════════════════════${NC}"
fi

# Show final status if any issues were detected
if [ "$FOUND_SPECULATION" = true ] || [ "$FOUND_FAKE_CODE" = true ]; then
    echo -e "${YELLOW}$(emoji "ℹ️" "i") NOTE${NC}: This is an advisory system. The hook is functioning correctly."
    
    # Log incidents
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Speculation: $SPECULATION_COUNT, Fake Code: $FAKE_CODE_COUNT patterns" >> "$LOG_FILE"
    
    # Create visible warning file in docs directory (CLAUDE.md compliant)
    # Secure warning file creation: validate path and write atomically (addresses CodeRabbit comment #2266139945)
    # Path validation already done at startup for security
    
    mkdir -p "$PROJECT_ROOT/docs"
    WARNING_FILE="$PROJECT_ROOT/docs/CRITICAL_FAKE_CODE_WARNING.md"
    
    # Atomic write using temporary file to prevent partial writes
    WARNING_DIR=$(dirname "$WARNING_FILE")
    TEMP_WARNING_FILE=$(mktemp -p "$WARNING_DIR" 'FAKE_CODE_WARNING.XXXXXX.md')
    # Ensure temp file is cleaned up on unexpected exits
    trap 'rm -f "$TEMP_WARNING_FILE"' EXIT
    cat > "$TEMP_WARNING_FILE" << 'EOF'
# 🚨 CRITICAL: FAKE CODE DETECTED

**IMMEDIATE ACTION REQUIRED** - Claude found fake/placeholder code patterns in your recent work.

## 🛑 VIOLATIONS DETECTED

EOF
    
    # Add detected patterns to temporary file
    echo "**Detected $FAKE_CODE_COUNT fake code pattern(s):**" >> "$TEMP_WARNING_FILE"
    echo "" >> "$TEMP_WARNING_FILE"
    for pattern in "${!FAKE_CODE_PATTERNS[@]}"; do
        if echo "$RESPONSE_TEXT" | grep -i -E "$pattern" > /dev/null 2>&1; then
            description="${FAKE_CODE_PATTERNS[$pattern]}"
            matching_text=$(echo "$RESPONSE_TEXT" | grep -i -E "$pattern" | head -1)
            echo "- **${description}**: \`${matching_text}\`" >> "$TEMP_WARNING_FILE"
        fi
    done
    
    # Generate date outside heredoc for security
    GEN_DATE="$(date)"
    cat >> "$TEMP_WARNING_FILE" << 'EOF'

## 🚨 CLAUDE.md RULE VIOLATIONS

- **Rule**: 'NO FAKE IMPLEMENTATIONS' - Always build real, functional code
- **Rule**: 'Real implementation > No implementation > Fake implementation'  
- **Rule**: 'NEVER create placeholder/demo code or duplicate existing protocols'

## ⚡ IMMEDIATE ACTIONS REQUIRED

1. **REMOVE** all placeholder comments and TODO markers
2. **IMPLEMENT** real, functional code that actually works
3. **ENHANCE** existing systems instead of creating parallel fake ones
4. **ENSURE** code performs its stated purpose, not simulation

## 🛠️ FIX COMMAND

Run this command immediately to fix all violations:

```bash
/fake
```

This will analyze and fix ALL fake code patterns automatically.

## 📋 CLEANUP

After fixing violations, delete this file:

```bash
rm "docs/CRITICAL_FAKE_CODE_WARNING.md"
```

---
EOF
    echo "**Generated**: $GEN_DATE" >> "$TEMP_WARNING_FILE"
    echo "**Hook Version**: Advanced Speculation & Fake Code Detection v2.0" >> "$TEMP_WARNING_FILE"
    
    # Atomically move temporary file to final location
    if mv "$TEMP_WARNING_FILE" "$WARNING_FILE"; then
        trap - EXIT
        echo "✅ Warning file created securely: $WARNING_FILE" >&2
    else
        echo "❌ Error: Failed to create warning file" >&2
        exit 1
    fi

    # Try multiple output methods for maximum visibility
    
    # Method 1: stdout (might be visible in some cases)
    echo "🚨 FAKE CODE WARNING FILE CREATED: Check docs/CRITICAL_FAKE_CODE_WARNING.md"
    
    # Method 2: stderr with exit 2 (BLOCKS operation and sends to Claude AI)
    echo -e "\n${RED}$(emoji "🛑" "BLOCKING") FAKE CODE DETECTED - OPERATION BLOCKED${NC}" >&2
    echo -e "${RED}📄 See: docs/CRITICAL_FAKE_CODE_WARNING.md${NC}" >&2
    echo -e "${RED}🚨 CRITICAL: Fix fake code before continuing - run /fake command${NC}" >&2
    exit 2
else
    # No issues detected - allow response to continue
    echo -e "${GREEN}$(emoji "✅" "OK") Hook running: No fake code detected${NC}" >&2
    exit 0
fi