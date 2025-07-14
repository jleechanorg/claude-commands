#!/bin/bash
# handoff.sh - Create structured task handoff with PR and worker prompt
# Usage: ./claude_command_scripts/commands/handoff.sh [task_name] [description]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Show help
show_help() {
    echo -e "${BLUE}📤 /handoff - Structured Task Handoff${NC}"
    echo ""
    echo "Creates a complete handoff package for task delegation:"
    echo "• Handoff branch with analysis"
    echo "• Detailed scratchpad with implementation plan"
    echo "• GitHub PR with ready-to-implement status"
    echo "• Updated roadmap tracking"
    echo "• Copy-paste worker prompt"
    echo "• Clean new branch for continued work"
    echo ""
    echo -e "${CYAN}Usage:${NC}"
    echo "  $0 [task_name] [description]"
    echo ""
    echo -e "${CYAN}Examples:${NC}"
    echo "  $0 logging_fix 'Add file logging configuration to main application'"
    echo "  $0 ui_polish 'Improve button placement and styling'"
    echo "  $0 test_coverage 'Add unit tests for utility functions'"
    echo ""
    echo -e "${CYAN}What it creates:${NC}"
    echo "  • Branch: handoff-[task_name] (pushed to remote)"
    echo "  • Scratchpad: roadmap/scratchpad_handoff_[task_name].md"
    echo "  • GitHub PR with complete documentation"
    echo "  • Roadmap entry with HANDOFF READY status"
    echo "  • Worker prompt for immediate delegation"
    echo "  • Returns you to your original working branch"
    echo ""
    echo -e "${CYAN}Options:${NC}"
    echo "  --help    Show this help message"
}

# Check if help requested
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    show_help
    exit 0
fi

