#!/bin/bash

# Token Configuration Helper Script
# Provides a systematic way to load tokens from ~/.token file
# Used by claude_mcp.sh and other scripts requiring authentication tokens

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Global variables for token status
GITHUB_TOKEN_LOADED=false
PERPLEXITY_TOKEN_LOADED=false
TOKEN_FILE_EXISTS=false

# Function to log token loading events
log_token_event() {
    local message="$1"
    local level="$2"  # INFO, WARN, ERROR

    case "$level" in
        "ERROR")
            echo -e "${RED}❌ $message${NC}" >&2
            ;;
        "WARN")
            echo -e "${YELLOW}⚠️ $message${NC}" >&2
            ;;
        *)
            echo -e "${BLUE}📋 $message${NC}"
            ;;
    esac
}

# Function to check if a token is valid format
validate_github_token() {
    local token="$1"
    if [[ "$token" =~ ^ghp_[A-Za-z0-9]{36}$ ]] || [[ "$token" =~ ^github_pat_[A-Za-z0-9_]{50,}$ ]]; then
        return 0
    else
        return 1
    fi
}

validate_perplexity_token() {
    local token="$1"
    if [[ "$token" =~ ^pplx-[A-Za-z0-9]{40,}$ ]]; then
        return 0
    else
        return 1
    fi
}

# Function to load tokens from ~/.token file
load_tokens() {
    local quiet_mode="$1"  # Set to "quiet" to suppress output

    local HOME_TOKEN_FILE="$HOME/.token"

    if [ ! -f "$HOME_TOKEN_FILE" ]; then
        TOKEN_FILE_EXISTS=false
        if [ "$quiet_mode" != "quiet" ]; then
            log_token_event "Token file not found at $HOME_TOKEN_FILE" "ERROR"
            echo -e "${YELLOW}📋 To create token file:${NC}"
            echo -e "${YELLOW}   1. Generate GitHub token at: https://github.com/settings/tokens${NC}"
            echo -e "${YELLOW}   2. Generate Perplexity token at: https://www.perplexity.ai/settings/api${NC}"
            echo -e "${YELLOW}   3. Create ~/.token file with:${NC}"
            echo -e "${YELLOW}      export GITHUB_TOKEN=\"ghp_your_github_token_here\"${NC}"
            echo -e "${YELLOW}      export PERPLEXITY_API_KEY=\"pplx_your_perplexity_token_here\"${NC}"
            echo -e "${YELLOW}   4. chmod 600 ~/.token${NC}"
        fi
        return 1
    fi

    TOKEN_FILE_EXISTS=true

    if [ "$quiet_mode" != "quiet" ]; then
        log_token_event "Loading tokens from $HOME_TOKEN_FILE" "INFO"
    fi

    # Source the token file to load environment variables
    if source "$HOME_TOKEN_FILE" 2>/dev/null; then
        # Verify and export GitHub token
        if [ -n "$GITHUB_TOKEN" ]; then
            if validate_github_token "$GITHUB_TOKEN"; then
                export GITHUB_PERSONAL_ACCESS_TOKEN="$GITHUB_TOKEN"
                export GITHUB_TOKEN="$GITHUB_TOKEN"
                GITHUB_TOKEN_LOADED=true
                if [ "$quiet_mode" != "quiet" ]; then
                    log_token_event "GitHub token loaded and validated" "INFO"
                fi
            else
                if [ "$quiet_mode" != "quiet" ]; then
                    log_token_event "GitHub token format is invalid" "WARN"
                fi
            fi
        else
            if [ "$quiet_mode" != "quiet" ]; then
                log_token_event "GITHUB_TOKEN not found in token file" "WARN"
            fi
        fi

        # Verify and export Perplexity token
        if [ -n "$PERPLEXITY_API_KEY" ]; then
            if validate_perplexity_token "$PERPLEXITY_API_KEY"; then
                export PERPLEXITY_API_KEY="$PERPLEXITY_API_KEY"
                PERPLEXITY_TOKEN_LOADED=true
                if [ "$quiet_mode" != "quiet" ]; then
                    log_token_event "Perplexity API key loaded and validated" "INFO"
                fi
            else
                if [ "$quiet_mode" != "quiet" ]; then
                    log_token_event "Perplexity API key format may be invalid" "WARN"
                fi
            fi
        else
            if [ "$quiet_mode" != "quiet" ]; then
                log_token_event "PERPLEXITY_API_KEY not found in token file" "WARN"
            fi
        fi

        return 0
    else
        if [ "$quiet_mode" != "quiet" ]; then
            log_token_event "Failed to source token file - check syntax" "ERROR"
        fi
        return 1
    fi
}

