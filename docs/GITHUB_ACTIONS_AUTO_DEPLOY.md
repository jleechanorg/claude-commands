# GitHub Actions Auto-Deployment

*Last updated: 2025-11-02*

This repository uses GitHub Actions to automatically deploy to Google Cloud Run when changes are pushed to specific branches.

**See also:**
- Development workflow definition: [`.github/workflows/auto-deploy-dev.yml`](../.github/workflows/auto-deploy-dev.yml)
- Production workflow definition: [`.github/workflows/deploy-production.yml`](../.github/workflows/deploy-production.yml)

## How It Works

The auto-deployment workflow is triggered on pushes to the `main` branch and automatically deploys the `mvp_site` application to the development environment.

### Branch Mapping

- **main** → auto-deploys to **dev** environment (`mvp-site-app-dev`)
- **Manual workflow** → deploys to **production** environment (`mvp-site-app-stable`) with approval

*Note: Production requires manual trigger and approval through GitHub Actions.*

## Workflow Overview

The workflow performs the following steps:

1. **Authenticate to GCP** - Uses the `GCP_SA_KEY` secret for service account authentication
2. **Deploy** - Runs `./deploy.sh mvp_site` to deploy the application
3. **Health Check** - Verifies the deployment by checking the `/health` endpoint (10 retries with 5s intervals)
   - *Note: The application implements a `/health` endpoint that returns HTTP 200*
4. **Summary** - Displays deployment details in the GitHub Actions UI

## Configuration

The workflow uses the following configuration:

- **GCP Project:** `ai-universe-2025`
- **Region:** `us-central1`
- **Timeout:** 45 minutes total (30 minutes for the deployment step)

### Environment-Specific Services

| Environment | Trigger | Cloud Run Service | Deploy Command | Approval |
|-------------|---------|-------------------|----------------|----------|
| dev | Push to main | mvp-site-app-dev | ./deploy.sh mvp_site | None |
| production | Manual workflow | mvp-site-app-stable | GitHub Actions only | **Required** |

*Note: Staging environment can be added by creating additional workflow files if needed.*

## Prerequisites

The following prerequisites should already be in place for this project.

### Application Requirements

- The application exposes a **`GET /health`** endpoint that returns HTTP 200. The workflow uses this endpoint to verify the deployment.

### Service Account and Secrets

- **GCP_SA_KEY** - Google Cloud service account key (JSON format). This secret must be configured in the repository settings.
- The service account must have the following IAM roles in the `ai-universe-2025` project:
  - `roles/run.admin` - Deploy and manage Cloud Run services
  - `roles/iam.serviceAccountUser` - Act as the Cloud Run runtime service account
  - `roles/storage.admin` - Push images to Container/Artifact Registry

### One-Time GCP Setup

These APIs should be enabled in the GCP project (one-time setup):

```bash
gcloud services enable run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  --project=ai-universe-2025
```

The workflow assumes these APIs are already enabled.

### Service Account Setup

If not already configured, create and configure the deployment service account:

**Note:** The service account can have any name (e.g., `github-deployer`, `github-actions`, `ci-deployer`). The important requirement is that the service account JSON key is stored in the `GCP_SA_KEY` GitHub secret.

```bash
# 1. Create service account (you can use any name instead of "github-deployer")
gcloud iam service-accounts create github-deployer \
  --project=ai-universe-2025

# 2. Grant required roles
gcloud projects add-iam-policy-binding ai-universe-2025 \
  --member="serviceAccount:github-deployer@ai-universe-2025.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding ai-universe-2025 \
  --member="serviceAccount:github-deployer@ai-universe-2025.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding ai-universe-2025 \
  --member="serviceAccount:github-deployer@ai-universe-2025.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

# 3. Create and download key
gcloud iam service-accounts keys create ~/github-deployer-key.json \
  --iam-account=github-deployer@ai-universe-2025.iam.gserviceaccount.com

# 4. Add to GitHub
# Go to: Settings → Secrets and variables → Actions → New repository secret
# Name: GCP_SA_KEY
# Value: (paste entire contents of github-deployer-key.json)
```

## Monitoring

After a deployment completes, the workflow provides quick links to:

- **Service Health** - Direct link to the `/health` endpoint
- **Cloud Run Console** - View service details, revisions, and metrics
- **Logs** - Query logs for the deployed service

These links are displayed in the GitHub Actions workflow summary.

## Deployment URLs

Development environment URL pattern: `https://mvp-site-app-dev-<hash>-uc.a.run.app`

Production environment URL pattern: `https://mvp-site-app-stable-<hash>-uc.a.run.app`

`<hash>` is the Cloud Run-managed revision hash (changes on each deploy). The workflow prints the exact URL in the deployment summary for quick access.

## Troubleshooting

### Deployment Times Out

The workflow has generous timeouts (45min job, 30min deploy step) to accommodate Cloud Build times. If deployments consistently timeout:

1. Check Cloud Build logs in GCP Console
2. Verify the Docker build completes successfully
3. Ensure the deployment script (`./deploy.sh`) is working correctly

### Health Check Fails

If the health check fails after deployment:

