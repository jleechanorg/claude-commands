#!/bin/bash

# Debug the memory monitor issue
PROJECT_ROOT="/home/jleechan/projects/worldarchitect.ai/worktree_human2"

# Colors
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Memory monitoring configuration
MEMORY_LIMIT_GB=30
SINGLE_PROCESS_LIMIT_GB=10
MONITOR_INTERVAL=2

get_total_memory_usage_gb() {
    local total_kb=$(pgrep -f "python.*test_" | xargs -r ps -o rss= -p 2>/dev/null | awk '{sum+=$1} END {print sum+0}')
    echo "scale=2; $total_kb / 1024 / 1024" | bc -l
}

simple_memory_monitor() {
    local monitor_file="$1"
    local counter=0
    
    print_status "Monitor starting for file: $monitor_file"
    
    while [ -f "$monitor_file" ] && [ $counter -lt 10 ]; do
        local total_memory=$(get_total_memory_usage_gb)
        print_status "Monitor loop $counter: ${total_memory}GB"
        counter=$((counter + 1))
        sleep 2
    done
    
    print_status "Monitor finished"
}

start_simple_monitor() {
    local monitor_file="$1"
    touch "$monitor_file"
    print_status "About to start monitor in background..."
    simple_memory_monitor "$monitor_file" &
    local pid=$!
    print_status "Started monitor with PID: $pid"
    echo "$pid"
}

# Test
temp_dir=$(mktemp -d)
monitor_file="$temp_dir/memory_monitor"

print_status "Testing simple monitor..."
monitor_pid=$(start_simple_monitor "$monitor_file")
print_status "Got monitor PID: $monitor_pid"

# Let it run for a bit
sleep 5

# Stop the monitor
print_status "Stopping monitor..."
rm -f "$monitor_file"

# Clean up
sleep 2
rm -rf "$temp_dir"
print_status "Test completed"