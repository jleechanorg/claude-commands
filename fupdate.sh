#!/bin/bash
# A script to push changes to GitHub and then deploy to GCP.
# A commit message is optional.

echo "--- Starting GitHub Push Step ---"
# The "$@" passes all arguments from this script directly to push.sh
# If no arguments are given, none are passed, and push.sh uses its default.
~/worldarchitect.ai/push.sh "$@" && \

echo ""
echo "--- Starting GCP Deploy Step ---"
~/worldarchitect.ai/deploy.sh

echo "Full update finished."
