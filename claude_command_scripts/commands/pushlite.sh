#!/bin/bash
# pushlite.sh - Simple push to GitHub without test server or automation
# Lightweight alternative to full /push command

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Help function
show_help() {
    echo "pushlite.sh - Simple push to GitHub without automation"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  pr          Push and create PR to main"
    echo "  force       Force push to origin (use with caution)"
    echo "  -h, --help  Show this help message"
    echo ""
    echo "Description:"
    echo "  Lightweight push command that:"
    echo "  1. Handles untracked files intelligently"
    echo "  2. Pushes current branch to origin"
    echo "  3. Optionally creates PR"
    echo "  4. Skips test automation and server management"
    echo ""
    echo "Examples:"
    echo "  $0          # Simple push"
    echo "  $0 pr       # Push and create PR"
    echo "  $0 force    # Force push"
    echo ""
    echo "Aliases: /pushlite, /pushl"
    exit 0
}

# Parse arguments
CREATE_PR=false
FORCE_PUSH=false

for arg in "$@"; do
    case "$arg" in
        pr)
            CREATE_PR=true
            ;;
        force)
            FORCE_PUSH=true
            ;;
        -h|--help)
            show_help
            ;;
        *)
            echo "Unknown option: $arg"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo -e "${CYAN}🚀 Push Lite${NC}"
echo "============"

# Pre-flight checks
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git is not installed${NC}"
    exit 1
fi

if [[ "$CREATE_PR" == "true" ]]; then
    if ! command -v gh &> /dev/null; then
        echo -e "${RED}❌ GitHub CLI (gh) is required for PR creation${NC}"
        exit 1
    fi
    if ! command -v jq &> /dev/null; then
        echo -e "${RED}❌ jq is required for PR creation (JSON parsing)${NC}"
        echo "Install with: sudo apt-get install jq (Ubuntu/Debian) or brew install jq (macOS)"
        exit 1
    fi
fi

# Get current branch
current_branch=$(git branch --show-current)
if [[ -z "$current_branch" ]]; then
    echo -e "${RED}❌ Not on any branch${NC}"
    exit 1
fi

echo -e "${BLUE}Branch:${NC} $current_branch"

# Check repository status
echo -e "\n${BLUE}📋 Repository Status${NC}"
git_status=$(git status --porcelain)
untracked_files=$(echo "$git_status" | grep "^??" | cut -c4- || true)
staged_files=$(echo "$git_status" | grep "^[MARCDT]" | cut -c4- || true)
modified_files=$(echo "$git_status" | grep "^.[MARCDT]" | cut -c4- || true)

# Count files (handle empty strings properly)
untracked_count=$(echo "$untracked_files" | sed '/^$/d' | wc -l)
staged_count=$(echo "$staged_files" | sed '/^$/d' | wc -l)
modified_count=$(echo "$modified_files" | sed '/^$/d' | wc -l)

echo "  Staged files: $staged_count"
echo "  Modified files: $modified_count"
echo "  Untracked files: $untracked_count"

# Handle untracked files if present
if [[ $untracked_count -gt 0 ]]; then
    echo -e "\n${YELLOW}📁 Untracked Files Found:${NC}"
    echo "$untracked_files" | head -20
    if [[ $untracked_count -gt 20 ]]; then
        echo "... and $((untracked_count - 20)) more files"
    fi
    
    echo -e "\n${YELLOW}Options:${NC}"
    echo "  [1] Add all untracked files and commit"
    echo "  [2] Select specific files to add"
    echo "  [3] Continue without adding (push existing commits only)"
    echo "  [4] Cancel push operation"
    echo ""
    
    while true; do
        read -p "Choose option [1-4]: " -n 1 -r choice
        echo
        
        case "$choice" in
            1)
                echo -e "${BLUE}📝 Adding all untracked files...${NC}"
                git add .
                
                # Suggest commit message based on files
                commit_msg="Add untracked files"
                if echo "$untracked_files" | grep -q "test_"; then
                    commit_msg="Add tests and supporting files"
                elif echo "$untracked_files" | grep -q "\.md$"; then
                    commit_msg="Add documentation"
                elif echo "$untracked_files" | grep -q "\.sh$"; then
                    commit_msg="Add scripts and tools"
                elif echo "$untracked_files" | grep -q "ci_replica"; then
                    commit_msg="Add CI replica tools"
                elif echo "$untracked_files" | grep -q "chrome"; then
                    commit_msg="Add browser automation tools"
                fi
                
                echo "Suggested commit message: $commit_msg"
                read -p "Enter commit message (or press Enter to use suggestion): " user_msg
                if [[ -n "$user_msg" ]]; then
                    commit_msg="$user_msg"
                fi
                
                git commit -m "$commit_msg"
                echo -e "${GREEN}✅ Files committed${NC}"
                break
                ;;
            2)
                echo -e "${BLUE}📝 Select files to add:${NC}"
                echo "$untracked_files" | nl -w2 -s') '
                echo ""
                read -p "Enter file numbers (space-separated, e.g., 1 3 5): " file_numbers
                
                selected_files=()
                for num in $file_numbers; do
                    if [[ "$num" =~ ^[0-9]+$ ]] && [[ $num -le $untracked_count ]]; then
                        file=$(echo "$untracked_files" | sed -n "${num}p")
                        selected_files+=("$file")
                    fi
                done
                
                if [[ ${#selected_files[@]} -gt 0 ]]; then
                    echo -e "${BLUE}Adding selected files:${NC}"
                    for file in "${selected_files[@]}"; do
                        echo "  + $file"
                        git add "$file"
                    done
                    
                    read -p "Enter commit message: " commit_msg
                    if [[ -n "$commit_msg" ]]; then
                        git commit -m "$commit_msg"
                        echo -e "${GREEN}✅ Selected files committed${NC}"
                    else
                        echo -e "${RED}❌ Commit message required${NC}"
                        exit 1
                    fi
                else
                    echo -e "${YELLOW}⚠️ No valid files selected${NC}"
                fi
                break
                ;;
            3)
                echo -e "${YELLOW}⚠️ Continuing without adding untracked files${NC}"
                break
                ;;
            4)
                echo -e "${RED}❌ Push cancelled${NC}"
                exit 0
                ;;
            *)
                echo "Invalid choice. Please select 1-4."
                continue
                ;;
        esac
    done
