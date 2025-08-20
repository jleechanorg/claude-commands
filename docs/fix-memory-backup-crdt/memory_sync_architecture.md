# Memory Synchronization Architecture

## Overview

This system provides Dropbox-like synchronization for Claude Code's Memory MCP across multiple development machines. It uses CRDT (Conflict-free Replicated Data Type) principles to enable seamless bi-directional sync without data loss.

## Architecture Components

### 1. Core Scripts

#### `fetch_memory.sh`
- **Purpose**: Pulls latest memory.json from backup repository and merges with local data
- **Features**: 
  - CRDT-based conflict resolution using Last-Write-Wins semantics
  - Device-specific metadata tracking for unique entity identification
  - Network failure handling with retries and timeouts
  - Atomic file updates to prevent corruption
- **Integration**: Called before Memory MCP operations and by cron every 15 minutes

#### `memory_backup_crdt.sh` (Enhanced)
- **Purpose**: Bi-directional sync that fetches before backing up changes
- **Enhancement**: Now calls `fetch_memory.sh` before performing backup
- **Features**: 
  - Existing CRDT merge capabilities
  - Enhanced with pre-backup fetch for true bi-directional sync
  - Maintains all existing security and error handling

#### `setup_memory_sync.sh`
- **Purpose**: One-time setup script for new machines
- **Features**:
  - Dependency checking (git, jq, cron)
  - Repository cloning/updating
  - Directory structure creation
  - Cron job installation
  - Security validation and permission setting
  - Comprehensive testing and validation

### 2. Data Flow Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Machine A     │    │   GitHub Repo    │    │   Machine B     │
│                 │    │   (Central Hub)  │    │                 │
│ Memory MCP      │◄──►│ memory.json      │◄──►│ Memory MCP      │
│ ~/.cache/mcp-   │    │ memory-A.json    │    │ ~/.cache/mcp-   │
│ memory/memory.  │    │ memory-B.json    │    │ memory/memory.  │
│ json            │    │ memory-C.json    │    │ json            │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         ▲                        ▲                        ▲
         │                        │                        │
    ┌────▼────┐              ┌────▼────┐              ┌────▼────┐
    │ Cron    │              │ CRDT    │              │ Cron    │
    │ Every   │              │ Merge   │              │ Every   │
    │ 15 min  │              │ Logic   │              │ 15 min  │
    └─────────┘              └─────────┘              └─────────┘
```

### 3. CRDT Conflict Resolution

#### Metadata Structure
Each memory entity gets enriched with sync metadata:
```json
{
  "id": "original_entity_id",
  "content": "entity_data",
  "_sync_metadata": {
    "host": "machine_hostname",
    "timestamp": "2025-01-21T15:30:00Z",
    "id": "hostname_originalid_timestamp"
  }
}
```

#### Conflict Resolution Rules
1. **Last-Write-Wins (LWW)**: Entities with same ID, newest timestamp wins
2. **Union Merge**: Different entity IDs are combined without conflict
3. **Device Isolation**: Each machine's changes are uniquely identifiable
4. **Metadata Preservation**: Original Memory MCP format maintained for compatibility

## Directory Structure

```
$HOME/.cache/
├── mcp-memory/
│   ├── memory.json              # Memory MCP data file
│   └── logs/
│       └── memory_sync.log      # Synchronization logs
└── memory-backup-repo/          # Git repository clone
    ├── memory.json              # Unified CRDT-merged data
    ├── memory-hostname1.json    # Device-specific backups
    ├── memory-hostname2.json
    └── .last_fetch_sync         # Sync state tracking
```

## Integration Points

### 1. Memory MCP Integration
- **File Location**: `~/.cache/mcp-memory/memory.json` (unchanged)
- **Format Compatibility**: Maintains Memory MCP's expected JSON array format
- **Transparent Operation**: Memory MCP operations work normally, sync happens in background

### 2. Cron Integration
```bash
# Automatically installed cron jobs
*/15 * * * * /path/to/scripts/fetch_memory.sh >> ~/.cache/mcp-memory/logs/memory_sync.log 2>&1
*/15 * * * * /path/to/scripts/memory_backup_crdt.sh >> ~/.cache/mcp-memory/logs/memory_sync.log 2>&1
```

### 3. Git Repository Structure
- **Central Repository**: `https://github.com/jleechanorg/worldarchitect-memory-backups.git`
- **Branch Strategy**: Single `main` branch with CRDT merge handling conflicts
- **File Strategy**: 
  - `memory.json`: Unified view for consumption
  - `memory-{hostname}.json`: Device-specific contributions for debugging

