#!/usr/bin/env bash
# Master dispatcher for Claude commands
# Routes commands to appropriate implementation (shell or Python)

set -euo pipefail

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMMANDS_DIR="$SCRIPT_DIR"

# Performance-critical commands (shell)
SHELL_COMMANDS=(
    "header"
    "integrate" 
    "resolve_conflicts"
    "pushlite"
    "pushl"
)

# Core Python commands
PYTHON_COMMANDS=(
    "execute"
    "e"
    "test"
    "testui"
    "testuif" 
    "testhttp"
    "testhttpf"
    "testi"
    "tester"
)

# Function to check if command should use shell
is_shell_command() {
    local cmd="$1"
    for shell_cmd in "${SHELL_COMMANDS[@]}"; do
        if [[ "$cmd" == "$shell_cmd" ]]; then
            return 0
        fi
    done
    return 1
}

# Function to check if command should use Python
is_python_command() {
    local cmd="$1"
    for python_cmd in "${PYTHON_COMMANDS[@]}"; do
        if [[ "$cmd" == "$python_cmd" ]]; then
            return 0
        fi
    done
    return 1
}

# Function to route to shell script
route_to_shell() {
    local cmd="$1"
    shift
    
    # Map commands to actual shell scripts
    case "$cmd" in
        "header")
            exec "$SCRIPT_DIR/../claude_command_scripts/git-header.sh" "$@"
            ;;
        "integrate")
            exec "$SCRIPT_DIR/../integrate.sh" "$@"
            ;;
        "pushlite"|"pushl")
            exec "$SCRIPT_DIR/../claude_command_scripts/commands/pushlite.sh" "$@"
            ;;
        *)
            # Look for shell script in commands directory
            if [[ -x "$COMMANDS_DIR/${cmd}.sh" ]]; then
                exec "$COMMANDS_DIR/${cmd}.sh" "$@"
            else
                echo "Error: Shell command '$cmd' not found"
                exit 1
            fi
            ;;
    esac
}

# Function to route to Python CLI
route_to_python() {
    local cmd="$1"
    shift
    
    # Map legacy commands to new unified commands
    case "$cmd" in
        "execute"|"e")
            exec python3 "$COMMANDS_DIR/core/execute.py" "$@"
            ;;
        "test")
            exec python3 "$COMMANDS_DIR/core/test.py" "$@"
            ;;
        # Legacy test command aliases
        "testui")
            exec python3 "$COMMANDS_DIR/core/test.py" ui --mock "$@"
            ;;
        "testuif")
            exec python3 "$COMMANDS_DIR/core/test.py" ui --real "$@"
            ;;
        "testhttp")
            exec python3 "$COMMANDS_DIR/core/test.py" http --mock "$@"
            ;;
        "testhttpf")
            exec python3 "$COMMANDS_DIR/core/test.py" http --real "$@"
            ;;
        "testi")
            exec python3 "$COMMANDS_DIR/core/test.py" integration "$@"
            ;;
        "tester")
            exec python3 "$COMMANDS_DIR/core/test.py" end2end "$@"
            ;;
        *)
            # Try the main CLI
            exec python3 "$COMMANDS_DIR/core/cli.py" "$cmd" "$@"
            ;;
    esac
}

# Main routing logic
main() {
    if [[ $# -eq 0 ]]; then
        echo "Claude Commands Dispatcher"
        echo "Usage: $0 <command> [arguments...]"
        echo ""
        echo "Performance-critical commands (shell):"
        printf "  %s\n" "${SHELL_COMMANDS[@]}"
        echo ""
        echo "Core workflow commands (Python):"
        printf "  %s\n" "${PYTHON_COMMANDS[@]}"
        echo ""
        echo "For help with a specific command:"
        echo "  $0 <command> --help"
        exit 0
    fi
    
    local command="$1"
    shift
    
    # Route based on command type
    if is_shell_command "$command"; then
        route_to_shell "$command" "$@"
    elif is_python_command "$command"; then
        route_to_python "$command" "$@"
    else
        # Default to Python CLI for unknown commands
        route_to_python "$command" "$@"
    fi
}

main "$@"