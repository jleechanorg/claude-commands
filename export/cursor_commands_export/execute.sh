#!/bin/bash
# Execute command - Strategic task execution (requires AI assistant)
# Usage: ./execute.sh [task]
# Aliases: e.sh, plan.sh

# Initialize security and configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/security_utils.sh"
source "$SCRIPT_DIR/config.sh"

# Initialize security utilities
init_security_utils || handle_error "Failed to initialize security utilities"
init_config || handle_error "Failed to initialize configuration"

# Get task description
task_description="$*"
current_branch=$(get_current_branch)
validate_branch_name "$current_branch" || handle_error "Invalid branch name: $current_branch"

# Create safe scratchpad path
scratchpad_path="$ROADMAP_DIR/scratchpad_${current_branch}.md"

log_message "INFO" "Execute/Plan command invoked for task: $task_description"

echo "=== Execute/Plan Command ==="
echo ""
echo "This command requires AI assistance for strategic planning and execution."
echo ""
echo "Manual execution checklist:"
echo "□ Assess task complexity (Low/Medium/High)"
echo "□ Check available context/time"
echo "□ Plan execution approach"
echo "□ Set checkpoint frequency (every 5 min or 3-5 files)"
echo "□ Update scratchpad: $scratchpad_path"
echo "□ Commit and push at checkpoints"
echo ""
echo "For complex tasks in Cursor:"
echo "1. Break down the task into subtasks"
echo "2. Create a todo list or project plan"
echo "3. Execute systematically with regular commits"
echo "4. Update progress documentation"
echo ""
echo "Your task: $task_description"
echo ""
echo "Recommended approach:"
echo "1. Create a detailed plan first"
echo "2. Get approval if needed"
echo "3. Execute with regular checkpoints"
echo "4. Document decisions and progress"
echo ""
echo "Current branch: $current_branch"
echo "Scratchpad: $scratchpad_path"
echo "Environment: $(detect_environment)"

log_message "INFO" "Execute/Plan guidance displayed"