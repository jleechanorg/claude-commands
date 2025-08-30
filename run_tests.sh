#!/bin/bash

# Test Runner Script for WorldArchitect.ai with Intelligent Test Selection
# Runs test_*.py files using intelligent selection by default or full suite with --full
# Always runs in CI simulation mode to catch environment-specific issues
#
# Usage:
#   ./run_tests.sh                           # Intelligent test selection (default, CI simulation)
#   ./run_tests.sh --full                    # Run complete test suite (CI simulation)
#   ./run_tests.sh test_file.py              # Run single specific test file
#   ./run_tests.sh test1.py test2.py         # Run multiple specific test files (serial execution)
#   ./run_tests.sh --dry-run                 # Show intelligent selection without execution
#   ./run_tests.sh --integration             # Include integration tests (works with intelligent mode)
#   ./run_tests.sh --unit                    # Run unit tests only (excludes integration tests - default)
#   ./run_tests.sh --parallel                # Run tests in parallel (default behavior)
#   ./run_tests.sh --unit --parallel         # Run unit tests in parallel (explicit flags)
#   ./run_tests.sh --coverage                # Run tests with coverage analysis
#   ./run_tests.sh --integration --coverage  # Run unit and integration tests with coverage
#   ./run_tests.sh --full --integration      # Full suite including integration tests
#   ./run_tests.sh --dry-run --integration   # Preview intelligent selection with integration tests
#   ./run_tests.sh --mcp                     # Run MCP server tests (requires MCP server running)
#
# CI Simulation Features:
# - Always simulates GitHub Actions environment to catch deployment issues early
# - Sets CI environment variables (CI=true, GITHUB_ACTIONS=true, MOCK_SERVICES_MODE=true)
# - Uses same environment setup as actual GitHub Actions workflow
# - Tests run with same dependencies as CI environment
#
# Intelligent Selection Features:
# - Analyzes git changes vs origin/main to select relevant tests
# - Typically reduces test execution by 60-80% for focused PRs
# - Falls back to full suite on analysis failures or large changesets
# - Maintains all safety features (memory monitoring, parallel execution)
#
# Integration tests (in test_integration/) require external dependencies like google-genai
# and are excluded by default to ensure tests run quickly and without external dependencies.
# Coverage runs tests sequentially (not parallel) for accurate coverage tracking.
# Coverage HTML output goes to: /tmp/worldarchitectai/coverage/

# Note: Not using 'set -e' so we can run all tests even if some fail

# Store project root before changing directories
PROJECT_ROOT="$(cd "$(dirname "$0")"; pwd)"

# Source venv utilities and setup venv if needed
source "$PROJECT_ROOT/scripts/venv_utils.sh"
ensure_venv

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Memory monitoring configuration
MEMORY_LIMIT_GB=30  # Kill script if total memory usage exceeds this (out of 47GB available)
SINGLE_PROCESS_LIMIT_GB=10  # Kill individual test if it exceeds this
MONITOR_INTERVAL=2  # Check memory every N seconds
LOG_INTERVAL=5     # Log detailed process info every N seconds

# Memory monitoring functions
get_memory_usage_gb() {
    local pid="$1"
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        # Get RSS memory in KB and convert to GB
        local rss=$(ps -o rss= -p "$pid" 2>/dev/null | tr -d ' ')
        if [ -n "$rss" ]; then
            echo "scale=2; $rss / 1024 / 1024" | bc -l
        else
            echo "0"
        fi
    else
        echo "0"
    fi
}

get_total_memory_usage_gb() {
    # Get total memory usage for all our test processes
    local total_kb=$(pgrep -f "python.*test_" | xargs -r ps -o rss= -p 2>/dev/null | awk '{sum+=$1} END {print sum+0}')
    echo "scale=2; $total_kb / 1024 / 1024" | bc -l
}

