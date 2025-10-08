#!/bin/bash
# Shared MCP installer logic used by both Claude and Codex wrappers.

__MCP_COMMON_PREV_SHELLOPTS=$(set +o)
set -euo pipefail

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "❌ scripts/mcp_common.sh is a shared library and must be sourced from a product-specific launcher."
    exit 1
fi

if [[ -z "${MCP_LAUNCHER_PATH:-}" ]]; then
    if [[ ${#BASH_SOURCE[@]} -gt 0 ]]; then
        MCP_LAUNCHER_PATH="${BASH_SOURCE[${#BASH_SOURCE[@]}-1]}"
    else
        MCP_LAUNCHER_PATH="$0"
    fi
fi

mcp_common__ensure_bash4() {
    local script_path="$1"
    shift

    if [[ -n "${MCP_SKIP_BASH_REEXEC:-}" ]]; then
        return 0
    fi

    if [[ -z "${BASH_VERSINFO:-}" ]] || [ "${BASH_VERSINFO[0]:-0}" -lt 4 ]; then
        for candidate in /opt/homebrew/bin/bash /usr/local/bin/bash; do
            if command -v "$candidate" >/dev/null 2>&1; then
                MCP_BASH_REEXEC_DONE=1 exec "$candidate" "$script_path" "$@"
            fi
        done
    fi
}

if [[ -z "${MCP_BASH_REEXEC_DONE:-}" ]]; then
    mcp_common__ensure_bash4 "$MCP_LAUNCHER_PATH" "$@"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Allow callers to preconfigure behaviour while providing sensible defaults.
TEST_MODE=${TEST_MODE:-false}
MCP_PRODUCT_NAME=${MCP_PRODUCT_NAME:-"Claude"}
MCP_CLI_BIN=${MCP_CLI_BIN:-"claude"}
MCP_SCOPE=${MCP_SCOPE:-user}
MCP_STATS_LOCK_FILE=${MCP_STATS_LOCK_FILE:-"/tmp/${MCP_CLI_BIN}_mcp_stats.lock"}
MCP_LOG_FILE_PREFIX=${MCP_LOG_FILE_PREFIX:-"/tmp/${MCP_CLI_BIN}_mcp"}
MCP_BACKUP_PREFIX=${MCP_BACKUP_PREFIX:-${MCP_CLI_BIN}}
MCP_REQUIRE_CLI=${MCP_REQUIRE_CLI:-false}
# Portable uppercase conversion (macOS ships Bash 3.2 without ^^)
MCP_PRODUCT_NAME_UPPER=$(printf '%s' "$MCP_PRODUCT_NAME" | tr '[:lower:]' '[:upper:]')
if [[ "${MCP_CLI_BIN}" == "codex" ]]; then
    MCP_SCOPE_ARGS=()
else
    MCP_SCOPE_ARGS=(--scope "$MCP_SCOPE")
fi

for mcp_common_arg in "$@"; do
    if [[ "$mcp_common_arg" == "--test" ]]; then
        TEST_MODE=true
        break
    fi
done
unset mcp_common_arg

GITHUB_TOKEN_LOADED=${GITHUB_TOKEN_LOADED:-false}
RENDER_API_KEY=${RENDER_API_KEY:-}
PERPLEXITY_API_KEY=${PERPLEXITY_API_KEY:-}
GROK_API_KEY=${GROK_API_KEY:-}
PLAYWRIGHT_ENABLED=${PLAYWRIGHT_ENABLED:-true}
REACT_MCP_ENABLED=${REACT_MCP_ENABLED:-false}
IOS_SIMULATOR_ENABLED=${IOS_SIMULATOR_ENABLED:-false}
GITHUB_MCP_ENABLED=${GITHUB_MCP_ENABLED:-false}
XAI_API_KEY=${XAI_API_KEY:-}
TMPDIR=${TMPDIR:-/tmp}

# Treat automation placeholders as unset to avoid accidental authentication attempts.
if [[ "${GITHUB_TOKEN:-}" == "your_token_here" ]]; then
    unset GITHUB_TOKEN
fi

# Safe exit that won't kill the parent shell if sourced
__mcp_common_restore_shellopts() {
  if [[ -n "${__MCP_COMMON_PREV_SHELLOPTS:-}" ]]; then
    eval "$__MCP_COMMON_PREV_SHELLOPTS"
    unset __MCP_COMMON_PREV_SHELLOPTS
  fi
}

safe_exit() {
  local code="${1:-0}"
  # If the script is sourced, 'return' is available; else 'return' errors and we use fallback exit
  __mcp_common_restore_shellopts
  return "$code" 2>/dev/null || {
    # Fallback exit for non-sourced execution
    builtin exit "$code"
  }
}

# Check bash version for associative array support
if [ "${BASH_VERSINFO[0]}" -lt 4 ]; then
    echo "❌ Error: This script requires bash 4.0 or higher for associative array support"
    echo "   Current bash version: ${BASH_VERSION}"
    echo "   Install newer bash: brew install bash (macOS) or update your system"
    safe_exit 1
fi

# Detect operating system for enhanced cross-platform compatibility
OS_TYPE="$(uname -s)"
case "$OS_TYPE" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    CYGWIN*)    MACHINE=Cygwin;;
    MINGW*)     MACHINE=MinGw;;
    MSYS*)      MACHINE=Git;;
    *)          MACHINE="UNKNOWN:$OS_TYPE"
esac

echo "🔍 Detected platform: $MACHINE ($OS_TYPE)"

if [[ "$MCP_REQUIRE_CLI" == true ]] && ! command -v "$MCP_CLI_BIN" >/dev/null 2>&1; then
    echo "❌ Error: ${MCP_PRODUCT_NAME} CLI ('$MCP_CLI_BIN') not found in PATH."
    echo "   Install the ${MCP_PRODUCT_NAME} CLI or ensure it is available before running this script."
    safe_exit 1
fi

# Detect timeout command for cross-platform compatibility
TIMEOUT_CMD=""
if command -v timeout >/dev/null 2>&1; then
    TIMEOUT_CMD="timeout"
elif command -v gtimeout >/dev/null 2>&1; then
    TIMEOUT_CMD="gtimeout"
elif [ -x "/opt/homebrew/opt/coreutils/libexec/gnubin/timeout" ]; then
    TIMEOUT_CMD="/opt/homebrew/opt/coreutils/libexec/gnubin/timeout"
elif [ -x "/usr/local/opt/coreutils/libexec/gnubin/timeout" ]; then
    TIMEOUT_CMD="/usr/local/opt/coreutils/libexec/gnubin/timeout"
fi

if [ -n "$TIMEOUT_CMD" ]; then
    echo "✅ Timeout command available: $TIMEOUT_CMD"
else
    echo "⚠️ No timeout command found - operations will run without timeout protection"
fi

# Detect flock availability for file locking
USE_FLOCK=false
if command -v flock >/dev/null 2>&1; then
    USE_FLOCK=true
fi

echo "🚀 Installing MCP Servers with Enhanced Reliability..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Synchronization for parallel processing
STATS_LOCK_FILE="$MCP_STATS_LOCK_FILE"

# Function to safely update stats counters with file locking
update_stats() {
    local stat_type="$1"
    local name="$2"
    local result="$3"

    # Use flock for atomic updates when available
    if [ "$USE_FLOCK" = true ]; then
        {
            flock -x 200
            case "$stat_type" in
                "TOTAL")
                    TOTAL_SERVERS=$((TOTAL_SERVERS + 1))
                    ;;
                "SUCCESS")
                    SUCCESSFUL_INSTALLS=$((SUCCESSFUL_INSTALLS + 1))
                    INSTALL_RESULTS["$name"]="$result"
                    ;;
                "FAILURE")
                    FAILED_INSTALLS=$((FAILED_INSTALLS + 1))
                    INSTALL_RESULTS["$name"]="$result"
                    ;;
            esac
        } 200>"$STATS_LOCK_FILE"
    else
        # No flock available, proceed without locking
        case "$stat_type" in
            "TOTAL")
                TOTAL_SERVERS=$((TOTAL_SERVERS + 1))
                ;;
            "SUCCESS")
                SUCCESSFUL_INSTALLS=$((SUCCESSFUL_INSTALLS + 1))
                INSTALL_RESULTS["$name"]="$result"
                ;;
            "FAILURE")
                FAILED_INSTALLS=$((FAILED_INSTALLS + 1))
                INSTALL_RESULTS["$name"]="$result"
                ;;
        esac
    fi
}

# Set up logging
LOG_FILE="${MCP_LOG_FILE_PREFIX}_$(date +%Y%m%d_%H%M%S).log"
echo "📝 Logging to: $LOG_FILE"

# In test mode, exit early with success
if [ "$TEST_MODE" = true ]; then
    echo "🧪 Test mode: Exiting early with success"
    safe_exit 0
    return 0 2>/dev/null || exit 0
fi

