#!/bin/bash

# Test Runner Script for WorldArchitect.ai
# Runs all test_*.py files in mvp_site directory using vpython

# Note: Not using 'set -e' so we can run all tests even if some fail

# Define vpython function locally (replicating the bashrc function)
vpython() {
    PROJECT_ROOT_PATH="$HOME/projects/worldarchitect.ai"
    VENV_ACTIVATE_SCRIPT="$PROJECT_ROOT_PATH/venv/bin/activate"
    
    if [ ! -f "$VENV_ACTIVATE_SCRIPT" ]; then
        echo "Error: Virtual environment activate script not found at $VENV_ACTIVATE_SCRIPT"
        echo "Please create the virtual environment first: cd $PROJECT_ROOT_PATH && python3 -m venv venv"
        return 1
    fi
    
    if [[ "$VIRTUAL_ENV" != "$PROJECT_ROOT_PATH/venv" ]]; then
        echo "Activating virtual environment: $PROJECT_ROOT_PATH/venv"
        source "$VENV_ACTIVATE_SCRIPT"
    else
        echo "Virtual environment already active."
    fi
    
    echo "Running python $*"
    python "$@"
}

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

# Find all test files
test_files=(test_*.py)

# Check if any test files exist
if [ ! -e "${test_files[0]}" ]; then
    print_warning "No test files found matching pattern test_*.py"
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
        
        # Run the test with TESTING environment variable using vpython
        # Capture output to temporary file for later display
        local output_file="$temp_dir/${test_file}.output"
        local status_file="$temp_dir/${test_file}.status"
        
        if TESTING=true vpython "$test_file" >"$output_file" 2>&1; then
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
        status_file="$temp_dir/${test_file}.status"
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
            status_file="$temp_dir/${test_file}.status"
            if [ -f "$status_file" ] && [ "$(cat "$status_file")" = "FAIL" ]; then
                echo "  - $test_file"
                output_file="$temp_dir/${test_file}.output"
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
    exit 1
fi 