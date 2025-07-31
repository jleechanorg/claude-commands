#!/bin/bash
# Common Test Functions for WorldArchitect.AI
# Shared functionality across run_tests.sh, coverage.sh, and run_tests_with_coverage.sh

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Check if coverage is installed and install if needed
check_and_install_coverage() {
    local venv_path="${1:-../venv}"

    print_status "Checking coverage installation..."

    # First, activate the virtual environment
    if ! source "$venv_path/bin/activate"; then
        print_error "Failed to activate virtual environment at $venv_path"
        return 1
    fi

    # Then check if coverage is importable
    if ! python -c "import coverage" 2>/dev/null; then
        print_warning "Coverage tool not found. Installing..."
        if ! pip install coverage; then
            print_error "Failed to install coverage"
            return 1
        fi
        print_success "Coverage installed successfully"
    else
        print_status "Coverage already installed"
    fi

    return 0
}

# Find test files with common exclusions
find_test_files() {
    local include_integration="$1"
    local test_files=()

    print_status "Discovering test files..."

    # Find all test_*.py files with common exclusions
    while IFS= read -r -d '' file; do
        test_files+=("$file")
    done < <(find ./tests -name "test_*.py" -type f \
        ! -path "./venv/*" \
        ! -path "./node_modules/*" \
        ! -path "./prototype/*" \
        ! -path "./tests/manual_tests/*" \
        ! -path "./tests/test_integration/*" \
        -print0)

    # Add integration tests if requested
    if [ "$include_integration" = true ]; then
        while IFS= read -r -d '' file; do
            test_files+=("$file")
        done < <(find ./tests/test_integration -name "test_*.py" -type f \
            ! -path "./venv/*" \
            ! -path "./node_modules/*" \
            ! -path "./prototype/*" \
            -print0 2>/dev/null)
    fi

    # Export the array for use by calling script
    printf '%s\n' "${test_files[@]}"

    local count=${#test_files[@]}
    print_status "Found $count test file(s) for execution"

    if [ $count -eq 0 ]; then
        print_error "No test files found matching criteria"
        return 1
    fi

    return 0
}

# Parse common command line arguments
parse_common_args() {
    local include_integration=false
    local enable_coverage=false
    local generate_html=true

    for arg in "$@"; do
        case $arg in
            --integration)
                include_integration=true
                ;;
            --coverage)
                enable_coverage=true
                ;;
            --html)
                generate_html=true
                ;;
            --no-html)
                generate_html=false
                ;;
            *)
                if [[ $arg == --* ]]; then
                    print_warning "Unknown argument: $arg"
                fi
                ;;
        esac
    done

    # Export variables for use by calling script
    echo "include_integration=$include_integration"
    echo "enable_coverage=$enable_coverage"
    echo "generate_html=$generate_html"
}

# Validate environment prerequisites
validate_environment() {
    local required_dir="mvp_site"

    if [ ! -d "$required_dir" ]; then
        print_error "Required directory '$required_dir' not found"
        print_error "Please run this script from the project root directory"
        return 1
    fi

    if [ ! -d "../venv" ] && [ ! -d "venv" ]; then
        print_error "Python virtual environment not found"
        print_error "Expected to find venv at ../venv or ./venv"
        return 1
    fi

    return 0
}

# Generate coverage reports
generate_coverage_reports() {
    local coverage_dir="$1"
    local generate_html="$2"
    local venv_path="${3:-../venv}"

    print_status "📊 Generating coverage report..."
    local coverage_start_time=$(date +%s)

    # Activate venv
    source "$venv_path/bin/activate"

    # Generate text coverage report
    if coverage report > "$coverage_dir/coverage_report.txt"; then
        print_success "Text coverage report generated successfully"

        # Display key coverage metrics
        echo
        print_status "📈 Coverage Summary:"
        echo "----------------------------------------"

        # Show overall coverage
        local overall_coverage=$(tail -1 "$coverage_dir/coverage_report.txt" | awk '{print $4}')
        echo "Overall Coverage: $overall_coverage"

        # Show key file coverage
        echo
        echo "Key Files Coverage:"
        grep -E "(main\.py|gemini_service\.py|game_state\.py|firestore_service\.py)" \
            "$coverage_dir/coverage_report.txt" | head -10 || echo "No key files found in report"

        echo "----------------------------------------"
    else
        print_error "Failed to generate coverage report"
        return 1
    fi

    # Generate HTML report if requested
    if [ "$generate_html" = true ]; then
        print_status "🌐 Generating HTML coverage report..."
        if coverage html --directory="$coverage_dir"; then
            print_success "HTML coverage report generated in $coverage_dir/"
            print_status "Open $coverage_dir/index.html in your browser to view detailed coverage"

            # Create a convenient symlink if possible
            if [ -w "/tmp" ]; then
                ln -sf "$coverage_dir/index.html" "/tmp/coverage.html" 2>/dev/null
                if [ $? -eq 0 ]; then
                    print_status "Quick access: file:///tmp/coverage.html"
                fi
            fi
        else
            print_error "Failed to generate HTML coverage report"
            return 1
        fi
    else
        print_status "HTML report skipped (--no-html specified)"
    fi

    # Calculate timing
    local coverage_end_time=$(date +%s)
    local coverage_duration=$((coverage_end_time - coverage_start_time))

    echo
    print_status "⏱️  Coverage generation completed in ${coverage_duration}s"
    print_status "📁 Coverage files saved to: $coverage_dir"

    return 0
}