# Default environment flags to reduce verbose MCP tool discovery and logging
if [ ${#DEFAULT_MCP_ENV_FLAGS[@]} -eq 0 ]; then
    DEFAULT_MCP_ENV_FLAGS=(
        --env "MCP_${MCP_PRODUCT_NAME_UPPER}_DEBUG=false"
        --env "MCP_VERBOSE_TOOLS=false"
        --env "MCP_AUTO_DISCOVER=false"
    )
fi

# Function to log with timestamp
log_with_timestamp() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to log errors with details
log_error_details() {
    local operation="$1"
    local package="$2"
    local error_output="$3"

    log_with_timestamp "ERROR: $operation failed for $package"
    log_with_timestamp "Error details: $error_output"
    echo "Error details: $error_output" >> "$LOG_FILE"
}

# Get Node and NPX paths with cross-platform detection
NODE_PATH=$(command -v node 2>/dev/null || true)
NPX_PATH=$(command -v npx 2>/dev/null || true)

# Mac homebrew specific detection if not found
if [ -z "$NODE_PATH" ] && [ "$MACHINE" = "Mac" ]; then
    echo -e "${BLUE}🔍 Checking Mac homebrew Node.js locations...${NC}"
    for potential_node in \
        "/opt/homebrew/bin/node" \
        "/usr/local/bin/node" \
        "$HOME/.nvm/current/bin/node"
    do
        if [ -x "$potential_node" ]; then
            NODE_PATH="$potential_node"
            # Find npx alongside node
            NODE_DIR=$(dirname "$NODE_PATH")
            if [ -x "$NODE_DIR/npx" ]; then
                NPX_PATH="$NODE_DIR/npx"
            fi
            break
        fi
    done
fi

# Windows/Git Bash specific path detection
if [ -z "$NODE_PATH" ] && { [ "$MACHINE" = "Git" ] || [ "$MACHINE" = "MinGw" ] || [ "$MACHINE" = "Cygwin" ]; }; then
    echo -e "${BLUE}🔍 Checking Windows-specific Node.js locations...${NC}"

    # Common Windows Node.js installation paths
    for potential_node in \
        "/c/Program Files/nodejs/node.exe" \
        "/c/Program Files (x86)/nodejs/node.exe" \
        "$USERPROFILE/AppData/Roaming/npm/node.exe" \
        "$APPDATA/npm/node.exe"
    do
        if [ -x "$potential_node" ]; then
            NODE_PATH="$potential_node"
            break
        fi
    done

    # Find npx alongside node
    if [ -n "$NODE_PATH" ]; then
        NODE_DIR=$(dirname "$NODE_PATH")
        if [ -x "$NODE_DIR/npx.exe" ]; then
            NPX_PATH="$NODE_DIR/npx.exe"
        elif [ -x "$NODE_DIR/npx" ]; then
            NPX_PATH="$NODE_DIR/npx"
        fi
    fi
fi

if [ -z "$NODE_PATH" ] || [ -z "$NPX_PATH" ]; then
    echo -e "${RED}❌ Node.js or NPX not found. Please install Node.js first.${NC}"
    echo -e "${YELLOW}💡 Platform: $MACHINE - Install from https://nodejs.org/${NC}"
    if [ "$MACHINE" = "Git" ] || [ "$MACHINE" = "MinGw" ]; then
        echo -e "${YELLOW}💡 For Git Bash on Windows, restart terminal after Node.js installation${NC}"
    fi
    safe_exit 1
fi

echo -e "${BLUE}📍 Node path: $NODE_PATH${NC}"
echo -e "${BLUE}📍 NPX path: $NPX_PATH${NC}"

# Check Node.js version and warn about compatibility
NODE_VERSION=$(node --version)
echo -e "${BLUE}📍 Node version: $NODE_VERSION${NC}"
log_with_timestamp "Node.js version: $NODE_VERSION"

# Check for major version compatibility
NODE_MAJOR=$(echo "$NODE_VERSION" | sed 's/v\([0-9]*\).*/\1/')
if [ "$NODE_MAJOR" -lt 20 ]; then
    echo -e "${YELLOW}⚠️ WARNING: Node.js $NODE_VERSION detected. MCP servers recommend Node 20+${NC}"
    echo -e "${YELLOW}   Some packages may show engine warnings but should still work${NC}"
    log_with_timestamp "WARNING: Node.js version $NODE_VERSION is below recommended v20+"
else
    echo -e "${GREEN}✅ Node.js version compatible with MCP servers${NC}"
fi

# Check npm permissions and suggest alternatives
echo -e "${BLUE}🔍 Checking npm global installation permissions...${NC}"
if npm list -g --depth=0 >/dev/null 2>&1; then
    echo -e "${GREEN}✅ NPM global permissions look good${NC}"
    USE_GLOBAL=true
else
    echo -e "${YELLOW}⚠️ Global npm permissions may be restricted${NC}"
    echo -e "${YELLOW}   Will use npx direct installation method${NC}"
    USE_GLOBAL=false
fi


# Run a command while capturing its combined stdout/stderr and exit code
capture_command_output() {
    local __output_var="$1"
    local __status_var="$2"
    shift 2
    local __output
    set +e
    __output="$("$@" 2>&1)"
    local __exit_code=$?
    set -euo pipefail
    printf -v "$__output_var" '%s' "$__output"
    printf -v "$__status_var" '%s' "$__exit_code"
}


# Track installation results
declare -A INSTALL_RESULTS
TOTAL_SERVERS=0
SUCCESSFUL_INSTALLS=0
FAILED_INSTALLS=0
CURRENT_STEP=0

# Ensure GitHub token availability per scripting guidelines
export GITHUB_TOKEN="${GITHUB_TOKEN:-$GITHUB_PERSONAL_ACCESS_TOKEN}"

# Parallel processing configuration
MAX_PARALLEL_JOBS=3
declare -A PARALLEL_PIDS
declare -A PARALLEL_RESULTS
declare -A PARALLEL_STATUS_FILES
declare -A PARALLEL_RESULT_FILES
declare -A PARALLEL_LOG_FILES

# Server installation queue for parallel processing
declare -a SERVER_QUEUE

# Function to check if package is a pip package
is_pip_package() {
    # No pip packages are currently installed directly by this script.
    # Placeholder for future expansions that may require pip-based servers.
    return 1
}

# Function to check if package exists in remote registry
package_exists() {
    local package="$1"
    if is_pip_package "$package"; then
        # Check PyPI registry (not local installation)
        python3 -c "import requests; import sys; response = requests.get(f'https://pypi.org/pypi/{sys.argv[1]}/json'); sys.exit(0 if response.status_code == 200 else 1)" "$package" 2>/dev/null
    else
        npm view "$package" version >/dev/null 2>&1
    fi
}

# Function to install npm package with permission-aware method
install_package() {
    local package="$1"
    log_with_timestamp "Attempting to install package: $package"

    # Special handling for pip packages
    if is_pip_package "$package"; then
        echo -e "${BLUE}  📦 Installing $package globally via pip...${NC}"
        local install_output
        local exit_code
        capture_command_output install_output exit_code pip install "$package"

        if [ $exit_code -eq 0 ]; then
            echo -e "${GREEN}  ✅ Package $package installed globally via pip${NC}"
            log_with_timestamp "SUCCESS: Package $package installed globally via pip"
            return 0
        else
            echo -e "${RED}  ❌ Failed to install $package via pip${NC}"
            log_error_details "pip install" "$package" "$install_output"
            return 1
        fi
    fi

    if [ "$USE_GLOBAL" = true ]; then
        echo -e "${BLUE}  📦 Installing $package globally...${NC}"
        # Capture detailed error output
        local install_output
        local exit_code
        capture_command_output install_output exit_code npm install -g "$package"

        if [ $exit_code -eq 0 ]; then
            echo -e "${GREEN}  ✅ Package $package installed globally${NC}"
            log_with_timestamp "SUCCESS: Package $package installed globally"
            return 0
        else
            echo -e "${YELLOW}  ⚠️ Global installation failed, trying alternative methods...${NC}"
            log_error_details "npm install -g" "$package" "$install_output"

            # Check if it's a permission error
            if echo "$install_output" | grep -q "EACCES\|permission denied"; then
                echo -e "${YELLOW}  🔧 Permission issue detected - switching to npx-only mode${NC}"
                log_with_timestamp "Permission error detected, using npx-only approach"
                USE_GLOBAL=false
                return 0  # Continue with npx approach
            else
                echo -e "${RED}  📋 Install error: $install_output${NC}"
                return 1
            fi
        fi
    else
        echo -e "${BLUE}  📦 Using npx direct execution (no global install needed)${NC}"
        log_with_timestamp "Using npx direct execution for $package"
        return 0
    fi
}

# Function to test if MCP server works
test_mcp_server() {
    local name="$1"
    echo -e "${BLUE}  🧪 Testing server $name...${NC}"

    # Try to get server info (this will fail if server can't start)
    if [ -n "$TIMEOUT_CMD" ]; then
        if $TIMEOUT_CMD 5s ${MCP_CLI_BIN} mcp list | grep -q "^$name:"; then
            echo -e "${GREEN}  ✅ Server $name is responding${NC}"
            return 0
        else
            echo -e "${YELLOW}  ⚠️ Server $name added but may need configuration${NC}"
            return 1
        fi
    else
        # No timeout available, run without it
        if ${MCP_CLI_BIN} mcp list | grep -q "^$name:"; then
            echo -e "${GREEN}  ✅ Server $name is responding${NC}"
            return 0
        else
            echo -e "${YELLOW}  ⚠️ Server $name added but may need configuration${NC}"
            return 1
        fi
    fi
}

# Function to cleanup failed server installation
cleanup_failed_server() {
    local name="$1"
    echo -e "${YELLOW}  🧹 Cleaning up failed installation of $name...${NC}"
    ${MCP_CLI_BIN} mcp remove "$name" >/dev/null 2>&1 || true
}

# Function to display current step with dynamic counting
display_step() {
    local title="$1"
    CURRENT_STEP=$((CURRENT_STEP + 1))
    echo -e "\n${BLUE}[$CURRENT_STEP] $title${NC}"
}

# Function to check MCP server in parallel
check_server_parallel() {
    local name="$1"
    local check_file
    check_file=$(mktemp)

    {
        if ${MCP_CLI_BIN} mcp list 2>/dev/null | grep -q "^$name:.*✓ Connected"; then
            echo "CONNECTED" > "$check_file"
        else
            echo "DISCONNECTED" > "$check_file"
        fi
    } &

    local bg_pid=$!
    # Temporarily disable unbound variable check for associative array assignment
    set +u
    PARALLEL_PIDS["$name"]=$bg_pid
    PARALLEL_STATUS_FILES["$name"]="$check_file"
    set -u
}

# Function to wait for parallel checks and collect results
collect_parallel_results() {
    local timeout_seconds=10

    for name in "${!PARALLEL_PIDS[@]}"; do
        local pid=${PARALLEL_PIDS["$name"]}
        local check_file="${PARALLEL_STATUS_FILES["$name"]}"

        # Each process gets individual timeout calculation
        local process_start_time=$(date +%s)
        local elapsed=0
        while kill -0 "$pid" 2>/dev/null && [ $elapsed -lt $timeout_seconds ]; do
            sleep 0.1
            elapsed=$(( $(date +%s) - process_start_time ))
        done

        # Kill if still running
        kill "$pid" 2>/dev/null || true
        wait "$pid" 2>/dev/null || true

        # Read result
        set +u
        if [ -n "$check_file" ] && [ -f "$check_file" ]; then
            PARALLEL_RESULTS["$name"]=$(cat "$check_file")
            rm -f "$check_file"
        else
            PARALLEL_RESULTS["$name"]="TIMEOUT"
        fi
        set -u
    done

    # Clear PID tracking (reinitialize associative array correctly)
    unset PARALLEL_PIDS
    declare -A PARALLEL_PIDS
    unset PARALLEL_STATUS_FILES
    declare -A PARALLEL_STATUS_FILES
}

# Enhanced function to add MCP server with full error checking
add_mcp_server() {
    local name="$1"
    local package="$2"
    shift 2
    local extra_args=("$@")
    local cli_args=()
    local cmd_args=()
    for arg in "${extra_args[@]}"; do
        if [[ "$arg" == --* ]]; then
            cli_args+=("$arg")
        else
            cmd_args+=("$arg")
        fi
    done

    update_stats "TOTAL" "$name" ""
    echo -e "${BLUE}  🔧 Setting up $name...${NC}"
    log_with_timestamp "Setting up MCP server: $name (package: $package)"

    # Check if server already exists
    if server_already_exists "$name"; then
        echo -e "${GREEN}  ✅ Server $name already exists, skipping installation${NC}"
        log_with_timestamp "Server $name already exists, skipping"
        update_stats "SUCCESS" "$name" "ALREADY_EXISTS"
        return 0
    fi

    # Check if package exists in registry
    if is_pip_package "$package"; then
        echo -e "${BLUE}  🔍 Checking if package $package exists in PyPI registry...${NC}"
        local registry_check
        local registry_exit_code
        local py_script="import requests; import sys; response = requests.get(f'https://pypi.org/pypi/{sys.argv[1]}/json'); print('Package found' if response.status_code == 200 else 'Package not found'); sys.exit(0 if response.status_code == 200 else 1)"
        capture_command_output registry_check registry_exit_code python3 -c "$py_script" "$package"

        if [ $registry_exit_code -ne 0 ]; then
            echo -e "${RED}  ❌ Package $package not found in PyPI registry${NC}"
            log_error_details "PyPI check" "$package" "$registry_check"
            INSTALL_RESULTS["$name"]="PACKAGE_NOT_FOUND"
            FAILED_INSTALLS=$((FAILED_INSTALLS + 1))
            return 1
        else
            echo -e "${GREEN}  ✅ Package $package exists in PyPI${NC}"
            log_with_timestamp "Package $package exists in PyPI registry"
        fi
    else
        echo -e "${BLUE}  🔍 Checking if package $package exists in npm registry...${NC}"
        local registry_check
        local registry_exit_code
        capture_command_output registry_check registry_exit_code npm view "$package" version

        if [ $registry_exit_code -ne 0 ]; then
            echo -e "${RED}  ❌ Package $package not found in npm registry${NC}"
            log_error_details "npm view" "$package" "$registry_check"
            INSTALL_RESULTS["$name"]="PACKAGE_NOT_FOUND"
            FAILED_INSTALLS=$((FAILED_INSTALLS + 1))
            return 1
        else
            echo -e "${GREEN}  ✅ Package $package exists (version: $(echo "$registry_check" | head -1))${NC}"
            log_with_timestamp "Package $package exists in registry"
        fi
    fi

    # Check if package is installed globally (only if using global mode)
    if [ "$USE_GLOBAL" = true ]; then
        if is_pip_package "$package"; then
            echo -e "${BLUE}  🔍 Checking global pip installation...${NC}"
            local global_check
            local global_exit_code
            capture_command_output global_check global_exit_code pip show "$package"

            if [ $global_exit_code -ne 0 ]; then
                echo -e "${YELLOW}  📦 Package $package not installed globally, installing...${NC}"
                log_with_timestamp "Package $package not installed globally, attempting installation"
                if ! install_package "$package"; then
                    INSTALL_RESULTS["$name"]="INSTALL_FAILED"
                    FAILED_INSTALLS=$((FAILED_INSTALLS + 1))
                    return 1
                fi
            else
                echo -e "${GREEN}  ✅ Package $package already installed globally via pip${NC}"
                log_with_timestamp "Package $package already installed globally via pip"
                echo "Global package check: $global_check" >> "$LOG_FILE"
            fi
        else
            echo -e "${BLUE}  🔍 Checking global npm installation...${NC}"
            local global_check
            local global_exit_code
            capture_command_output global_check global_exit_code npm list -g "$package"

            if [ $global_exit_code -ne 0 ]; then
                echo -e "${YELLOW}  📦 Package $package not installed globally, installing...${NC}"
                log_with_timestamp "Package $package not installed globally, attempting installation"
                if ! install_package "$package"; then
                    # If global install failed due to permissions, continue with npx
                    if [ "$USE_GLOBAL" = false ]; then
                        echo -e "${BLUE}  🔄 Continuing with npx direct execution${NC}"
                    else
                        INSTALL_RESULTS["$name"]="INSTALL_FAILED"
                        FAILED_INSTALLS=$((FAILED_INSTALLS + 1))
                        return 1
                    fi
                fi
            else
                echo -e "${GREEN}  ✅ Package $package already installed globally${NC}"
                log_with_timestamp "Package $package already installed globally"
                echo "Global package check: $global_check" >> "$LOG_FILE"
            fi
        fi
    else
        echo -e "${BLUE}  🔄 Using npx direct execution - no global installation required${NC}"
        log_with_timestamp "Using npx direct execution for $package"
    fi

    # Remove existing server if present
    ${MCP_CLI_BIN} mcp remove "$name" >/dev/null 2>&1 || true

    # Add server with error checking
    echo -e "${BLUE}  🔗 Adding MCP server $name...${NC}"
    log_with_timestamp "Attempting to add MCP server: $name"

    # Capture detailed error output from ${MCP_CLI_BIN} mcp add
    local add_output
    local add_cmd

    # Special handling for grok-mcp which requires direct node execution
    if [ "$name" = "grok-mcp" ]; then
        echo -e "${BLUE}  🔧 Special setup for grok-mcp using direct node execution...${NC}"
        local grok_path=""
        if command -v npm >/dev/null 2>&1; then
            local npm_root_output=""
            local npm_root_status=0
            capture_command_output npm_root_output npm_root_status npm root -g
            if [ "$npm_root_status" -eq 0 ] && [ -n "$npm_root_output" ]; then
                grok_path="${npm_root_output}/grok-mcp/build/index.js"
            fi
            if [ -z "$grok_path" ] || [ ! -f "$grok_path" ]; then
                echo -e "${YELLOW}  ⚠️ Grok MCP not found at $grok_path${NC}"
                echo -e "${BLUE}  📦 Installing grok-mcp globally from npm...${NC}"
                log_with_timestamp "grok-mcp not found, installing globally"

                local install_output
                local install_exit_code
                capture_command_output install_output install_exit_code npm install -g grok-mcp --registry https://registry.npmjs.org/

                if [ $install_exit_code -eq 0 ]; then
                    echo -e "${GREEN}  ✅ Successfully installed grok-mcp globally${NC}"
                    log_with_timestamp "grok-mcp installed successfully"

                    # Re-calculate path after installation to get actual location
                    capture_command_output npm_root_output npm_root_status npm root -g
                    if [ "$npm_root_status" -eq 0 ] && [ -n "$npm_root_output" ]; then
                        grok_path="${npm_root_output}/grok-mcp/build/index.js"
                    else
                        grok_path=""
                    fi

                    # Verify installation at actual location
                    if [ -n "$grok_path" ] && [ -f "$grok_path" ]; then
                        echo -e "${GREEN}  ✅ Verified grok-mcp at $grok_path${NC}"
                    else
                        echo -e "${RED}  ❌ grok-mcp installation succeeded but file not found at expected path: $grok_path${NC}"
                        log_error_details "grok-mcp verification" "grok-mcp" "File not found after installation at expected path: $grok_path"
                        INSTALL_RESULTS["$name"]="VERIFY_FAILED"
                        FAILED_INSTALLS=$((FAILED_INSTALLS + 1))
                        return 1
                    fi
                else
                    echo -e "${RED}  ❌ Failed to install grok-mcp globally${NC}"
                    log_error_details "npm install grok-mcp" "grok-mcp" "$install_output"
                    echo -e "${RED}  📋 Install error: $install_output${NC}"
                    INSTALL_RESULTS["$name"]="INSTALL_FAILED"
                    FAILED_INSTALLS=$((FAILED_INSTALLS + 1))
                    return 1
                fi
            else
                echo -e "${GREEN}  ✅ Found grok-mcp at $grok_path${NC}"
                log_with_timestamp "grok-mcp found at global installation"
            fi
        else
            grok_path="/usr/local/lib/node_modules/grok-mcp/build/index.js"
            echo -e "${YELLOW}  ⚠️ npm command not found, using fallback path: $grok_path${NC}"
        fi

        # Add XAI_API_KEY environment variable for grok-mcp
        local grok_env_flags=("${DEFAULT_MCP_ENV_FLAGS[@]}")
        if [ -n "${XAI_API_KEY:-}" ] || [ -n "${GROK_API_KEY:-}" ]; then
            local api_key="${XAI_API_KEY:-$GROK_API_KEY}"
            grok_env_flags+=(--env "XAI_API_KEY=$api_key")
        fi
        add_cmd=(${MCP_CLI_BIN} mcp add "${MCP_SCOPE_ARGS[@]}" "${grok_env_flags[@]}" "${cli_args[@]}" "$name" "$NODE_PATH" "$grok_path" "${cmd_args[@]}")
    else
        add_cmd=(${MCP_CLI_BIN} mcp add "${MCP_SCOPE_ARGS[@]}" "${DEFAULT_MCP_ENV_FLAGS[@]}" "${cli_args[@]}" "$name" "$NPX_PATH" "$package" "${cmd_args[@]}")
    fi

    local add_exit_code
    capture_command_output add_output add_exit_code "${add_cmd[@]}"

    if [ $add_exit_code -eq 0 ]; then
        echo -e "${GREEN}  ✅ Successfully added $name${NC}"
        log_with_timestamp "Successfully added MCP server: $name"

        # Test if server actually works
        sleep 1  # Give server time to initialize
        if test_mcp_server "$name"; then
            INSTALL_RESULTS["$name"]="SUCCESS"
            SUCCESSFUL_INSTALLS=$((SUCCESSFUL_INSTALLS + 1))
        else
            INSTALL_RESULTS["$name"]="NEEDS_CONFIG"
            SUCCESSFUL_INSTALLS=$((SUCCESSFUL_INSTALLS + 1))  # Still count as success
        fi
    else
        echo -e "${RED}  ❌ Failed to add $name to ${MCP_PRODUCT_NAME} MCP${NC}"
        log_error_details "${MCP_CLI_BIN} mcp add" "$name" "$add_output"
        echo -e "${RED}  📋 Add error: $add_output${NC}"
        cleanup_failed_server "$name"
        INSTALL_RESULTS["$name"]="ADD_FAILED"
        FAILED_INSTALLS=$((FAILED_INSTALLS + 1))
        return 1
    fi
}

# GitHub Token Configuration (for private repository access)
# Uses centralized token loading system for better maintainability
#
# Generate tokens at:
# - GitHub: https://github.com/settings/tokens (scopes: repo, read:org, read:user)
# - Perplexity: https://www.perplexity.ai/settings/api
#
# NOTE: This script uses GitHub's NEW official MCP server (github/github-mcp-server)
# which is HTTP-based and hosted remotely, replacing the old deprecated npm package

# Load centralized token helper
TOKEN_HELPER="$SCRIPT_DIR/load_tokens.sh"

if [ -f "$TOKEN_HELPER" ]; then
    echo -e "${BLUE}📋 Loading tokens using centralized helper...${NC}"
    log_with_timestamp "Using centralized token helper: $TOKEN_HELPER"

    # Source the token helper to load functions and tokens
    source "$TOKEN_HELPER"

    # Load tokens
    if load_tokens; then
        log_with_timestamp "Tokens loaded successfully via centralized helper"

        # Ensure tokens are properly exported for use in this script
        # The load_tokens function may not export variables to parent shell properly
        if [ -f "$HOME/.token" ]; then
            source "$HOME/.token" 2>/dev/null || true
            export GITHUB_PERSONAL_ACCESS_TOKEN="$GITHUB_TOKEN"
        fi
    else
        echo -e "${RED}❌ Failed to load tokens via centralized helper${NC}"
        echo -e "${YELLOW}💡 Run '$TOKEN_HELPER create' to create template token file${NC}"
        echo -e "${YELLOW}💡 Run '$TOKEN_HELPER help' for more options${NC}"
        log_with_timestamp "ERROR: Token loading failed, aborting for security"
        safe_exit 1
    fi
else
    echo -e "${YELLOW}⚠️ Centralized token helper not found, falling back to legacy method${NC}"
    log_with_timestamp "WARNING: Token helper not found at $TOKEN_HELPER, using fallback"

    # Fallback to legacy token loading
    HOME_TOKEN_FILE="$HOME/.token"
    if [ -f "$HOME_TOKEN_FILE" ]; then
        echo -e "${GREEN}✅ Loading tokens from $HOME_TOKEN_FILE${NC}"
        source "$HOME_TOKEN_FILE"
        export GITHUB_PERSONAL_ACCESS_TOKEN="$GITHUB_TOKEN"
    else
        echo -e "${RED}❌ No token file found${NC}"
        echo -e "${YELLOW}💡 Create ~/.token file with your tokens${NC}"
        safe_exit 1
    fi
fi

# Ensure GITHUB_PERSONAL_ACCESS_TOKEN is exported for compatibility
export GITHUB_PERSONAL_ACCESS_TOKEN

# Function to check environment requirements
check_github_requirements() {
    if [ "$GITHUB_TOKEN_LOADED" = true ]; then
        echo -e "${GREEN}✅ GitHub token loaded - GitHub remote server will have full access${NC}"

        # Test token validity using the centralized helper
        echo -e "${BLUE}  🔍 Testing GitHub token validity...${NC}"
        if test_github_token; then
            echo -e "${BLUE}  📡 Using GitHub's NEW official remote MCP server${NC}"
            echo -e "${BLUE}  🔗 Server URL: https://api.githubcopilot.com/mcp/${NC}"
        fi
    elif [ -n "$GITHUB_PERSONAL_ACCESS_TOKEN" ]; then
        echo -e "${YELLOW}⚠️ GitHub token found but not validated by centralized helper${NC}"
        echo -e "${YELLOW}   Server will work for public repositories${NC}"
        echo -e "${YELLOW}   For private repos, ensure token has required scopes${NC}"
    else
        echo -e "${YELLOW}⚠️ No GitHub token found${NC}"
        echo -e "${YELLOW}   Server will work for public repositories only${NC}"
        echo -e "${YELLOW}   For private repos, add GITHUB_TOKEN to ~/.token file${NC}"
    fi
}

# Enhanced MCP server checking with parallel health checks
echo -e "${BLUE}🔍 Checking existing MCP installations and health status...${NC}"
log_with_timestamp "Checking existing MCP servers with parallel health checks"

EXISTING_SERVERS=""
if EXISTING_SERVERS=$(${MCP_CLI_BIN} mcp list 2>&1); then
    EXISTING_COUNT=$(printf '%s\n' "$EXISTING_SERVERS" | awk -F':' '/^[A-Za-z].*:/{count++} END {print count+0}')
    echo -e "${GREEN}✅ Found $EXISTING_COUNT existing MCP servers${NC}"
    log_with_timestamp "Found $EXISTING_COUNT existing MCP servers"

    if [ "$EXISTING_COUNT" -gt 0 ]; then
        echo -e "${BLUE}📋 Running parallel health checks on existing servers...${NC}"

        # Extract server names and start parallel health checks
        mapfile -t SERVER_NAMES < <(printf '%s\n' "$EXISTING_SERVERS" | awk -F':' '/^[A-Za-z].*:/{print $1}')

        # Start parallel health checks (limited to MAX_PARALLEL_JOBS)
        check_count=0
        for server_name in "${SERVER_NAMES[@]}"; do
            if [ $check_count -ge $MAX_PARALLEL_JOBS ]; then
                # Wait for some checks to complete before starting more
                collect_parallel_results
                check_count=0
            fi
            check_server_parallel "$server_name"
            check_count=$((check_count + 1))
        done

        # Wait for remaining checks to complete
        collect_parallel_results

        # Display results
        echo -e "${BLUE}📋 Server health status:${NC}"
        for server_name in "${SERVER_NAMES[@]}"; do
            status="${PARALLEL_RESULTS["$server_name"]:-"UNKNOWN"}"
            case "$status" in
                "CONNECTED")
                    echo -e "  ${GREEN}✓${NC} $server_name"
                    ;;
                "DISCONNECTED")
                    echo -e "  ${RED}✗${NC} $server_name"
                    ;;
                "TIMEOUT")
                    echo -e "  ${YELLOW}⏱${NC} $server_name (timeout)"
                    ;;
                *)
                    echo -e "  ${YELLOW}?${NC} $server_name (unknown)"
                    ;;
            esac
        done

        echo "$EXISTING_SERVERS" >> "$LOG_FILE"
    fi
