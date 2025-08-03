#!/bin/bash

# CI Replica Launcher Script
# Interactive launcher to help users choose the right CI replication script

set -euo pipefail

# Initialize exit code tracking
SCRIPT_EXIT_CODE=0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${CYAN}================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}================================${NC}"
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

print_header "CI Environment Replica Launcher"
print_info "This launcher helps you choose the right CI replication script"
echo

# Check if scripts exist
scripts=(
    "ci_local_replica.sh"
    "ci_debug_replica.sh"
    "ci_failure_reproducer.sh"
)

missing_scripts=()
for script in "${scripts[@]}"; do
    if [ ! -f "$script" ]; then
        missing_scripts+=("$script")
    fi
done

if [ ${#missing_scripts[@]} -gt 0 ]; then
    print_error "Missing scripts:"
    for script in "${missing_scripts[@]}"; do
        echo "  - $script"
    done
    exit 1
fi

# Make scripts executable
chmod +x "${scripts[@]}"

# Interactive menu
echo "Available CI replication scripts:"
echo
echo "1. Basic CI Replication (ci_local_replica.sh)"
echo "   - Quick and simple CI environment replication"
echo "   - Good for most CI debugging needs"
echo "   - Recommended for first-time users"
echo
echo "2. Debug CI Replication (ci_debug_replica.sh)"
echo "   - Advanced debugging with verbose output"
echo "   - Environment comparison and analysis"
echo "   - Preserve debugging information"
echo "   - Good for complex CI issues"
echo
echo "3. Maximum Isolation Reproducer (ci_failure_reproducer.sh)"
echo "   - Complete isolation from local environment"
echo "   - Best for reproducing stubborn CI failures"
echo "   - Creates temporary isolated environment"
echo "   - Recommended for hard-to-reproduce failures"
echo
echo "4. Show help for a specific script"
echo "5. Exit"
echo

while true; do
    echo -n "Please choose an option (1-5): "
    read -r choice

    case $choice in
        1)
            print_info "Running Basic CI Replication..."
            echo
            ./ci_local_replica.sh
            SCRIPT_EXIT_CODE=$?
            break
            ;;
        2)
            print_info "Debug CI Replication options:"
            echo "  a. Standard debug mode"
            echo "  b. Verbose debug mode"
            echo "  c. Clean debug mode"
            echo "  d. Preserve virtual environment"
            echo "  e. Custom options"
            echo
            echo -n "Choose debug option (a-e): "
            read -r debug_choice

            case $debug_choice in
                a)
                    print_info "Running Debug CI Replication (standard)..."
                    ./ci_debug_replica.sh --debug
                    SCRIPT_EXIT_CODE=$?
                    ;;
                b)
                    print_info "Running Debug CI Replication (verbose)..."
                    ./ci_debug_replica.sh --debug --verbose
                    SCRIPT_EXIT_CODE=$?
                    ;;
                c)
                    print_info "Running Debug CI Replication (clean)..."
                    ./ci_debug_replica.sh --debug --clean
                    SCRIPT_EXIT_CODE=$?
                    ;;
                d)
                    print_info "Running Debug CI Replication (preserve venv)..."
                    ./ci_debug_replica.sh --debug --preserve-venv
                    SCRIPT_EXIT_CODE=$?
                    ;;
                e)
                    echo -n "Enter custom options: "
                    read -r custom_options
                    print_info "Running Debug CI Replication with custom options..."
                    ./ci_debug_replica.sh $custom_options
                    SCRIPT_EXIT_CODE=$?
                    ;;
                *)
                    print_error "Invalid debug option. Running standard debug mode..."
                    ./ci_debug_replica.sh --debug
                    SCRIPT_EXIT_CODE=$?
                    ;;
            esac
            break
            ;;
        3)
            print_info "Maximum Isolation Reproducer options:"
            echo "  a. Full isolation (recommended)"
            echo "  b. Full isolation with preserved directory"
            echo "  c. Partial isolation"
            echo "  d. Minimal isolation"
            echo "  e. Custom options"
            echo
            echo -n "Choose isolation option (a-e): "
            read -r isolation_choice

            case $isolation_choice in
                a)
                    print_info "Running Maximum Isolation Reproducer (full)..."
                    ./ci_failure_reproducer.sh --isolation=full
                    ;;
                b)
                    print_info "Running Maximum Isolation Reproducer (full + keep)..."
                    ./ci_failure_reproducer.sh --isolation=full --keep-isolation
                    ;;
                c)
                    print_info "Running Maximum Isolation Reproducer (partial)..."
                    ./ci_failure_reproducer.sh --isolation=partial
                    ;;
                d)
                    print_info "Running Maximum Isolation Reproducer (minimal)..."
                    ./ci_failure_reproducer.sh --isolation=minimal
                    ;;
                e)
                    echo -n "Enter custom options: "
                    read -r custom_options
                    print_info "Running Maximum Isolation Reproducer with custom options..."
                    ./ci_failure_reproducer.sh $custom_options
                    ;;
                *)
                    print_error "Invalid isolation option. Running full isolation..."
                    ./ci_failure_reproducer.sh --isolation=full
                    ;;
            esac
            break
            ;;
        4)
            print_info "Available scripts for help:"
            echo "  1. ci_local_replica.sh --help"
            echo "  2. ci_debug_replica.sh --help"
            echo "  3. ci_failure_reproducer.sh --help"
            echo
            echo -n "Choose script for help (1-3): "
            read -r help_choice

            case $help_choice in
                1)
                    echo "ci_local_replica.sh help:"
                    echo "This script doesn't have specific help options."
                    echo "It runs a basic CI environment replication."
                    ;;
                2)
                    ./ci_debug_replica.sh --help
                    ;;
                3)
                    ./ci_failure_reproducer.sh --help
                    ;;
                *)
                    print_error "Invalid help option"
                    ;;
            esac
            echo
            echo -n "Press Enter to continue..."
            read -r
            continue
            ;;
        5)
            print_info "Exiting..."
            exit 0
            ;;
        *)
            print_error "Invalid option. Please choose 1-5."
            continue
            ;;
    esac
done

# Check exit status and print appropriate message
if [ $SCRIPT_EXIT_CODE -eq 0 ]; then
    print_success "CI replication completed successfully!"
    print_info "Check the output above for results and any debugging information."
else
    print_error "CI replication failed with exit code $SCRIPT_EXIT_CODE"
    print_info "Check the output above for error details."
fi
print_info "For more details, see CI_REPLICA_USAGE.md"

# Exit with the same code as the child script
exit $SCRIPT_EXIT_CODE
