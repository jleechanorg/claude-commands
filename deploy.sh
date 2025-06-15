#!/bin/bash
# A script to build the container and deploy it to Cloud Run.

# Ensure we are in the correct directory
cd ~/worldarchitect.ai || exit

echo "Building container image with Cloud Build..."
gcloud builds submit --tag gcr.io/worldarchitecture-ai/webapp-image && \

echo "Deploying image to Cloud Run..."
gcloud run deploy worldarchitecture-webapp \
  --image gcr.io/worldarchitecture-ai/webapp-image \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated

echo "Deployment script finished."
