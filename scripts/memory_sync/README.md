# Memory MCP Synchronization System

Dropbox-like synchronization for Memory MCP across multiple development machines.

## Architecture

```
[Machine A] ←→ [GitHub Backup Repo] ←→ [Machine B]
     ↓                                      ↓
[Local Cache]                        [Local Cache]
     ↓                                      ↓
[Memory MCP]                        [Memory MCP]
```

## Components

### 1. fetch_memory.py
Pulls latest memory data from backup repository and converts from JSONL format (repo) to array format (MCP cache). Python version with enhanced git conflict handling.

```bash
python3 ./scripts/memory_sync/fetch_memory.py
```

### 2. merge_memory.py
CRDT-based conflict resolution using Last-Write-Wins strategy. Merges local cache with repo data.

```bash
python3 ./scripts/memory_sync/merge_memory.py
```

### 3. backup_memory_enhanced.py
Enhanced backup script with fetch-before-backup capability. Handles git conflicts gracefully.

```bash
python3 ./scripts/memory_sync/backup_memory_enhanced.py
```

### 4. setup_memory_sync.sh
Complete setup for new machines including repository cloning, cron jobs, and convenience commands.

```bash
./scripts/memory_sync/setup_memory_sync.sh
```

## Data Formats

- **MCP Cache**: `~/.cache/mcp-memory/memory.json` (JSON array format)
- **Backup Repo**: `~/projects/worldarchitect-memory-backups/memory.json` (JSONL format)

## CRDT Conflict Resolution

Uses Last-Write-Wins based on timestamp comparison:
- `timestamp` field (primary)
- `last_updated` field (secondary)  
- `created_at` field (tertiary)
- `_crdt_metadata.timestamp` field (quaternary)

## Usage

### Manual Sync Commands
```bash
# Pull latest from backup repo
fetch-memory

# Merge local changes with repo  
merge-memory

# Push local changes to backup repo
backup-memory
```

### Automatic Sync
- Hourly cron job: `0 * * * * python3 backup_memory_enhanced.py`
- Logs: `~/.cache/mcp-memory/backup.log`

## Setup for New Machine

1. Run setup script:
```bash
git clone https://github.com/jleechanorg/worldarchitect.ai.git
cd worldarchitect.ai/worktree_human
./scripts/memory_sync/setup_memory_sync.sh
```

2. Verify setup:
```bash
fetch-memory
backup-memory
```

## Features

✅ **Dropbox-like Sync**: Automatic synchronization across multiple machines  
✅ **CRDT Conflict Resolution**: Last-Write-Wins strategy for concurrent edits  
✅ **Format Conversion**: Seamless conversion between MCP (array) and repo (JSONL) formats  
✅ **Git Integration**: Full version control with conflict detection  
✅ **Cron Automation**: Hourly background synchronization  
✅ **Convenience Commands**: Simple `fetch-memory`, `merge-memory`, `backup-memory` commands  
✅ **Error Handling**: Graceful fallback when network unavailable  
✅ **Setup Automation**: One-command setup for new machines  

## Implementation Status

- ✅ Core CRDT merge logic
- ✅ Format conversion (JSONL ↔ Array)
- ✅ Fetch and backup scripts
- ✅ Setup automation
- ✅ Git conflict detection
- 🔄 Git conflict auto-resolution (needs enhancement)
- 🔄 Integration with claude_mcp.sh startup

## Next Steps

1. Enhance git conflict resolution with automatic stash/merge
2. Integrate with Memory MCP startup sequence
3. Add monitoring and health checks
4. Create status dashboard for sync health