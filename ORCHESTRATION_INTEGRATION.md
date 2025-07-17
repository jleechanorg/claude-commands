# Orchestration Integration with Claude Code CLI

The orchestration system is now integrated to start automatically with Claude Code CLI.

## How It Works

### Automatic Startup
When you run `./claude_start.sh`, the script:
1. Checks if orchestration is already running
2. If not, starts it silently in the background
3. Shows available orchestration commands if successful
4. Continues with normal Claude startup

### Features
- **Silent Background Operation**: Orchestration starts without verbose output
- **Optional Feature**: If orchestration fails, Claude still starts normally
- **Always Available**: Once started, orchestration commands work in any Claude session

## Usage

### Starting Claude with Orchestration
```bash
# Just use the normal startup script
./claude_start.sh

# You'll see:
# 🔧 Checking orchestration system...
# ✅ Orchestration system started
# 🔍 Checking MCP servers...
# ...
# 💡 Orchestration commands available:
#    • /orch status     - Check orchestration status
#    • /orch Build X    - Delegate task to AI agents
#    • /orch help       - Show orchestration help
```

### Using Orchestration Commands
Once in Claude, you can use natural language orchestration:
```
/orch What's the status?
/orch Build a user authentication system
/orch Remove dead code from the codebase
/orch Fix all failing tests
```

### Manual Control
If needed, you can still manually control orchestration:
```bash
# Start orchestration manually
./orchestration/start_system.sh start

# Stop orchestration
./orchestration/start_system.sh stop

# Check status
./orchestration/start_system.sh status
```

## Key Benefits

1. **Zero Configuration**: No need to remember to start orchestration
2. **Seamless Integration**: Works automatically with Claude
3. **Non-Intrusive**: Doesn't affect Claude if orchestration fails
4. **Always Ready**: Orchestration commands available when needed

## Architecture

- `claude_start.sh`: Enhanced to check and start orchestration
- `orchestration/start_system.sh`: Supports `--quiet` flag for silent startup
- `/orch` command: Natural language interface to orchestration
- Real Claude Code CLI agents: Not simulated, actual Claude instances

## Troubleshooting

If orchestration doesn't start:
- Check Redis is installed: `redis-cli --version`
- Check tmux is installed: `tmux -V`
- View logs: `cat orchestration/logs/*.log`
- Start manually: `./orchestration/start_system.sh start`