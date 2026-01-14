# PR Preview Comment Posting Fix

## Issue Summary

PR preview comments were not always being posted, even when deployments succeeded. This was caused by:

1. **Conditional execution**: The comment step used `if: ${{ success() }}`, meaning it only ran if ALL previous steps succeeded. If any step failed (e.g., health check timeout), the comment wouldn't be posted.

2. **No error handling**: The script had no try/catch blocks or validation, so API failures could fail silently.

3. **Missing validation**: The script didn't validate that required context (PR number, repo info) or environment variables existed before attempting to post.

## Root Cause

The workflow step condition:
```yaml
if: ${{ success() && github.event_name == 'pull_request' }}
```

This meant:
- If the health check step failed (even if deployment succeeded), the comment step was skipped entirely
- No error messages were logged when the comment posting failed
- Silent failures made debugging difficult

## Solution

### Changes Made

1. **Changed condition to `always()`**: Now runs even if some steps fail, as long as deployment info is available:
   ```yaml
   if: ${{ always() && github.event_name == 'pull_request' && steps.deployment_info.outputs.service_url != '' }}
   ```

2. **Added comprehensive error handling**:
   - Try/catch block around the entire script
   - Validation of required context (`context.payload.pull_request`)
   - Validation of required environment variables (`PREVIEW_URL`)
   - Graceful handling of missing optional values

3. **Added logging**:
   - Success message with comment ID when posting succeeds
   - Error messages with details when posting fails
   - Warning instead of failing the workflow if comment posting fails

4. **Improved resilience**:
   - Handles missing environment variables gracefully
   - Shows different messages based on deployment success/failure
   - Uses fallback values for optional fields

### Example Failure Scenarios Now Handled

1. **Health check timeout**: Comment still posts with warning message
2. **Missing PR context**: Error logged, workflow continues
3. **API rate limiting**: Error logged, workflow continues
4. **Missing environment variables**: Validation catches it early with clear error

## Testing

To verify the fix works:

1. Check that comments are posted even when health checks fail
2. Verify error messages appear in workflow logs when comment posting fails
3. Confirm workflow doesn't fail entirely if comment posting fails

## Related Files

- `.github/workflows/pr-preview.yml` - Main workflow file with comment posting logic
