#!/bin/bash
# 🚨 DEVELOPMENT INFRASTRUCTURE SCRIPT
# ⚠️ REQUIRES PROJECT ADAPTATION - Contains project-specific configurations
# This script provides development environment management patterns
# Adapt paths, service names, and configurations for your project

#!/bin/bash

# Simple script to resolve conflicts for current PR
# Usage: ./resolve_conflicts.sh

echo "🔄 Auto-resolving conflicts for current branch..."

# Get current branch and PR number
CURRENT_BRANCH=$(git branch --show-current)
PR_NUMBER=$(gh pr view --json number --jq '.number' 2>/dev/null || echo "")

if [ -z "$PR_NUMBER" ]; then
    echo "❌ Not in a PR branch or no PR found"
    exit 1
fi

echo "📍 Branch: $CURRENT_BRANCH"
echo "📋 PR: #$PR_NUMBER"

# Use the full auto-resolution script
chmod +x scripts/auto_resolve_conflicts.sh
./scripts/auto_resolve_conflicts.sh $PR_NUMBER
