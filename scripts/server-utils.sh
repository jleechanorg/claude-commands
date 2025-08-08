#!/bin/bash
# server-utils.sh - Comprehensive server utilities for WorldArchitect.AI
# Consolidates all common server management functions

# Load configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/server-config.sh"

# =============================================================================
# PORT MANAGEMENT FUNCTIONS
# =============================================================================

# Enhanced port checking with multiple fallback methods
is_port_in_use() {
    local port=$1
    
    # Method 1: lsof (most reliable)
    if command -v lsof &> /dev/null; then
        lsof -i :$port &> /dev/null
        return $?
    fi
    
    # Method 2: netstat fallback
    if command -v netstat &> /dev/null; then
        netstat -an 2>/dev/null | grep -q ":$port.*LISTEN"
        return $?
    fi
    
    # Method 3: ss command fallback
    if command -v ss &> /dev/null; then
        ss -tlnp 2>/dev/null | grep -q ":$port "
        return $?
    fi
    
    # If no tools available, assume port is free
    echo "${EMOJI_WARNING} Warning: No port checking tools available (lsof, netstat, ss)"
    return 1
}

# Find next available port in a range
find_available_port() {
    local start_port=${1:-$DEFAULT_FLASK_PORT}
    local max_attempts=${2:-10}
    local port=$start_port
    local attempts=0

    while [ $attempts -lt $max_attempts ]; do
        if ! is_port_in_use $port; then
            echo $port
            return 0
        fi
        
        echo "${EMOJI_INFO} Port $port in use, trying $((port + 1))..."
        port=$((port + 1))
        attempts=$((attempts + 1))
    done

    echo "${EMOJI_ERROR} ERROR: No available ports found in range $start_port-$((start_port + max_attempts - 1))"
    return 1
}

# Kill processes using a specific port with graceful shutdown
kill_port_processes() {
    local port=$1
    local timeout=${2:-5}
    
    echo "${EMOJI_SEARCH} Checking for processes using port $port..."

    # Get PIDs using the port
    local pids=$(lsof -ti:$port 2>/dev/null || true)
    if [ -z "$pids" ]; then
        echo "${EMOJI_CHECK} Port $port is already free"
        return 0
    fi

    echo "${EMOJI_SWORD} Found processes using port $port: $pids"
    
    # Step 1: Graceful shutdown (SIGTERM)
    echo "${EMOJI_GEAR} Attempting graceful shutdown..."
    echo "$pids" | xargs kill -TERM 2>/dev/null || true
    
    # Wait for graceful shutdown
    local waited=0
    while [ $waited -lt $timeout ]; do
        local remaining_pids=$(lsof -ti:$port 2>/dev/null || true)
        if [ -z "$remaining_pids" ]; then
            echo "${EMOJI_CHECK} Port $port freed gracefully"
            return 0
        fi
        sleep 1
        waited=$((waited + 1))
        echo "${EMOJI_CLOCK} Waiting for graceful shutdown... ($waited/$timeout)s"
    done
    
    # Step 2: Force kill (SIGKILL)
    local remaining_pids=$(lsof -ti:$port 2>/dev/null || true)
    if [ -n "$remaining_pids" ]; then
        echo "${EMOJI_SWORD} Force killing remaining processes: $remaining_pids"
        echo "$remaining_pids" | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
    
    # Step 3: Verify port is free
    if is_port_in_use $port; then
        echo "${EMOJI_ERROR} ERROR: Port $port still in use after kill attempts"
        return 1
    else
        echo "${EMOJI_CHECK} Port $port is now free"
        return 0
    fi
}

# Ensure port is available (kill if necessary)
ensure_port_free() {
    local port=$1
    local timeout=${2:-5}
    
    echo "${EMOJI_TARGET} Ensuring port $port is available..."
    
    if ! is_port_in_use $port; then
        echo "${EMOJI_CHECK} Port $port is already free"
        return 0
    fi
    
    if ! kill_port_processes $port $timeout; then
        echo "${EMOJI_ERROR} CRITICAL: Failed to free port $port"
        echo "  Please manually kill processes and try again:"
        echo "  lsof -ti:$port | xargs kill -9"
        return 1
    fi
    
    return 0
}

