# Testing Claude Code Action

## Quick Test (Without API Key)

1. **Merge the PR first** (or test on the PR itself)
2. Comment on any PR: `@claude help`
3. You should see the workflow trigger in the Actions tab
4. It will fail with "Missing ANTHROPIC_API_KEY" - this confirms the workflow is set up correctly

## Full Testing (With API Key)

### Step 1: Get an API Key

Choose one option:

#### Option A: Anthropic API Key (Easiest)
1. Go to https://console.anthropic.com/
2. Sign up/login
3. Go to API Keys section
4. Create a new API key
5. Copy the key (starts with `sk-ant-`)

#### Option B: OAuth Token (For Claude Pro/Max users)
```bash
# Install Claude CLI
npm install -g @anthropic-ai/claude-github

# Generate token
claude setup-token
```

### Step 2: Add Secret to GitHub

1. Go to your repository: https://github.com/jleechan2015/worldarchitect.ai
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add:
   - Name: `ANTHROPIC_API_KEY`
   - Value: Your API key from Step 1

### Step 3: Test Commands

Create a test PR or use an existing one, then try these comments:

#### Basic Test
```
@claude help
```
Expected: Claude responds with available commands

#### Code Review
```
@claude review this PR
```
Expected: Claude analyzes the PR changes

#### Ask Questions
```
@claude what does the game_state.py file do?
```
Expected: Claude explains the file's purpose

#### Fix Issues
```
@claude fix the failing tests
```
Expected: Claude attempts to fix test failures

### Step 4: Monitor the Action

1. Go to **Actions** tab in your repo
2. You'll see "Claude Code Assistant" workflow runs
3. Click on a run to see details
4. Check the logs for any errors

## Testing Without Merging

You can test on the PR itself (#432):

1. Add the API key to your repository secrets (as above)
2. Go to PR #432: https://github.com/jleechan2015/worldarchitect.ai/pull/432
3. Comment: `@claude can you review this PR?`
4. Watch the Actions tab for the workflow

## Troubleshooting

### "Claude doesn't respond"
- Check Actions tab for workflow runs
- Ensure API key is correctly set
- Check workflow logs for errors

### "Authentication failed"
- Verify API key starts with `sk-ant-`
- Check it's in the right secret name: `ANTHROPIC_API_KEY`
- Try regenerating the key

### "Workflow doesn't trigger"
- Ensure you're commenting on a PR, not an issue
- Check the exact spelling: `@claude` (lowercase)
- Verify the workflow file exists in the main branch

## Local Testing (Advanced)

Test the action locally with `act`:

```bash
# Install act
brew install act  # or see https://github.com/nektos/act

# Create .env file
echo "ANTHROPIC_API_KEY=your-key-here" > .env

# Run locally
act issue_comment -e test-event.json --secret-file .env
```

Create `test-event.json`:
```json
{
  "action": "created",
  "issue": {
    "number": 1,
    "pull_request": {}
  },
  "comment": {
    "body": "@claude help",
    "user": {
      "login": "testuser"
    }
  }
}
```

## Quick Verification Checklist

- [ ] Workflow appears in Actions tab
- [ ] Commenting `@claude` triggers a workflow run
- [ ] With API key: Claude responds to comments
- [ ] Without API key: Workflow fails with auth error
- [ ] Check rate limits in Anthropic dashboard

## Cost Monitoring

Monitor your API usage at: https://console.anthropic.com/usage

Each interaction uses API credits based on:
- Input tokens (your comment + context)
- Output tokens (Claude's response)
- Number of turns in conversation
