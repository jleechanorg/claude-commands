#!/bin/bash

# Simple test of memory monitor
temp_dir=$(mktemp -d)
monitor_file="$temp_dir/memory_monitor"

memory_monitor() {
    local monitor_file="$1"
    echo "Monitor started for file: $monitor_file"
    local counter=0
    
    while [ -f "$monitor_file" ] && [ $counter -lt 5 ]; do
        echo "Monitor loop iteration: $counter"
        counter=$((counter + 1))
        sleep 1
    done
    echo "Monitor finished"
}

start_memory_monitor() {
    local monitor_file="$1"
    touch "$monitor_file"
    echo "About to start memory_monitor in background..."
    memory_monitor "$monitor_file" &
    local pid=$!
    echo "Background process PID: $pid"
    echo $pid
}

echo "Testing memory monitor..."
monitor_pid=$(start_memory_monitor "$monitor_file")
echo "Got monitor PID: $monitor_pid"

# Let it run for 3 seconds
sleep 3

# Stop the monitor
rm -f "$monitor_file"
sleep 2

# Clean up
rm -rf "$temp_dir"
echo "Test completed"