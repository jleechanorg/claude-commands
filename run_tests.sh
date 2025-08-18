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
#   ./run_tests.sh --coverage                # Run tests with coverage analysis
#   ./run_tests.sh --integration --coverage  # Run unit and integration tests with coverage
#   ./run_tests.sh --full --integration      # Full suite including integration tests
#   ./run_tests.sh --dry-run --integration   # Preview intelligent selection with integration tests
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
            local python_pids=$(pgrep -f "python.*test_" 2>/dev/null || true)
            if [ -n "$python_pids" ]; then
                echo "$python_pids" | while read pid; do
                    if [ -n "$pid" ]; then
                        local proc_memory=$(get_memory_usage_gb "$pid")
                        local cmd=$(ps -p "$pid" -o cmd= 2>/dev/null | cut -c1-80 || echo "unknown")
                        echo -e "${BLUE}[INFO]${NC}   📊 PID $pid: ${proc_memory}GB - $cmd" >&3
                    fi
                done
            else
                echo -e "${BLUE}[INFO]${NC}   📊 No Python test processes running" >&3
            fi
        fi
        
        if [ "$comparison" = "1" ]; then
            echo -e "${RED}[FAIL]${NC} 🚨 MEMORY LIMIT EXCEEDED: ${total_memory}GB > ${MEMORY_LIMIT_GB}GB" >&3
            pkill -f "python.*test_" || true
            echo "MEMORY_KILL" > "$monitor_file.kill"
            break
        fi
        
        # Check individual process limits
        pgrep -f "python.*test_" 2>/dev/null | while read pid; do
            if [ -n "$pid" ]; then
                local proc_memory=$(get_memory_usage_gb "$pid")
                local proc_comparison=$(echo "$proc_memory > $SINGLE_PROCESS_LIMIT_GB" | bc -l 2>/dev/null)
                
                if [ "$proc_comparison" = "1" ]; then
                    echo -e "${RED}[FAIL]${NC} 🚨 KILLING RUNAWAY PROCESS: PID $pid using ${proc_memory}GB > ${SINGLE_PROCESS_LIMIT_GB}GB" >&3
                    kill -9 "$pid" 2>/dev/null || true
                fi
            fi
        done
        
        log_counter=$((log_counter + 1))
        sleep "$MONITOR_INTERVAL"
    done
    
    # Restore stdout
    exec 1>&3
}

simple_memory_monitor() {
    local memory_limit_gb=${1:-5}  # Default to 5GB if no parameter provided
    
    while true; do
        sleep 10
        
        # Get total memory used by Python test processes in MB
        local total_mb=$(pgrep -f "python.*test_" | xargs -r ps -o rss= -p 2>/dev/null | awk '{sum+=$1} END {print sum+0}')
        local total_gb=$((total_mb / 1024))
        
        if [ $total_gb -gt $memory_limit_gb ]; then
            print_error "🚨 MEMORY LIMIT EXCEEDED: ${total_gb}GB > ${memory_limit_gb}GB - killing Python test processes"
            pkill -f "python.*test_"
            break
        fi
        
        # Log every 30 seconds (every 3 iterations)
        if [ $(($(date +%s) % 30)) -lt 10 ]; then
            print_status "📊 Memory usage: ${total_gb}GB (limit: ${memory_limit_gb}GB)"
        fi
    done
}

# Function to print colored output
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

# Check if we're in the right directory
if [ ! -d "mvp_site" ]; then
    print_error "mvp_site directory not found. Please run this script from the project root."
    exit 1
fi

# Stay at project root for proper test discovery
# Activate virtual environment
print_status "Activating virtual environment..."
# Venv already activated by ensure_venv above

pip install -r mvp_site/requirements.txt

print_status "Running tests from project root for complete discovery..."
print_status "Setting TESTING=true for faster AI model usage"
print_status "TEST_MODE=${TEST_MODE:-mock} (Real-Mode Testing Framework)"

# CI Simulation Logic - Always enabled to catch environment-specific issues
print_status "🔧 CI Simulation Mode: Simulating GitHub Actions environment"

# Set CI environment variables to match GitHub Actions exactly
export CI=true
# NOTE: GITHUB_ACTIONS export removed to prevent CI simulation issues
# export GITHUB_ACTIONS=true
export TESTING=true
export MOCK_SERVICES_MODE=true

# Simulate GitHub Actions runner environment
export RUNNER_OS="Linux"
export RUNNER_ARCH="X64"

