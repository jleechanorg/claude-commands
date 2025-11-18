#!/usr/bin/env bash
# Grant IAM permissions to GCP service account for PR preview deployments
# This script adds the Service Usage Admin role to enable GCP APIs
# Successfully executed on 2025-11-17 to fix PR #2045 preview deployment permissions

set -euo pipefail

# Configuration
PROJECT_ID="worldarchitecture-ai"
SERVICE_ACCOUNT="dev-runner@worldarchitecture-ai.iam.gserviceaccount.com"
ROLE="roles/serviceusage.serviceUsageAdmin"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== GCP Service Account IAM Permission Grant ===${NC}"
echo ""
echo "Project: ${PROJECT_ID}"
echo "Service Account: ${SERVICE_ACCOUNT}"
echo "Role to Grant: ${ROLE}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ Error: gcloud CLI is not installed${NC}"
    echo ""
    echo "Please install gcloud SDK:"
    echo "  macOS: brew install --cask google-cloud-sdk"
    echo "  Linux: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo -e "${RED}❌ Error: Not authenticated with gcloud${NC}"
    echo ""
    echo "Please authenticate:"
    echo "  gcloud auth login"
    exit 1
fi

# Get current authenticated account
CURRENT_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -1)
echo -e "${BLUE}📋 Authenticated as: ${CURRENT_ACCOUNT}${NC}"
echo ""

# Check if user has permission to grant IAM roles
echo -e "${YELLOW}🔍 Checking permissions...${NC}"
if ! gcloud projects get-iam-policy "${PROJECT_ID}" &> /dev/null; then
    echo -e "${RED}❌ Error: You don't have permission to view IAM policies for project ${PROJECT_ID}${NC}"
    echo ""
    echo "Required role: Project IAM Admin or Owner"
    exit 1
fi

# Grant the IAM role
echo -e "${YELLOW}🔐 Granting Service Usage Admin role...${NC}"
if gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="${ROLE}" \
    --condition=None \
    --quiet; then
    echo -e "${GREEN}✅ Successfully granted ${ROLE}${NC}"
else
    echo -e "${RED}❌ Failed to grant role${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}🔍 Verifying permissions...${NC}"

# Verify the role was granted
if gcloud projects get-iam-policy "${PROJECT_ID}" \
    --flatten="bindings[].members" \
    --filter="bindings.members:serviceAccount:${SERVICE_ACCOUNT}" \
    --format="table(bindings.role)" | grep -q "${ROLE}"; then
    echo -e "${GREEN}✅ Verification successful!${NC}"
    echo ""
    echo -e "${BLUE}Current roles for ${SERVICE_ACCOUNT}:${NC}"
    gcloud projects get-iam-policy "${PROJECT_ID}" \
        --flatten="bindings[].members" \
        --filter="bindings.members:serviceAccount:${SERVICE_ACCOUNT}" \
        --format="table(bindings.role)"
else
    echo -e "${RED}❌ Verification failed - role not found${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}=== Done! ===${NC}"
echo ""
echo "The service account can now enable the following APIs:"
echo "  • run.googleapis.com (Cloud Run)"
echo "  • cloudbuild.googleapis.com (Cloud Build)"
echo "  • artifactregistry.googleapis.com (Artifact Registry)"
echo ""
echo "Next steps:"
echo "  1. Re-run the failed GitHub Actions workflow"
echo "  2. Or push a new commit to trigger the workflow"
echo ""
