#!/bin/bash
# run_local_server.sh - WorldArchitect.AI Dual Server Launcher
# Starts both Flask backend and React v2 frontend servers simultaneously
#
# Usage: ./run_local_server.sh [--cleanup|-c]
#   --cleanup, -c  Show interactive server cleanup menu
#   (default)      Keep existing servers, find available ports

# Parse command line arguments
INTERACTIVE_CLEANUP=false
for arg in "$@"; do
    case $arg in
        --cleanup|-c)
            INTERACTIVE_CLEANUP=true
            shift
            ;;
    esac
done

# Load shared utilities
MAIN_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$MAIN_SCRIPT_DIR"
source "$MAIN_SCRIPT_DIR/scripts/server-utils.sh"
source "$MAIN_SCRIPT_DIR/scripts/venv_utils.sh"

# Hardcode the WorldArchitect project for local tooling that touches GCP
DEFAULT_GCP_PROJECT="worldarchitecture-ai"
GCP_PROJECT="${GCP_PROJECT_OVERRIDE:-$DEFAULT_GCP_PROJECT}"
if command -v gcloud >/dev/null 2>&1; then
    if gcloud config configurations describe worldarchitect-ai >/dev/null 2>&1; then
        gcloud config configurations activate worldarchitect-ai >/dev/null
    fi
    gcloud config set project "$GCP_PROJECT" >/dev/null
    gcloud config set billing/quota_project "$GCP_PROJECT" >/dev/null
fi
export CLOUDSDK_CORE_PROJECT="$GCP_PROJECT"
export CLOUDSDK_BILLING_QUOTA_PROJECT="$GCP_PROJECT"
export GOOGLE_CLOUD_PROJECT="$GCP_PROJECT"
export GCLOUD_PROJECT="$GCP_PROJECT"

# Helper to pull secrets from Google Secret Manager without exposing values
load_secret_env() {
    local secret_name="$1"
    local env_var="$2"

    if ! command -v gcloud >/dev/null 2>&1; then
        echo "${EMOJI_WARNING} gcloud not available; cannot load ${env_var} from Secret Manager"
        return 1
    fi

    local value
    if value=$(gcloud secrets versions access latest --secret "$secret_name" --project="$GCP_PROJECT" 2>/dev/null); then
        if [ -n "$value" ]; then
            # Always prefer Secret Manager for local runs; override existing value if present
            if [ -n "${!env_var:-}" ]; then
                echo "${EMOJI_INFO} ${env_var} present; overriding with Secret Manager (${secret_name})"
            fi
            export "$env_var"="$value"
            echo "${EMOJI_CHECK} Loaded ${env_var} from Secret Manager (${secret_name}, len=${#value})"
            return 0
        fi
    fi

    echo "${EMOJI_WARNING} Unable to load ${env_var} from Secret Manager (${secret_name})"
    return 1
}

# Ensure all relative paths below are resolved from the repo root
cd "$PROJECT_ROOT"

print_banner "WorldArchitect.AI Development Server Launcher" "Dual server setup: Flask backend + React v2 frontend"

# Function to offer cleanup of existing servers with aggressive port clearing
cleanup_servers_interactive() {
    list_worldarchitect_servers

    local servers=$(ps aux | grep -E "python -m mvp_site\.main serve" | grep -v grep || true)
    local vite_servers=$(ps aux | grep -E "(vite|node.*vite)" | grep -v grep || true)

    if [ -n "$servers" ] || [ -n "$vite_servers" ]; then
        echo ""
        echo "${EMOJI_GEAR} Server Cleanup Options:"
        echo "   [a] Kill all servers (aggressive cleanup)"
        echo "   [p] Kill processes on target ports only"
        echo "   [n] Keep all servers running"
        echo -n "   Choice (default: n): "
        read -r choice
        choice=${choice:-n}  # Default to keeping servers running

        case "$choice" in
            a|A)
                echo "${EMOJI_GEAR} Stopping all servers..."
                kill_worldarchitect_servers true
                ;;
            p|P)
                echo "${EMOJI_GEAR} Killing processes on target ports..."
                # Clear the default target ports explicitly
                ensure_port_free "$DEFAULT_FLASK_PORT"
                ensure_port_free "$DEFAULT_REACT_PORT"
                ;;
            *)
                echo "${EMOJI_INFO} Keeping existing servers running"
                ;;
        esac
        echo ""
    else
        # No servers running, but still do aggressive port cleanup
        echo "${EMOJI_INFO} No servers currently running"
        echo "${EMOJI_GEAR} Performing aggressive port cleanup..."
        kill_worldarchitect_servers true
    fi
}

