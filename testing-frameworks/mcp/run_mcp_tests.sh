#!/bin/bash

# MCP Architecture Test Runner
# Comprehensive testing suite for MCP refactor infrastructure

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TESTING_MCP_DIR="$PROJECT_ROOT/testing_mcp"
RESULTS_DIR="$TESTING_MCP_DIR/results"

# Default values
TEST_TYPE="all"
USE_REAL_APIS=false
VERBOSE=false
DOCKER_MODE=false
CLEANUP=true
TIMEOUT=300  # 5 minutes default timeout

# Create results directory
mkdir -p "$RESULTS_DIR"

# Logging
LOG_FILE="$RESULTS_DIR/test_run_$(date +%Y%m%d_%H%M%S).log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

print_header() {
    echo -e "${BLUE}=====================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}=====================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

usage() {
    cat << EOF
Usage: $0 [OPTIONS] [TEST_TYPE]

Test MCP architecture infrastructure comprehensively.

TEST_TYPES:
    all             Run all tests (default)
    integration     Run integration tests only
    performance     Run performance benchmarks only
    unit            Run unit tests only
    docker          Run tests in Docker environment
    mock            Run tests with mock services only

OPTIONS:
    --real-apis     Use real APIs (costs money, default: false)
    --verbose       Enable verbose output
    --docker        Run tests in Docker containers
    --no-cleanup    Skip cleanup of test resources
    --timeout SEC   Set test timeout in seconds (default: 300)
    --help          Show this help message

EXAMPLES:
    $0                          # Run all tests with mocks
    $0 integration --verbose    # Run integration tests with verbose output
    $0 performance --real-apis  # Run performance tests with real APIs
    $0 --docker                 # Run all tests in Docker environment

ENVIRONMENT VARIABLES:
    MCP_SERVER_URL      URL for MCP server (default: http://localhost:8000)
    GEMINI_API_KEY      Gemini API key for real API tests
    JWT_SECRET_KEY      JWT secret for authentication tests
    TEST_USER_ID        Test user ID (default: test-user-123)

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --real-apis)
            USE_REAL_APIS=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --docker)
            DOCKER_MODE=true
            shift
            ;;
        --no-cleanup)
            CLEANUP=false
            shift
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --help)
            usage
            exit 0
            ;;
        all|integration|performance|unit|docker|mock)
            TEST_TYPE="$1"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Set Docker mode if test type is docker
if [[ "$TEST_TYPE" == "docker" ]]; then
    DOCKER_MODE=true
    TEST_TYPE="all"
fi

# Set environment variables
export TESTING=true
export MCP_SERVER_URL="${MCP_SERVER_URL:-http://localhost:8000}"
export TEST_USER_ID="${TEST_USER_ID:-test-user-123}"
export PYTHONPATH="$PROJECT_ROOT:$TESTING_MCP_DIR:$PYTHONPATH"

if [[ "$USE_REAL_APIS" == "true" ]]; then
    export TEST_MODE="real"
    if [[ -z "$GEMINI_API_KEY" ]]; then
        print_error "GEMINI_API_KEY required for real API tests"
        exit 1
    fi
else
    export TEST_MODE="mock"
    export GEMINI_API_KEY="test-key"
fi

if [[ "$VERBOSE" == "true" ]]; then
    export LOG_LEVEL="DEBUG"
    export PYTEST_ARGS="-v -s"
else
    export LOG_LEVEL="INFO"
    export PYTEST_ARGS="-v"
fi

# Function to check dependencies
check_dependencies() {
    log "Checking dependencies..."

    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required"
        exit 1
    fi

    # Check virtual environment
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        print_warning "Not in a virtual environment. Activating venv if available..."
        if [[ -f "$PROJECT_ROOT/venv/bin/activate" ]]; then
            source "$PROJECT_ROOT/venv/bin/activate"
        fi
    fi

    # Check Docker if in Docker mode
    if [[ "$DOCKER_MODE" == "true" ]]; then
        if ! command -v docker &> /dev/null; then
            print_error "Docker is required for Docker mode"
            exit 1
        fi

        if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
            print_error "Docker Compose is required for Docker mode"
            exit 1
        fi
    fi

    print_success "Dependencies check passed"
}

