#!/bin/bash

# Enable strict error handling
set -e          # Exit immediately if any command fails
set -u          # Exit if undefined variables are used
set -o pipefail # Exit if any command in a pipeline fails

# Deploy Firestore Security Rules Script
# This script deploys the newly created security rules to Firebase

echo "🔐 Deploying Firestore Security Rules to Production"
echo "=================================================="

# Check if Firebase CLI is installed
if ! command -v firebase &> /dev/null; then
    echo "❌ Firebase CLI not found. Installing..."
    npm install -g firebase-tools
fi

# Check if user is logged in
if ! firebase projects:list &> /dev/null; then
    echo "🔑 Firebase login required. Please run:"
    echo "   firebase login"
    echo ""
    echo "Then re-run this script."
    exit 1
fi

# Deploy rules
echo "📤 Deploying Firestore security rules..."
firebase deploy --only firestore:rules

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SUCCESS: Firestore security rules deployed!"
    echo "🔒 Your database is now secure and protected."
    echo ""
    echo "📋 What was deployed:"
    echo "   ✓ User-based authentication required"
    echo "   ✓ Campaign data restricted to owners only"
    echo "   ✓ Input validation on campaign creation"
    echo "   ✓ Proper read/write permissions"
    echo "   ✓ Default deny-all for unknown paths"
    echo ""
    echo "🎯 Next steps:"
    echo "   1. Test your app to ensure all functionality works"
    echo "   2. Monitor Firebase console for any rule violations"
    echo "   3. Update indexes if needed: firebase deploy --only firestore:indexes"
else
    echo ""
    echo "❌ ERROR: Failed to deploy rules"
    echo "Please check the error messages above and try again"
    exit 1
fi