print_status "✅ CI simulation environment configured (matches GitHub Actions)"

# Parse command line arguments
include_integration=false
enable_coverage=false
coverage_dir="/tmp/worldarchitectai/coverage"
intelligent_mode=true
dry_run_mode=false
specific_test_files=()

for arg in "$@"; do
    case $arg in
        --integration)
            include_integration=true
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

# Test selection logic
selected_test_files=()
use_intelligent_selection=false

# Handle specific test files first
if [ ${#specific_test_files[@]} -gt 0 ]; then
    # Use specific test files provided by user
    selected_test_files=("${specific_test_files[@]}")
    print_status "✅ Using ${#selected_test_files[@]} specified test file(s)"
elif [ "$intelligent_mode" = true ]; then
    print_status "🔍 Analyzing git changes for intelligent test selection..."
    
    # Check if dependency analyzer exists
    analyzer_script="$PROJECT_ROOT/scripts/test_dependency_analyzer.py"
    if [ -f "$analyzer_script" ]; then
        # Run the dependency analyzer
        analysis_output_file="/tmp/selected_tests.txt"
        
        # Note: The analyzer includes always-run tests and handles integration logic internally
        # based on the configuration, so we don't need to pass integration flag separately
        if python3 "$analyzer_script" --git-diff --output "$analysis_output_file" 2>/dev/null; then
            if [ -f "$analysis_output_file" ] && [ -s "$analysis_output_file" ]; then
                # Successfully got test selection
                mapfile -t selected_test_files < "$analysis_output_file"
                use_intelligent_selection=true
                
                # Count total tests for comparison
                total_possible_tests=$(find ./mvp_site/tests -name "test_*.py" -type f | wc -l)
                selected_count=${#selected_test_files[@]}
                
                if [ $total_possible_tests -gt 0 ]; then
                    reduction_pct=$(echo "scale=0; (($total_possible_tests - $selected_count) * 100) / $total_possible_tests" | bc -l 2>/dev/null || echo "0")
                    time_savings_min=$(echo "scale=0; $reduction_pct * 15 / 100" | bc -l 2>/dev/null || echo "0")
                    
                    print_status "📊 Running $selected_count selected tests (${reduction_pct}% reduction, ~$((total_possible_tests - selected_count)) tests skipped)"
                    if [ $time_savings_min -gt 0 ]; then
                        print_status "⚡ Estimated time savings: ~${time_savings_min} minutes"
                    fi
                else
                    print_status "📊 Running $selected_count selected tests"
                fi
                
                # Show changed files that triggered selection
                changed_files=$(cd "$PROJECT_ROOT" && git diff --name-only origin/main...HEAD 2>/dev/null | head -5)
                if [ -n "$changed_files" ]; then
                    changed_files_display=$(echo "$changed_files" | tr '\n' ', ' | sed 's/, $//')
                    print_status "📁 Changes detected: $changed_files_display"
                fi
            else
                print_warning "⚠️  Intelligent analysis produced no results, falling back to full suite"
                use_intelligent_selection=false
            fi
        else
            print_warning "⚠️  Intelligent analysis failed, falling back to full suite"
            use_intelligent_selection=false
        fi
    else
        print_warning "⚠️  Dependency analyzer not found at $analyzer_script, falling back to full suite"
        use_intelligent_selection=false
    fi
    
    # Handle dry run mode
    if [ "$dry_run_mode" = true ]; then
        if [ "$use_intelligent_selection" = true ]; then
            echo
            print_status "📋 Intelligent selection would run these ${#selected_test_files[@]} tests:"
            for test_file in "${selected_test_files[@]}"; do
                if [ -n "$test_file" ]; then
                    echo "  - $test_file"
                fi
            done
        else
            echo
            print_status "📋 Would run full test suite (intelligent selection unavailable)"
        fi
        echo
        print_status "🏁 Dry run complete - no tests executed"
        exit 0
    fi
fi

if [ "$enable_coverage" = true ]; then
    print_status "🧪 Coverage analysis enabled (--coverage flag specified)"
    print_status "HTML output will be saved to: $coverage_dir"

    # Create coverage output directory
    mkdir -p "$coverage_dir"

    # Check if coverage is installed
    print_status "Checking coverage installation..."

    # Check if coverage is importable (venv already activated)
    if ! python -c "import coverage" 2>/dev/null; then
        print_warning "Coverage tool not found. Installing..."
        if ! pip install coverage; then
            print_error "Failed to install coverage"
            exit 1
        fi
        print_success "Coverage installed successfully"
    else
        print_status "Coverage already installed"
    fi

    # Clear any previous coverage data
    coverage erase

    print_warning "Coverage mode: Running tests SEQUENTIALLY (not parallel) for accurate tracking"
else
    print_status "Running tests in parallel mode (use --coverage for coverage analysis)"
fi

# Find test files - handle individual test file, intelligent selection, or discovery
test_files=()

# Check if specific test files were specified
if [ ${#specific_test_files[@]} -gt 0 ]; then
    # Validate and add specific test files
    for test_file in "${specific_test_files[@]}"; do
        if [ -f "$test_file" ]; then
            test_files+=("$test_file")
        else
            print_error "Test file not found: $test_file"
            exit 1
        fi
    done
    print_status "🎯 Running ${#test_files[@]} specified test file(s) in serial mode"
elif [ "$use_intelligent_selection" = true ] && [ ${#selected_test_files[@]} -gt 0 ]; then
    # Use intelligently selected tests
    print_status "🎯 Using intelligent test selection results"
    
    # Convert selected test paths to full paths and validate they exist
    for selected_test in "${selected_test_files[@]}"; do
        if [ -n "$selected_test" ]; then
            # Remove leading ./ if present
            clean_path="${selected_test#./}"
            
            # Check if file exists
            if [ -f "./$clean_path" ]; then
                test_files+=("./$clean_path")
            else
                print_warning "Selected test file not found: $clean_path"
            fi
        fi
    done
    
    # Ensure we still respect integration flag for always-run tests
    if [ "$include_integration" = true ]; then
        # Add integration tests that might not be in intelligent selection
        if [ -d "./mvp_site/test_integration" ]; then
            while IFS= read -r -d '' file; do
                # Normalize path format for consistent duplicate detection
                file_normalized="${file#./}"  # Remove ./ prefix
                
                # Check against normalized test_files array (also remove ./ prefix for comparison)
                is_duplicate=false
                for existing_test in "${test_files[@]}"; do
                    existing_normalized="${existing_test#./}"
                    if [ "$file_normalized" = "$existing_normalized" ]; then
                        is_duplicate=true
                        break
                    fi
                done
                
                # Only add if not already included
                if [ "$is_duplicate" = false ]; then
                    test_files+=("$file")
                fi
            done < <(find ./mvp_site/test_integration -name "test_*.py" -type f -print0 2>/dev/null)
        fi
    fi
else
    # Fall back to traditional test discovery
    # Check if intelligent test selection is available
    if [ -n "${INTELLIGENT_TEST_SELECTION:-}" ] && [ -f "${INTELLIGENT_TEST_SELECTION}" ]; then
        print_status "🧠 Using intelligent test selection results"
        while IFS= read -r file; do
            if [ -f "$file" ]; then
                test_files+=("$file")
            fi
        done < "${INTELLIGENT_TEST_SELECTION}"
    else
        print_status "🔍 Discovering all test files (traditional mode)"
        
        # Main mvp_site tests
        while IFS= read -r -d '' file; do
            test_files+=("$file")
        done < <(find ./mvp_site/tests -name "test_*.py" -type f \
            ! -path "./venv/*" \
            ! -path "./node_modules/*" \
            ! -path "./prototype/*" \
            ! -path "./mvp_site/tests/manual_tests/*" \
            ! -path "./mvp_site/tests/test_integration/*" \
            -print0 2>/dev/null)

        # Project root tests directory
        if [ -d "./tests" ]; then
            while IFS= read -r -d '' file; do
                test_files+=("$file")
            done < <(find ./tests -name "test_*.py" -type f \
                ! -path "./prototype/*" \
                ! -path "./tests/manual_tests/*" \
                ! -path "./tests/test_integration/*" \
                -print0 2>/dev/null)
        fi
    fi

    # Always include test_integration_mock.py from mvp_site/test_integration directory (fast mock tests)
    if [ -f "./mvp_site/test_integration/test_integration_mock.py" ]; then
        test_files+=("./mvp_site/test_integration/test_integration_mock.py")
    fi

    # Also include test_integration directories if not in GitHub export mode
    if [ "$include_integration" = true ]; then
        # Check for test_integration in mvp_site, project root, and tests/ directory
        if [ -d "./mvp_site/test_integration" ]; then
            print_status "Including integration tests from mvp_site/test_integration/"
            while IFS= read -r -d '' file; do
                # Normalize path format for consistent duplicate detection
                file_normalized="${file#./}"
                
                # Check against normalized test_files array
                is_duplicate=false
                for existing_test in "${test_files[@]}"; do
                    existing_normalized="${existing_test#./}"
                    if [ "$file_normalized" = "$existing_normalized" ]; then
                        is_duplicate=true
                        break
                    fi
                done
                
                # Only add if not already included
                if [ "$is_duplicate" = false ]; then
                    test_files+=("$file")
                fi
            done < <(find ./mvp_site/test_integration -name "test_*.py" -type f -print0 2>/dev/null)
        fi
        
        if [ -d "./test_integration" ]; then
            print_status "Including integration tests from test_integration/"
            while IFS= read -r -d '' file; do
                # Normalize path format for consistent duplicate detection
                file_normalized="${file#./}"
                
                # Check against normalized test_files array
                is_duplicate=false
                for existing_test in "${test_files[@]}"; do
                    existing_normalized="${existing_test#./}"
                    if [ "$file_normalized" = "$existing_normalized" ]; then
                        is_duplicate=true
                        break
                    fi
                done
                
                # Only add if not already included
                if [ "$is_duplicate" = false ]; then
                    test_files+=("$file")
                fi
            done < <(find ./test_integration -name "test_*.py" -type f -print0 2>/dev/null)
        fi

        if [ -d "./tests/test_integration" ]; then
            print_status "Including integration tests from tests/test_integration/"
            while IFS= read -r -d '' file; do
                # Normalize path format for consistent duplicate detection
                file_normalized="${file#./}"
                
                # Check against normalized test_files array
                is_duplicate=false
                for existing_test in "${test_files[@]}"; do
                    existing_normalized="${existing_test#./}"
                    if [ "$file_normalized" = "$existing_normalized" ]; then
                        is_duplicate=true
                        break
                    fi
                done
                
                # Only add if not already included
                if [ "$is_duplicate" = false ]; then
                    test_files+=("$file")
                fi
            done < <(find ./tests/test_integration -name "test_*.py" -type f -print0 2>/dev/null)
        fi

        if [ -d "./mvp_site/tests/test_integration" ]; then
            print_status "Including integration tests from mvp_site/tests/test_integration/"
            while IFS= read -r -d '' file; do
                # Normalize path format for consistent duplicate detection
                file_normalized="${file#./}"
                
                # Check against normalized test_files array
                is_duplicate=false
                for existing_test in "${test_files[@]}"; do
                    existing_normalized="${existing_test#./}"
                    if [ "$file_normalized" = "$existing_normalized" ]; then
                        is_duplicate=true
                        break
                    fi
                done
                
                # Only add if not already included
                if [ "$is_duplicate" = false ]; then
                    test_files+=("$file")
                fi
            done < <(find ./mvp_site/tests/test_integration -name "test_*.py" -type f -print0 2>/dev/null)
        fi
    fi

    # Also include .claude/commands tests if they exist
    if [ -d ".claude/commands/tests" ]; then
        print_status "Including .claude/commands tests..."
        while IFS= read -r -d '' file; do
            test_files+=("$file")
        done < <(find .claude/commands/tests -name "test_*.py" -type f -print0)
    fi

    # Also include orchestration tests if they exist
    if [ -d "orchestration/tests" ]; then
        print_status "Including orchestration tests..."
        while IFS= read -r -d '' file; do
            test_files+=("$file")
        done < <(find orchestration/tests -name "test_*.py" -type f -print0)
    fi

    # Also include claude_command_scripts tests if they exist
    if [ -d "claude_command_scripts/commands" ]; then
        print_status "Including claude_command_scripts tests..."
        while IFS= read -r -d '' file; do
            test_files+=("$file")
        done < <(find claude_command_scripts/commands -name "test_*.py" -type f -print0)
    fi

    # Include claude-bot-commands tests if they exist
    if [ -d "claude-bot-commands/tests" ]; then
        print_status "Including claude-bot-commands tests..."
        while IFS= read -r -d '' file; do
            test_files+=("$file")
        done < <(find claude-bot-commands/tests -name "test_*.py" -type f -print0 2>/dev/null)
    fi

    # Include .claude/hooks tests if they exist
    if [ -d ".claude/hooks/tests" ]; then
        print_status "Including .claude/hooks tests..."
        while IFS= read -r -d '' file; do
            test_files+=("$file")
        done < <(find .claude/hooks/tests -name "test_*.py" -type f -print0 2>/dev/null)
    fi

    # Include direct .claude/commands test files (not in tests subdirectory)
    if [ -d ".claude/commands" ]; then
        print_status "Including .claude/commands direct test files..."
        while IFS= read -r -d '' file; do
            test_files+=("$file")
        done < <(find .claude/commands -maxdepth 1 -name "test_*.py" -type f -print0 2>/dev/null)
    fi
fi

# Run qwen command tests if they exist
if [ -d ".claude/commands/qwen" ]; then
    print_status "🚀 Discovering qwen command tests..."
    while IFS= read -r -d $'\0' test_file; do
        test_files+=("$test_file")
        echo "  - Found: $test_file"
    done < <(find .claude/commands/qwen -name "test_*.py" -type f -print0 2>/dev/null)
fi

# Run Claude Code hooks tests if they exist
if [ -x ".claude/hooks/tests/run_all_hook_tests.sh" ]; then
    print_status "🪝 Running Claude Code hooks tests..."
    if .claude/hooks/tests/run_all_hook_tests.sh; then
        print_success "Hook tests passed"
    else
        print_error "Hook tests failed"
        failed_tests=$((failed_tests + 1))
    fi
    echo
fi

# Check if any test files exist
if [ ${#test_files[@]} -eq 0 ]; then
    if [ "$include_integration" = false ]; then
        print_warning "No unit test files found in tests/ directory"
    else
        print_warning "No test files found (checked both unit and integration tests)"
    fi
    exit 0
fi

# Initialize counters
total_tests=0
passed_tests=0
failed_tests=0

print_status "Found ${#test_files[@]} test file(s):"
for file in "${test_files[@]}"; do
    echo "  - $file"
done
echo

# Function to run a single test file
run_test() {
    local test_file="$1"
    local temp_dir="$2"

    if [ -f "$test_file" ]; then
        print_status "Running: $test_file"

        # Create a safe filename for temp files by replacing slashes and dots
        local safe_filename=$(echo "$test_file" | sed 's|[./]|_|g')
        local output_file="$temp_dir/${safe_filename}.output"
        local status_file="$temp_dir/${safe_filename}.status"

        # Set PYTHONPATH to include project root, mvp_site, and .claude/commands for imports (only if they exist)
        PYTHONPATH_TO_EXPORT="$PROJECT_ROOT"
        if [ -d "$PROJECT_ROOT/mvp_site" ]; then
            PYTHONPATH_TO_EXPORT="$PYTHONPATH_TO_EXPORT:$PROJECT_ROOT/mvp_site"
        fi
        if [ -d "$PROJECT_ROOT/.claude/commands" ]; then
            PYTHONPATH_TO_EXPORT="$PYTHONPATH_TO_EXPORT:$PROJECT_ROOT/.claude/commands"
        fi
        export PYTHONPATH="$PYTHONPATH_TO_EXPORT:${PYTHONPATH:-}"
        
        # Choose command based on coverage mode
        if [ "$enable_coverage" = true ]; then
            # Run with coverage
            if TESTING=true TEST_MODE="${TEST_MODE:-mock}" coverage run --append --source=. "$test_file" >"$output_file" 2>&1; then
                echo "PASS" > "$status_file"
                print_success "$test_file completed successfully"
            else
                echo "FAIL" > "$status_file"
                print_error "$test_file failed"
            fi
        else
            # Run without coverage (normal mode)
            if TESTING=true TEST_MODE="${TEST_MODE:-mock}" python "$test_file" >"$output_file" 2>&1; then
                echo "PASS" > "$status_file"
                print_success "$test_file completed successfully"
            else
                echo "FAIL" > "$status_file"
                print_error "$test_file failed"
            fi
        fi
        echo "----------------------------------------"

        # Store output for potential display
        if [ -s "$output_file" ]; then
            echo "=== Output from $test_file ===" >> "$temp_dir/all_output.log"
            cat "$output_file" >> "$temp_dir/all_output.log"
            echo "=== End of $test_file output ===" >> "$temp_dir/all_output.log"
            echo "" >> "$temp_dir/all_output.log"
        fi
    fi
}

# Create temporary directory for parallel execution
temp_dir=$(mktemp -d)
monitor_file="$temp_dir/memory_monitor"
trap "rm -rf $temp_dir" EXIT

# Start memory monitoring based on environment
if [ "${GITHUB_ACTIONS:-}" = "true" ]; then
    # Real GitHub Actions - no memory monitoring (original behavior)
    print_status "🛡️  GitHub Actions detected - no memory monitoring (original behavior)"
    monitor_pid=""
elif [ "${CI:-}" = "true" ]; then
    # CI replica (run_ci_replica.sh) - higher limit for local CI testing
    print_status "🛡️  CI replica mode - memory monitoring (limit: 10GB total)"
    simple_memory_monitor 10 &
    monitor_pid=$!
    trap "kill $monitor_pid 2>/dev/null; rm -rf $temp_dir" EXIT
else
    # Regular local development - conservative limit
    print_status "🛡️  Local development - memory monitoring (limit: 5GB total)"
    simple_memory_monitor 5 &
    monitor_pid=$!
    trap "kill $monitor_pid 2>/dev/null; rm -rf $temp_dir" EXIT
fi

# Choose execution mode based on coverage
if [ "$enable_coverage" = true ]; then
    # Sequential execution for coverage
    print_status "Running tests sequentially for coverage analysis..."
    start_time=$(date +%s)

    for test_file in "${test_files[@]}"; do
        # Check for memory kill signal before each test
        if [ -f "$monitor_file.kill" ]; then
            print_error "🚨 SCRIPT TERMINATED: Memory limit exceeded during sequential execution"
            exit 2
        fi
        
        if [ -f "$test_file" ]; then
            total_tests=$((total_tests + 1))
            echo -n "[$total_tests/${#test_files[@]}] "
            run_test "$test_file" "$temp_dir"
        fi
    done

    test_end_time=$(date +%s)
    test_duration=$((test_end_time - start_time))
    print_status "⏱️  Test execution completed in ${test_duration}s"
else
    # Parallel execution with environment-appropriate concurrency limits
    if [ "${GITHUB_ACTIONS:-}" = "true" ]; then
        # Real GitHub Actions - match runner CPU cores (2 cores)
        max_workers=2
        print_status "Running tests in parallel (GitHub Actions: $max_workers workers - matching runner cores)..."
    elif [ "${CI:-}" = "true" ]; then
        # CI replica - high parallelism for CI testing locally
        max_workers=$(nproc)
        print_status "Running tests in parallel (CI replica: $max_workers workers - full CPU with memory monitoring)..."
    else
        # Regular local development - conservative limit  
        max_workers=2
        print_status "Running tests in parallel (Local dev: $max_workers workers for memory safety)..."
    fi

    # Count total tests for progress tracking
    for test_file in "${test_files[@]}"; do
        if [ -f "$test_file" ]; then
            total_tests=$((total_tests + 1))
        fi
    done

    # Export variables and functions needed by xargs subshells
    export PROJECT_ROOT enable_coverage TEST_MODE RED GREEN YELLOW BLUE NC
    export -f run_test print_status print_success print_error
    
    # Run tests with controlled concurrency using xargs
    printf '%s\n' "${test_files[@]}" | xargs -P "$max_workers" -I {} bash -c '
        if [ -f "$1" ]; then
            run_test "$1" "$2"
        fi
    ' _ {} "$temp_dir"
fi

# Check for memory kill signal
if [ -f "$monitor_file.kill" ]; then
    print_error "🚨 SCRIPT TERMINATED: Memory limit exceeded to prevent system crash"
    print_error "One or more test processes consumed too much memory (>${MEMORY_LIMIT_GB}GB total)"
    
    # Stop the memory monitor
    rm -f "$monitor_file" 2>/dev/null
    
    # Show memory usage at time of kill
    total_memory=$(get_total_memory_usage_gb)
    print_error "Memory usage at termination: ${total_memory}GB"
    
    exit 2  # Exit code 2 = memory kill
fi

# Collect results
for test_file in "${test_files[@]}"; do
    if [ -f "$test_file" ]; then
        safe_filename=$(echo "$test_file" | sed 's|[./]|_|g')
        status_file="$temp_dir/${safe_filename}.status"
        if [ -f "$status_file" ]; then
            status=$(cat "$status_file")
            if [ "$status" = "PASS" ]; then
                passed_tests=$((passed_tests + 1))
            else
                failed_tests=$((failed_tests + 1))
            fi
        fi
    fi
done

# Generate coverage report if enabled
if [ "$enable_coverage" = true ]; then
    echo
    print_status "📊 Generating coverage report..."
    coverage_start_time=$(date +%s)

    # Generate text coverage report
    if coverage report > "$coverage_dir/coverage_report.txt"; then
        print_success "Coverage report generated successfully"

        # Display key coverage metrics
        echo
        print_status "📈 Coverage Summary:"
        echo "----------------------------------------"

        # Show overall coverage
        overall_coverage=$(tail -1 "$coverage_dir/coverage_report.txt" | awk '{print $4}')
        echo "Overall Coverage: $overall_coverage"

        # Show key file coverage
        echo
        echo "Key Files Coverage:"
        grep -E "(main\\.py|gemini_service\\.py|game_state\\.py|firestore_service\\.py)" "$coverage_dir/coverage_report.txt" | head -10

        echo "----------------------------------------"
    else
        print_error "Failed to generate coverage report"
    fi

    # Generate HTML report
    print_status "🌐 Generating HTML coverage report..."
    if coverage html --directory="$coverage_dir"; then
        print_success "HTML coverage report generated in $coverage_dir/"
        print_status "Open $coverage_dir/index.html in your browser to view detailed coverage"
    else
        print_error "Failed to generate HTML coverage report"
    fi

    # Calculate coverage generation time
    coverage_end_time=$(date +%s)
    coverage_duration=$((coverage_end_time - coverage_start_time))

    echo
    print_status "⏱️  Coverage generation completed in ${coverage_duration}s"
    print_status "📁 Coverage files saved to: $coverage_dir"
fi

# Print summary
echo
print_status "🧪 Test Summary:"
echo "  Total tests: $total_tests"
echo "  Passed: $passed_tests"
echo "  Failed: $failed_tests"

# Show intelligent selection metrics if used
if [ "$use_intelligent_selection" = true ]; then
    echo
    print_status "🧠 Intelligent Selection Report:"
    total_possible_tests=$(find ./mvp_site/tests -name "test_*.py" -type f | wc -l)
    if [ $total_possible_tests -gt 0 ]; then
        reduction_pct=$(echo "scale=0; (($total_possible_tests - $total_tests) * 100) / $total_possible_tests" | bc -l 2>/dev/null || echo "0")
        echo "  Selected tests: $total_tests / $total_possible_tests total"
        echo "  Reduction: ${reduction_pct}% (saved ~$((total_possible_tests - total_tests)) test executions)"
        echo "  Mode: Intelligent test selection based on git changes"
    fi
else
    echo
    print_status "🔧 Full Suite Report:"
    echo "  Mode: Complete test suite execution"
fi

# Show failed test details if any
if [ $failed_tests -gt 0 ]; then
    echo
    print_warning "Failed test details:"
    for test_file in "${test_files[@]}"; do
        if [ -f "$test_file" ]; then
            safe_filename=$(echo "$test_file" | sed 's|[./]|_|g')
            status_file="$temp_dir/${safe_filename}.status"
            if [ -f "$status_file" ] && [ "$(cat "$status_file")" = "FAIL" ]; then
                echo "  - $test_file"
                output_file="$temp_dir/${safe_filename}.output"
                if [ -f "$output_file" ] && [ -s "$output_file" ]; then
                    echo "    Last few lines of output:"
                    tail -n 10 "$output_file" | sed 's/^/      /'
                fi
            fi
        fi
    done
fi

# Stop memory monitor
if [ -n "$monitor_pid" ]; then
    print_status "🛡️  Stopping memory monitor..."
    rm -f "$monitor_file" 2>/dev/null
fi

if [ $failed_tests -eq 0 ]; then
    print_success "All tests passed! 🎉"
    exit 0
else
    print_error "$failed_tests test(s) failed"

    # Clean summary at the end
    echo
    echo "SUMMARY: $passed_tests passed, $failed_tests failed"
    echo "FAILED TESTS:"
    for test_file in "${test_files[@]}"; do
        if [ -f "$test_file" ]; then
            safe_filename=$(echo "$test_file" | sed 's|[./]|_|g')
            status_file="$temp_dir/${safe_filename}.status"
            if [ -f "$status_file" ] && [ "$(cat "$status_file")" = "FAIL" ]; then
                echo "$test_file"
            fi
        fi
    done

    exit 1
fi
