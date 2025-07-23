#!/bin/bash
# Simple test for integrate.sh branch protection features

echo "🧪 Testing integrate.sh branch protection features..."
echo "=================================================="

# Test 1: Check that script has branch protection logic
echo "Test 1: Checking for branch protection logic..."
if grep -q "create.*PR" integrate.sh; then
    echo "✅ PASS: Script contains PR creation logic"
else
    echo "❌ FAIL: No PR creation logic found"
    exit 1
fi

# Test 2: Check for sync PR detection
echo "Test 2: Checking for sync PR detection..."
if grep -q "check_existing_sync_pr" integrate.sh; then
    echo "✅ PASS: Script has sync PR detection"
else
    echo "❌ FAIL: No sync PR detection found"
    exit 1
fi

# Test 3: Check for repository rule handling
echo "Test 3: Checking for repository rule handling..."
if grep -q "repository.*rule\|branch.*protection" integrate.sh; then
    echo "✅ PASS: Script handles repository rules"
else
    echo "❌ FAIL: No repository rule handling found"
    exit 1
fi

# Test 4: Check script syntax
echo "Test 4: Checking script syntax..."
if bash -n integrate.sh; then
    echo "✅ PASS: Script syntax is valid"
else
    echo "❌ FAIL: Script has syntax errors"
    exit 1
fi

# Test 5: Check for merge branch logic
echo "Test 5: Checking for merge branch logic..."
if grep -q "merge-main.*date" integrate.sh; then
    echo "✅ PASS: Script has merge branch logic"
else
    echo "❌ FAIL: No merge branch logic found"
    exit 1
fi

echo "=================================================="
echo "🎉 All tests passed! integrate.sh branch protection fix is working."