# Function to install test dependencies
install_dependencies() {
    log "Installing test dependencies..."

    cd "$TESTING_MCP_DIR"

    if [[ -f "requirements.txt" ]]; then
        pip install -r requirements.txt >> "$LOG_FILE" 2>&1
        print_success "Test dependencies installed"
    else
        print_warning "No test requirements.txt found"
    fi
}

# Function to start mock services
start_mock_services() {
    log "Starting mock services..."

    # Start mock MCP server
    cd "$TESTING_MCP_DIR"
    python utils/mock_mcp_server.py 8001 >> "$LOG_FILE" 2>&1 &
    MOCK_SERVER_PID=$!

    # Wait for mock server to be ready
    for i in {1..30}; do
        if curl -s http://localhost:8001/health > /dev/null 2>&1; then
            print_success "Mock MCP server started (PID: $MOCK_SERVER_PID)"
            break
        fi
        sleep 1
    done

    if ! curl -s http://localhost:8001/health > /dev/null 2>&1; then
        print_error "Mock MCP server failed to start"
        return 1
    fi
}

# Function to stop mock services
stop_mock_services() {
    if [[ -n "$MOCK_SERVER_PID" ]]; then
        log "Stopping mock services..."
        kill $MOCK_SERVER_PID 2>/dev/null || true
        print_success "Mock services stopped"
    fi
}

# Function to run tests in Docker
run_docker_tests() {
    print_header "Running Tests in Docker Environment"

    cd "$TESTING_MCP_DIR/deployment"

    # Build and start services
    log "Building Docker services..."
    docker-compose build >> "$LOG_FILE" 2>&1

    log "Starting Docker services..."
    docker-compose up -d firestore-emulator redis mock-mcp-server >> "$LOG_FILE" 2>&1

    # Wait for services to be ready
    log "Waiting for services to be ready..."
    sleep 10

    # Run tests in Docker
    log "Running tests in Docker..."
    if docker-compose run --rm test-runner; then
        print_success "Docker tests passed"
        DOCKER_TEST_RESULT=0
    else
        print_error "Docker tests failed"
        DOCKER_TEST_RESULT=1
    fi

    # Cleanup Docker services
    if [[ "$CLEANUP" == "true" ]]; then
        log "Cleaning up Docker services..."
        docker-compose down >> "$LOG_FILE" 2>&1
    fi

    return $DOCKER_TEST_RESULT
}

# Function to run unit tests
run_unit_tests() {
    print_header "Running Unit Tests"

    cd "$TESTING_MCP_DIR"

    log "Running MCP unit tests..."
    if python -m pytest utils/ -v --junitxml="$RESULTS_DIR/unit_results.xml" >> "$LOG_FILE" 2>&1; then
        print_success "Unit tests passed"
        return 0
    else
        print_error "Unit tests failed"
        return 1
    fi
}

# Function to run integration tests
run_integration_tests() {
    print_header "Running Integration Tests"

    cd "$TESTING_MCP_DIR"

    log "Running MCP integration tests..."

    # Set timeout for pytest
    timeout_arg=""
    if [[ "$TIMEOUT" -gt 0 ]]; then
        timeout_arg="--timeout=$TIMEOUT"
    fi

    if python -m pytest integration/ $PYTEST_ARGS $timeout_arg --junitxml="$RESULTS_DIR/integration_results.xml" >> "$LOG_FILE" 2>&1; then
        print_success "Integration tests passed"
        return 0
    else
        print_error "Integration tests failed"
        cat "$LOG_FILE" | tail -20  # Show last 20 lines for debugging
        return 1
    fi
}

