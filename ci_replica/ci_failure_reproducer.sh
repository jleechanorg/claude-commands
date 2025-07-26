#!/bin/bash

# CI Failure Reproducer Script for WorldArchitect.AI
# Specifically designed to reproduce CI failures locally with maximum isolation
# Creates a completely isolated environment to match CI conditions

set -euo pipefail  # Exit on error, undefined var, or failed pipeline

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${CYAN}======================================================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}======================================================================${NC}"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
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

print_isolate() {
    echo -e "${MAGENTA}[ISOLATE]${NC} $1"
}

# Parse command line arguments
ISOLATION_MODE="full"
PYTHON_VERSION="3.11"
KEEP_ISOLATION_DIR=false
SKIP_SYSTEM_PACKAGES=false

for arg in "$@"; do
    case $arg in
        --isolation=*)
            ISOLATION_MODE="${arg#*=}"
            ;;
        --python=*)
            PYTHON_VERSION="${arg#*=}"
            ;;
        --keep-isolation)
            KEEP_ISOLATION_DIR=true
            ;;
        --skip-system-packages)
            SKIP_SYSTEM_PACKAGES=true
            ;;
        --help)
            echo "CI Failure Reproducer Script"
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --isolation=MODE      Isolation mode: full, partial, minimal (default: full)"
            echo "  --python=VERSION      Python version to use (default: 3.11)"
            echo "  --keep-isolation      Keep isolation directory after completion"
            echo "  --skip-system-packages Skip system package installation"
            echo "  --help                Show this help message"
            echo ""
            echo "Isolation modes:"
            echo "  full     - Complete isolation in temporary directory"
            echo "  partial  - Isolated Python environment only"
            echo "  minimal  - Just clean virtual environment"
            exit 0
            ;;
        *)
            print_warning "Unknown argument: $arg"
            ;;
    esac
done

PROJECT_ROOT="$(cd "$(dirname "$0")"; pwd)"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ISOLATION_DIR="/tmp/ci_isolation_$TIMESTAMP"

print_header "CI Failure Reproducer - Maximum Isolation Mode"
print_info "Isolation mode: $ISOLATION_MODE"
print_info "Python version: $PYTHON_VERSION"
print_info "Project root: $PROJECT_ROOT"
print_info "Isolation directory: $ISOLATION_DIR"

# Step 1: Create Isolated Environment
print_step "1. Creating Isolated Environment"

