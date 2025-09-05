#!/bin/bash

set -euo pipefail

# Ultra-fast direct API wrapper for Cerebras with invisible context extraction

# Pre-flight dependency checks
if ! command -v jq >/dev/null 2>&1; then
  echo "Error: jq is required but not installed." >&2
  exit 5
fi
if ! command -v curl >/dev/null 2>&1; then
  echo "Error: curl is required but not installed." >&2
  exit 5
fi

# Check curl version and set appropriate flags for backward compatibility
# Default to conservative --fail flag for safety
CURL_FAIL_FLAG="--fail"

# Attempt to parse curl version, fall back gracefully on any parsing failure
if CURL_VERSION=$(curl --version 2>/dev/null | head -n1 | sed 's/curl \([0-9]*\.[0-9]*\).*/\1/' 2>/dev/null) && [ -n "$CURL_VERSION" ]; then
    CURL_MAJOR=$(echo "$CURL_VERSION" | cut -d. -f1 2>/dev/null)
    CURL_MINOR=$(echo "$CURL_VERSION" | cut -d. -f2 2>/dev/null)
    
    # Validate that we got numeric values before attempting comparison
    if [[ "$CURL_MAJOR" =~ ^[0-9]+$ ]] && [[ "$CURL_MINOR" =~ ^[0-9]+$ ]]; then
        # --fail-with-body requires curl 7.76.0+ (March 2021)
        if [ "$CURL_MAJOR" -gt 7 ] || { [ "$CURL_MAJOR" -eq 7 ] && [ "$CURL_MINOR" -ge 76 ]; }; then
            CURL_FAIL_FLAG="--fail-with-body"
        fi
    fi
fi

# Parse command line arguments
PROMPT=""
CONTEXT_FILE=""
DISABLE_AUTO_CONTEXT=false
SKIP_CODEGEN_SYS_PROMPT=false
LIGHT_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --context-file)
            if [ $# -lt 2 ] || [[ "$2" == --* ]]; then
                echo "Error: --context-file requires a file path argument" >&2
                exit 1
            fi
            CONTEXT_FILE="$2"
            shift 2
            ;;
        --no-auto-context)
            DISABLE_AUTO_CONTEXT=true
            shift
            ;;
        --skip-codegen-sys-prompt)
            SKIP_CODEGEN_SYS_PROMPT=true
            shift
            ;;
        --light)
            LIGHT_MODE=true
            shift
            ;;
        *)
            PROMPT="$PROMPT $1"
            shift
            ;;
    esac
done

# Remove leading space from PROMPT and validate input
PROMPT=$(echo "$PROMPT" | sed 's/^ *//')

if [ -z "$PROMPT" ]; then
    echo "Usage: cerebras_direct.sh [--context-file FILE] [--no-auto-context] [--skip-codegen-sys-prompt] [--light] <prompt>"
    echo "  --context-file           Include conversation context from file"
    echo "  --no-auto-context        Skip automatic context extraction"
    echo "  --skip-codegen-sys-prompt Use documentation-focused system prompt instead of code generation"
    echo "  --light                  Use light mode (no system prompts and no security filtering)"
    echo ""
    echo "SECURITY WARNING: --light mode bypasses all security checks. Use with trusted prompts only."
    exit 1
fi

