#!/bin/bash

# WorldArchitect.AI Local Development Server
# This script starts both Flask backend and React v2 frontend servers

echo "WorldArchitect.AI Development Server Launcher"
echo "==========================================="

# Function to check if a port is in use
is_port_in_use() {
    local port=$1
    if command -v lsof &> /dev/null; then
        lsof -i :$port &> /dev/null
    else
        netstat -an 2>/dev/null | grep -q ":$port.*LISTEN"
    fi
}

# Function to find next available port starting from a given port
find_available_port() {
    local start_port=$1
    local port=$start_port

    while is_port_in_use $port; do
        echo "Port $port is already in use, trying $((port + 1))..."
        port=$((port + 1))
    done

    echo $port
}

# Kill any existing server processes
echo "Stopping any existing servers..."
pkill -f "python.*main.py" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true
pkill -f "node.*vite" 2>/dev/null || true
sleep 2

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "ERROR: Virtual environment not found!"
    echo "Please run: python3 -m venv venv"
    exit 1
fi

# Set environment variables
export TESTING=true

# Find available port for Flask (starting from 5005)
FLASK_PORT=$(find_available_port 5005)
export PORT=$FLASK_PORT

# Start Flask backend in a new terminal/tab if possible
echo ""
echo "Starting Flask backend on port $FLASK_PORT..."
if command -v gnome-terminal &> /dev/null; then
    gnome-terminal --tab --title="Flask Backend" -- bash -c "source venv/bin/activate && TESTING=true PORT=$FLASK_PORT python mvp_site/main.py serve; exec bash"
elif command -v xterm &> /dev/null; then
    xterm -title "Flask Backend" -e "source venv/bin/activate && TESTING=true PORT=$FLASK_PORT python mvp_site/main.py serve" &
else
    # Fallback: run in background
    (source venv/bin/activate && TESTING=true PORT=$FLASK_PORT python mvp_site/main.py serve) &
    FLASK_PID=$!
    echo "Flask backend started in background (PID: $FLASK_PID)"
fi

# Give Flask time to start
sleep 3

# Find available port for React (starting from 3001)
REACT_PORT=$(find_available_port 3001)

# Start React frontend
echo "Starting React v2 frontend on port $REACT_PORT..."
cd mvp_site/frontend_v2

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing React dependencies..."
    npm install
fi

# Start React in a new terminal/tab if possible
if command -v gnome-terminal &> /dev/null; then
    gnome-terminal --tab --title="React Frontend" -- bash -c "npm run dev -- --port $REACT_PORT; exec bash"
elif command -v xterm &> /dev/null; then
    xterm -title "React Frontend" -e "npm run dev -- --port $REACT_PORT" &
else
    # Fallback: run in foreground
    echo ""
    echo "==========================================="
    echo "Servers are starting:"
    echo "Flask backend: http://localhost:$FLASK_PORT"
    echo "React frontend: http://localhost:$REACT_PORT"
    echo ""
    echo "Press Ctrl+C to stop the React server"
    echo "You'll need to manually stop Flask if running in background"
    echo "==========================================="
    npm run dev -- --port $REACT_PORT
fi

# If we're using terminals, show the URLs
if command -v gnome-terminal &> /dev/null || command -v xterm &> /dev/null; then
    echo ""
    echo "==========================================="
    echo "Development servers launched!"
    echo "Flask backend: http://localhost:$FLASK_PORT"
    echo "React frontend: http://localhost:$REACT_PORT"
    echo ""
    echo "Servers are running in separate terminal windows/tabs"
    echo "Close the terminal windows to stop the servers"
    echo "==========================================="
fi
