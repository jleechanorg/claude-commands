# Claude Code Action Setup Guide

This repository uses the official [Claude Code Action](https://github.com/anthropics/claude-code-action) to enable AI-powered assistance directly in GitHub pull requests and issues.

## Setup Instructions

### 1. Authentication Setup

You have two options for authentication:

#### Option A: Anthropic API Key (Recommended)
1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Create an API key
3. In your GitHub repository:
   - Go to Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `ANTHROPIC_API_KEY`
   - Value: Your API key from Anthropic

#### Option B: OAuth Token (For Claude Pro/Max Users)
1. Install Claude for GitHub from your local machine:
   ```bash
   npm install -g @anthropic-ai/claude-github
   claude setup-token
   ```
2. Follow the prompts to generate an OAuth token
3. Add the token as a GitHub secret:
   - Name: `CLAUDE_CODE_OAUTH_TOKEN`
   - Value: Your generated OAuth token

### 2. Enable the Workflow

The workflow is already configured in `.github/workflows/claude-code.yml`. Once you've added your authentication secret, it will automatically activate.

## Usage

### Basic Commands

In any pull request or issue, mention `@claude` to interact with the AI assistant:

- **Ask questions**: `@claude what does the game_state.py file do?`
- **Request code review**: `@claude review this PR`
- **Fix issues**: `@claude fix the failing tests`
- **Implement features**: `@claude add error handling to the save_campaign function`

### Examples

```
@claude help me understand the Gemini API integration

@claude fix the type errors in firestore_service.py

@claude add unit tests for the new dice rolling feature

@claude review this PR and suggest improvements
```

## Configuration

The workflow is configured with:
- **Trigger phrase**: `@claude`
- **Max turns**: 3 (number of back-and-forth exchanges)
- **Timeout**: 30 minutes
- **Base branch**: main

### Custom System Prompt

The action includes a custom system prompt with WorldArchitect.AI project context to ensure Claude understands:
- The technology stack
- Project structure
- Testing conventions
- Coding standards from CLAUDE.md

## Permissions

The action requires these permissions:
- `contents: write` - To read/write code
- `pull-requests: write` - To comment on PRs
- `issues: write` - To comment on issues
- `actions: read` - To check CI status

## Security Best Practices

1. **Never commit API keys** - Always use GitHub secrets
2. **Review changes** - Claude will create commits; always review them
3. **Limit permissions** - Only give collaborator access to trusted users
4. **Monitor usage** - Check your Anthropic dashboard for API usage

## Troubleshooting

### Claude doesn't respond
- Check that your API key is correctly set in GitHub secrets
- Ensure the workflow file exists at `.github/workflows/claude-code.yml`
- Check the Actions tab for any workflow errors

### Authentication errors
- Verify your API key is valid in the Anthropic console
- For OAuth, regenerate the token with `claude setup-token`

### Rate limiting
- Claude Code Action respects Anthropic API rate limits
- If you hit limits, wait a few minutes before trying again

## Advanced Configuration

See `.github/workflows/claude-code-advanced.yml.example` for additional configuration options including:
- Custom file restrictions
- Auto-review on PR creation
- Integration with specific test commands
- Command aliases

## Support

- [Claude Code Action Documentation](https://github.com/anthropics/claude-code-action)
- [Anthropic Support](https://support.anthropic.com/)
- Project-specific issues: Create an issue in this repository