else
    echo -e "${YELLOW}⚠️ Could not get MCP server list: $EXISTING_SERVERS${NC}"
    log_error_details "${MCP_CLI_BIN} mcp list" "N/A" "$EXISTING_SERVERS"
fi
echo ""

# Function to check if MCP server already exists
server_already_exists() {
    local name="$1"
    echo "$EXISTING_SERVERS" | grep -q "^$name:"
}

# Function to setup Render MCP Server
setup_render_mcp_server() {
    local add_output=""
    local add_exit_code=0
    display_step "Setting up Render MCP Server..."
    TOTAL_SERVERS=$((TOTAL_SERVERS + 1))
    echo -e "${BLUE}  ☁️ Configuring Render MCP server for cloud infrastructure management...${NC}"
    log_with_timestamp "Setting up MCP server: render (HTTP: https://mcp.render.com/mcp)"

    # Check if server already exists
    if server_already_exists "render"; then
        echo -e "${GREEN}  ✅ Server render already exists, skipping installation${NC}"
        log_with_timestamp "Server render already exists, skipping"
        INSTALL_RESULTS["render"]="ALREADY_EXISTS"
        SUCCESSFUL_INSTALLS=$((SUCCESSFUL_INSTALLS + 1))
    else
        # Check if RENDER_API_KEY is available
        if [ -n "$RENDER_API_KEY" ]; then
            echo -e "${GREEN}  ✅ Render API key found - setting up cloud infrastructure server${NC}"
            echo -e "${BLUE}  📋 Features: Service management, database queries, deployment monitoring${NC}"

            # Remove existing render server to reconfigure
            ${MCP_CLI_BIN} mcp remove "render" >/dev/null 2>&1 || true

            # Add Render MCP server using HTTP transport with secure JSON configuration
            echo -e "${BLUE}  🔗 Adding Render MCP server with HTTP transport...${NC}"
            log_with_timestamp "Attempting to add Render MCP server with API key"

            # 🚨 SECURITY FIX: Use secure temp file to avoid API key in process list
            # 🔧 ESCAPING FIX: Properly escape API key for JSON to handle special characters
            escaped_api_key="${RENDER_API_KEY//\\/\\\\}"  # Escape backslashes
            escaped_api_key="${escaped_api_key//\"/\\\"}"    # Escape quotes

            # Create secure temp file (600 permissions)
            json_temp=$(mktemp)
            chmod 600 "$json_temp"
            echo "{\"type\":\"http\",\"url\":\"https://mcp.render.com/mcp\",\"headers\":{\"Authorization\":\"Bearer $escaped_api_key\"}}" > "$json_temp"
            local json_payload
            json_payload=$(<"$json_temp")
            capture_command_output add_output add_exit_code "${MCP_CLI_BIN}" mcp add-json "${MCP_SCOPE_ARGS[@]}" "render" "$json_payload"
            rm -f "$json_temp"

            # 🚨 SECURITY FIX: Redact API key from logs to prevent secret leakage
            add_output_redacted=${add_output//${RENDER_API_KEY}/<RENDER_API_KEY>}

            if [ $add_exit_code -eq 0 ]; then
                echo -e "${GREEN}  ✅ Successfully configured Render MCP server${NC}"
                echo -e "${BLUE}  📋 Server info:${NC}"
                echo -e "     • API URL: https://mcp.render.com/mcp"
                echo -e "     • Features: Service creation, database management, metrics analysis"
                echo -e "     • Documentation: https://render.com/docs/mcp-server"
                log_with_timestamp "Successfully added Render MCP server with HTTP transport"
                INSTALL_RESULTS["render"]="SUCCESS"
                SUCCESSFUL_INSTALLS=$((SUCCESSFUL_INSTALLS + 1))
            else
                echo -e "${RED}  ❌ Failed to add Render MCP server${NC}"
                log_error_details "${MCP_CLI_BIN} mcp add render" "render" "$add_output_redacted"
                echo -e "${RED}  📋 Add error: $add_output_redacted${NC}"
                INSTALL_RESULTS["render"]="ADD_FAILED"
                FAILED_INSTALLS=$((FAILED_INSTALLS + 1))
            fi
        else
            echo -e "${YELLOW}  ⚠️ Render API key not found - skipping cloud infrastructure server${NC}"
            echo -e "${YELLOW}  💡 Render server provides cloud infrastructure management with natural language${NC}"
            echo -e "${YELLOW}  💡 Add RENDER_API_KEY to ~/.token file or environment to enable${NC}"
            log_with_timestamp "Render API key not found, skipping server installation"
            INSTALL_RESULTS["render"]="API_KEY_MISSING"
            # Don't count as failure since this is expected without API key
            # Total servers already counted at start - no adjustment needed
        fi
    fi
}

# Check environment requirements
echo -e "${BLUE}🔍 Checking environment requirements...${NC}"
check_github_requirements
echo ""

# Define server installation batches for parallel processing
# Group servers that can be installed concurrently without conflicts

# Environment flags for optional MCP servers (disabled by default for context optimization)
PLAYWRIGHT_ENABLED=${PLAYWRIGHT_ENABLED:-true}
REACT_MCP_ENABLED=${REACT_MCP_ENABLED:-false}
IOS_SIMULATOR_ENABLED=${IOS_SIMULATOR_ENABLED:-false}
GITHUB_MCP_ENABLED=${GITHUB_MCP_ENABLED:-false}

declare -A BATCH_1=(
    ["sequential-thinking"]="@modelcontextprotocol/server-sequential-thinking"
    ["context7"]="@upstash/context7-mcp"
)

declare -A BATCH_2=(
    ["gemini-cli-mcp"]="@yusukedev/gemini-cli-mcp"
    ["ddg-search"]="@oevortex/ddg_search"
    ["grok-mcp"]="grok-mcp"
)

# Function to install server batch in parallel
install_batch_parallel() {
    local -n batch_ref=$1
    local batch_name="$2"

    echo -e "${BLUE}🚀 Installing $batch_name in parallel...${NC}"
    log_with_timestamp "Starting parallel installation of $batch_name"

    # Start installations in parallel
    for server_name in "${!batch_ref[@]}"; do
        local package="${batch_ref[$server_name]}"
        local result_file
        local log_file
        result_file=$(mktemp)
        log_file=$(mktemp)

        {
            if add_mcp_server "$server_name" "$package" > "$log_file" 2>&1; then
                local status="SUCCESS"
                local reason="${INSTALL_RESULTS["$server_name"]:-SUCCESS}"
                printf '%s|%s\n' "$status" "$reason" > "$result_file"
            else
                local status="FAILED"
                local reason="${INSTALL_RESULTS["$server_name"]:-FAILED}"
                printf '%s|%s\n' "$status" "$reason" > "$result_file"
            fi
        } &

        local bg_pid=$!
        # Temporarily disable unbound variable check for associative array assignment
        set +u
        PARALLEL_PIDS["$server_name"]=$bg_pid
        PARALLEL_RESULT_FILES["$server_name"]="$result_file"
        PARALLEL_LOG_FILES["$server_name"]="$log_file"
        log_with_timestamp "Started parallel installation of $server_name (PID: ${PARALLEL_PIDS[$server_name]})"
        set -u
    done

    # Wait for all installations to complete
    echo -e "${BLUE}  ⏳ Waiting for $batch_name installations to complete...${NC}"

    for server_name in "${!batch_ref[@]}"; do
        set +u
        local pid="${PARALLEL_PIDS[$server_name]}"
        local result_file="${PARALLEL_RESULT_FILES[$server_name]}"
        local log_file="${PARALLEL_LOG_FILES[$server_name]}"
        set -u

        # Wait for this installation
        if wait "$pid"; then
            local result_line="UNKNOWN|UNKNOWN"
            if [ -n "$result_file" ] && [ -f "$result_file" ]; then
                result_line="$(cat "$result_file")"
            fi
            IFS='|' read -r result reason <<<"$result_line"
            update_stats "TOTAL" "$server_name" ""
            INSTALL_RESULTS["$server_name"]="$reason"
            if [ "$result" = "SUCCESS" ]; then
                update_stats "SUCCESS" "$server_name" "$reason"
                echo -e "${GREEN}  ✓ $server_name completed successfully${NC}"
                log_with_timestamp "Parallel installation SUCCESS: $server_name"
            else
                update_stats "FAILURE" "$server_name" "$reason"
                echo -e "${RED}  ✗ $server_name failed${NC}"
                log_with_timestamp "Parallel installation FAILED: $server_name"
                # Show error details
                if [ -f "$log_file" ]; then
                    echo -e "${RED}    Error details: $(tail -1 "$log_file")${NC}"
                fi
            fi
        else
            update_stats "TOTAL" "$server_name" ""
            update_stats "FAILURE" "$server_name" "PROCESS_FAILED"
            echo -e "${RED}  ✗ $server_name process failed${NC}"
            log_with_timestamp "Parallel installation PROCESS_FAILED: $server_name"
        fi

        # Cleanup temp files
        if [ -n "$result_file" ]; then
            rm -f "$result_file"
        fi
        if [ -n "$log_file" ]; then
            rm -f "$log_file"
        fi
        set +u
        unset PARALLEL_RESULT_FILES["$server_name"]
        unset PARALLEL_LOG_FILES["$server_name"]
        set -u
    done

    # Clear parallel tracking (reinitialize associative array correctly)
    unset PARALLEL_PIDS
    declare -A PARALLEL_PIDS
    unset PARALLEL_RESULT_FILES
    declare -A PARALLEL_RESULT_FILES
    unset PARALLEL_LOG_FILES
    declare -A PARALLEL_LOG_FILES

    echo -e "${GREEN}✅ $batch_name installation batch completed${NC}"
}

# Function to install Playwright MCP server with environment guard
install_playwright_mcp() {
    if [[ "$PLAYWRIGHT_ENABLED" != "true" ]]; then
        echo -e "${YELLOW}  ⚠️ Playwright MCP server disabled (set PLAYWRIGHT_ENABLED=true to enable)${NC}"
        return 0
    fi

    echo -e "${BLUE}  🎭 Installing Playwright MCP server...${NC}"
    add_mcp_server "playwright-mcp" "@playwright/mcp"
}

# Function to install React MCP server with environment guard
install_react_mcp() {
    local add_output=""
    local add_exit_code=0
    if [[ "$REACT_MCP_ENABLED" != "true" ]]; then
        echo -e "${YELLOW}  ⚠️ React MCP server disabled (set REACT_MCP_ENABLED=true to enable)${NC}"
        return 0
    fi

    TOTAL_SERVERS=$((TOTAL_SERVERS + 1))
    echo -e "${BLUE}  ⚛️ Configuring React MCP server for React development...${NC}"
    log_with_timestamp "Setting up MCP server: react-mcp (local: react-mcp/index.js)"

    # Check if server already exists
    if server_already_exists "react-mcp"; then
        echo -e "${GREEN}  ✅ Server react-mcp already exists, skipping installation${NC}"
        log_with_timestamp "Server react-mcp already exists, skipping"
        INSTALL_RESULTS["react-mcp"]="ALREADY_EXISTS"
        SUCCESSFUL_INSTALLS=$((SUCCESSFUL_INSTALLS + 1))
        return 0
    fi

    # Get the absolute path to the react-mcp directory
    REACT_MCP_PATH="$REPO_ROOT/react-mcp/index.js"

    # Check if react-mcp directory exists
    if [ -f "$REACT_MCP_PATH" ]; then
        echo -e "${GREEN}  ✅ Found React MCP server at: $REACT_MCP_PATH${NC}"
        log_with_timestamp "Found React MCP server at: $REACT_MCP_PATH"

        # Ensure dependencies are installed
        if [ -f "${REPO_ROOT}/react-mcp/package.json" ]; then
            if [ ! -d "${REPO_ROOT}/react-mcp/node_modules" ]; then
                echo -e "${BLUE}  📦 Installing react-mcp dependencies...${NC}"

                local dep_exit_code=0
                if [ -f "${REPO_ROOT}/react-mcp/package-lock.json" ]; then
                    capture_command_output dep_output dep_exit_code npm --prefix "${REPO_ROOT}/react-mcp" ci
                else
                    echo -e "${YELLOW}  ⚠️ No package-lock.json found, using npm install instead${NC}"
                    capture_command_output dep_output dep_exit_code npm --prefix "${REPO_ROOT}/react-mcp" install
                fi

                if [ $dep_exit_code -ne 0 ]; then
                    echo -e "${RED}  ❌ Failed to install react-mcp dependencies${NC}"
                    log_error_details "npm dependency installation (react-mcp)" "react-mcp" "$dep_output"
                    update_stats "FAILURE" "react-mcp" "INSTALL_FAILED"
                    echo -e "${YELLOW}  ⚠️ Skipping react-mcp server addition due to dependency failure${NC}"
                    return 1
                fi
                echo -e "${GREEN}  ✅ Dependencies installed for react-mcp${NC}"
            fi
        fi

        # Remove existing react-mcp server to reconfigure
        ${MCP_CLI_BIN} mcp remove "react-mcp" >/dev/null 2>&1 || true

        # Add React MCP server
        echo -e "${BLUE}  🔗 Adding React MCP server...${NC}"
        log_with_timestamp "Attempting to add React MCP server"

        capture_command_output add_output add_exit_code "${MCP_CLI_BIN}" mcp add "${MCP_SCOPE_ARGS[@]}" "react-mcp" "$NODE_PATH" "$REACT_MCP_PATH" "${DEFAULT_MCP_ENV_FLAGS[@]}"
        if [ $add_exit_code -eq 0 ]; then
            echo -e "${GREEN}  ✅ Successfully configured React MCP server${NC}"
            log_with_timestamp "Successfully added React MCP server"
            INSTALL_RESULTS["react-mcp"]="SUCCESS"
            SUCCESSFUL_INSTALLS=$((SUCCESSFUL_INSTALLS + 1))
        else
            echo -e "${RED}  ❌ Failed to add React MCP server${NC}"
            log_error_details "${MCP_CLI_BIN} mcp add react-mcp" "react-mcp" "$add_output"
            INSTALL_RESULTS["react-mcp"]="ADD_FAILED"
            FAILED_INSTALLS=$((FAILED_INSTALLS + 1))
            return 1
        fi
    else
        echo -e "${RED}  ❌ React MCP server not found at expected path: $REACT_MCP_PATH${NC}"
        echo -e "${YELLOW}  💡 Run 'git submodule update --init --recursive' to initialize submodules${NC}"
        log_with_timestamp "ERROR: React MCP server not found at $REACT_MCP_PATH"
        INSTALL_RESULTS["react-mcp"]="DEPENDENCY_MISSING"
        FAILED_INSTALLS=$((FAILED_INSTALLS + 1))
        return 1
    fi
}

# Function to install iOS Simulator MCP server with environment guard
install_ios_simulator_mcp() {
    if [[ "$IOS_SIMULATOR_ENABLED" != "true" ]]; then
        echo -e "${YELLOW}  ⚠️ iOS Simulator MCP server disabled (set IOS_SIMULATOR_ENABLED=true to enable)${NC}"
        return 0
    fi

    TOTAL_SERVERS=$((TOTAL_SERVERS + 1))
    local name="ios-simulator-mcp"
    local TEMP_DIR
    local MCP_SERVERS_DIR
    local IOS_MCP_PATH
    local add_output
    local add_exit_code
    local clone_cmd

    echo -e "${BLUE}📱 Setting up iOS Simulator MCP Server...${NC}"
    log_with_timestamp "Setting up iOS Simulator MCP Server with special handling"

    # Check if server already exists
    if server_already_exists "$name"; then
        echo -e "${GREEN}  ✅ Server $name already exists, skipping installation${NC}"
        log_with_timestamp "Server $name already exists, skipping"
        INSTALL_RESULTS["$name"]="ALREADY_EXISTS"
        SUCCESSFUL_INSTALLS=$((SUCCESSFUL_INSTALLS + 1))
        return 0
    fi

    # Check for macOS environment (iOS Simulator requires macOS)
    if [ "$MACHINE" != "Mac" ]; then
        echo -e "${YELLOW}  ⚠️ iOS Simulator MCP server requires macOS, skipping on $MACHINE${NC}"
        case "$MACHINE" in
            "Linux")
                echo -e "${BLUE}  💡 Consider using Android emulator alternatives for mobile development on Linux${NC}"
                ;;
            "Cygwin"|"MinGw"|"Git")
                echo -e "${BLUE}  💡 Consider using Windows Subsystem for Android (WSA) or Android Studio emulators${NC}"
                ;;
        esac
        log_with_timestamp "iOS Simulator MCP server skipped: requires macOS, current platform is $MACHINE"
        INSTALL_RESULTS["$name"]="PLATFORM_INCOMPATIBLE"
        # Don't count as failure - this is expected behavior on non-Mac platforms
        return 0
    fi

    # Check for Xcode command line tools
    echo -e "${BLUE}  🔍 Checking for Xcode command line tools...${NC}"
    if ! command -v xcrun >/dev/null 2>&1; then
        echo -e "${RED}  ❌ xcrun not found - Xcode command line tools required${NC}"
        echo -e "${YELLOW}  💡 Install with: xcode-select --install${NC}"
        log_with_timestamp "xcrun not found, Xcode command line tools required for iOS Simulator MCP"
        INSTALL_RESULTS["$name"]="DEPENDENCY_MISSING"
        FAILED_INSTALLS=$((FAILED_INSTALLS + 1))
        return 1
    else
        echo -e "${GREEN}  ✅ Xcode command line tools found${NC}"
    fi

    # Check if iOS Simulator is available
    echo -e "${BLUE}  🔍 Checking iOS Simulator availability...${NC}"
    if ! xcrun simctl list devices >/dev/null 2>&1; then
        echo -e "${YELLOW}  ⚠️ iOS Simulator may not be available or configured${NC}"
        echo -e "${YELLOW}  💡 Install Xcode from App Store for full iOS Simulator support${NC}"
    else
        echo -e "${GREEN}  ✅ iOS Simulator is available${NC}"
    fi

    # Install ios-simulator-mcp using git since it's not on npm
    echo -e "${BLUE}  📦 Installing ios-simulator-mcp from GitHub repository...${NC}"

    # Create temporary directory for installation
    TEMP_DIR=$(mktemp -d)
    echo -e "${BLUE}  📁 Using temporary directory: $TEMP_DIR${NC}"

    # Clone the repository with security improvements
    echo -e "${BLUE}  🔄 Cloning ios-simulator-mcp repository...${NC}"
    if [ -n "$TIMEOUT_CMD" ]; then
        if ! "$TIMEOUT_CMD" 60 git clone --depth=1 --single-branch https://github.com/joshuayoes/ios-simulator-mcp.git "$TEMP_DIR/ios-simulator-mcp" >/dev/null 2>&1; then
            echo -e "${RED}  ❌ Failed to clone ios-simulator-mcp repository (timeout)${NC}"
            log_with_timestamp "Failed to clone ios-simulator-mcp repository (timeout)"
            rm -rf "$TEMP_DIR"
            INSTALL_RESULTS["$name"]="CLONE_TIMEOUT"
            FAILED_INSTALLS=$((FAILED_INSTALLS + 1))
            return 1
        fi
    elif ! git clone --depth=1 --single-branch https://github.com/joshuayoes/ios-simulator-mcp.git "$TEMP_DIR/ios-simulator-mcp" >/dev/null 2>&1; then
        echo -e "${RED}  ❌ Failed to clone ios-simulator-mcp repository${NC}"
        log_with_timestamp "Failed to clone ios-simulator-mcp repository"
        rm -rf "$TEMP_DIR"
        INSTALL_RESULTS["$name"]="CLONE_FAILED"
        FAILED_INSTALLS=$((FAILED_INSTALLS + 1))
        return 1
    fi

    # Verify repository integrity
    if [ ! -f "$TEMP_DIR/ios-simulator-mcp/package.json" ]; then
        echo -e "${RED}  ❌ Repository integrity check failed - missing package.json${NC}"
        log_with_timestamp "Repository integrity check failed"
        rm -rf "$TEMP_DIR"
        INSTALL_RESULTS["$name"]="INTEGRITY_FAILED"
        FAILED_INSTALLS=$((FAILED_INSTALLS + 1))
        return 1
    fi

    # Install dependencies in the cloned repository
    echo -e "${BLUE}  📦 Installing dependencies...${NC}"
    local -a dep_cmd
    if [ -f "$TEMP_DIR/ios-simulator-mcp/package-lock.json" ]; then
        dep_cmd=(npm --prefix "$TEMP_DIR/ios-simulator-mcp" ci)
    else
        dep_cmd=(npm --prefix "$TEMP_DIR/ios-simulator-mcp" install)
    fi
    if ! "${dep_cmd[@]}" >/dev/null 2>&1; then
        echo -e "${RED}  ❌ Failed to install dependencies${NC}"
        log_with_timestamp "Failed to install dependencies for ios-simulator-mcp"
        rm -rf "$TEMP_DIR"
        INSTALL_RESULTS["$name"]="INSTALL_FAILED"
        FAILED_INSTALLS=$((FAILED_INSTALLS + 1))
        return 1
    fi

    # Build the TypeScript source so the runtime entrypoint exists
    echo -e "${BLUE}  🛠️  Building iOS Simulator MCP server...${NC}"
    local BUILD_LOG_FILE
    BUILD_LOG_FILE="$(mktemp)"
    trap 'rm -f "$BUILD_LOG_FILE"' RETURN
    local -a build_runner
    build_runner=(npm --prefix "$TEMP_DIR/ios-simulator-mcp" run build)
    if [ -n "$TIMEOUT_CMD" ]; then
        build_runner=("$TIMEOUT_CMD" 180s "${build_runner[@]}")
    fi
    if ! "${build_runner[@]}" >"$BUILD_LOG_FILE" 2>&1; then
        echo -e "${RED}  ❌ Failed to build ios-simulator-mcp${NC}"
        echo -e "${YELLOW}  --- Build output below ---${NC}"
        cat "$BUILD_LOG_FILE"
        echo -e "${YELLOW}  --- End build output ---${NC}"
        log_with_timestamp "Failed to build ios-simulator-mcp"
        rm -rf "$TEMP_DIR"
        INSTALL_RESULTS["$name"]="BUILD_FAILED"
        FAILED_INSTALLS=$((FAILED_INSTALLS + 1))
        rm -f "$BUILD_LOG_FILE"
        trap - RETURN
        return 1
    fi
    rm -f "$BUILD_LOG_FILE"
    trap - RETURN

    # Move to permanent location in ~/.mcp/servers/
    # Use robust home directory detection for cross-platform compatibility
    if [ -n "$HOME" ]; then
        MCP_SERVERS_DIR="$HOME/.mcp/servers"
    elif [ -n "$USERPROFILE" ]; then
        # Windows fallback
        MCP_SERVERS_DIR="$USERPROFILE/.mcp/servers"
    else
        # Last resort fallback
        MCP_SERVERS_DIR="/tmp/.mcp/servers"
        echo -e "${YELLOW}  ⚠️ Using temporary directory for MCP servers: $MCP_SERVERS_DIR${NC}"
    fi
    mkdir -p "$MCP_SERVERS_DIR"
    IOS_MCP_PATH="$MCP_SERVERS_DIR/ios-simulator-mcp"

    # Remove existing installation if present
    if [ -d "$IOS_MCP_PATH" ]; then
        # Validate path before removal for safety
        case "$IOS_MCP_PATH" in
            */\.mcp/servers/ios-simulator-mcp)
                echo -e "${BLUE}  🧹 Removing existing installation...${NC}"
                if [ -d "$IOS_MCP_PATH/.git" ]; then
                    local backup_archive
                    backup_archive="${IOS_MCP_PATH%/}.backup.$(date +%s).tgz"
                    if tar -czf "$backup_archive" -C "$(dirname "$IOS_MCP_PATH")" "$(basename "$IOS_MCP_PATH")" >/dev/null 2>&1; then
                        echo -e "${BLUE}  💾 Backed up existing installation to: $backup_archive${NC}"
                        log_with_timestamp "Backed up existing ios-simulator-mcp to $backup_archive"
                    else
                        echo -e "${YELLOW}  ⚠️ Unable to create backup of existing installation; proceeding with removal${NC}"
                        log_with_timestamp "Failed to create ios-simulator-mcp backup prior to removal"
                    fi
                fi
                rm -rf "$IOS_MCP_PATH"
                ;;
            *)
                echo -e "${RED}❌ Error: Unexpected installation path '$IOS_MCP_PATH', aborting for safety${NC}"
                return 1
                ;;
        esac
    fi

    # Move to permanent location
    echo -e "${BLUE}  📦 Installing to permanent location: $IOS_MCP_PATH${NC}"
    if ! mv "$TEMP_DIR/ios-simulator-mcp" "$IOS_MCP_PATH"; then
        echo -e "${RED}  ❌ Failed to move to permanent location${NC}"
        log_with_timestamp "Failed to move ios-simulator-mcp to permanent location"
        rm -rf "$TEMP_DIR"
        INSTALL_RESULTS["$name"]="INSTALL_FAILED"
        FAILED_INSTALLS=$((FAILED_INSTALLS + 1))
        return 1
    fi

    # Cleanup temporary directory
    rm -rf "$TEMP_DIR"

    # Determine the correct runtime entrypoint (TypeScript build output vs. plain JS)
    local IOS_MCP_ENTRYPOINT
    if [ -f "$IOS_MCP_PATH/build/index.js" ]; then
        IOS_MCP_ENTRYPOINT="$IOS_MCP_PATH/build/index.js"
        log_with_timestamp "Using built entrypoint: $IOS_MCP_ENTRYPOINT"
    elif [ -f "$IOS_MCP_PATH/index.js" ]; then
        IOS_MCP_ENTRYPOINT="$IOS_MCP_PATH/index.js"
        echo -e "${YELLOW}  ⚠️ build/index.js not found; falling back to index.js${NC}"
        log_with_timestamp "build/index.js missing, using index.js for ios-simulator-mcp"
    else
        echo -e "${RED}  ❌ Could not locate ios-simulator-mcp entrypoint after install${NC}"
        log_with_timestamp "Failed to locate ios-simulator-mcp entrypoint"
        INSTALL_RESULTS["$name"]="ENTRYPOINT_MISSING"
        FAILED_INSTALLS=$((FAILED_INSTALLS + 1))
        return 1
    fi

    # Add server to ${MCP_PRODUCT_NAME} MCP configuration
    echo -e "${BLUE}  🔗 Adding iOS Simulator MCP server to ${MCP_PRODUCT_NAME} configuration...${NC}"

    # Remove existing server if present
    ${MCP_CLI_BIN} mcp remove "$name" >/dev/null 2>&1 || true

    # Add server using node to run the compiled entrypoint
    capture_command_output add_output add_exit_code "${MCP_CLI_BIN}" mcp add "${MCP_SCOPE_ARGS[@]}" "$name" "$NODE_PATH" "$IOS_MCP_ENTRYPOINT" "${DEFAULT_MCP_ENV_FLAGS[@]}"

    if [ $add_exit_code -eq 0 ]; then
        echo -e "${GREEN}  ✅ Successfully configured iOS Simulator MCP server${NC}"
        echo -e "${BLUE}  📋 Server info:${NC}"
        echo -e "     • Path: $IOS_MCP_ENTRYPOINT"
        echo -e "     • Platform: macOS with iOS Simulator support"
        echo -e "     • Features: iOS app control, simulator management, screenshot capture"
        echo -e "     • Repository: https://github.com/joshuayoes/ios-simulator-mcp"
        log_with_timestamp "Successfully added iOS Simulator MCP server"
        INSTALL_RESULTS["$name"]="SUCCESS"
        SUCCESSFUL_INSTALLS=$((SUCCESSFUL_INSTALLS + 1))
    else
        echo -e "${RED}  ❌ Failed to add iOS Simulator MCP server to ${MCP_PRODUCT_NAME} configuration${NC}"
        log_error_details "${MCP_CLI_BIN} mcp add ios-simulator-mcp" "$name" "$add_output"
        echo -e "${RED}  📋 Add error: $add_output${NC}"
        INSTALL_RESULTS["$name"]="ADD_FAILED"
        FAILED_INSTALLS=$((FAILED_INSTALLS + 1))
        return 1
    fi
}

