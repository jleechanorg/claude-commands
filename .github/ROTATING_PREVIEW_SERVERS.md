# GCP Preview Server Rotation Guide - WorldArchitect.AI

This document provides complete documentation for the rotating server pool system for PR preview deployments on Google Cloud Run.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [System Components](#system-components)
- [How It Works](#how-it-works)
- [Usage](#usage)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

## Architecture Overview

### Problem Solved

- **Old System**: Created a new Cloud Run service for every PR (`mvp-site-app-pr-123`)
  - ❌ Slow deployments (service creation overhead)
  - ❌ Unpredictable URLs
  - ❌ Resource management complexity

- **New System**: Pre-allocated pool of 10 Cloud Run services that rotate PRs
  - ✅ Fast deployments (no service creation)
  - ✅ Predictable URLs (s1-s10)
  - ✅ Automatic cleanup and reuse
  - ✅ LRU eviction when pool is full

### Solution Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Server Pool (s1-s10)                    │
├─────────────────────────────────────────────────────────────┤
│ mvp-site-app-s1  │ mvp-site-app-s2  │ ... │ mvp-site-app-s10│
│   PR #123        │   PR #456        │     │   (available)   │
└─────────────────────────────────────────────────────────────┘
         ↑                  ↑                        ↑
         │                  │                        │
    PR opened          PR opened               PR pool full
    assigns s1         assigns s2           evicts oldest PR
```

**State Management**: Cloud Run service labels (`pr-number`) are the source of truth

**Benefits**:
- ✅ Fast deployments (reuse existing services)
- ✅ Predictable URLs (e.g., `mvp-site-app-s3.run.app`)
- ✅ No state file management
- ✅ Automatic cleanup via GitHub Actions
- ✅ Handles concurrent PRs gracefully

## System Components

### 1. Server Pool Script

**Location**: `.github/scripts/pr-server-pool.sh`

**Functions**:
- `assign <PR_NUMBER>` - Assign an available server to a PR
- `release <PR_NUMBER>` - Release a server back to the pool
- `status` - Display current pool utilization

**How It Works**:
1. Queries Cloud Run services using `gcloud run services describe`
2. Reads `pr-number` label from each service
3. Stateless logic - Cloud Run is the source of truth
4. LRU eviction - evicts service with oldest `lastTransitionTime`

**Configuration**:
```bash
POOL_SIZE=10                          # Number of preview servers
SERVICE_PREFIX="mvp-site-app"         # Service name prefix
GCP_PROJECT="worldarchitecture-ai"    # GCP project ID
GCP_REGION="us-central1"              # Cloud Run region
```

**Example Usage**:
```bash
# Assign server to PR #123
.github/scripts/pr-server-pool.sh assign 123
# Output: {"server":"s3","serviceName":"mvp-site-app-s3","evicted":null}

# Release server from PR #123
.github/scripts/pr-server-pool.sh release 123
# Output: {"server":"s3","serviceName":"mvp-site-app-s3"}

# Check pool status
.github/scripts/pr-server-pool.sh status
# Shows table of server assignments
```

### 2. PR Preview Workflow

**Location**: `.github/workflows/pr-preview.yml`

**Trigger**: Pull request events (opened, reopened, synchronize, ready_for_review)

**Key Steps**:
1. **Assign Server**: Uses pool script to assign an available server
2. **Notify Evictions**: If pool is full, notifies the evicted PR
3. **Build Image**: Builds Docker image and pushes to GCR
4. **Deploy**: Deploys to assigned Cloud Run service with `pr-number` label
5. **Health Check**: Verifies the deployed service is healthy
6. **Post Comment**: Posts preview URL and deployment details to PR

**Service Configuration**:
```yaml
Environment: preview
Memory: 512Mi
CPU: 1
Max Instances: 2
Timeout: 300s
Secrets: GEMINI_API_KEY (from Secret Manager)
```

### 3. PR Cleanup Workflow

**Location**: `.github/workflows/pr-cleanup.yml`

**Trigger**: Pull request closed

**Key Steps**:
1. **Find Assignment**: Uses pool script to find which server was assigned
2. **Remove Label**: Removes `pr-number` label from Cloud Run service
3. **Post Comment**: Confirms cleanup and server release
4. **Show Status**: Displays updated pool status

**Important**: Services are NOT deleted, only labels are removed (for fast redeployment)

## How It Works

### PR Opens

```
1. PR #123 opened
   ↓
2. Workflow triggers (pr-preview.yml)
   ↓
3. Script assigns server: s3
   ↓
4. Docker image built: gcr.io/worldarchitecture-ai/mvp-site-app-s3:SHA
   ↓
5. Deploy to mvp-site-app-s3 with label pr-number=123
   ↓
6. Health check passes
   ↓
7. Comment posted with preview URL
```

### PR Closes

```
1. PR #123 closed
   ↓
2. Cleanup workflow triggers (pr-cleanup.yml)
   ↓
3. Script finds server: s3 assigned to PR #123
   ↓
4. Remove label: pr-number from mvp-site-app-s3
   ↓
5. Server s3 now available for new PRs
   ↓
6. Comment posted confirming cleanup
```

### Pool Full (Eviction)

```
1. PR #789 opened, pool full (all 10 servers assigned)
   ↓
2. Script finds oldest deployment: s5 (PR #123)
   ↓
3. Evict PR #123 from s5
   ↓
4. Assign s5 to PR #789
   ↓
5. Notify PR #123 that it was evicted
   ↓
6. Deploy PR #789 to s5
```

## Usage

### For Developers

**Opening a PR**:
1. Open a PR with changes to `mvp_site/`, `Dockerfile`, or deployment scripts
2. Wait 5-8 minutes for deployment
3. Check PR comments for preview URL
4. URL format: `https://mvp-site-app-s{N}-{HASH}.run.app`

**Closing a PR**:
- Server is automatically released back to the pool
- Service remains running (not deleted)

**If Your PR is Evicted**:
- You'll receive a comment notification
- To get a new preview: Close and reopen your PR
- Or wait for pool capacity to free up

### For Administrators

**Check Pool Status**:
```bash
.github/scripts/pr-server-pool.sh status
```

**Manually Release a Server**:
```bash
# Find which server is assigned to PR #123
.github/scripts/pr-server-pool.sh release 123

# Remove the label from Cloud Run
gcloud run services update mvp-site-app-s3 \
  --project=worldarchitecture-ai \
  --region=us-central1 \
  --remove-labels=pr-number
```

**Increase Pool Size**:
Edit `.github/scripts/pr-server-pool.sh`:
```bash
POOL_SIZE=15  # Increase from 10 to 15
```

**Pre-create Services** (optional, for faster first deployment):
```bash
for i in {1..10}; do
  gcloud run deploy "mvp-site-app-s${i}" \
    --image=gcr.io/cloudrun/hello \
    --region=us-central1 \
    --platform=managed \
    --allow-unauthenticated \
    --memory=512Mi \
    --cpu=1 \
    --quiet
done
```

## Monitoring

### GitHub Actions

**Workflow Runs**:
- PR Preview: https://github.com/jleechanorg/worldarchitect.ai/actions/workflows/pr-preview.yml
- PR Cleanup: https://github.com/jleechanorg/worldarchitect.ai/actions/workflows/pr-cleanup.yml

**Check Recent Deployments**:
```bash
gh run list --workflow=pr-preview.yml --limit 10
```

### Google Cloud Console

**Cloud Run Services**:
- Console: https://console.cloud.google.com/run?project=worldarchitecture-ai
- Filter by `mvp-site-app-s*` to see pool services

**Check Service Labels**:
```bash
gcloud run services describe mvp-site-app-s3 \
  --project=worldarchitecture-ai \
  --region=us-central1 \
  --format="value(metadata.labels)"
```

### Pool Metrics

**Utilization**:
```bash
# Get current assignments
.github/scripts/pr-server-pool.sh status

# Count assigned servers
gcloud run services list \
  --project=worldarchitecture-ai \
  --region=us-central1 \
  --filter="metadata.name:mvp-site-app-s*" \
  --format="value(metadata.labels.pr-number)" | grep -v "^$" | wc -l
```

## Troubleshooting

### Service Assignment Issues

**Problem**: PR not getting assigned to a server

**Solutions**:
```bash
# 1. Check script has execute permissions
chmod +x .github/scripts/pr-server-pool.sh

# 2. Verify gcloud CLI is authenticated
gcloud auth list

# 3. Check GCP service account has Cloud Run Admin role
gcloud projects get-iam-policy worldarchitecture-ai \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:*" \
  --format="table(bindings.role)"

# 4. Test script locally
.github/scripts/pr-server-pool.sh status
```

### Label Not Updating

**Problem**: Service label doesn't update after deployment

**Solutions**:
```bash
# 1. Check if label was set
gcloud run services describe mvp-site-app-s3 \
  --region=us-central1 \
  --format="value(metadata.labels)"

# 2. Manually update label
gcloud run services update mvp-site-app-s3 \
  --project=worldarchitecture-ai \
  --region=us-central1 \
  --update-labels="pr-number=123"

# 3. Verify service account has run.services.update permission
gcloud projects get-iam-policy worldarchitecture-ai \
  --flatten="bindings[].members" \
  --filter="bindings.role:roles/run.admin"
```

### Pool Always Full

**Problem**: All servers show as assigned

**Solutions**:
```bash
# 1. Check if cleanup workflow is running on PR close
gh run list --workflow=pr-cleanup.yml --limit 5

# 2. Manually release stale servers
# Find closed PRs still holding servers
for i in {1..10}; do
  PR=$(gcloud run services describe "mvp-site-app-s${i}" \
    --region=us-central1 \
    --format="value(metadata.labels.pr-number)" 2>/dev/null)

  if [ -n "$PR" ]; then
    # Check if PR is still open
    STATUS=$(gh pr view "$PR" --json state --jq '.state' 2>/dev/null || echo "CLOSED")
    if [ "$STATUS" = "CLOSED" ]; then
      echo "Releasing server s${i} from closed PR #$PR"
      gcloud run services update "mvp-site-app-s${i}" \
        --region=us-central1 \
        --remove-labels=pr-number
    fi
  fi
done

# 3. Increase POOL_SIZE in pr-server-pool.sh
```

### Deployment Failures

**Problem**: Deployment succeeds but service doesn't work

**Solutions**:
```bash
# 1. Check Cloud Run logs
gcloud run services logs read mvp-site-app-s3 \
  --project=worldarchitecture-ai \
  --region=us-central1 \
  --limit=50

# 2. Verify Docker image builds locally
docker build -t test-image mvp_site/

# 3. Check health endpoint
curl -v https://mvp-site-app-s3-HASH.run.app/health

# 4. Verify secrets are available
gcloud secrets versions access latest --secret=gemini-api-key
```

### Eviction Not Working

**Problem**: Evicted PR doesn't receive notification

**Solutions**:
```bash
# 1. Check workflow logs
gh run view --log

# 2. Verify GH_TOKEN has write permissions
# In workflow: permissions.pull-requests: write

# 3. Test eviction notification manually
gh pr comment 123 --body "Test notification"
```

## Cost Optimization

### Cloud Run Pricing

**Current Configuration**:
- Idle services with `--min-instances=0` cost nothing
- Only pay for active preview usage
- Pool of 10 services ≈ $0/month when idle

**Optimization Tips**:
1. ✅ Use `--min-instances=0` to avoid idle costs (already configured)
2. ✅ Set reasonable `--max-instances=2` to prevent runaway costs (already configured)
3. ✅ Use `--cpu=1` for previews (cheaper than production)
4. ✅ Set `--timeout=300` for faster cold start recovery
5. 📊 Monitor usage: https://console.cloud.google.com/run?project=worldarchitecture-ai

### Resource Limits

**Current Limits** (per service):
```yaml
Memory: 512Mi      # Adequate for Flask app
CPU: 1             # Single vCPU
Max Instances: 2   # Prevents excessive scaling
Timeout: 300s      # 5 minutes
```

**Recommended for High Traffic**:
- Increase memory to 1Gi for better performance
- Increase max instances to 5 for burst handling
- Monitor cold start times and adjust min instances

## Security Considerations

### Service Account Permissions

**Minimum Required**:
- `roles/run.admin` - Deploy and manage Cloud Run services
- `roles/cloudbuild.builds.builder` - Build Docker images
- `roles/secretmanager.secretAccessor` - Access Gemini API key

**Best Practices**:
- ✅ Use Workload Identity Federation (already configured)
- ✅ Store service account key in GitHub Secrets (already configured)
- ✅ Rotate service account keys regularly
- ❌ Never commit secrets to repository

### Preview Access Control

**Current Configuration**: `--allow-unauthenticated`
- ✅ Good for: Public QA and testing
- ❌ Risk: Anyone with URL can access preview

**For Private Previews**:
```bash
# Use Cloud IAM for authentication
gcloud run services update mvp-site-app-s1 \
  --no-allow-unauthenticated \
  --region=us-central1
```

### Secrets Management

**Current Secrets**:
- `GEMINI_API_KEY` - Stored in GCP Secret Manager (latest version)
- `GCP_SA_KEY` - Stored in GitHub Secrets

**Access Pattern**:
```yaml
--set-secrets="GEMINI_API_KEY=gemini-api-key:latest"
```

**Best Practices**:
- ✅ Use Secret Manager for runtime secrets (already configured)
- ✅ Use GitHub Secrets for CI/CD credentials (already configured)
- ✅ Use `latest` alias for automatic rotation
- ❌ Never hardcode secrets in Dockerfile or code

## Migration Notes

### Migrating from Old System

**Old System** (`pr-dev-preview.yml`):
- Created service: `mvp-site-app-pr-{PR_NUMBER}`
- One service per PR
- Services deleted on PR close

**New System** (`pr-preview.yml` + `pr-cleanup.yml`):
- Reuses services: `mvp-site-app-s{1-10}`
- Pool of 10 rotating servers
- Services persist, only labels removed

**Transition Plan**:
1. ✅ New workflows created (`pr-preview.yml`, `pr-cleanup.yml`)
2. 📋 Old workflow remains (`pr-dev-preview.yml`)
3. 🔄 **Next Step**: Disable old workflow after testing new system
4. 🧹 **Cleanup**: Delete old per-PR services after migration

**Cleanup Old Services**:
```bash
# List all old per-PR services
gcloud run services list \
  --project=worldarchitecture-ai \
  --region=us-central1 \
  --filter="metadata.name:mvp-site-app-pr-*" \
  --format="value(metadata.name)"

# Delete old services (after verifying)
for service in $(gcloud run services list --filter="metadata.name:mvp-site-app-pr-*" --format="value(metadata.name)"); do
  gcloud run services delete "$service" \
    --region=us-central1 \
    --quiet
done
```

## Additional Resources

- **GCP Cloud Run Documentation**: https://cloud.google.com/run/docs
- **GitHub Actions Documentation**: https://docs.github.com/en/actions
- **WorldArchitect.AI GitHub**: https://github.com/jleechanorg/worldarchitect.ai
- **SHA-Pinning Guidelines**: [.github/README.md](.github/README.md)

---

**Last Updated**: 2025-11-19
**System Version**: v1.0
**Maintained By**: WorldArchitect.AI Team
