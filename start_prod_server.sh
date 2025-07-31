#!/bin/bash
# Start WorldArchitect.AI in production mode with MCP architecture

set -e

# Kill any existing servers
echo "Stopping any existing servers..."
pkill -f "python.*main.py" 2>/dev/null || true
pkill -f "python.*mcp_api.py" 2>/dev/null || true
pkill -f "gunicorn" 2>/dev/null || true
sleep 2

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Set production environment variables
export FLASK_ENV=production
export FLASK_DEBUG=0
export TESTING=false
export PORT=8081
export MCP_SERVER_URL="http://localhost:8000"

echo "Starting MCP Architecture servers..."
echo "=================================="

# Start MCP server (world_logic.py) in background
echo "1. Starting MCP server on port 8000..."
cd mvp_site
python mcp_api.py --port 8000 --host localhost > /tmp/mcp_server.log 2>&1 &
MCP_PID=$!
cd ..

# Wait for MCP server to be ready
echo "   Waiting for MCP server to be ready..."
for i in {1..10}; do
    if curl -s "http://localhost:8000/health" > /dev/null 2>&1; then
        echo "   ✅ MCP server is ready!"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "   ❌ MCP server failed to start"
        echo "   Check logs: tail -f /tmp/mcp_server.log"
        exit 1
    fi
    sleep 1
done

# Start Flask API Gateway with Gunicorn
echo ""
echo "2. Starting Flask API Gateway on port $PORT..."
cd mvp_site
gunicorn -b 0.0.0.0:$PORT main:app \
    --workers 4 \
    --timeout 300 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --daemon

cd ..

# Wait for API Gateway to be ready
echo "   Waiting for API Gateway to be ready..."
for i in {1..10}; do
    if curl -s "http://localhost:$PORT" > /dev/null 2>&1; then
        echo "   ✅ API Gateway is ready!"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "   ❌ API Gateway failed to start"
        exit 1
    fi
    sleep 1
done

echo ""
echo "=================================="
echo "✅ WorldArchitect.AI is running in production mode!"
echo ""
echo "Services:"
echo "  - MCP Server: http://localhost:8000 (internal)"
echo "  - API Gateway: http://localhost:$PORT"
echo ""
echo "Access the application at: http://localhost:$PORT"
echo ""
echo "Logs:"
echo "  - MCP Server: tail -f /tmp/mcp_server.log"
echo "  - API Gateway: Check gunicorn output"
echo ""
echo "To stop all servers: pkill -f 'python.*mcp_api.py' && pkill -f 'gunicorn'"
