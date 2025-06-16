#!/bin/bash
# A smart deploy script.
# Deploys the current directory if it contains a Dockerfile.
# Otherwise, it prompts for a choice from all found projects.

TARGET_DIR=""

# Check for a Dockerfile in the current directory first.
if [ -f "Dockerfile" ]; then
    echo "==> Dockerfile found. Defaulting to current directory."
    TARGET_DIR="."
else
    # If no Dockerfile here, find all potential projects.
    echo "==> No Dockerfile here. Searching for deployable apps..."
    PROJECTS=($(find . -maxdepth 2 -name "Dockerfile" -exec dirname {} \; | sort))

    if [ ${#PROJECTS[@]} -eq 0 ]; then
        echo "ERROR: No projects with a Dockerfile found in this repository."
        exit 1
    fi

    echo "Please choose a project to deploy:"
    select PROJECT_CHOICE in "${PROJECTS[@]}"; do
        if [ -n "$PROJECT_CHOICE" ]; then
            TARGET_DIR="$PROJECT_CHOICE"
            break
        else
            echo "Invalid selection. Please try again."
        fi
    done
fi

echo ""
echo ">>> Building container image from directory '$TARGET_DIR'..."
gcloud builds submit "$TARGET_DIR" --tag gcr.io/worldarchitecture-ai/webapp-image && \

echo ""
echo ">>> Deploying image to Cloud Run..."
gcloud run deploy worldarchitecture-webapp \
  --image gcr.io/worldarchitecture-ai/webapp-image \
  --platform managed \
  --region us-central1 \
  --memory=1Gi \
  --set-secrets=GEMINI_API_KEY=gemini-api-key:latest \
  --allow-unauthenticated

echo "Deployment script finished."