# Basic input validation - check for extremely long prompts that could cause issues
if [ ${#PROMPT} -gt 100000 ]; then
    echo "Error: Prompt too long (${#PROMPT} characters). Maximum 100,000 characters allowed." >&2
    exit 1
fi

# Security confirmation for light mode
if [ "$LIGHT_MODE" = true ]; then
    echo "🚨 CRITICAL: Light mode disables ALL security filtering" >&2
    echo "⚠️  This bypasses protection against harmful AI output" >&2
    echo "Continue? [y/N]" >&2
    read -r confirmation
    if [[ ! "$confirmation" =~ ^[Yy]$ ]]; then
        echo "Light mode cancelled for security." >&2
        exit 1
    fi
fi

# Validate API key
API_KEY="${CEREBRAS_API_KEY:-${OPENAI_API_KEY:-}}"
if [ -z "${API_KEY}" ]; then
    echo "Error: CEREBRAS_API_KEY (preferred) or OPENAI_API_KEY must be set." >&2
    echo "Please set your Cerebras API key in environment variables." >&2
    exit 2
fi

# Invisible automatic context extraction (if not disabled and no context file provided)
CONVERSATION_CONTEXT=""
AUTO_CONTEXT_FILE=""

# Cache project root path for performance (avoid repeated git calls)
# Use git -C SCRIPT_DIR to make repo-root detection independent of caller's CWD
# Resolve symlinks for SCRIPT_DIR to handle edge cases with symbolic links
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
if PROJECT_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null)"; then
    :  # git worked, PROJECT_ROOT is set
else
    # Fallback: assume repo root is three levels up from this script: .claude/commands/cerebras/ -> repo root
    PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." 2>/dev/null && pwd)"
    # Validate fallback by checking for CLAUDE.md
    if [ ! -f "$PROJECT_ROOT/CLAUDE.md" ]; then
        # Final fallback: traverse up from SCRIPT_DIR to find CLAUDE.md (preferred over caller CWD)
        CURRENT_DIR="$SCRIPT_DIR"
        PROJECT_ROOT=""  # Reset to ensure ultimate fallback triggers if traversal fails
        while [ "$CURRENT_DIR" != "/" ]; do
            if [ -f "$CURRENT_DIR/CLAUDE.md" ]; then
                PROJECT_ROOT="$CURRENT_DIR"
                break
            fi
            CURRENT_DIR="$(dirname "$CURRENT_DIR")"
        done
        # Ultimate fallback to current directory (now guaranteed to trigger if traversal failed)
        PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
    fi
fi

# Guaranteed cleanup for auto-extracted context (handles errors/interrupts)
cleanup() {
  if [ -n "$AUTO_CONTEXT_FILE" ] && [ -f "$AUTO_CONTEXT_FILE" ]; then
    rm -f "$AUTO_CONTEXT_FILE" 2>/dev/null
  fi
}
trap cleanup EXIT INT TERM

if [ "$DISABLE_AUTO_CONTEXT" = false ] && [ -z "$CONTEXT_FILE" ]; then
    # Create branch-safe temporary file for auto-extracted context
    BRANCH_NAME="$(git branch --show-current 2>/dev/null | sed 's/[^a-zA-Z0-9_-]/_/g')"
    [ -z "$BRANCH_NAME" ] && BRANCH_NAME="main"
    AUTO_CONTEXT_FILE="$(mktemp "/tmp/cerebras_auto_context_${BRANCH_NAME}_XXXXXX.txt" 2>/dev/null)"
    
    # Validate temporary file creation (graceful degradation on failure)
    if [ -z "$AUTO_CONTEXT_FILE" ]; then
        # Continue without context extraction if mktemp fails (invisible operation)
        # No warning output - maintaining invisible operation for Claude Code CLI
        :
    fi
    
    # Silent context extraction (invisible to Claude Code CLI)
    if [ -n "$AUTO_CONTEXT_FILE" ]; then
        # Find the extract_conversation_context.py script (SCRIPT_DIR already set above)
        EXTRACT_SCRIPT="$SCRIPT_DIR/extract_conversation_context.py"
        
        if [ -f "$EXTRACT_SCRIPT" ]; then
            # Extract context using script's default token limit
            # Run from project root to ensure correct path resolution
            if [ -n "${DEBUG:-}" ] || [ -n "${CEREBRAS_DEBUG:-}" ]; then
                # Capture extractor exit code and emit minimal diagnostics when debug is on
                EXTRACTOR_EXIT=0
                (cd "$PROJECT_ROOT" && python3 "$EXTRACT_SCRIPT") >"$AUTO_CONTEXT_FILE" 2>>"${CEREBRAS_DEBUG_LOG:-/tmp/cerebras_context_debug.log}" || EXTRACTOR_EXIT=$?
                if [ "$EXTRACTOR_EXIT" -ne 0 ]; then
                    echo "DEBUG: Context extractor exit code: $EXTRACTOR_EXIT" >>"${CEREBRAS_DEBUG_LOG:-/tmp/cerebras_context_debug.log}"
                fi
            else
                # Mirror debug error handling to maintain invisible operation
                EXTRACTOR_EXIT=0
                (cd "$PROJECT_ROOT" && python3 "$EXTRACT_SCRIPT") >"$AUTO_CONTEXT_FILE" 2>/dev/null || EXTRACTOR_EXIT=$?
                # Continue silently regardless of extraction success - invisible operation maintained
            fi
            
            # Use the auto-extracted context if successful
            if [ -s "$AUTO_CONTEXT_FILE" ]; then
                CONTEXT_FILE="$AUTO_CONTEXT_FILE"
            fi
        fi
    fi
fi

# Load conversation context from file (manual or auto-extracted)
if [ -n "$CONTEXT_FILE" ] && [ -f "$CONTEXT_FILE" ]; then
    CONVERSATION_CONTEXT=$(cat "$CONTEXT_FILE" 2>/dev/null)
fi

# Claude Code system prompt for consistency - can be overridden
if [ "$LIGHT_MODE" = true ]; then
    SYSTEM_PROMPT=""
elif [ "$SKIP_CODEGEN_SYS_PROMPT" = true ]; then
    SYSTEM_PROMPT="You are an expert technical writer and software architect. Generate comprehensive, detailed documentation with complete sections and no placeholder content. Focus on thorough analysis, specific implementation details, and production-ready specifications."
else
    SYSTEM_PROMPT="You are an expert software engineer and code generator. Generate high-quality, production-ready code.

CORE RULES:
- Generate complete, working code implementations
- Follow modern best practices and conventions
- Include proper imports and dependencies
- Use appropriate error handling
- Write clean, maintainable code
- Follow the requested programming language standards

OUTPUT REQUIREMENTS:
- Generate actual code, not references or instructions
- Provide complete implementations, not placeholders
- Include all necessary imports and setup
- Make code production-ready and functional
- Focus on code generation, not tool usage or file operations"
fi

# User task
if [ -n "$CONVERSATION_CONTEXT" ]; then
    if [ -n "$SYSTEM_PROMPT" ]; then
        USER_PROMPT="$CONVERSATION_CONTEXT

---

Task: $PROMPT

Generate the code following the above guidelines with full awareness of the conversation context above."
    else
        USER_PROMPT="$CONVERSATION_CONTEXT

---

Task: $PROMPT

Generate the code with full awareness of the conversation context above."
    fi
else
    if [ -n "$SYSTEM_PROMPT" ]; then
        USER_PROMPT="Task: $PROMPT

Generate the code following the above guidelines."
    else
        USER_PROMPT="Task: $PROMPT

Generate the code."
    fi
fi

# Start timing
START_TIME=$(date +%s%N)

# Direct API call to Cerebras with error handling and timeouts
# Prevent set -e from aborting on curl errors so we can map them explicitly
CURL_EXIT=0

# Prepare messages array - include system prompt only if it's not empty
if [ -n "$SYSTEM_PROMPT" ]; then
    MESSAGES="[
      {\"role\": \"system\", \"content\": $(echo "$SYSTEM_PROMPT" | jq -Rs .)},
      {\"role\": \"user\", \"content\": $(echo "$USER_PROMPT" | jq -Rs .)}
    ]"
else
    MESSAGES="[
      {\"role\": \"user\", \"content\": $(echo "$USER_PROMPT" | jq -Rs .)}
    ]"
fi

HTTP_RESPONSE=$(curl -sS "$CURL_FAIL_FLAG" --connect-timeout 10 --max-time 60 \
  -w "HTTPSTATUS:%{http_code}" -X POST "${CEREBRAS_API_BASE:-https://api.cerebras.ai}/v1/chat/completions" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"qwen-3-coder-480b\",
    \"messages\": $MESSAGES,
    \"max_tokens\": 1000000,
    \"temperature\": 0.1,
    \"stream\": false
  }") || CURL_EXIT=$?

# On transport or HTTP-level failures, emit the raw body (if any) and standardize exit code
if [ "$CURL_EXIT" -ne 0 ]; then
  [ -n "$HTTP_RESPONSE" ] && echo "$HTTP_RESPONSE" >&2
  echo "API Error: curl failed with exit code $CURL_EXIT" >&2
  exit 3
fi
    
# Extract HTTP status and body safely (no subshell whitespace issues)
HTTP_STATUS="${HTTP_RESPONSE##*HTTPSTATUS:}"
HTTP_BODY="${HTTP_RESPONSE%HTTPSTATUS:*}"

# Check for API errors
if [ "$HTTP_STATUS" -ne 200 ]; then
    ERROR_MSG=$(echo "$HTTP_BODY" | jq -r '.error.message // .message // "Unknown error"')
    echo "API Error ($HTTP_STATUS): $ERROR_MSG" >&2
    exit 3
fi

RESPONSE="$HTTP_BODY"

# Calculate elapsed time
END_TIME=$(date +%s%N)
ELAPSED_MS=$(( (END_TIME - START_TIME) / 1000000 ))

# Extract and display the response (OpenAI format)
CONTENT=$(echo "$RESPONSE" | jq -r '.choices[0].message.content // empty')
if [ -z "$CONTENT" ]; then
    echo "Error: Unexpected API response format." >&2
    echo "Raw response:" >&2
    echo "$RESPONSE" >&2
    exit 4
fi

# Count lines in generated content
LINE_COUNT=$(echo "$CONTENT" | wc -l | tr -d ' ')

# Get branch name for output directory
CURRENT_BRANCH=$(git -C "$SCRIPT_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
OUTPUT_DIR="/tmp/${CURRENT_BRANCH}"
mkdir -p "$OUTPUT_DIR"

# Generate timestamp for unique filename
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_FILE="${OUTPUT_DIR}/cerebras_output_${TIMESTAMP}.md"

# Write content to file and also display
echo "$CONTENT" > "$OUTPUT_FILE"

# Show timing at the beginning with line count and mode indicator
echo ""
if [ "$LIGHT_MODE" = true ]; then
    echo "⚡ CEREBRAS LIGHT MODE: ${ELAPSED_MS}ms (${LINE_COUNT} lines) ⚡"
    echo "⚠️  Light Mode Active - No System Prompts or Security Filtering"
else
    echo "🚀🚀🚀 CEREBRAS GENERATED IN ${ELAPSED_MS}ms (${LINE_COUNT} lines) 🚀🚀🚀"
fi
echo ""
echo "Output saved to: $OUTPUT_FILE"
echo ""
echo "$CONTENT"

# Show prominent timing display at the end
echo ""
echo "🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀"
echo "⚡ CEREBRAS BLAZING FAST: ${ELAPSED_MS}ms"
echo "🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀"

# Silent cleanup of auto-extracted context file (invisible to Claude Code CLI)
if [ -n "$AUTO_CONTEXT_FILE" ] && [ -f "$AUTO_CONTEXT_FILE" ]; then
    rm -f "$AUTO_CONTEXT_FILE" 2>/dev/null
fi
