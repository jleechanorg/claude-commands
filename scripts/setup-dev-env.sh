#!/bin/bash

# setup-dev-env.sh
# Sets up development environment for fresh branches from main
# Handles virtual environment creation, dependencies, and git hooks

set -euo pipefail

# Get the project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Color functions
print_info() {
    echo -e "\033[0;34m[INFO]\033[0m $1"
}

print_success() {
    echo -e "\033[0;32m[SUCCESS]\033[0m $1"
}

print_error() {
    echo -e "\033[0;31m[ERROR]\033[0m $1"
}

print_warning() {
    echo -e "\033[1;33m[WARN]\033[0m $1"
}

# Change to project root
cd "$PROJECT_ROOT"

print_info "🚀 Setting up development environment..."

# 1. Create virtual environment if needed
if [ ! -d "venv" ]; then
    print_info "Creating virtual environment..."
    if ! python3 -m venv venv; then
        print_error "Failed to create virtual environment"
        exit 1
    fi
    print_success "Virtual environment created"
else
    print_info "Virtual environment already exists"
fi

# 2. Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate

# 3. Upgrade pip
print_info "Upgrading pip..."
pip install --upgrade pip

# 4. Install requirements
if [ -f "mvp_site/requirements.txt" ]; then
    print_info "Installing Python dependencies..."
    pip install -r mvp_site/requirements.txt
    print_success "Dependencies installed"
else
    print_warning "mvp_site/requirements.txt not found, skipping dependency installation"
fi

# 5. Install pre-commit
print_info "Installing pre-commit..."
if ! command -v pre-commit >/dev/null 2>&1; then
    print_info "Installing pre-commit in virtual environment..."
    pip install pre-commit
else
    print_info "pre-commit already available"
fi

# 6. Install pre-commit hooks
print_info "Installing pre-commit hooks..."
pre-commit install
print_success "Pre-commit hooks installed"

# 7. Verify setup
print_info "Verifying setup..."

# Check if git hooks are working
if [ -f "$(git rev-parse --git-path hooks/pre-commit)" ]; then
    print_success "Git hooks are properly configured"
else
    print_warning "Git hooks may not be properly configured"
fi

# Check if venv has required packages
if python -c "import coverage" >/dev/null 2>&1; then
    print_success "Coverage tool is available"
else
    print_info "Installing coverage tool..."
    if ! python -m pip install --upgrade --disable-pip-version-check coverage; then
        print_error "Failed to install coverage. Please check your pip setup."
        exit 1
    fi
    if python -c "import coverage" >/dev/null 2>&1; then
        print_success "Coverage tool installed"
    else
        print_error "Coverage still not importable after installation."
        exit 1
    fi
fi

print_success "🎉 Development environment setup complete!"
print_info ""
print_info "To activate the environment manually in the future:"
print_info "  source venv/bin/activate"
print_info ""
print_info "To run tests:"
print_info "  ./run_tests.sh"
print_info ""
print_info "Git hooks will automatically run with the virtual environment."
