#!/bin/bash
set -e

# --- Git Push Step ---
echo "--- Starting GitHub Push Step ---"
# Navigate to the repo root to ensure we push the whole repo
cd "$(dirname "$0")"

# Use the logic from your existing push.sh script
if [ -z "$1" ]; then
    COMMIT_MESSAGE="commit at this time $(date '+%Y-%m-%d %H:%M:%S %Z')"
else
    COMMIT_MESSAGE="$1 $(date '+%Y-%m-%d %H:%M:%S %Z')"
fi

echo "Staging all changes..."
git add .
echo "Committing with message: '$COMMIT_MESSAGE'..."
# Use git commit --allow-empty for cases where only metadata changes
git commit --allow-empty -m "$COMMIT_MESSAGE"
echo "Pushing changes to GitHub..."
git push
echo "Push complete."


# --- GCP Deploy Step ---
echo ""
echo "--- Starting GCP Deploy Step ---"
# Check if the current directory has a Dockerfile
if [ -f "Dockerfile" ]; then
    ./deploy.sh
else
    # If not, assume we are in the root and show the menu
    echo "You are in the root directory. Please choose an app to deploy:"
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
