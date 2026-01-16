#!/usr/bin/env bash
# Stream tmux logs with readable formatting

main() {
    if [ -z "$1" ]; then
        echo "Usage: $0 <session_name>"
        echo ""
        echo "Available sessions:"
        tmux list-sessions 2>/dev/null || echo "No tmux sessions found"
        return 1
    fi

    SESSION_NAME="$1"

    # Security: Validate SESSION_NAME to prevent path traversal
    # Only allow alphanumeric, dots, underscores, and hyphens
    if [[ ! "$SESSION_NAME" =~ ^[A-Za-z0-9._-]+$ ]] || [[ "$SESSION_NAME" == *".."* ]]; then
        echo "Error: Invalid session name. Only alphanumeric characters, dots, underscores, and hyphens are allowed."
        return 1
    fi

    echo "Streaming tmux session: $SESSION_NAME"
    echo "Press Ctrl+C to stop"
    echo "=========================================="
    echo "System time: $(date)"
    echo ""

    # Try to find the actual session name (tmux converts dots to underscores)
    # Try variations: exact match, with trailing underscore, with trailing dot
    ACTUAL_SESSION=""
    for candidate in "$SESSION_NAME" "${SESSION_NAME}_" "${SESSION_NAME}."; do
        if tmux has-session -t "$candidate" 2>/dev/null; then
            ACTUAL_SESSION="$candidate"
            break
        fi
    done

    # If still not found, try without trailing dot/underscore
    if [ -z "$ACTUAL_SESSION" ]; then
        BASE_NAME="${SESSION_NAME%.}"
        BASE_NAME="${BASE_NAME%_}"
        for candidate in "$BASE_NAME" "${BASE_NAME}_" "${BASE_NAME}."; do
            if tmux has-session -t "$candidate" 2>/dev/null; then
                ACTUAL_SESSION="$candidate"
                break
            fi
        done
    fi

    if [ -z "$ACTUAL_SESSION" ]; then
        echo "Error: tmux session '$SESSION_NAME' not found"
        echo ""
        echo "Available sessions:"
        tmux list-sessions 2>/dev/null || echo "No tmux sessions found"
        return 1
    fi

    # Use the actual session name found
    SESSION_NAME="$ACTUAL_SESSION"
    if [ "$ACTUAL_SESSION" != "$1" ]; then
        echo "ℹ️  Using session: $ACTUAL_SESSION (resolved from: $1)"
        echo ""
    fi

    # Function to extract and format meaningful content
    format_output() {
        local content="$1"

        # Try to extract Claude's text messages
        if echo "$content" | grep -q '"type":"text"'; then
            TEXT=$(echo "$content" | grep -o '"text":"[^"]*"' | sed 's/"text":"//' | sed 's/"$//')
            TEXT=$(printf '%b' "$TEXT")
            if [ -n "$TEXT" ]; then
                echo -e "\n🤖 \033[1;34mClaude:\033[0m"
                echo "$TEXT"
                echo ""
            fi
        fi

        # Try to extract tool commands
        if echo "$content" | grep -q '"name":"Bash"'; then
            CMD=$(echo "$content" | grep -o '"command":"[^"]*"' | sed 's/"command":"//' | sed 's/"$//' | head -1)
            DESC=$(echo "$content" | grep -o '"description":"[^"]*"' | sed 's/"description":"//' | sed 's/"$//' | head -1)
            if [ -n "$CMD" ]; then
                echo -e "🔧 \033[1;33mBash:\033[0m $DESC"
                if [ ${#CMD} -gt 200 ]; then
                    printf "   $ %.197s...\n" "$CMD"
                else
                    echo "   $ $CMD"
                fi
                echo ""
            fi
        fi

        # Try to extract todo updates
        if echo "$content" | grep -q '"content":"[^"]*","status":"'; then
            echo -e "\n📝 \033[1;36mTodos:\033[0m"
            echo "$content" | grep -o '{"content":"[^"]*","status":"[^"]*"' | while read -r todo; do
                # shellcheck disable=SC2001
                TASK=$(echo "$todo" | sed 's/.*"content":"\([^"]*\)".*/\1/')
                # shellcheck disable=SC2001
                STATUS=$(echo "$todo" | sed 's/.*"status":"\([^"]*\)".*/\1/')
                case "$STATUS" in
                    "completed") echo "  ✅ $TASK" ;;
                    "in_progress") echo "  🔄 $TASK" ;;
                    "pending") echo "  ⏳ $TASK" ;;
                    *) echo "  • $TASK ($STATUS)" ;;
                esac
            done
            echo ""
        fi
    }

    # Get log file path - sanitize SESSION_NAME to prevent path traversal
    # Remove any path traversal characters (/, ..) from session name
    # First remove .. sequences, then remove slashes, then sanitize other special chars
    SANITIZED_SESSION=$(echo "$SESSION_NAME" | sed 's/\.\.//g' | sed 's/\///g' | sed 's/[^a-zA-Z0-9_-]/-/g')
    if [ -z "$SANITIZED_SESSION" ]; then
        SANITIZED_SESSION="unknown-session"
    fi
    LOG_FILE="/tmp/orchestration_logs/${SANITIZED_SESSION}.log"

    if [ -f "$LOG_FILE" ]; then
        echo "Tailing log file: $LOG_FILE"
        echo ""

        # Show last 50 lines formatted
        tail -50 "$LOG_FILE" | while IFS= read -r line; do
            format_output "$line"
        done

        # Follow new output
        tail -n 0 -f "$LOG_FILE" | while IFS= read -r line; do
            format_output "$line"
        done
    else
        echo "Log file not found: $LOG_FILE"
        echo "Attempting to capture directly from tmux..."
        echo ""

        # Fallback: capture from tmux
        while tmux has-session -t "$SESSION_NAME" 2>/dev/null; do
            CONTENT=$(tmux capture-pane -t "$SESSION_NAME" -p -S -100 2>/dev/null)
            clear
            echo "Last update: $(date)"
            echo "=========================================="
            echo ""

            # Show last few meaningful lines
            echo "$CONTENT" | tail -20 | grep -v '^{"type"' | grep -v '^$' || echo "(Processing...)"

            sleep 3
        done
        echo "Session '$SESSION_NAME' ended. Exiting."
    fi
}

main "$@"
