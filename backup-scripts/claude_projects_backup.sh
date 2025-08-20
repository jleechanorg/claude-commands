#!/bin/bash
# Claude projects backup script with configurable destination
# Usage: ./claude_projects_backup.sh [destination_dir]

# Default destination if none provided
DEFAULT_DEST="$HOME/backups/claude-projects"
DEST_DIR="${1:-$DEFAULT_DEST}"

# Source directory
SOURCE_DIR="$HOME/.claude/projects"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Timestamp for backup
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="claude_projects_backup_$TIMESTAMP"

echo -e "${BLUE}🔄 Starting Claude projects backup...${NC}"
echo -e "${BLUE}📁 Source: $SOURCE_DIR${NC}"
echo -e "${BLUE}📁 Destination: $DEST_DIR${NC}"

# Check if source directory exists
if [ ! -d "$SOURCE_DIR" ]; then
    echo -e "${RED}❌ Source directory not found: $SOURCE_DIR${NC}"
    exit 1
fi

# Create destination directory if it doesn't exist
if [ ! -d "$DEST_DIR" ]; then
    echo -e "${YELLOW}⚠️  Creating destination directory: $DEST_DIR${NC}"
    mkdir -p "$DEST_DIR"
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Failed to create destination directory${NC}"
        exit 1
    fi
fi

# Create timestamped backup
echo -e "${BLUE}📦 Creating backup: $BACKUP_NAME${NC}"

# Use rsync for efficient backup with progress
rsync -av --progress "$SOURCE_DIR/" "$DEST_DIR/$BACKUP_NAME/"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Backup completed successfully${NC}"
    echo -e "${GREEN}📁 Backup location: $DEST_DIR/$BACKUP_NAME${NC}"
    
    # Show backup size
    BACKUP_SIZE=$(du -h "$DEST_DIR/$BACKUP_NAME" | tail -1 | cut -f1)
    echo -e "${BLUE}📊 Backup size: $BACKUP_SIZE${NC}"
    
    # Create a "latest" symlink for convenience
    cd "$DEST_DIR"
    rm -f latest
    ln -s "$BACKUP_NAME" latest
    echo -e "${BLUE}🔗 Created 'latest' symlink${NC}"
    
    # Cleanup old backups (keep last 20)
    echo -e "${BLUE}🧹 Cleaning up old backups (keeping last 20)...${NC}"
    ls -1t claude_projects_backup_* 2>/dev/null | tail -n +21 | while read old_backup; do
        if [ -d "$old_backup" ]; then
            echo -e "${YELLOW}🗑️  Removing old backup: $old_backup${NC}"
            rm -rf "$old_backup"
        fi
    done
    
else
    echo -e "${RED}❌ Backup failed${NC}"
    exit 1
fi

echo -e "${GREEN}🎉 Backup process completed${NC}"