# =============================================================================
# VIRTUAL ENVIRONMENT FUNCTIONS
# =============================================================================

# Enhanced virtual environment detection with worktree support
detect_and_activate_venv() {
    local python_cmd=""
    
    # Check for local venv first
    if [ -f "venv/bin/activate" ]; then
        echo "${EMOJI_PYTHON} Activating local virtual environment..."
        source venv/bin/activate
        python_cmd="python"
    # Check for worktree venv (from tools/localserver.sh logic)
    elif [ -f ".git" ] && grep -q "gitdir:" .git 2>/dev/null; then
        echo "${EMOJI_INFO} Detected git worktree environment"
        local gitdir=$(grep gitdir: .git | cut -d' ' -f2)
        local main_project_dir=$(echo "$gitdir" | sed 's/\.git\/worktrees\/.*//')
        
        if [ -f "$main_project_dir/venv/bin/activate" ]; then
            echo "${EMOJI_PYTHON} Activating main project virtual environment..."
            source "$main_project_dir/venv/bin/activate"
            python_cmd="python"
        fi
    fi
    
    # Fallback to system Python3 with validation
    if [ -z "$python_cmd" ]; then
        if command -v python3 &> /dev/null; then
            echo "${EMOJI_WARNING} No virtual environment found, using system Python3"
            python_cmd="python3"
            
            # Validate Flask is available
            if ! $python_cmd -c "import flask" 2>/dev/null; then
                echo "${EMOJI_ERROR} ERROR: Flask is not installed"
                echo ""
                echo "📚 To set up the environment, run:"
                echo "   python3 -m venv venv"
                echo "   source venv/bin/activate"
                echo "   pip install -r mvp_site/requirements.txt"
                return 1
            fi
        else
            echo "${EMOJI_ERROR} ERROR: Python3 not found"
            return 1
        fi
    fi
    
    # Export Python command for use by calling scripts
    export PYTHON_CMD="$python_cmd"
    echo "${EMOJI_CHECK} Python environment ready: $python_cmd"
    return 0
}

# =============================================================================
# PROCESS MANAGEMENT FUNCTIONS  
# =============================================================================

# Kill WorldArchitect.AI server processes
kill_worldarchitect_servers() {
    local verbose=${1:-false}
    
    if [ "$verbose" = true ]; then
        echo "${EMOJI_GEAR} Stopping WorldArchitect.AI servers..."
    fi
    
    # Kill Flask servers
    pkill -f "python.*main.py.*serve" 2>/dev/null || true
    
    # Kill Vite/React servers  
    pkill -f "vite" 2>/dev/null || true
    pkill -f "node.*vite" 2>/dev/null || true
    
    # Kill npm processes
    pkill -f "npm.*dev" 2>/dev/null || true
    
    if [ "$verbose" = true ]; then
        sleep 2
        echo "${EMOJI_CHECK} Server cleanup completed"
    fi
}

# List running WorldArchitect.AI servers
list_worldarchitect_servers() {
    echo ""
    echo "${EMOJI_INFO} Currently Running WorldArchitect.AI Servers:"
    echo "-----------------------------------------------------"

    # Find Flask servers
    local flask_servers=$(ps aux | grep -E "python.*main.py.*serve" | grep -v grep || true)
    
    if [ -z "$flask_servers" ]; then
        echo "${EMOJI_CHECK} No Flask servers currently running"
    else
        echo "Flask Servers:"
        echo "$flask_servers" | while read -r line; do
            local pid=$(echo "$line" | awk '{print $2}')
            local port=$(lsof -p $pid 2>/dev/null | grep LISTEN | awk '{print $9}' | cut -d: -f2 | head -1)
            [ -z "$port" ] && port="unknown"
            echo "  ${EMOJI_TARGET} PID: $pid | Port: $port"
        done
    fi
    
    # Find Vite servers
    local vite_servers=$(ps aux | grep -E "(vite|node.*vite)" | grep -v grep || true)
    
    if [ -z "$vite_servers" ]; then
        echo "${EMOJI_CHECK} No Vite servers currently running"
    else
        echo "Vite/React Servers:"
        echo "$vite_servers" | while read -r line; do
            local pid=$(echo "$line" | awk '{print $2}')
            local port=$(lsof -p $pid 2>/dev/null | grep LISTEN | awk '{print $9}' | cut -d: -f2 | head -1)
            [ -z "$port" ] && port="unknown"
            echo "  ${EMOJI_TARGET} PID: $pid | Port: $port"
        done
    fi
    
    echo ""
}

