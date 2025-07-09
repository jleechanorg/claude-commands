# Scratchpad - Fix GitHub Actions PR Permissions Error

## Problem Description
GitHub Actions workflow is failing with:
```
Run if [ "pull_request" = "pull_request" ]; then
GraphQL: Resource not accessible by integration (repository.pullRequest)
Error: Process completed with exit code 1.
```

## Error Analysis
1. **GraphQL Error**: "Resource not accessible by integration" for `repository.pullRequest`
2. **Context**: This error typically occurs when a GitHub Actions workflow tries to access PR information without proper permissions
3. **Suspicious Condition**: `if [ "pull_request" = "pull_request" ]` is always true

## Investigation Plan

### Step 1: Identify the Failing Workflow
- [ ] Check `.github/workflows/` directory for all workflow files
- [ ] Look for workflows that use GraphQL queries or PR operations
- [ ] Find the specific workflow with the suspicious condition

### Step 2: Analyze Permission Issues
- [ ] Check the `permissions:` block in the workflow
- [ ] Verify if it needs `pull-requests: read` or `pull-requests: write`
- [ ] Check if it's using the correct GitHub token (GITHUB_TOKEN vs PAT)

### Step 3: Fix the Condition
- [ ] The condition `if [ "pull_request" = "pull_request" ]` should likely be checking an environment variable
- [ ] Should probably be: `if [ "${{ github.event_name }}" = "pull_request" ]`

### Step 4: Common Fixes
1. **Add proper permissions**:
   ```yaml
   permissions:
     pull-requests: read  # or write
     contents: read
   ```

2. **Fix the conditional**:
   ```yaml
   if: github.event_name == 'pull_request'
   ```

3. **Use proper token**:
   - Default `GITHUB_TOKEN` for read operations
   - Personal Access Token (PAT) for cross-repo or elevated permissions

## Next Steps
1. Search for the failing workflow file
2. Analyze its current permissions and GraphQL queries
3. Implement the fix
4. Test with a draft PR

## Status
🔄 Investigation starting...

## Investigation Results

### Found the Issue!
- **File**: `.github/workflows/auto_resolve_conflicts.yml`
- **Problem**: The workflow uses `gh pr` commands but has NO permissions block
- **Specific commands failing**:
  - Line 43: `gh pr list` 
  - Line 53: `gh pr view $PR_NUMBER`
  - Line 85: `gh pr comment`

### Root Cause
The workflow is missing the `permissions:` block entirely. When using GitHub CLI to query or modify PRs, explicit permissions are required.

### Solution
Add permissions block after line 13:
```yaml
    permissions:
      contents: write      # For git operations
      pull-requests: write # For PR queries and comments
```

## Implementation
✅ **Fixed!** Added the permissions block to `.github/workflows/auto_resolve_conflicts.yml`

The workflow now has proper permissions to:
- Query PR information using `gh pr list` and `gh pr view`
- Post comments to PRs using `gh pr comment`
- Push commits back to the branch (contents: write)

## Testing
The fix will be tested when:
1. This PR is created
2. Any PR with conflicts triggers the workflow
3. A push to a branch with an open PR occurs

## Status
✅ **COMPLETE** - Fix implemented and ready for PR