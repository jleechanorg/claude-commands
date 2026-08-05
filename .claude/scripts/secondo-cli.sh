#!/bin/bash

# Second Opinion CLI - Get multi-model AI feedback
# Usage: ~/.claude/scripts/secondo-cli.sh [design|code-review|bugs|all] [question]
# Explicit error handling is used (no `set -e`) to preserve interactive shells.

# Configuration
MCP_URL="https://ai-universe-backend-dev-114133832173.us-central1.run.app/mcp"
TIMEOUT=180

# AI Universe Firebase env (required so auth-cli.mjs can SILENTLY refresh the
# 1-hour idToken via the refresh token). Without these, `auth-cli.mjs status`
# falsely reports "Not authenticated" once the idToken expires (~hourly), even
# though the long-lived refresh token is still valid. API key is the public
# AI Universe shared key (safe to expose per Firebase security model).
export VITE_AI_UNIVERSE_FIREBASE_PROJECT_ID="${VITE_AI_UNIVERSE_FIREBASE_PROJECT_ID:-ai-universe-b3551}"
export VITE_AI_UNIVERSE_FIREBASE_AUTH_DOMAIN="${VITE_AI_UNIVERSE_FIREBASE_AUTH_DOMAIN:-ai-universe-b3551.firebaseapp.com}"
export VITE_AI_UNIVERSE_FIREBASE_API_KEY="${VITE_AI_UNIVERSE_FIREBASE_API_KEY:-AIzaSyDWT4aEG2UoKEtTxozniGC6uPZi1fgjtG8}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored messages
error() { echo -e "${RED}❌ $1${NC}" >&2; }
success() { echo -e "${GREEN}✅ $1${NC}"; }
info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }

# Check required dependencies
check_dependencies() {
  local missing=()

  if ! command -v http >/dev/null 2>&1 && ! command -v curl >/dev/null 2>&1; then
    missing+=("httpie-or-curl")
  fi

  if ! command -v jq >/dev/null 2>&1; then
    missing+=("jq")
  fi

  if ! command -v node >/dev/null 2>&1; then
    missing+=("node")
  fi

  if [ ${#missing[@]} -gt 0 ]; then
    error "Missing required dependencies: ${missing[*]}"
    echo ""
    echo "Installation tips:"
    if ! command -v http >/dev/null 2>&1; then
      echo "  HTTPie:   https://httpie.io/docs/cli/installation"
      echo "  curl:     Usually pre-installed (https://curl.se/)"
    fi
    if ! command -v jq >/dev/null 2>&1; then
      echo "  jq:       https://jqlang.github.io/jq/download/"
    fi
    if ! command -v node >/dev/null 2>&1; then
      echo "  Node.js:  https://nodejs.org/en/download"
    fi
    return 1
  fi

  return 0
}

# Check authentication
check_auth() {
  if ! check_dependencies; then
    return 1
  fi
  if ! node ~/.claude/scripts/auth-cli.mjs status >/dev/null 2>&1; then
    error "Not authenticated"
    echo ""
    echo "Please authenticate first:"
    echo "  node ~/.claude/scripts/auth-cli.mjs login"
    echo ""
    return 1
  fi
}

# Get authentication token
get_token() {
  TOKEN=$(node ~/.claude/scripts/auth-cli.mjs token 2>/dev/null)
  if [ $? -ne 0 ] || [ -z "$TOKEN" ]; then
    error "Failed to get authentication token"
    return 1
  fi
  echo "$TOKEN"
}

# Construct question based on feedback type
construct_question() {
  local feedback_type="$1"
  local custom_question="$2"
  local context="$3"

  if [ -n "$custom_question" ]; then
    echo "$custom_question"
    return
  fi

  case "$feedback_type" in
    design)
      cat <<EOF
Design Review Request: $context

Analyze the architectural decisions:
- Is the design pattern appropriate?
- Are there better alternatives?
- What are potential scalability issues?
- Industry best practices comparison?
EOF
      ;;
    code-review)
      cat <<EOF
Code Review Request: $context

Review this code for:
- Security vulnerabilities
- Performance issues
- Code quality and maintainability
- TypeScript/JavaScript best practices
- Potential bugs or edge cases
EOF
      ;;
    bugs)
      cat <<EOF
Bug Investigation: $context

Analyze potential bugs:
- Race conditions or timing issues
- Error handling gaps
- Edge cases not covered
- Type safety concerns
- Memory leaks or resource issues
EOF
      ;;
    all|*)
      cat <<EOF
Comprehensive Review: $context

Provide multi-model feedback on:
1. Design & Architecture
2. Code Quality & Security
3. Potential Bugs & Edge Cases

Include industry sources and actionable recommendations.
EOF
      ;;
  esac
}