1. Verify the `/health` endpoint is implemented and returns HTTP 200
2. Check the Cloud Run logs for startup errors
3. Ensure all required environment variables and secrets are configured
4. Verify the service has sufficient memory/CPU resources (currently configured: 2Gi memory)

### Authentication Errors

If the workflow fails to authenticate to GCP:

1. Verify the `GCP_SA_KEY` secret is configured in GitHub repository settings
2. Ensure the service account has the required IAM roles
3. Check that the service account key is valid and hasn't expired

### Failed to Retrieve Deployment URL

If the workflow fails to retrieve the deployment URL:

1. Check that the service name matches the expected pattern (`mvp-site-app-dev`)
2. Verify the service was deployed successfully in the Cloud Run Console
3. Ensure the region (`us-central1`) is correct

## Local Testing

Before relying on auto-deployment, test the deployment script locally:

```bash
# From project root - deploys to dev environment (default)
./deploy.sh mvp_site

# For production/stable deployment (deploys with "stable" environment suffix)
# Note: This is for future production workflows, not used by the dev auto-deployment
./deploy.sh mvp_site stable
```

**Environment Parameter:**
- No parameter or `dev` → deploys to `mvp-site-app-dev`
- `stable` → deploys to `mvp-site-app-stable` (for production use)

**Note:** Local production deployments (`./deploy.sh mvp_site stable`) are blocked. See Production Deployment section below.

## Production Deployment

Production deployments require manual approval and must be triggered through GitHub Actions.

### Why Production is Protected

For safety and compliance, production deployments:
- ❌ **Cannot** be run from local machines
- ✅ **Must** use GitHub Actions workflow
- ✅ **Require** manual approval from designated reviewers
- ✅ **Provide** full audit trail of who deployed what and when

### How to Deploy to Production

1. **Go to the workflow:**
   - https://github.com/jleechanorg/worldarchitect.ai/actions/workflows/deploy-production.yml

2. **Click "Run workflow"**

3. **Type confirmation:**
   - Enter exactly: `DEPLOY TO PRODUCTION`
   - This prevents accidental clicks

4. **Click "Run workflow" button**

5. **Wait for approval:**
   - Designated reviewer receives notification
   - Reviewer checks the changes
   - Reviewer approves in GitHub UI (Environments → production)

6. **Deployment proceeds automatically:**
   - Deploys `mvp_site` to `mvp-site-app-stable`
   - Runs health checks (15 retries, 10s intervals)
   - Shows deployment summary with links

### Production Workflow Features

- **Double confirmation:** Text input + environment approval
- **Health checks:** More retries than dev (15 vs 10)
- **Longer timeouts:** 60min job, 40min deploy
- **Audit trail:** Complete history in GitHub Actions
- **Deployment summary:** Shows approver, timestamp, commit SHA

### Setting Up Production Environment Protection

Before first production deployment, configure GitHub environment protection:

1. Go to repository **Settings → Environments**
2. Click **"New environment"**
3. Name: `production`
4. Check **"Required reviewers"**
5. Add reviewer(s) by GitHub username
6. **Save protection rules**

Without this setup, the workflow will fail with "environment not found" error.

### Local Production Deployment Blocked

Attempting to deploy to production locally shows this message:

```
$ ./deploy.sh mvp_site stable

================================================================================
🚨 PRODUCTION DEPLOYMENT BLOCKED 🚨
================================================================================

Production deployments are NOT allowed from local machines for safety.

You must use the GitHub Actions workflow with manual approval:

1. Go to: https://github.com/jleechanorg/worldarchitect.ai/actions/workflows/deploy-production.yml
2. Click "Run workflow"
3. Type "DEPLOY TO PRODUCTION" in the confirmation field
4. Click "Run workflow"
5. Wait for designated reviewer approval
6. Deployment proceeds after approval
...
```

This protection cannot be bypassed locally, ensuring all production deployments go through proper approval.

## Adding Additional Environments

To add auto-deployment for staging or production:

1. Create a new workflow file (e.g., `.github/workflows/auto-deploy-staging.yml`)
2. Update the branch trigger (e.g., `staging` or `production`)
3. Update the environment name and service name
4. Update the deploy command (e.g., `./deploy.sh mvp_site stable`)
5. Update this documentation with the new environment mapping

## Reference Implementation

This auto-deployment setup is based on the proven implementation from:
- **Repository:** ai_universe backend
- **Pull Request:** [#500](https://github.com/jleechanorg/ai_universe/pull/500)

### Key Features

- No runtime API enabling (assumes pre-provisioned environment)
- Generous timeouts to prevent premature cancellation
- URL validation before health checks
- HTTP status code logging for debugging
- Conditional deployment summary (only when URL retrieval succeeds)
- SHA-pinned GitHub Actions for security

## Security

All GitHub Actions in this workflow use SHA-pinned versions for security:
- `actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11` (v4)
- `google-github-actions/auth@55bd3a7c6e2ae7cf1877fd1ccb9d54c0503c457c` (v2)
- `google-github-actions/setup-gcloud@98ddc00a17442e89a24bbf282954a3b65ce6d200` (v2)

This prevents supply chain attacks through compromised action versions.
