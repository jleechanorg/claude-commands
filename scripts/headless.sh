#!/bin/bash

# /headless - Enhanced Automated Development with Planning and PR Creation
# Usage: /headless [prompt]

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get the prompt from arguments
PROMPT="$*"

if [ -z "$PROMPT" ]; then
    echo -e "${RED}❌ Error: No prompt provided${NC}"
    echo -e "${CYAN}Usage:${NC} /headless [prompt]"
    echo -e "${CYAN}Example:${NC} /headless 'Add user authentication system with login/logout'"
    exit 1
fi

# Generate a unique branch name based on timestamp and prompt
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
TASK_NAME="headless_${TIMESTAMP}"
BRANCH_NAME="$TASK_NAME"
WORKTREE_DIR="$TASK_NAME"

echo -e "${BLUE}🚀 Enhanced Headless Development with Planning${NC}"
echo -e "${CYAN}Task:${NC} $PROMPT"
echo -e "${CYAN}Branch:${NC} $BRANCH_NAME"
echo -e "${CYAN}Worktree:${NC} $WORKTREE_DIR"
echo ""

# Phase 1: Planning (from /handoff)
echo -e "${BLUE}📋 Phase 1: Creating Analysis and Planning${NC}"

# Helper functions
get_current_branch() {
    git branch --show-current 2>/dev/null || echo "main"
}

get_default_branch() {
    # Try to determine the default branch dynamically
    local default_branch
    default_branch=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')
    if [ -z "$default_branch" ]; then
        # Fallback: try to get the default from remote info
        default_branch=$(git remote show origin 2>/dev/null | grep "HEAD branch" | cut -d' ' -f5)
    fi
    if [ -z "$default_branch" ]; then
        # Final fallback to main
        default_branch="main"
    fi
    echo "$default_branch"
}

check_git_status() {
    git status --porcelain 2>/dev/null || echo ""
}

has_changes() {
    ! git diff --quiet || ! git diff --cached --quiet || [ -n "$(git ls-files --others --exclude-standard)" ]
}