# Perform server cleanup (interactive only with --cleanup flag)
if [ "$INTERACTIVE_CLEANUP" = true ]; then
    cleanup_servers_interactive
else
    echo "${EMOJI_INFO} Keeping existing servers (use --cleanup for interactive cleanup)"
fi

# Setup virtual environment using new venv_utils
ensure_venv
if [ $? -ne 0 ]; then
    echo "${EMOJI_ERROR} Failed to setup virtual environment"
    exit 1
fi

# Validate that virtual environment is properly activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "${EMOJI_ERROR} Virtual environment not activated properly"
    echo "${EMOJI_INFO} Attempting manual activation..."
    if [ -f "$PROJECT_ROOT/venv/bin/activate" ]; then
        # Always activate using an absolute path to avoid CWD issues
        # shellcheck disable=SC1091
        source "$PROJECT_ROOT/venv/bin/activate"
        if [ -z "$VIRTUAL_ENV" ]; then
            echo "${EMOJI_ERROR} Manual activation also failed"
            exit 1
        fi
    else
        echo "${EMOJI_ERROR} Virtual environment activation file not found: $PROJECT_ROOT/venv/bin/activate"
        exit 1
    fi
fi

echo "${EMOJI_CHECK} Virtual environment active: $VIRTUAL_ENV"

# Aggressive port cleanup - ensure target ports are available
echo "${EMOJI_GEAR} Ensuring target ports are available..."
ensure_port_free $DEFAULT_FLASK_PORT 3 2>/dev/null || true
ensure_port_free $DEFAULT_REACT_PORT 3 2>/dev/null || true

# Hardcode WorldAI Firebase env for local runs
CREDS_FILE="${GOOGLE_APPLICATION_CREDENTIALS:-$HOME/serviceAccountKey.json}"
if [ ! -f "$CREDS_FILE" ]; then
    echo "${EMOJI_WARNING} Firebase credentials not found at $CREDS_FILE"
    echo "${EMOJI_INFO} For local development, copy your serviceAccountKey.json to $HOME/"
    echo "${EMOJI_INFO} Or set GOOGLE_APPLICATION_CREDENTIALS environment variable"
    # Continue anyway; Firebase init will fail gracefully if needed
fi
export GOOGLE_APPLICATION_CREDENTIALS="$CREDS_FILE"
export FIREBASE_PROJECT_ID="worldarchitecture-ai"

# Load LLM API keys from Secret Manager when not already provided
load_secret_env "gemini-api-key" "GEMINI_API_KEY"
load_secret_env "cerebras-api-key" "CEREBRAS_API_KEY"
load_secret_env "openrouter-api-key" "OPENROUTER_API_KEY"

# Fail fast if required keys are still missing
for required_var in GEMINI_API_KEY CEREBRAS_API_KEY; do
    if [ -z "${!required_var:-}" ]; then
        echo "${EMOJI_ERROR} ${required_var} is not set and could not be loaded from Secret Manager. Aborting."
        exit 1
    fi
done

# If using WORLDAI_GOOGLE_APPLICATION_CREDENTIALS, auto-ack dev mode for local runs
if [ -n "${WORLDAI_GOOGLE_APPLICATION_CREDENTIALS:-}" ] && [ -z "${WORLDAI_DEV_MODE:-}" ]; then
    export WORLDAI_DEV_MODE=true
    echo "${EMOJI_INFO} WORLDAI_GOOGLE_APPLICATION_CREDENTIALS detected; setting WORLDAI_DEV_MODE=true for local run"
fi

# Find available ports
echo "${EMOJI_SEARCH} Finding available ports..."
DETECTED_FLASK_PORT=$(find_available_port $DEFAULT_FLASK_PORT 10)
if [ $? -eq 0 ] && [ -n "$DETECTED_FLASK_PORT" ]; then
    FLASK_PORT="$DETECTED_FLASK_PORT"
else
    echo "${EMOJI_WARNING} Could not find available Flask port, forcing default $DEFAULT_FLASK_PORT"
    FLASK_PORT="$DEFAULT_FLASK_PORT"
fi

DETECTED_REACT_PORT=$(find_available_port $DEFAULT_REACT_PORT 10)
if [ $? -eq 0 ] && [ -n "$DETECTED_REACT_PORT" ]; then
    REACT_PORT="$DETECTED_REACT_PORT"
