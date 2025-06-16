#!/bin/bash
set -e

# --- Preparation ---
# Find the repository root, regardless of where the script is called from.
REPO_ROOT=$(git rev-parse --show-toplevel)
# Save the directory where the user initially ran the command.
INITIAL_DIR=$PWD

# --- Git Push Step ---
echo "--- Starting GitHub Push Step ---"
# Change to the repo root to perform git operations.
cd "$REPO_ROOT"

if [ -z "$1" ]; then
    COMMIT_MESSAGE="commit at this time $(date '+%Y-%m-%d %H:%M:%S %Z')"
else
    COMMIT_MESSAGE="$1 $(date '+%Y-%m-%d %H:%M:%S %Z')"
fi

echo "Staging all changes..."
git add .
echo "Committing with message: '$COMMIT_MESSAGE'..."
git commit --allow-empty -m "$COMMIT_MESSAGE"
echo "Pushing changes to GitHub..."
git push
echo "Push complete."


# --- GCP Deploy Step ---
echo ""
echo "--- Starting GCP Deploy Step ---"
# Now, check if the INITIAL directory has a Dockerfile.
if [ -f "$INITIAL_DIR/Dockerfile" ]; then
    # It does. Deploy it automatically.
    # deploy.sh should be run from the root and given the target directory name.
    DEPLOY_TARGET=$(basename "$INITIAL_DIR")
    echo "Auto-detecting and deploying app in '$DEPLOY_TARGET'..."
    ./deploy.sh "$DEPLOY_TARGET"
else
    # It does not. Assume we are in the root and show the interactive menu.
    echo "No Dockerfile in current directory. Please choose an app to deploy:"
    apps=($(find . -maxdepth 2 -type f -name "Dockerfile" -printf "%h\n" | sed 's|./||' | sort))
    
    if [ ${#apps[@]} -eq 0 ]; then
        echo "No apps with a Dockerfile found."
        exit 1
    fi

    select app in "${apps[@]}"; do
        if [[ -n $app ]]; then
            ./deploy.sh "$app"
            break
        else
            echo "Invalid selection. Please try again."
        fi
    done
fi

echo "Full update finished."
