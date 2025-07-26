# GitHub Actions Workflow Local Testing

This directory contains tools for testing the `/claude` slash command workflow locally before pushing to GitHub.

## Quick Start

```bash
# Run complete test suite
./test-github-workflow.sh

# Test a specific command
./test-github-workflow.sh single "hello world!"

# Start server only for manual testing
./test-github-workflow.sh server-only
```

## What It Tests

The testing script validates the complete GitHub Actions workflow:

1. **Extract Step**: Tests jq extraction of prompt and comment ID from GitHub event payload
2. **Call Claude Step**: Tests curl command to local Claude bot server
3. **Comment Back Step**: Tests response formatting for GitHub comment

## Mock Event Structure

Uses the exact payload structure from `peter-evans/slash-command-dispatch`:

```json
{
  "client_payload": {
    "slash_command": {
      "command": "claude",
      "args": {
        "all": "your command here"
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
```

## Test Scenarios

The script automatically tests:
- ✅ Basic commands: `/claude hello!`
- ✅ Questions: `/claude what is 2+2?`
- ✅ Complex requests: `/claude help me debug this code`
- ✅ Error handling: Empty prompts, server failures
- ✅ Response formatting: GitHub comment structure

## Workflow Validation

This ensures your GitHub Actions workflow will work correctly by testing:

1. **jq Paths**: Correct extraction from `client_payload.slash_command.args.all`
2. **curl Syntax**: Proper `--data-urlencode` formatting
3. **Claude Server**: End-to-end integration with local Claude Code CLI
4. **Error Handling**: Null prompt validation and proper error responses

## Usage in Development

1. **Before Committing**: Run tests to validate workflow changes
2. **Debugging Issues**: Use single test mode to isolate problems
3. **Manual Testing**: Start server-only mode for interactive testing

## Benefits

- 🚀 **Fast Feedback**: No waiting for GitHub Actions
- 🔍 **Complete Coverage**: Tests entire workflow end-to-end
- 🛠️ **Easy Debugging**: Clear output shows exactly what fails
- 📋 **Realistic Testing**: Uses actual GitHub event payload structure