case $ISOLATION_MODE in
    "full")
        print_isolate "Full isolation mode: Creating complete isolated environment"
        mkdir -p "$ISOLATION_DIR"
        cd "$ISOLATION_DIR"

        # Copy entire project to isolation directory
        print_info "Copying project to isolation directory..."
        cp -r "$PROJECT_ROOT"/* . 2>/dev/null || true
        cp -r "$PROJECT_ROOT"/.* . 2>/dev/null || true

        # Remove any existing virtual environments
        rm -rf venv .venv env

        print_success "Project copied to isolated environment"
        ;;

    "partial")
        print_isolate "Partial isolation mode: Using original directory with environment isolation"
        cd "$PROJECT_ROOT"
        rm -rf venv .venv env
        ;;

    "minimal")
        print_isolate "Minimal isolation mode: Clean virtual environment only"
        cd "$PROJECT_ROOT"
        if [ -d venv ]; then
            rm -rf venv
        fi
        ;;
esac

# Step 2: Complete Environment Reset
print_step "2. Complete Environment Reset"

# Save original environment for comparison
print_info "Saving original environment..."
env | sort > /tmp/original_env_$TIMESTAMP.txt

# Complete environment variable reset
print_isolate "Resetting all Python-related environment variables..."
unset PYTHONPATH PYTHONHOME VIRTUAL_ENV CONDA_DEFAULT_ENV CONDA_PREFIX
unset PIPENV_ACTIVE POETRY_ACTIVE PIP_USER PYTHONSTARTUP PYTHONOPTIMIZE
unset PYTHONDONTWRITEBYTECODE PYTHONHASHSEED PYTHONUNBUFFERED
unset PYTHON_EGG_CACHE PYTHONIOENCODING PYTHONWARNINGS
unset SETUPTOOLS_USE_DISTUTILS

# Set CI-specific environment (comprehensive)
print_isolate "Setting CI-specific environment variables..."
export CI=true
export GITHUB_ACTIONS=true
export TESTING=true
export TEST_MODE=mock
export DEBUG=false
export RUNNER_OS=Linux
export RUNNER_ARCH=X64
export RUNNER_TEMP=/tmp
export RUNNER_WORKSPACE=$(pwd)
export DEBIAN_FRONTEND=noninteractive
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
export TZ=UTC

# Clear any cached Python bytecode
print_isolate "Clearing Python bytecode cache..."
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Step 3: Python Version Management
print_step "3. Python Version Management"

# Try to use the exact Python version specified
if [ "$PYTHON_VERSION" = "3.11" ]; then
    if command -v python3.11 &> /dev/null; then
        PYTHON_CMD="python3.11"
        print_success "Using Python 3.11 (exact CI match)"
    else
        print_warning "Python 3.11 not found, checking for alternatives..."

        # Try to install python3.11 if possible
        if command -v apt-get &> /dev/null && [ "$SKIP_SYSTEM_PACKAGES" = false ]; then
            print_info "Attempting to install Python 3.11..."
            if sudo apt-get update && sudo apt-get install -y python3.11 python3.11-venv python3.11-dev; then
                PYTHON_CMD="python3.11"
                print_success "Python 3.11 installed successfully"
            else
                print_error "Failed to install Python 3.11"
                PYTHON_CMD="python3"
                print_warning "Falling back to default Python 3"
            fi
        else
            PYTHON_CMD="python3"
            print_warning "Using default Python 3 (may cause CI differences)"
        fi
    fi
else
    PYTHON_CMD="python$PYTHON_VERSION"
    if ! command -v "$PYTHON_CMD" &> /dev/null; then
        print_error "Python $PYTHON_VERSION not found"
        exit 1
    fi
fi

print_info "Python command: $PYTHON_CMD"
print_info "Python version: $($PYTHON_CMD --version)"

# Step 4: Virtual Environment Creation (CI-exact)
print_step "4. Virtual Environment Creation (CI-exact)"

print_isolate "Creating fresh virtual environment..."
$PYTHON_CMD -m venv venv

# Activate virtual environment
print_isolate "Activating virtual environment..."
source venv/bin/activate

# Verify isolation
if [ "$VIRTUAL_ENV" != "$(pwd)/venv" ]; then
    print_error "Virtual environment activation failed"
    exit 1
fi

print_success "Virtual environment isolated and activated"

# Step 5: Dependency Installation (Exact CI Sequence)
print_step "5. Dependency Installation (Exact CI Sequence)"

# Clear any pip cache to ensure fresh installs
print_isolate "Clearing pip cache..."
pip cache purge 2>/dev/null || true

# Step 5.1: Upgrade pip and install resolver tools (CI-exact)
print_info "Step 5.1: Upgrading pip and installing resolver tools..."
python -m pip install --upgrade pip setuptools wheel --no-cache-dir

# Step 5.2: Pin grpcio versions (CI-exact)
print_info "Step 5.2: Installing pinned grpcio versions..."
pip install grpcio==1.73.1 grpcio-status==1.73.1 --no-cache-dir

# Step 5.3: Install protobuf (CI-exact)
print_info "Step 5.3: Installing protobuf..."
pip install protobuf==4.25.3 --no-cache-dir

# Step 5.4: Install project requirements (CI-exact)
print_info "Step 5.4: Installing project requirements..."
if [ -f "mvp_site/requirements.txt" ]; then
    pip install -r mvp_site/requirements.txt --no-cache-dir
else
    print_error "Requirements file not found: mvp_site/requirements.txt"
    exit 1
fi

print_success "Dependencies installed with CI-exact sequence"

# Step 6: vpython Verification (CI-exact)
print_step "6. vpython Verification (CI-exact)"

chmod +x vpython
if ./vpython --version; then
    print_success "vpython verification successful"
else
    print_error "vpython verification failed"
    exit 1
fi

# Step 7: Environment Verification and Comparison
print_step "7. Environment Verification and Comparison"

print_info "Final environment state:"
print_info "  Working directory: $(pwd)"
print_info "  Python executable: $(which python)"
print_info "  Python version: $(python --version)"
print_info "  Virtual environment: $VIRTUAL_ENV"
print_info "  Pip version: $(pip --version)"

# Compare with original environment
print_info "Environment changes from original:"
env | sort > /tmp/final_env_$TIMESTAMP.txt
diff /tmp/original_env_$TIMESTAMP.txt /tmp/final_env_$TIMESTAMP.txt || true

# Step 8: Test Execution (CI-exact)
print_step "8. Test Execution (CI-exact path)"

print_info "Making run_tests.sh executable..."
chmod +x run_tests.sh

print_info "Executing tests with CI-exact environment..."
export TESTING=true

# Run tests and capture detailed output
print_info "Running: ./run_tests.sh"
if ./run_tests.sh 2>&1 | tee /tmp/test_output_$TIMESTAMP.txt; then
    print_success "=================================================================="
    print_success "✅ ALL TESTS PASSED - NO CI FAILURE REPRODUCED"
    print_success "=================================================================="
    print_info "This suggests the CI failure may be due to:"
    print_info "  1. Timing issues specific to CI environment"
    print_info "  2. External service dependencies not available in CI"
    print_info "  3. Resource constraints in CI environment"
    print_info "  4. Race conditions in parallel test execution"
    test_exit_code=0
else
    print_error "=================================================================="
    print_error "❌ TESTS FAILED - CI FAILURE SUCCESSFULLY REPRODUCED"
    print_error "=================================================================="
    print_info "CI failure has been reproduced locally!"
    print_info "This indicates the failure is reproducible and can be debugged locally."
    print_info "Test output saved to: /tmp/test_output_$TIMESTAMP.txt"
    test_exit_code=1
fi

# Step 9: Cleanup and Results
print_step "9. Cleanup and Results"

if [ "$KEEP_ISOLATION_DIR" = true ] && [ "$ISOLATION_MODE" = "full" ]; then
    print_info "Isolation directory preserved: $ISOLATION_DIR"
elif [ "$ISOLATION_MODE" = "full" ]; then
    print_info "Cleaning up isolation directory..."
    cd "$PROJECT_ROOT"
    rm -rf "$ISOLATION_DIR"
fi

# Provide debugging information
print_info "Debugging information:"
print_info "  Test output: /tmp/test_output_$TIMESTAMP.txt"
print_info "  Original env: /tmp/original_env_$TIMESTAMP.txt"
print_info "  Final env: /tmp/final_env_$TIMESTAMP.txt"

if [ $test_exit_code -eq 0 ]; then
    print_success "CI FAILURE REPRODUCER: Tests passed - failure not reproduced"
    print_info "The CI failure may be environment-specific or timing-related"
else
    print_error "CI FAILURE REPRODUCER: Tests failed - failure reproduced successfully"
    print_info "You can now debug the failure in the isolated environment"
fi

# Final recommendations
print_info "Next steps:"
if [ $test_exit_code -eq 0 ]; then
    print_info "  1. Check CI logs for specific error messages"
    print_info "  2. Look for timing or resource-related issues"
    print_info "  3. Consider running tests with different concurrency settings"
    print_info "  4. Check for external service dependencies"
else
    print_info "  1. Examine test output in /tmp/test_output_$TIMESTAMP.txt"
    print_info "  2. Debug failing tests in the isolated environment"
    print_info "  3. Compare environment differences if needed"
    print_info "  4. Fix issues and re-run this script to verify"
fi

exit $test_exit_code
