# Fix: Robust MCP Port Handling in run_local_server.sh

The script `run_local_server.sh` can pass an empty port argument to the MCP server if `find_available_port` fails, causing startup crashes.

## Issues
1. `MCP_PORT=$(find_available_port $MCP_PORT 10)` overwrites `MCP_PORT` with the command output.
2. If the command fails or returns empty output, `MCP_PORT` becomes empty.
3. The subsequent `if [ $? -ne 0 ]` block logs a warning but proceeds with the empty `MCP_PORT`.

## Required Fixes
Modify `run_local_server.sh` around line 207:

1. Capture the exit code of `find_available_port`.
2. Only update `MCP_PORT` if the command succeeded and returned a value.
3. Fallback to a default (e.g., 8001) if detection fails.

## Example Logic
```bash
DEFAULT_MCP_PORT=${MCP_SERVER_PORT:-8001}
DETECTED_PORT=$(find_available_port $DEFAULT_MCP_PORT 10)
if [ $? -eq 0 ] && [ -n "$DETECTED_PORT" ]; then
    MCP_PORT="$DETECTED_PORT"
else
    echo "${EMOJI_WARNING} Could not find available port, forcing default $DEFAULT_MCP_PORT"
    MCP_PORT="$DEFAULT_MCP_PORT"
fi
```
