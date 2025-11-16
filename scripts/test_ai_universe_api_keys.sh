#!/bin/bash
#
# Test API Keys Against AI Universe Repository
#
# This script clones the ai_universe repo and tests API keys against
# the actual services used by the repository.
#
# Usage:
#   bash scripts/test_ai_universe_api_keys.sh
#   Or from project root:
#   ./scripts/test_ai_universe_api_keys.sh
#

set -uo pipefail
# Don't use set -e so we can handle test failures gracefully

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
WORK_DIR="/tmp/ai_universe_api_test_$$"
REPO_URL="https://github.com/jleechanorg/ai_universe.git"
REPO_DIR="${WORK_DIR}/ai_universe"

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}Cleaning up...${NC}"
    if [ -d "${WORK_DIR}" ]; then
        rm -rf "${WORK_DIR}"
    fi
}
trap cleanup EXIT

# Load API keys from bashrc
load_keys_from_bashrc() {
    local bashrc_path="${HOME}/.bashrc"

    if [ ! -f "${bashrc_path}" ]; then
        echo -e "${RED}Error: ${bashrc_path} not found${NC}" >&2
        return 1
    fi

    # Parse bashrc to extract export statements
    # Handle comments and quoted values properly
    while IFS= read -r line || [ -n "${line}" ]; do
        # Remove comments (but preserve # inside quotes)
        local in_quotes=false
        local quote_char=""
        local cleaned_line=""
        for (( i=0; i<${#line}; i++ )); do
            local char="${line:$i:1}"
            if [[ "${char}" == "\"" ]] || [[ "${char}" == "'" ]]; then
                if [[ -z "${quote_char}" ]]; then
                    quote_char="${char}"
                    in_quotes=true
                elif [[ "${char}" == "${quote_char}" ]]; then
                    quote_char=""
                    in_quotes=false
                fi
            elif [[ "${char}" == "#" ]] && [[ "${in_quotes}" == false ]]; then
                break
            fi
            cleaned_line+="${char}"
        done

        # Trim whitespace
        cleaned_line=$(echo "${cleaned_line}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

        if [[ "${cleaned_line}" =~ ^export[[:space:]]+([A-Z_]+)= ]]; then
            local key_name="${BASH_REMATCH[1]}"
            if [[ "${key_name}" =~ ^(GITHUB_TOKEN|OPENAI_API_KEY|PERPLEXITY_API_KEY|OPENROUTER_API_KEY|CEREBRAS_API_KEY|GROK_API_KEY|ANTHROPIC_API_KEY|GEMINI_API_KEY)$ ]]; then
                # Extract value (handle quoted strings)
                local value
                if [[ "${cleaned_line}" =~ =\"([^\"]+)\" ]]; then
                    value="${BASH_REMATCH[1]}"
                elif [[ "${cleaned_line}" =~ =\'([^\']+)\' ]]; then
                    value="${BASH_REMATCH[1]}"
                elif [[ "${cleaned_line}" =~ =([^[:space:]#]+) ]]; then
                    value="${BASH_REMATCH[1]}"
                fi
                if [[ -n "${value}" ]]; then
                    export "${key_name}"="${value}"
                fi
            fi
        fi
    done < "${bashrc_path}"
}

# Test GitHub token with ai_universe repo
test_github_repo_access() {
    local token="${1:-}"

    if [ -z "${token}" ]; then
        echo -e "${RED}❌ GITHUB_TOKEN not set${NC}"
        return 1
    fi

    echo -e "${BLUE}Testing GitHub repo access...${NC}"

    # Test GitHub API access
    local response
    response=$(curl -s -w "\n%{http_code}" \
        -H "Authorization: Bearer ${token}" \
        -H "Accept: application/vnd.github.v3+json" \
        "https://api.github.com/repos/jleechanorg/ai_universe" 2>/dev/null || echo "ERROR\n000")

    local http_code
    http_code=$(echo "${response}" | tail -n1)
    local body
    body=$(echo "${response}" | sed '$d')

    if [ "${http_code}" = "200" ]; then
        local repo_name
        repo_name=$(echo "${body}" | grep -o '"full_name":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
        echo -e "${GREEN}✅ GitHub token valid - Can access repo: ${repo_name}${NC}"
        return 0
    elif [ "${http_code}" = "401" ] || [ "${http_code}" = "403" ]; then
        echo -e "${RED}❌ GitHub token invalid or insufficient permissions${NC}"
        return 1
    else
        echo -e "${YELLOW}⚠️  GitHub API returned status ${http_code}${NC}"
        return 1
    fi
}

# Test Gemini API (used by ai_universe)
test_gemini_api() {
    local api_key="${1:-}"

    if [ -z "${api_key}" ]; then
        echo -e "${RED}❌ GEMINI_API_KEY not set${NC}"
        return 1
    fi

    echo -e "${BLUE}Testing Gemini API...${NC}"

    # Test Gemini API by listing models
    local response
    response=$(curl -s -w "\n%{http_code}" \
        "https://generativelanguage.googleapis.com/v1beta/models?key=${api_key}" 2>/dev/null || echo "ERROR\n000")

    local http_code
    http_code=$(echo "${response}" | tail -n1)
    local body
    body=$(echo "${response}" | sed '$d')

    if [ "${http_code}" = "200" ]; then
        local model_count
        model_count=$(echo "${body}" | grep -o '"models"' | wc -l || echo "0")
        echo -e "${GREEN}✅ Gemini API key valid - Can list models${NC}"
        return 0
    elif [ "${http_code}" = "403" ]; then
        echo -e "${RED}❌ Gemini API key invalid or quota exceeded${NC}"
        return 1
    else
        echo -e "${YELLOW}⚠️  Gemini API returned status ${http_code}${NC}"
        return 1
    fi
}

# Test OpenAI API (used for multi-model synthesis)
test_openai_api() {
    local api_key="${1:-}"

    if [ -z "${api_key}" ]; then
        echo -e "${RED}❌ OPENAI_API_KEY not set${NC}"
        return 1
    fi

    echo -e "${BLUE}Testing OpenAI API...${NC}"

    local response
    response=$(curl -s -w "\n%{http_code}" \
        -H "Authorization: Bearer ${api_key}" \
        -H "Content-Type: application/json" \
        -d '{"model":"gpt-3.5-turbo","messages":[{"role":"user","content":"test"}],"max_tokens":5}' \
        "https://api.openai.com/v1/chat/completions" 2>/dev/null || echo "ERROR\n000")

    local http_code
    http_code=$(echo "${response}" | tail -n1)

    if [ "${http_code}" = "200" ]; then
        echo -e "${GREEN}✅ OpenAI API key valid${NC}"
        return 0
    elif [ "${http_code}" = "401" ]; then
        echo -e "${RED}❌ OpenAI API key invalid${NC}"
        return 1
    else
        echo -e "${YELLOW}⚠️  OpenAI API returned status ${http_code}${NC}"
        return 1
    fi
}

# Test Anthropic API (used for multi-model synthesis)
test_anthropic_api() {
    local api_key="${1:-}"

    if [ -z "${api_key}" ]; then
        echo -e "${RED}❌ ANTHROPIC_API_KEY not set${NC}"
        return 1
    fi

    echo -e "${BLUE}Testing Anthropic API...${NC}"

    local response
    response=$(curl -s -w "\n%{http_code}" \
        -H "x-api-key: ${api_key}" \
        -H "anthropic-version: 2023-06-01" \
        -H "Content-Type: application/json" \
        -d '{"model":"claude-3-haiku-20240307","max_tokens":5,"messages":[{"role":"user","content":"test"}]}' \
        "https://api.anthropic.com/v1/messages" 2>/dev/null || echo "ERROR\n000")

    local http_code
    http_code=$(echo "${response}" | tail -n1)
    local body
    body=$(echo "${response}" | sed '$d')

    if [ "${http_code}" = "200" ]; then
        echo -e "${GREEN}✅ Anthropic API key valid${NC}"
        return 0
    elif [ "${http_code}" = "401" ]; then
        echo -e "${RED}❌ Anthropic API key invalid${NC}"
        return 1
    elif [ "${http_code}" = "400" ] && echo "${body}" | grep -q "credit balance"; then
        echo -e "${GREEN}✅ Anthropic API key valid (credit balance too low)${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  Anthropic API returned status ${http_code}${NC}"
        return 1
    fi
}

# Test Perplexity API (used for multi-model synthesis)
test_perplexity_api() {
    local api_key="${1:-}"

    if [ -z "${api_key}" ]; then
        echo -e "${RED}❌ PERPLEXITY_API_KEY not set${NC}"
        return 1
    fi

    echo -e "${BLUE}Testing Perplexity API...${NC}"

    local response
    response=$(curl -s -w "\n%{http_code}" \
        -H "Authorization: Bearer ${api_key}" \
        -H "Content-Type: application/json" \
        -d '{"model":"sonar","messages":[{"role":"user","content":"test"}],"max_tokens":5}' \
        "https://api.perplexity.ai/chat/completions" 2>/dev/null || echo "ERROR\n000")

    local http_code
    http_code=$(echo "${response}" | tail -n1)

    if [ "${http_code}" = "200" ]; then
        echo -e "${GREEN}✅ Perplexity API key valid${NC}"
        return 0
    elif [ "${http_code}" = "401" ]; then
        echo -e "${RED}❌ Perplexity API key invalid${NC}"
        return 1
    else
        echo -e "${YELLOW}⚠️  Perplexity API returned status ${http_code}${NC}"
        return 1
    fi
}

# Test OpenRouter API (used for multi-model synthesis)
test_openrouter_api() {
    local api_key="${1:-}"

    if [ -z "${api_key}" ]; then
        echo -e "${RED}❌ OPENROUTER_API_KEY not set${NC}"
        return 1
    fi

    echo -e "${BLUE}Testing OpenRouter API...${NC}"

    local response
    response=$(curl -s -w "\n%{http_code}" \
        -H "Authorization: Bearer ${api_key}" \
        -H "Content-Type: application/json" \
        -d '{"model":"openai/gpt-3.5-turbo","messages":[{"role":"user","content":"test"}],"max_tokens":5}' \
        "https://openrouter.ai/api/v1/chat/completions" 2>/dev/null || echo "ERROR\n000")

    local http_code
    http_code=$(echo "${response}" | tail -n1)

    if [ "${http_code}" = "200" ]; then
        echo -e "${GREEN}✅ OpenRouter API key valid${NC}"
        return 0
    elif [ "${http_code}" = "401" ]; then
        echo -e "${RED}❌ OpenRouter API key invalid${NC}"
        return 1
    else
        echo -e "${YELLOW}⚠️  OpenRouter API returned status ${http_code}${NC}"
        return 1
    fi
}

# Clone ai_universe repo
clone_repo() {
    echo -e "${BLUE}Cloning ai_universe repository...${NC}"

    mkdir -p "${WORK_DIR}"

    if ! git clone --depth 1 "${REPO_URL}" "${REPO_DIR}" 2>/dev/null; then
        echo -e "${RED}❌ Failed to clone repository${NC}" >&2
        return 1
    fi

    echo -e "${GREEN}✅ Repository cloned successfully${NC}"
    return 0
}

# Check if repo uses specific API keys
check_repo_api_usage() {
    echo -e "\n${BLUE}Checking API key usage in repository...${NC}"

    if [ ! -d "${REPO_DIR}" ]; then
        echo -e "${RED}❌ Repository not cloned${NC}"
        return 1
    fi

    # Check for API key references in code
    local key_files
    key_files=$(find "${REPO_DIR}" -type f \( -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.mjs" \) \
        -exec grep -l "API_KEY\|api.*key" {} \; 2>/dev/null | head -10 || true)

    if [ -n "${key_files}" ]; then
        echo -e "${GREEN}✅ Found API key references in:${NC}"
        echo "${key_files}" | while read -r file; do
            echo "  - ${file#${REPO_DIR}/}"
        done
    else
        echo -e "${YELLOW}⚠️  No API key references found${NC}"
    fi
}

# Main execution
main() {
    echo -e "${BLUE}${BLUE}========================================${NC}"
    echo -e "${BLUE}AI Universe API Key Testing${NC}"
    echo -e "${BLUE}========================================${NC}\n"

    # Load keys from bashrc
    echo -e "${YELLOW}Loading API keys from ~/.bashrc...${NC}"
    load_keys_from_bashrc

    # Clone repository
    if ! clone_repo; then
        echo -e "${RED}Failed to clone repository. Testing API keys without repo...${NC}"
    else
        check_repo_api_usage
    fi

    echo -e "\n${BLUE}Testing API keys...${NC}\n"

    # Test each API key
    local passed=0
    local failed=0

    echo ""
    if test_github_repo_access "${GITHUB_TOKEN:-}"; then
        ((passed++)) || true
    else
        ((failed++)) || true
    fi

    echo ""
    if test_gemini_api "${GEMINI_API_KEY:-}"; then
        ((passed++)) || true
    else
        ((failed++)) || true
    fi

    echo ""
    if test_openai_api "${OPENAI_API_KEY:-}"; then
        ((passed++)) || true
    else
        ((failed++)) || true
    fi

    echo ""
    if test_anthropic_api "${ANTHROPIC_API_KEY:-}"; then
        ((passed++)) || true
    else
        ((failed++)) || true
    fi

    echo ""
    if test_perplexity_api "${PERPLEXITY_API_KEY:-}"; then
        ((passed++)) || true
    else
        ((failed++)) || true
    fi

    echo ""
    if test_openrouter_api "${OPENROUTER_API_KEY:-}"; then
        ((passed++)) || true
    else
        ((failed++)) || true
    fi

    # Summary
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}Test Summary${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo -e "${GREEN}Passed: ${passed}${NC}"
    echo -e "${RED}Failed: ${failed}${NC}"
    echo -e "${BLUE}Total: $((passed + failed))${NC}"

    if [ ${failed} -eq 0 ]; then
        echo -e "\n${GREEN}✅ All API keys are valid!${NC}"
        return 0
    else
        echo -e "\n${YELLOW}⚠️  Some API keys failed validation${NC}"
        return 1
    fi
}

# Run main function
main "$@"