# Function to run performance tests
run_performance_tests() {
    print_header "Running Performance Benchmarks"

    cd "$TESTING_MCP_DIR"

    log "Running performance benchmarks..."
    if python performance/benchmark_mcp_vs_direct.py >> "$LOG_FILE" 2>&1; then
        print_success "Performance benchmarks passed"
        return 0
    else
        print_error "Performance benchmarks failed"
        return 1
    fi
}

# Function to generate test report
generate_report() {
    print_header "Generating Test Report"

    local report_file="$RESULTS_DIR/test_report_$(date +%Y%m%d_%H%M%S).html"

    cat > "$report_file" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>MCP Architecture Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .pass { color: green; }
        .fail { color: red; }
        .warning { color: orange; }
        pre { background: #f5f5f5; padding: 10px; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>MCP Architecture Test Report</h1>
    <p><strong>Generated:</strong> $(date)</p>
    <p><strong>Test Type:</strong> $TEST_TYPE</p>
    <p><strong>API Mode:</strong> $([ "$USE_REAL_APIS" == "true" ] && echo "Real APIs" || echo "Mock APIs")</p>
    <p><strong>Docker Mode:</strong> $([ "$DOCKER_MODE" == "true" ] && echo "Yes" || echo "No")</p>

    <h2>Test Results</h2>
    <pre>$(cat "$LOG_FILE" | tail -50)</pre>

    <h2>Files Generated</h2>
    <ul>
EOF

    # Add result files to report
    for result_file in "$RESULTS_DIR"/*.xml "$RESULTS_DIR"/*.json; do
        if [[ -f "$result_file" ]]; then
            echo "        <li>$(basename "$result_file")</li>" >> "$report_file"
        fi
    done

    cat >> "$report_file" << EOF
    </ul>
</body>
</html>
EOF

    print_success "Test report generated: $report_file"
}

# Cleanup function
cleanup() {
    if [[ "$CLEANUP" == "true" ]]; then
        log "Cleaning up test resources..."
        stop_mock_services

        # Kill any leftover processes
        pkill -f "mock_mcp_server" 2>/dev/null || true

        print_success "Cleanup completed"
    fi
}

# Trap to ensure cleanup on exit
trap cleanup EXIT

# Main execution
main() {
    print_header "MCP Architecture Test Suite"

    log "Starting MCP test run with type: $TEST_TYPE"
    log "Configuration: USE_REAL_APIS=$USE_REAL_APIS, DOCKER_MODE=$DOCKER_MODE, VERBOSE=$VERBOSE"

    # Check dependencies
    check_dependencies

    # Install dependencies
    install_dependencies

    local exit_code=0

    # Run tests based on type
    if [[ "$DOCKER_MODE" == "true" ]]; then
        if ! run_docker_tests; then
            exit_code=1
        fi
    else
        # Start mock services for non-Docker tests
        if [[ "$TEST_MODE" == "mock" ]]; then
            start_mock_services
        fi

        case $TEST_TYPE in
            "unit")
                if ! run_unit_tests; then
                    exit_code=1
                fi
                ;;
            "integration")
                if ! run_integration_tests; then
                    exit_code=1
                fi
                ;;
            "performance")
                if ! run_performance_tests; then
                    exit_code=1
                fi
                ;;
            "mock")
                export TEST_MODE="mock"
                if ! run_unit_tests || ! run_integration_tests; then
                    exit_code=1
                fi
                ;;
            "all")
                if ! run_unit_tests; then
                    exit_code=1
                fi
                if ! run_integration_tests; then
                    exit_code=1
                fi
                if ! run_performance_tests; then
                    exit_code=1
                fi
                ;;
            *)
                print_error "Unknown test type: $TEST_TYPE"
                exit_code=1
                ;;
        esac
    fi

    # Generate report
    generate_report

    # Final status
    if [[ $exit_code -eq 0 ]]; then
        print_success "All tests passed! MCP architecture testing completed successfully."
    else
        print_error "Some tests failed. Check the logs for details."
    fi

    log "Test run completed with exit code: $exit_code"
    return $exit_code
}

# Run main function
main "$@"
