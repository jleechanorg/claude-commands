#!/bin/bash

# Coverage Test Runner Script for WorldArchitect.ai
# Runs all test_*.py files with comprehensive coverage analysis
#
# Usage:
#   ./run_tests_with_coverage.sh                   # Unit tests only with coverage (HTML report included by default)
#   ./run_tests_with_coverage.sh --integration     # Unit tests AND integration tests with coverage
#   ./run_tests_with_coverage.sh --no-html         # Generate text report only (skip HTML)
#   ./run_tests_with_coverage.sh --integration --no-html  # Integration tests with text report only
#
# This script runs tests SEQUENTIALLY (not parallel) to ensure accurate coverage tracking

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

# Parse command line arguments
include_integration=false
generate_html=true  # Default to generating HTML

for arg in "$@"; do
    case $arg in
        --integration)
            include_integration=true
            ;;
        --no-html)
            generate_html=false
            ;;
        *)
            print_warning "Unknown argument: $arg"
            ;;
    esac
done

# Create coverage output directory
mkdir -p "/tmp/worldarchitectai/coverage"

# Change to mvp_site directory
cd mvp_site

print_status "🧪 Running tests with coverage analysis..."
print_status "Setting TESTING=true for faster AI model usage"
print_status "HTML output will be saved to: /tmp/worldarchitectai/coverage"

if [ "$include_integration" = true ]; then
    print_status "Integration tests enabled (--integration flag specified)"
else
    print_status "Skipping integration tests (use --integration to include them)"
fi

# Check if coverage is installed
print_status "Checking coverage installation..."

# First, activate the virtual environment
if ! source ../venv/bin/activate; then
    print_error "Failed to activate virtual environment"
    exit 1
fi

# Then check if coverage is importable
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

print_status "Found ${#test_files[@]} test file(s) for coverage analysis"
print_status "Running tests SEQUENTIALLY to ensure accurate coverage tracking..."
echo

# Start coverage tracking
start_time=$(date +%s)
print_status "⏱️  Starting coverage analysis at $(date)"

# Clear any previous coverage data
source ../venv/bin/activate && coverage erase

# Initialize counters
total_tests=0
passed_tests=0
failed_tests=0
failed_test_files=()

# Run tests sequentially with coverage
for test_file in "${test_files[@]}"; do
    if [ -f "$test_file" ]; then
        total_tests=$((total_tests + 1))
        echo -n "[$total_tests/${#test_files[@]}] Running: $test_file ... "

        if TESTING=true source ../venv/bin/activate && coverage run --append --source=. "$VPYTHON" "$test_file" >/dev/null 2>&1; then
            passed_tests=$((passed_tests + 1))
            print_success "✓"
        else
            failed_tests=$((failed_tests + 1))
            failed_test_files+=("$test_file")
            print_error "✗"
        fi
    fi
done

# Calculate test execution time
test_end_time=$(date +%s)
test_duration=$((test_end_time - start_time))

echo
print_status "⏱️  Test execution completed in ${test_duration}s"
print_status "📊 Generating coverage report..."

# Generate coverage reports
coverage_start_time=$(date +%s)

# Generate terminal coverage report
source ../venv/bin/activate && coverage report > coverage_report.txt
coverage_report_exit_code=$?

# Display key coverage metrics
if [ $coverage_report_exit_code -eq 0 ]; then
    print_success "Coverage report generated successfully"

    # Extract and display key metrics
    echo
    print_status "📈 Coverage Summary:"
    echo "----------------------------------------"

    # Show overall coverage
    overall_coverage=$(tail -1 coverage_report.txt | awk '{print $4}')
    echo "Overall Coverage: $overall_coverage"

    # Show key file coverage
    echo
    echo "Key Files Coverage:"
    grep -E "(main\.py|gemini_service\.py|game_state\.py|firestore_service\.py)" coverage_report.txt | head -10

    echo "----------------------------------------"

    # Display full report
    echo
    print_status "📋 Full Coverage Report:"
    cat coverage_report.txt

else
    print_error "Failed to generate coverage report"
fi

# Generate HTML report if enabled
if [ "$generate_html" = true ]; then
    print_status "🌐 Generating HTML coverage report..."
    if source ../venv/bin/activate && coverage html --directory="/tmp/worldarchitectai/coverage"; then
        print_success "HTML coverage report generated in /tmp/worldarchitectai/coverage/"
        print_status "Open /tmp/worldarchitectai/coverage/index.html in your browser to view detailed coverage"
    else
        print_error "Failed to generate HTML coverage report"
    fi
else
    print_status "HTML report skipped (--no-html specified)"
fi

# Calculate coverage generation time
coverage_end_time=$(date +%s)
coverage_duration=$((coverage_end_time - coverage_start_time))
total_duration=$((coverage_end_time - start_time))

# Print timing summary
echo
print_status "⏱️  Timing Summary:"
echo "  Test execution: ${test_duration}s"
echo "  Coverage generation: ${coverage_duration}s"
echo "  Total time: ${total_duration}s"

# Print test summary
echo
print_status "🧪 Test Summary:"
echo "  Total tests: $total_tests"
echo "  Passed: $passed_tests"
echo "  Failed: $failed_tests"

# Show failed test details if any
if [ $failed_tests -gt 0 ]; then
    echo
    print_warning "Failed test files:"
    for failed_file in "${failed_test_files[@]}"; do
        echo "  - $failed_file"
    done
fi

# Final status
if [ $failed_tests -eq 0 ]; then
    print_success "✅ All tests passed with coverage analysis complete!"
    exit 0
else
    print_error "❌ $failed_tests test(s) failed"
    exit 1
fi
