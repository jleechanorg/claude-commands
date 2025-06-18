#!/bin/bash
set -e

# --- Preparation ---
REPO_ROOT=$(git rev-parse --show-toplevel)
cd "$REPO_ROOT"

# --- Argument Parsing for fupdate ---
COMMIT_MSG=""
DEPLOY_ARGS=() # Array to hold arguments for deploy.sh

# Loop through all arguments to separate commit message from deploy arguments
for arg in "$@"; do
    # If the argument is a directory or a known environment, it's for deploy.sh
    if [ -d "$arg" ] || [[ "$arg" == "stable" ]] || [[ "$arg" == "dev" ]]; then
        DEPLOY_ARGS+=("$arg")
    else
        # Otherwise, assume it's part of the commit message
        COMMIT_MSG="$arg"
    fi
done

# --- Git Push Step ---
echo "--- Starting GitHub Push Step ---"

# Use a default commit message if none was found
if [ -z "$COMMIT_MSG" ]; then
    COMMIT_MSG="commit at this time $(date '+%Y-%m-%d %H:%M:%S %Z')"
fi

echo "Staging all changes..."
git add .
echo "Committing with message: '$COMMIT_MSG'..."
git commit --allow-empty -m "$COMMIT_MSG"
echo "Pushing changes to GitHub..."
git push
echo "Push complete."


# --- GCP Deploy Step ---
echo ""
echo "--- Starting GCP Deploy Step ---"

# Pass only the filtered deployment arguments to the deploy.sh script
# The "${DEPLOY_ARGS[@]}" syntax correctly handles spaces and quotes in arguments
./deploy.sh "${DEPLOY_ARGS[@]}"

echo "Full update finished."
