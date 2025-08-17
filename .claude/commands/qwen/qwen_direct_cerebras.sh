#!/bin/bash

# Ultra-fast direct API wrapper
# Supports both Cerebras (default) and Anthropic (--sonnet flag)

# Parse command line arguments
USE_SONNET=false
PROMPT=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --sonnet)
            USE_SONNET=true
            shift
            ;;
        *)
            PROMPT="$PROMPT $1"
            shift
            ;;
    esac
done

# Remove leading space from PROMPT
PROMPT=$(echo "$PROMPT" | sed 's/^ *//')

if [ -z "$PROMPT" ]; then
    echo "Usage: qwen_direct_cerebras.sh [--sonnet] <prompt>"
    echo "  --sonnet    Use Anthropic Claude Sonnet instead of Qwen"
    exit 1
fi

# Validate API keys based on chosen mode
if [ "$USE_SONNET" = true ]; then
    if [ -z "${CLAUDE_API_KEY}" ]; then
        echo "Error: CLAUDE_API_KEY environment variable is not set." >&2
        echo "Please set your Anthropic API key: export CLAUDE_API_KEY=your_key_here" >&2
        exit 2
    fi
else
    # Prefer CEREBRAS_API_KEY; allow OPENAI_API_KEY as fallback for compatibility
    API_KEY="${CEREBRAS_API_KEY:-${OPENAI_API_KEY:-}}"
    if [ -z "${API_KEY}" ]; then
        echo "Error: CEREBRAS_API_KEY (preferred) or OPENAI_API_KEY must be set." >&2
        echo "Set your Cerebras key: export CEREBRAS_API_KEY=your_cerebras_key_here" >&2
        exit 2
    fi
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
USER_PROMPT="Task: $PROMPT

Generate the code following the above guidelines."

# Start timing
START_TIME=$(date +%s%N)

# Choose API based on flag
if [ "$USE_SONNET" = true ]; then
    # Anthropic Claude Sonnet API call with error handling
    HTTP_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST "https://api.anthropic.com/v1/messages" \
      -H "x-api-key: ${CLAUDE_API_KEY}" \
      -H "Content-Type: application/json" \
      -H "anthropic-version: 2023-06-01" \
      -d "{
        \"model\": \"claude-3-5-sonnet-20241022\",
        \"max_tokens\": 2000,
        \"temperature\": 0.1,
        \"system\": $(echo "$SYSTEM_PROMPT" | jq -Rs .),
        \"messages\": [
          {\"role\": \"user\", \"content\": $(echo "$USER_PROMPT" | jq -Rs .)}
        ]
      }")
    
    # Extract HTTP status and body
    HTTP_BODY=$(echo $HTTP_RESPONSE | sed -E 's/HTTPSTATUS\:[0-9]{3}$//')
    HTTP_STATUS=$(echo $HTTP_RESPONSE | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')
    
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
    
    # Show timing at the beginning
    echo ""
    echo "🧠🧠🧠 SONNET GENERATED IN ${ELAPSED_MS}ms 🧠🧠🧠"
    echo ""
    
    # Extract and display the response (Anthropic format)
    CONTENT=$(echo "$RESPONSE" | jq -r '.content[0].text // empty')
    if [ -z "$CONTENT" ]; then
        echo "Error: Unexpected API response format." >&2
        echo "Raw response:" >&2
        echo "$RESPONSE" >&2
        exit 4
    fi
    echo "$CONTENT"
    
    # Show prominent timing display at the end
    echo ""
    echo "🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠"
    echo "⚡ SONNET PERFORMANCE: ${ELAPSED_MS}ms"
    echo "🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠"
else
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
        \"max_tokens\": 2000,
        \"temperature\": 0.1,
        \"stream\": false
      }")
    
    # Extract HTTP status and body
    HTTP_BODY=$(echo $HTTP_RESPONSE | sed -E 's/HTTPSTATUS\:[0-9]{3}$//')
    HTTP_STATUS=$(echo $HTTP_RESPONSE | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')
    
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
    
    # Show timing at the beginning
    echo ""
    echo "🚀🚀🚀 QWEN GENERATED IN ${ELAPSED_MS}ms 🚀🚀🚀"
    echo ""
    
    # Extract and display the response (OpenAI format)
    CONTENT=$(echo "$RESPONSE" | jq -r '.choices[0].message.content // empty')
    if [ -z "$CONTENT" ]; then
        echo "Error: Unexpected API response format." >&2
        echo "Raw response:" >&2
        echo "$RESPONSE" >&2
        exit 4
    fi
    echo "$CONTENT"
    
    # Show prominent timing display at the end
    echo ""
    echo "🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀"
    echo "⚡ QWEN BLAZING FAST: ${ELAPSED_MS}ms (vs Sonnet comparison)"
    echo "🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀"
fi