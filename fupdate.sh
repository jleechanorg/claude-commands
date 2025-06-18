#!/bin/bash
set -e

# --- Preparation ---
# Find the repository root for git operations
REPO_ROOT=$(git rev-parse --show-toplevel)
# IMPORTANT: Store the directory where the script was initially called
INITIAL_DIR=$(pwd)

# --- Argument Parsing & Context Awareness ---
COMMIT_MSG=""
# Capture all arguments to pass them through later
ALL_ARGS=("$@")

# Find the commit message within the arguments
for arg in "$@"; do
    # A simple assumption: if it's not a known environment name, it's a commit message.
    # This is not perfect but works for your use case.
    if [[ "$arg" != "stable" ]] && [[ "$arg" != "dev" ]]; then
        COMMIT_MSG="$arg"
    fi
done

# --- Git Push Step (Run from Repo Root) ---
cd "$REPO_ROOT"
echo "--- Starting GitHub Push Step ---"

# Use a default commit message if none was provided
if [ -z "$COMMIT_MSG" ]; then
    COMMIT_MSG="commit from $(basename "$INITIAL_DIR") at $(date '+%Y-%m-%d %H:%M:%S %Z')"
fi

echo "Staging all changes..."
git add .
echo "Committing with message: '$COMMIT_MSG'..."
git commit --allow-empty -m "$COMMIT_MSG"
echo "Pushing changes to GitHub..."
git push
echo "Push complete."


# --- GCP Deploy Step (Run from the original directory) ---
echo ""
echo "--- Starting GCP Deploy Step ---"

# Go back to the directory where the user ran the command
cd "$INITIAL_DIR"

# Call deploy.sh. It will now correctly auto-detect the Dockerfile
# because it is being run from the correct directory.
# We also pass the original arguments in case they are needed (e.g., for environment).
"$REPO_ROOT/deploy.sh" "${ALL_ARGS[@]}"

echo "Full update finished."
