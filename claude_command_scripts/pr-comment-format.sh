#!/bin/bash

# PR Comment Formatter - CLI script for generating structured PR comment responses
# Usage: ./pr-comment-format.sh [template|interactive|json <file>]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FORMATTER_SCRIPT="$PROJECT_ROOT/scripts/pr_comment_formatter.py"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to show usage
show_usage() {
    print_color $BLUE "PR Comment Formatter - Generate structured PR comment responses"
    echo
    echo "Usage: $0 [command] [options]"
    echo
    echo "Commands:"
    echo "  template          Generate a template response"
    echo "  interactive       Interactive mode to build response"
    echo "  json <file>       Generate response from JSON file"
    echo "  help              Show this help message"
    echo
    echo "Examples:"
    echo "  $0 template                                    # Generate template"
    echo "  $0 interactive                                 # Interactive mode"
    echo "  $0 json /path/to/response.json                # From JSON file"
    echo
}

# Function to run the formatter
run_formatter() {
    local mode=$1
    local file=$2
    
    cd "$PROJECT_ROOT"
    
    if [[ "$mode" == "template" ]]; then
        print_color $GREEN "Generating PR comment template..."
        python3 "$FORMATTER_SCRIPT" 2>/dev/null | head -n -4  # Remove the demo dividers
        
    elif [[ "$mode" == "json" ]]; then
        if [[ -z "$file" ]]; then
            print_color $RED "Error: JSON file path required"
            echo "Usage: $0 json <file>"
            exit 1
        fi
        
        if [[ ! -f "$file" ]]; then
            print_color $RED "Error: File not found: $file"
            exit 1
        fi
        
        print_color $GREEN "Generating PR comment response from JSON..."
        python3 -c "
import sys
import json
sys.path.insert(0, 'scripts')
from pr_comment_formatter import PRCommentFormatter

with open('$file', 'r') as f:
    data = json.load(f)
    
response = PRCommentFormatter.from_json(data)
print(response.format_response())
"
        
    elif [[ "$mode" == "interactive" ]]; then
        run_interactive_mode
        
    else
        print_color $RED "Error: Unknown command: $mode"
        show_usage
        exit 1
    fi
}

# Function to run interactive mode
run_interactive_mode() {
    print_color $BLUE "=== Interactive PR Comment Response Builder ==="
    echo
    
    # Get summary title
    read -p "Enter summary title: " summary_title
    
    # Create temporary Python script for interactive mode
    cat > /tmp/pr_interactive.py << 'EOF'
import sys
sys.path.insert(0, 'scripts')
from pr_comment_formatter import PRCommentFormatter, CommentStatus

# Get summary from command line
summary_title = sys.argv[1] if len(sys.argv) > 1 else "PR Updated & Comments Addressed"
response = PRCommentFormatter.create_response(summary_title)

def get_status_from_input(prompt):
    """Get status from user input with validation."""
    while True:
        status_input = input(f"{prompt} (resolved/fixed/validated/addressed/rejected/skipped/pending): ").strip().lower()
        try:
            return CommentStatus.from_string(status_input)
        except:
            print("Invalid status. Please use: resolved, fixed, validated, addressed, rejected, skipped, or pending")

def add_tasks():
    """Add tasks interactively."""
    print("\n=== Adding Tasks ===")
    while True:
        task_desc = input("Enter task description (or 'done' to finish): ").strip()
        if task_desc.lower() == 'done':
            break
        
        details = []
        print("Enter task details (press Enter on empty line to finish):")
        while True:
            detail = input("- ").strip()
            if not detail:
                break
            details.append(detail)
        
        status = get_status_from_input("Task status")
        response.add_task(task_desc, details, status)
        print(f"✅ Added task: {task_desc}")

def add_user_comments():
    """Add user comments interactively."""
    print("\n=== Adding User Comments ===")
    while True:
        comment_text = input("Enter user comment text (or 'done' to finish): ").strip()
        if comment_text.lower() == 'done':
            break
        
        # Get line number (optional)
        line_input = input("Line number (press Enter to skip): ").strip()
        line_number = int(line_input) if line_input.isdigit() else None
        
        # Get response
        comment_response = input("Enter your response: ").strip()
        
        # Get status
        status = get_status_from_input("Comment status")
        
        response.add_user_comment(line_number, comment_text, comment_response, status)
        print(f"✅ Added user comment at line {line_number or 'N/A'}")

def add_copilot_comments():
    """Add Copilot comments interactively."""
    print("\n=== Adding Copilot Comments ===")
    while True:
        comment_desc = input("Enter Copilot comment description (or 'done' to finish): ").strip()
        if comment_desc.lower() == 'done':
            break
        
        # Get status
        status = get_status_from_input("Comment status")
        
        # Get reason
        reason = input("Enter reason/explanation: ").strip()
        
        response.add_copilot_comment(comment_desc, status, reason)
        print(f"✅ Added Copilot comment: {comment_desc}")

# Run interactive sections
add_tasks()
add_user_comments()
add_copilot_comments()

# Get final status
final_status = input("\nEnter final status summary: ").strip()
response.final_status = final_status

# Output the formatted response
print("\n" + "="*60)
print("GENERATED PR COMMENT RESPONSE:")
print("="*60)
print(response.format_response())
EOF

    # Run the interactive script
    cd "$PROJECT_ROOT"
    python3 /tmp/pr_interactive.py "$summary_title"
    
    # Clean up
    rm -f /tmp/pr_interactive.py
}

# Function to create example JSON file
create_example_json() {
    cat > /tmp/example_pr_response.json << 'EOF'
{
    "summary_title": "Example PR Response",
    "tasks": [
        {
            "description": "Fixed critical bug",
            "details": [
                "Root cause identified in authentication module",
                "Added comprehensive unit tests",
                "Implemented proper error handling"
            ],
            "status": "fixed"
        },
        {
            "description": "Updated documentation",
            "details": [
                "API endpoints documented",
                "Code examples added"
            ],
            "status": "resolved"
        }
    ],
    "user_comments": [
        {
            "line_number": 123,
            "text": "Is this thread-safe?",
            "response": "Added synchronization locks and thread safety tests",
            "status": "resolved"
        },
        {
            "line_number": 456,
            "text": "What about error handling?",
            "response": "Implemented comprehensive error handling with logging",
            "status": "addressed"
        }
    ],
    "copilot_comments": [
        {
            "description": "Dead code removal",
            "status": "fixed",
            "reason": "Cleaned up unused variables and imports"
        },
        {
            "description": "SQL injection risk",
            "status": "fixed",
            "reason": "Implemented parameterized queries"
        },
        {
            "description": "Performance optimization",
            "status": "rejected",
            "reason": "Current implementation is sufficient for expected load"
        }
    ],
    "final_status": "All comments addressed, tests passing, ready for review"
}
EOF
    
    print_color $GREEN "Example JSON file created at: /tmp/example_pr_response.json"
    echo "You can use it with: $0 json /tmp/example_pr_response.json"
}

# Main script logic
main() {
    case "${1:-help}" in
        "template")
            run_formatter "template"
            ;;
        "interactive")
            run_formatter "interactive"
            ;;
        "json")
            run_formatter "json" "$2"
            ;;
        "example")
            create_example_json
            ;;
        "help"|"--help"|"-h")
            show_usage
            ;;
        *)
            print_color $RED "Error: Unknown command: $1"
            echo
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"