else
    echo "${EMOJI_WARNING} Could not find available React port, forcing default $DEFAULT_REACT_PORT"
    REACT_PORT="$DEFAULT_REACT_PORT"
fi

export PORT=$FLASK_PORT

print_server_config $FLASK_PORT $REACT_PORT

# Start Flask backend in a new terminal/tab if possible
echo ""
echo "${EMOJI_ROCKET} Starting Flask backend on port $FLASK_PORT..."

if command -v gnome-terminal &> /dev/null; then
    gnome-terminal --tab --title="Flask Backend" -- bash -c "cd '$PROJECT_ROOT' && source '$PROJECT_ROOT/venv/bin/activate' && PYTHONPATH='$PROJECT_ROOT':${PYTHONPATH:-} TESTING=false PORT=$FLASK_PORT python -m mvp_site.main serve || (echo 'Flask exited with status $?'; read -p 'Press enter to close'); exec bash"
elif command -v xterm &> /dev/null; then
    xterm -title "Flask Backend" -e "cd '$PROJECT_ROOT' && source '$PROJECT_ROOT/venv/bin/activate' && PYTHONPATH='$PROJECT_ROOT':${PYTHONPATH:-} TESTING=false PORT=$FLASK_PORT python -m mvp_site.main serve; echo 'Flask exited with status $?'; read -p 'Press enter to close'" &
else
    # Fallback: run in background
    echo "${EMOJI_INFO} Running Flask in background (no terminal emulator found)"
    # Check if venv is still active in subshell, if not reactivate it
    (
        cd "$PROJECT_ROOT" || exit 1
        if [ -z "$VIRTUAL_ENV" ] && [ -f "$PROJECT_ROOT/venv/bin/activate" ]; then
            # shellcheck disable=SC1091
            source "$PROJECT_ROOT/venv/bin/activate"
        fi
        GEMINI_API_KEY="$GEMINI_API_KEY" \
        CEREBRAS_API_KEY="$CEREBRAS_API_KEY" \
        PYTHONPATH="$PROJECT_ROOT:${PYTHONPATH:-}" \
        TESTING=false \
        PORT=$FLASK_PORT \
        python -m mvp_site.main serve
    ) &
    FLASK_PID=$!
    echo "${EMOJI_INFO} Flask backend started in background (PID: $FLASK_PID)"
fi

# Give Flask time to start
echo "${EMOJI_CLOCK} Waiting for Flask to initialize..."
sleep 3

# Validate Flask is running
if ! validate_server $FLASK_PORT 5 2; then
    echo "${EMOJI_ERROR} Flask backend failed to start properly"
    exit 1
fi

# Start MCP Server for WorldArchitect.AI (Production Mode - HTTP for local development)
echo ""
echo "${EMOJI_ROCKET} Starting MCP server in production mode..."

# Find available MCP port (default 8001)
DEFAULT_MCP_PORT=${MCP_SERVER_PORT:-8001}
DETECTED_PORT=$(find_available_port $DEFAULT_MCP_PORT 10)
if [ $? -eq 0 ] && [ -n "$DETECTED_PORT" ]; then
    MCP_PORT="$DETECTED_PORT"
else
    echo "${EMOJI_WARNING} Could not find available port for MCP server, forcing default $DEFAULT_MCP_PORT"
    MCP_PORT="$DEFAULT_MCP_PORT"
fi

if command -v gnome-terminal &> /dev/null; then
    gnome-terminal --tab --title="MCP Server" -- bash -c "cd '$PROJECT_ROOT' && source '$PROJECT_ROOT/venv/bin/activate' && GEMINI_API_KEY='$GEMINI_API_KEY' CEREBRAS_API_KEY='$CEREBRAS_API_KEY' bash '$PROJECT_ROOT/scripts/start_mcp_production.sh' --host 127.0.0.1 --port $MCP_PORT; exec bash"
elif command -v xterm &> /dev/null; then
    xterm -title "MCP Server" -e "cd '$PROJECT_ROOT' && source '$PROJECT_ROOT/venv/bin/activate' && GEMINI_API_KEY='$GEMINI_API_KEY' CEREBRAS_API_KEY='$CEREBRAS_API_KEY' bash '$PROJECT_ROOT/scripts/start_mcp_production.sh' --host 127.0.0.1 --port $MCP_PORT" &