# Function to install GitHub MCP server with environment guard
install_github_mcp() {
    if [[ "$GITHUB_MCP_ENABLED" != "true" ]]; then
        echo -e "${YELLOW}  ⚠️ GitHub MCP server disabled (set GITHUB_MCP_ENABLED=true to enable)${NC}"
        return 0
    fi

    echo -e "${BLUE}  🔧 Setting up github-server (NEW Official Remote HTTP Server)...${NC}"
    log_with_timestamp "Setting up GitHub MCP server with environment guard"
    local add_output=""
    local add_exit_code=0

    # Check if server already exists
    if server_already_exists "github-server"; then
        echo -e "${GREEN}  ✅ Server github-server already exists, skipping installation${NC}"
        log_with_timestamp "Server github-server already exists, skipping"
        INSTALL_RESULTS["github-server"]="ALREADY_EXISTS"
        SUCCESSFUL_INSTALLS=$((SUCCESSFUL_INSTALLS + 1))
    else
        echo -e "${BLUE}  🔗 Adding GitHub official remote MCP server...${NC}"
        log_with_timestamp "Adding GitHub official remote MCP server"

        # Remove any old deprecated GitHub server first
        ${MCP_CLI_BIN} mcp remove "github-server" >/dev/null 2>&1 || true

        # Add the new official GitHub HTTP MCP server (secure: token via temporary file)
        local temp_config=$(mktemp -t github_mcp.XXXXXX)
        chmod 600 "$temp_config"
        cat > "$temp_config" <<EOF
{"type":"http","url":"https://api.githubcopilot.com/mcp/","authorization_token":"Bearer ${GITHUB_PERSONAL_ACCESS_TOKEN}"}
EOF
        capture_command_output add_output add_exit_code "${MCP_CLI_BIN}" mcp add-json "${MCP_SCOPE_ARGS[@]}" "github-server" - < "$temp_config"
        rm -f "$temp_config"

        if [ $add_exit_code -eq 0 ]; then
            echo -e "${GREEN}  ✅ Successfully added GitHub remote MCP server${NC}"
            log_with_timestamp "Successfully added GitHub remote MCP server"
            INSTALL_RESULTS["github-server"]="SUCCESS"
            SUCCESSFUL_INSTALLS=$((SUCCESSFUL_INSTALLS + 1))
        else
            echo -e "${RED}  ❌ Failed to add GitHub remote MCP server${NC}"
            log_error_details "${MCP_CLI_BIN} mcp add-json" "github-server" "$add_output"
            echo -e "${RED}  📋 Add error: $add_output${NC}"
            INSTALL_RESULTS["github-server"]="ADD_FAILED"
            FAILED_INSTALLS=$((FAILED_INSTALLS + 1))
        fi
    fi
}