# Function to check token status
check_token_status() {
    echo -e "${BLUE}🔍 Token Configuration Status${NC}"
    echo "=========================="

    if [ "$TOKEN_FILE_EXISTS" = true ]; then
        echo -e "${GREEN}✅ Token file exists: $HOME/.token${NC}"
    else
        echo -e "${RED}❌ Token file missing: $HOME/.token${NC}"
    fi

    if [ "$GITHUB_TOKEN_LOADED" = true ]; then
        echo -e "${GREEN}✅ GitHub token: Loaded and valid${NC}"
    else
        echo -e "${RED}❌ GitHub token: Not loaded or invalid${NC}"
    fi

    if [ "$PERPLEXITY_TOKEN_LOADED" = true ]; then
        echo -e "${GREEN}✅ Perplexity token: Loaded and valid${NC}"
    else
        echo -e "${YELLOW}⚠️ Perplexity token: Not loaded${NC}"
    fi
}

# Function to test GitHub token by making API call
test_github_token() {
    if [ "$GITHUB_TOKEN_LOADED" != true ]; then
        log_token_event "GitHub token not loaded - cannot test" "ERROR"
        return 1
    fi

    log_token_event "Testing GitHub token validity..." "INFO"

    # Create temporary curl config to hide token from process listings
    local curl_config=$(mktemp)
    printf 'header = "Authorization: Bearer %s"\n' "$GITHUB_TOKEN" > "$curl_config"

    # Test token with secure curl configuration
    if curl --silent --fail --config "$curl_config" --url https://api.github.com/user >/dev/null 2>&1; then
        log_token_event "GitHub token is valid and working" "INFO"
        rm -f "$curl_config"
        return 0
    else
        log_token_event "GitHub token appears to be invalid or expired" "ERROR"
        echo -e "${YELLOW}💡 Generate new token at: https://github.com/settings/tokens${NC}"
        echo -e "${YELLOW}💡 Required scopes: repo, read:org, read:user${NC}"
        rm -f "$curl_config"
        return 1
    fi
}

# Function to create template token file
create_token_template() {
    local token_file="$HOME/.token"

    if [ -f "$token_file" ]; then
        log_token_event "Token file already exists at $token_file" "WARN"
        return 1
    fi

    cat > "$token_file" << 'EOF'
# Token Configuration File
# This file should be kept secure with chmod 600 permissions
#
# GitHub Personal Access Token
# Generate at: https://github.com/settings/tokens
# Required scopes: repo, read:org, read:user
export GITHUB_TOKEN="ghp_your_github_token_here"

# Perplexity API Key (optional)
# Generate at: https://www.perplexity.ai/settings/api
export PERPLEXITY_API_KEY="pplx_your_perplexity_token_here"
EOF

    chmod 600 "$token_file"

    log_token_event "Created token template at $token_file" "INFO"
    echo -e "${YELLOW}📝 Please edit $token_file and add your actual tokens${NC}"
    return 0
}

# If script is called directly, provide command-line interface
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    case "${1:-load}" in
        "load")
            load_tokens
            ;;
        "status")
            load_tokens quiet
            check_token_status
            ;;
        "test")
            load_tokens quiet
            test_github_token
            ;;
        "create")
            create_token_template
            ;;
        "help")
            echo "Token Configuration Helper"
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  load     Load tokens from ~/.token (default)"
            echo "  status   Show token configuration status"
            echo "  test     Test GitHub token validity"
            echo "  create   Create template ~/.token file"
            echo "  help     Show this help message"
            ;;
        *)
            echo "Unknown command: $1"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
fi
