#!/bin/bash
set -e

# --- Argument Parsing & Directory Logic ---
TARGET_DIR=""
ENVIRONMENT="dev" # Default environment

# --- THIS IS THE NEW CONTEXT-AWARE LOGIC ---
# First, check if the CURRENT directory has a Dockerfile.
if [ -f "./Dockerfile" ]; then
    # If so, we've found our target.
    TARGET_DIR="."
    # Check if an argument was provided, and if so, assume it's the environment.
    if [[ "$1" == "stable" ]]; then
        ENVIRONMENT="stable"
    fi
else
    # The current directory is not a deployable app.
    # Check if the first argument is a valid directory.
    if [ -d "$1" ]; then
        TARGET_DIR="$1"
        # Check if the second argument is the environment.
        if [[ "$2" == "stable" ]]; then
            ENVIRONMENT="stable"
        fi
    fi
fi

# If TARGET_DIR is still empty after all checks, show the interactive menu.
if [ -z "$TARGET_DIR" ]; then
    echo "No app auto-detected. Please choose an app to deploy:"
    apps=($(find . -maxdepth 2 -type f -name "Dockerfile" -printf "%h\n" | sed 's|./||' | sort))
    if [ ${#apps[@]} -eq 0 ]; then
        echo "No apps with a Dockerfile found."
        exit 1
    fi
    select app in "${apps[@]}"; do
        if [[ -n $app ]]; then
            TARGET_DIR=$app
            # After selection, check if an argument was passed for the environment
            if [[ "$1" == "stable" ]]; then
                ENVIRONMENT="stable"
            fi
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

# Copy world directory into mvp_site for deployment
echo "DEBUG: TARGET_DIR = '$TARGET_DIR'"
echo "DEBUG: Current directory = $(pwd)"

# Check for world directory in current dir or parent dir
WORLD_DIR=""
if [ -d "world" ]; then
    WORLD_DIR="world"
    echo "DEBUG: Found world directory in current directory"
elif [ -d "../world" ]; then
    WORLD_DIR="../world"
    echo "DEBUG: Found world directory in parent directory"
else
    echo "DEBUG: No world directory found"
fi

# Handle different possible values of TARGET_DIR
if [[ "$TARGET_DIR" == *"mvp_site"* ]] && [ -n "$WORLD_DIR" ]; then
    echo "Copying world directory into mvp_site..."
    cp -r "$WORLD_DIR" "$TARGET_DIR/"
    echo "DEBUG: World files copied from $WORLD_DIR to $TARGET_DIR/world"
    ls -la "$TARGET_DIR/world/" | head -5
elif [[ "$TARGET_DIR" == *"mvp_site"* ]] && [ -z "$WORLD_DIR" ]; then
    echo "WARNING: No world directory found to copy!"
    echo "Deployment may fail if world files are required."
fi

(cd "$TARGET_DIR" && gcloud builds submit . --tag "$IMAGE_TAG")

# --- Deploy Step ---
echo "Deploying to Cloud Run as service '$SERVICE_NAME'..."
gcloud run deploy "$SERVICE_NAME" \
    --image "$IMAGE_TAG" \
    --platform managed \
    --allow-unauthenticated \
    --set-secrets="GEMINI_API_KEY=gemini-api-key:latest" \
    --memory=2Gi \
    --timeout=300

echo "--- Deployment of '$SERVICE_NAME' complete. ---"
gcloud run services describe "$SERVICE_NAME" --platform managed --format 'value(status.url)'
