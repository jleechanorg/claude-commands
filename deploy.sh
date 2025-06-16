#!/bin/bash
set -e

# This script deploys an application to Cloud Run.
# It is context-aware and can be run in two ways:
# 1. From the repo root with a directory argument: ./deploy.sh mvp_site
# 2. From inside an application's directory: cd mvp_site; ../deploy.sh

# --- Determine the target directory ---
TARGET_DIR=""
if [ -n "$1" ]; then
    # Case 1: An argument is provided.
    TARGET_DIR="$1"
    echo "Deploying specified directory: '$TARGET_DIR'"
else
    # Case 2: No argument is provided, use the current directory.
    TARGET_DIR="."
    echo "No directory specified. Deploying current directory..."
fi

# --- Validate the target directory ---
if [ ! -f "$TARGET_DIR/Dockerfile" ]; then
    echo "Error: No Dockerfile found in '$TARGET_DIR'. Cannot deploy."
    exit 1
fi

# --- Configuration ---
# Get the absolute path of the target dir and then its base name for the service.
# This handles cases like '.' correctly.
SERVICE_NAME=$(basename $(realpath "$TARGET_DIR"))
# Sanitize the name for Cloud Run (replace _ with -)
SERVICE_NAME=$(echo "$SERVICE_NAME" | tr '_' '-')-app
PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"

echo "--- Preparing to deploy service '$SERVICE_NAME' ---"

# --- Build Step ---
# Use a subshell to temporarily change to the target directory.
# This provides the correct and simplest build context (.) to gcloud builds submit.
echo "Building container image from '$TARGET_DIR'..."
(cd "$TARGET_DIR" && gcloud builds submit . --tag "gcr.io/$PROJECT_ID/$SERVICE_NAME")

# --- Deploy Step ---
echo "Deploying to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
    --image "gcr.io/$PROJECT_ID/$SERVICE_NAME" \
    --platform managed \
    --region "$REGION" \
    --allow-unauthenticated

echo "--- Deployment of '$SERVICE_NAME' complete. ---"
