#!/bin/bash
set -e

# This script deploys a subdirectory to Cloud Run.
# It can be run from the repository root with an argument, or from within an app directory.
# Usage: ./deploy.sh <directory-name> OR (from an app dir) ./deploy.sh

# --- Configuration ---
REGION="us-central1"
PROJECT_ID=$(gcloud config get-value project)

# --- Context-Aware Logic ---
if [ -n "$1" ]; then
    # If an argument is provided, use it as the deploy directory.
    DEPLOY_DIR="$1"
    BUILD_CONTEXT="$1"
    echo "Deploying specified directory: $DEPLOY_DIR"
else
    # If no argument, check for a Dockerfile in the current directory.
    if [ ! -f "Dockerfile" ]; then
        echo "Error: No directory specified and no Dockerfile found in current directory."
        echo "Usage: -bash <directory-name> OR run this script from a directory with a Dockerfile."
        exit 1
    fi
    DEPLOY_DIR=$(basename "$PWD")
    BUILD_CONTEXT="." # Build from the current directory
    echo "No directory specified. Deploying current directory: $DEPLOY_DIR"
fi

SERVICE_NAME=$(echo "$DEPLOY_DIR" | tr '_' '-')-app

if [ ! -d "$DEPLOY_DIR" ] && [ "$BUILD_CONTEXT" != "." ]; then
    echo "Error: Directory '$DEPLOY_DIR' does not exist."
    exit 1
fi

if [ ! -f "$DEPLOY_DIR/Dockerfile" ]; then
    echo "Error: No Dockerfile found in '$DEPLOY_DIR'."
    exit 1
fi

echo "--- Preparing to deploy service '' from context '' ---"

# --- Build Step ---
echo "Building container image..."
gcloud builds submit "$BUILD_CONTEXT" --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

# --- Deploy Step ---
echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated

echo "--- Deployment of '' complete. ---"
