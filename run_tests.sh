#!/bin/bash

# Test Runner Script for WorldArchitect.ai
# Runs all test_*.py files in mvp_site directory using vpython
#
# Usage:
#   ./run_tests.sh                  # Run unit tests only (default)
#   ./run_tests.sh --integration    # Run unit tests AND integration tests
#   ./run_tests.sh --coverage       # Run unit tests with coverage analysis
#   ./run_tests.sh --integration --coverage  # Run unit and integration tests with coverage
#
# Integration tests (in test_integration/) require external dependencies like google-genai
# and are excluded by default to ensure tests run quickly and without external dependencies.
# Coverage runs tests sequentially (not parallel) for accurate coverage tracking.
# Coverage HTML output goes to: /tmp/worldarchitectai/coverage/

# Note: Not using 'set -e' so we can run all tests even if some fail

# Store project root before changing directories
PROJECT_ROOT="$(cd "$(dirname "$0")"; pwd)"

# Check if virtual environment exists, create if not
if [ ! -d "$PROJECT_ROOT/venv" ]; then
    echo "Virtual environment not found at $PROJECT_ROOT/venv"
    echo "Creating virtual environment..."
    if ! python3 -m venv "$PROJECT_ROOT/venv"; then
        echo "Error: Failed to create virtual environment."
        exit 1
    fi
    echo "Virtual environment created successfully."
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Change to mvp_site directory
cd mvp_site

# Activate virtual environment
print_status "Activating virtual environment..."
source "$PROJECT_ROOT/venv/bin/activate"

pip install -r requirements.txt

print_status "Running tests in mvp_site directory..."
print_status "Setting TESTING=true for faster AI model usage"
print_status "TEST_MODE=${TEST_MODE:-mock} (Real-Mode Testing Framework)"

# Parse command line arguments
include_integration=false
enable_coverage=false
coverage_dir="/tmp/worldarchitectai/coverage"

for arg in "$@"; do
    case $arg in
        --integration)
            include_integration=true
            ;;
        --coverage)
            enable_coverage=true
            ;;
        *)
            if [[ $arg == --* ]]; then
                print_warning "Unknown argument: $arg"
            fi
            ;;
    esac
done

if [ "$include_integration" = true ]; then
    print_status "Integration tests enabled (--integration flag specified)"
else
    print_status "Skipping integration tests (use --integration to include them)"
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

# Find all test files in tests subdirectory, excluding venv, prototype, manual_tests, and test_integration
test_files=()
while IFS= read -r -d '' file; do
    test_files+=("$file")
done < <(find ./tests -name "test_*.py" -type f \
    ! -path "./venv/*" \
    ! -path "./node_modules/*" \
    ! -path "./prototype/*" \
    ! -path "./tests/manual_tests/*" \
    ! -path "./tests/test_integration/*" \
    -print0)

# Always include test_integration_mock.py from mvp_site/test_integration directory (fast mock tests)
if [ -f "./mvp_site/test_integration/test_integration_mock.py" ]; then
    test_files+=("./mvp_site/test_integration/test_integration_mock.py")
fi

# Also include test_integration directories if not in GitHub export mode
if [ "$include_integration" = true ]; then
    # Check for test_integration in both root and tests/ directory
    if [ -d "./test_integration" ]; then
        print_status "Including integration tests from test_integration/"
        while IFS= read -r -d '' file; do
            test_files+=("$file")
        done < <(find ./test_integration -name "test_*.py" -type f -print0)
    fi

    if [ -d "./tests/test_integration" ]; then
        print_status "Including integration tests from tests/test_integration/"
        while IFS= read -r -d '' file; do
            test_files+=("$file")
        done < <(find ./tests/test_integration -name "test_*.py" -type f -print0)
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
    done < <(find claude-bot-commands/tests -name "test_*.py" -type f -print0)
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
trap "rm -rf $temp_dir" EXIT

# Choose execution mode based on coverage
if [ "$enable_coverage" = true ]; then
    # Sequential execution for coverage
    print_status "Running tests sequentially for coverage analysis..."
    start_time=$(date +%s)

    for test_file in "${test_files[@]}"; do
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
    # Parallel execution for normal mode
    print_status "Running tests in parallel (one thread per file)..."

    # Run tests in parallel using background processes
    pids=()
    for test_file in "${test_files[@]}"; do
        if [ -f "$test_file" ]; then
            total_tests=$((total_tests + 1))
            run_test "$test_file" "$temp_dir" &
            pids+=($!)
        fi
    done

    # Wait for all background processes to complete
    print_status "Waiting for all tests to complete..."
    for pid in "${pids[@]}"; do
        wait "$pid"
    done
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
    if source ../venv/bin/activate && coverage report > "$coverage_dir/coverage_report.txt"; then
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
    if source ../venv/bin/activate && coverage html --directory="$coverage_dir"; then
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
