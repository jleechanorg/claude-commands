#!/bin/bash
# port-utils.sh - Shared port detection utilities for WorldArchitect.AI scripts
#
# This module provides common port detection functionality to avoid code duplication
# across multiple command scripts that need to find available ports.

# Configuration
BASE_PORT=8081
MAX_PORTS=10

# Colors for output (if not already defined)
if [ -z "$RED" ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    NC='\033[0m' # No Color
fi

# Function to find available port starting from BASE_PORT
find_available_port() {
    local port=$BASE_PORT
    local max_port=$((BASE_PORT + MAX_PORTS - 1))

    while [ $port -le $max_port ]; do
        if ! lsof -i:$port > /dev/null 2>&1; then
            echo $port
            return 0
        fi
        port=$((port + 1))
    done

    echo -e "${RED}❌ No available ports in range $BASE_PORT-$max_port${NC}" >&2
    return 1
}

# Function to check if a specific port is in use
is_port_in_use() {
    local port=$1
    if [ -z "$port" ]; then
        echo "Usage: is_port_in_use <port>" >&2
        return 1
    fi

    lsof -i:$port > /dev/null 2>&1
    return $?
}

# Function to list running servers in our port range
list_running_servers() {
    echo -e "${YELLOW}🖥️  Running servers in range $BASE_PORT-$((BASE_PORT + MAX_PORTS - 1)):${NC}"

    local found_any=false
    for port in $(seq $BASE_PORT $((BASE_PORT + MAX_PORTS - 1))); do
        local pid=$(lsof -ti:$port 2>/dev/null)
        if [ -n "$pid" ]; then
            local cmd=$(ps -p $pid -o args --no-headers 2>/dev/null | head -1)
            echo "   Port $port: PID $pid - $cmd"
            found_any=true
        fi
    done

    if [ "$found_any" = false ]; then
        echo "   (No servers running in port range)"
    fi
}
