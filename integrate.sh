#!/bin/bash

# integrate.sh - Updates from main and creates fresh dev branch
# This script implements the standard integration pattern for the project

set -e  # Exit on any error

echo "🔄 Starting integration process..."
echo "1. Switching to main branch..."
git checkout main

echo "2. Pulling latest changes from origin..."
git pull

echo "3. Deleting existing dev branch (if it exists)..."
git branch -D dev 2>/dev/null || echo "   (dev branch didn't exist, continuing...)"

echo "4. Creating fresh dev branch from main..."
git checkout -b dev

echo "✅ Integration complete! You are now on a fresh 'dev' branch with latest main changes."
echo "📍 Current branch: $(git branch --show-current)" 