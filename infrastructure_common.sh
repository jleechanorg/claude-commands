#!/bin/bash
# Common Infrastructure Functions - Portable Configuration Support
# Source this file in infrastructure scripts for consistent configuration

# Load configuration if available
load_infrastructure_config() {
    local config_file=".infrastructure.conf"
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local project_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

    # Try to find config file in various locations
    local config_paths=(
        "$project_root/$config_file"
        "$script_dir/$config_file"
        "$HOME/$config_file"
        "./$config_file"
    )

    for config_path in "${config_paths[@]}"; do
        if [[ -f "$config_path" ]]; then
            echo "📝 Loading configuration from: $config_path"
            source "$config_path"
            return 0
        fi
    done

    echo "ℹ️  No configuration file found. Using auto-detection and defaults."
    echo "   Create .infrastructure.conf from .infrastructure.conf.example for custom settings."
    return 1
}

# Auto-detect source directory
detect_source_directory() {
    local source_dir="${PROJECT_SRC_DIR:-}"

    if [[ -z "$source_dir" ]]; then
        # Try common source directory patterns
        for dir in src lib app mvp_site source code; do
            if [[ -d "$dir" ]]; then
                source_dir="$dir"
                break
            fi
        done

        # Fallback to current directory if no common patterns found
        if [[ -z "$source_dir" ]]; then
            source_dir="."
        fi
    fi

    echo "$source_dir"
}

# Auto-detect project name
detect_project_name() {
    local project_name="${PROJECT_NAME:-}"

    if [[ -z "$project_name" ]]; then
        project_name="$(basename "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null || echo "project")"
    fi

    echo "$project_name"
}

# Auto-detect repository URL
detect_repo_url() {
    local repo_url="${GITHUB_REPO_URL:-}"

    if [[ -z "$repo_url" ]]; then
        if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
            repo_url="$(git config --get remote.origin.url 2>/dev/null || echo '')"
            # Convert SSH to HTTPS format if needed
            if [[ "$repo_url" =~ ^git@github\.com:(.+)\.git$ ]]; then
                repo_url="https://github.com/${BASH_REMATCH[1]}"
            fi
        fi
    fi

    echo "$repo_url"
}

# Auto-detect email
detect_email() {
    local email="${EMAIL_USER:-}"

    if [[ -z "$email" ]]; then
        email="$(git config user.email 2>/dev/null || echo '')"
    fi

    echo "$email"
}

# Get project root directory
get_project_root() {
    echo "${PROJECT_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
}

# Initialize infrastructure environment
init_infrastructure_env() {
    echo "🔧 Initializing portable infrastructure environment..."

    # Load configuration
    load_infrastructure_config

    # Set up auto-detected variables if not already set
    export PROJECT_NAME="${PROJECT_NAME:-$(detect_project_name)}"
    export PROJECT_SRC_DIR="${PROJECT_SRC_DIR:-$(detect_source_directory)}"
    export PROJECT_ROOT="${PROJECT_ROOT:-$(get_project_root)}"
    export GITHUB_REPO_URL="${GITHUB_REPO_URL:-$(detect_repo_url)}"
    export EMAIL_USER="${EMAIL_USER:-$(detect_email)}"

    # Set up derived variables
    export COVERAGE_DIR="${COVERAGE_DIR:-/tmp/${PROJECT_NAME}/coverage}"
    export VPYTHON_PATH="${VPYTHON_PATH:-${PROJECT_ROOT}/vpython}"
    export TEST_SERVER_SCRIPT="${TEST_SERVER_SCRIPT:-${PROJECT_ROOT}/test_server_manager.sh}"

    echo "✅ Infrastructure environment initialized:"
    echo "   Project: $PROJECT_NAME"
    echo "   Source: $PROJECT_SRC_DIR"
    echo "   Root: $PROJECT_ROOT"
    echo "   Repo: ${GITHUB_REPO_URL:-<not detected>}"
    echo "   Email: ${EMAIL_USER:-<not detected>}"
}

# Colors for output
export RED='\033[0;31m'
export GREEN='\033[0;32m'
export YELLOW='\033[1;33m'
export BLUE='\033[0;34m'
export NC='\033[0m' # No Color

# Common output functions
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

print_error() {
    echo -e "${RED}[FAIL]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}