# Core MCP Servers Installation
echo -e "${BLUE}📊 Installing Core MCP Servers with Parallel Processing...${NC}"

display_step "Setting up GitHub MCP Server (Official Remote)..."
# GitHub released a new official MCP server that replaces @modelcontextprotocol/server-github
# The new server is HTTP-based and hosted by GitHub for better reliability and features
install_github_mcp

display_step "Installing Batch 1 Servers (Parallel)..."
install_batch_parallel BATCH_1 "Batch 1"

display_step "Installing Optional Playwright MCP Server..."
install_playwright_mcp

display_step "Setting up Memory MCP Server..."
# Create memory data directory in user's home
mkdir -p ~/.cache/mcp-memory
echo -e "${BLUE}  📁 Memory data directory: ~/.cache/mcp-memory/${NC}"

# Configure memory server with custom data path
MEMORY_PATH="$HOME/.cache/mcp-memory/memory.json"
echo -e "${BLUE}  📁 Memory file path: $MEMORY_PATH${NC}"

# Remove existing memory server to reconfigure
${MCP_CLI_BIN} mcp remove "memory-server" -s "${MCP_SCOPE}" >/dev/null 2>&1 || true

# Add memory server with environment variable configuration
echo -e "${BLUE}  🔗 Adding memory server with custom configuration...${NC}"
capture_command_output add_output add_exit_code "${MCP_CLI_BIN}" mcp add "${MCP_SCOPE_ARGS[@]}" "memory-server" "$NPX_PATH" "@modelcontextprotocol/server-memory" "${DEFAULT_MCP_ENV_FLAGS[@]}" --env "MEMORY_FILE_PATH=$MEMORY_PATH"

