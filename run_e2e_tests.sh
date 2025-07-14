#!/bin/bash

# Enhanced End-to-End Test Runner with Real-Mode Testing Framework Support
# Reads TEST_MODE environment variable to determine testing mode
# Supports mock, real, and capture modes using TestServiceProvider abstraction
#
# Usage:
#   TEST_MODE=mock ./run_e2e_tests.sh     # Mock services (default)
#   TEST_MODE=real ./run_e2e_tests.sh     # Real services 
#   TEST_MODE=capture ./run_e2e_tests.sh  # Real services with data capture
#
# Or via slash commands:
#   /teste  -> TEST_MODE=mock
#   /tester -> TEST_MODE=real
#   /testerc -> TEST_MODE=capture

set -e

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

# Store project root
PROJECT_ROOT="$(cd "$(dirname "$0")"; pwd)"

# Determine test mode from environment variable
TEST_MODE="${TEST_MODE:-mock}"

print_status "🧪 Real-Mode Testing Framework - E2E Runner"
print_status "Test Mode: $TEST_MODE"
echo "=============================================="

# Validate TEST_MODE
case "$TEST_MODE" in
    "mock")
        print_status "📱 Mock Mode: Using MockServiceProvider (fast, free)"
        ;;
    "real") 
        print_status "🌐 Real Mode: Using RealServiceProvider (costs money)"
        ;;
    "capture")
        print_status "📡 Capture Mode: Using RealServiceProvider with data capture"
        ;;
    *)
        print_error "Invalid TEST_MODE: $TEST_MODE"
        print_error "Valid modes: mock, real, capture"
        exit 1
        ;;
esac

# Check if we're in the right directory
if [ ! -d "mvp_site" ]; then
    print_error "mvp_site directory not found. Please run this script from the project root."
    exit 1
fi

# Validate environment for real/capture modes
if [[ "$TEST_MODE" == "real" || "$TEST_MODE" == "capture" ]]; then
    print_status "Validating real service configuration..."
    
    # Check for required environment variables
    missing_vars=()
    
    if [[ -z "$TEST_GEMINI_API_KEY" ]]; then
        missing_vars+=("TEST_GEMINI_API_KEY")
    fi
    
    if [[ -z "$TEST_FIRESTORE_PROJECT" ]]; then
        print_warning "TEST_FIRESTORE_PROJECT not set, using default: worldarchitect-test"
        export TEST_FIRESTORE_PROJECT="worldarchitect-test"
    fi
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        print_error "Missing required environment variables for $TEST_MODE mode:"
        for var in "${missing_vars[@]}"; do
            print_error "  - $var"
        done
        print_error ""
        print_error "Setup instructions:"
        print_error "  export TEST_GEMINI_API_KEY=your_test_api_key"
        print_error "  export TEST_FIRESTORE_PROJECT=your_test_project  # optional"
        exit 1
    fi
    
    print_success "Real service configuration validated"
    print_status "Firestore Project: $TEST_FIRESTORE_PROJECT"
    print_status "Gemini API Key: ${TEST_GEMINI_API_KEY:0:10}***"
fi

# Set up capture directory for capture mode
if [[ "$TEST_MODE" == "capture" ]]; then
    CAPTURE_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    CAPTURE_DIR="/tmp/test_captures/$CAPTURE_TIMESTAMP"
    export TEST_CAPTURE_DIR="$CAPTURE_DIR"
    
    print_status "Setting up data capture..."
    mkdir -p "$CAPTURE_DIR"
    print_status "Capture directory: $CAPTURE_DIR"
fi

# Check if virtual environment exists
if [ ! -d "$PROJECT_ROOT/venv" ]; then
    print_error "Virtual environment not found at $PROJECT_ROOT/venv"
    print_error "Please run: python3 -m venv venv && source venv/bin/activate && pip install -r mvp_site/requirements.txt"
    exit 1
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source "$PROJECT_ROOT/venv/bin/activate"

# Change to mvp_site directory
cd mvp_site

# Install requirements
print_status "Installing/updating requirements..."
pip install -r requirements.txt > /dev/null 2>&1

# Set environment variables for test execution
export TESTING=true

# For real/capture modes, set service configuration
if [[ "$TEST_MODE" == "real" || "$TEST_MODE" == "capture" ]]; then
    export FIREBASE_PROJECT_ID="$TEST_FIRESTORE_PROJECT"
    export GEMINI_API_KEY="$TEST_GEMINI_API_KEY"
fi

print_status "Environment configured:"
print_status "  TEST_MODE=$TEST_MODE"
print_status "  TESTING=$TESTING"
if [[ "$TEST_MODE" == "real" || "$TEST_MODE" == "capture" ]]; then
    print_status "  FIREBASE_PROJECT_ID=$FIREBASE_PROJECT_ID"
    print_status "  GEMINI_API_KEY=${GEMINI_API_KEY:0:10}***"
fi
if [[ "$TEST_MODE" == "capture" ]]; then
    print_status "  TEST_CAPTURE_DIR=$TEST_CAPTURE_DIR"
fi

echo ""

# Find all end-to-end test files
print_status "Discovering end-to-end test files..."
e2e_test_files=()

