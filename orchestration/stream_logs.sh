#!/bin/bash
# Stream tmux logs with readable formatting

main() {
    detect_log_root() {
        if [ -n "$ORCHESTRATION_LOG_DIR" ] && [ -d "$ORCHESTRATION_LOG_DIR" ]; then
            echo "$ORCHESTRATION_LOG_DIR"
            return
        fi
        for candidate in \
            "/private/tmp/worldarchitect.ai/sdui-spec-run/pairv2/run_001/orchestration_logs" \
            "/tmp/worldarchitect.ai/sdui-spec-run/pairv2/run_001/orchestration_logs" \
            "/tmp/orchestration_logs"; do
            if [ -d "$candidate" ]; then
                echo "$candidate"
                return
            fi
        done
        echo "/tmp/orchestration_logs"
    }

    LOG_ROOT="$(detect_log_root)"

    if [ "$1" = "--latest" ]; then
        LATEST_LOG="$(ls -t "$LOG_ROOT"/coder-*.log "$LOG_ROOT"/verifier-*.log 2>/dev/null | grep -E '/(coder|verifier)-.*\.log$' | head -n1)"
        if [ -z "$LATEST_LOG" ]; then
            echo "No coder/verifier logs found under: $LOG_ROOT"
            return 1
        fi
        LATEST_SESSION="$(basename "$LATEST_LOG" .log)"
        echo "Using latest session: $LATEST_SESSION"
        exec "$0" "$LATEST_SESSION"
    fi

    if [ -z "$1" ]; then
        echo "Usage: $0 <session_name>"
        echo "   or: $0 --latest"
        echo ""
        echo "Log root: $LOG_ROOT"
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
        local has_jq=0
        if command -v jq >/dev/null 2>&1; then
            has_jq=1
        fi

        # Structured JSON parsing path (preferred when jq is available).
        if [ "$has_jq" -eq 1 ] && echo "$content" | jq -e . >/dev/null 2>&1; then
            local event_type sub_type text tool_name tool_cmd tool_desc
            event_type="$(echo "$content" | jq -r '.type // empty')"
            sub_type="$(echo "$content" | jq -r '.subtype // empty')"

            if [ "$event_type" = "system" ] && [ -n "$sub_type" ]; then
                local cwd model
                cwd="$(echo "$content" | jq -r '.cwd // empty')"
                model="$(echo "$content" | jq -r '.model // empty')"
                echo -e "\n⚙️  \033[1;35mSystem:\033[0m ${sub_type}"
                [ -n "$model" ] && echo "   model: $model"
                [ -n "$cwd" ] && echo "   cwd:   $cwd"
                echo ""
                return
            fi

            text="$(echo "$content" | jq -r '.message.content[]? | select(.type=="text") | .text' 2>/dev/null)"
            if [ -n "$text" ]; then
                if [ ${#text} -gt 1200 ]; then
                    text="${text:0:1200}
...[truncated]"
                fi
                echo -e "\n🤖 \033[1;34mAssistant:\033[0m"
                echo "$text"
                echo ""
                return
            fi

            tool_name="$(echo "$content" | jq -r '.message.content[]? | select(.type=="tool_use") | .name' 2>/dev/null | head -1)"
            if [ -n "$tool_name" ] && [ "$tool_name" != "null" ]; then
                tool_cmd="$(echo "$content" | jq -r '.message.content[]? | select(.type=="tool_use") | .input.command // empty' 2>/dev/null | head -1)"
                tool_desc="$(echo "$content" | jq -r '.message.content[]? | select(.type=="tool_use") | .input.description // empty' 2>/dev/null | head -1)"
                echo -e "🔧 \033[1;33mTool:\033[0m $tool_name"
                [ -n "$tool_desc" ] && echo "   desc: $tool_desc"
                if [ -n "$tool_cmd" ]; then
                    if [ ${#tool_cmd} -gt 200 ]; then
                        printf "   cmd: %.197s...\n" "$tool_cmd"
                    else
                        echo "   cmd: $tool_cmd"
                    fi
                fi
                echo ""
                return
            fi

            if [ "$event_type" = "user" ]; then
                local tool_result_type
                tool_result_type="$(echo "$content" | jq -r '.message.content[]? | select(.type=="tool_result") | .type' 2>/dev/null | head -1)"
                if [ -n "$tool_result_type" ]; then
                    echo -e "🧾 \033[1;32mTool result received\033[0m"
                    return
                fi
            fi

            # If JSON but no known event shape, ignore to avoid noisy dumps.
            return
        fi

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
    LOG_FILE="${LOG_ROOT}/${SANITIZED_SESSION}.log"

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
