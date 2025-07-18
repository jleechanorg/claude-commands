#!/bin/bash
# Setup Memory MCP Backup Schedule
# This script configures automatic daily PR creation and hourly updates

echo "🔧 Setting up Memory MCP backup schedule..."

# Get the absolute path to the memory directory
MEMORY_DIR="$(cd "$(dirname "$0")" && pwd)"

# Check if backup scripts exist
if [ ! -f "$MEMORY_DIR/backup_memory_pr.sh" ]; then
    echo "❌ Error: backup_memory_pr.sh not found in $MEMORY_DIR"
    exit 1
fi

if [ ! -f "$MEMORY_DIR/backup_memory_hourly.sh" ]; then
    echo "❌ Error: backup_memory_hourly.sh not found in $MEMORY_DIR"
    exit 1
fi

# Make scripts executable
chmod +x "$MEMORY_DIR/backup_memory_pr.sh"
chmod +x "$MEMORY_DIR/backup_memory_hourly.sh"

# Setup cron jobs
echo "📅 Configuring cron jobs..."

# Daily PR creation at 2 AM
DAILY_CRON="0 2 * * * cd $MEMORY_DIR && ./backup_memory_pr.sh >> $MEMORY_DIR/backup_daily.log 2>&1"

# Hourly updates (every hour except 2 AM)
HOURLY_CRON="0 0,1,3-23 * * * cd $MEMORY_DIR && ./backup_memory_hourly.sh >> $MEMORY_DIR/backup_hourly.log 2>&1"

# Check and install cron jobs independently
if ! crontab -l 2>/dev/null | grep -q "backup_memory_pr.sh"; then
    (crontab -l 2>/dev/null; echo "$DAILY_CRON") | crontab -
    echo "✅ Daily backup cron installed"
else
    echo "ℹ️  Daily backup cron job already exists"
fi

if ! crontab -l 2>/dev/null | grep -q "backup_memory_hourly.sh"; then
    (crontab -l 2>/dev/null; echo "$HOURLY_CRON") | crontab -
    echo "✅ Hourly backup cron installed"
else
    echo "ℹ️  Hourly backup cron job already exists"
fi

# Display current cron configuration
echo ""
echo "📋 Current Memory MCP backup schedule:"
crontab -l | grep backup_memory

echo ""
echo "✅ Memory MCP backup system configured!"
echo ""
echo "📍 Daily PR creation: 2:00 AM"
echo "📍 Hourly updates: Every hour (except 2 AM)"
echo "📍 Logs: $MEMORY_DIR/backup_daily.log and backup_hourly.log"
echo ""
echo "💡 To manually run a backup:"
echo "   Daily PR: cd $MEMORY_DIR && ./backup_memory_pr.sh"
echo "   Hourly update: cd $MEMORY_DIR && ./backup_memory_hourly.sh"
echo ""
echo "💡 To check backup status:"
echo "   Current PR: gh pr list --head memory-backup-\$(date +%Y-%m-%d)"
echo "   View logs: tail -f $MEMORY_DIR/backup_*.log"