create_planning_scratchpad() {
    local task_name="$1"
    local prompt="$2"
    local current_branch="$(get_current_branch)"
    local timestamp="$(date '+%Y-%m-%d %H:%M')"
    local filename="roadmap/scratchpad_${task_name}.md"
    
    cat > "$filename" << EOF
# 🎯 HEADLESS COMMAND READY (Copy-paste when ready)

\`\`\`bash
claude -p "TASK: $prompt

CONTEXT: Complete analysis and implementation plan available
WORKTREE: $(pwd)
BRANCH: $BRANCH_NAME

SETUP: Already in isolated worktree with clean branch
GOAL: $prompt
IMPLEMENTATION: See detailed plan below

FILES TO MODIFY: See specific file list in implementation section
SUCCESS CRITERIA: All requirements met with tests passing
TIMELINE: Implement according to step-by-step plan

FULL SPECIFICATION: $(pwd)/$filename

START: Implement the detailed plan below" --output-format stream-json --verbose --dangerously-skip-permissions
\`\`\`

---

# Headless Development Plan: ${task_name}

**Created**: $timestamp  
**Original Branch**: $current_branch  
**Task**: $prompt  
**Status**: Analysis complete, ready for headless execution

## Problem Statement

$prompt

## Analysis Summary

Add detailed analysis here:
- Requirements identified and validated
- Current codebase structure understood
- Solution approach designed
- Dependencies and constraints mapped

## Implementation Plan

### Step 1: Core Implementation
- [ ] Create/modify primary files with specific functionality
- [ ] Implement main logic with proper error handling
- [ ] Add necessary imports and dependencies
- [ ] Validation step: Core functionality works

### Step 2: Testing & Validation  
- [ ] Add unit tests for new functionality
- [ ] Add integration tests if needed
- [ ] Manual verification steps
- [ ] Performance and security considerations

### Step 3: Documentation & Polish
- [ ] Update documentation if needed
- [ ] Code review and cleanup
- [ ] Final testing and validation
- [ ] Ensure no regressions

## Files to Create/Modify

- \`file1.py\`: Description of specific changes needed
- \`file2.py\`: Description of specific changes needed  
- \`tests/test_file.py\`: New test cases for validation

## Testing Strategy

1. **Unit Tests**: Test individual components and functions
2. **Integration Tests**: Test component interactions  
3. **Manual Verification**: Verify end-to-end functionality

## Context for Headless Execution

This task is fully planned and ready for automated implementation.

**Key Requirements:**
- Follow existing code patterns and conventions
- Maintain backwards compatibility
- Add comprehensive test coverage
- Document any breaking changes

## Success Criteria

- [ ] Implementation complete per detailed plan
- [ ] All tests passing (new and existing)
- [ ] Code follows project conventions
- [ ] No regressions in existing functionality
- [ ] Ready for code review

## Branch Status

- **Planning**: ✅ Complete  
- **Implementation**: ⏳ Ready for headless execution
- **Testing**: ⏳ Pending implementation
- **Review**: ⏳ Pending completion
EOF

    echo "$filename"
}

# Remember original directory
ORIGINAL_DIR="$(pwd)"

# Check for uncommitted changes in current location
if has_changes; then
    echo -e "${YELLOW}⚠️  Warning: You have uncommitted changes in current directory${NC}"
    echo "Please commit or stash them first:"
    git status --short
    echo ""
    exit 1
fi

# Determine the default branch dynamically
DEFAULT_BRANCH=$(get_default_branch)
echo -e "${CYAN}📍 Using base branch: $DEFAULT_BRANCH${NC}"

# Create git worktree with new branch from default branch
echo -e "${CYAN}📁 Creating isolated worktree...${NC}"
if ! git worktree add -b "$BRANCH_NAME" "$WORKTREE_DIR" "$DEFAULT_BRANCH"; then
    echo -e "${RED}❌ Error: Failed to create git worktree from $DEFAULT_BRANCH${NC}"
    exit 1
fi

# Change to worktree directory with error handling
cd "$WORKTREE_DIR" || {
    echo -e "${RED}❌ Error: Cannot enter worktree directory $WORKTREE_DIR${NC}"
    exit 1
}
echo -e "${CYAN}📁 Working in: $(pwd)${NC}"

# Create planning scratchpad with analysis
echo -e "${CYAN}📋 Creating detailed planning scratchpad...${NC}"
SCRATCHPAD_FILE=$(create_planning_scratchpad "$TASK_NAME" "$PROMPT")

# Commit the scratchpad
git add "$SCRATCHPAD_FILE"
git commit -m "Add planning scratchpad for headless task: $PROMPT

Detailed implementation plan in $SCRATCHPAD_FILE
Ready for headless execution

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push the planning branch
git push -u origin "$BRANCH_NAME"

# Phase 2: Generate Copy-Paste Command
echo ""
echo "="*80
echo -e "${GREEN}✅ PLANNING PHASE COMPLETE${NC}"
echo "="*80
echo -e "${CYAN}📋 Planning file:${NC} $SCRATCHPAD_FILE"
echo -e "${CYAN}🌿 Branch:${NC} $BRANCH_NAME (pushed to remote)"
echo -e "${CYAN}📁 Worktree:${NC} $(pwd)"
echo ""
echo "="*80
echo -e "${GREEN}🤖 HEADLESS COMMAND READY (Copy & Paste)${NC}"
echo "="*80
echo ""
echo -e "${YELLOW}claude -p \"TASK: $PROMPT"
echo ""
echo "CONTEXT: Complete analysis and implementation plan available"
echo "WORKTREE: $(pwd)"
echo "BRANCH: $BRANCH_NAME"
echo ""
echo "SETUP: Already in isolated worktree with clean branch"
echo "GOAL: $PROMPT"
echo "IMPLEMENTATION: See detailed plan below"
echo ""
echo "FILES TO MODIFY: See specific file list in implementation section"
echo "SUCCESS CRITERIA: All requirements met with tests passing"
echo "TIMELINE: Implement according to step-by-step plan"
echo ""
echo "FULL SPECIFICATION: $(pwd)/$SCRATCHPAD_FILE"
echo ""
echo "START: Implement the detailed plan below\" --output-format stream-json --verbose --dangerously-skip-permissions${NC}"
echo ""
echo "="*80
echo -e "${GREEN}📋 Next Steps:${NC}"
echo -e "${CYAN}1.${NC} Review the generated plan in: $SCRATCHPAD_FILE"
echo -e "${CYAN}2.${NC} Modify the plan if needed (add details, adjust approach)"
echo -e "${CYAN}3.${NC} Copy and paste the command above when ready to execute"
echo -e "${CYAN}4.${NC} The command will run Claude in headless mode in this worktree"
echo ""
echo -e "${GREEN}✅ Ready for headless execution!${NC}"

# Return to original directory but keep worktree
cd "$ORIGINAL_DIR" || {
    echo -e "${YELLOW}⚠️ Warning: Could not return to original directory $ORIGINAL_DIR${NC}"
    echo "You are currently in: $(pwd)"
}