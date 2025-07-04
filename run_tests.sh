#!/bin/bash

# Test Runner Script for WorldArchitect.ai
# Runs all test_*.py files in mvp_site directory using vpython
#
# Usage:
#   ./run_tests.sh                  # Run unit tests only (default)
#   ./run_tests.sh --integration    # Run unit tests AND integration tests
#
# Integration tests (in test_integration/) require external dependencies like google-genai
# and are excluded by default to ensure tests run quickly and without external dependencies.

# Note: Not using 'set -e' so we can run all tests even if some fail

# Use the vpython script in project root
VPYTHON="$PWD/vpython"

# Check if vpython exists
if [ ! -f "$VPYTHON" ]; then
    echo "Error: vpython script not found at $VPYTHON"
    exit 1
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

print_status "Running tests in mvp_site directory..."
print_status "Setting TESTING=true for faster AI model usage"

# Check if we should include integration tests
# Default: exclude integration tests unless --integration flag is specified
include_integration=false

if [ "$1" = "--integration" ]; then
    include_integration=true
    print_status "Integration tests enabled (--integration flag specified)"
else
    print_status "Skipping integration tests (use --integration to include them)"
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
        
        if TESTING=true "$VPYTHON" "$test_file" >"$output_file" 2>&1; then
            echo "PASS" > "$status_file"
            print_success "$test_file completed successfully"
        else
            echo "FAIL" > "$status_file"
            print_error "$test_file failed"
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

# Print summary
echo
print_status "Test Summary:"
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