if [ $add_exit_code -eq 0 ]; then
    echo -e "${GREEN}  ✅ Successfully configured memory server with custom path${NC}"
    log_with_timestamp "Successfully added memory server with custom path: $MEMORY_PATH"
else
    echo -e "${YELLOW}  ⚠️ Environment variable method failed, trying fallback...${NC}"
    log_with_timestamp "Environment variable method failed: $add_output"

    # Fallback: use standard add but create a symlink or wrapper script
    echo -e "${BLUE}  🔄 Using fallback configuration method...${NC}"

    # Create wrapper script that sets the environment variable
    WRAPPER_SCRIPT="$HOME/.cache/mcp-memory/memory-server-wrapper.sh"
    local debug_env_var="MCP_${MCP_PRODUCT_NAME_UPPER}_DEBUG"
    cat > "$WRAPPER_SCRIPT" <<EOF
#!/bin/bash
export MEMORY_FILE_PATH="\$HOME/.cache/mcp-memory/memory.json"
export ${debug_env_var}=false
export MCP_VERBOSE_TOOLS=false
export MCP_AUTO_DISCOVER=false
exec npx @modelcontextprotocol/server-memory "\$@"
EOF
    chmod +x "$WRAPPER_SCRIPT"

    # Add server using the wrapper script
    capture_command_output fallback_output fallback_exit_code "${MCP_CLI_BIN}" mcp add "${MCP_SCOPE_ARGS[@]}" "memory-server" "$WRAPPER_SCRIPT" "${DEFAULT_MCP_ENV_FLAGS[@]}"

    if [ $fallback_exit_code -eq 0 ]; then
        echo -e "${GREEN}  ✅ Successfully added memory server with wrapper script${NC}"
        log_with_timestamp "Successfully added memory server with wrapper script"
    else
        echo -e "${RED}  ❌ Both methods failed for memory server${NC}"
        log_error_details "${MCP_CLI_BIN} mcp add wrapper" "memory-server" "$fallback_output"
        echo -e "${YELLOW}  💡 You may need to manually configure the memory server${NC}"
    fi
