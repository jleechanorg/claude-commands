#!/bin/bash
# Shell wrapper for CRDT-based memory backup system
# Provides backwards compatibility with existing scripts

# Default values
MEMORY_FILE="${MEMORY_FILE:-memory.json}"
GIT_REPO="${GIT_REPO:-.}"
HOSTNAME="${HOSTNAME:-$(hostname)}"

# Parse arguments
ACTION=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --backup)
            ACTION="backup"
            shift
            ;;
        --merge)
            ACTION="merge"
            shift
            ;;
        --file)
            MEMORY_FILE="$2"
            shift 2
            ;;
        --repo)
            GIT_REPO="$2"
            shift 2
            ;;
        --host)
            HOSTNAME="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--backup|--merge] [--file <memory.json>] [--repo <path>] [--host <hostname>]"
            exit 1
            ;;
    esac
done

# Default to backup if no action specified
if [ -z "$ACTION" ]; then
    ACTION="backup"
fi

# Call Python implementation
if [ "$ACTION" = "backup" ]; then
    python3 "$(dirname "$0")/memory_backup_crdt.py" \
        --backup \
        --file "$MEMORY_FILE" \
        --repo "$GIT_REPO" \
        --host "$HOSTNAME"
elif [ "$ACTION" = "merge" ]; then
    python3 "$(dirname "$0")/memory_backup_crdt.py" \
        --merge \
        --repo "$GIT_REPO"
else
    echo "Invalid action: $ACTION"
    exit 1
fi