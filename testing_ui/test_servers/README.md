# Test Servers

This directory contains specialized test servers for different testing scenarios.

## Servers

- `debug_server.py` - Server with enhanced debugging capabilities
- `monitored_test_server.py` - Server with comprehensive logging and monitoring
- `run_server_testing_mode.py` - Runs the main server in testing mode
- `start_test_server.py` - Simple test server starter
- `test_server_fixed.py` - Test server with specific fixes applied

## Usage

To start a test server:
```bash
python3 test_servers/server_name.py
```

Most servers run on port 8086 by default and have `TESTING=true` enabled for faster AI responses.

## Features

- Enhanced error logging
- Request/response monitoring
- Test authentication bypass
- Debug output
- JSON error responses