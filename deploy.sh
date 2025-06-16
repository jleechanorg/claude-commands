#!/bin/bash
set -e

# --- Argument Parsing & Directory Logic ---
TARGET_DIR=""
ENVIRONMENT="dev" # Default environment

# Intelligent argument parsing
if [ -z "$1" ]; then
    # No arguments: Show menu
    echo "No directory specified. Please choose an app to deploy:"
elif [ -d "$1" ]; then
    # First argument is a directory
    TARGET_DIR="$1"
    # Check if the second argument is the environment
    if [[ "$2" == "stable" ]]; then
        ENVIRONMENT="stable"
    fi
else
    # First argument is NOT a directory, assume it's the environment
    if [[ "$1" == "stable" ]]; then
        ENVIRONMENT="stable"
    fi
    # After checking for environment, show menu because no directory was given
    echo "No directory specified. Please choose an app to deploy:"
fi

# If TARGET_DIR is still empty, run the interactive menu
if [ -z "$TARGET_DIR" ]; then
    apps=($(find . -maxdepth 2 -type f -name "Dockerfile" -printf "%h\n" | sed 's|./||' | sort))
    if [ ${#apps[@]} -eq 0 ]; then
        echo "No apps with a Dockerfile found."
        exit 1
    fi
    select app in "${apps[@]}"; do
        if [[ -n $app ]]; then
            TARGET_DIR=$app
            break
        else
            echo "Invalid selection. Please try again."
        fi
    done
fi

# --- Final Check & Configuration ---
echo "--- Deployment Details ---"
echo "Target Directory: $TARGET_DIR"
echo "Environment:      $ENVIRONMENT"
echo "--------------------------"

if [ ! -f "$TARGET_DIR/Dockerfile" ]; then
    echo "Error: No Dockerfile found in '$TARGET_DIR'."
    exit 1
fi

BASE_SERVICE_NAME=$(basename $(realpath "$TARGET_DIR") | tr '_' '-')-app
SERVICE_NAME="$BASE_SERVICE_NAME-$ENVIRONMENT"
PROJECT_ID=$(gcloud config get-value project)

echo "--- Preparing to deploy service '$SERVICE_NAME' to project '$PROJECT_ID' ---"

# --- Build Step ---
IMAGE_TAG="gcr.io/$PROJECT_ID/$BASE_SERVICE_NAME:$ENVIRONMENT-latest"
echo "Building container image from '$TARGET_DIR' with tag '$IMAGE_TAG'..."
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