fi

display_step "Installing Batch 2 Servers (Parallel)..."
install_batch_parallel BATCH_2 "Batch 2"

display_step "Installing iOS Simulator MCP Server..."
install_ios_simulator_mcp

display_step "Setting up Web Search MCP Servers..."
echo -e "${BLUE}📋 Installing both free DuckDuckGo and premium Perplexity search servers${NC}"

# Remove existing web search servers to avoid conflicts
${MCP_CLI_BIN} mcp remove "web-search-duckduckgo" >/dev/null 2>&1 || true
${MCP_CLI_BIN} mcp remove "perplexity-ask" >/dev/null 2>&1 || true
${MCP_CLI_BIN} mcp remove "perplexity-search" >/dev/null 2>&1 || true
${MCP_CLI_BIN} mcp remove "ddg-search" >/dev/null 2>&1 || true

# DuckDuckGo is now installed in Batch 2
echo -e "${BLUE}  → DuckDuckGo Web Search (Free) - installed in Batch 2${NC}"
echo -e "${GREEN}✅ DuckDuckGo search - completely free, no API key needed${NC}"
echo -e "${BLUE}📋 Features: Web search, content fetching, privacy-focused${NC}"

# Install Perplexity search server (premium, requires API key)
echo -e "\n${BLUE}  → Perplexity AI Search (Premium)...${NC}"
if [ -n "$PERPLEXITY_API_KEY" ]; then
    echo -e "${GREEN}✅ Perplexity API key found - installing premium search server${NC}"
    echo -e "${BLUE}📋 Features: AI-powered search, real-time web research, advanced queries${NC}"

    # Add Perplexity server with API key - using @chatmcp/server-perplexity-ask (working alternative)
    # Note: Replaced problematic 'server-perplexity-ask' package with working distribution
    echo -e "${BLUE}    🔧 Installing Perplexity search server...${NC}"
    capture_command_output add_output add_exit_code "${MCP_CLI_BIN}" mcp add "${MCP_SCOPE_ARGS[@]}" "perplexity-ask" "npx" "@chatmcp/server-perplexity-ask" "${DEFAULT_MCP_ENV_FLAGS[@]}" --env "PERPLEXITY_API_KEY=$PERPLEXITY_API_KEY"

    if [ $add_exit_code -eq 0 ]; then
        echo -e "${GREEN}    ✅ Successfully added Perplexity search server${NC}"
        log_with_timestamp "Successfully added Perplexity search server with API key"
        INSTALL_RESULTS["perplexity-ask"]="SUCCESS"
        SUCCESSFUL_INSTALLS=$((SUCCESSFUL_INSTALLS + 1))
    else
        echo -e "${RED}    ❌ Failed to add Perplexity search server${NC}"
        log_error_details "${MCP_CLI_BIN} mcp add perplexity" "perplexity-ask" "$add_output"
        INSTALL_RESULTS["perplexity-ask"]="ADD_FAILED"
        FAILED_INSTALLS=$((FAILED_INSTALLS + 1))
    fi
else
    echo -e "${YELLOW}⚠️ Perplexity API key not found - skipping premium server${NC}"
    echo -e "${YELLOW}💡 Perplexity server provides AI-powered search with real-time web research${NC}"
    echo -e "${YELLOW}💡 Add PERPLEXITY_API_KEY to ~/.token file to enable${NC}"
    log_with_timestamp "Perplexity API key not found, skipping premium server installation"
fi

# Optional: Notion Server (if available)
display_step "Setting up Filesystem MCP Server..."
TOTAL_SERVERS=$((TOTAL_SERVERS + 1))
echo -e "${BLUE}  📁 Configuring filesystem access for projects directory...${NC}"
log_with_timestamp "Setting up MCP server: filesystem (package: @modelcontextprotocol/server-filesystem)"

# Check if server already exists
if server_already_exists "filesystem"; then
    echo -e "${GREEN}  ✅ Server filesystem already exists, skipping installation${NC}"
    log_with_timestamp "Server filesystem already exists, skipping"
    INSTALL_RESULTS["filesystem"]="ALREADY_EXISTS"
    SUCCESSFUL_INSTALLS=$((SUCCESSFUL_INSTALLS + 1))
else
    # Remove existing filesystem server to reconfigure with proper directory access
    ${MCP_CLI_BIN} mcp remove "filesystem" >/dev/null 2>&1 || true

    # Add filesystem server with proper directory configuration
    echo -e "${BLUE}  🔗 Adding filesystem server with $HOME/projects access...${NC}"
    capture_command_output add_output add_exit_code "${MCP_CLI_BIN}" mcp add "${MCP_SCOPE_ARGS[@]}" "filesystem" "$NPX_PATH" "@modelcontextprotocol/server-filesystem" "$HOME/projects" "${DEFAULT_MCP_ENV_FLAGS[@]}"

    if [ $add_exit_code -eq 0 ]; then
        echo -e "${GREEN}  ✅ Successfully configured filesystem server with project directory access${NC}"
        log_with_timestamp "Successfully added filesystem server with $HOME/projects access"
        INSTALL_RESULTS["filesystem"]="SUCCESS"
        SUCCESSFUL_INSTALLS=$((SUCCESSFUL_INSTALLS + 1))
    else
        echo -e "${RED}  ❌ Failed to add filesystem server${NC}"
        log_error_details "${MCP_CLI_BIN} mcp add filesystem" "filesystem" "$add_output"
        INSTALL_RESULTS["filesystem"]="ADD_FAILED"
        FAILED_INSTALLS=$((FAILED_INSTALLS + 1))
    fi
fi



display_step "Setting up React MCP Server..."
install_react_mcp

display_step "Setting up WorldArchitect MCP Server..."
TOTAL_SERVERS=$((TOTAL_SERVERS + 1))
echo -e "${BLUE}  🎮 Configuring project MCP server for application mechanics...${NC}"
log_with_timestamp "Setting up MCP server: worldarchitect (local: mvp_site/mcp_api.py)"

# Check if server already exists
if server_already_exists "worldarchitect"; then
    echo -e "${GREEN}  ✅ Server worldarchitect already exists, skipping installation${NC}"
    log_with_timestamp "Server worldarchitect already exists, skipping"
    INSTALL_RESULTS["worldarchitect"]="ALREADY_EXISTS"
    SUCCESSFUL_INSTALLS=$((SUCCESSFUL_INSTALLS + 1))
else
    # Get the absolute path to the WorldArchitect project
    WORLDARCHITECT_MCP_PATH="$REPO_ROOT/mvp_site/mcp_api.py"
    WORLDARCHITECT_PYTHON="$REPO_ROOT/venv/bin/python"

    # Check if mcp_api.py exists
    if [ -f "$WORLDARCHITECT_MCP_PATH" ]; then
        echo -e "${GREEN}  ✅ Found WorldArchitect MCP server at: $WORLDARCHITECT_MCP_PATH${NC}"
        log_with_timestamp "Found WorldArchitect MCP server at: $WORLDARCHITECT_MCP_PATH"

        # Remove existing worldarchitect server to reconfigure
        ${MCP_CLI_BIN} mcp remove "worldarchitect" >/dev/null 2>&1 || true

        # Add WorldArchitect MCP server using Python with proper environment
        echo -e "${BLUE}  🔗 Adding WorldArchitect MCP server...${NC}"
        log_with_timestamp "Attempting to add WorldArchitect MCP server"

        capture_command_output add_output add_exit_code "${MCP_CLI_BIN}" mcp add "${MCP_SCOPE_ARGS[@]}" "worldarchitect" "$WORLDARCHITECT_PYTHON" "$WORLDARCHITECT_MCP_PATH" "${DEFAULT_MCP_ENV_FLAGS[@]}"

        if [ $add_exit_code -eq 0 ]; then
            echo -e "${GREEN}  ✅ Successfully configured WorldArchitect MCP server${NC}"
            echo -e "${BLUE}  📋 Server info:${NC}"
            echo -e "     • Path: $WORLDARCHITECT_MCP_PATH"
            echo -e "     • Available tools: D&D campaign creation, character management, game actions, world state"
            echo -e "     • Features: Real D&D 5e mechanics, Gemini API integration, Firebase storage"
            log_with_timestamp "Successfully added WorldArchitect MCP server"
            INSTALL_RESULTS["worldarchitect"]="SUCCESS"
            SUCCESSFUL_INSTALLS=$((SUCCESSFUL_INSTALLS + 1))
        else
            echo -e "${RED}  ❌ Failed to add WorldArchitect MCP server${NC}"
            log_error_details "${MCP_CLI_BIN} mcp add worldarchitect" "worldarchitect" "$add_output"
            INSTALL_RESULTS["worldarchitect"]="ADD_FAILED"
            FAILED_INSTALLS=$((FAILED_INSTALLS + 1))
        fi
    else
        echo -e "${RED}  ❌ WorldArchitect MCP server not found at expected path: $WORLDARCHITECT_MCP_PATH${NC}"
        echo -e "${YELLOW}  💡 Ensure you're running this script from the WorldArchitect.AI project root${NC}"
        log_with_timestamp "ERROR: WorldArchitect MCP server not found at $WORLDARCHITECT_MCP_PATH"
        INSTALL_RESULTS["worldarchitect"]="DEPENDENCY_MISSING"
        FAILED_INSTALLS=$((FAILED_INSTALLS + 1))
    fi
fi

# Setup Render MCP Server
setup_render_mcp_server

display_step "Setting up Serena MCP Server..."
TOTAL_SERVERS=$((TOTAL_SERVERS + 1))
echo -e "${BLUE}  🧠 Configuring Serena MCP server for semantic code analysis...${NC}"
log_with_timestamp "Setting up MCP server: serena (uvx: git+https://github.com/oraios/serena)"

# Pre-flight check: Ensure uvx is available
echo -e "${BLUE}  🔍 Checking uvx availability...${NC}"
if ! command -v uvx >/dev/null 2>&1; then
    echo -e "${RED}  ❌ 'uvx' not found - required for Serena MCP server${NC}"
    echo -e "${YELLOW}  💡 Install uvx with: pip install uv${NC}"
    log_with_timestamp "ERROR: uvx not found, skipping Serena MCP server installation"
    INSTALL_RESULTS["serena"]="DEPENDENCY_MISSING"
    FAILED_INSTALLS=$((FAILED_INSTALLS + 1))
    TOTAL_SERVERS=$((TOTAL_SERVERS - 1))  # Correct count since we're not installing
else
    echo -e "${GREEN}  ✅ uvx found: $(uvx --version 2>/dev/null || echo "available")${NC}"
    log_with_timestamp "uvx dependency check passed"

    # Check if server already exists
    if server_already_exists "serena"; then
    echo -e "${GREEN}  ✅ Server serena already exists, skipping installation${NC}"
    log_with_timestamp "Server serena already exists, skipping"
    INSTALL_RESULTS["serena"]="ALREADY_EXISTS"
    SUCCESSFUL_INSTALLS=$((SUCCESSFUL_INSTALLS + 1))