memory_monitor() {
    local monitor_file="$1"
    local log_counter=0
    local start_time=$(date +%s)

    # Redirect output to avoid interfering with main script
    exec 3>&1  # Save stdout
    exec 1>/dev/null  # Redirect stdout to null during background monitoring

    while [ -f "$monitor_file" ]; do
        local current_time=$(date +%s)
        local total_memory=$(get_total_memory_usage_gb)
        local comparison=$(echo "$total_memory > $MEMORY_LIMIT_GB" | bc -l 2>/dev/null)

        # Log detailed process info every 3 iterations (every 6 seconds)
        if [ $((log_counter % 3)) -eq 0 ]; then
            local elapsed=$((current_time - start_time))
            echo -e "${BLUE}[INFO]${NC} ⏱️  Memory Monitor [${elapsed}s]: Total=${total_memory}GB (limit: ${MEMORY_LIMIT_GB}GB)" >&3

            # Show all Python test processes with memory usage
            local python_procs=$(pgrep -f "python.*test_" 2>/dev/null)
            if [ -n "$python_procs" ]; then
                echo -e "${BLUE}[INFO]${NC} 📊 Active test processes:" >&3
                for pid in $python_procs; do
                    local mem=$(get_memory_usage_gb "$pid")
                    local cmd=$(ps -p "$pid" -o args= 2>/dev/null | head -c 60)
                    if [ -n "$cmd" ]; then
                        echo -e "${BLUE}[INFO]${NC}   PID:$pid Mem:${mem}GB Command: $cmd" >&3
                    fi
                done
            fi
        fi

        # Check for memory violations
        if [ "$comparison" = "1" ]; then
            echo -e "${RED}[ERROR]${NC} 🚨 Total memory usage exceeds limit: ${total_memory}GB > ${MEMORY_LIMIT_GB}GB" >&3
            echo -e "${RED}[ERROR]${NC} 💀 Terminating all test processes for memory safety" >&3

            # Kill all Python test processes
            pgrep -f "python.*test_" | xargs -r kill -TERM 2>/dev/null || true
            sleep 2
            pgrep -f "python.*test_" | xargs -r kill -KILL 2>/dev/null || true

            echo -e "${RED}[ERROR]${NC} ❌ Test execution halted due to memory limit violation" >&3
            break
        fi

        # Check individual process limits
        for pid in $(pgrep -f "python.*test_" 2>/dev/null); do
            local mem=$(get_memory_usage_gb "$pid")
            local comparison=$(echo "$mem > $SINGLE_PROCESS_LIMIT_GB" | bc -l 2>/dev/null)
            if [ "$comparison" = "1" ]; then
                local cmd=$(ps -p "$pid" -o args= 2>/dev/null | head -c 60)
                echo -e "${RED}[ERROR]${NC} 🚨 Process PID:$pid memory exceeds limit: ${mem}GB > ${SINGLE_PROCESS_LIMIT_GB}GB" >&3
                echo -e "${RED}[ERROR]${NC} 💀 Terminating process: $cmd" >&3
                kill -TERM "$pid" 2>/dev/null || true
                sleep 1
                kill -KILL "$pid" 2>/dev/null || true
            fi
        done

        log_counter=$((log_counter + 1))
        sleep $MONITOR_INTERVAL
    done

    # Restore stdout
    exec 1>&3
    exec 3>&- 2>/dev/null || true
}

# Helper functions
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

print_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
}

# Claude settings validation function
validate_claude_settings() {
    local claude_settings="$PROJECT_ROOT/.claude/settings.json"

    print_status "🔒 Running critical Claude settings validation..."

    if [ ! -f "$claude_settings" ]; then
        print_error "❌ .claude/settings.json not found"
        return 1
    fi

    # Basic JSON validation and key checks using Python
    if ! python3 -c "
import json, sys
try:
    with open('$claude_settings', 'r') as f:
        data = json.load(f)
    # Check for critical keys - these must exist for Claude Code to work
    required_keys = ['mcpServers']
    for key in required_keys:
        if key not in data:
            print(f'Missing required key: {key}')
            sys.exit(1)
    # Validate MCP servers structure
    if not isinstance(data.get('mcpServers', {}), dict):
        print('mcpServers must be a dictionary')
        sys.exit(1)
    print('✅ Claude settings.json validation passed')
except json.JSONDecodeError as e:
    print(f'Invalid JSON in settings.json: {e}')
    sys.exit(1)
except Exception as e:
    print(f'Settings validation error: {e}')
    sys.exit(1)
" 2>/dev/null; then
        print_pass "✅ Claude settings.json validation passed"
        return 0
    else
        print_fail "❌ Claude settings.json validation failed"
        return 1
    fi
}

