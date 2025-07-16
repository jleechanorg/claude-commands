# Memory MCP Storage

This directory contains the Memory MCP (Model Context Protocol) storage system for persistent knowledge management.

## Files

### `memory.json`
- **Purpose**: Persistent knowledge graph storage
- **Format**: JSON entities and relations from Memory MCP
- **Updates**: Hourly automatic backups from local MCP storage
- **Constraints**: Append-only (no data shrinkage or modification allowed)
- **Local Source**: `$MEMORY_FILE` (default: `~/.cache/mcp-memory/memory.json`)

### `backup_memory.sh`
- **Purpose**: Automated backup script with conflict resolution
- **Schedule**: Runs hourly via crontab (`0 * * * *`)
- **Features**:
  - Pulls latest changes before backup
  - Validates append-only constraint (no data shrinkage)
  - Resolves conflicts by preserving append-only version
  - Pushes to main branch with proper commit messages
  - Returns to original branch after backup
- **Error Handling**: Exits with error if append-only constraint violated

## Integration

### Memory MCP
- Used by `/learn` command for persistent knowledge storage
- Entities: `learning`, `pattern`, `lesson`, `context`
- Relations: `relates_to`, `caused_by`, `prevents`, `applies_to`
- Cross-conversation persistence

### Backup Process
1. Local Memory MCP updates (`/home/jleechan/.cache/mcp-memory/memory.json`)
2. Hourly cron job runs `backup_memory.sh`
3. Script validates append-only constraint
4. Copies to `memory/memory.json` in main repo
5. Commits and pushes to main branch with conflict resolution

## Safety Features

- **Append-Only Validation**: File size must only increase
- **Content Integrity**: Existing data cannot be modified
- **Conflict Resolution**: Automatic handling of concurrent updates
- **Rollback Protection**: Script exits if data constraints violated
- **Branch Management**: Preserves current working branch

## Deployment

After updating the backup script in this repo, deploy it to the stable location:

```bash
# Deploy script to stable location
cp memory/backup_memory.sh $HOME/backup_memory.sh
chmod +x $HOME/backup_memory.sh

# Update crontab to use stable path
(crontab -l | grep -v backup_memory; echo "0 * * * * $HOME/backup_memory.sh >> $HOME/.cache/mcp-memory/backup.log 2>&1") | crontab -
```

## Environment Variables

The backup script supports these environment variables for portability:

- **MEMORY_FILE**: Path to local memory.json file (default: `~/.cache/mcp-memory/memory.json`)
- **REPO_DIR**: Path to worldarchitect.ai repository (auto-detected if not set)

## Usage

The memory system runs automatically. For manual backup:

```bash
# Run backup manually
./memory/backup_memory.sh

# Check backup status
tail -f /home/jleechan/.cache/mcp-memory/backup.log

# View memory contents
cat memory/memory.json | jq '.'
```

## Troubleshooting

If backup fails:
1. Check `/home/jleechan/.cache/mcp-memory/backup.log` for errors
2. Verify append-only constraint wasn't violated
3. Ensure no concurrent modifications to memory.json
4. Check git repository status for conflicts