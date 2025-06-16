#!/bin/bash
TARGET_DIR=$1
if [ -z "$TARGET_DIR" ]; then
  echo "ERROR: Please provide the target directory to deploy."
  echo "Usage: ./deploy.sh <directory>"
  exit 1
fi
echo "Building container image from directory '$TARGET_DIR'..."
gcloud builds submit "$TARGET_DIR" --tag gcr.io/worldarchitecture-ai/webapp-image && \
echo "Deploying image to Cloud Run with Gemini API key..."
gcloud run deploy worldarchitecture-webapp \
  --image gcr.io/worldarchitecture-ai/webapp-image \
  --platform managed \
  --region us-central1 \
  --memory=1Gi \
  --set-secrets=GEMINI_API_KEY=gemini-api-key:latest \
  --allow-unauthenticated
echo "Deployment script finished."