# Intelligent test selection based on git changes
intelligent_test_selection() {
    print_status "🔍 Analyzing git changes for intelligent test selection..."

    # Create temporary file for selected tests
    local selected_tests_file="/tmp/selected_tests.txt"
    > "$selected_tests_file"  # Clear the file

    # Check if we're in a git repository and have origin/main
    if ! git rev-parse --git-dir >/dev/null 2>&1; then
        print_warning "Not in a git repository, falling back to full test suite"
        return 1
    fi

    if ! git rev-parse origin/main >/dev/null 2>&1; then
        print_warning "origin/main not found, falling back to full test suite"
        return 1
    fi

    # Get list of changed files
    local changed_files
    changed_files=$(git diff --name-only origin/main..HEAD 2>/dev/null) || {
        print_warning "Failed to get git diff, falling back to full test suite"
        return 1
    }

    if [ -z "$changed_files" ]; then
        print_warning "No changes detected vs origin/main, running minimal test set"
        # For no changes, run a minimal set of core tests
        find mvp_site -name "test_core_*.py" -o -name "test_basic_*.py" 2>/dev/null | head -5 > "$selected_tests_file"
        if [ ! -s "$selected_tests_file" ]; then
            # Fallback: select first few test files
            find mvp_site -name "test_*.py" 2>/dev/null | head -3 > "$selected_tests_file"
        fi
    else
        # Analyze changed files and select relevant tests
        local test_patterns=()

        # Process each changed file
        while IFS= read -r file; do
            if [ -z "$file" ]; then continue; fi

            # Skip certain file types that don't affect tests
            case "$file" in
                *.md|*.txt|*.yml|*.yaml|*.json|*.gitignore|*.dockerignore)
                    continue ;;
            esac

            # Extract base name without extension for test pattern matching
            local base_name=$(basename "$file" | sed 's/\.[^.]*$//')
            local dir_name=$(dirname "$file")

            # Add patterns for test file discovery
            test_patterns+=("test_${base_name}.py")
            test_patterns+=("test_*${base_name}*.py")

            # If it's a Python file, also look for tests in the same directory
            if [[ "$file" == *.py ]]; then
                # Add directory-specific test patterns
                test_patterns+=("${dir_name}/test_*.py")

                # Special handling for common directories
                case "$dir_name" in
                    mvp_site/*)
                        test_patterns+=("mvp_site/test_*.py")
                        test_patterns+=("mvp_site/tests/test_*.py")
                        ;;
                    *api*)
                        test_patterns+=("**/test_api*.py")
                        test_patterns+=("**/test_*api*.py")
                        ;;
                    *auth*)
                        test_patterns+=("**/test_auth*.py")
                        test_patterns+=("**/test_*auth*.py")
                        ;;
                esac
            fi
        done <<< "$changed_files"

        # Find matching test files
        local found_count=0
        for pattern in "${test_patterns[@]}"; do
            # Use find with the pattern, suppressing errors
            find "$PROJECT_ROOT" -name "$pattern" -type f 2>/dev/null | while read -r test_file; do
                # Skip if file doesn't exist or is not readable
                if [ -f "$test_file" ] && [ -r "$test_file" ]; then
                    echo "$test_file"
                    found_count=$((found_count + 1))
                fi
            done
        done | sort -u >> "$selected_tests_file"

        # Always include core critical tests
        find mvp_site -name "test_core*.py" -o -name "test_basic*.py" -o -name "test_critical*.py" 2>/dev/null >> "$selected_tests_file"

        # Remove duplicates and empty lines
        sort -u "$selected_tests_file" | grep -v '^$' > "${selected_tests_file}.tmp" && mv "${selected_tests_file}.tmp" "$selected_tests_file"
    fi

    # Check if we found any tests
    local test_count=$(wc -l < "$selected_tests_file" 2>/dev/null || echo "0")
    echo "Selected $test_count tests written to $selected_tests_file"

    if [ "$test_count" -eq 0 ]; then
        print_warning "⚠️  Intelligent analysis produced no results, falling back to full suite"
        return 1
    elif [ "$test_count" -gt 50 ]; then
        print_warning "⚠️  Large changeset detected ($test_count tests selected), consider using --full"
        # Still use intelligent selection but warn about potential long runtime
        return 0
    else
        print_success "✅ Intelligent selection found $test_count relevant tests"
        return 0
    fi
}

