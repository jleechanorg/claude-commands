#!/bin/bash
set -euo pipefail

source "$(dirname "$0")/scripts/deploy_common.sh"

# --- Argument Parsing & Directory Logic ---
TARGET_DIR=""
ENVIRONMENT="dev" # Default environment

# --- THIS IS THE NEW CONTEXT-AWARE LOGIC ---
# First, check if the CURRENT directory has a Dockerfile.
if [ -f "./Dockerfile" ]; then
    # If so, we've found our target.
    TARGET_DIR="."
    # Check if an argument was provided, and if so, assume it's the environment.
    if [[ "${1:-}" == "stable" ]]; then
        ENVIRONMENT="stable"
    fi
else
    # The current directory is not a deployable app.
    # Check if the first argument is a valid directory.
    if [ -d "${1:-}" ]; then
        TARGET_DIR="${1:-}"
        # Check if the second argument is the environment.
        if [[ "${2:-}" == "stable" ]]; then
            ENVIRONMENT="stable"
        fi
    fi
fi

# If TARGET_DIR is still empty after all checks, show the interactive menu.
if [ -z "$TARGET_DIR" ]; then
    echo "No app auto-detected. Please choose an app to deploy:"
    apps=()
    while IFS= read -r app_path; do
        apps+=("$app_path")
    done < <(
        python3 - <<'PY'
import pathlib

EXCLUDED_NAMES = {"genesis"}

def should_include(path: pathlib.Path) -> bool:
    """Determine whether the given path should be included in the menu.

    Args:
        path: Relative path to a candidate app directory.

    Returns:
        True when none of the path components match an excluded directory name,
        otherwise False.
    """

    return not any(part in EXCLUDED_NAMES for part in path.parts)

root = pathlib.Path(".").resolve()
apps = set()

for dockerfile in root.glob("Dockerfile"):
    apps.add(".")

for dockerfile in root.glob("*/Dockerfile"):
    relative = dockerfile.parent.relative_to(root)
    if should_include(relative):
        apps.add(str(relative))

for dockerfile in root.glob("*/*/Dockerfile"):
    relative = dockerfile.parent.relative_to(root)
    if should_include(relative):
        apps.add(str(relative))

for app in sorted(apps):
    print(app)
PY
    )
    if [ ${#apps[@]} -eq 0 ]; then
        echo "No apps with a Dockerfile found."
        exit 1
    fi
    select app in "${apps[@]}"; do
        if [[ -n $app ]]; then
            TARGET_DIR=$app
            # After selection, check if an argument was passed for the environment
            if [[ "${1:-}" == "stable" ]]; then
                ENVIRONMENT="stable"
            fi
            break
        else
            echo "Invalid selection. Please try again."
        fi
    done
fi


# --- Production Deployment Protection ---
block_local_production_deployment() {
    # Block local production deployments - must use GitHub Actions workflow
    if [[ "$ENVIRONMENT" == "stable" ]] && [[ "${GITHUB_ACTIONS:-}" != "true" ]]; then
        cat <<'EOF'

================================================================================
🚨 PRODUCTION DEPLOYMENT BLOCKED 🚨
================================================================================

Production deployments are NOT allowed from local machines for safety.

You must use the GitHub Actions workflow with manual approval:

1. Go to: https://github.com/jleechanorg/worldarchitect.ai/actions/workflows/deploy-production.yml
2. Click "Run workflow"
3. Type "DEPLOY TO PRODUCTION" in the confirmation field
4. Click "Run workflow"
5. Wait for designated reviewer approval
6. Deployment proceeds after approval

This ensures:
✅ Proper approval process
✅ Full audit trail
✅ Prevents accidental production deployments
✅ Team visibility of production changes

For development/staging deployments, use:
  ./deploy.sh mvp_site       (deploys to dev)

================================================================================
EOF
        exit 1
    fi
}

# --- Final Check & Configuration ---
echo "--- Deployment Details ---"
echo "Target Directory: $TARGET_DIR"
echo "Environment:      $ENVIRONMENT"
echo "--------------------------"

# Check for production deployment protection
block_local_production_deployment

if [ ! -f "$TARGET_DIR/Dockerfile" ]; then
    echo "Error: No Dockerfile found in '$TARGET_DIR'."
    exit 1
fi

TARGET_REALPATH=$(python3 -c "import os, sys; print(os.path.realpath(sys.argv[1]))" "$TARGET_DIR")
BASE_SERVICE_NAME=$(basename "$TARGET_REALPATH" | tr '_' '-')-app
SERVICE_NAME="$BASE_SERVICE_NAME-$ENVIRONMENT"
PROJECT_ID=$(deploy_common::get_project_id)

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
BUILD_CONTEXT="$TARGET_REALPATH"
TEMP_CONTEXT=""

cleanup_temp_context() {
    if [[ -n "$TEMP_CONTEXT" && -d "$TEMP_CONTEXT" ]]; then
        rm -rf "$TEMP_CONTEXT"
    fi
}

if [[ $(basename "$TARGET_REALPATH") == "mvp_site" ]]; then
    if [ -n "$WORLD_DIR" ]; then
        echo "Creating temporary build context for mvp_site..."
        TEMP_CONTEXT=$(mktemp -d)
        trap cleanup_temp_context EXIT

        rsync -a "$TARGET_REALPATH/" "$TEMP_CONTEXT/"
        rm -rf "$TEMP_CONTEXT/world"
        mkdir -p "$TEMP_CONTEXT/world"
        rsync -a "${WORLD_DIR%/}/" "$TEMP_CONTEXT/world/"

        BUILD_CONTEXT="$TEMP_CONTEXT"

        echo "DEBUG: World files copied from $WORLD_DIR to $TEMP_CONTEXT/world"
        find "$TEMP_CONTEXT/world" -mindepth 1 -maxdepth 1 | head -5
    else
        echo "WARNING: No world directory found to copy!"
        echo "Deployment may fail if world files are required."
    fi
elif [ -z "$WORLD_DIR" ]; then
    echo "WARNING: No world directory found to copy!"
    echo "Deployment may fail if world files are required."
fi

deploy_common::submit_build "$BUILD_CONTEXT" "$IMAGE_TAG"

# --- Deploy Step ---
echo "Deploying to Cloud Run as service '$SERVICE_NAME'..."
deploy_common::deploy_service \
    "$SERVICE_NAME" \
    "$IMAGE_TAG" \
    "GEMINI_API_KEY=gemini-api-key:latest" \
    "2Gi" \
    "300" \
    "1" \
    "10" \
    "10"

echo "--- Deployment of '$SERVICE_NAME' complete. ---"

# Configure load balancer timeout to match service timeout
echo "Configuring load balancer timeout..."
deploy_common::update_service_timeout "$SERVICE_NAME" "300"

deploy_common::service_url "$SERVICE_NAME"
