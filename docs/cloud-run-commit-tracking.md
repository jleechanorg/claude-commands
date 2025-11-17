# Cloud Run Commit SHA Tracking

## Overview

This project implements comprehensive commit SHA tracking for Cloud Run deployments using multiple best practices from Google Cloud documentation. Every deployment is now traceable back to its exact source code commit.

## Implementation Methods

We use **three complementary approaches** for maximum traceability:

### 1. Container Image Tagging (Primary Method)
- **Image tags include commit SHA**: `gcr.io/PROJECT_ID/SERVICE:ENVIRONMENT-COMMIT_SHA`
- **Additional latest tag**: `gcr.io/PROJECT_ID/SERVICE:ENVIRONMENT-latest`
- **Example**: `gcr.io/worldarchitecture-ai/mvp-site-app:dev-a1b2c3d`

### 2. Cloud Run Labels (Metadata Method)
- **Short SHA label**: `commit-sha=a1b2c3d` (7 characters)
- **Full SHA label**: `commit-sha-full=a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0` (40 characters)
- Labels are preserved across revisions and visible in Cloud Run console

### 3. Cloud Build Integration (Automatic)
- Cloud Build automatically captures source information
- Build history shows the commit that triggered each build
- Accessible via `gcloud builds list`

## How It Works

### Local Deployments
When deploying locally via `./deploy.sh`:
```bash
# Automatically detects commit SHA from git
COMMIT_SHA=$(git rev-parse HEAD)
./deploy.sh mvp_site          # Uses local git commit
./deploy.sh mvp_site staging  # Uses local git commit
```

### CI/CD Deployments (GitHub Actions)
When deploying via GitHub Actions:
```bash
# Automatically uses GITHUB_SHA environment variable
# Workflows: auto-deploy-dev.yml, deploy-production.yml
```

### Fallback (No Git Available)
If git is not available, uses timestamp-based identifier:
```bash
# Format: local-YYYYMMDD-HHMMSS
# Example: local-20250114-143022
```

## Viewing Commit SHA Information

### Method 1: Cloud Run Console (Easiest)

