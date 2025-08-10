#!/bin/bash

# Quick test of just a few test files to identify the memory hog
PROJECT_ROOT="$(cd "$(dirname "$0")" ; pwd)"
source "$PROJECT_ROOT/scripts/venv_utils.sh"
ensure_venv

# Colors
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Simple memory monitor - just show top 5 memory-consuming processes every 5 seconds
simple_monitor() {
    while true; do
        echo "=== Memory Monitor $(date) ==="
        ps -eo pid,ppid,%mem,rss,cmd --sort=-%mem | head -10
        echo "Total system memory usage:"
        free -h
        echo "==============================================="
        sleep 5
    done
}

# Start simple monitoring in background
simple_monitor &
monitor_pid=$!

print_status "Started simple monitor with PID: $monitor_pid"
print_status "Running just first 3 test files..."

# Set environment
export TESTING=true
export TEST_MODE=mock
export PYTHONPATH="$PROJECT_ROOT:$PROJECT_ROOT/mvp_site:${PYTHONPATH:-}"

# Run just the first 3 test files
test_files=(
    "./mvp_site/tests/test_fake_services_simple.py"
    "./mvp_site/tests/test_gemini_token_management.py"
    "./mvp_site/tests/test_settings_e2e.py"
)

for test_file in "${test_files[@]}"; do
    if [ -f "$test_file" ]; then
        print_status "Testing: $test_file"
        timeout 30s python "$test_file"
        exit_code=$?
        print_status "Test completed with exit code: $exit_code"
        
        # Show current memory usage after each test
        print_status "Memory after test:"
        ps -eo pid,ppid,%mem,rss,cmd --sort=-%mem | head -5
        echo "---"
    else
        print_status "File not found: $test_file"
    fi
done

print_status "Stopping monitor..."
kill $monitor_pid 2>/dev/null

print_status "Test completed"