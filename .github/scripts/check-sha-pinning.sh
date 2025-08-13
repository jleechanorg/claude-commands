#!/bin/bash

# GitHub Actions SHA-Pinning Compliance Checker
# This script verifies that all GitHub Actions in workflow files use SHA-pinned versions
# Usage: .github/scripts/check-sha-pinning.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔍 Checking GitHub Actions SHA-pinning compliance..."
echo "=================================================="

# Find all workflow files
workflow_files=$(find .github/workflows -name "*.yml" -o -name "*.yaml" 2>/dev/null)

if [ -z "$workflow_files" ]; then
    echo -e "${YELLOW}No workflow files found in .github/workflows/${NC}"
    exit 0
fi

# Track violations
violations=0
total_actions=0

# Check each workflow file
for file in $workflow_files; do
    echo -e "\n📄 Checking: ${file}"
    
    # Find all uses: statements with @ references
    # This regex finds lines with "uses:" followed by something with an @ symbol
    while IFS= read -r line_info; do
        if [ -z "$line_info" ]; then
            continue
        fi
        
        line_num=$(echo "$line_info" | cut -d: -f1)
        line_content=$(echo "$line_info" | cut -d: -f2-)
        
        # Extract the action reference (everything after "uses:" and any whitespace)
        action_ref=$(echo "$line_content" | sed -n 's/.*uses:[[:space:]]*\([^[:space:]]*\).*/\1/p')
        
        if [ -z "$action_ref" ]; then
            continue
        fi
        
        total_actions=$((total_actions + 1))
        
        # Check if it contains an @ symbol
        if [[ "$action_ref" == *"@"* ]]; then
            # Extract the part after @
            version_ref=$(echo "$action_ref" | cut -d@ -f2 | cut -d' ' -f1)
            
            # Check if it's a 40-character SHA (full commit hash)
            if [[ ! "$version_ref" =~ ^[a-f0-9]{40}$ ]]; then
                echo -e "  ${RED}❌ Line $line_num: Non-SHA reference found${NC}"
                echo -e "     Action: $action_ref"
                echo -e "     Version ref: @$version_ref"
                
                # Check if it's a tag or branch reference
                if [[ "$version_ref" =~ ^v[0-9] ]] || [[ "$version_ref" == "main" ]] || [[ "$version_ref" == "master" ]] || [[ "$version_ref" == "latest" ]]; then
                    echo -e "     ${YELLOW}⚠️  This appears to be a mutable tag/branch reference - security risk!${NC}"
                fi
                
                violations=$((violations + 1))
            else
                echo -e "  ${GREEN}✅ Line $line_num: SHA-pinned (secure)${NC}"
            fi
        fi
    done < <(grep -n "uses:" "$file" 2>/dev/null | grep "@" || true)
done

# Summary
echo -e "\n=================================================="
echo "📊 SHA-Pinning Compliance Summary"
echo "=================================================="
echo "Total actions found: $total_actions"
echo "SHA-pinned (secure): $((total_actions - violations))"
echo -e "Non-SHA references (vulnerable): ${violations}"

if [ $violations -gt 0 ]; then
    echo -e "\n${RED}❌ FAILED: Found $violations non-SHA-pinned action reference(s)${NC}"
    echo -e "${YELLOW}Please update all action references to use full commit SHAs.${NC}"
    echo -e "${YELLOW}See .github/README.md for instructions on finding the correct SHAs.${NC}"
    exit 1
else
    echo -e "\n${GREEN}✅ PASSED: All GitHub Actions are properly SHA-pinned${NC}"
    echo -e "${GREEN}Your workflows are protected against supply chain attacks!${NC}"
    exit 0
fi