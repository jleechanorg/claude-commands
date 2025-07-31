# MCP Architecture Deployment Guide

## Quick Start

**Default (Recommended)**: Direct calls mode - single process
```bash
python main.py serve
```

**Two-process mode**: HTTP communication with separate MCP server
```bash
# Terminal 1: Start MCP server
python world_logic.py

# Terminal 2: Start Flask app with HTTP mode
python main.py serve --mcp-http
```

## Command Line Options

```bash
python main.py serve [OPTIONS]

Options:
  --mcp-http                Use HTTP communication with MCP server 
                           (default: direct calls for easier deployment)
  --mcp-server-url URL     MCP server URL (default: http://localhost:8000)
```

## Environment Variables

```bash
MCP_SERVER_URL=url     # Custom MCP server URL (default: http://localhost:8000)
```

## Cloud Run Deployment

The default configuration works out-of-the-box with Cloud Run:

```bash
./deploy.sh mvp_site       # Deploys with direct calls (default)
```

**No additional configuration needed** - the Dockerfile and deploy script already use the optimal settings.

## Architecture Modes

### Direct Calls Mode (Default)
- **Single process**: Flask app directly imports and calls world_logic.py
- **Benefits**: Simpler deployment, no network overhead, easier Cloud Run setup
- **Use case**: Production deployments, Cloud Run, single-instance scenarios

### HTTP Mode 
- **Two processes**: Flask app (8081) → HTTP → MCP server (8000)  
- **Benefits**: True separation, can scale independently, debugging isolation
- **Use case**: Development, microservices architecture, distributed deployments

## Troubleshooting

**Error**: `Connection refused [Errno 111]` on `localhost:8000`
- **Cause**: Using `--mcp-http` flag but MCP server not running
- **Fix**: Either remove `--mcp-http` flag (use direct calls) or start MCP server first

**Cloud Run deployment issues**:
- **Default config works**: No changes needed, uses direct calls automatically
- **If you need HTTP mode**: Deploy both services and configure networking

## Testing

```bash
# Test direct calls (default)
python main.py serve

# Test HTTP mode (requires MCP server running)
python world_logic.py &  # Start MCP server
python main.py serve --mcp-http
```