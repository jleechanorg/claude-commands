#!/bin/bash

# venv-pre-commit.sh
# Wrapper script that automatically activates virtual environment before running pre-commit
# This ensures pre-commit hooks work on fresh branches without manual venv activation

set -e

# Get the project root directory (where this script is located relative to scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Function to print colored output
print_info() {
    echo -e "\033[0;34m[INFO]\033[0m $1"
}

print_success() {
    echo -e "\033[0;32m[SUCCESS]\033[0m $1"
}

print_error() {
    echo -e "\033[0;31m[ERROR]\033[0m $1"
}

# Change to project root
cd "$PROJECT_ROOT"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_info "Virtual environment not found. Creating..."
    if ! python3 -m venv venv; then
        print_error "Failed to create virtual environment"
        exit 1
    fi
    print_success "Virtual environment created successfully"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate

# Check if pre-commit is installed
if ! command -v pre-commit >/dev/null 2>&1; then
    print_info "pre-commit not found. Installing..."
    if ! pip install pre-commit; then
        print_error "Failed to install pre-commit"
        exit 1
    fi
    print_success "pre-commit installed successfully"
fi

# Install pre-commit hooks if not already installed
if [ ! -f .git/hooks/pre-commit ]; then
    print_info "Installing pre-commit hooks..."
    if ! pre-commit install; then
        print_error "Failed to install pre-commit hooks"
        exit 1
    fi
    print_success "Pre-commit hooks installed successfully"
fi

# Run pre-commit with all passed arguments
print_info "Running pre-commit..."
exec pre-commit "$@"