1. Go to [Cloud Run Console](https://console.cloud.google.com/run?project=worldarchitecture-ai)
2. Click on your service (e.g., `mvp-site-app-dev`)
3. Navigate to the **"Revisions"** tab
4. Click on any revision to see details
5. Look for:
   - **Image**: Shows the commit SHA in the tag (e.g., `dev-a1b2c3d`)
   - **Labels**: Shows `commit-sha` and `commit-sha-full`

### Method 2: gcloud CLI (Detailed)

**View service labels:**
```bash
gcloud run services describe mvp-site-app-dev \
  --region=us-central1 \
  --project=worldarchitecture-ai \
  --format="yaml(metadata.labels)"
```

**Output example:**
```yaml
metadata:
  labels:
    commit-sha: a1b2c3d
    commit-sha-full: a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0
```

**View revision details with commit info:**
```bash
gcloud run revisions describe REVISION_NAME \
  --region=us-central1 \
  --project=worldarchitecture-ai \
  --format="yaml"
```

### Method 3: Cloud Build History

**List builds with commit information:**
```bash
gcloud builds list \
  --filter="images:gcr.io/worldarchitecture-ai/mvp-site-app" \
  --format="table(id,createTime,status,source.repoSource.commitSha,images)" \
  --limit=10
```

### Method 4: Container Registry (Image Tags)

**List all images with their tags:**
```bash
gcloud container images list-tags gcr.io/worldarchitecture-ai/mvp-site-app \
  --format="table(tags,digest,timestamp)" \
  --limit=20
```

**Output example:**
```
TAGS                      DIGEST        TIMESTAMP
dev-a1b2c3d,dev-latest   sha256:abc... 2025-01-14T14:30:22
stable-a9b8c7d           sha256:def... 2025-01-13T10:15:45
```

## Querying Deployment History

### Find which commit is currently deployed

**For development environment:**
```bash
# Get the current revision
CURRENT_REVISION=$(gcloud run services describe mvp-site-app-dev \
  --region=us-central1 \
  --project=worldarchitecture-ai \
  --format='value(status.latestReadyRevisionName)')

# Get commit SHA from revision labels
gcloud run revisions describe $CURRENT_REVISION \
  --region=us-central1 \
  --project=worldarchitecture-ai \
  --format='value(metadata.labels.commit-sha-full)'
```

**For production environment:**
```bash
# Same as above but for mvp-site-app-stable
CURRENT_REVISION=$(gcloud run services describe mvp-site-app-stable \
  --region=us-central1 \
  --project=worldarchitecture-ai \
  --format='value(status.latestReadyRevisionName)')

gcloud run revisions describe $CURRENT_REVISION \
  --region=us-central1 \
  --project=worldarchitecture-ai \
  --format='value(metadata.labels.commit-sha-full)'
```

### Trace a deployment back to source code

1. **Get the commit SHA** (using methods above)
2. **View the commit in GitHub:**
   ```bash
   # Open in browser
   open "https://github.com/jleechanorg/worldarchitect.ai/commit/<COMMIT_SHA>"
   ```
3. **Check out the exact code locally:**
   ```bash
   git checkout <COMMIT_SHA>
   ```

### Find all deployments for a specific commit

```bash
# Search Cloud Build history
gcloud builds list \
  --filter="source.repoSource.commitSha=<COMMIT_SHA>" \
  --format="table(id,createTime,status,images)"
```

## Troubleshooting

### Labels not showing up?

Check if the deployment completed successfully:
```bash
gcloud run services describe mvp-site-app-dev \
  --region=us-central1 \
  --project=worldarchitecture-ai \
  --format="yaml(status.conditions)"
```

### Image tag doesn't contain commit SHA?

This might be an old deployment before commit SHA tracking was implemented. All new deployments will have commit SHA in the image tag.

### How to rollback to a specific commit?

```bash
# Find the image tag for the commit
gcloud container images list-tags gcr.io/worldarchitecture-ai/mvp-site-app \
  | grep <COMMIT_SHA_SHORT>

# Deploy that specific image
gcloud run deploy mvp-site-app-dev \
  --image=gcr.io/worldarchitecture-ai/mvp-site-app:dev-<COMMIT_SHA_SHORT> \
  --region=us-central1 \
  --project=worldarchitecture-ai
```

## Best Practices

1. **Always deploy from clean git state**: Ensure all changes are committed before deploying
2. **Use CI/CD for production**: Production deployments should always go through GitHub Actions
3. **Check commit SHA after deployment**: Verify the deployment used the expected commit
4. **Keep labels up to date**: Labels are automatically set during deployment
5. **Document deployment decisions**: Use descriptive commit messages

## Benefits

- **Full Traceability**: Know exactly what code is running in each environment
- **Easy Rollbacks**: Quickly identify and rollback to working commits
- **Audit Trail**: Complete history of what was deployed when
- **Debugging**: Match production issues to exact source code
- **Compliance**: Meet requirements for deployment tracking and auditing

## References

- [Cloud Run: Continuous deployment with Cloud Build](https://cloud.google.com/run/docs/continuous-deployment-with-cloud-build)
- [Cloud Run: Managing revisions](https://cloud.google.com/run/docs/managing/revisions)
- [Cloud Run: Deploy from source code](https://cloud.google.com/run/docs/deploying-source-code)
- [Cloud Build: Building containers](https://cloud.google.com/run/docs/building/containers)

## Implementation Files

- `deploy.sh` - Main deployment script with commit SHA capture
- `scripts/deploy_common.sh` - Shared deployment functions
- `.github/workflows/auto-deploy-dev.yml` - Auto-deployment to dev on push to main
- `.github/workflows/deploy-production.yml` - Manual production deployment
- `.github/workflows/deploy-dev.yml` - Reusable dev deployment workflow
