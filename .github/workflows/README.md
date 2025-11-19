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

## Email Notifications for Deployments

### Overview

This project uses a **centralized email notification system** that sends deployment status emails (success ✅ or failure ❌) after every deployment. This section provides a complete, copy-paste guide for implementing this in any repository.

### Architecture

```
GitHub Actions Workflow
    ↓
Deploy Step (success/failure)
    ↓
Composite Action: send-deploy-notification
    ↓
dawidd6/action-send-mail (v6)
    ↓
SMTP Server (Gmail)
    ↓
Email Delivered
```

### Key Features

- ✅ **Centralized**: Single reusable composite action for all deployments
- ✅ **DRY Principle**: No code duplication across workflows
- ✅ **Smart Formatting**: Automatic success ✅ / failure ❌ detection
- ✅ **Rich Content**: Deployment URL, health check, console links, logs
- ✅ **Non-blocking**: `continue-on-error: true` ensures deployment isn't blocked by email failures
- ✅ **Security**: SHA-pinned actions, uses GitHub Secrets for credentials

---

## Complete Implementation Guide

### Step 1: Create the Composite Action

Create `.github/actions/send-deploy-notification/action.yml`:

```yaml
# Centralized Email Notification Action for Deployments
# This composite action sends email notifications for deployment success or failure
#
# Usage:
#   - name: Send deployment notification
#     uses: ./.github/actions/send-deploy-notification
#     with:
#       status: success  # or failure
#       environment: dev
#       service_name: mvp-site-app-dev
#       region: us-central1
#       project: worldarchitecture-ai
#       branch: main
#       commit_sha: ${{ github.sha }}
#       deployment_url: https://example.com
#       workflow_url: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}
#       email_user: ${{ secrets.EMAIL_USER }}
#       email_password: ${{ secrets.EMAIL_APP_PASSWORD }}

name: 'Send Deployment Email Notification'
description: 'Sends email notifications for deployment success or failure'

inputs:
  status:
    description: 'Deployment status (success or failure)'
    required: true
  environment:
    description: 'Deployment environment (dev, production, etc.)'
    required: true
  service_name:
    description: 'Name of the deployed service'
    required: true
  region:
    description: 'GCP region'
    required: false
    default: 'us-central1'
  project:
    description: 'GCP project ID'
    required: false
    default: 'worldarchitecture-ai'
  branch:
    description: 'Git branch name'
    required: true
  commit_sha:
    description: 'Git commit SHA'
    required: true
  deployment_url:
    description: 'URL of the deployed service'
    required: false
    default: ''
  workflow_url:
    description: 'URL of the GitHub Actions workflow run'
    required: true
  email_user:
    description: 'Email username (for SMTP authentication and recipient)'
    required: true
  email_password:
    description: 'Email password or app password'
    required: true

runs:
  using: 'composite'
  steps:
    - name: Send email notification
      continue-on-error: true
      uses: dawidd6/action-send-mail@6d98ae34d733f9a723a9e04e94f2f24ba05e1402  # v6
      with:
        server_address: smtp.gmail.com
        server_port: 587
        username: ${{ inputs.email_user }}
        password: ${{ inputs.email_password }}
        subject: >-
          ${{ inputs.status == 'success' && '✅ SUCCESS' || '❌ FAILED' }}:
          ${{ inputs.environment }} Deployment - ${{ inputs.service_name }}
        to: ${{ inputs.email_user }}
        from: WorldArchitect.AI Deploy Bot <${{ inputs.email_user }}>
        body: |
          ${{ inputs.status == 'success' && '✅' || '🚨' }} ${{ inputs.environment }} Deployment ${{ inputs.status == 'success' && 'Successful' || 'Failed' }}

          Environment: ${{ inputs.environment }}
          Service: ${{ inputs.service_name }}
          ${{ inputs.region && format('Region: {0}', inputs.region) || '' }}
          ${{ inputs.project && format('Project: {0}', inputs.project) || '' }}
          Branch: ${{ inputs.branch }}
          Commit: ${{ inputs.commit_sha }}

          Status: ${{ inputs.status == 'success' && 'SUCCESS ✅' || 'FAILED ❌' }}

          ${{ inputs.deployment_url && format('Deployment URL: {0}', inputs.deployment_url) || '' }}
          ${{ inputs.deployment_url && format('Health Check: {0}/health', inputs.deployment_url) || '' }}

          ${{ inputs.region && inputs.project && inputs.service_name && format('Console: https://console.cloud.google.com/run/detail/{0}/{1}?project={2}', inputs.region, inputs.service_name, inputs.project) || '' }}
          ${{ inputs.project && inputs.service_name && format('Logs: https://console.cloud.google.com/logs/query?project={0}&query=resource.type%3D%22cloud_run_revision%22%0Aresource.labels.service_name%3D%22{1}%22', inputs.project, inputs.service_name) || '' }}

          Workflow: ${{ inputs.workflow_url }}

          ${{ inputs.status == 'failure' && format('Please check the workflow logs for details: {0}', inputs.workflow_url) || '' }}
```

