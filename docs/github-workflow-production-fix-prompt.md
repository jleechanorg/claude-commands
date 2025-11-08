# GitHub Production Workflow Fix Prompt

**Use this prompt in other repositories that copied the production deployment workflow from worldarchitect.ai**

---

## Prompt to Copy-Paste:

```
I need to fix the GitHub Actions production deployment workflow that was copied from another repo. It has several configuration issues that need to be corrected for this repository.

## Issues to Fix:

1. **Wrong GCP Project ID**
   - The workflow uses `ai-universe-2025` but should use the correct project for this repo
   - Find the correct project: `gcloud projects list`
   - Update ALL references in `.github/workflows/deploy-production.yml`

2. **Missing GitHub Secret**
   - The workflow expects `GCP_SA_KEY` secret but it's not configured
   - Create service account key and add as GitHub secret
   - Ensure service account has proper permissions

3. **Cloud Build Log Streaming Issue**
   - Deploy scripts need `--no-stream-logs` flag to prevent permission errors
   - Update `scripts/deploy_common.sh` (or equivalent deploy script)

4. **Service Account Permissions**
   - Service account needs these roles:
     - `roles/cloudbuild.builds.editor`
     - `roles/storage.admin`
     - `roles/run.admin`
     - `roles/iam.serviceAccountUser`

## Steps to Complete:

### 1. Identify Correct GCP Project
```bash
# List all projects and identify the correct one for this repo
gcloud projects list

# Note the PROJECT_ID for this specific repository
```

### 2. Find All Wrong Project References
Search `.github/workflows/deploy-production.yml` for:
- `ai-universe-2025` (replace with correct PROJECT_ID)
- Console URLs with wrong project IDs
- Any hardcoded project references

### 3. Fix Deploy Script
In `scripts/deploy_common.sh` (or equivalent):

**Find this:**
```bash
deploy_common::submit_build() {
  local context_dir=$1
  local image_tag=$2
  (cd "$context_dir" && gcloud builds submit . --tag "$image_tag")
}
```

**Replace with:**
```bash
deploy_common::submit_build() {
  local context_dir=$1
  local image_tag=$2
  (cd "$context_dir" && gcloud builds submit . --tag "$image_tag" --no-stream-logs)
}
```

### 4. Create Service Account and Grant Permissions
```bash
# Identify or create service account (usually dev-runner@PROJECT_ID.iam.gserviceaccount.com)
gcloud iam service-accounts list --project PROJECT_ID

# Grant required permissions
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
  --role="roles/cloudbuild.builds.editor"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
  --role="roles/iam.serviceAccountUser"
```

### 5. Create and Add GitHub Secret
```bash
# Create service account key
gcloud iam service-accounts keys create ~/gcp-github-actions-key.json \
  --iam-account=SERVICE_ACCOUNT_EMAIL \
  --project PROJECT_ID

# Add as GitHub secret using gh CLI
cat ~/gcp-github-actions-key.json | gh secret set GCP_SA_KEY

# Clean up local key file
rm ~/gcp-github-actions-key.json
```

### 6. Update Workflow File
Replace ALL instances in `.github/workflows/deploy-production.yml`:
- Project IDs: `ai-universe-2025` → `YOUR_PROJECT_ID`
- Service names: Update to match your actual Cloud Run service names
- Region: Update if different from `us-central1`
- Console URLs: Fix project IDs in all GitHub step summary URLs

### 7. Create PR and Test
```bash
# Create branch
git checkout -b fix/production-deployment-workflow

# Add changes
git add .github/workflows/deploy-production.yml scripts/deploy_common.sh

# Commit
git commit -m "Fix production deployment workflow for this repository

- Update GCP project ID from ai-universe-2025 to correct project
- Add --no-stream-logs flag to prevent permission errors
- Fix console URLs in workflow

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push and create PR
git push origin HEAD:fix/production-deployment-workflow
gh pr create --title "Fix production deployment workflow" --body "Fixes production deployment workflow configuration for this repository"
```

## Verification Checklist:

After making these changes, verify:

- [ ] Correct GCP project ID in all workflow steps
- [ ] Service account has all 4 required roles
- [ ] `GCP_SA_KEY` secret exists in GitHub repository settings
- [ ] `--no-stream-logs` flag added to deploy script
- [ ] Console URLs in workflow point to correct project
- [ ] Service names match actual Cloud Run services
- [ ] Region matches your deployment region
- [ ] Workflow can authenticate to GCP successfully
- [ ] Builds complete without permission errors
- [ ] Traffic routes correctly to new revisions

## Common Mistakes to Avoid:

1. ❌ Forgetting to update console URLs (they have project IDs too)
2. ❌ Missing service account permissions (need all 4 roles)
3. ❌ Not removing old service account keys after creating new ones
4. ❌ Using wrong service account (some repos have multiple)
5. ❌ Forgetting to add `--no-stream-logs` flag
6. ❌ Leaving hardcoded project IDs in comments/documentation

## Expected Results:

After fixes:
- ✅ GitHub Actions can authenticate to GCP
- ✅ Builds complete successfully without streaming errors
- ✅ Deployments update Cloud Run services correctly
- ✅ Traffic routes to latest revision automatically
- ✅ All logs available in Cloud Logging
- ✅ Health checks pass
- ✅ No permission denied errors

Please fix all these issues systematically and create a PR with the changes.
```

---

## Quick Reference Commands:

### Find Current Issues
```bash
# Check what project workflow is using
grep "project" .github/workflows/deploy-production.yml

# Check if secret exists
gh secret list | grep GCP_SA_KEY

# Check deploy script
grep "gcloud builds submit" scripts/deploy_common.sh
```

### Verify Service Account
```bash
# List service accounts
gcloud iam service-accounts list --project PROJECT_ID

# Check permissions
gcloud projects get-iam-policy PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:SERVICE_ACCOUNT_EMAIL"
```

### Test Deployment After Fix
```bash
# Trigger workflow manually
gh workflow run deploy-production.yml --ref main -f confirm_production="DEPLOY TO PRODUCTION"

# Monitor run
gh run list --workflow=deploy-production.yml --limit 1
```

---

**Template Created:** 2025-11-08
**Source Issue:** worldarchitect.ai production deployment fixes (PR #1962, #1963)
**Applies To:** All repositories that copied the production workflow template
