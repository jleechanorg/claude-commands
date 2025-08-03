# /localserver

Starts the local development server for testing with health verification.

## Usage
```
/localserver [--stable]
```

**Options:**
- `--stable`: Disable auto-reload for stable campaign creation testing (debug mode enabled by default)

## What it does
1. **Detects current git branch** and calculates branch-specific ports
2. **Lists all running servers** with branch names and PIDs
3. **Warns if >5 servers running** with cleanup recommendations
4. **Checks for existing servers** (doesn't kill automatically)
5. Activates the virtual environment
6. Sets TESTING=true (for mock AI responses)
7. **Finds available ports** starting from branch-specific port (hash-based)
8. Starts Flask server on available port
9. Serves React V2 frontend at /v2 path (no separate server needed)
10. **Performs health checks to verify servers respond**
11. Reports actual server status (✅ Ready or ❌ Failed)

## Implementation
Executes the `./run_local_server.sh` script which handles all the setup and startup, then performs automatic health verification using curl.

## Health Verification
- **Flask backend API**: `curl http://localhost:{port}/` (expects HTTP 200)
- **React V2 frontend**: `curl http://localhost:{port}/v2/` (expects correct content)
- **Content verification**: Checks for "WorldArchitect.AI" title in React app
- **Failure handling**: If health checks fail, provides diagnostic information
- **Success criteria**: Both API and React V2 must respond before declaring "ready"

## Branch-Based Port Assignment
- **Algorithm**: MD5 hash of branch name → port offset (mod 1000)
- **Base ports**: Flask 8081, React 3001
- **Example**: Branch `feature-x` might get Flask port 8547, React port 3467
- **Fallback**: If branch port is busy, finds next available port
- **Benefit**: Different branches won't compete for same ports

## Server Management
- **Lists all running servers** with their branch names and PIDs
- **Shows total count** of running servers
- **Warning threshold**: >5 servers triggers cleanup recommendation
- **Cleanup commands**:
  ```bash
  pkill -f 'python.*main.py'  # Stop all Flask servers
  pkill -f 'vite'             # Stop all Vite servers
  kill <pid>                  # Stop specific server
  ```

## Notes
- The server runs in testing mode (no real AI API calls)
- **Debug mode is enabled by default** for development auto-reload (use --stable to disable for campaign testing)
- **Non-destructive**: Warns about existing servers but doesn't kill them
- **Smart port detection**: Branch-specific ports with automatic fallback
- **Health checks are mandatory** - never trust startup logs alone
