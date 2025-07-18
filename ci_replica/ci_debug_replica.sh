#!/bin/bash

# CI Debug Replica Script for WorldArchitect.AI
# Enhanced version with debugging capabilities and environment isolation
# Replicates GitHub Actions CI environment with maximum fidelity

set -euo pipefail  # Exit on error, undefined var, or failed pipeline

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
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

print_debug() {
    echo -e "${MAGENTA}[DEBUG]${NC} $1"
}

# Parse command line arguments
DEBUG_MODE=false
VERBOSE=false
CLEAN_MODE=false
PRESERVE_VENV=false

for arg in "$@"; do
    case $arg in
        --debug)
            DEBUG_MODE=true
            ;;
        --verbose)
            VERBOSE=true
            ;;
        --clean)
            CLEAN_MODE=true
            ;;
        --preserve-venv)
            PRESERVE_VENV=true
            ;;
        --help)
            echo "CI Debug Replica Script"
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --debug           Enable debug mode with detailed output"
            echo "  --verbose         Enable verbose logging"
            echo "  --clean           Clean all temporary files and caches"
            echo "  --preserve-venv   Don't recreate virtual environment if it exists"
            echo "  --help            Show this help message"
            exit 0
            ;;
        *)
            print_warning "Unknown argument: $arg"
            ;;
    esac
done

# Store original working directory
ORIGINAL_DIR=$(pwd)
PROJECT_ROOT="$(cd "$(dirname "$0")"; pwd)"

print_header "WorldArchitect.AI CI Debug Replica"
print_info "Enhanced CI environment replication with debugging capabilities"
print_info "Based on: .github/workflows/test.yml"
print_info "Project root: $PROJECT_ROOT"

if [ "$DEBUG_MODE" = true ]; then
    print_debug "Debug mode enabled"
    set -x  # Enable command tracing
fi

# Step 1: Environment Analysis and Cleanup
print_step "Step 1: Environment Analysis and Cleanup"

# Save original environment
if [ "$DEBUG_MODE" = true ]; then
    print_debug "Saving original environment..."
    env | sort > /tmp/ci_replica_original_env.txt
    print_debug "Original environment saved to /tmp/ci_replica_original_env.txt"
fi

# Clear environment variables that might interfere (comprehensive)
print_info "Clearing potentially interfering environment variables..."
unset PYTHONPATH
unset PYTHONHOME
unset VIRTUAL_ENV
unset CONDA_DEFAULT_ENV
unset CONDA_PREFIX
unset PIPENV_ACTIVE
unset POETRY_ACTIVE
unset PIP_USER
unset PYTHONSTARTUP
unset PYTHONOPTIMIZE
unset PYTHONDONTWRITEBYTECODE
unset PYTHONHASHSEED

# Set CI-specific environment variables (comprehensive)
print_info "Setting CI-specific environment variables..."
export CI=true
export GITHUB_ACTIONS=true
export TESTING=true
export TEST_MODE=mock
export DEBUG=false
export RUNNER_OS=Linux
export RUNNER_ARCH=X64

# Additional environment variables that CI might set
export DEBIAN_FRONTEND=noninteractive
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
export TZ=UTC

# CI-specific paths
export HOME=/home/runner
export GITHUB_WORKSPACE=$PROJECT_ROOT
export GITHUB_ENV=/tmp/github_env
export GITHUB_PATH=/tmp/github_path

# Create CI-like directory structure
mkdir -p /tmp/github_env /tmp/github_path

if [ "$DEBUG_MODE" = true ]; then
    print_debug "CI environment variables set:"
    env | grep -E "(CI|GITHUB|TESTING|DEBUG|RUNNER)" | sort
fi

# Step 2: System Information and Compatibility Check
print_step "Step 2: System Information and Compatibility Check"

print_info "System information:"
echo "  OS: $(uname -s) $(uname -r) $(uname -m)"
echo "  Hostname: $(hostname)"
echo "  User: $(whoami)"
echo "  Date: $(date)"
echo "  Timezone: $(date +%Z)"

# Check for Python 3.11 availability
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
    print_success "Python 3.11 found (matches CI exactly)"
    PYTHON_VERSION=$($PYTHON_CMD --version)
    echo "  Python: $PYTHON_VERSION"
else
    PYTHON_CMD="python3"
    PYTHON_VERSION=$($PYTHON_CMD --version)
    print_warning "Python 3.11 not found, using $PYTHON_VERSION"
    print_warning "CI uses Python 3.11, results may differ significantly"
    
    # Check Python version compatibility
    if $PYTHON_CMD -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
        print_info "Python version is compatible (3.8+)"
    else
        print_error "Python version is too old. Minimum required: 3.8"
        exit 1
    fi
