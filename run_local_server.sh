#!/bin/bash

# WorldArchitect.AI Local Development Server
# This script starts a local Flask development server for testing

# Kill any existing server processes
echo "Stopping any existing servers..."
pkill -f "python.*main.py" 2>/dev/null || true
sleep 1

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Set environment variables
export TESTING=true
export PORT=5005

# Start the server
echo "Starting development server on port $PORT..."
echo "Server will be available at: http://localhost:$PORT"
echo "Press Ctrl+C to stop the server"
echo ""

# Run the server
python mvp_site/main.py serve