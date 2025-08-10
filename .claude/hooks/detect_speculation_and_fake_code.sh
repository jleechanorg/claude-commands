#!/bin/bash
# Advanced Speculation & Fake Code Detection Hook for Claude Code
# Lightweight but comprehensive detection using pattern matching and heuristics

# Hardcoded project root (same as git header approach)
PROJECT_ROOT="/home/jleechan/projects/worldarchitect.ai"
LOG_FILE="/tmp/claude_detection_log.txt"

# Read response text
RESPONSE_TEXT="${1:-$(cat)}"

# Color codes
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

# Unicode/emoji support detection
USE_EMOJI=true
if ! locale | grep -qi 'utf-8'; then USE_EMOJI=false; fi
emoji() { $USE_EMOJI && printf '%s' "$1" || printf '%s' "$2"; }

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
    echo -e "\n${RED}$(emoji "✅" "OK") FAKE CODE DETECTION ACTIVE${NC}: Found fake/placeholder code patterns in response"
    echo -e "${RED}$(emoji "🛑" "X") Code Quality Warning${NC}: Detected $FAKE_CODE_COUNT fake/placeholder code pattern(s)"
    echo -e "${RED}Instead of fake code:${NC}"
    echo "   1. Implement real, functional code"
    echo "   2. Enhance existing systems vs creating parallel ones"
    echo "   3. Remove placeholder comments and TODOs"
    echo "   4. Ensure code actually performs its stated purpose"
    echo ""
    echo -e "${GREEN}$(emoji "🔧" "T") RECOMMENDED ACTION${NC}: Run '/fake' command for comprehensive code quality audit"
    echo -e "${GREEN}Usage${NC}: Type '/fake' to analyze and fix all fake/placeholder code patterns"
    echo ""
fi

# Show final status if any issues were detected
if [ "$FOUND_SPECULATION" = true ] || [ "$FOUND_FAKE_CODE" = true ]; then
    echo -e "${YELLOW}$(emoji "ℹ️" "i") NOTE${NC}: This is an advisory system. The hook is functioning correctly."
    
    # Log incidents
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Speculation: $SPECULATION_COUNT, Fake Code: $FAKE_CODE_COUNT patterns" >> "$LOG_FILE"
    
    # Exit 0 - Advisory warnings, allow response to continue
    exit 0
else
    # No issues detected - silent success
    exit 0
fi