else
    # Remove existing serena server to reconfigure
    ${MCP_CLI_BIN} mcp remove "serena" >/dev/null 2>&1 || true

    # Add Serena MCP server using uvx with git repository
    echo -e "${BLUE}  🔗 Adding Serena MCP server via uvx...${NC}"
    log_with_timestamp "Attempting to add Serena MCP server via uvx"

    # Use add-json for uvx configuration
    local debug_env_var="MCP_${MCP_PRODUCT_NAME_UPPER}_DEBUG"
    local serena_payload
    serena_payload=$(printf '{"command":"uvx","args":["--from","git+https://github.com/oraios/serena","serena","start-mcp-server"],"env":{"%s":"false","MCP_VERBOSE_TOOLS":"false","MCP_AUTO_DISCOVER":"false"}}' "$debug_env_var")
    capture_command_output add_output add_exit_code "${MCP_CLI_BIN}" mcp add-json "${MCP_SCOPE_ARGS[@]}" "serena" "$serena_payload"

    if [ $add_exit_code -eq 0 ]; then
        echo -e "${GREEN}  ✅ Successfully configured Serena MCP server${NC}"
        echo -e "${BLUE}  📋 Server info:${NC}"
        echo -e "     • Repository: https://github.com/oraios/serena"
        echo -e "     • Available tools: Semantic code analysis, file operations, memory system"
        echo -e "     • Dashboard: http://127.0.0.1:24282/dashboard/index.html"
        echo -e "     • Configuration: ~/.serena/serena_config.yml"
        log_with_timestamp "Successfully added Serena MCP server via uvx"
        INSTALL_RESULTS["serena"]="SUCCESS"
        SUCCESSFUL_INSTALLS=$((SUCCESSFUL_INSTALLS + 1))
    else
        echo -e "${RED}  ❌ Failed to add Serena MCP server${NC}"
        log_error_details "${MCP_CLI_BIN} mcp add-json serena" "serena" "$add_output"
        INSTALL_RESULTS["serena"]="ADD_FAILED"
        FAILED_INSTALLS=$((FAILED_INSTALLS + 1))
    fi
    fi
fi

# Final verification and results
echo -e "\n${BLUE}✅ Verifying final installation...${NC}"
MCP_LIST=$(${MCP_CLI_BIN} mcp list 2>/dev/null)
ACTUAL_SERVERS=$(echo "$MCP_LIST" | grep -E "^[a-zA-Z].*:" | wc -l)

echo -e "\n${GREEN}📋 Installation Results Summary:${NC}"
echo -e "${GREEN}=================================${NC}"
echo -e "${BLUE}Total servers attempted: $TOTAL_SERVERS${NC}"
echo -e "${GREEN}Successful installations: $SUCCESSFUL_INSTALLS${NC}"
echo -e "${RED}Failed installations: $FAILED_INSTALLS${NC}"
echo -e "${BLUE}Currently active servers: $ACTUAL_SERVERS${NC}"

echo -e "\n${BLUE}📊 Detailed Results:${NC}"
for server in "${!INSTALL_RESULTS[@]}"; do
    result="${INSTALL_RESULTS[$server]}"
    case "$result" in
        "SUCCESS")
            echo -e "${GREEN}  ✅ $server: Installed and working${NC}"
            ;;
        "NEEDS_CONFIG")
            echo -e "${YELLOW}  ⚠️ $server: Installed but may need configuration${NC}"
            ;;
        "ALREADY_EXISTS")
            echo -e "${BLUE}  ℹ️ $server: Already existed, skipped installation${NC}"
            ;;
        "PACKAGE_NOT_FOUND")
            echo -e "${RED}  ❌ $server: Package not found in npm registry${NC}"
            ;;
        "INSTALL_FAILED")
            echo -e "${RED}  ❌ $server: Failed to install npm package${NC}"
            ;;
        "ADD_FAILED")
            echo -e "${RED}  ❌ $server: Failed to add to ${MCP_PRODUCT_NAME} MCP${NC}"
            ;;
        "DEPENDENCY_MISSING")
            echo -e "${RED}  ❌ $server: Required dependency not found${NC}"
            ;;
        "PLATFORM_INCOMPATIBLE")
            echo -e "${YELLOW}  ⚠️ $server: Platform incompatible (requires different OS)${NC}"
            ;;
        "CLONE_FAILED")
            echo -e "${RED}  ❌ $server: Failed to clone repository${NC}"
            ;;
    esac
done

# Backup System Verification
verify_backup_system() {
    local backup_status="healthy"
    local issues_found=0

    echo -e "\n${BLUE}🔍 Verifying ${MCP_PRODUCT_NAME} backup system...${NC}"

    # Check if backup cron job is configured
    if crontab -l 2>/dev/null | grep -q "${MCP_BACKUP_PREFIX}_backup"; then
        echo -e "${GREEN}  ✅ Backup cron job is configured${NC}"
        local cron_line=$(crontab -l 2>/dev/null | grep "${MCP_BACKUP_PREFIX}_backup")
        echo -e "${CYAN}     Schedule: $cron_line${NC}"
    else
        echo -e "${YELLOW}  ⚠️ No backup cron job found${NC}"
        echo -e "${YELLOW}     Run: ./scripts/${MCP_BACKUP_PREFIX}_backup.sh --setup-cron${NC}"
        backup_status="warning"
        ((issues_found++))
    fi

    # Check if backup script exists and is executable in portable location
    local backup_script="$HOME/.local/bin/${MCP_BACKUP_PREFIX}_backup.sh"
    if [[ -x "$backup_script" ]]; then
        echo -e "${GREEN}  ✅ Backup script is executable (portable location): $backup_script${NC}"
    elif [[ -f "$backup_script" ]]; then
        echo -e "${YELLOW}  ⚠️ Backup script exists but not executable: $backup_script${NC}"
        echo -e "${YELLOW}     Run: chmod +x $backup_script${NC}"
        backup_status="warning"
        ((issues_found++))
    else
        echo -e "${RED}  ❌ Backup script not found in portable location: $backup_script${NC}"
        echo -e "${RED}     Run: ./scripts/install_backup_system.sh${NC}"
        backup_status="error"
        ((issues_found++))
    fi

    # Check if backup destination is accessible
    local product_dir="$HOME/.${MCP_BACKUP_PREFIX}"
    if [[ -d "$product_dir" ]]; then
        echo -e "${GREEN}  ✅ ${MCP_PRODUCT_NAME} directory exists: $product_dir${NC}"
        local file_count=$(find "$product_dir" -type f 2>/dev/null | wc -l | tr -d ' ')
        echo -e "${CYAN}     Files to backup: $file_count${NC}"
    else
        echo -e "${YELLOW}  ⚠️ ${MCP_PRODUCT_NAME} directory not found: $product_dir${NC}"
        backup_status="warning"
        ((issues_found++))
    fi

    # Check recent backup activity
    # Security: Check consistent shared backup log directory
    local backup_log_dir="${TMPDIR:-/tmp}/${MCP_BACKUP_PREFIX}_backup_logs"
    local backup_log=""

    # Look for latest backup log in shared secure directory
    if [[ -d "$backup_log_dir" ]]; then
        # Find the most recent backup log file
        # Cross-platform stat detection (GNU vs BSD)
        if stat --version >/dev/null 2>&1; then
            # GNU stat (Linux)
            backup_log=$(find "$backup_log_dir" -name "${MCP_BACKUP_PREFIX}_backup_*.log" -type f -exec stat -c '%Y %n' {} + 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2- || echo "")
        else
            # BSD stat (macOS) - need different approach for find+stat
            backup_log=$(find "$backup_log_dir" -name "${MCP_BACKUP_PREFIX}_backup_*.log" -type f -print0 2>/dev/null | while IFS= read -r -d '' file; do
                timestamp=$(stat -f %m "$file" 2>/dev/null)
                echo "$timestamp $file"
            done | sort -n | tail -1 | cut -d' ' -f2- || echo "")
        fi
        if [[ -z "$backup_log" ]]; then
            # If no timestamped logs, check for generic log name
            if [[ -f "$backup_log_dir/${MCP_BACKUP_PREFIX}_backup_cron.log" ]]; then
                backup_log="$backup_log_dir/${MCP_BACKUP_PREFIX}_backup_cron.log"
            fi
        fi
    fi

    # Fallback to legacy insecure location if shared directory not found
    if [[ -z "$backup_log" && -f "/tmp/${MCP_BACKUP_PREFIX}_backup_cron.log" ]]; then
        backup_log="/tmp/${MCP_BACKUP_PREFIX}_backup_cron.log"
        echo -e "${YELLOW}  ⚠️ Using insecure legacy log location: /tmp/${MCP_BACKUP_PREFIX}_backup_cron.log${NC}"
    fi

    if [[ -n "$backup_log" && -f "$backup_log" ]]; then
        local last_backup_time=$(stat -c %Y "$backup_log" 2>/dev/null || stat -f %m "$backup_log" 2>/dev/null)
        local current_time=$(date +%s)
        if [[ "$last_backup_time" =~ ^[0-9]+$ ]] && (( current_time >= last_backup_time )); then
            local hours_since_backup=$(( (current_time - last_backup_time) / 3600 ))
        else
            echo -e "${YELLOW}  ⚠️ Unable to compute hours since last backup (stat parse issue)${NC}"
            hours_since_backup=9999
        fi

        if [[ $hours_since_backup -le 6 ]]; then
            echo -e "${GREEN}  ✅ Recent backup activity (${hours_since_backup}h ago)${NC}"
        else
            echo -e "${YELLOW}  ⚠️ No recent backup activity (${hours_since_backup}h ago)${NC}"
            backup_status="warning"
            ((issues_found++))
        fi
    else
        # Define the expected log locations for user reference
        local backup_log_secure="$backup_log_dir/${MCP_BACKUP_PREFIX}_backup_*.log"
        local backup_log_legacy="/tmp/${MCP_BACKUP_PREFIX}_backup.log"
        echo -e "${YELLOW}  ⚠️ No backup log found in secure ($backup_log_secure) or legacy ($backup_log_legacy) locations${NC}"
        backup_status="warning"
        ((issues_found++))
    fi

    # Summary
    case "$backup_status" in
        "healthy")
            echo -e "${GREEN}  🎉 Backup system is healthy${NC}"
            ;;
        "warning")
            echo -e "${YELLOW}  ⚠️ Backup system has $issues_found warnings${NC}"
            ;;
        "error")
            echo -e "${RED}  ❌ Backup system has $issues_found errors${NC}"
            ;;
    esac

    return $issues_found
}

# Run backup verification
verify_backup_system

echo -e "\n${BLUE}🔍 Current MCP Server List:${NC}"
echo "$MCP_LIST"

# Final logging summary
log_with_timestamp "Installation completed: $SUCCESSFUL_INSTALLS successful, $FAILED_INSTALLS failed"
echo -e "\n${BLUE}📝 Detailed log saved to: $LOG_FILE${NC}"
echo -e "${BLUE}💡 To view log: cat $LOG_FILE${NC}"

if [ "$SUCCESSFUL_INSTALLS" -gt 0 ]; then
    echo -e "\n${GREEN}🎉 MCP servers installed successfully!${NC}"
    if [ "$FAILED_INSTALLS" -gt 0 ]; then
        echo -e "${YELLOW}⚠️ Some servers failed to install. Check the detailed results above or log file.${NC}"
        echo -e "${YELLOW}💡 Log file: $LOG_FILE${NC}"
    fi
    safe_exit 0
else
    echo -e "\n${RED}❌ No servers were successfully installed. Please check the errors above.${NC}"
    echo -e "${RED}💡 Check the detailed log: $LOG_FILE${NC}"
    safe_exit 1
fi
