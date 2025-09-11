#!/bin/bash
# MCP Slash Command Executor Hook - Shell Version
# Detects SLASH_COMMAND_EXECUTE: pattern and executes the commands automatically

# Read input from stdin
raw_input=$(cat)

# Debug logging (gated behind environment flag for security)
if [[ -n "${MCP_EXECUTOR_DEBUG:-}" ]]; then
  log_file="${MCP_EXECUTOR_LOG_FILE:-/tmp/mcp-executor-debug.log}"
  timestamp=$(date '+%Y-%m-%d %H:%M:%S')
  printf '[%s] HOOK TRIGGERED - Input length: %d\n' "$timestamp" "${#raw_input}" >> "$log_file"
fi

# Try to parse PostToolUse JSON first, fall back to plain text
input=$(printf '%s' "$raw_input" | python3 -c '
import sys, json
try:
    # Read input once to avoid seek issues with non-seekable stdin
    raw_content = sys.stdin.read()
    
    # First check if input contains SLASH_COMMAND_EXECUTE directly
    if "SLASH_COMMAND_EXECUTE:" in raw_content:
        print(raw_content)
    else:
        data = json.loads(raw_content)
        
        # Direct string response (most common from MCP tools)
        if isinstance(data, str) and "SLASH_COMMAND_EXECUTE:" in data:
            print(data)
        # PostToolUse hook structure: extract tool_response content
        elif isinstance(data, dict) and "tool_response" in data:
            response = data["tool_response"]
            if isinstance(response, str):
                print(response)
            elif isinstance(response, dict) and "content" in response:
                print(response["content"])
            elif isinstance(response, dict):
                # Try common response field names
                for field in ["result", "output", "data", "text"]:
                    if field in response:
                        print(str(response[field]))
                        break
                else:
                    print(str(response))
            else:
                print(str(response))
        # Handle MCP tool response arrays with text content
        elif isinstance(data, list) and len(data) > 0:
            for item in data:
                if isinstance(item, dict) and "text" in item:
                    text = item["text"]
                    if "SLASH_COMMAND_EXECUTE:" in str(text):
                        print(text)
                        break
            else:
                # Fallback to first item with text
                if isinstance(data[0], dict) and "text" in data[0]:
                    print(data[0]["text"])
                else:
                    print(str(data[0]))
        # Handle dict with stdout field (from Bash tool responses)
        elif isinstance(data, dict) and "stdout" in data:
            stdout_content = data["stdout"]
            if "SLASH_COMMAND_EXECUTE:" in str(stdout_content):
                print(stdout_content)
            else:
                print(str(data))
        # Fallback: legacy parsing for direct content
        elif isinstance(data, dict) and "content" in data:
            print(data["content"])
        else:
            print(str(data))
except Exception as e:
    # If JSON parsing failed, use raw content for SLASH_COMMAND_EXECUTE pattern
    if "SLASH_COMMAND_EXECUTE:" in raw_content:
        print(raw_content)
    else:
        # Not our pattern, pass through
        print(raw_content)
' 2>/dev/null || echo "$raw_input")

# Debug: Log extracted input (only if debug enabled)
if [[ -n "${MCP_EXECUTOR_DEBUG:-}" ]]; then
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    log_file="${MCP_EXECUTOR_LOG_FILE:-/tmp/mcp-executor-debug.log}"
    printf '[%s] EXTRACTED: %s\n' "$timestamp" "$input" >> "$log_file"
fi

# Check for SLASH_COMMAND_EXECUTE pattern (handles both direct pattern and text field content)
if [[ "$input" == SLASH_COMMAND_EXECUTE:* ]] || [[ "$input" == *"SLASH_COMMAND_EXECUTE:"* ]]; then
    # Extract the command after the pattern
    if [[ "$input" == SLASH_COMMAND_EXECUTE:* ]]; then
        # Direct pattern format
        command="${input#SLASH_COMMAND_EXECUTE:}"
    else
        # Array format with text field - extract just the command part
        command=$(echo "$input" | grep -o 'SLASH_COMMAND_EXECUTE:[^"}'"'"']*' | sed 's/SLASH_COMMAND_EXECUTE://' | sed "s/'.*$//")
    fi
    command=$(echo "$command" | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')
    
    # Debug logging
    if [[ -n "${MCP_EXECUTOR_DEBUG:-}" ]]; then
        timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        log_file="${MCP_EXECUTOR_LOG_FILE:-/tmp/mcp-executor-debug.log}"
        printf '[%s] EXECUTING: %s\n' "$timestamp" "$command" >> "$log_file"
    fi
    
    # Find project root
    REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
    if [[ -z "$REPO_ROOT" ]]; then
        echo "Error: Could not find project root with git repository"
        exit 0
    fi
    
    # Change to project root for command execution
    cd "$REPO_ROOT" || {
        echo "Error: Could not change to project root: $REPO_ROOT"
        exit 0
    }
    
    # Execute the slash command by simulating user input to Claude Code CLI
    # We'll use the same approach as compose-commands.sh but for direct execution
    
    # Extract command name (first word after /)
    cmd_name=$(echo "$command" | sed 's|^/||' | cut -d' ' -f1)
    cmd_args=$(echo "$command" | cut -d' ' -f2-)
    
    # Check if command file exists
    cmd_file="$REPO_ROOT/.claude/commands/${cmd_name}.md"
    if [[ ! -f "$cmd_file" ]]; then
        echo "Error: Command file not found: $cmd_file"
        exit 0
    fi
    
    # Read the command file and execute based on its patterns
    # Look for !`command` patterns and execute them
    temp_script=$(mktemp)
    trap "rm -f '$temp_script'" EXIT
    
    # Extract executable commands from the markdown file
    grep -E '^\s*!\s*`[^`]+`\s*$' "$cmd_file" | sed 's/^\s*!\s*`\(.*\)`\s*$/\1/' > "$temp_script"
    
    if [[ -s "$temp_script" ]]; then
        # Execute the commands in sequence
        echo "🚀 Executing slash command: $command"
        echo ""
        
        # Set up environment variables that commands might need
        export ARGUMENTS="$cmd_args"
        declare -a CMD_ARG=()
        if [[ -n "$cmd_args" ]]; then
            # Parse arguments into array
            while IFS= read -r -d '' arg; do
                CMD_ARG+=("$arg")
            done < <(printf '%s\0' "$cmd_args")
        fi
        export CTX_ARG=("${CMD_ARG[@]}")
        
        # Execute each command
        while IFS= read -r cmd_line; do
            if [[ -n "$cmd_line" ]]; then
                echo "📋 Running: $cmd_line"
                # Execute the command and capture output
                if eval "$cmd_line"; then
                    echo "✅ Command completed successfully"
                else
                    echo "❌ Command failed with exit code $?"
                fi
                echo ""
            fi
        done < "$temp_script"
        
        echo "🎯 Slash command execution completed: $command"
    else
        # No executable commands found - this is an instruction-based command
        # For these commands, Claude should execute them directly by reading the instructions
        echo "🎯 Executing instruction-based command: $command"
        echo ""
        
        # For /fake3 specifically, execute the workflow directly
        if [[ "$cmd_name" == "fake3" ]]; then
            echo "🚀 Starting /fake3 - Automated Fake Code Detection and Fixing"
            echo "📍 Branch: $(git branch --show-current)"
            echo ""
            
            # Execute /fake command through the current Claude session
            # by reading the fake command file and implementing its workflow
            fake_cmd_file="$REPO_ROOT/.claude/commands/fake.md"
            if [[ -f "$fake_cmd_file" ]]; then
                echo "🔍 Running fake code detection..."
                
                # Check for executable patterns in fake.md
                fake_temp_script=$(mktemp)
                trap "rm -f '$fake_temp_script'" EXIT
                
                grep -E '^\s*!\s*`[^`]+`\s*$' "$fake_cmd_file" | sed 's/^\s*!\s*`\(.*\)`\s*$/\1/' > "$fake_temp_script"
                
                if [[ -s "$fake_temp_script" ]]; then
                    echo "📋 Executing /fake detection patterns..."
                    while IFS= read -r fake_cmd_line; do
                        if [[ -n "$fake_cmd_line" ]]; then
                            echo "🔍 Running: $fake_cmd_line"
                            if eval "$fake_cmd_line"; then
                                echo "✅ Detection completed"
                            else
                                echo "❌ Detection failed"
                            fi
                        fi
                    done < "$fake_temp_script"
                else
                    echo "💡 /fake is instruction-based - would need Claude to analyze code"
                fi
                
                rm -f "$fake_temp_script"
            else
                echo "❌ /fake command file not found: $fake_cmd_file"
            fi
            
            echo ""
            echo "✅ /fake3 iteration 1 completed"
            echo "🎯 Full /fake3 workflow would require Claude orchestration"
        else
            echo "📄 Instruction-based command: $command"
            echo "💡 Requires Claude to implement workflow from: $cmd_file"
        fi
    fi
    
    # Debug logging
    if [[ -n "${MCP_EXECUTOR_DEBUG:-}" ]]; then
        timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        log_file="${MCP_EXECUTOR_LOG_FILE:-/tmp/mcp-executor-debug.log}"
        printf '[%s] COMPLETED: %s\n' "$timestamp" "$command" >> "$log_file"
    fi
    
else
    # No pattern detected, pass through unchanged
    echo "$input"
fi