else
    # Fallback: run in background with dual transport (stdio + HTTP) using named pipe
    echo "${EMOJI_INFO} Running MCP server in background (no terminal emulator found)"
    GEMINI_API_KEY="$GEMINI_API_KEY" \
    CEREBRAS_API_KEY="$CEREBRAS_API_KEY" \
    "$PROJECT_ROOT/scripts/mcp_dual_background.sh" --host 127.0.0.1 --port $MCP_PORT &
    MCP_PID=$!
    echo "${EMOJI_INFO} MCP server started in background (PID: $MCP_PID, Port: $MCP_PORT)"
fi

# Navigate to frontend directory
if [ ! -d "mvp_site/frontend_v2" ]; then
    echo "${EMOJI_ERROR} ERROR: Frontend v2 directory not found!"
    echo "   Looking for: $(pwd)/mvp_site/frontend_v2"
    exit 1
fi

cd mvp_site/frontend_v2

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "${EMOJI_WARNING} Node modules not found. Installing dependencies..."
    npm install --ignore-scripts
    if [ $? -ne 0 ]; then
        echo "${EMOJI_ERROR} Failed to install npm dependencies"
        exit 1
    fi
fi

# Start React frontend with environment variables
echo ""
echo "${EMOJI_ROCKET} Starting React v2 frontend on port $REACT_PORT..."
echo "${EMOJI_INFO} Frontend will proxy API calls to Flask backend on port $FLASK_PORT"

# Set environment variables for React build
export PORT=$FLASK_PORT  # For vite.config.ts proxy target
export REACT_APP_API_URL="http://localhost:$FLASK_PORT"

# Function to safely export Firebase environment variables
setup_firebase_env() {
    # Source Firebase configuration from .bashrc with error handling
    if [ -f ~/.bashrc ]; then
        source ~/.bashrc 2>/dev/null || true
    fi

    # Export Firebase config with VITE_ prefix for frontend (safe quoting)
    export VITE_FIREBASE_API_KEY="${FIREBASE_API_KEY:-}"
    export VITE_FIREBASE_AUTH_DOMAIN="${FIREBASE_AUTH_DOMAIN:-}"
    export VITE_FIREBASE_PROJECT_ID="${FIREBASE_PROJECT_ID:-}"
    export VITE_FIREBASE_STORAGE_BUCKET="${FIREBASE_STORAGE_BUCKET:-}"
    export VITE_FIREBASE_MESSAGING_SENDER_ID="${FIREBASE_MESSAGING_SENDER_ID:-}"
    export VITE_FIREBASE_APP_ID="${FIREBASE_APP_ID:-}"
    export VITE_FIREBASE_MEASUREMENT_ID="${FIREBASE_MEASUREMENT_ID:-}"
}

# Function to build safe environment command for terminal spawning
build_env_command() {
    local port="$1"
    # Use printf to safely build command with proper escaping
    printf 'cd %q && source ~/.bashrc 2>/dev/null || true && export PORT=%q VITE_FIREBASE_API_KEY=%q VITE_FIREBASE_AUTH_DOMAIN=%q VITE_FIREBASE_PROJECT_ID=%q VITE_FIREBASE_STORAGE_BUCKET=%q VITE_FIREBASE_MESSAGING_SENDER_ID=%q VITE_FIREBASE_APP_ID=%q VITE_FIREBASE_MEASUREMENT_ID=%q && npx vite --port %q --host 0.0.0.0' \
        "$PROJECT_ROOT/mvp_site/frontend_v2" \
        "$port" \
        "${FIREBASE_API_KEY:-}" \
        "${FIREBASE_AUTH_DOMAIN:-}" \
        "${FIREBASE_PROJECT_ID:-}" \
        "${FIREBASE_STORAGE_BUCKET:-}" \
        "${FIREBASE_MESSAGING_SENDER_ID:-}" \
        "${FIREBASE_APP_ID:-}" \
        "${FIREBASE_MEASUREMENT_ID:-}" \
        "$REACT_PORT"
}

echo "${EMOJI_GEAR} Setting up Firebase environment variables..."
setup_firebase_env
echo "${EMOJI_CHECK} Firebase configuration loaded for React V2"

# Start the React development server using safe environment handling
if command -v gnome-terminal &> /dev/null; then
    ENV_COMMAND=$(build_env_command "$FLASK_PORT")
    gnome-terminal --tab --title="React Frontend" -- bash -c "$ENV_COMMAND; exec bash"
