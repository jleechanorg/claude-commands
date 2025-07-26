#!/bin/bash
# analyze_code_authenticity.sh - LLM-based fake code detection
# Uses Claude's natural language understanding instead of keyword matching

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Get changed files
get_changed_files() {
    # Get list of changed files vs default branch
    local DEFAULT_BRANCH diff_cmd
    DEFAULT_BRANCH=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | cut -d'/' -f2)
    DEFAULT_BRANCH=${DEFAULT_BRANCH:-main}
    diff_cmd=$(git diff --name-only -z "origin/${DEFAULT_BRANCH}"...HEAD 2>/dev/null ||
               git diff --name-only -z "${DEFAULT_BRANCH}"...HEAD 2>/dev/null || true)
    printf '%s' "$diff_cmd"
}

# Create analysis markdown file with code content
create_analysis_file() {
    local analysis_file="$1"
    local changed_files="$2"

    cat > "$analysis_file" <<EOF
# Code Authenticity Analysis

## Task
Analyze the following code changes for fake, simulated, or demo code patterns.

## Definition of Fake Code
- Hardcoded responses that simulate real logic without implementing it
- Functions that claim sophistication but use simple keyword matching
- Mock API responses with placeholder data
- Code that appears to demonstrate a concept rather than implement real functionality
- Generic template responses that don't reflect actual analysis

## Example of Fake Code Pattern
\`\`\`python
def _create_contextual_response(self, body: str, user: str, file_path: str, line: str) -> str:
    body_lower = body.lower()
    if 'error' in body_lower or 'bug' in body_lower:
        response_parts.append("Thank you for identifying this issue! ")
    elif 'suggestion' in body_lower:
        response_parts.append("Excellent suggestion! ")
\`\`\`
This is fake because it uses hardcoded responses based on simple keyword detection.

## Code to Analyze

EOF

    # Add each changed file's content using proper NUL-delimited array processing
    local changed_files_array
    if [[ -n "$changed_files" ]]; then
        mapfile -d '' -t changed_files_array < <(printf '%s' "$changed_files")

        if ((${#changed_files_array[@]})); then
            for file in "${changed_files_array[@]}"; do
                if [[ -n "$file" && -f "$file" ]]; then
                    # Only analyze code files
                    case "$file" in
                        *.py|*.js|*.ts|*.jsx|*.tsx|*.java|*.cpp|*.c|*.go|*.rs)
                            echo "### File: $file" >> "$analysis_file"
                            echo "" >> "$analysis_file"
                            echo "\`\`\`${file##*.}" >> "$analysis_file"
                            cat "$file" >> "$analysis_file"
                            echo "" >> "$analysis_file"
                            echo "\`\`\`" >> "$analysis_file"
                            echo "" >> "$analysis_file"
                            ;;
                    esac
                fi
            done
        fi
    fi

    cat >> "$analysis_file" <<EOF

## Analysis Request
Please analyze each file and identify:
1. Any fake/simulated code patterns
2. Functions that claim sophistication but use simple logic
3. Hardcoded responses or mock implementations
4. Code that appears to be for demonstration rather than production

For each issue found, provide:
- File name and approximate line number
- Type of fake pattern detected
- Brief explanation of why it's considered fake
- Suggestion for improvement (if applicable)

If no fake code patterns are found, simply respond with "✅ No fake code patterns detected"

If fake patterns are found, start the response with "🚨 FAKE CODE DETECTED" and list the issues.
EOF
}

# Use Claude to analyze the code
analyze_with_claude() {
    local analysis_file="$1"

    # Try to use Claude Code CLI to analyze the file
    if command -v claudepw &> /dev/null; then
        echo -e "${YELLOW}🔍 Analyzing code with Claude LLM...${NC}"

        # Use claudepw to analyze the markdown file with permissions skipped
        claudepw --dangerously-skip-permissions --file "$analysis_file" --prompt "Analyze this code for fake/demo patterns as described in the file." 2>>"$analysis_file.error" || {
            echo -e "${YELLOW}⚠️  Claude CLI not available or encountered an error. Check $analysis_file.error for details.${NC}"
            return 1
        }
    elif command -v claude &> /dev/null; then
        echo -e "${YELLOW}🔍 Analyzing code with Claude LLM...${NC}"

        # Fallback to regular claude if claudepw not available
        claude --dangerously-skip-permissions --file "$analysis_file" --prompt "Analyze this code for fake/demo patterns as described in the file." 2>>"$analysis_file.error" || {
            echo -e "${YELLOW}⚠️  Claude CLI not available or encountered an error. Check $analysis_file.error for details.${NC}"
            return 1
        }
    else
        echo -e "${YELLOW}⚠️  Claude CLI not available, skipping fake code detection${NC}"
        return 1
    fi
}

# Main function
main() {
    echo -e "${GREEN}🔍 Checking code authenticity with LLM analysis...${NC}"

    # Get changed files
    changed_files=$(get_changed_files)

    if [[ -z "$changed_files" ]]; then
        echo "✅ No code files changed"
        return 0
    fi

    # Create temporary analysis file
    analysis_file=$(mktemp "/tmp/code_analysis_XXXXXX.md")

    # Set up cleanup trap
    trap 'rm -f "$analysis_file" "$analysis_file.error"' EXIT

    # Create the analysis markdown
    create_analysis_file "$analysis_file" "$changed_files"

    echo "📝 Created analysis file: $analysis_file"
    echo "Files to analyze:"
    if [[ -n "$changed_files" ]]; then
        local changed_files_array
        mapfile -d '' -t changed_files_array < <(printf '%s' "$changed_files")

        if ((${#changed_files_array[@]})); then
            for file in "${changed_files_array[@]}"; do
                if [[ -n "$file" && -f "$file" ]]; then
                    case "$file" in
                        *.py|*.js|*.ts|*.jsx|*.tsx|*.java|*.cpp|*.c|*.go|*.rs)
                            echo "  - $file"
                            ;;
                    esac
                fi
            done
        fi
    fi

    # Analyze with Claude
    if analysis_result=$(analyze_with_claude "$analysis_file"); then
        echo ""
        echo "Analysis Result:"
        echo "$analysis_result"

        # Check if fake code was detected
        if echo "$analysis_result" | grep -q "🚨 FAKE CODE DETECTED"; then
            echo -e "\n${RED}🚨 Fake code patterns detected!${NC}"

            # Call /learn to document the patterns
            echo -e "${YELLOW}📚 Calling /learn to document fake code patterns...${NC}"

            # Try to call the learn command
            if [[ -f "./claude_command_scripts/commands/learn.sh" ]]; then
                temp_file=$(mktemp)
                echo "Fake code patterns detected: $analysis_result" > "$temp_file"
                ./claude_command_scripts/commands/learn.sh < "$temp_file"
                rm -f "$temp_file"
            elif command -v claudepw &> /dev/null; then
                claudepw --dangerously-skip-permissions --prompt "/learn Fake code patterns detected in push: $analysis_result"
            elif command -v claude &> /dev/null; then
                claude --dangerously-skip-permissions --prompt "/learn Fake code patterns detected in push: $analysis_result"
            fi

            echo -e "\n${YELLOW}⚠️  Consider reviewing the flagged code before pushing${NC}"
            return 1  # Warning level
        else
            echo -e "\n${GREEN}✅ No fake code patterns detected${NC}"
            return 0
        fi
    else
        echo -e "${YELLOW}⚠️  Could not perform LLM analysis${NC}"
        return 0  # Continue if analysis fails
    fi
}

# Run main function
main "$@"