**Key Points:**
- **SHA-pinned action**: `dawidd6/action-send-mail@6d98ae34d733f9a723a9e04e94f2f24ba05e1402` (v6)
- **Non-blocking**: `continue-on-error: true` prevents email failures from blocking deployments
- **Smart formatting**: Conditional logic for success ✅ / failure ❌ content
- **Rich metadata**: Includes deployment URL, health check, console links, logs

---

### Step 2: Configure GitHub Secrets

Add these secrets to your repository (Settings → Secrets and variables → Actions → New repository secret):

#### EMAIL_USER
- **Description**: Gmail email address for sending notifications
- **Example**: `your-email@gmail.com`
- **Value**: Your Gmail email address

#### EMAIL_APP_PASSWORD
- **Description**: Gmail App Password (NOT your regular Gmail password)
- **How to generate**:
  1. Go to: https://myaccount.google.com/apppasswords
  2. Sign in to your Google Account
  3. Click "Select app" → Choose "Mail"
  4. Click "Select device" → Choose "Other (Custom name)"
  5. Enter name: `GitHub Actions Deploy Bot`
  6. Click "Generate"
  7. Copy the 16-character app password (format: `xxxx xxxx xxxx xxxx`)
  8. Add as GitHub secret (remove spaces: `xxxxxxxxxxxxxxxx`)

**Security Notes:**
- ✅ Use Gmail App Passwords, not your actual Gmail password
- ✅ Store in GitHub Secrets, never commit to code
- ✅ App passwords can be revoked individually at any time
- ✅ Requires 2FA enabled on your Google Account

---

### Step 3: Integrate into Deployment Workflows

Add notification steps to your deployment workflows. Example for a deployment workflow:

```yaml
name: Deploy to Development

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11  # v4

      # ... your deployment steps here ...

      - name: Get deployment URL
        id: get-url
        run: |
          # Get your deployed service URL
          URL="https://your-service.run.app"
          echo "url=$URL" >> $GITHUB_OUTPUT

      # Send notification on FAILURE
      - name: Send failure email notification
        if: failure()
        uses: ./.github/actions/send-deploy-notification
        with:
          status: failure
          environment: dev
          service_name: your-service-name
          region: us-central1
          project: your-gcp-project
          branch: ${{ github.ref_name }}
          commit_sha: ${{ github.sha }}
          deployment_url: ${{ steps.get-url.outputs.url }}
          workflow_url: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}
          email_user: ${{ secrets.EMAIL_USER }}
          email_password: ${{ secrets.EMAIL_APP_PASSWORD }}

      # Send notification on SUCCESS
      - name: Send success email notification
        if: success()
        uses: ./.github/actions/send-deploy-notification
        with:
          status: success
          environment: dev
          service_name: your-service-name
          region: us-central1
          project: your-gcp-project
          branch: ${{ github.ref_name }}
          commit_sha: ${{ github.sha }}
          deployment_url: ${{ steps.get-url.outputs.url }}
          workflow_url: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}
          email_user: ${{ secrets.EMAIL_USER }}
          email_password: ${{ secrets.EMAIL_APP_PASSWORD }}
```