elif command -v xterm &> /dev/null; then
    ENV_COMMAND=$(build_env_command "$FLASK_PORT")
    xterm -title "React Frontend" -e bash -c "$ENV_COMMAND" &
else
    # Fallback: run in background (already safe)
    echo "${EMOJI_INFO} Running React in background (no terminal emulator found)"
    (
        cd "$PROJECT_ROOT/mvp_site/frontend_v2" || exit 1
        setup_firebase_env
        export PORT=$FLASK_PORT
        npx vite --port $REACT_PORT --host 0.0.0.0
    ) &
    REACT_PID=$!
    echo "${EMOJI_INFO} React frontend started in background (PID: $REACT_PID)"
fi

# Comprehensive health checks for both servers
echo ""
echo "${EMOJI_SEARCH} Performing comprehensive health checks..."
echo "-------------------------------------------------------------"

# Initialize health status flags
FLASK_OK=true
REACT_OK=true
# Wait a bit more for React to fully start
echo "${EMOJI_CLOCK} Waiting for React frontend to initialize..."
sleep 5

# Validate Flask backend again
echo "${EMOJI_TARGET} Testing Flask backend..."
if ! validate_server $FLASK_PORT 3 2; then
    echo "${EMOJI_ERROR} Flask backend health check failed"
    kill_worldarchitect_servers true
    exit 1
fi

# Validate React frontend
echo "${EMOJI_TARGET} Testing React frontend..."
if ! validate_server $REACT_PORT 8 3; then
    echo "${EMOJI_ERROR} React frontend health check failed"
    echo "${EMOJI_INFO} This is common - React may take longer to start"
    echo "${EMOJI_INFO} Flask backend is working. Check React manually if needed."
    REACT_OK=false
fi

# Final validation - test API endpoint
echo "${EMOJI_TARGET} Testing API connectivity..."
if curl -s -f --max-time 3 "http://localhost:$FLASK_PORT/api/campaigns" > /dev/null 2>&1; then
    echo "${EMOJI_CHECK} API endpoint responding correctly"
elif curl -s --max-time 3 "http://localhost:$FLASK_PORT/api/campaigns" 2>/dev/null | grep -q "No token provided"; then
    echo "${EMOJI_CHECK} API endpoint responding correctly (authentication required)"
else
    echo "${EMOJI_WARNING} API endpoint test inconclusive"
fi

echo ""
if [ "$FLASK_OK" = true ] && [ "$REACT_OK" = true ]; then
    echo "${EMOJI_CHECK} Health checks completed successfully!"
elif [ "$FLASK_OK" = true ] && [ "$REACT_OK" = false ]; then
    echo "${EMOJI_WARNING} Backend healthy; React may still be starting. Proceed to the frontend URL and refresh."
else
    echo "${EMOJI_ERROR} Health checks did not complete successfully."
fi
echo ""
echo "${EMOJI_INFO} Server URLs:"
echo "   - Flask Backend:  http://localhost:$FLASK_PORT"
echo "   - React Frontend: http://localhost:$REACT_PORT"
echo "   - MCP Server:     http://localhost:${MCP_PORT:-8001} (Production mode)"
echo ""
echo "${EMOJI_INFO} For authentication bypass in development:"
echo "   http://localhost:$REACT_PORT?test_mode=true&test_user_id=test-user-123"
echo ""
echo "${EMOJI_GEAR} To stop servers:"
echo "   - Close terminal tabs, or"
echo "   - Run: pkill -f 'python.*main.py.*serve' && pkill -f 'node.*vite' && pkill -f \"python.*(mcp_api.py|mvp_site\\\\.mcp_api)\""
echo ""
echo "Press Ctrl+C to exit this script (servers will continue running in background)"

# Wait for user to exit
MCP_PROCESS_PATTERN="python.*(mcp_api.py|mvp_site\\.mcp_api)"
while true; do
    sleep 10
    # Check if servers are still running
    if ! ps aux | grep -E "python -m mvp_site\.main serve" | grep -v grep > /dev/null; then
        echo "${EMOJI_WARNING} Flask backend appears to have stopped"
        break
    fi
    if ! ps aux | grep -E "node.*vite" | grep -v grep > /dev/null; then
        echo "${EMOJI_WARNING} React frontend appears to have stopped"
        break
    fi
    if ! ps aux | grep -E "$MCP_PROCESS_PATTERN" | grep -v grep > /dev/null; then
        echo "${EMOJI_WARNING} MCP server appears to have stopped"
        # Don't break for MCP server - it's not critical for the web interface
    fi
done
