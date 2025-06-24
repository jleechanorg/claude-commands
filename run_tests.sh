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

# Run each test file
for test_file in "${test_files[@]}"; do
    if [ -f "$test_file" ]; then
        total_tests=$((total_tests + 1))
        print_status "Running: $test_file"
        
        # Run the test with TESTING environment variable using vpython
        if TESTING=true vpython "$test_file"; then
            print_success "$test_file completed successfully"
            passed_tests=$((passed_tests + 1))
        else
            print_error "$test_file failed"
            failed_tests=$((failed_tests + 1))
        fi
        echo "----------------------------------------"
    fi
done

# Print summary
echo
print_status "Test Summary:"
echo "  Total tests: $total_tests"
echo "  Passed: $passed_tests"
echo "  Failed: $failed_tests"

if [ $failed_tests -eq 0 ]; then
    print_success "All tests passed! 🎉"
    exit 0
else
    print_error "$failed_tests test(s) failed"
    exit 1
fi 