## Security Measures

### 1. Path Validation
- Prevents directory traversal attacks
- Validates all file paths before operations
- Rejects symlinks for security

### 2. Permission Management
- Memory files: 600 (owner read/write only)
- Directories: 700 (owner access only)
- Scripts: 700 (owner execute only)

### 3. Input Validation
- JSON validation before file updates
- Git repository validation
- Script ownership verification

### 4. Timeout Protection
- All network operations have timeouts
- Prevents hanging processes
- Graceful degradation on failures

## Error Handling & Resilience

### 1. Network Failures
- **Offline Mode**: Continue working with local data when network unavailable
- **Retry Logic**: Multiple attempts with exponential backoff
- **Graceful Degradation**: Don't fail Memory MCP operations due to sync issues

### 2. Git Conflicts
- **CRDT Resolution**: Automatic conflict resolution using CRDT principles
- **Merge Strategy**: Always converges to consistent state across machines
- **Fallback**: Local data preserved if merge fails

### 3. Corruption Recovery
- **Atomic Updates**: File operations are atomic to prevent partial corruption
- **Backup Creation**: Corrupted files backed up before recreation
- **Validation**: JSON validation before accepting merged data

## Setup Process for New Machines

### 1. Initial Setup
```bash
# Clone/download the setup script
./scripts/setup_memory_sync.sh

# The script will:
# - Check dependencies (git, jq, cron)
# - Clone backup repository
# - Create directory structure
# - Install sync scripts
# - Configure cron jobs
# - Run initial sync
```

### 2. Automatic Discovery
- New machines automatically join the sync network
- No manual configuration required after initial setup
- Device-specific identification prevents conflicts

### 3. Validation
- Comprehensive testing during setup
- Real-time sync verification
- Log monitoring for ongoing health

## Performance Characteristics

### 1. Sync Frequency
- **Default**: Every 15 minutes
- **Configurable**: Can be adjusted in cron configuration
- **On-Demand**: Manual sync available via script execution

### 2. Network Efficiency
- **Incremental**: Only changed data is processed
- **Compressed**: Git handles data compression
- **Batched**: Multiple changes batched into single commits

### 3. Storage Efficiency
- **Deduplication**: Git handles storage deduplication
- **History**: Full change history preserved in Git
- **Pruning**: Old device-specific files can be cleaned up

## Monitoring & Debugging

### 1. Log Files
- **Location**: `~/.cache/mcp-memory/logs/memory_sync.log`
- **Content**: Detailed sync operations, errors, and timing
- **Rotation**: Logs will need manual rotation/cleanup

### 2. Status Checking
```bash
# View recent sync activity
tail -f ~/.cache/mcp-memory/logs/memory_sync.log

# Check current memory state
cat ~/.cache/mcp-memory/memory.json | jq .

# Verify cron jobs
crontab -l | grep memory

# Manual sync test
scripts/fetch_memory.sh --test
```

### 3. Troubleshooting Common Issues
- **Permission Errors**: Check file/directory permissions
- **Network Issues**: Verify Git repository access
- **JSON Corruption**: Check logs for validation errors
- **Cron Problems**: Verify cron service is running

## Migration from Existing System

### 1. Backward Compatibility
- Existing memory data is preserved
- Current Memory MCP operations continue working
- No disruption to ongoing development

### 2. Gradual Rollout
- Can be installed on one machine first
- Other machines can join the sync network incrementally
- Fallback to local-only operation if needed

### 3. Data Migration
- Existing `memory.json` automatically incorporated
- Historical data preserved through Git history
- Device-specific metadata added progressively

## Future Enhancements

### 1. Conflict Resolution UI
- Visual merge tool for complex conflicts
- Manual conflict resolution interface
- Conflict notification system

### 2. Performance Optimization
- Real-time sync using file watchers
- Differential sync for large datasets
- Compressed transfer protocols

### 3. Extended Metadata
- Change tracking and attribution
- Sync statistics and analytics
- Performance monitoring dashboard

This architecture provides a robust, scalable foundation for multi-machine Memory MCP synchronization while maintaining simplicity and reliability.