# =============================================================================
# SERVER VALIDATION FUNCTIONS
# =============================================================================

# Validate server is responding with enhanced checks
validate_server() {
    local port=$1
    local max_attempts=${2:-10}
    local timeout=${3:-2}
    local endpoint=${4:-"/"}
    local attempt=1

    echo ""
    echo "${EMOJI_SEARCH} Validating server on port $port..."
    echo "---------------------------------------------"

    while [ $attempt -le $max_attempts ]; do
        echo "Attempt $attempt/$max_attempts: Testing http://localhost:$port$endpoint"

        if curl -s -f --max-time $timeout "http://localhost:$port$endpoint" > /dev/null 2>&1; then
            echo "${EMOJI_CHECK} Server is responding correctly!"
            echo "${EMOJI_ROCKET} Server URL: http://localhost:$port/"
            return 0
        else
            echo "${EMOJI_WARNING} Server not responding yet, waiting 2 seconds..."
            sleep 2
            ((attempt++))
        fi
    done

    echo "${EMOJI_ERROR} ERROR: Server failed to respond after $max_attempts attempts"
    
    # Diagnostic information
    echo "${EMOJI_SEARCH} Diagnostics:"
    if ps aux | grep -E "python.*main.py.*serve" | grep -v grep > /dev/null; then
        echo "  ${EMOJI_WARNING} Server process is running but not responding to HTTP requests"
    else
        echo "  ${EMOJI_ERROR} Server process has died"
    fi
    
    return 1
}

# =============================================================================
# LOGGING FUNCTIONS
# =============================================================================

# Setup branch-isolated logging directory
setup_logging() {
    local service_name=${1:-"server"}
    local current_branch=$(git branch --show-current 2>/dev/null || echo "unknown")
    local log_dir="$LOG_DIR_BASE/$current_branch"
    
    mkdir -p "$log_dir"
    
    local log_file="$log_dir/${service_name}_$(date +%Y%m%d_%H%M%S).log"
    echo "$log_file"
}

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

# Print banner with consistent formatting
print_banner() {
    local title="$1"
    local subtitle="$2"
    
    echo "${EMOJI_ROCKET} $title"
    echo "$(printf '=%.0s' $(seq 1 ${#title}))"
    
    if [ -n "$subtitle" ]; then
        echo "$subtitle"
        echo ""
    fi
}

# Print configuration summary
print_server_config() {
    local flask_port="$1"
    local react_port="$2"
    
    echo ""
    echo "${EMOJI_INFO} Server Configuration:"
    echo "   - Flask Backend: http://localhost:$flask_port"
    [ -n "$react_port" ] && echo "   - React Frontend: http://localhost:$react_port"
    echo "   - Mode: ${TESTING:+Testing}${FLASK_ENV:+ ($FLASK_ENV)}"
    echo "   - Python: ${PYTHON_CMD:-python3}"
    echo "   - Working Directory: $(pwd)"
    echo ""
    
    if [ "$TESTING" = "true" ]; then
        echo "${EMOJI_INFO} Test Mode Access:"
        echo "   For authenticated access without sign-in:"
        echo "   http://localhost:$flask_port?test_mode=true&test_user_id=test-user-123"
        echo ""
    fi
}

# Validation: Ensure all functions are properly defined
if ! declare -f is_port_in_use > /dev/null; then
    echo "${EMOJI_ERROR} ERROR: Server utilities failed to load properly"
    exit 1
fi

echo "${EMOJI_CHECK} Server utilities loaded successfully"