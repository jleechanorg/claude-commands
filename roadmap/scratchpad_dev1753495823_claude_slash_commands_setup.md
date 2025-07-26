# GitHub Claude Slash Commands Setup - Your Action Items

Branch: `dev1753495823`  
Goal: Set up self-hosted GitHub runner and test the `/claude` slash command system

## 🎯 What This Does

This system lets you type `/claude <prompt>` in any GitHub PR comment, and it will:
1. Capture the command via GitHub Actions
2. Send the prompt to your local Claude Code CLI
3. Post Claude's response back as a comment on the PR

**Zero API costs, complete privacy, runs on your infrastructure.**

## 📋 Your Setup Checklist

### Phase 1: Local Testing (Do This First)

#### 1.1 Test the Local Endpoint
```bash
# Start the Claude endpoint server
./start-claude-slash-commands.sh
# Keep this running in one terminal

# In another terminal, test it
python3 test-claude-endpoint.py
```

**Expected result:** Server starts on port 5001, health check passes, test requests work.

#### 1.2 Manual Test (Optional but Recommended)
```bash
# Test with curl while server is running
curl -X POST -d "prompt=Hello Claude, please respond with 'Manual test successful'" http://127.0.0.1:5001/claude
```

### Phase 2: GitHub Configuration

#### 2.1 Create GitHub Personal Access Token
1. Go to: https://github.com/settings/tokens/new
2. Name: "Claude Slash Command Bot"
3. Select scope: **`repo`** (Full control of private repositories)
4. Generate token and **copy it immediately** (you can't see it again)

#### 2.2 Add GitHub Repository Secrets
Go to: https://github.com/jleechan2015/worldarchitect.ai/settings/secrets/actions

Add these secrets:
| Secret Name | Value |
|-------------|-------|
| `REPO_ACCESS_TOKEN` | Your GitHub PAT from step 2.1 |
| `CLAUDE_ENDPOINT` | `http://127.0.0.1:5001/claude` |

### Phase 3: Self-Hosted Runner Setup

#### 3.1 Download and Configure Runner

**On your local machine (the one running Claude Code):**

```bash
# Create runner directory
mkdir ~/actions-runner && cd ~/actions-runner

# Download runner (Linux x64 - adjust for your OS)
curl -o actions-runner-linux-x64-2.311.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz

# Extract
tar xzf ./actions-runner-linux-x64-2.311.0.tar.gz

# Configure runner - YOU NEED TO GET THE TOKEN FROM GITHUB
./config.sh --url https://github.com/jleechan2015/worldarchitect.ai --token YOUR_RUNNER_TOKEN --labels self-hosted,claude
```

#### 3.2 Get Your Runner Token
1. Go to: https://github.com/jleechan2015/worldarchitect.ai/settings/actions/runners
2. Click "New self-hosted runner"
3. Select your OS (Linux/macOS/Windows)
4. Copy the token from the configuration command
5. Use that token in the `./config.sh` command above

#### 3.3 Install and Start Runner Service
```bash
# Install as service (Linux/macOS)
sudo ./svc.sh install

# Start service
sudo ./svc.sh start

# Check status
sudo ./svc.sh status
```

#### 3.4 Verify Runner is Online
1. Go to: https://github.com/jleechan2015/worldarchitect.ai/settings/actions/runners
2. You should see your runner listed with status "Online"
3. It should have labels: `self-hosted, claude`

### Phase 4: End-to-End Test

#### 4.1 Make Sure Everything is Running
- [ ] Claude endpoint server is running (`./start-claude-slash-commands.sh`)
- [ ] GitHub runner service is online
- [ ] GitHub secrets are configured

#### 4.2 Test in a PR Comment
1. Create or find any PR in your repository
2. Add a comment: `/claude Hello! Please respond with "GitHub slash command working!"`
3. Watch for:
   - GitHub adds "eyes" reaction to your comment (dispatch working)
   - New comment appears with Claude's response (processor working)

## 🔧 Troubleshooting Guide

### If Local Tests Fail
```bash
# Check if Claude Code CLI works
claude-code --version

# Check if server can start
python3 claude-endpoint-server.py
# Should show: "Starting Claude endpoint server on http://127.0.0.1:5001"

# Check port availability
netstat -an | grep 5001
# Should be empty (port available) or show LISTEN (server running)
```

### If GitHub Runner Fails
```bash
# Check runner logs
sudo journalctl -u actions.runner.jleechan2015-worldarchitect.ai.* -f

# Check runner status
sudo ./svc.sh status

# Restart runner
sudo ./svc.sh stop
sudo ./svc.sh start
```

### If PR Test Fails
1. **Check GitHub Actions logs:**
   - Go to: https://github.com/jleechan2015/worldarchitect.ai/actions
   - Look for "Slash Command Dispatch" and "Claude Processor" workflows
   - Check for error messages

2. **Verify runner connectivity:**
   - Runner must be able to reach `127.0.0.1:5001`
   - If Claude endpoint is on different machine, update `CLAUDE_ENDPOINT` secret

3. **Check secrets:**
   - `REPO_ACCESS_TOKEN` - must have `repo` scope
   - `CLAUDE_ENDPOINT` - must be reachable from runner

## 🎯 Success Criteria

You'll know it's working when:
- [ ] Local endpoint server starts without errors
- [ ] Test script passes all checks
- [ ] GitHub runner shows "Online" status with `claude` label
- [ ] `/claude` comment in PR gets "eyes" reaction
- [ ] Claude's response appears as new comment within 30-60 seconds

## 🚀 Usage Examples Once Working

```
/claude What does this PR do?

/claude Review this code for potential bugs

/claude Generate unit tests for the new functions

/claude Explain the security implications of these changes

/claude What are the performance considerations here?
```

## 📁 Files You Created

All these files are now in your repository:
- `.github/workflows/slash-dispatch.yml` - GitHub Actions dispatcher
- `.github/workflows/claude-processor.yml` - GitHub Actions processor  
- `claude-endpoint-server.py` - Local HTTP server
- `test-claude-endpoint.py` - Testing script
- `start-claude-slash-commands.sh` - Startup script
- `GITHUB_CLAUDE_SLASH_COMMANDS.md` - Full documentation
- `CLAUDE_SLASH_COMMANDS_SUMMARY.md` - Quick overview

## 🆘 If You Get Stuck

1. **Start with local testing** - don't set up GitHub until local works
2. **Check the logs** - both endpoint server and GitHub Actions workflows
3. **One step at a time** - don't try to debug everything at once
4. **Verify network connectivity** - runner must reach your Claude endpoint

## 🎉 Next Steps After Success

1. **Customize responses** - edit `claude-endpoint-server.py` for custom prompts
2. **Add rate limiting** - prevent abuse in production
3. **Monitor usage** - add logging for request tracking
4. **Multiple endpoints** - run different Claude configs on different ports
5. **Team sharing** - document for other team members

---

**Current Status:** ✅ Code implemented, ready for your setup
**Next Action:** Start with Phase 1 local testing