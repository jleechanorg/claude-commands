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
        *)
            PROMPT="$PROMPT $1"
            shift
            ;;
    esac
done

# Remove leading space from PROMPT and validate input
PROMPT=$(echo "$PROMPT" | sed 's/^ *//')

# Input validation - prevent command injection
if [[ "$PROMPT" =~ [\$\`\;\|\&] ]]; then
    echo "Error: Invalid characters detected in prompt." >&2
    exit 1
fi

if [ -z "$PROMPT" ]; then
    echo "Usage: cerebras_direct.sh [--context-file FILE] [--no-auto-context] <prompt>"
    echo "  --context-file      Include conversation context from file"
    echo "  --no-auto-context   Skip automatic context extraction"
    exit 1
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
        # Find the extract_conversation_context.py script
        SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        EXTRACT_SCRIPT="$SCRIPT_DIR/extract_conversation_context.py"
        
        if [ -f "$EXTRACT_SCRIPT" ]; then
            # Extract context silently using script's default token limit (20K)
            python3 "$EXTRACT_SCRIPT" > "$AUTO_CONTEXT_FILE" 2>/dev/null
            
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

# Claude Code system prompt for consistency
SYSTEM_PROMPT="You are an expert software engineer following Claude Code guidelines.

CRITICAL RULES:
- Be concise, direct, and to the point
- Minimize output tokens while maintaining quality
- NEVER add comments unless explicitly asked
- NEVER create new files unless absolutely necessary
- Always prefer editing existing files
- Follow existing code conventions and patterns in the project
- Use existing libraries already in the project
- Follow security best practices
- Assist with defensive security tasks only

FOLLOWING CONVENTIONS:
- Check neighboring files and package.json/requirements.txt/Cargo.toml for existing libraries
- Look at existing components/modules to understand code style before creating new ones
- Examine imports and surrounding context to maintain framework consistency
- Consider framework choice, naming conventions, typing patterns from existing code
- Make changes that are idiomatic to the existing codebase

FILE HANDLING:
- ALWAYS read files before editing to understand current state
- Use targeted edits instead of full file replacements
- Preserve existing functionality unless explicitly asked to change it
- When creating new components, follow patterns from similar existing components

CODE REFERENCES:
- When referencing specific functions include pattern: file_path:line_number
- This helps users navigate to exact locations in the code
- Example: 'Fixed the auth bug in src/auth/login.py:42'

OUTPUT FORMAT:
- Output code only unless explanation requested
- No preamble or postamble
- No unnecessary commentary
- Just the code that solves the task
- Include file_path:line references when mentioning specific code locations"

# User task
if [ -n "$CONVERSATION_CONTEXT" ]; then
    USER_PROMPT="$CONVERSATION_CONTEXT

---

Task: $PROMPT

Generate the code following the above guidelines with full awareness of the conversation context above."
else
    USER_PROMPT="Task: $PROMPT

Generate the code following the above guidelines."
fi

# Start timing
START_TIME=$(date +%s%N)

# Direct API call to Cerebras with error handling and timeouts
# Prevent set -e from aborting on curl errors so we can map them explicitly
CURL_EXIT=0
HTTP_RESPONSE=$(curl -sS "$CURL_FAIL_FLAG" --connect-timeout 10 --max-time 60 \
  -w "HTTPSTATUS:%{http_code}" -X POST "${CEREBRAS_API_BASE:-https://api.cerebras.ai}/v1/chat/completions" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"qwen-3-coder-480b\",
    \"messages\": [
      {\"role\": \"system\", \"content\": $(echo "$SYSTEM_PROMPT" | jq -Rs .)},
      {\"role\": \"user\", \"content\": $(echo "$USER_PROMPT" | jq -Rs .)}
    ],
    \"max_tokens\": 32768,
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

# Show timing at the beginning with line count
echo ""
echo "🚀🚀🚀 CEREBRAS GENERATED IN ${ELAPSED_MS}ms (${LINE_COUNT} lines) 🚀🚀🚀"
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
