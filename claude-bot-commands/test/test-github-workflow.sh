#!/bin/bash

# GitHub Actions Workflow Local Testing Script
# Tests the complete /claude slash command flow locally

set -e

echo "🧪 GitHub Actions Workflow Local Testing"
echo "========================================"

# Configuration
CLAUDE_SERVER_PORT=5001
CLAUDE_ENDPOINT="http://127.0.0.1:${CLAUDE_SERVER_PORT}/claude"
MOCK_EVENT_FILE="/tmp/mock_github_event.json"

# Create mock GitHub event payload (matches peter-evans/slash-command-dispatch structure)
create_mock_event() {
    local command_args="$1"
    cat > "$MOCK_EVENT_FILE" << EOF
{
  "client_payload": {
    "slash_command": {
      "command": "claude",
      "args": {
        "all": "$command_args"
      }
    },
    "github": {
      "payload": {
        "comment": {
          "id": "1234567890"
        },
        "repository": {
          "full_name": "jleechanorg/worldarchitect.ai"
        },
        "issue": {
          "number": 994
        }
      }
    }
  }
}
EOF
    echo "📄 Created mock event: $MOCK_EVENT_FILE"
    echo "Command args: '$command_args'"
}

# Start Claude bot server
start_claude_server() {
    echo "🚀 Starting Claude bot server on port $CLAUDE_SERVER_PORT..."
    cd claude-bot-commands/server
    python3 claude-bot-server.py &
    CLAUDE_PID=$!
    cd - > /dev/null

    # Wait for server to start
    sleep 2

    # Test health endpoint
    if curl -s "http://127.0.0.1:${CLAUDE_SERVER_PORT}/health" > /dev/null; then
        echo "✅ Claude server started successfully (PID: $CLAUDE_PID)"
    else
        echo "❌ Failed to start Claude server"
        exit 1
    fi
}

# Stop Claude bot server
stop_claude_server() {
    if [ ! -z "$CLAUDE_PID" ]; then
        echo "🛑 Stopping Claude server (PID: $CLAUDE_PID)..."
        kill $CLAUDE_PID 2>/dev/null || true
        wait $CLAUDE_PID 2>/dev/null || true
    fi
}

# Test jq extraction (GitHub Actions Extract step)
test_extraction() {
    echo ""
    echo "🔍 Testing jq extraction (Extract step)..."

    # Set GITHUB_EVENT_PATH like GitHub Actions does
    export GITHUB_EVENT_PATH="$MOCK_EVENT_FILE"

    # Run the exact commands from the workflow
    P=$(jq -r '.client_payload.slash_command.args.all // empty' "$GITHUB_EVENT_PATH")
    CID=$(jq -r '.client_payload.github.payload.comment.id // empty' "$GITHUB_EVENT_PATH")

    echo "Extracted prompt: '$P'"
    echo "Extracted comment ID: '$CID'"

    # Validate extraction
    if [ -z "$P" ] || [ "$P" = "null" ]; then
        echo "❌ Prompt extraction failed"
        return 1
    fi

    if [ -z "$CID" ] || [ "$CID" = "null" ]; then
        echo "❌ Comment ID extraction failed"
        return 1
    fi

    echo "✅ Extraction successful"

    # Export for next test
    export EXTRACTED_PROMPT="$P"
    export EXTRACTED_CID="$CID"
}

# Test Claude API call (GitHub Actions Call Claude step)
test_claude_call() {
    echo ""
    echo "🤖 Testing Claude API call (Call Claude step)..."

    echo "Calling Claude with prompt: '$EXTRACTED_PROMPT'"

    # Run the exact curl command from the workflow
    A=$(curl -s --data-urlencode "prompt=$EXTRACTED_PROMPT" "$CLAUDE_ENDPOINT")

    echo "Claude response: '$A'"

    # Validate response
    if [ -z "$A" ]; then
        echo "❌ Empty response from Claude"
        return 1
    fi

    if [[ "$A" == *"❌ Error"* ]]; then
        echo "❌ Claude returned an error: $A"
        return 1
    fi

    echo "✅ Claude call successful"

    # Export for next test
    export CLAUDE_RESPONSE="$A"
}

# Test comment formatting (GitHub Actions Comment back step)
test_comment_format() {
    echo ""
    echo "💬 Testing comment formatting (Comment back step)..."

    # Format the response like the workflow does
    FORMATTED_COMMENT="**🤖 Claude Bot Reply**
\`\`\`
$CLAUDE_RESPONSE
\`\`\`"

    echo "Formatted comment:"
    echo "$FORMATTED_COMMENT"
    echo ""
    echo "Comment ID: $EXTRACTED_CID"
    echo "✅ Comment formatting successful"
}

# Run a complete test
run_test() {
    local test_prompt="$1"
    echo ""
    echo "🎯 Testing: /claude $test_prompt"
    echo "----------------------------------------"

    create_mock_event "$test_prompt"
    test_extraction
    test_claude_call
    test_comment_format

    echo "✅ Test completed successfully!"
}

# Cleanup function
cleanup() {
    stop_claude_server
    rm -f "$MOCK_EVENT_FILE"
    echo "🧹 Cleanup completed"
}

# Set up cleanup on exit
trap cleanup EXIT

# Main test execution
main() {
    echo "Starting comprehensive workflow testing..."

    start_claude_server

    # Test various command scenarios
    run_test "hello!"
    run_test "what is 2+2?"
    run_test "help me debug this code"

    echo ""
    echo "🎉 All tests passed! The GitHub slash command workflow should work correctly."
    echo ""
    echo "Next steps:"
    echo "1. Push your workflow changes to GitHub"
    echo "2. Test with a real /claude command in a PR comment"
    echo "3. Check GitHub Actions logs if issues occur"
}

# Handle script arguments
if [ "$1" = "single" ]; then
    # Single test mode for quick debugging
    shift
    start_claude_server
    run_test "${*:-hello!}"
elif [ "$1" = "server-only" ]; then
    # Just start the server for manual testing
    start_claude_server
    echo "Claude server running. Press Ctrl+C to stop."
    read -r
else
    # Full test suite
    main
fi
