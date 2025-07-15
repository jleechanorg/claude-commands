#!/bin/bash
# Simple backup script for Memory MCP
# Creates timestamped backups and manages retention

set -e

# Configuration
MEMORY_FILE="$HOME/.cache/mcp-memory/memory.json"
BACKUP_DIR="$HOME/.cache/mcp-memory/backups"
MAX_BACKUPS=20
COMPRESS=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--file)
            MEMORY_FILE="$2"
            shift 2
            ;;
        -d|--backup-dir)
            BACKUP_DIR="$2"
            shift 2
            ;;
        -n|--max-backups)
            MAX_BACKUPS="$2"
            shift 2
            ;;
        -c|--compress)
            COMPRESS=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  -f, --file PATH         Memory file path (default: ~/.cache/mcp-memory/memory.json)"
            echo "  -d, --backup-dir PATH   Backup directory (default: ~/.cache/mcp-memory/backups)"
            echo "  -n, --max-backups NUM   Maximum backups to keep (default: 20)"
            echo "  -c, --compress          Compress backups"
            echo "  -h, --help              Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Check if memory file exists
if [[ ! -f "$MEMORY_FILE" ]]; then
    echo "Warning: Memory file $MEMORY_FILE does not exist"
    exit 1
fi

# Generate timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="memory_${TIMESTAMP}"

# Create backup
echo "Creating backup: $BACKUP_NAME"

if [[ "$COMPRESS" == "true" ]]; then
    BACKUP_FILE="$BACKUP_DIR/${BACKUP_NAME}.json.gz"
    gzip -c "$MEMORY_FILE" > "$BACKUP_FILE"
else
    BACKUP_FILE="$BACKUP_DIR/${BACKUP_NAME}.json"
    cp "$MEMORY_FILE" "$BACKUP_FILE"
fi

# Verify backup
echo "Verifying backup..."
if [[ "$COMPRESS" == "true" ]]; then
    if ! gzip -t "$BACKUP_FILE"; then
        echo "Error: Backup verification failed"
        rm -f "$BACKUP_FILE"
        exit 1
    fi
else
    if ! python3 -c "import json; json.load(open('$BACKUP_FILE'))" 2>/dev/null; then
        echo "Error: Backup is not valid JSON"
        rm -f "$BACKUP_FILE"
        exit 1
    fi
fi

# Calculate sizes
ORIGINAL_SIZE=$(stat -c%s "$MEMORY_FILE")
BACKUP_SIZE=$(stat -c%s "$BACKUP_FILE")

echo "Backup created successfully:"
echo "  Original size: $(numfmt --to=iec $ORIGINAL_SIZE)"
echo "  Backup size: $(numfmt --to=iec $BACKUP_SIZE)"

if [[ "$COMPRESS" == "true" ]]; then
    COMPRESSION_RATIO=$(echo "scale=1; $BACKUP_SIZE * 100 / $ORIGINAL_SIZE" | bc -l)
    echo "  Compression ratio: ${COMPRESSION_RATIO}%"
fi

# Cleanup old backups
echo "Cleaning up old backups (keeping $MAX_BACKUPS most recent)..."

# Find and sort backup files by timestamp
BACKUP_FILES=($(ls -1 "$BACKUP_DIR"/memory_*.json* 2>/dev/null | sort -r))
BACKUP_COUNT=${#BACKUP_FILES[@]}

if [[ $BACKUP_COUNT -gt $MAX_BACKUPS ]]; then
    FILES_TO_DELETE=($(printf '%s\n' "${BACKUP_FILES[@]:$MAX_BACKUPS}"))
    
    for file in "${FILES_TO_DELETE[@]}"; do
        echo "  Removing old backup: $(basename "$file")"
        rm -f "$file"
    done
    
    DELETED_COUNT=$((BACKUP_COUNT - MAX_BACKUPS))
    echo "  Deleted $DELETED_COUNT old backup(s)"
else
    echo "  No cleanup needed (${BACKUP_COUNT}/${MAX_BACKUPS} backups)"
fi

# Show backup statistics
echo ""
echo "Backup statistics:"
echo "  Total backups: $((BACKUP_COUNT > MAX_BACKUPS ? MAX_BACKUPS : BACKUP_COUNT))"
echo "  Backup directory: $BACKUP_DIR"

# Calculate total backup size
TOTAL_SIZE=0
for file in "${BACKUP_FILES[@]:0:$MAX_BACKUPS}"; do
    if [[ -f "$file" ]]; then
        SIZE=$(stat -c%s "$file")
        TOTAL_SIZE=$((TOTAL_SIZE + SIZE))
    fi
done

echo "  Total backup size: $(numfmt --to=iec $TOTAL_SIZE)"

# Show recent backups
echo ""
echo "Recent backups:"
for file in "${BACKUP_FILES[@]:0:5}"; do
    if [[ -f "$file" ]]; then
        SIZE=$(stat -c%s "$file")
        MTIME=$(stat -c%Y "$file")
        DATE=$(date -d @$MTIME "+%Y-%m-%d %H:%M:%S")
        echo "  $(basename "$file") - $DATE ($(numfmt --to=iec $SIZE))"
    fi
done

echo ""
echo "Backup completed successfully!"