fi

# Check if there are any commits to push
commits_ahead=$(git rev-list --count @{upstream}..HEAD 2>/dev/null || echo "unknown")
if [[ "$commits_ahead" == "0" ]]; then
    echo -e "\n${YELLOW}⚠️ No new commits to push${NC}"
    if [[ "$FORCE_PUSH" != "true" ]]; then
        echo "Branch is up to date with remote"
        exit 0
    fi
fi

# Push to remote
echo -e "\n${BLUE}📤 Pushing to remote...${NC}"

# Execute push directly (avoid eval for security)
if [[ "$FORCE_PUSH" == "true" ]]; then
    echo -e "${YELLOW}⚠️ Force pushing (this will overwrite remote history)${NC}"
    read -p "Are you sure? [y/N]: " -n 1 -r confirm
    echo
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        echo -e "${RED}❌ Force push cancelled${NC}"
        exit 0
    fi
    echo "Executing: git push --force-with-lease origin $current_branch"
    if git push --force-with-lease origin "$current_branch"; then
        echo -e "${GREEN}✅ Push successful${NC}"
    else
        echo -e "${RED}❌ Push failed${NC}"
        exit 1
    fi
else
    # Check if upstream is set
    if ! git rev-parse --abbrev-ref @{upstream} >/dev/null 2>&1; then
        echo "Setting upstream and pushing..."
        echo "Executing: git push -u origin $current_branch"
        if git push -u origin "$current_branch"; then
            echo -e "${GREEN}✅ Push successful${NC}"
        else
            echo -e "${RED}❌ Push failed${NC}"
            exit 1
        fi
    else
        echo "Executing: git push origin $current_branch"
        if git push origin "$current_branch"; then
            echo -e "${GREEN}✅ Push successful${NC}"
        else
            echo -e "${RED}❌ Push failed${NC}"
            exit 1
        fi
    fi
fi

# Create PR if requested
if [[ "$CREATE_PR" == "true" ]]; then
    echo -e "\n${BLUE}📋 Creating Pull Request...${NC}"
    
    # Check if PR already exists
    existing_pr=$(gh pr list --head "$current_branch" --json number,url --limit 1 2>/dev/null || echo "[]")
    pr_exists=$(echo "$existing_pr" | jq 'length > 0' 2>/dev/null || echo "false")
    
    if [[ "$pr_exists" == "true" ]]; then
        pr_number=$(echo "$existing_pr" | jq -r '.[0].number')
        pr_url=$(echo "$existing_pr" | jq -r '.[0].url')
        echo -e "${YELLOW}⚠️ PR already exists: #$pr_number${NC}"
        echo "  URL: $pr_url"
    else
        # Create new PR
        echo "Creating new PR..."
        if pr_url=$(gh pr create --title "$(git log -1 --pretty=format:'%s')" --body "Automated PR creation via pushlite

## Changes
- $(git log --oneline --no-merges origin/main..HEAD | head -5 | sed 's/^/- /')

🤖 Generated with pushlite command"); then
            echo -e "${GREEN}✅ PR created successfully${NC}"
            echo "  URL: $pr_url"
        else
            echo -e "${RED}❌ Failed to create PR${NC}"
            echo "You can create it manually with: gh pr create"
        fi
    fi
fi

# Run CI replica test
echo -e "\n${BLUE}🔄 Running CI replica test...${NC}"
if [ -f "./run_ci_replica.sh" ]; then
    if ./run_ci_replica.sh; then
        echo -e "${GREEN}✅ CI replica tests passed${NC}"
    else
        echo -e "${YELLOW}⚠️ CI replica tests failed - review before merging${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ CI replica script not found${NC}"
fi

# Summary
echo -e "\n${GREEN}✅ Push Lite Complete${NC}"
echo "  Branch: $current_branch"
echo "  Remote: origin/$current_branch"

if [[ "$commits_ahead" != "unknown" && "$commits_ahead" != "0" ]]; then
    echo "  Commits pushed: $commits_ahead"
fi

if [[ "$CREATE_PR" == "true" ]]; then
    echo "  PR: Processed"
fi

echo -e "\n${CYAN}💡 Tips:${NC}"
echo "  • Use 'git status' to check working directory"
echo "  • Use 'gh pr view' to see PR details"
echo "  • Use '/push' for full automation with tests"