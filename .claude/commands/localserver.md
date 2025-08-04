# /localserver

Starts the local development server for testing with health verification.

## Usage
```
/localserver [--stable]
```

**Options:**
- `--stable`: Disable auto-reload for stable campaign creation testing (debug mode enabled by default)

## What it does
1. **Lists all running servers** with branch names and PIDs
2. **Automatically kills conflicting processes** on target ports (5005 for Flask)
3. **Ensures port availability** by force-killing any processes using the required ports
4. Activates the virtual environment
5. Sets TESTING=true (for mock AI responses)
6. **Uses fixed ports** (Flask: 5005, React V2: served at /v2 path)
7. Starts Flask server on port 5005
8. Serves React V2 frontend at /v2 path (no separate server needed)
9. **Performs health checks with curl** to verify server responds correctly
10. **Validates server startup** before declaring success
11. Reports actual server status (✅ Ready or ❌ Failed)

## Implementation
Executes the `./run_local_server.sh` script which:
1. **Force-kills processes** on port 5005 to ensure availability
2. **Starts Flask server** on fixed port 5005
3. **Performs curl validation** to verify server responds correctly
4. **Reports final status** based on actual health check results

## Health Verification
- **Flask backend API**: `curl http://localhost:5005/` (expects HTTP 200)
- **React V2 frontend**: `curl http://localhost:5005/v2/` (expects correct content)
- **Content verification**: Checks for "WorldArchitect.AI" title in React app
- **Failure handling**: If health checks fail, provides diagnostic information
- **Success criteria**: Both API and React V2 must respond before declaring "ready"
- **Mandatory validation**: Server startup always includes curl validation step

## Fixed Port Assignment
- **Flask Server**: Always uses port 5005
- **React V2 Frontend**: Served at `/v2` path on Flask server (no separate port)
- **Port Management**: Automatically kills any processes using port 5005
- **Simplicity**: No dynamic port finding - consistent port usage
- **Reliability**: Eliminates port conflicts through force-killing

## Server Management
- **Lists all running servers** with their branch names and PIDs
- **Automatic process killing** for conflicting processes on port 5005
- **Force cleanup**: Kills any processes using required ports before starting
- **Process verification**: Uses `lsof` to identify and terminate port conflicts
- **Cleanup commands**:
  ```bash
  # Automatic cleanup (built into script):
  lsof -ti:5005 | xargs kill -9  # Kill processes on port 5005
  pkill -f 'python.*main.py'     # Stop all Flask servers (manual)
  ```

## Notes
- The server runs in testing mode (no real AI API calls)
- **Debug mode is enabled by default** for development auto-reload (use --stable to disable for campaign testing)
- **Aggressive process management**: Automatically kills conflicting processes on port 5005
- **Fixed port usage**: Always uses port 5005 for predictable development
- **Health checks are mandatory** - includes curl validation to verify server response
- **Startup validation**: Never declares success without confirming server responds to requests