**Key Integration Points:**
- `if: failure()` - Sends email only when any previous step fails
- `if: success()` - Sends email only when all previous steps succeed
- `deployment_url` - Pass the actual deployed service URL from a previous step
- `workflow_url` - Auto-generated link to the GitHub Actions run

**Customization Options:**
- Change `environment` to match your environment (dev, staging, production)
- Update `service_name`, `region`, `project` to match your infrastructure
- Modify email subject/body in the composite action

---

### Step 4: Test the Email Integration

Create a test workflow to validate email configuration:

Create `.github/workflows/test-email-notification.yml`:

```yaml
name: Test Email Notification

on:
  workflow_dispatch:
    inputs:
      notification_type:
        description: 'Type of notification to test'
        required: true
        default: 'success'
        type: choice
        options:
          - success
          - failure

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11  # v4

      - name: Simulate deployment
        run: |
          echo "Testing email notification with status: ${{ inputs.notification_type }}"
          if [ "${{ inputs.notification_type }}" == "failure" ]; then
            exit 1
          fi

      - name: Send failure notification
        if: failure()
        uses: ./.github/actions/send-deploy-notification
        with:
          status: failure
          environment: test
          service_name: test-service
          region: us-central1
          project: your-project
          branch: main
          commit_sha: ${{ github.sha }}
          deployment_url: https://test.example.com
          workflow_url: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}
          email_user: ${{ secrets.EMAIL_USER }}
          email_password: ${{ secrets.EMAIL_APP_PASSWORD }}

      - name: Send success notification
        if: success()
        uses: ./.github/actions/send-deploy-notification
        with:
          status: success
          environment: test
          service_name: test-service
          region: us-central1
          project: your-project
          branch: main
          commit_sha: ${{ github.sha }}
          deployment_url: https://test.example.com
          workflow_url: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}
          email_user: ${{ secrets.EMAIL_USER }}
          email_password: ${{ secrets.EMAIL_APP_PASSWORD }}
```

**How to test:**
1. Go to Actions → Test Email Notification → Run workflow
2. Select "success" or "failure" to test both scenarios
3. Check your email inbox for the notification
4. Verify all links work correctly

---

### Email Templates

#### Success Email Example

```
Subject: ✅ SUCCESS: dev Deployment - mvp-site-app-dev

✅ dev Deployment Successful

Environment: dev
Service: mvp-site-app-dev
Region: us-central1
Project: worldarchitecture-ai
Branch: main
Commit: abc123def456

Status: SUCCESS ✅

Deployment URL: https://mvp-site-app-dev-xyz.run.app
Health Check: https://mvp-site-app-dev-xyz.run.app/health

Console: https://console.cloud.google.com/run/detail/us-central1/mvp-site-app-dev?project=worldarchitecture-ai
Logs: https://console.cloud.google.com/logs/query?project=worldarchitecture-ai&query=...

Workflow: https://github.com/yourorg/yourrepo/actions/runs/123456789
```

#### Failure Email Example

```
Subject: ❌ FAILED: production Deployment - mvp-site-app-stable

🚨 production Deployment Failed

Environment: production
Service: mvp-site-app-stable
Region: us-central1
Project: worldarchitecture-ai
Branch: main
Commit: abc123def456

Status: FAILED ❌

Workflow: https://github.com/yourorg/yourrepo/actions/runs/123456789

Please check the workflow logs for details: https://github.com/yourorg/yourrepo/actions/runs/123456789
```

---

### Troubleshooting

#### Email not received

**Solutions:**
1. Check spam/junk folder
2. Verify `EMAIL_USER` secret is set correctly
3. Verify `EMAIL_APP_PASSWORD` is correct (16 characters, no spaces)
4. Check workflow logs for SMTP errors
5. Ensure 2FA is enabled on Google Account