fi

# Check for required system packages
print_info "Checking system dependencies..."
required_packages=("git" "curl" "wget")
for pkg in "${required_packages[@]}"; do
    if command -v $pkg &> /dev/null; then
        print_success "$pkg: Available"
    else
        print_warning "$pkg: Not found"
    fi
done

# Step 3: Clean Virtual Environment Setup
print_step "Step 3: Clean Virtual Environment Setup"

cd "$PROJECT_ROOT"

# Handle virtual environment based on options
if [ "$PRESERVE_VENV" = true ] && [ -d "$PROJECT_ROOT/venv" ]; then
    print_info "Preserving existing virtual environment (--preserve-venv)"
    if [ -f "$PROJECT_ROOT/venv/bin/activate" ]; then
        print_success "Existing virtual environment found and preserved"
    else
        print_error "Virtual environment directory exists but activate script missing"
        print_info "Recreating virtual environment..."
        rm -rf "$PROJECT_ROOT/venv"
        $PYTHON_CMD -m venv venv
    fi
else
    # Remove existing virtual environment to start fresh (like CI)
    if [ -d "$PROJECT_ROOT/venv" ]; then
        print_info "Removing existing virtual environment..."
        rm -rf "$PROJECT_ROOT/venv"
    fi
    
    # Create fresh virtual environment (exactly like CI)
    print_info "Creating fresh virtual environment with $PYTHON_CMD..."
    $PYTHON_CMD -m venv venv
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate

# Verify virtual environment activation
if [ "$VIRTUAL_ENV" != "$PROJECT_ROOT/venv" ]; then
    print_error "Virtual environment activation failed"
    print_error "Expected: $PROJECT_ROOT/venv"
    print_error "Actual: $VIRTUAL_ENV"
    exit 1
fi

print_success "Virtual environment activated: $VIRTUAL_ENV"

if [ "$DEBUG_MODE" = true ]; then
    print_debug "Python executable: $(which python)"
    print_debug "Pip executable: $(which pip)"
    print_debug "Virtual environment python: $(python --version)"
fi

# Step 4: Dependency Installation (CI-exact sequence)
print_step "Step 4: Dependency Installation (CI-exact sequence)"

# Cache pip dependencies (simulate CI cache)
print_info "Setting up pip cache..."
export PIP_CACHE_DIR=/tmp/pip-cache
mkdir -p $PIP_CACHE_DIR

# Upgrade pip and install resolver tools (matches CI exactly)
print_info "Upgrading pip and installing resolver tools..."
if [ "$VERBOSE" = true ]; then
    python -m pip install --upgrade pip setuptools wheel --verbose
else
    python -m pip install --upgrade pip setuptools wheel
fi

# Pin grpcio and grpcio-status to compatible versions (matches CI exactly)
print_info "Installing pinned grpcio versions..."
if [ "$VERBOSE" = true ]; then
    pip install grpcio==1.73.1 grpcio-status==1.73.1 --verbose
else
    pip install grpcio==1.73.1 grpcio-status==1.73.1
fi

# Install protobuf first to avoid conflicts (matches CI exactly)
print_info "Installing protobuf (conflict prevention)..."
if [ "$VERBOSE" = true ]; then
    pip install protobuf==4.25.3 --verbose
else
    pip install protobuf==4.25.3
fi

# Install project requirements (matches CI exactly)
print_info "Installing project requirements..."
if [ -f "mvp_site/requirements.txt" ]; then
    if [ "$VERBOSE" = true ]; then
        pip install -r mvp_site/requirements.txt --verbose
    else
        pip install -r mvp_site/requirements.txt
    fi
    print_success "Requirements installed successfully"
else
    print_error "Requirements file not found: mvp_site/requirements.txt"
    exit 1
fi

# Step 5: Verify vpython works (matches CI exactly)
print_step "Step 5: Verify vpython Script"

print_info "Making vpython executable..."
chmod +x vpython

print_info "Testing vpython functionality..."
if ./vpython --version; then
    print_success "vpython verification successful"
else
    print_error "vpython verification failed"
    exit 1
fi

# Step 6: Detailed Environment Verification
print_step "Step 6: Detailed Environment Verification"

print_info "Installed package versions:"
python -c "
import sys
import pkg_resources

# Key packages to check
packages = [
    'flask', 'gunicorn', 'firebase-admin', 'google-cloud-firestore', 
    'protobuf', 'google-genai', 'flask-cors', 'selenium', 'requests'
]

