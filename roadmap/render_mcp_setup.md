# MCP Server Deployment on Render.com (Alongside Existing Flask App)

This guide explains how to deploy the WorldArchitect Game MCP server on Render.com alongside your existing Flask application deployment.

## Prerequisites

- Existing Flask app already deployed on Render.com
- GitHub repository with MCP server integration (this PR)
- Render.com account with existing service
- Environment secrets already configured for Flask app

## Deployment Options

### Option 1: Single Service (Recommended)
Deploy both Flask and MCP server in the same Render service using different ports.

#### Step 1: Update Existing Service

Your existing Flask service can be modified to also start the MCP server:

1. **Update Start Command** in Render dashboard:
   ```bash
   ./start_game_mcp.sh start && gunicorn --bind 0.0.0.0:$PORT mvp_site.main:app
   ```

2. **Environment Variables** (add to existing ones):
   ```
   MCP_PORT=7000
   MCP_HOST=0.0.0.0
   ```

3. **Service Configuration**:
   - Main Flask app runs on `$PORT` (assigned by Render)
   - MCP server runs on port `7000`
   - Both accessible via the same Render URL

#### Step 2: Access Endpoints

- **Flask App**: `https://your-service.onrender.com/`
- **MCP Health**: `https://your-service.onrender.com:7000/health`
- **MCP JSON-RPC**: `https://your-service.onrender.com:7000/rpc`

### Option 2: Separate Service
Deploy MCP server as a dedicated Render service.

#### Step 1: Create New Web Service

1. **Repository**: Same repository, different start command
2. **Start Command**:
   ```bash
   python mvp_site/mcp_api.py --port $PORT --host 0.0.0.0
   ```
3. **Environment Variables**: Copy from existing Flask service
4. **Plan**: Free tier sufficient for MCP server

#### Step 2: Service URLs

- **Main Flask**: `https://worldarchitect-web.onrender.com/`
- **MCP Server**: `https://worldarchitect-mcp.onrender.com/`

## Configuration

### Environment Variables Required

```bash
# Existing Flask app variables (already configured)
GEMINI_API_KEY=your_gemini_key
FIREBASE_CREDENTIALS_JSON={"type":"service_account",...}

# Additional for MCP server
MCP_PORT=7000  # Or $PORT for separate service
MCP_HOST=0.0.0.0
PYTHONPATH=/opt/render/project/src
```

### Render.yaml (Optional)

```yaml
services:
  - type: web
    name: worldarchitect-web
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: ./start_game_mcp.sh start && gunicorn --bind 0.0.0.0:$PORT mvp_site.main:app
    envVars:
      - key: MCP_PORT
        value: 7000
      - key: MCP_HOST
        value: 0.0.0.0
```

## Cost Analysis

### Single Service (Option 1)
- **Cost**: Same as current Flask deployment ($0-$7/month)
- **Resources**: Shared between Flask and MCP server
- **Scaling**: Both services scale together

### Separate Service (Option 2)
- **Flask Service**: Current cost unchanged
- **MCP Service**: Additional $0-$7/month
- **Total**: Up to $14/month for both services
- **Scaling**: Independent scaling

## Testing Deployment

### 1. Health Check
```bash
curl https://your-service.onrender.com:7000/health
# Expected: {"status": "healthy", "server": "world-logic"}
```

### 2. MCP Tools List
```bash
curl -X POST https://your-service.onrender.com:7000/rpc \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}'
```

### 3. Claude MCP Configuration
```bash
# Single service
claude mcp add-json --scope user "worldarchitect-render" \
  '{"type": "http", "url": "https://your-service.onrender.com:7000/rpc"}'

# Separate service
claude mcp add-json --scope user "worldarchitect-mcp" \
  '{"type": "http", "url": "https://worldarchitect-mcp.onrender.com/rpc"}'
```

## Troubleshooting

### Common Issues

1. **Port Conflicts**: Ensure MCP_PORT (7000) doesn't conflict with Flask PORT
2. **Environment Variables**: Copy all secrets from existing Flask service
3. **Build Failures**: Verify all dependencies in requirements.txt
4. **Import Errors**: Ensure PYTHONPATH includes project root

### Logs Access

```bash
# View service logs in Render dashboard
# Or via Render CLI:
render logs -s your-service-name --tail
```

### Health Monitoring

- **Flask Health**: Standard Render health checks
- **MCP Health**: Custom endpoint at `/health`
- **Both services**: Monitor through Render dashboard

## Migration Strategy

1. **Test Locally**: Verify MCP server works with `./start_game_mcp.sh`
2. **Deploy to Staging**: Use Render preview deployments
3. **Update Production**: Modify existing service start command
4. **Verify**: Test both Flask and MCP endpoints
5. **Claude Integration**: Update MCP client configuration

This approach leverages your existing Render.com setup while adding MCP server capability with minimal additional cost and complexity.
