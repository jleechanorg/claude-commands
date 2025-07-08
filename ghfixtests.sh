#!/bin/bash

# Script to find PRs with failing tests and offer to fix them via Claude comments

echo "🔍 Scanning recent PRs for failing tests..."
echo

# Get PRs with failing checks
failing_prs=""
pr_count=0

# Check last 20 open PRs
while IFS=$'\t' read -r number title; do
    # Check if this PR has failing tests
    if gh pr checks "$number" 2>/dev/null | grep -q "fail"; then
        # Get failing check details
        failing_checks=$(gh pr checks "$number" 2>/dev/null | grep "fail" | awk '{print $2}' | tr '\n' ', ' | sed 's/, $//')
        
        failing_prs="${failing_prs}${number}|${title}|${failing_checks}\n"
        ((pr_count++))
    fi
done < <(gh pr list --limit 20 --state open --json number,title --jq '.[] | [.number, .title] | @tsv')

if [ $pr_count -eq 0 ]; then
    echo "✅ No PRs with failing tests found!"
    exit 0
fi

echo "Found $pr_count PR(s) with failing tests:"
echo

# Display failing PRs
i=1
declare -A pr_map
while IFS='|' read -r number title checks; do
    [ -z "$number" ] && continue
    echo "$i. PR #$number: $title"
    echo "   ❌ Failing: $checks"
    echo
    pr_map[$i]=$number
    ((i++))
done < <(echo -e "$failing_prs")

# Ask user what to do
echo "Would you like to:"
echo "[a] Fix all failing PRs"
echo "[1,2,3...] Fix specific PRs (comma-separated numbers)"
echo "[n] Cancel"
echo
read -p "Your choice: " choice

if [[ "$choice" == "n" ]]; then
    echo "Cancelled."
    exit 0
fi

# Determine which PRs to fix
prs_to_fix=""
if [[ "$choice" == "a" ]]; then
    # Fix all
    for key in "${!pr_map[@]}"; do
        prs_to_fix="${prs_to_fix} ${pr_map[$key]}"
    done
else
    # Fix specific ones
    IFS=',' read -ra selections <<< "$choice"
    for sel in "${selections[@]}"; do
        sel=$(echo "$sel" | tr -d ' ')
        if [[ -n "${pr_map[$sel]}" ]]; then
            prs_to_fix="${prs_to_fix} ${pr_map[$sel]}"
        fi
    done
fi

if [[ -z "$prs_to_fix" ]]; then
    echo "No valid PRs selected."
    exit 1
fi

# Post comments to selected PRs
echo
echo "📝 Posting Claude comments to fix tests..."
for pr in $prs_to_fix; do
    echo -n "Commenting on PR #$pr... "
    
    # Get more details about failures if possible
    failure_details=$(gh pr checks "$pr" 2>/dev/null | grep "fail" | head -5 | sed 's/^/  - /')
    
    comment="@claude-code-action fix unit tests

The CI checks are failing. Please investigate and fix all failing tests.

Failing checks:
$failure_details

Please ensure all tests pass before completing."
    
    if gh pr comment "$pr" --body "$comment" 2>/dev/null; then
        echo "✅ Done"
    else
        echo "❌ Failed"
    fi
done

echo
echo "🎉 Complete! Claude should now be working on fixing the tests."