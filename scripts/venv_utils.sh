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

    choose_venv_python() {
        # Allow override for CI or local workflows.
        if [ -n "${VENV_PYTHON:-}" ] && command -v "$VENV_PYTHON" >/dev/null 2>&1; then
            echo "$VENV_PYTHON"
            return 0
        fi

        # Prefer a Python >= 3.10 because some dependencies (e.g., mcp) require it.
        local candidates=(
            python
            python3
            python3.12
            python3.11
            python3.10
        )

        local best=""
        local best_major=0
        local best_minor=0

        for candidate in "${candidates[@]}"; do
            if ! command -v "$candidate" >/dev/null 2>&1; then
                continue
            fi

            local major_minor
            major_minor="$(
                "$candidate" -c 'import sys; print(f"{sys.version_info[0]} {sys.version_info[1]}")' 2>/dev/null
            )"
            if [ -z "$major_minor" ]; then
                continue
            fi

            local major minor
            major="$(echo "$major_minor" | awk '{print $1}')"
            minor="$(echo "$major_minor" | awk '{print $2}')"

            # Require >= 3.10
            if [ "$major" -lt 3 ] || { [ "$major" -eq 3 ] && [ "$minor" -lt 10 ]; }; then
                continue
            fi

            if [ "$major" -gt "$best_major" ] || { [ "$major" -eq "$best_major" ] && [ "$minor" -gt "$best_minor" ]; }; then
                best="$candidate"
                best_major="$major"
                best_minor="$minor"
            fi
        done

        if [ -n "$best" ]; then
            echo "$best"
            return 0
        fi

        # Fall back to python3 (historical default) if nothing suitable is found.
        echo "python3"
        return 0
    }

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
    local venv_python
    venv_python="$(choose_venv_python)"
    print_info "Using python interpreter for venv: $venv_python"

    if "$venv_python" -m venv "$venv_path"; then
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

        # Install genesis requirements if they exist
        if [ -f "$PROJECT_ROOT/genesis/requirements.txt" ]; then
            print_info "Installing genesis requirements..."
            if pip install -r "$PROJECT_ROOT/genesis/requirements.txt" --quiet; then
                print_success "Genesis requirements installed successfully"
            else
                print_error "Failed to install some Genesis requirements, but continuing..."
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
