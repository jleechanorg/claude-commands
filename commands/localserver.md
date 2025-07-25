# /localserver

Starts the local development server for testing.

## Usage
```
/localserver
```

## What it does
1. Kills any existing Python server processes
2. Activates the virtual environment
3. Sets TESTING=true (for mock AI responses)
4. Starts Flask server on port 5005
5. Server accessible at http://localhost:5005

## Implementation
Executes the `./run_local_server.sh` script which handles all the setup and startup.

## Notes
- The server runs in testing mode (no real AI API calls)
- Debug mode is enabled
- Press Ctrl+C to stop the server
- If port 5005 is busy, edit PORT in run_local_server.sh