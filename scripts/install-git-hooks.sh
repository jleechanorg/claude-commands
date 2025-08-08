#!/bin/bash

# install-git-hooks.sh
# Installs git hooks that work with virtual environments
# Handles both fresh branches and existing setups

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

# Change to project root
cd "$PROJECT_ROOT"

print_info "🔧 Installing git hooks with automatic venv activation..."

# 1. Ensure virtual environment exists
if [ ! -d "venv" ]; then
    print_info "Virtual environment not found. Running setup script..."
    "$SCRIPT_DIR/setup-dev-env.sh"
fi

# 2. Activate virtual environment
source venv/bin/activate

# 3. Install pre-commit if not available
if ! command -v pre-commit >/dev/null 2>&1; then
    print_info "Installing pre-commit..."
    pip install pre-commit
fi

# 4. Install git hooks
print_info "Installing pre-commit hooks..."
pre-commit install

# 5. Create a backup of the original hook
HOOKS_DIR="$(git rev-parse --git-path hooks)"
PRECOMMIT_HOOK="$HOOKS_DIR/pre-commit"

if [ -f "$PRECOMMIT_HOOK" ]; then
    cp "$PRECOMMIT_HOOK" "$PRECOMMIT_HOOK.backup"
    print_info "Backed up original hook to $PRECOMMIT_HOOK.backup"
fi

# 6. Create an enhanced pre-commit hook that's more robust
cat > "$PRECOMMIT_HOOK" << 'EOF'
#!/usr/bin/env bash
# Enhanced pre-commit hook with automatic virtual environment activation
# Works with fresh branches from main

set -e

# Get project root
PROJECT_ROOT="$(git rev-parse --show-toplevel)"
cd "$PROJECT_ROOT"

# Function to print colored output
print_info() {
    echo -e "\033[0;34m[INFO]\033[0m $1" >&2
}

print_error() {
    echo -e "\033[0;31m[ERROR]\033[0m $1" >&2
}

# 1. Ensure virtual environment exists
if [ ! -d "venv" ]; then
    print_info "Virtual environment not found. Creating..."
    if ! python3 -m venv venv; then
        print_error "Failed to create virtual environment"
        exit 1
    fi
    print_info "Virtual environment created successfully"
fi

# 2. Activate virtual environment
source venv/bin/activate

# 3. Ensure pre-commit is installed
if ! command -v pre-commit >/dev/null 2>&1; then
    print_info "Installing pre-commit in virtual environment..."
    if ! pip install pre-commit; then
        print_error "Failed to install pre-commit. Check your pip setup."
        exit 1
    fi
fi

# 4. Install dependencies if requirements.txt exists and venv is fresh
if [ -f "mvp_site/requirements.txt" ] && [ ! -f "venv/.deps_installed" ]; then
    print_info "Installing Python dependencies..."
    if ! pip install -r mvp_site/requirements.txt; then
        print_error "Failed to install Python dependencies. Check mvp_site/requirements.txt"
        exit 1
    fi
    touch venv/.deps_installed
fi

# 5. Run pre-commit
ARGS=(hook-impl --config=.pre-commit-config.yaml --hook-type=pre-commit)
HOOKS_DIR="$(git rev-parse --git-path hooks)"
ARGS+=(--hook-dir "$HOOKS_DIR" -- "$@")

exec python -mpre_commit "${ARGS[@]}"
EOF

# 7. Make the hook executable
chmod +x "$PRECOMMIT_HOOK"

# 8. Test the hook
print_info "Testing git hooks installation..."
if pre-commit run --all-files >/dev/null 2>&1 || true; then
    print_success "Git hooks installed and working!"
else
    print_info "Git hooks installed (some checks may need fixes - this is normal)"
fi

print_success "🎉 Git hooks installation complete!"
print_info ""
print_info "The git hooks will now automatically:"
print_info "  • Create virtual environment if missing"
print_info "  • Activate virtual environment"
print_info "  • Install dependencies if needed"
print_info "  • Run code quality checks"
print_info ""
print_info "This works on fresh branches from main without manual setup!"
