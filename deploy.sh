#!/bin/bash
set -e

# --- Argument Parsing ---
if [ -z "$1" ]; then
    echo "Usage: ./deploy.sh <directory> [environment]"
    echo "  <directory>: The directory of the app to deploy (e.g., mvp_site)."
    echo "  [environment]: Optional. 'stable' for production. Defaults to 'dev'."
    exit 1
fi

TARGET_DIR="$1"
# --- THIS IS THE NEW LOGIC ---
# If the second argument ($2) is not provided, use "dev" as the default.
ENVIRONMENT="${2:-dev}" 

echo "--- Deployment Details ---"
echo "Target Directory: $TARGET_DIR"
echo "Environment:      $ENVIRONMENT"
echo "--------------------------"


if [ ! -f "$TARGET_DIR/Dockerfile" ]; then
    echo "Error: No Dockerfile found in '$TARGET_DIR'."
    exit 1
fi

# --- Configuration ---
BASE_SERVICE_NAME=$(basename $(realpath "$TARGET_DIR") | tr '_' '-')-app
SERVICE_NAME="$BASE_SERVICE_NAME-$ENVIRONMENT"
PROJECT_ID=$(gcloud config get-value project)

echo "--- Preparing to deploy service '$SERVICE_NAME' to project '$PROJECT_ID' ---"

# --- Build Step ---
IMAGE_TAG="gcr.io/$PROJECT_ID/$BASE_SERVICE_NAME:$ENVIRONMENT-latest"
echo "Building container image from '$TARGET_DIR' with tag '$IMAGE_TAG'..."
# Note: I'm keeping the --no-cache flag for now to ensure we resolve the 503 error.
# We can remove it later for faster builds once the app is stable.
(cd "$TARGET_DIR" && gcloud builds submit . --tag "$IMAGE_TAG" --no-cache)

# --- Deploy Step ---
echo "Deploying to Cloud Run as service '$SERVICE_NAME'..."
gcloud run deploy "$SERVICE_NAME" \
    --image "$IMAGE_TAG" \
    --platform managed \
    --allow-unauthenticated \
    --set-secrets="GEMINI_API_KEY=gemini-api-key:latest"

echo "--- Deployment of '$SERVICE_NAME' complete. ---"
gcloud run services describe "$SERVICE_NAME" --platform managed --format 'value(status.url)'
