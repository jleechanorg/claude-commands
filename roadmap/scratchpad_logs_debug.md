# Scratchpad: Logging Debug Analysis

**Branch**: logs_debug  
**Goal**: Document root cause analysis of missing logs in /tmp/worldarchitectai_logs/  
**Status**: Analysis complete, ready for implementation handoff

## Problem Statement

Logs documented in CLAUDE.md as being in `/tmp/worldarchitectai_logs/[branch-name].log` are not appearing when running the application directly.

## Root Cause Analysis

### Current Logging Architecture

1. **`mvp_site/logging_util.py`**: 
   - Pure wrapper around Python's standard logging
   - No file handlers configured
   - Only provides console output with emoji enhancements

2. **`prototype/logging_config.py`**: 
   - Has proper file logging setup with FileHandler
   - Creates timestamped logs in `prototype/logs/`
   - NOT used by main application

3. **`test_server_manager.sh`**: 
   - Creates logs in `/tmp/worldarchitectai_logs/` via stdout/stderr redirection
   - Line 101: `nohup python3 mvp_site/main.py serve > "$BRANCH_LOG_FILE" 2>&1 &`
   - Only works when app runs through test server manager

### Evidence Found

- **`logging_util.py:138`**: Just calls `logging.basicConfig(**kwargs)` with no file configuration
- **`main.py`**: No logging setup code found in startup sequence
- **Existing logs**: Only 3 files in `/tmp/worldarchitectai_logs/` from test server runs
- **Current branch**: `logs_debug` - no log file exists for this branch

### The Gap

The main application has **zero file logging configuration**. When you run:
- `python mvp_site/main.py` → Console output only, no log files
- `./test_server_manager.sh start` → Creates log files via shell redirection

## Solution Required

Add file logging configuration to `mvp_site/main.py` that:

1. **Creates log directory**: Ensure `/tmp/worldarchitectai_logs/` exists
2. **Branch-specific logs**: Configure `logging_util.basicConfig()` with FileHandler pointing to `/tmp/worldarchitectai_logs/{branch_name}.log`
3. **Git integration**: Use `git branch --show-current` to get branch name
4. **Fallback handling**: Handle cases where git isn't available or outside repo

## Implementation Plan

### Step 1: Add logging setup function to `main.py`
```python
def setup_file_logging():
    """Configure file logging for current git branch."""
    import os
    import subprocess
    
    # Create log directory
    log_dir = "/tmp/worldarchitectai_logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Get current branch name
    try:
        branch = subprocess.check_output(
            ["git", "branch", "--show-current"], 
            cwd=os.path.dirname(__file__),
            text=True
        ).strip()
    except:
        branch = "unknown"
    
    # Configure file logging
    log_file = os.path.join(log_dir, f"{branch}.log")
    logging_util.basicConfig(
        level=logging_util.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging_util.StreamHandler(),  # Console
            logging_util.FileHandler(log_file)  # File
        ]
    )
    
    logging_util.info(f"File logging configured: {log_file}")
```

### Step 2: Call setup function in main.py startup
Add call to `setup_file_logging()` near the beginning of the Flask app initialization.

### Step 3: Test verification
- Run `python mvp_site/main.py` directly
- Verify log file appears in `/tmp/worldarchitectai_logs/logs_debug.log`
- Verify both console and file output work

## Files to Modify

- `mvp_site/main.py`: Add file logging setup function and call
- Potentially `mvp_site/logging_util.py`: Add any missing handler exports

## Testing Requirements

1. **Direct execution**: `python mvp_site/main.py` should create log files
2. **Test server compatibility**: Ensure `test_server_manager.sh` still works
3. **Branch switching**: Log files should update when switching branches
4. **Error handling**: Graceful fallback if git unavailable

## Context for Next Worker

This is a straightforward implementation task. The analysis is complete - the issue is simply that the main application never configures file logging, only console logging. The solution pattern already exists in `prototype/logging_config.py` and just needs to be adapted for the main application with branch-specific naming.

## Branch Status

- **Analysis**: ✅ Complete
- **Implementation**: ⏳ Ready for handoff
- **Testing**: ⏳ Pending implementation