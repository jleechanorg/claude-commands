# Deprecated Server Scripts

**Created**: 2025-07-15  
**Status**: These scripts are deprecated in favor of the unified test server management system.

## Deprecated Scripts

### 1. `run_test_server.sh`
- **Replaced by**: `test_server_manager.sh` + `/testserver` command
- **Issues**: Single server only, no branch isolation, port conflicts
- **Migration**: Use `/testserver start` instead

### 2. `run_local_server.sh` 
- **Replaced by**: `test_server_manager.sh` with port 5005 allocation
- **Issues**: Hardcoded port 5005, no multi-branch support
- **Migration**: Use `/testserver start` (auto-allocates ports)

### 3. `tools/localserver.sh`
- **Replaced by**: Consolidated into `test_server_manager.sh`
- **Issues**: Duplicated functionality
- **Migration**: Use `/testserver` command

## Migration Guide

### Old Commands → New Commands

```bash
# OLD WAY
./run_test_server.sh start
./run_local_server.sh
./tools/localserver.sh start

# NEW WAY (standardized)
./claude_command_scripts/commands/testserver.sh start
# or directly:
./test_server_manager.sh start
```

### Benefits of New System

1. **Multi-branch support**: Each branch gets its own server and port
2. **Automatic port allocation**: No more port conflicts (8081-8090 range)
3. **Process management**: PID tracking, proper cleanup
4. **Branch-specific logging**: Logs stored by branch name
5. **Integration ready**: Works with `/push` and `/integrate` commands
6. **Status monitoring**: Easy to see what's running

### Features

- `/testserver start [branch]` - Start server for branch
- `/testserver stop [branch]` - Stop server for branch  
- `/testserver list` - Show all running servers
- `/testserver status` - Show current branch status
- `/testserver cleanup` - Stop all servers

## Cleanup Plan

These deprecated scripts should be removed after confirming no active usage:

1. `run_test_server.sh` - Check for references in scripts/docs
2. `run_local_server.sh` - Simple replacement, safe to remove
3. `tools/localserver.sh` - Verify no external dependencies

## References Updated

- [x] `claude_command_scripts/commands/push.sh` - Updated to use new system
- [x] Created `/testserver` command implementation
- [ ] Update documentation/README references
- [ ] Remove deprecated scripts after transition period