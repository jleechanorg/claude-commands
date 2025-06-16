#!/bin/bash
set -e

# This script is a wrapper that performs git operations and then calls the main deploy.sh script.

# --- Preparation ---
# Find the repository root, regardless of where the script is called from.
REPO_ROOT=$(git rev-parse --show-toplevel)
cd "$REPO_ROOT" # Ensure all operations run from the root

# --- Git Push Step ---
echo "--- Starting GitHub Push Step ---"
COMMIT_MSG=""
# Loop through all arguments to find the commit message and environment
for arg in "$@"; do
    if [[ "$arg" != "stable" ]] && [[ "$arg" != "dev" ]] && [[ ! -d "$arg" ]]; then
        COMMIT_MSG="$arg"
    fi
done

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

# Pass all original arguments directly to the deploy.sh script
./deploy.sh "$@"

echo "Full update finished."
