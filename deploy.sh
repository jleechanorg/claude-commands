#!/bin/bash
# A script to build the container and deploy it to Cloud Run.

cd ~/worldarchitect.ai || exit

echo "Building container image with Cloud Build..."
gcloud builds submit --tag gcr.io/worldarchitecture-ai/webapp-image && \

echo "Deploying image to Cloud Run with Gemini API key..."
gcloud run deploy worldarchitecture-webapp \
  --image gcr.io/worldarchitecture-ai/webapp-image \
  --platform managed \
  --region us-central1 \
  --set-secrets=GEMINI_API_KEY=gemini-api-key:latest \
  --allow-unauthenticated

echo "Deployment script finished."