# Parse command line arguments
include_integration=false
mcp_tests=false
enable_coverage=false
intelligent_mode=true
dry_run_mode=false
specific_test_files=()

for arg in "$@"; do
    case $arg in
        --integration)
            include_integration=true
            ;;
        --unit)
            # Unit tests mode - exclude integration tests (this is the default behavior)
            include_integration=false
            ;;
        --parallel)
            # Parallel mode - this is already the default, included for compatibility
            # Does nothing since parallel execution is the default behavior
            ;;
        --mcp)
            mcp_tests=true
            ;;
        --coverage)
            enable_coverage=true
            ;;
        --full|--all-tests|--no-intelligent)
            intelligent_mode=false
            ;;
        --dry-run)
            dry_run_mode=true
            # Don't force intelligent mode - let user override with --full
            ;;
        *)
            if [[ $arg == --* ]]; then
                print_warning "Unknown argument: $arg"
            elif [[ $arg == *.py ]]; then
                # Handle specific test files (individual or multiple)
                specific_test_files+=("$arg")
                intelligent_mode=false  # Disable intelligent mode when running specific files
            fi
            ;;
    esac
done

# Display mode information
if [ ${#specific_test_files[@]} -gt 0 ]; then
    print_status "🎯 Specific Test Mode: Running ${#specific_test_files[@]} specified test file(s)"
    for test_file in "${specific_test_files[@]}"; do
        print_status "  - $test_file"
    done
elif [ "$intelligent_mode" = true ]; then
    if [ "$dry_run_mode" = true ]; then
        print_status "🧠 Intelligent Test Selection Mode (DRY RUN - no tests executed)"
    else
        print_status "🧠 Intelligent Test Selection Mode (use --full for complete suite)"
    fi
else
    print_status "🔧 Full Test Suite Mode (all tests will be executed)"
fi

if [ "$include_integration" = true ]; then
    print_status "Integration tests enabled (--integration flag specified)"
else
    print_status "Skipping integration tests (use --integration to include them)"
fi

# Validate Claude settings before running tests
if ! validate_claude_settings; then
    print_error "Claude settings validation failed, stopping test execution"
    exit 1
fi

# Change to project root for consistent test discovery
cd "$PROJECT_ROOT"
print_status "Running tests from project root for complete discovery..."

# Set environment variables for testing
if [ -z "$TESTING" ]; then
    export TESTING=true
    print_status "Setting TESTING=true for faster AI model usage"
fi

# Set test mode to mock by default for CI compatibility
if [ -z "$TEST_MODE" ]; then
    export TEST_MODE=mock
fi
print_status "TEST_MODE=$TEST_MODE (Real-Mode Testing Framework)"

# CI simulation - always enabled for consistency
if [ "$GITHUB_ACTIONS" != "true" ]; then
    print_status "🔧 CI Simulation Mode: Simulating GitHub Actions environment"
    export CI=true
    export GITHUB_ACTIONS=true
    export MOCK_SERVICES_MODE=true
fi
print_success "✅ CI simulation environment configured (matches GitHub Actions)"

# Determine test files to run based on mode
test_files=()

if [ ${#specific_test_files[@]} -gt 0 ]; then
    # User specified exact files - use them directly
    for test_file in "${specific_test_files[@]}"; do
        if [ -f "$test_file" ]; then
            test_files+=("$test_file")
        else
            print_warning "⚠️  Test file not found: $test_file"
        fi
    done
elif [ "$intelligent_mode" = true ] && [ "$mcp_tests" != true ]; then
    # Try intelligent test selection first
    if intelligent_test_selection; then
        # Read selected test files
        while IFS= read -r test_file; do
            if [ -n "$test_file" ] && [ -f "$test_file" ]; then
                test_files+=("$test_file")
            fi
        done < /tmp/selected_tests.txt

        # Double-check we have valid files
        if [ ${#test_files[@]} -eq 0 ]; then
            print_warning "⚠️  No valid test files from intelligent selection, falling back to full suite"
            intelligent_mode=false
        fi
    else
        # Intelligent selection failed, fall back to full suite
        intelligent_mode=false
    fi
fi

# If not using specific files or intelligent mode failed, do full discovery
if [ ${#test_files[@]} -eq 0 ]; then
    if [ "$enable_coverage" = true ]; then
        print_warning "Coverage mode: Running tests SEQUENTIALLY (not parallel) for accurate tracking"
    else
        print_status "Running tests in parallel mode (use --coverage for coverage analysis)"
    fi

    print_status "🔍 Discovering all test files (traditional mode)"

    # Standard test discovery - find all test_*.py files
    test_files=($(find mvp_site -name "test_*.py" -type f 2>/dev/null | sort))

    # Add .claude/commands tests if directory exists
    if [ -d ".claude/commands/tests" ]; then
        print_status "Including .claude/commands tests..."
        while IFS= read -r -d '' test_file; do
            test_files+=("$test_file")
        done < <(find .claude/commands -name "test_*.py" -type f -print0 2>/dev/null)
    fi

    # Add orchestration tests if directory exists
    if [ -d "orchestration/tests" ]; then
        print_status "Including orchestration tests..."
        while IFS= read -r -d '' test_file; do
            test_files+=("$test_file")
        done < <(find orchestration -name "test_*.py" -type f -print0 2>/dev/null)
    fi

    # Add claude_command_scripts tests if directory exists
    if [ -d "claude_command_scripts/tests" ]; then
        print_status "Including claude_command_scripts tests..."
        while IFS= read -r -d '' test_file; do
            test_files+=("$test_file")
        done < <(find claude_command_scripts -name "test_*.py" -type f -print0 2>/dev/null)
    fi

    # Add claude-bot-commands tests if directory exists
    if [ -d "claude-bot-commands/tests" ]; then
        print_status "Including claude-bot-commands tests..."
        while IFS= read -r -d '' test_file; do
            test_files+=("$test_file")
        done < <(find claude-bot-commands -name "test_*.py" -type f -print0 2>/dev/null)
    fi

    # Add .claude/hooks tests if they exist
    if [ -d ".claude/hooks" ]; then
        print_status "Including .claude/hooks tests..."
        while IFS= read -r -d '' test_file; do
            test_files+=("$test_file")
        done < <(find .claude/hooks -name "test_*.py" -type f -print0 2>/dev/null)
    fi

    # Add direct .claude/commands test files (not in subdirectories)
    if [ -d ".claude/commands" ]; then
        print_status "Including .claude/commands direct test files..."
        while IFS= read -r -d '' test_file; do
            test_files+=("$test_file")
        done < <(find .claude/commands -maxdepth 1 -name "test_*.py" -type f -print0 2>/dev/null)
    fi

    # Add scripts/tests if directory exists
    if [ -d "scripts/tests" ]; then
        print_status "Including scripts/tests..."
        while IFS= read -r -d '' test_file; do
            test_files+=("$test_file")
        done < <(find scripts/tests -name "test_*.py" -type f -print0 2>/dev/null)
    fi

    # Discover cerebras command tests
    print_status "🚀 Discovering cerebras command tests..."
    if [ -d ".claude/commands/cerebras/tests" ]; then
        while IFS= read -r -d '' test_file; do
            echo "  - Found: $test_file"
            test_files+=("$test_file")
        done < <(find .claude/commands/cerebras/tests -name "test_*.py" -type f -print0 2>/dev/null)
    fi
fi

# Filter out integration tests if not requested
if [ "$include_integration" != true ]; then
    filtered_files=()
    for test_file in "${test_files[@]}"; do
        # Skip integration test directories and files
        if [[ "$test_file" == *test_integration* ]] || [[ "$test_file" == *integration_test* ]]; then
            continue
        fi
        filtered_files+=("$test_file")
    done
    test_files=("${filtered_files[@]}")
fi

# Add MCP server tests if requested
if [ "$mcp_tests" = true ]; then
    print_status "🔌 Including MCP server tests..."
    while IFS= read -r -d '' test_file; do
        test_files+=("$test_file")
    done < <(find . -path "*/mcp*" -name "test_*.py" -type f -print0 2>/dev/null)
fi

# Remove duplicates and sort
# Use temp file approach that works on all bash versions (including 3.2+)
if [ ${#test_files[@]} -gt 0 ]; then
    # Use a temp file approach that works on GNU/BSD mktemp and falls back safely
    temp_file="$(mktemp -p "${TMPDIR:-/tmp}" worldarchitect_tests.XXXXXX 2>/dev/null \
        || mktemp -t worldarchitect_tests.XXXXXX 2>/dev/null \
        || mktemp 2>/dev/null \
        )" || { echo "❌ ERROR: Failed to create secure temporary file" >&2; exit 1; }

    # Add trap to ensure cleanup even on unexpected exit
    trap 'rm -f "$temp_file"' EXIT

    printf '%s\n' "${test_files[@]}" | LC_ALL=C sort -u > "$temp_file"
    test_files=()
    while IFS= read -r file; do
        if [ -n "$file" ]; then
            test_files+=("$file")
        fi
    done < "$temp_file"
    rm -f "$temp_file"
fi
print_status "📊 Found ${#test_files[@]} test files to execute"

# Display first few test files as preview
if [ ${#test_files[@]} -gt 0 ]; then
    print_status "📋 Test files preview (first 10):"
    for i in $(seq 0 $((${#test_files[@]} - 1 > 9 ? 9 : ${#test_files[@]} - 1))); do
        echo "  ${test_files[$i]}"
    done
    if [ ${#test_files[@]} -gt 10 ]; then
        echo "  ... and $((${#test_files[@]} - 10)) more files"
    fi
fi

# Exit early if dry run mode
if [ "$dry_run_mode" = true ]; then
    print_success "🏁 Dry run complete - no tests were executed"
    exit 0
fi

# Validate we have test files to run
if [ ${#test_files[@]} -eq 0 ]; then
    print_error "❌ No test files found to execute"
    exit 1
fi

# Run Claude Code hooks tests first
print_status "🪝 Running Claude Code hooks tests..."
if [ -d ".claude/hooks" ]; then
    hook_test_script=".claude/hooks/test_hooks.sh"
    if [ -f "$hook_test_script" ] && [ -x "$hook_test_script" ]; then
        echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
        echo -e "${BLUE}║     Claude Code Hooks Test Suite          ║${NC}"
        echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
        echo

        if ! "$hook_test_script"; then
            print_fail "Hook tests failed"
        else
            print_success "Hook tests passed"
        fi
    else
        print_status "Hook test script not found or not executable, skipping..."
    fi
else
    print_status "No .claude/hooks directory found, skipping hook tests..."
fi

# Run backup script tests
print_status "💾 Running backup script tests..."
backup_test_script="scripts/tests/test_claude_backup.sh"
if [ -f "$backup_test_script" ] && [ -x "$backup_test_script" ]; then
    if ! "$backup_test_script"; then
        print_fail "Backup script tests failed"
    else
        print_success "Backup script tests passed"
    fi
else
    print_status "Backup test script not found or not executable at $backup_test_script, skipping..."
fi

# Coverage mode setup
if [ "$enable_coverage" = true ]; then
    print_status "🔍 Setting up coverage analysis..."

    # Create coverage directory
    coverage_dir="/tmp/worldarchitectai/coverage"
    mkdir -p "$coverage_dir"

    # Install coverage if not already installed
    if ! python3 -c "import coverage" 2>/dev/null; then
        print_status "Installing coverage package..."
        python3 -m pip install coverage
    fi

    # Set coverage configuration
    export COVERAGE_FILE="$coverage_dir/.coverage"

    print_status "📊 Coverage reports will be saved to: $coverage_dir"
fi

# Create temporary directory for parallel execution
tmp_dir=$(mktemp -d)
trap "rm -rf $tmp_dir" EXIT

# Create memory monitor file
monitor_file="$tmp_dir/memory_monitor.lock"
touch "$monitor_file"

# Start background memory monitoring
memory_monitor "$monitor_file" &
monitor_pid=$!

# Function to cleanup background processes
cleanup() {
    # Stop memory monitoring
    if [ -f "$monitor_file" ]; then
        rm -f "$monitor_file"
    fi
    if [ -n "$monitor_pid" ] && kill -0 "$monitor_pid" 2>/dev/null; then
        kill "$monitor_pid" 2>/dev/null || true
        wait "$monitor_pid" 2>/dev/null || true
    fi

    # Clean up any remaining test processes
    pgrep -f "python.*test_" | xargs -r kill -TERM 2>/dev/null || true
    sleep 1
    pgrep -f "python.*test_" | xargs -r kill -KILL 2>/dev/null || true

    rm -rf "$tmp_dir"
}
trap cleanup EXIT INT TERM

# Determine number of parallel workers based on environment
if [ "$enable_coverage" = true ]; then
    max_workers=1
    print_warning "Coverage mode: Running tests SEQUENTIALLY for accurate coverage tracking"
elif [ "$GITHUB_ACTIONS" = "true" ]; then
    # GitHub Actions runners have 2 cores
    max_workers=2
    print_status "Running tests in parallel (GitHub Actions: $max_workers workers - matching runner cores)..."
elif [ -n "$CI" ]; then
    # CI replica - high parallelism for CI testing locally
    max_workers=4
    print_status "Running tests in parallel (CI replica: $max_workers workers - full CPU with memory monitoring)..."
else
    # Local development - conservative parallelism to avoid overwhelming system
    available_cores=$(nproc 2>/dev/null || echo "4")
    max_workers=$((available_cores > 4 ? 4 : available_cores))
    print_status "Running tests in parallel (Local dev: $max_workers workers for memory safety)..."
fi

# Initialize result tracking
total_tests=${#test_files[@]}
passed_tests=0
failed_tests=0
skipped_tests=0
failed_test_files=()

print_status "🚀 Starting test execution: $total_tests files, $max_workers workers"
print_status "📊 Memory monitoring active: ${MEMORY_LIMIT_GB}GB total limit, ${SINGLE_PROCESS_LIMIT_GB}GB per process"

# Function to run a single test file
run_single_test() {
    local test_file="$1"
    local result_file="$tmp_dir/$(basename "$test_file").result"
    local start_time=$(date +%s)

    {
        echo "TESTFILE: $test_file"
        echo "START: $(date '+%Y-%m-%d %H:%M:%S')"

        if [ "$enable_coverage" = true ]; then
            # Run with coverage
            if timeout 300 python3 -m coverage run --append --source=mvp_site "$test_file" 2>&1; then
                echo "RESULT: PASS"
            else
                echo "RESULT: FAIL"
            fi
        else
            # Run normally
            if timeout 300 python3 "$test_file" 2>&1; then
                echo "RESULT: PASS"
            else
                echo "RESULT: FAIL"
            fi
        fi

        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        echo "DURATION: ${duration}s"
        echo "END: $(date '+%Y-%m-%d %H:%M:%S')"
    } > "$result_file"
}

# Export the function for use with xargs
export -f run_single_test
export tmp_dir enable_coverage

# Run tests in parallel using xargs
if [ $max_workers -eq 1 ]; then
    # Sequential execution
    for test_file in "${test_files[@]}"; do
        run_single_test "$test_file"
    done
else
    # Parallel execution
    printf '%s\n' "${test_files[@]}" | xargs -P "$max_workers" -I {} bash -c 'run_single_test "$@"' _ {}
fi

# Wait for all background jobs to complete
wait

# Stop memory monitoring
rm -f "$monitor_file"
if [ -n "$monitor_pid" ] && kill -0 "$monitor_pid" 2>/dev/null; then
    kill "$monitor_pid" 2>/dev/null || true
    wait "$monitor_pid" 2>/dev/null || true
fi

print_status "📊 Processing test results..."

# Process results from all test files
for test_file in "${test_files[@]}"; do
    result_file="$tmp_dir/$(basename "$test_file").result"

    if [ -f "$result_file" ]; then
        result=$(grep "^RESULT:" "$result_file" | cut -d' ' -f2)
        duration=$(grep "^DURATION:" "$result_file" | cut -d' ' -f2 || echo "?s")

        case "$result" in
            "PASS")
                passed_tests=$((passed_tests + 1))
                echo -e "  ${GREEN}✓${NC} $(basename "$test_file") (${duration})"
                ;;
            "FAIL")
                failed_tests=$((failed_tests + 1))
                failed_test_files+=("$test_file")
                echo -e "  ${RED}✗${NC} $(basename "$test_file") (${duration})"

                # Show failure details
                echo -e "    ${RED}Error details:${NC}"
                grep -v "^\(TESTFILE:\|START:\|RESULT:\|DURATION:\|END:\)" "$result_file" | head -10 | sed 's/^/      /'
                ;;
            *)
                skipped_tests=$((skipped_tests + 1))
                echo -e "  ${YELLOW}?${NC} $(basename "$test_file") (${duration}) - Unknown result"
                ;;
        esac
    else
        skipped_tests=$((skipped_tests + 1))
        echo -e "  ${YELLOW}?${NC} $(basename "$test_file") - No result file"
        failed_test_files+=("$test_file")
    fi
done

# Generate coverage report if enabled
if [ "$enable_coverage" = true ]; then
    print_status "📊 Generating coverage report..."

    cd "$PROJECT_ROOT"
    python3 -m coverage combine 2>/dev/null || true
    python3 -m coverage html -d "$coverage_dir" 2>/dev/null || print_warning "Failed to generate HTML coverage report"
    python3 -m coverage report --show-missing || print_warning "Failed to generate coverage summary"

    print_status "📊 Coverage HTML report: $coverage_dir/index.html"
fi

# Print final summary
echo
echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              Test Summary                 ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo
echo -e "Total tests run: ${BLUE}$total_tests${NC}"
echo -e "Passed: ${GREEN}$passed_tests${NC}"
echo -e "Failed: ${RED}$failed_tests${NC}"
if [ $skipped_tests -gt 0 ]; then
    echo -e "Skipped/Unknown: ${YELLOW}$skipped_tests${NC}"
fi
echo

# Show failed tests if any
if [ $failed_tests -gt 0 ]; then
    echo -e "${RED}Failed tests:${NC}"
    for failed_test in "${failed_test_files[@]}"; do
        echo -e "  ${RED}• $(basename "$failed_test")${NC}"
    done
    echo
fi

# Calculate success rate
if [ $total_tests -gt 0 ]; then
    success_rate=$(echo "scale=1; $passed_tests * 100 / $total_tests" | bc -l 2>/dev/null || echo "0")
    echo -e "Success rate: ${success_rate}%"
    echo
fi

# Exit with appropriate code
if [ $failed_tests -eq 0 ]; then
    print_success "🎉 All tests passed!"
    exit 0
else
    print_error "❌ $failed_tests test(s) failed"
    exit 1
fi