print('  Python:', sys.version.split()[0])
print('  Pip:', end=' ')
try:
    import pip
    print(pip.__version__)
except:
    print('version unknown')

for pkg in packages:
    try:
        version = pkg_resources.get_distribution(pkg).version
        print(f'  {pkg}: {version}')
    except pkg_resources.DistributionNotFound:
        print(f'  {pkg}: Not installed')
    except Exception as e:
        print(f'  {pkg}: Error - {e}')
"

# Check for potential conflicts
print_info "Checking for potential package conflicts..."
pip check || print_warning "Package conflicts detected (may be harmless)"

# Step 7: Pre-test Environment Verification
print_step "Step 7: Pre-test Environment Verification"

# Check if we're in the right directory
if [ ! -d "mvp_site" ]; then
    print_error "mvp_site directory not found. This script must be run from project root."
    exit 1
fi

# Check critical files exist
critical_files=("run_tests.sh" "mvp_site/requirements.txt" "vpython")
for file in "${critical_files[@]}"; do
    if [ ! -f "$file" ]; then
        print_error "Critical file missing: $file"
        exit 1
    fi
done

# Check directory structure
print_info "Verifying directory structure..."
expected_dirs=("mvp_site" "mvp_site/tests" ".github" ".github/workflows")
for dir in "${expected_dirs[@]}"; do
    if [ -d "$dir" ]; then
        print_success "$dir: Present"
    else
        print_warning "$dir: Missing"
    fi
done

print_success "Pre-test verification completed"

# Step 8: Test Execution with CI-exact Environment
print_step "Step 8: Test Execution with CI-exact Environment"

print_info "Making run_tests.sh executable..."
chmod +x run_tests.sh

print_info "Running tests using project's run_tests.sh script..."
print_info "This matches the exact CI execution path"

# Set environment variables exactly like CI
export TESTING=true

# Create test results directory (like CI)
mkdir -p mvp_site/test-results

# Execute tests exactly like CI does
print_info "Executing: ./run_tests.sh"
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
    print_error "Note: Test failures may be due to:"
    print_error "  - Missing local services (e.g., test server)"
    print_error "  - Test isolation issues"
    print_error "  - Timing-sensitive tests"
    print_error "  - Environment differences despite replication"
    test_exit_code=1
fi

# Step 9: Post-test Analysis and Cleanup
print_step "Step 9: Post-test Analysis and Cleanup"

if [ "$DEBUG_MODE" = true ]; then
    print_debug "Saving final environment state..."
    env | sort > /tmp/ci_replica_final_env.txt
    print_debug "Final environment saved to /tmp/ci_replica_final_env.txt"
    
    if [ -f /tmp/ci_replica_original_env.txt ]; then
        print_debug "Environment changes:"
        diff /tmp/ci_replica_original_env.txt /tmp/ci_replica_final_env.txt || true
    fi
fi

# Clean up temporary files if requested
if [ "$CLEAN_MODE" = true ]; then
    print_info "Cleaning temporary files..."
    rm -rf /tmp/pip-cache
    rm -rf /tmp/github_env
    rm -rf /tmp/github_path
    rm -f /tmp/ci_replica_*.txt
    print_success "Temporary files cleaned"
fi

# Final results
print_step "Final Results"

if [ $test_exit_code -eq 0 ]; then
    print_success "CI Debug Replica: ALL TESTS PASSED ✅"
    print_info "Your local environment successfully replicates CI behavior"
else
    print_error "CI Debug Replica: TESTS FAILED ❌"
    print_info "This indicates either:"
    print_info "  1. Genuine test failures that would also fail in CI"
    print_info "  2. Local environment differences despite replication attempts"
    print_info "  3. Missing system dependencies or services"
fi

print_info "Environment replication summary:"
print_info "  Virtual environment: $PROJECT_ROOT/venv"
print_info "  Python version: $PYTHON_VERSION"
print_info "  CI environment variables: Set"
print_info "  Dependencies: Installed with CI-exact sequence"
print_info "  Test execution: CI-exact path"

print_info "To use this environment later:"
print_info "  source $PROJECT_ROOT/venv/bin/activate"
print_info "  export TESTING=true"

if [ "$DEBUG_MODE" = true ]; then
    print_debug "Debug files available:"
    print_debug "  Original env: /tmp/ci_replica_original_env.txt"
    print_debug "  Final env: /tmp/ci_replica_final_env.txt"
fi

# Return to original directory
cd "$ORIGINAL_DIR"

if [ "$DEBUG_MODE" = true ]; then
    set +x  # Disable command tracing
fi

exit $test_exit_code