# Look for end2end tests in various locations
while IFS= read -r -d '' file; do
    e2e_test_files+=("$file")
done < <(find . -name "*end2end*.py" -type f \
    ! -path "./venv/*" \
    ! -path "./node_modules/*" \
    ! -path "./mvp_site/tests/test_end2end/run_end2end_tests.py" \
    -print0)

# Also include specific integration test patterns
while IFS= read -r -d '' file; do
    e2e_test_files+=("$file")
done < <(find . -name "test_*integration*.py" -type f \
    ! -path "./venv/*" \
    ! -path "./node_modules/*" \
    -print0)

if [[ ${#e2e_test_files[@]} -eq 0 ]]; then
    print_warning "No end-to-end test files found"
    print_warning "Looking for files matching: *end2end*.py, test_*integration*.py"
    exit 0
fi

print_status "Found ${#e2e_test_files[@]} end-to-end test files:"
for file in "${e2e_test_files[@]}"; do
    print_status "  - $file"
done

echo ""

# Cost warning for real/capture modes
if [[ "$TEST_MODE" == "real" || "$TEST_MODE" == "capture" ]]; then
    print_warning "⚠️  WARNING: $TEST_MODE mode will use real services"
    print_warning "  - Gemini API calls will incur costs"
    print_warning "  - Firestore operations will create real data"
    print_warning "  - Test cleanup will run automatically after tests"
    if [[ "$TEST_MODE" == "capture" ]]; then
        print_warning "  - All service interactions will be captured and stored"
    fi
    echo ""
    
    read -p "Continue with $TEST_MODE mode testing? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Testing cancelled by user"
        exit 1
    fi
    
    print_success "Proceeding with $TEST_MODE mode testing"
    echo ""
fi

# Run the tests
print_status "🚀 Running end-to-end tests in $TEST_MODE mode..."
echo ""

start_time=$(date +%s)
passed_tests=0
failed_tests=0
failed_test_files=()

# Run each test file
for test_file in "${e2e_test_files[@]}"; do
    if [ -f "$test_file" ]; then
        print_status "Running: $test_file"
        
        if python "$test_file"; then
            print_success "✅ $test_file"
            passed_tests=$((passed_tests + 1))
        else
            print_error "❌ $test_file"
            failed_tests=$((failed_tests + 1))
            failed_test_files+=("$test_file")
        fi
        echo "----------------------------------------"
    fi
done

end_time=$(date +%s)
duration=$((end_time - start_time))

# Print summary
echo ""
echo "🎯 End-to-End Test Summary ($TEST_MODE mode)"
echo "=============================================="
print_status "⏱️  Duration: ${duration}s"
print_status "📊 Total tests: $((passed_tests + failed_tests))"
print_success "✅ Passed: $passed_tests"

if [[ $failed_tests -gt 0 ]]; then
    print_error "❌ Failed: $failed_tests"
    print_error "Failed test files:"
    for file in "${failed_test_files[@]}"; do
        print_error "  - $file"
    done
else
    print_success "🎉 All tests passed!"
fi

# Capture mode specific output
if [[ "$TEST_MODE" == "capture" ]]; then
    echo ""
    print_status "📡 Data Capture Summary"
    echo "========================"
    print_status "Capture directory: $TEST_CAPTURE_DIR"
    
    if [[ -d "$TEST_CAPTURE_DIR" && "$(ls -A "$TEST_CAPTURE_DIR" 2>/dev/null)" ]]; then
        print_status "Captured files:"
        ls -la "$TEST_CAPTURE_DIR/" | tail -n +2 | while read -r line; do
            print_status "  $line"
        done
        
        echo ""
        print_status "💡 Next steps:"
        print_status "1. Review captured data in $TEST_CAPTURE_DIR"
        print_status "2. Use captured data to update mock implementations"
        print_status "3. Run /teste to validate mock accuracy"
        print_status "4. Consider adding $TEST_CAPTURE_DIR to .gitignore"
    else
        print_warning "⚠️  No data was captured - check test implementation"
    fi
fi

# Cleanup for real/capture modes
if [[ "$TEST_MODE" == "real" || "$TEST_MODE" == "capture" ]]; then
    echo ""
    print_status "🧹 Running test data cleanup..."
    
    # Attempt to run cleanup via TestServiceProvider
    if python -c "
from testing_framework import get_current_provider
try:
    provider = get_current_provider()
    if hasattr(provider, 'cleanup'):
        provider.cleanup()
        print('✅ Test data cleanup completed')
    else:
        print('⚠️  Provider does not support cleanup')
except Exception as e:
    print(f'⚠️  Cleanup failed: {e}')
" 2>/dev/null; then
        print_success "Cleanup completed successfully"
    else
        print_warning "Cleanup script not available or failed"
        print_warning "Manual cleanup may be required for test data"
    fi
fi

echo ""

# Set exit code based on test results
if [[ $failed_tests -gt 0 ]]; then
    print_error "❌ Some tests failed in $TEST_MODE mode"
    exit 1
else
    print_success "✅ All tests passed in $TEST_MODE mode"
    exit 0
fi