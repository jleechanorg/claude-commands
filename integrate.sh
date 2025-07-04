#!/bin/bash

# integrate.sh - Updates from main and creates fresh dev branch
# This script implements the standard integration pattern for the project

set -e  # Exit on any error

echo "🔄 Starting integration process..."
echo "1. Switching to main branch..."
git checkout main

echo "2. Pulling latest changes from origin..."
git pull

echo "3. Creating timestamp for unique branch name..."
timestamp=$(date +%s)
branch_name="dev${timestamp}"
echo "   New branch will be: $branch_name"

echo "4. Creating fresh dev branch from main..."
git checkout -b "$branch_name"

echo "✅ Integration complete! You are now on a fresh '$branch_name' branch with latest main changes."
echo "📍 Current branch: $(git branch --show-current)" 