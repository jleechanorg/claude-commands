# Claude Bot Commands

## ⚠️ CRITICAL WARNING: NO HARDCODED COMMAND PARSING ⚠️

**THIS IS A HARD RULE - NEVER VIOLATE**

### ❌ FORBIDDEN PATTERNS:

```python
# ❌ NEVER DO THIS:
if prompt.lower() in ['hello', 'hi']:
    return "Hello!"
elif 'help' in prompt.lower():
    return "I can help!"
elif '2+2' in prompt:
    return "4"
```

### ❌ FORBIDDEN APPROACHES:
- Pattern matching prompts (`if/elif` chains)
- Hardcoded response dictionaries
- Keyword detection for responses
- Any form of "fake" command parsing that mimics Claude responses

### ✅ ONLY ACCEPTABLE APPROACHES:
1. **Real Claude CLI integration** (when it works)
2. **Error responses** explaining CLI limitations
3. **Generic acknowledgments** without content-specific responses

### 🚨 WHY THIS RULE EXISTS:
- **Fake implementations are misleading** - they pretend to be Claude but aren't
- **Maintenance nightmare** - every new prompt type requires manual coding
- **Quality degradation** - hardcoded responses are inferior to real Claude
- **User confusion** - inconsistent behavior compared to real Claude CLI

### 📋 CURRENT STATUS:
The Claude CLI has EBADF (bad file descriptor) errors and doesn't work reliably in automated environments. Until this is resolved:

- **Return error messages** explaining the CLI limitation
- **Do NOT create fake responses** to work around the problem
- **Direct users to local Claude CLI** for real assistance

### 🛠️ FUTURE SOLUTIONS:
- Fix Claude CLI EBADF issues
- Implement proper Claude API integration
- Use external services that actually provide Claude responses

## Files in this directory:

- `server/claude-bot-server.py` - HTTP server for GitHub Actions integration
- `tests/` - Test files for the server functionality
- `test/` - Bash test scripts

## Usage:

```bash
# Start the server
cd server/
python3 claude-bot-server.py

# Test the endpoint
curl -X POST -d "prompt=your prompt here" http://127.0.0.1:5001/claude
```

## Remember:

**If you find yourself writing `if prompt.lower()...` STOP IMMEDIATELY!**

This is exactly the pattern that is forbidden. Instead, focus on fixing the underlying Claude CLI integration or providing honest error responses about the limitation.
