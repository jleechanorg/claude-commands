#!/bin/bash

# CI Local Replica Script for WorldArchitect.AI
# Replicates the GitHub Actions CI environment as closely as possible locally
# Based on .github/workflows/test.yml

set -euo pipefail  # Exit on error, undefined var, or failed pipeline

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_header() {
    echo -e "${CYAN}===================================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}===================================================${NC}"
}

print_step() {
    echo -e "${BLUE}[CI-STEP]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Store original working directory
ORIGINAL_DIR=$(pwd)
# Find the project root (script is in ci_replica/ subdirectory)
PROJECT_ROOT="$(cd "$(dirname "$0")/.."; pwd)"

print_header "WorldArchitect.AI CI Local Replica"
print_info "Replicating GitHub Actions CI environment locally"
print_info "Based on: .github/workflows/test.yml"
print_info "Project root: $PROJECT_ROOT"

# Step 1: Environment Cleanup and Setup (mimics fresh CI environment)
print_step "Step 1: Environment Cleanup and Setup"

# Clear Python-related environment variables that might interfere
print_info "Clearing Python environment variables..."
unset PYTHONPATH
unset PYTHONHOME
unset VIRTUAL_ENV
unset CONDA_DEFAULT_ENV
unset CONDA_PREFIX

# Set CI-specific environment variables
print_info "Setting CI-specific environment variables..."
export CI=true
export GITHUB_ACTIONS=true
export TESTING=true
export TEST_MODE=mock
export DEBUG=false

# Display environment info
print_info "Environment setup:"
echo "  CI: $CI"
echo "  GITHUB_ACTIONS: $GITHUB_ACTIONS"
echo "  TESTING: $TESTING"
echo "  TEST_MODE: $TEST_MODE"
echo "  DEBUG: $DEBUG"

# Step 2: Python Version Check
print_step "Step 2: Python Version Check"

# CI uses Python 3.11 - check if available
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
    print_success "Python 3.11 found (matches CI)"
    $PYTHON_CMD --version
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    print_warning "Python 3.11 not found, using $(python3 --version)"
    print_warning "CI uses Python 3.11, results may differ"
else
    print_error "No Python 3 found. Please install Python 3.11 to match CI"
    exit 1
fi

# Step 3: Clean Virtual Environment Setup
print_step "Step 3: Clean Virtual Environment Setup"

# Remove existing virtual environment to start fresh (like CI)
if [ -d "$PROJECT_ROOT/venv" ]; then
    print_info "Removing existing virtual environment..."
    rm -rf "$PROJECT_ROOT/venv"
fi

# Create fresh virtual environment (exactly like CI)
print_info "Creating fresh virtual environment with $PYTHON_CMD..."
cd "$PROJECT_ROOT"
$PYTHON_CMD -m venv venv

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate

# Verify virtual environment
if [ "$VIRTUAL_ENV" != "$PROJECT_ROOT/venv" ]; then
    print_error "Virtual environment activation failed"
    exit 1
fi

print_success "Virtual environment activated: $VIRTUAL_ENV"

# Step 4: Dependency Installation (exactly like CI)
print_step "Step 4: Dependency Installation (CI-exact sequence)"

# Upgrade pip and install resolver tools (matches CI)
print_info "Upgrading pip and installing resolver tools..."
python -m pip install --upgrade pip setuptools wheel

# Pin grpcio and grpcio-status to compatible versions (matches CI)
print_info "Installing pinned grpcio versions..."
pip install grpcio==1.73.1 grpcio-status==1.73.1

# Install protobuf first to avoid conflicts (matches CI)
print_info "Installing protobuf (conflict prevention)..."
pip install protobuf==4.25.3

# Install project requirements (matches CI)
print_info "Installing project requirements..."
pip install -r mvp_site/requirements.txt

# Step 5: Verify vpython works (matches CI)
print_step "Step 5: Verify vpython Script"

print_info "Making vpython executable..."
chmod +x vpython

print_info "Testing vpython..."
if ./vpython --version; then
    print_success "vpython verification successful"
else
    print_error "vpython verification failed"
    exit 1
fi

# Step 6: System Information (for debugging)
print_step "Step 6: System Information"

print_info "System information:"
echo "  OS: $(uname -s) $(uname -r)"
echo "  Python: $($PYTHON_CMD --version)"
echo "  Pip: $(pip --version)"
echo "  Virtual env: $VIRTUAL_ENV"
echo "  Working dir: $(pwd)"

print_info "Key package versions:"
python -c "
import sys
packages = ['flask', 'gunicorn', 'firebase-admin', 'google-cloud-firestore', 'protobuf']
for pkg in packages:
    try:
        __import__(pkg)
        if pkg == 'flask':
            import flask
            print(f'  Flask: {flask.__version__}')
        elif pkg == 'gunicorn':
            import gunicorn
            print(f'  Gunicorn: {gunicorn.__version__}')
        elif pkg == 'firebase-admin':
            import firebase_admin
            print(f'  Firebase Admin: {firebase_admin.__version__}')
        elif pkg == 'google-cloud-firestore':
            import google.cloud.firestore
            print(f'  Firestore: {google.cloud.firestore.__version__}')
        elif pkg == 'protobuf':
            import google.protobuf
            print(f'  Protobuf: {google.protobuf.__version__}')
    except ImportError as e:
        print(f'  {pkg}: Not installed or import error')
    except AttributeError:
        print(f'  {pkg}: Installed (version unknown)')
"

# Step 7: Pre-test Verification
print_step "Step 7: Pre-test Verification"

# Check if we're in the right directory
if [ ! -d "mvp_site" ]; then
    print_error "mvp_site directory not found. This script must be run from project root."
    exit 1
fi

# Check critical files exist
critical_files=("run_tests.sh" "mvp_site/requirements.txt")
for file in "${critical_files[@]}"; do
    if [ ! -f "$file" ]; then
        print_error "Critical file missing: $file"
        exit 1
    fi
done

print_success "Pre-test verification passed"

# Step 8: Run Tests (exactly like CI)
print_step "Step 8: Run Test Suite (CI-exact execution)"

print_info "Making run_tests.sh executable..."
chmod +x run_tests.sh

print_info "Running tests using project's run_tests.sh script..."
print_info "This matches the exact CI execution path"

# Set environment variables exactly like CI
export TESTING=true

# Execute tests exactly like CI does
if ./run_tests.sh; then
    print_success "========================================="
    print_success "✅ ALL TESTS PASSED"
    print_success "========================================="
    test_exit_code=0
else
    print_error "========================================="
    print_error "❌ SOME TESTS FAILED"
    print_error "========================================="
    print_error ""
    print_error "Note: Test failures in CI may be due to:"
    print_error "  - Missing local services (e.g., test server)"
    print_error "  - Test isolation issues"
    print_error "  - Timing-sensitive tests"
    print_error "  - Environment differences"
    test_exit_code=1
fi

# Step 9: Cleanup and Results
print_step "Step 9: Results Summary"

if [ $test_exit_code -eq 0 ]; then
    print_success "CI Local Replica: ALL TESTS PASSED ✅"
    print_info "Your local environment successfully replicates CI behavior"
else
    print_error "CI Local Replica: TESTS FAILED ❌"
    print_info "This indicates either:"
    print_info "  1. Genuine test failures that would also fail in CI"
    print_info "  2. Local environment differences despite replication attempts"
fi

print_info "CI environment replication complete"
print_info "Virtual environment preserved at: $PROJECT_ROOT/venv"
print_info "To use this environment later: source $PROJECT_ROOT/venv/bin/activate"

# Return to original directory
cd "$ORIGINAL_DIR"

exit $test_exit_code