#!/bin/bash
# Monitor status of all running agents

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

while true; do
    clear
    echo "=========================================="
    echo "Agent Status Monitor - $(date)"
    echo "=========================================="
    echo

    # Check running tmux sessions
    echo "Running Agent Sessions:"
    tmux list-sessions 2>/dev/null | grep -E "(agent|opus)" | while IFS=: read -r session rest; do
        pane_lines=$(tmux capture-pane -t "$session" -p -S -10 2>/dev/null | tail -5)
        echo "📍 $session:"
        echo "$pane_lines" | sed 's/^/   /'
        echo
    done

    # Check shared status file
    if [ -f "$SCRIPT_DIR/tasks/shared_status.txt" ]; then
        echo "----------------------------------------"
        echo "Shared Status:"
        cat "$SCRIPT_DIR/tasks/shared_status.txt"
        echo
    fi

    # Check task files
    echo "----------------------------------------"
    echo "Task Files:"
    for task_file in "$SCRIPT_DIR/tasks/"*_tasks.txt; do
        if [ -f "$task_file" ]; then
            filename=$(basename "$task_file")
            count=$(wc -l < "$task_file" 2>/dev/null || echo "0")
            echo "   $filename: $count pending tasks"
        fi
    done

    echo
    echo "Press Ctrl+C to exit..."
    sleep 10
done
