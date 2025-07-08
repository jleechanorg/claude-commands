# Adding Anthropic API Key to GitHub Secrets

## Step-by-Step Instructions

### 1. Navigate to Your Repository Settings

Go to: https://github.com/jleechan2015/worldarchitect.ai/settings/secrets/actions

Or manually:
1. Open your repository: https://github.com/jleechan2015/worldarchitect.ai
2. Click on **Settings** (in the repository navigation bar)
3. In the left sidebar, scroll down to **Security** section
4. Click on **Secrets and variables**
5. Click on **Actions**

### 2. Add New Repository Secret

1. Click the green **New repository secret** button
2. Fill in the fields:
   - **Name**: `ANTHROPIC_API_KEY` (must be exactly this)
   - **Secret**: Paste your API key (sk-ant-api03-...)
3. Click **Add secret**

### 3. Verify the Secret

After adding, you should see:
- `ANTHROPIC_API_KEY` listed under "Repository secrets"
- It will show "Updated just now"
- The value will be hidden (shown as ***)

## Quick Checklist

- [ ] API key starts with `sk-ant-`
- [ ] Secret name is exactly `ANTHROPIC_API_KEY` (all caps)
- [ ] Added as Repository secret (not Environment or Organization)
- [ ] Shows in the secrets list

## Testing After Setup

1. Go to any PR (after the workflow is merged)
2. Comment: `@claude help`
3. Check Actions tab - workflow should run successfully
4. Claude should respond in the PR

## Troubleshooting

### "Bad credentials" error
- Double-check the API key is copied correctly
- Ensure no extra spaces before/after the key
- Try regenerating a new key in Anthropic Console

### "Secret not found" error
- Verify the secret name is exactly `ANTHROPIC_API_KEY`
- Check it's a Repository secret, not Organization
- Try deleting and re-adding the secret

### Still not working?
1. Check Actions tab for detailed error logs
2. Verify the workflow file exists in main branch
3. Ensure you have billing set up in Anthropic Console

## Security Notes

- Never commit API keys to code
- GitHub Secrets are encrypted
- Only accessible to workflows in your repo
- Rotate keys regularly for security