# Send MCP request
send_mcp_request() {
  local token="$1"
  local question="$2"

  local request_json=$(cat <<EOF
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "agent.second_opinion",
    "arguments": {
      "question": $(echo "$question" | jq -Rs .)
    }
  },
  "id": 1
}
EOF
)

  # Check if HTTPie is available, fallback to curl
  if command -v http >/dev/null 2>&1; then
    echo "$request_json" | http POST "$MCP_URL" \
      Accept:'application/json, text/event-stream' \
      Authorization:"Bearer $token" \
      --timeout="$TIMEOUT" \
      --print=b 2>&1
  elif command -v curl >/dev/null 2>&1; then
    curl -s -X POST "$MCP_URL" \
      -H "Accept: application/json, text/event-stream" \
      -H "Authorization: Bearer $token" \
      -H "Content-Type: application/json" \
      --max-time "$TIMEOUT" \
      -d "$request_json" 2>&1
  else
    error "Neither HTTPie nor curl is installed. Please install one of them."
    echo "  brew install httpie  # macOS"
    echo "  apt-get install httpie  # Ubuntu/Debian"
    echo "  - OR -"
    echo "  curl is usually pre-installed on most systems"
    return 1
  fi
}

# Parse and display response
display_response() {
  local response="$1"

  # Check for errors (JSON-RPC standard: .error.message and .error.data)
  if echo "$response" | jq -e '.error' >/dev/null 2>&1; then
    local error_msg=$(echo "$response" | jq -r '.error.message // (.error|tostring)')
    local error_details=$(echo "$response" | jq -r '.error.data // empty')

    error "MCP Error: $error_msg"

    if [ -n "$error_details" ]; then
      if echo "$error_details" | jq -e 'has("resetTime")' >/dev/null 2>&1; then
        local reset_time=$(echo "$error_details" | jq -r '.resetTime')
        warn "Rate limit exceeded. Resets at: $reset_time"
      fi
    fi

    return 1
  fi

  # Extract the response content (try nested .result.result first, fallback to .result)
  local content=$(echo "$response" | jq -r '.result.result.content[0].text // .result.content[0].text // empty')

  if [ -z "$content" ]; then
    error "Invalid response format"
    warn "Expected: .result.result.content[0].text or .result.content[0].text in MCP response"
    return 1
  fi

  # Parse the JSON content
  local parsed
  if ! parsed=$(echo "$content" | jq '.'); then
    error "Failed to parse MCP response content"
    return 1
  fi

  # Display summary
  echo ""
  echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
  echo -e "${CYAN}📊 Multi-Model Second Opinion Results${NC}"
  echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
  echo ""

  local total_models=$(echo "$parsed" | jq -r '.summary.totalModels // "N/A"')
  local total_tokens=$(echo "$parsed" | jq -r '.summary.totalTokens // "N/A"')
  local total_cost=$(echo "$parsed" | jq -r '.summary.totalCost // "N/A"')

  info "Models Consulted: $total_models"
  info "Total Tokens: $total_tokens"
  if [ "$total_cost" = "N/A" ]; then
    info "Total Cost: N/A"
  else
    info "Total Cost: \$$total_cost"
  fi
  echo ""

  # Display primary opinion
  echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${GREEN}🎯 Primary Opinion ($(echo "$parsed" | jq -r '.primary.modelDisplayName'))${NC}"
  echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo ""
  echo "$parsed" | jq -r '.primary.response' | fold -s -w 80
  echo ""

  # Display secondary opinions
  local secondary_count=$(echo "$parsed" | jq '.secondaryOpinions | length')

  if [ "$secondary_count" -gt 0 ]; then
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}💡 Secondary Perspectives${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    for i in $(seq 0 $((secondary_count - 1))); do
      local model=$(echo "$parsed" | jq -r ".secondaryOpinions[$i].modelDisplayName")
      local opinion=$(echo "$parsed" | jq -r ".secondaryOpinions[$i].response")

      echo -e "${YELLOW}### $model${NC}"
      echo ""
      echo "$opinion" | fold -s -w 80
      echo ""
    done
  fi

  # Display synthesis
  if echo "$parsed" | jq -e '.synthesis' >/dev/null 2>&1; then
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}✨ Final Synthesis (Multi-Model Consensus)${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "$parsed" | jq -r '.synthesis.response' | fold -s -w 80
    echo ""
  fi

  echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
  echo ""
}

# Main execution
main() {
  local feedback_type="${1:-all}"
  shift || true
  local custom_question=""
  local context=""

  if [[ ! "$feedback_type" =~ ^(design|code-review|bugs|all)$ ]]; then
    custom_question="$feedback_type"
    if [ $# -gt 0 ]; then
      custom_question+=" $*"
    fi
    feedback_type="all"
  else
    custom_question="$*"
  fi

  info "Getting multi-model second opinion..."
  echo ""

  if ! check_auth; then
    return 1
  fi

  local token
  if ! token=$(get_token); then
    return 1
  fi

  if [ -z "${custom_question// }" ]; then
    context="Current development context"
    warn "No specific question provided. Using feedback type: $feedback_type"
    echo ""
  fi

  local question
  if ! question=$(construct_question "$feedback_type" "$custom_question" "$context"); then
    error "Failed to construct question payload"
    return 1
  fi

  info "Sending request to MCP server..."
  echo ""

  local response
  if ! response=$(send_mcp_request "$token" "$question"); then
    return 1
  fi

  if ! display_response "$response"; then
    return 1
  fi

  return 0
}

# Run main with all arguments
if ! main "$@"; then
  exit 1
fi
