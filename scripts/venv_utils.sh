#!/bin/bash
# venv_utils.sh - Common virtual environment utilities
# Source this file to use: source scripts/venv_utils.sh

# Get the project root directory
if [ -z "$PROJECT_ROOT" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
fi

# Color output functions
print_info() {
    echo -e "\033[0;34m[INFO]\033[0m $1"
}

print_success() {
    echo -e "\033[0;32m[SUCCESS]\033[0m $1"
}

print_error() {
    echo -e "\033[0;31m[ERROR]\033[0m $1"
}

# Function to setup virtual environment if not exists
setup_venv() {
    local venv_path="${1:-$PROJECT_ROOT/venv}"

    # Check if venv exists and is valid
    if [ -d "$venv_path" ] && [ -f "$venv_path/bin/activate" ]; then
        # Venv exists, just activate it
        source "$venv_path/bin/activate"
        return 0
    fi

    # Venv doesn't exist or is corrupted, create it
    print_info "Virtual environment not found or invalid at $venv_path"
    print_info "Creating virtual environment..."

    # Remove corrupted venv if it exists
    if [ -d "$venv_path" ]; then
        print_info "Removing corrupted venv directory..."
        rm -rf "$venv_path"
    fi

    # Create new venv
    if python3 -m venv "$venv_path"; then
        print_success "Virtual environment created successfully"
        source "$venv_path/bin/activate"

        # Upgrade pip to latest version
        print_info "Upgrading pip..."
        python -m pip install --upgrade pip --quiet

        # Install requirements if requirements.txt exists
        if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
            print_info "Installing requirements from requirements.txt..."
            if pip install -r "$PROJECT_ROOT/requirements.txt" --quiet; then
                print_success "Requirements installed successfully"
            else
                print_error "Failed to install some requirements, but continuing..."
            fi
        fi

        # Install mvp_site requirements if they exist
        if [ -f "$PROJECT_ROOT/mvp_site/requirements.txt" ]; then
            print_info "Installing mvp_site requirements..."
            if pip install -r "$PROJECT_ROOT/mvp_site/requirements.txt" --quiet; then
                print_success "MVP site requirements installed successfully"
            else
                print_error "Failed to install some MVP requirements, but continuing..."
            fi
        fi

        return 0
    else
        print_error "Failed to create virtual environment"
        print_error "Please ensure python3-venv is installed: sudo apt-get install python3-venv"
        return 1
    fi
}

# Function to ensure venv is active
ensure_venv() {
    if [ -z "$VIRTUAL_ENV" ]; then
        setup_venv "$@"
    else
        print_success "Virtual environment is already active: $VIRTUAL_ENV"
    fi
}