# Check arguments
if [[ $# -lt 2 ]]; then
    echo -e "${RED}❌ Error: Missing required arguments${NC}"
    echo ""
    echo "Usage: $0 [task_name] [description]"
    echo "Example: $0 logging_fix 'Add file logging configuration to main application'"
    echo ""
    echo "Use --help for more information"
    exit 1
fi

TASK_NAME="$1"
shift
DESCRIPTION="$*"

# Validate task name (no spaces, reasonable length)
if [[ ! "$TASK_NAME" =~ ^[a-zA-Z0-9_-]+$ ]]; then
    echo -e "${RED}❌ Error: Task name must contain only letters, numbers, underscores, and hyphens${NC}"
    echo "Invalid: '$TASK_NAME'"
    echo "Valid examples: logging_fix, ui-polish, test_coverage"
    exit 1
fi

if [[ ${#TASK_NAME} -gt 50 ]]; then
    echo -e "${RED}❌ Error: Task name too long (max 50 characters)${NC}"
    exit 1
fi

if [[ ${#DESCRIPTION} -lt 10 ]]; then
    echo -e "${RED}❌ Error: Description too short (min 10 characters)${NC}"
    exit 1
fi

# Helper functions
get_current_branch() {
    local branch
    branch=$(git branch --show-current 2>/dev/null)
    if [[ -z "$branch" ]]; then
        echo -e "${RED}❌ Error: Unable to detect current git branch${NC}" >&2
        echo "This command must be run from within a git repository." >&2
        exit 1
    fi
    echo "$branch"
}

check_git_status() {
    git status --porcelain 2>/dev/null || echo ""
}

generate_task_id() {
    echo "TASK-$(openssl rand -hex 4 | tr '[:lower:]' '[:upper:]')"
}

create_scratchpad() {
    local task_name="$1"
    local description="$2"
    local current_branch="$(get_current_branch)"
    local timestamp="$(date '+%Y-%m-%d %H:%M')"
    local filename="roadmap/scratchpad_handoff_${task_name}.md"
    
    cat > "$filename" << EOF
# Scratchpad: ${task_name//_/ } (Title Case)

**Branch**: $current_branch  
**Goal**: $description  
**Status**: Analysis complete, ready for implementation handoff  
**Created**: $timestamp

## Problem Statement

$description

## Analysis Summary

Add detailed analysis here:
- Root cause identified
- Current state documented  
- Solution approach validated
- Dependencies mapped

## Implementation Plan

### Step 1: [First Implementation Step]
- [ ] Specific action item with file references
- [ ] Another action item with expected outcome
- [ ] Validation step

### Step 2: [Second Implementation Step]  
- [ ] Specific action item
- [ ] Another action item
- [ ] Validation step

### Step 3: [Testing & Validation]
- [ ] Unit tests for new functionality
- [ ] Integration tests if needed
- [ ] Manual verification steps
- [ ] Performance/security considerations

## Files to Modify

- \`file1.py\`: Description of changes needed
- \`file2.py\`: Description of changes needed
- \`tests/test_file.py\`: New test cases required

## Testing Requirements

1. **Unit Tests**: 
   - Test new functionality
   - Edge case coverage
   - Error handling validation

2. **Integration Tests**: 
   - End-to-end workflow testing
   - Component interaction validation

3. **Manual Verification**: 
   - [ ] Feature works as expected
   - [ ] No regressions introduced
   - [ ] Performance acceptable

## Context for Next Worker

This task is ready for implementation. The analysis phase is complete and the implementation approach is defined.

**Key Background:**
- Previous attempts/considerations
- Important constraints or requirements
- Integration points with existing system

## Dependencies

- No blocking dependencies identified
- Related to: [Reference any related tasks/PRs]
- Requires: [Any specific tools/environments]

## Definition of Done

- [ ] Implementation complete per plan
- [ ] All tests passing (unit + integration)
- [ ] Code review approved
- [ ] Documentation updated if needed
- [ ] No regressions in existing functionality

## Branch Status

- **Analysis**: ✅ Complete
- **Implementation**: ⏳ Ready for handoff
- **Testing**: ⏳ Pending implementation
- **Deployment**: ⏳ Pending completion
EOF

    echo "$filename"
}

update_roadmap() {
    local task_name="$1"
    local description="$2"
    local task_id="$(generate_task_id)"
    
    # Create backup
    cp roadmap/roadmap.md roadmap/roadmap.md.backup
    
    # Add to roadmap after "Next Priority Tasks" line
    awk -v task_id="$task_id" -v desc="$description" '
        /^### Next Priority Tasks \(Ready to Start\)/ { 
            print $0
            print "- **" task_id "** 🟡 " desc " - HANDOFF READY"
            next
        }
        { print }
    ' roadmap/roadmap.md.backup > roadmap/roadmap.md
    
    rm roadmap/roadmap.md.backup
    echo "$task_id"
}

create_pr() {
    local task_name="$1"
    local description="$2"
    local scratchpad_file="$3"
    local branch_name="$(get_current_branch)"
    
    # Create PR body
    local pr_body="## Handoff Task

**Task**: $description

**Status**: Ready for implementation handoff

## Analysis Complete

Complete analysis and implementation plan available in \`$scratchpad_file\`.

## Implementation Required

See scratchpad for:
- [ ] Detailed implementation steps
- [ ] Files to modify with specific changes
- [ ] Testing requirements and validation steps
- [ ] Definition of done criteria

## Ready for Assignment

This task has been analyzed and is ready for a worker to pick up and implement.

### Next Steps for Worker
1. Review implementation plan in \`$scratchpad_file\`
2. Follow step-by-step implementation guide
3. Write tests as specified
4. Verify all acceptance criteria met

🤖 Generated with [Claude Code](https://claude.ai/code)"
    
    # Commit changes
    git add "$scratchpad_file" roadmap/roadmap.md
    git commit -m "Add handoff task: $description

Implementation plan in $scratchpad_file
Ready for worker assignment

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
    
    # Push branch
    git push origin "HEAD:$branch_name"
    
    # Create PR
    local pr_url
    pr_url=$(gh pr create \
        --title "Handoff: $description" \
        --body "$pr_body" 2>&1)
    
    if [[ $? -eq 0 ]]; then
        echo "$pr_url"
    else
        echo -e "${RED}❌ Failed to create PR: $pr_url${NC}"
        return 1
    fi
}


generate_worker_prompt() {
    local task_name="$1"
    local description="$2"
    local pr_url="$3"
    local scratchpad_file="$4"
    
    echo "## Worker Assignment

**Task**: $description

**Reference**: $pr_url

**Analysis**: Complete implementation plan available in \`$scratchpad_file\`

**Status**: Ready for implementation

### Quick Summary
- Analysis phase complete
- Implementation approach defined  
- Files to modify identified
- Testing strategy documented

### Deliverables
1. Implement solution per scratchpad plan
2. Write/update tests as specified
3. Verify all tests pass
4. Submit for code review

### Getting Started
1. Check out the handoff branch or read the scratchpad for full details
2. Review implementation plan in \`$scratchpad_file\`
3. Follow step-by-step implementation guide
4. Run tests to verify solution

The analysis is complete - this is ready for implementation."
}

# Main execution
main() {
    echo -e "${BLUE}🚀 Creating handoff for: ${CYAN}$DESCRIPTION${NC}"
    echo ""
    
    # Remember original branch
    local original_branch="$(get_current_branch)"
    
    # Check for uncommitted changes
    if [[ -n "$(check_git_status)" ]]; then
        echo -e "${YELLOW}⚠️  Warning: You have uncommitted changes${NC}"
        echo "Please commit or stash them first:"
        git status --short
        echo ""
        exit 1
    fi
    
    # Create handoff branch
    local handoff_branch="handoff-$TASK_NAME"
    echo -e "${CYAN}📝 Creating handoff branch: $handoff_branch${NC}"
    
    if git show-ref --verify --quiet "refs/heads/$handoff_branch"; then
        echo -e "${RED}❌ Branch $handoff_branch already exists${NC}"
        exit 1
    fi
    
    git checkout -b "$handoff_branch"
    
    # Create scratchpad
    echo -e "${CYAN}📋 Creating scratchpad...${NC}"
    local scratchpad_file
    scratchpad_file=$(create_scratchpad "$TASK_NAME" "$DESCRIPTION")
    
    # Update roadmap
    echo -e "${CYAN}🗺️  Updating roadmap...${NC}"
    local task_id
    task_id=$(update_roadmap "$TASK_NAME" "$DESCRIPTION")
    
    # Create PR
    echo -e "${CYAN}🔀 Creating PR...${NC}"
    local pr_url
    pr_url=$(create_pr "$TASK_NAME" "$DESCRIPTION" "$scratchpad_file")
    
    if [[ $? -ne 0 ]]; then
        echo -e "${RED}❌ Failed to create PR${NC}"
        exit 1
    fi
    
    # Switch back to original branch
    echo -e "${CYAN}🔄 Returning to original branch: $original_branch${NC}"
    git checkout "$original_branch"
    
    # Show results
    echo ""
    echo "="*60
    echo -e "${GREEN}✅ HANDOFF COMPLETE${NC}"
    echo "="*60
    echo -e "${CYAN}📋 Scratchpad:${NC} $scratchpad_file"
    echo -e "${CYAN}🔀 PR:${NC} $pr_url"
    echo -e "${CYAN}🆔 Task ID:${NC} $task_id"
    echo -e "${CYAN}🌿 Handoff branch:${NC} $handoff_branch (pushed to remote)"
    echo -e "${CYAN}📍 Current branch:${NC} $original_branch (restored)"
    echo ""
    echo "="*60
    echo -e "${GREEN}📤 WORKER PROMPT (Copy & Paste)${NC}"
    echo "="*60
    generate_worker_prompt "$TASK_NAME" "$DESCRIPTION" "$pr_url" "$scratchpad_file"
    echo ""
    echo -e "${GREEN}✅ Ready for delegation!${NC}"
}

# Run main function
main "$@"