#### Authentication error (SMTP 535)

**Problem:** `535 Authentication failed`

**Solutions:**
1. Regenerate Gmail App Password
2. Verify no spaces in app password when adding to GitHub Secrets
3. Check that 2FA is enabled on your Google Account
4. Use App Password, not regular Gmail password

#### Email sends but links don't work

**Solutions:**
1. Verify `deployment_url` is captured correctly in previous step
2. Check `region`, `project`, `service_name` match your actual infrastructure
3. Ensure GCP console links use correct project ID

#### Email notification blocks deployment

**Problem:** Deployment fails when email can't be sent

**Solution:** Ensure `continue-on-error: true` is set in composite action:
```yaml
- name: Send email notification
  continue-on-error: true  # <-- This line is critical
  uses: dawidd6/action-send-mail@...
```

---

### Customization Guide

#### Use Different SMTP Provider

Replace Gmail SMTP with your provider:

```yaml
# For SendGrid
server_address: smtp.sendgrid.net
server_port: 587
username: apikey
password: ${{ inputs.email_password }}  # SendGrid API key

# For AWS SES
server_address: email-smtp.us-east-1.amazonaws.com
server_port: 587
username: ${{ inputs.email_user }}  # SMTP credentials
password: ${{ inputs.email_password }}

# For Mailgun
server_address: smtp.mailgun.org
server_port: 587
```

#### Add Multiple Recipients

Modify the composite action:

```yaml
to: ${{ inputs.email_user }}, team@example.com, devops@example.com
cc: manager@example.com
```

#### Customize Email Subject

In composite action, modify:

```yaml
subject: >-
  [${{ inputs.environment }}] ${{ inputs.status == 'success' && '✅' || '❌' }}
  ${{ inputs.service_name }} deployed from ${{ inputs.branch }}
```

#### Add Custom Metadata

Add inputs to composite action:

```yaml
inputs:
  deployer:
    description: 'Who triggered the deployment'
    required: false
    default: 'GitHub Actions'
```

Then use in body:

```yaml
body: |
  Deployed by: ${{ inputs.deployer }}
  ...
```

---

### Files Checklist

To implement this in another repository, create these files:

- [ ] `.github/actions/send-deploy-notification/action.yml` - Composite action
- [ ] `.github/workflows/test-email-notification.yml` - Test workflow (optional)
- [ ] GitHub Secrets: `EMAIL_USER`, `EMAIL_APP_PASSWORD`
- [ ] Update your deployment workflows to call the notification action

---

### Benefits

- ✅ **Instant notification**: Know immediately when deployments succeed or fail
- ✅ **Zero maintenance**: Once set up, runs automatically forever
- ✅ **Non-blocking**: Email failures don't block deployments
- ✅ **Rich context**: All important links in one email
- ✅ **Audit trail**: Email archive serves as deployment history
- ✅ **DRY principle**: Single source of truth, easy to update

---

### Real-World Usage

This implementation is currently used in:
- `deploy-dev.yml` - Automatic dev deployments on push to main
- `deploy-production.yml` - Manual production deployments with approval

Every deployment (successful or failed) sends an email with complete context.

---

## Additional Documentation

- **Complete deployment guide:** [docs/GITHUB_ACTIONS_AUTO_DEPLOY.md](../../docs/GITHUB_ACTIONS_AUTO_DEPLOY.md)
- **Service account setup:** [docs/GITHUB_ACTIONS_AUTO_DEPLOY.md#service-account-setup](../../docs/GITHUB_ACTIONS_AUTO_DEPLOY.md#service-account-setup)
- **Troubleshooting:** [docs/GITHUB_ACTIONS_AUTO_DEPLOY.md#troubleshooting](../../docs/GITHUB_ACTIONS_AUTO_DEPLOY.md#troubleshooting)

---

**Questions?** Check the documentation or review workflow run logs in the Actions tab.
