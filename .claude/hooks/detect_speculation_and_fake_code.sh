#!/usr/bin/env bash
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
    ["LET_ME_WAIT"]="Waiting assumption"
    ["WAIT_FOR_COMPLET"]="Command completion speculation"
    ["ILL_WAIT_FOR"]="Future waiting speculation"
    ["WAITING_FOR_FINISH"]="Finish waiting assumption"
    ["LET_FINISH"]="Finish assumption"
    ["COMMAND_RUNNING"]="Running state assumption"
    ["THE_COMMAND_EXECUT"]="Execution state speculation"
    ["RUNNING_COMPLET"]="Running completion speculation"
    ["SYSTEM_PROCESSING"]="System processing assumption"
    ["WHILE_EXECUT"]="Execution process speculation"
    ["SHOULD_SEE"]="Outcome prediction"
    ["WILL_RESULT"]="Result prediction"
    ["EXPECT_TO"]="Expectation speculation"
    ["LIKELY_THAT"]="Probability speculation"
    ["DURING_PROCESS"]="Process timing assumption"
    ["AS_RUNS"]="Runtime state assumption"
    ["ONCE_COMPLETE"]="Completion timing speculation"
)

# FAKE CODE PATTERNS - Based on research insights
declare -A FAKE_CODE_PATTERNS=(
    ["TODO_IMPLEMENT"]="Placeholder implementation"
    ["FIXME"]="Incomplete code marker"
    ["PLACEHOLDER"]="Explicit placeholder"
    ["IMPLEMENT_LATER"]="Deferred implementation"
    ["DUMMY_VALUE"]="Dummy/hardcoded values"
    ["RETURN_NULL_STUB"]="Stub function"
    ["THROW_NOT_IMPLEMENTED"]="Not implemented exception"
    ["CONSOLE_LOG_TEST"]="Debug/test code left in"
    ["ALERT_DEBUG"]="Debug alert code"
    ["EXAMPLE_IMPLEMENTATION"]="Example/demo code"
    ["SAMPLE_CODE"]="Sample code pattern"
    ["THIS_EXAMPLE"]="Example code indicator"
    ["BASIC_TEMPLATE"]="Template code"
    ["COPY_FROM"]="Copied code indication"
    ["SIMILAR_TO"]="Code similarity admission"
    ["BASED_ON_EXISTING"]="Duplicate logic pattern"
    ["CREATE_NEW_INSTEAD"]="Parallel system creation"
    ["REPLACE_EXISTING_WITH"]="Unnecessary replacement"
    ["SIMPLER_VERSION_OF"]="Inferior parallel implementation"
    ["SIMULATE_CALL"]="Simulated function call"
    ["IN_PRODUCTION_WOULD"]="Production disclaimer"
    ["WOULD_GO_HERE"]="Placeholder location marker"
    ["FOR_NOW_RETURN_NONE"]="Fake null return"
    ["ADD_PERFORMANCE_MARKER"]="Fake performance tracking"
    ["THEORETICAL_PERFORMANCE"]="Theoretical simulation"
    ["ESTIMATED_LINE_COUNT"]="Estimated line count"
    ["APPROXIMATELY_NUMERIC"]="Numeric approximation"
    ["AROUND_LINES"]="Line count estimation"
    ["ROUGHLY_NUMERIC"]="Rough numeric estimate"
    ["TABLE_ESTIMATION"]="Table estimation marker"
    ["ESTIMATED_LINES"]="Line count estimation"
)

FOUND_SPECULATION=false
FOUND_FAKE_CODE=false
SPECULATION_COUNT=0
FAKE_CODE_COUNT=0

