# GitHub Claude Bot Commands Setup Guide

This guide implements a complete GitHub bot command system that responds to `/claude` comments in pull requests by sending prompts to your locally-hosted Claude instance and posting replies back to GitHub.

## Overview

The system consists of:
1. **Bot Command Dispatcher** - GitHub Actions workflow that captures `/claude` comments
2. **Claude Bot Processor** - GitHub Actions workflow that processes the commands on a self-hosted runner
3. **Local Claude Bot Server** - Python server that forwards prompts to Claude Code CLI
4. **Self-hosted GitHub Runner** - Connects GitHub to your local Claude instance

## Prerequisites

- Claude Code CLI installed and working on your local machine
- Python 3.6+ for the endpoint server
- GitHub repository with Actions enabled
- GitHub Personal Access Token with `repo` scope

## Setup Instructions

### 1. Create GitHub Personal Access Token

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Give it a name like "Claude Slash Command Bot"
4. Select scope: **`repo`** (Full control of private repositories)
5. Copy the generated token (you'll need it for secrets)

### 2. Configure GitHub Secrets

In your GitHub repository, go to Settings → Secrets and variables → Actions, then add:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `REPO_ACCESS_TOKEN` | Your GitHub PAT | Allows commenting on PRs |
| `CLAUDE_ENDPOINT` | `http://127.0.0.1:5001/claude` | Local Claude endpoint URL |

### 3. Set Up Self-Hosted GitHub Runner

Download and configure a self-hosted runner for your repository:

```bash
# Create runner directory
mkdir actions-runner && cd actions-runner

# Download runner (Linux x64)
curl -o actions-runner-linux-x64-2.311.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz

# Extract
tar xzf ./actions-runner-linux-x64-2.311.0.tar.gz

# Configure runner
./config.sh --url https://github.com/OWNER/REPO --token YOUR_RUNNER_TOKEN --labels self-hosted,claude

# Install as service
sudo ./svc.sh install

# Start service
sudo ./svc.sh start
```

Replace `OWNER/REPO` with your GitHub repository path and get the runner token from your repository's Settings → Actions → Runners → New self-hosted runner.

### 4. Start the Local Claude Bot Server

```bash
# Start the Claude bot server
./start-claude-bot.sh
```

The server will run on `http://127.0.0.1:5001` by default. You can change the port with:

```bash
CLAUDE_ENDPOINT_PORT=8080 ./start-claude-bot.sh
```

### 5. Test the Health Check

Verify the endpoint is running:

```bash
curl http://127.0.0.1:5001/health
# Should return: Claude bot server is running
```

## Usage

### Basic Usage

In any pull request comment, type:

```
/claude What is the purpose of this PR?
```

The system will:
1. Capture the slash command via the dispatch workflow
2. Send a `repository_dispatch` event to trigger the processor
3. Extract the prompt from the comment
4. Forward it to your local Claude endpoint
5. Post Claude's response back as a comment

### Example Commands

```
/claude Review this code for potential bugs

/claude Explain the changes in this PR

/claude Generate unit tests for the new functions

/claude What are the security implications of this change?
```

## Workflow Files

The system includes two GitHub Actions workflows:

### `.github/workflows/slash-dispatch.yml`
- Captures `/claude` comments on pull requests
- Adds an "eyes" reaction to acknowledge the command
- Triggers the processor via `repository_dispatch`

### `.github/workflows/claude-processor.yml`
- Runs on the self-hosted runner with `claude` label
- Extracts the prompt from the slash command
- Calls the local Claude endpoint
- Posts the response back to the PR

## Local Claude Endpoint Server

The `claude-endpoint-server.py` script:
- Runs an HTTP server on port 5001
- Accepts POST requests with prompts
- Forwards prompts to Claude Code CLI
- Returns Claude's responses
- Includes health check endpoint
- Handles both JSON and form-encoded requests

## Troubleshooting

### Runner Issues
- Check runner status: `sudo ./svc.sh status`
- View runner logs: `sudo journalctl -u actions.runner.OWNER-REPO.SERVICE-NAME -f`
- Ensure runner has `claude` label

### Endpoint Issues
- Test endpoint: `curl -X POST -d "prompt=Hello" http://127.0.0.1:5001/claude`
- Check server logs for errors
- Verify Claude Code CLI is accessible from the runner

### GitHub Actions Issues
- Check Actions tab for workflow runs
- Verify secrets are properly configured
- Ensure PAT has sufficient permissions

### Network Issues
- Confirm self-hosted runner can reach `127.0.0.1:5001`
- Check firewall settings
- Verify Claude endpoint is bound to correct interface

## Security Considerations

- The endpoint only accepts requests from localhost
- GitHub PAT should have minimal required permissions
- Self-hosted runner runs in isolated environment
- Consider rate limiting for production use

## Customization

### Custom Claude Commands
Modify `claude-endpoint-server.py` to customize how prompts are sent to Claude:

```python
# Example: Add custom system prompts
result = subprocess.run([
    'claude-code', 
    '--message', f"System: You are a code reviewer.\n\nUser: {prompt}"
], capture_output=True, text=True, timeout=60)
```

### Response Formatting
Modify the comment template in `claude-processor.yml`:

```yaml
body: |
  **🤖 Claude Analysis**
  
  ${{ steps.y.outputs.answer }}
  
  *Powered by local Claude instance*
```

### Multiple Models
Extend the endpoint to support different models:

```
/claude-fast Quick question about this code
/claude-detailed Comprehensive analysis needed
```

## Cost and Performance

- **Zero API costs** - Everything runs locally
- **Response time** - Depends on local Claude performance (~5-30 seconds)
- **Concurrent requests** - Limited by local resources
- **Privacy** - All processing happens on your infrastructure

## Advanced Configuration

### Running as Systemd Service

Create `/etc/systemd/system/claude-endpoint.service`:

```ini
[Unit]
Description=Claude Endpoint Server
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/your/repo
ExecStart=/usr/bin/python3 /path/to/your/repo/claude-endpoint-server.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable claude-endpoint
sudo systemctl start claude-endpoint
```

### Load Balancing Multiple Claude Instances

For high-traffic repositories, you can run multiple Claude endpoints on different ports and use a load balancer.

## Monitoring

### Log Analysis
Monitor the endpoint server logs for usage patterns:

```bash
# View real-time logs
tail -f /var/log/claude-endpoint.log

# Analyze request patterns
grep "Received prompt" /var/log/claude-endpoint.log | wc -l
```

### GitHub Actions Monitoring
- Monitor workflow success rates in Actions tab
- Set up notifications for failed workflows
- Track response times and usage

## Contributing

To improve this system:
1. Fork the repository
2. Test your changes with the local setup
3. Submit PR with clear description of improvements
4. Include any new configuration requirements

## Support

For issues:
1. Check the troubleshooting section
2. Review GitHub Actions logs
3. Test endpoint connectivity manually
4. Verify runner configuration and labels

This system provides a complete, self-hosted solution for GitHub-integrated Claude assistance without external API dependencies.