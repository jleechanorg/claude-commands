#!/bin/bash
# WorldArchitect.AI - Memory MCP Backup Setup Script
# Sets up automatic hourly backups to memory-backup branch

set -e

echo "🔧 Setting up Memory MCP Backup System..."

# Check if memory directory exists
MEMORY_DIR="$HOME/.cache/mcp-memory"
if [ ! -d "$MEMORY_DIR" ]; then
    echo "❌ Memory MCP directory not found at $MEMORY_DIR"
    echo "Please ensure Memory MCP is installed and has been used at least once."
    exit 1
fi

# Check if memory.json exists
if [ ! -f "$MEMORY_DIR/memory.json" ]; then
    echo "⚠️  No memory.json found. Creating empty file..."
    echo '{}' > "$MEMORY_DIR/memory.json"
fi

# Initialize git repo if not already initialized
cd "$MEMORY_DIR"
if [ ! -d .git ]; then
    echo "📦 Initializing git repository..."
    git init
    git branch -m main
    git add memory.json
    git commit -m "Initial memory backup" || true
fi

# Set up remote to worldarchitect.ai repo
echo "🔗 Setting up remote repository..."
git remote remove origin 2>/dev/null || true
git remote add origin https://github.com/jleechan2015/worldarchitect.ai.git

# Create backup script
echo "📝 Creating backup script..."
cat > "$MEMORY_DIR/backup_memory.sh" << 'EOF'
#!/bin/bash
# Memory MCP Backup Script - Hourly Auto-Push to GitHub
# Append-only commits to memory-backup branch

cd ~/.cache/mcp-memory

# Check if memory.json exists and has changes
if [ ! -f memory.json ]; then
    echo "$(date): No memory.json file found"
    exit 1
fi

# Add and commit if there are changes
git add memory.json
if git diff --cached --quiet; then
    echo "$(date): No changes to commit"
    exit 0
fi

# Create append-only commit with timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
git commit -m "Memory backup: ${TIMESTAMP}"

# Push to GitHub main (create remote if doesn't exist)
if ! git remote get-url origin &>/dev/null; then
    echo "$(date): Setting up GitHub remote..."
    git remote add origin https://github.com/jleechan2015/worldarchitect.ai.git
fi

# Push directly to main branch in worldarchitect.ai repo
git push origin main

echo "$(date): Memory backup completed successfully"
EOF

chmod +x "$MEMORY_DIR/backup_memory.sh"

# Create README
echo "📖 Creating README..."
cat > "$MEMORY_DIR/README.md" << 'EOF'
# Memory MCP Backup Repository

This repository contains automated backups of Memory MCP data.

- **Backup Location**: `main` branch in worldarchitect.ai repo
- **Backup Frequency**: Hourly via cron job
- **Commit Style**: Append-only to main branch
- **Data Format**: JSON snapshots with timestamps
- **Purpose**: Disaster recovery and data continuity

## Setup
Automated via cron job running `backup_memory.sh` every hour.

## Restore
```bash
# Fetch latest backup
git fetch origin main
git checkout origin/main -- .cache/mcp-memory/memory.json
# Copy to MCP directory
cp memory.json ~/.cache/mcp-memory/memory.json
```

## Manual Backup
Run `~/.cache/mcp-memory/backup_memory.sh` to trigger backup manually.
EOF

# Commit backup infrastructure
git add .
git commit -m "Add backup script and README" || true

# Install cron job
echo "⏰ Setting up hourly cron job..."
CRON_CMD="0 * * * * $MEMORY_DIR/backup_memory.sh >> $MEMORY_DIR/backup.log 2>&1"
(crontab -l 2>/dev/null | grep -v "backup_memory.sh"; echo "$CRON_CMD") | crontab -

# Test the backup
echo "🧪 Testing backup script..."
"$MEMORY_DIR/backup_memory.sh"

echo "✅ Memory backup system installed successfully!"
echo ""
echo "📋 Summary:"
echo "  - Backup script: $MEMORY_DIR/backup_memory.sh"
echo "  - Backup branch: main (in worldarchitect.ai repo)"
echo "  - Cron schedule: Every hour at :00"
echo "  - Log file: $MEMORY_DIR/backup.log"
echo ""
echo "🚀 First backup will run within the next hour."
echo "   To backup manually: ~/.cache/mcp-memory/backup_memory.sh"