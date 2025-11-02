# GitHub Actions Workflows

This directory contains automated deployment workflows for WorldArchitect.AI.

## Overview

We use GitHub Actions for **two types of deployments**:
1. **Auto-deployment** (main → dev) - Fast iteration
2. **Manual production deployment** - Approval-based releases

---

## Workflows

### 1. Auto-Deploy to Development (`auto-deploy-dev.yml`)

**Trigger:** Push to `main` branch

**Purpose:** Automatically deploy development environment on every push to main for fast iteration.

**Flow:**
```
Push to main → GitHub Actions → GCP Cloud Build → Cloud Run (dev)
```

**Service deployed:**
- `mvp-site-app-dev`

**URL:**
- Auto-retrieved after deployment
- Check GitHub Actions summary for deployment URL

**Features:**
- ✅ Automatic trigger on push
- ✅ Health checks after deployment (/health endpoint)
- ✅ Deployment summary in GitHub UI
- ✅ No approval needed (dev environment)
- ✅ SHA-pinned actions for security

**View runs:**
https://github.com/jleechanorg/worldarchitect.ai/actions/workflows/auto-deploy-dev.yml

---

### 2. Deploy to Production (`deploy-production.yml`)

**Trigger:** Manual (`workflow_dispatch`)

**Purpose:** Deploy to production with required manual approval for safety.

**Flow:**
```
Manual trigger → Confirmation input → GitHub Actions → Wait for approval → GCP Cloud Build → Cloud Run (prod)
```

**Service deployed:**
- `mvp-site-app-stable`

**URL:**
- Auto-retrieved after deployment
- Check GitHub Actions summary for deployment URL

**Features:**
- ✅ Manual trigger only
- ✅ **Requires approval** from designated reviewers
- ✅ Double confirmation (text input + environment approval)
- ✅ Health checks after deployment (/health endpoint)
- ✅ Full audit trail of approvals
- ✅ Deployment summary in GitHub UI
- ✅ SHA-pinned actions for security

**How to deploy:**
1. Go to: https://github.com/jleechanorg/worldarchitect.ai/actions/workflows/deploy-production.yml
2. Click "Run workflow"
3. **Type exactly:** `DEPLOY TO PRODUCTION` (in the confirmation field)
4. Click "Run workflow" button
5. **Wait for approval** from designated reviewer
6. Reviewer approves in GitHub UI under "Environments → production"
7. Deployment proceeds automatically after approval

**View runs:**
https://github.com/jleechanorg/worldarchitect.ai/actions/workflows/deploy-production.yml

---

## Deployment Methods Comparison

| Method | Environment | Trigger | Approval | Use Case |
|--------|-------------|---------|----------|----------|
| **Auto-deploy workflow** | dev | Push to main | None | Fast development iteration |
| **Manual workflow** | production | Manual trigger | **Required** | Production releases |
| **Command line** | dev | `./deploy.sh mvp_site` | None | Local testing |
| **Command line** | production | ❌ **BLOCKED** | N/A | Prevented for safety |

---

## Environment Configuration

### Development (dev)
- **Trigger:** Automatic (push to main)
- **Approval:** None required
- **Service:** `mvp-site-app-dev`
- **Deploy command:** `./deploy.sh mvp_site`
- **Health check:** 10 retries, 5s intervals
- **Timeout:** 45min job, 30min deploy

### Production (stable)
- **Trigger:** Manual workflow only
- **Approval:** **Required** from designated reviewers
- **Service:** `mvp-site-app-stable`
- **Deploy command:** `./deploy.sh mvp_site stable` (GitHub Actions only)
- **Health check:** 15 retries, 10s intervals
- **Timeout:** 60min job, 40min deploy
- **Local deployment:** ❌ BLOCKED (must use GitHub Actions)

---

## Production Deployment Protection

### Why Production is Blocked Locally

Production deployments from local machines are **completely blocked** for safety:

```bash
$ ./deploy.sh mvp_site stable

================================================================================
🚨 PRODUCTION DEPLOYMENT BLOCKED 🚨
================================================================================

Production deployments are NOT allowed from local machines for safety.

You must use the GitHub Actions workflow with manual approval:
...
```

### Benefits of GitHub Actions Only

