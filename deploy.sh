#!/bin/bash
# A script to build the container from the CURRENT directory and deploy it.

echo "Building container image from current directory..."
# Use "." as the source for the build
gcloud builds submit . --tag gcr.io/worldarchitecture-ai/webapp-image && \

echo "Deploying image to Cloud Run with Gemini API key..."
gcloud run deploy worldarchitecture-webapp \
  --image gcr.io/worldarchitecture-ai/webapp-image \
  --platform managed \
  --region us-central1 \
  --memory=1Gi \
  --set-secrets=GEMINI_API_KEY=gemini-api-key:latest \
  --allow-unauthenticated

echo "Deployment script finished."
