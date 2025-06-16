#!/bin/bash
# A script to push changes to GitHub and then deploy.
# The deploy script is now smart enough to figure out what to do.
# A commit message is optional.

# All arguments passed to this script will be forwarded to push.sh
COMMIT_MSG="$@"

echo "--- Starting GitHub Push Step ---"
~/worldarchitect.ai/push.sh "$COMMIT_MSG" && \

echo ""
echo "--- Starting GCP Deploy Step ---"
# The deploy script also lives in the root of the repo
~/worldarchitect.ai/deploy.sh

echo "Full update finished."