# Function to get regex pattern from key
get_regex_pattern() {
    case $1 in
        "LET_ME_WAIT") echo "[Ll]et me wait" ;;
        "WAIT_FOR_COMPLET") echo "[Ww]ait for.*complet" ;;
        "ILL_WAIT_FOR") echo "I'll wait for" ;;
        "WAITING_FOR_FINISH") echo "[Ww]aiting for.*finish" ;;
        "LET_FINISH") echo "[Ll]et.*finish" ;;
        "COMMAND_RUNNING") echo "command.*running" ;;
        "THE_COMMAND_EXECUT") echo "[Tt]he command.*execut" ;;
        "RUNNING_COMPLET") echo "[Rr]unning.*complet" ;;
        "SYSTEM_PROCESSING") echo "system.*processing" ;;
        "WHILE_EXECUT") echo "while.*execut" ;;
        "SHOULD_SEE") echo "should.*see" ;;
        "WILL_RESULT") echo "will.*result" ;;
        "EXPECT_TO") echo "expect.*to" ;;
        "LIKELY_THAT") echo "likely.*that" ;;
        "DURING_PROCESS") echo "during.*process" ;;
        "AS_RUNS") echo "as.*runs" ;;
        "ONCE_COMPLETE") echo "once.*complete" ;;
        "TODO_IMPLEMENT") echo "TODO:.*implement" ;;
        "PLACEHOLDER") echo "placeholder" ;;
        "IMPLEMENT_LATER") echo "implement.*later" ;;
        "DUMMY_VALUE") echo "dummy.*value" ;;
        "RETURN_NULL_STUB") echo "return.*null.*#.*stub" ;;
        "THROW_NOT_IMPLEMENTED") echo "throw.*NotImplemented" ;;
        "CONSOLE_LOG_TEST") echo "console\.log.*test" ;;
        "ALERT_DEBUG") echo "alert.*debug" ;;
        "EXAMPLE_IMPLEMENTATION") echo "Example.*implementation" ;;
        "SAMPLE_CODE") echo "Sample.*code" ;;
        "THIS_EXAMPLE") echo "This.*example" ;;
        "BASIC_TEMPLATE") echo "Basic.*template" ;;
        "COPY_FROM") echo "copy.*from" ;;
        "SIMILAR_TO") echo "similar.*to" ;;
        "BASED_ON_EXISTING") echo "based.*on.*existing" ;;
        "CREATE_NEW_INSTEAD") echo "create.*new.*instead" ;;
        "REPLACE_EXISTING_WITH") echo "replace.*existing.*with" ;;
        "SIMPLER_VERSION_OF") echo "simpler.*version.*of" ;;
        "SIMULATE_CALL") echo "[Ss]imulate.*call" ;;
        "IN_PRODUCTION_WOULD") echo "in production.*would" ;;
        "WOULD_GO_HERE") echo "would go here" ;;
        "FOR_NOW_RETURN_NONE") echo "For now.*return.*None" ;;
        "ADD_PERFORMANCE_MARKER") echo "add.*performance.*marker" ;;
        "THEORETICAL_PERFORMANCE") echo "theoretical.*performance" ;;
        "ESTIMATED_LINE_COUNT") echo "~[0-9]+.*lines" ;;
        "APPROXIMATELY_NUMERIC") echo "approximately.*[0-9]+" ;;
        "AROUND_LINES") echo "around.*[0-9]+.*lines" ;;
        "ROUGHLY_NUMERIC") echo "roughly.*[0-9]+" ;;
        "TABLE_ESTIMATION") echo "\\|.*~.*\\|" ;;
        "ESTIMATED_LINES") echo "estimated.*[0-9]+.*lines" ;;
        *) echo "$1" ;;
    esac
}

# Check for speculation patterns
for pattern_key in "${!SPECULATION_PATTERNS[@]}"; do
    regex_pattern=$(get_regex_pattern "$pattern_key")
    if echo "$RESPONSE_TEXT" | grep -i -E "$regex_pattern" > /dev/null 2>&1; then
        FOUND_SPECULATION=true
        ((SPECULATION_COUNT++))

        description="${SPECULATION_PATTERNS[$pattern_key]}"
        matching_text=$(echo "$RESPONSE_TEXT" | grep -i -E "$regex_pattern" | head -1)

        echo -e "${YELLOW}$(emoji "⚠️" "!") SPECULATION DETECTED${NC}: $description"
        echo -e "   ${RED}Pattern${NC}: $regex_pattern"
        echo -e "   ${RED}Match${NC}: $matching_text"
        echo ""
    fi
done

# Check for fake code patterns
for pattern_key in "${!FAKE_CODE_PATTERNS[@]}"; do
    regex_pattern=$(get_regex_pattern "$pattern_key")
    if echo "$RESPONSE_TEXT" | grep -i -E "$regex_pattern" > /dev/null 2>&1; then
        FOUND_FAKE_CODE=true
        ((FAKE_CODE_COUNT++))

        description="${FAKE_CODE_PATTERNS[$pattern_key]}"
        matching_text=$(echo "$RESPONSE_TEXT" | grep -i -E "$regex_pattern" | head -1)

        echo -e "${RED}$(emoji "🚨" "!") FAKE CODE DETECTED${NC}: $description"
        echo -e "   ${RED}Pattern${NC}: $regex_pattern"
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
    for pattern_key in "${!FAKE_CODE_PATTERNS[@]}"; do
        regex_pattern=$(get_regex_pattern "$pattern_key")
        if echo "$RESPONSE_TEXT" | grep -i -E "$regex_pattern" > /dev/null 2>&1; then
            description="${FAKE_CODE_PATTERNS[$pattern_key]}"
            matching_text=$(echo "$RESPONSE_TEXT" | grep -i -E "$regex_pattern" | head -1)
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
