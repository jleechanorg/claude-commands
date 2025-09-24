#!/bin/bash

# CI Change Detection Script for Directory-Based Testing
# Shared logic for detecting changed directories and generating test matrices
# Used by GitHub Actions workflows to optimize CI execution

set -e
set -o pipefail  # Ensure pipeline failures propagate

# Function to detect changed files based on event type
detect_changed_files() {
    local event_name="$1"
    local base_sha="$2"
    local head_sha="$3"

    # Input validation
    if [ -z "$event_name" ]; then
        echo "Error: event_name parameter is required" >&2
        return 1
    fi

    if [ "$event_name" = "pull_request" ]; then
        if [ -z "$base_sha" ] || [ -z "$head_sha" ]; then
            echo "Error: base_sha and head_sha required for pull_request events" >&2
            return 1
        fi
        if ! git diff --name-only "$base_sha"..."$head_sha" 2>/dev/null; then
            echo "Error: Failed to get diff for PR ($base_sha...$head_sha)" >&2
            return 1
        fi
    else
        if ! git diff --name-only "HEAD~1..HEAD" 2>/dev/null; then
            echo "Error: Failed to get diff for push" >&2
            return 1
        fi
    fi
}

# Function to analyze directory changes and generate matrix
generate_test_matrix() {
    local changed_files="$1"
    local output_format="$2"  # "simple" or "include"

    # Input validation
    if [ -z "$output_format" ]; then
        echo "Error: output_format parameter is required" >&2
        return 1
    fi

    if [ "$output_format" != "simple" ] && [ "$output_format" != "include" ]; then
        echo "Error: output_format must be 'simple' or 'include'" >&2
        return 1
    fi

    echo "Changed files:"
    echo "$changed_files"

    # Initialize directory flags (compatible with older bash)
    local mvp_changed=0
    local claude_changed=0
    local orch_changed=0
    local scripts_changed=0
    local mcp_changed=0
    local auto_changed=0

    # Analyze changes by directory (safe for files with spaces)
    # Use process substitution to avoid subshell variable scope issues
    while IFS= read -r file; do
        [ -z "$file" ] && continue
        dir="${file%%/*}"  # Extract first directory component efficiently
        case "$dir" in
            "mvp_site")
                mvp_changed=1
                ;;
            ".claude")
                claude_changed=1
                ;;
            "orchestration")
                orch_changed=1
                ;;
            "scripts")
                scripts_changed=1
                ;;
            "mcp_servers")
                mcp_changed=1
                ;;
            "automation")
                auto_changed=1
                ;;
            *)
                # For root-level files or other dirs, run core tests (mvp_site)
                mvp_changed=1
                ;;
        esac
    done <<< "$changed_files"

    # Build test directories list and matrix
    local test_dirs=""
    local matrix_output=""
    local has_changes="false"

    # Helper function to add directory to outputs
    add_directory() {
        local dir="$1"
        if [ -n "$test_dirs" ]; then
            test_dirs="$test_dirs,$dir"
        else
            test_dirs="$dir"
        fi
        has_changes="true"

        # Build matrix based on output format
        if [ "$output_format" = "include" ]; then
            if [ -n "$matrix_output" ]; then
                matrix_output="$matrix_output,"
            fi
            matrix_output="$matrix_output{\"test-group\":\"$dir\",\"test-dirs\":\"$dir\"}"
        else
            # Simple format
            if [ -n "$matrix_output" ]; then
                matrix_output="$matrix_output,\"$dir\""
            else
                matrix_output="\"$dir\""
            fi
        fi
    }

    # Add directories based on changes
    [ "$mvp_changed" = "1" ] && add_directory "mvp_site"
    [ "$claude_changed" = "1" ] && add_directory ".claude"
    [ "$orch_changed" = "1" ] && add_directory "orchestration"
    [ "$scripts_changed" = "1" ] && add_directory "scripts"
    [ "$mcp_changed" = "1" ] && add_directory "mcp_servers"
    [ "$auto_changed" = "1" ] && add_directory "automation"

    # Fallback to core tests if no specific changes detected
    if [ "$has_changes" = "false" ]; then
        test_dirs="mvp_site"
        if [ "$output_format" = "include" ]; then
            matrix_output="{\"test-group\":\"core\",\"test-dirs\":\"mvp_site\"}"
        else
            matrix_output="\"mvp_site\""
        fi
        has_changes="true"
    fi

    # Output results
    echo "test-dirs=$test_dirs"
    if [ "$output_format" = "include" ]; then
        echo "matrix={\"include\":[$matrix_output]}"
    else
        echo "matrix={\"test-dir\":[$matrix_output]}"
    fi
    echo "has-changes=$has_changes"

    echo "Final test directories: $test_dirs"
    echo "Matrix output: $matrix_output"
}

# Main execution
main() {
    local event_name="${1:-push}"
    local base_sha="${2:-}"
    local head_sha="${3:-}"
    local output_format="${4:-simple}"

    echo "🔍 CI Change Detection Starting"
    echo "Event: $event_name, Format: $output_format"

    # Detect changed files
    local changed_files
    changed_files=$(detect_changed_files "$event_name" "$base_sha" "$head_sha")

    # Generate test matrix
    generate_test_matrix "$changed_files" "$output_format"

    echo "✅ CI Change Detection Complete"
}

# Execute if run directly
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi
