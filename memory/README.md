# Memory MCP System

This directory contains the Memory MCP integration system for WorldArchitect.AI, providing persistent knowledge storage and compliance tracking.

## Quick Start

### Automated Setup (Recommended)

```bash
# Run the setup script from the project root
./memory/setup.sh
```

This will:
- Create necessary directories
- Configure backup worktree
- Deploy backup script
- Set up hourly cron job
- Test the backup system

### Manual Setup

If you prefer manual setup or the automated setup fails:

1. **Create directories:**
   ```bash
   mkdir -p ~/.cache/mcp-memory
   ```

2. **Create backup worktree:**
   ```bash
   git worktree add ~/worldarchitect-backup main
   ```

3. **Deploy backup script:**
   ```bash
   cp memory/backup_memory_portable.sh ~/backup_memory.sh
   chmod +x ~/backup_memory.sh
   ```

4. **Set up cron job:**
   ```bash
   (crontab -l 2>/dev/null; echo "0 * * * * ~/backup_memory.sh >> ~/.cache/mcp-memory/backup.log 2>&1") | crontab -
   ```

## System Components

### Core Files

- **`memory.json`** - Main memory data file (JSONL format)
- **`setup.sh`** - Automated setup script
- **`backup_memory_portable.sh`** - Portable backup script
- **`config.json`** - Configuration file (created by setup)

### Development Tools

- **`mock_mcp_reader.py`** - Mock Memory MCP reader for testing
- **`compliance_checker.py`** - Compliance checking system
- **`enhanced_header_command.py`** - Enhanced /header command with memory integration

### Legacy Files

- **`backup_memory.sh`** - Original backup script (user-specific)
- **`check_backup_version.sh`** - Version checking utility

## Features

### Memory Storage

The system uses a JSON Lines (JSONL) format where each line is a JSON object:

```json
{"type":"entity","name":"example","entityType":"learning","observations":["Example observation"]}
{"type":"relation","from":"entity1","to":"entity2","relationType":"relates_to"}
```

### Compliance Tracking

The system tracks compliance with CLAUDE.md rules:

- **Header violations** - Missing mandatory branch headers
- **Push verification** - Forgetting to push changes to remote
- **Import violations** - Inline imports instead of top-level
- **Test execution** - Skipping test runs

### Enhanced Commands

#### Enhanced /header Command

```bash
# Basic usage
python3 memory/enhanced_header_command.py

# Detailed compliance analysis
python3 memory/enhanced_header_command.py --verbose

# Show only header format
python3 memory/enhanced_header_command.py --quiet

# Show related learnings
python3 memory/enhanced_header_command.py --context header
```

#### Mock MCP Reader

```bash
# Test the mock reader
python3 memory/mock_mcp_reader.py

# Test compliance checker
python3 memory/compliance_checker.py
```

## Configuration

The system uses `config.json` for configuration:

```json
{
    "version": "1.0.0",
    "user_home": "/home/username",
    "repo_root": "/path/to/worldarchitect.ai",
    "memory_dir": "/path/to/memory",
    "memory_file": "/home/username/.cache/mcp-memory/memory.json",
    "backup_worktree": "/home/username/worldarchitect-backup",
    "is_fork": false,
    "backup_enabled": true,
    "backup_to_remote": true,
    "backup_interval_hours": 1,
    "max_backup_retries": 3,
    "log_file": "/home/username/.cache/mcp-memory/backup.log"
}
```

### Fork Support

For forked repositories, the system automatically:
- Detects fork status
- Enables local-only backup mode
- Disables remote push operations
- Maintains full functionality locally

## Backup System

### Append-Only Design

The backup system enforces strict append-only behavior:

1. **Size Check** - New file must be larger than existing
2. **Content Validation** - Existing data must be unchanged
3. **Conflict Resolution** - Validates data integrity during merges
4. **Rollback Protection** - Aborts on data corruption detection

### Backup Process

1. **Validation** - Check append-only constraints
2. **Worktree Management** - Use clean backup worktree
3. **Branch Switching** - Temporarily switch to main for backup
4. **Conflict Resolution** - Handle merge conflicts safely
5. **Remote Sync** - Push changes to GitHub (if not fork)
6. **Cleanup** - Return to safe branch (not main)

### Logs and Monitoring

