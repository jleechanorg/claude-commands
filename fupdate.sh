#!/bin/bash
# A script to push changes to GitHub and then deploy to GCP.
# It requires a commit message as the first argument.

# Check if a commit message was provided
if [ -z "$1" ]; then
  echo "ERROR: Please provide a commit message."
  echo "Usage: fupdate \"Your commit message\""
  exit 1
fi

echo "--- Starting GitHub Push Step ---"
~/bin/push.sh "$1" && \

echo ""
echo "--- Starting GCP Deploy Step ---"
~/bin/deploy.sh

echo "Full update finished."
