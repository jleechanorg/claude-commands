#!/bin/bash

# Pre-commit hook to check GitHub Actions SHA-pinning
# To install this hook:
#   cp .github/hooks/pre-commit-sha-check.sh .git/hooks/pre-commit
#   chmod +x .git/hooks/pre-commit
#
# Or add to existing pre-commit hook:
#   cat .github/hooks/pre-commit-sha-check.sh >> .git/hooks/pre-commit

# Only check if workflow files are being committed
if git diff --cached --name-only | grep -q "\.github/workflows/.*\.y[a]ml$"; then
    echo "🔍 Checking GitHub Actions SHA-pinning in staged workflow files..."
    
    # Get list of staged workflow files
    staged_workflows=$(git diff --cached --name-only | grep "\.github/workflows/.*\.y[a]ml$")
    
    violations=0
    
    for file in $staged_workflows; do
        # Check the staged version of the file
        staged_content=$(git show ":$file" 2>/dev/null)
        
        if [ -z "$staged_content" ]; then
            continue
        fi
        
        # Look for uses: statements with non-SHA references
        while IFS= read -r line; do
            if [[ "$line" =~ uses:[[:space:]]*([^[:space:]]+) ]]; then
                action_ref="${BASH_REMATCH[1]}"
                
                if [[ "$action_ref" == *"@"* ]]; then
                    version_ref=$(echo "$action_ref" | cut -d@ -f2 | cut -d' ' -f1)
                    
                    # Check if it's NOT a 40-character SHA
                    if [[ ! "$version_ref" =~ ^[a-f0-9]{40}$ ]]; then
                        echo "❌ ERROR: Non-SHA reference found in $file"
                        echo "   Action: $action_ref"
                        echo "   Please use SHA-pinned version instead of @$version_ref"
                        echo ""
                        violations=$((violations + 1))
                    fi
                fi
            fi
        done <<< "$staged_content"
    done
    
    if [ $violations -gt 0 ]; then
        echo "=========================================="
        echo "❌ COMMIT BLOCKED: SHA-pinning violations detected!"
        echo ""
        echo "All GitHub Actions must use SHA-pinned versions for security."
        echo "See .github/README.md for instructions on finding correct SHAs."
        echo ""
        echo "To find the SHA for an action:"
        echo "  gh api repos/{owner}/{action}/git/refs/tags/{tag} --jq '.object.sha'"
        echo ""
        echo "Example fix:"
        echo "  ❌ uses: actions/checkout@v4"
        echo "  ✅ uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11  # v4.1.1"
        echo "=========================================="
        exit 1
    else
        echo "✅ All GitHub Actions in staged files are properly SHA-pinned"
    fi
fi

# Continue with commit
exit 0