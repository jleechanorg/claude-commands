#!/bin/bash
set -e

# --- Determine the target directory ---
TARGET_DIR=""
if [ -n "$1" ]; then
    TARGET_DIR="$1"
    echo "Deploying specified directory: '$TARGET_DIR'"
else
    TARGET_DIR="."
    echo "No directory specified. Deploying current directory..."
fi

if [ ! -f "$TARGET_DIR/Dockerfile" ]; then
    echo "Error: No Dockerfile found in '$TARGET_DIR'."
    exit 1
fi

# --- Configuration ---
SERVICE_NAME=$(basename $(realpath "$TARGET_DIR") | tr '_' '-')-app
PROJECT_ID=$(gcloud config get-value project)
REGION="$(gcloud config get-value run/region 2>/dev/null || echo 'us-central1')"

echo "--- Preparing to deploy service '$SERVICE_NAME' ---"

# --- Build Step ---
echo "Building container image from '$TARGET_DIR'..."
(cd "$TARGET_DIR" && gcloud builds submit . --tag "gcr.io/$PROJECT_ID/$SERVICE_NAME")

# --- Deploy Step ---
echo "Deploying to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
    --image "gcr.io/$PROJECT_ID/$SERVICE_NAME" \
    --platform managed \
    --region "$REGION" \
    --allow-unauthenticated \
    --set-secrets="GEMINI_API_KEY=gemini-api-key:latest"

echo "--- Deployment of '$SERVICE_NAME' complete. ---"
