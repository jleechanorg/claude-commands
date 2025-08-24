#!/bin/bash

# Ultra-fast direct API wrapper for Cerebras

# Parse command line arguments
PROMPT=""
CONTEXT_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --context-file)
            CONTEXT_FILE="$2"
            shift 2
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
    echo "Usage: cerebras_direct.sh [--context-file FILE] <prompt>"
    echo "  --context-file   Include conversation context from file"
    exit 1
fi

# Validate API key
API_KEY="${CEREBRAS_API_KEY:-${OPENAI_API_KEY:-}}"
if [ -z "${API_KEY}" ]; then
    echo "Error: CEREBRAS_API_KEY (preferred) or OPENAI_API_KEY must be set." >&2
    echo "Please set your Cerebras API key in environment variables." >&2
    exit 2
fi

# Load conversation context if provided
CONVERSATION_CONTEXT=""
if [ -n "$CONTEXT_FILE" ] && [ -f "$CONTEXT_FILE" ]; then
    CONVERSATION_CONTEXT=$(cat "$CONTEXT_FILE")
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

# Direct API call to Cerebras with error handling
HTTP_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST "https://api.cerebras.ai/v1/chat/completions" \
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
  }")
    
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
