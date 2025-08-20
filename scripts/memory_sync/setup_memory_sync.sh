#!/bin/bash
set -e

# Memory Sync Setup Script for New Machines
# Provides Dropbox-like synchronization for Memory MCP across multiple development environments

CACHE_DIR="$HOME/.cache/mcp-memory"
REPO_DIR="$HOME/projects/worldarchitect-memory-backups"
CACHE_FILE="$CACHE_DIR/memory.json"
REPO_FILE="$REPO_DIR/memory.json"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Setting up Memory MCP synchronization..."
echo "   Cache directory: $CACHE_DIR"
echo "   Backup repository: $REPO_DIR"

# Create cache directory
mkdir -p "$CACHE_DIR"

# Clone or update repository
if [ ! -d "$REPO_DIR" ]; then
    echo "📥 Cloning memory backup repository..."
    git clone https://github.com/jleechanorg/worldarchitect-memory-backups.git "$REPO_DIR"
else
    echo "🔄 Updating existing repository..."
    cd "$REPO_DIR" && git pull origin main
fi

# Initialize cache with repo data if cache is empty
if [ ! -f "$CACHE_FILE" ] || [ ! -s "$CACHE_FILE" ]; then
    echo "🔧 Initializing local memory cache..."
    if [ -f "$REPO_FILE" ]; then
        # Convert JSONL to array format for MCP cache using secure script
        python3 "$SCRIPT_DIR/convert_memory_format.py" "$REPO_FILE" "$CACHE_FILE"
    else
        echo "[]" > "$CACHE_FILE"
        echo "Initialized empty memory cache"
    fi
fi

# Setup cron job for automatic hourly sync
echo "⏰ Setting up hourly memory sync cron job..."
BACKUP_SCRIPT="$SCRIPT_DIR/backup_memory_enhanced.py"
CRON_JOB="0 * * * * /usr/bin/python3 $BACKUP_SCRIPT >> $HOME/.cache/mcp-memory/backup.log 2>&1"

# Remove existing memory backup cron jobs and add new one
(crontab -l 2>/dev/null | grep -v "backup_memory" || true; echo "$CRON_JOB") | crontab -

echo "✅ Cron job installed: hourly memory sync at :00 minutes"

# Create convenience symlinks
SYNC_DIR="$HOME/.local/bin"
mkdir -p "$SYNC_DIR"

# Symlink scripts for easy access
ln -sf "$SCRIPT_DIR/fetch_memory.py" "$SYNC_DIR/fetch-memory"
ln -sf "$SCRIPT_DIR/merge_memory.py" "$SYNC_DIR/merge-memory"  
ln -sf "$SCRIPT_DIR/backup_memory_enhanced.py" "$SYNC_DIR/backup-memory"

echo "🔗 Created convenience commands:"
echo "   fetch-memory  - Pull latest memory from backup repo"
echo "   merge-memory  - Manually merge cache and repo memories"
echo "   backup-memory - Push local memories to backup repo"

# Test the setup
echo "🧪 Testing memory sync setup..."
python3 "$SCRIPT_DIR/merge_memory.py"

# Initial backup to ensure everything works
echo "📤 Running initial backup..."
python3 "$BACKUP_SCRIPT"

echo ""
echo "🎉 Memory synchronization setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Memory MCP will now sync automatically every hour"
echo "   2. Use 'fetch-memory' to manually pull latest changes"
echo "   3. Use 'backup-memory' to manually push changes"
echo "   4. Logs are saved to: $HOME/.cache/mcp-memory/backup.log"
echo ""
echo "🔧 Architecture:"
echo "   • Local cache: $CACHE_FILE (array format for MCP)"
echo "   • Backup repo: $REPO_FILE (JSONL format for git)"
echo "   • CRDT merge resolves conflicts using Last-Write-Wins"
echo "   • Works across multiple machines like Dropbox"
echo ""
echo "✨ Your Memory MCP now has Dropbox-like synchronization!"