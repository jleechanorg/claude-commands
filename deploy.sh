#!/bin/bash
set -e

# This script deploys a subdirectory to Cloud Run.
# It must be run from the repository root.
# Usage: ./deploy.sh <directory-name>
# Example: ./deploy.sh mvp_site

# --- Configuration ---
REGION="us-central1"
PROJECT_ID=$(gcloud config get-value project)

# --- Input Validation ---
if [ -z "$1" ]; then
    echo "Error: No directory specified."
    echo "Usage: -bash <directory-name>"
    exit 1
fi

DEPLOY_DIR=$1
# FIX: Sanitize the directory name by replacing underscores with dashes for the service name.
SERVICE_NAME=$(basename "$DEPLOY_DIR" | tr '_' '-')-app

if [ ! -d "$DEPLOY_DIR" ]; then
    echo "Error: Directory '$DEPLOY_DIR' does not exist."
    exit 1
fi

if [ ! -f "$DEPLOY_DIR/Dockerfile" ]; then
    echo "Error: No Dockerfile found in '$DEPLOY_DIR'."
    exit 1
fi

echo "--- Preparing to deploy '' from directory '' ---"

# --- Build Step ---
echo "Building container image from '$DEPLOY_DIR'..."
(cd "$DEPLOY_DIR" && gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME)

# --- Deploy Step ---
echo "Deploying '' to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated

echo "--- Deployment of '' complete. ---"