- **Log Location**: `~/.cache/mcp-memory/backup.log`
- **Real-time Monitoring**: `tail -f ~/.cache/mcp-memory/backup.log`
- **Cron Job**: Hourly backups via crontab

## Memory MCP Integration

### Read Functions

The system provides three main read functions:

```python
# Get entire knowledge graph
graph = reader.read_graph()

# Search for entities by content
results = reader.search_nodes("compliance")

# Get specific entities by name
entities = reader.open_nodes(["Header Compliance Violation"])
```

### Compliance Analysis

```python
# Check header compliance with history
checker = HeaderComplianceChecker()
results = checker.check_header_compliance(verbose=True)

# Get violation patterns
patterns = compliance_reader.get_violation_patterns()

# Check if reminder needed
needs_reminder = compliance_reader.should_remind_about_rule("MANDATORY_HEADER")
```

### Learning Retrieval

```python
# Get learnings by category
learnings = learning_reader.get_learnings_by_category("commands")

# Get related learnings
related = learning_reader.get_related_learnings("header")

# Get learning knowledge graph
graph = learning_reader.get_learning_graph()
```

## Testing

### Unit Tests

```bash
# Test mock reader
python3 memory/mock_mcp_reader.py

# Test compliance checker
python3 memory/compliance_checker.py

# Test enhanced header command
python3 memory/enhanced_header_command.py --verbose
```

### Integration Tests

```bash
# Test backup script
~/backup_memory.sh

# Check backup logs
tail -20 ~/.cache/mcp-memory/backup.log

# Verify cron job
crontab -l | grep backup_memory
```

## Troubleshooting

### Common Issues

1. **Backup Worktree Missing**
   ```bash
   git worktree add ~/worldarchitect-backup main
   ```

2. **Permission Errors**
   ```bash
   chmod +x ~/backup_memory.sh
   ```

3. **Memory File Not Found**
   ```bash
   mkdir -p ~/.cache/mcp-memory
   echo '{"type":"entity","name":"test","entityType":"test","observations":["test"]}' > ~/.cache/mcp-memory/memory.json
   ```

4. **Cron Job Not Running**
   ```bash
   # Check cron service
   sudo systemctl status cron
   
   # Check cron logs
   grep backup_memory /var/log/syslog
   ```

### Fork Repository Issues

If you're using a fork of the repository:

1. **Local-Only Mode**: The system automatically detects forks and enables local-only backup
2. **No Remote Push**: Backup changes stay local to prevent unauthorized pushes
3. **Full Functionality**: All compliance tracking and learning features work normally

### Version Mismatches

The system checks for version mismatches between repository and deployed scripts:

```bash
# Update deployed script
cp memory/backup_memory_portable.sh ~/backup_memory.sh
```

## Development

### Adding New Compliance Rules

1. **Define Rule** in `compliance_checker.py`
2. **Add Detection** in `_extract_violation_type()`
3. **Update Recommendations** in `_generate_recommendations()`
4. **Test** with mock data

### Extending Memory Schema

1. **Add Entity Type** to memory data
2. **Update Reader** in `mock_mcp_reader.py`
3. **Add Analysis** in appropriate checker class
4. **Document** in this README

## Architecture

### Data Flow

```
Memory MCP → ~/.cache/mcp-memory/memory.json → Backup Script → GitHub
     ↓
Mock Reader → Compliance Checker → Enhanced Commands
```

### Security

- **Append-Only**: Prevents data corruption and loss
- **Validation**: Multiple integrity checks
- **Isolation**: Backup worktree prevents main branch conflicts
- **Logging**: Complete audit trail of all operations

## Future Enhancements

1. **Real MCP Integration** - Replace mock reader with actual Memory MCP calls
2. **Web Interface** - Browser-based compliance dashboard
3. **Advanced Analytics** - Pattern detection and trend analysis
4. **Integration Hooks** - Pre-response compliance checking
5. **Multi-User Support** - Shared memory pools for team collaboration

## Support

For issues or questions:

1. Check the troubleshooting section above
2. Review backup logs: `~/.cache/mcp-memory/backup.log`
3. Test components individually using the testing commands
4. Ensure all prerequisites are installed (git, jq, cron)

## License

This system is part of the WorldArchitect.AI project and follows the same license terms.