- ✅ **Proper approval process** - Required reviewer sign-off
- ✅ **Full audit trail** - Complete history in GitHub
- ✅ **Prevents accidents** - No accidental prod deployments
- ✅ **Team visibility** - Everyone sees production changes
- ✅ **Consistent process** - Same workflow every time

---

## Monitoring

### Development Deployments

After auto-deployment, check:
- GitHub Actions summary for deployment status
- Service health: `https://[service-url]/health`
- Cloud Run Console: https://console.cloud.google.com/run/detail/us-central1/mvp-site-app-dev?project=ai-universe-2025
- Logs: https://console.cloud.google.com/logs

### Production Deployments

After manual deployment with approval:
- GitHub Actions summary shows approval chain
- Service health: `https://[service-url]/health`
- Cloud Run Console: https://console.cloud.google.com/run/detail/us-central1/mvp-site-app-stable?project=ai-universe-2025
- Logs: https://console.cloud.google.com/logs

---

## Troubleshooting

### Auto-deployment not triggering

**Problem:** Push to main doesn't trigger deployment

**Solutions:**
1. Check if workflow is enabled in repository settings
2. Verify branch name is exactly `main`
3. Check workflow file syntax is valid YAML
4. Review Actions tab for failed workflow runs

### Health check failures

**Problem:** Deployment succeeds but health check fails

**Solutions:**
1. Verify `/health` endpoint is implemented and returns HTTP 200
2. Check Cloud Run logs for startup errors
3. Ensure environment variables/secrets are configured
4. Verify service has sufficient memory (2Gi)
5. Check for database connection issues

### Production workflow not showing approval

**Problem:** Production workflow doesn't require approval

**Solutions:**
1. Go to Settings → Environments
2. Verify "production" environment exists
3. Add required reviewers to the environment
4. Ensure "Required reviewers" is enabled
5. Save protection rules

### Local production deployment blocked

**Problem:** Want to deploy to production locally for testing

**Solution:** This is **intentional**. Production deployments must go through GitHub Actions workflow for:
- Proper approval process
- Full audit trail
- Team visibility

Use development environment for testing: `./deploy.sh mvp_site`

---

## Setup Requirements

### GitHub Secrets

- `GCP_SA_KEY` - Google Cloud service account key (JSON format)

### GitHub Environment Protection

1. Go to: Settings → Environments
2. Click "New environment"
3. Name: `production`
4. Check "Required reviewers"
5. Add reviewer(s) by username
6. Save protection rules

### GCP Prerequisites

- Project: `ai-universe-2025`
- Region: `us-central1`
- APIs enabled:
  - Cloud Run API
  - Cloud Build API
  - Artifact Registry API
- Service account with roles:
  - `roles/run.admin`
  - `roles/iam.serviceAccountUser`
  - `roles/storage.admin`

---

## Security

### SHA-Pinned Actions

All workflows use SHA-pinned GitHub Actions for security:
- `actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11` (v4)
- `google-github-actions/auth@55bd3a7c6e2ae7cf1877fd1ccb9d54c0503c457c` (v2)
- `google-github-actions/setup-gcloud@98ddc00a17442e89a24bbf282954a3b65ce6d200` (v2)

This prevents supply chain attacks through compromised action versions.

### Production Protection

- Double confirmation required (text input + environment approval)
- Local deployments completely blocked
- Full audit trail in GitHub Actions
- Designated reviewers must approve
- Clear deployment summaries with timestamps

---

## Additional Documentation

- **Complete deployment guide:** [docs/GITHUB_ACTIONS_AUTO_DEPLOY.md](../../docs/GITHUB_ACTIONS_AUTO_DEPLOY.md)
- **Service account setup:** [docs/GITHUB_ACTIONS_AUTO_DEPLOY.md#service-account-setup](../../docs/GITHUB_ACTIONS_AUTO_DEPLOY.md#service-account-setup)
- **Troubleshooting:** [docs/GITHUB_ACTIONS_AUTO_DEPLOY.md#troubleshooting](../../docs/GITHUB_ACTIONS_AUTO_DEPLOY.md#troubleshooting)

---

**Questions?** Check the documentation or review workflow run logs in the Actions tab.
