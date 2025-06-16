#!/bin/bash
DEPLOY_DIR=$1
COMMIT_MSG="${*:2}"
if [ -z "$DEPLOY_DIR" ]; then
  echo "ERROR: Please provide the target directory to deploy as the first argument."
  echo "Usage: ./fupdate.sh <directory> [optional commit message]"
  exit 1
fi
echo "--- Starting GitHub Push Step ---"
./push.sh "$COMMIT_MSG" && \
echo ""
echo "--- Starting GCP Deploy Step for '$DEPLOY_DIR' ---"
./deploy.sh "$DEPLOY_DIR"
echo "Full update finished."
