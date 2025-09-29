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

    # Directory groups allow us to fan out to multiple test jobs while
    # maintaining stable cache keys and predictable ordering.
    declare -A GROUP_CONFIG=(
        [core]="mvp_site"
        [claude]=".claude"
        [orchestration]="orchestration"
        [automation]="automation"
        [scripts]="scripts"
        [mcp]="mcp_servers"
    )

    # Preserve deterministic ordering when emitting the matrix
    local ordered_groups=(core claude orchestration automation scripts mcp)

    # Map the top-level directory to its logical group
    declare -A DIR_TO_GROUP=()
    for group in "${!GROUP_CONFIG[@]}"; do
        IFS=',' read -ra group_dirs <<< "${GROUP_CONFIG[$group]}"
        for raw_dir in "${group_dirs[@]}"; do
            local dir="$(echo "$raw_dir" | xargs)"
            [ -z "$dir" ] && continue
            DIR_TO_GROUP["$dir"]="$group"
        done
    done

    declare -A SELECTED_GROUPS=()

    # Analyze changes by directory (safe for files with spaces)
    while IFS= read -r file; do
        [ -z "$file" ] && continue

        local dir_component=""
        if [[ "$file" == */* ]]; then
            dir_component="${file%%/*}"
        else
            dir_component="$file"
        fi

        local group="${DIR_TO_GROUP[$dir_component]}"
        if [ -z "$group" ]; then
            # For root-level files or other dirs, run core tests (mvp_site)
            group="core"
        fi

        SELECTED_GROUPS["$group"]=1
    done <<< "$changed_files"

    # Fallback to core tests if no specific changes detected
    if [ "${#SELECTED_GROUPS[@]}" -eq 0 ]; then
        SELECTED_GROUPS[core]=1
    fi

    local test_dirs=""
    local matrix_output=""
    local has_changes="false"
    declare -A added_dirs=()
    declare -A added_simple_dirs=()

    for group in "${ordered_groups[@]}"; do
        if [ -z "${SELECTED_GROUPS[$group]}" ]; then
            continue
        fi

        has_changes="true"

        local cleaned_dirs=""
        IFS=',' read -ra group_dirs <<< "${GROUP_CONFIG[$group]}"
        for raw_dir in "${group_dirs[@]}"; do
            local dir="$(echo "$raw_dir" | xargs)"
            [ -z "$dir" ] && continue

            if [ -z "${added_dirs[$dir]}" ]; then
                if [ -n "$test_dirs" ]; then
                    test_dirs="$test_dirs,$dir"
                else
                    test_dirs="$dir"
                fi
                added_dirs["$dir"]=1
            fi

            if [ -n "$cleaned_dirs" ]; then
                cleaned_dirs="$cleaned_dirs,$dir"
            else
                cleaned_dirs="$dir"
            fi
        done

        if [ "$output_format" = "include" ]; then
            if [ -n "$matrix_output" ]; then
                matrix_output="$matrix_output,"
            fi
            matrix_output="$matrix_output{\"test-group\":\"$group\",\"test-dirs\":\"$cleaned_dirs\"}"
        else
            local primary_dir="${cleaned_dirs%%,*}"
            if [ -z "${added_simple_dirs[$primary_dir]}" ]; then
                if [ -n "$matrix_output" ]; then
                    matrix_output="$matrix_output,\"$primary_dir\""
                else
                    matrix_output="\"$primary_dir\""
                fi
                added_simple_dirs["$primary_dir"]=1
            fi
        fi
    done

    # Output results
    local selected_groups_list=""
    for group in "${ordered_groups[@]}"; do
        if [ -n "${SELECTED_GROUPS[$group]}" ]; then
            if [ -n "$selected_groups_list" ]; then
                selected_groups_list="$selected_groups_list,$group"
            else
                selected_groups_list="$group"
            fi
        fi
    done

    echo "selected-groups=$selected_groups_list"
    echo "test-dirs=$test_dirs"
    if [ "$output_format" = "include" ]; then
        echo "matrix={\"include\":[$matrix_output]}"
    else
        echo "matrix={\"test-dir\":[$matrix_output]}"
    fi
    echo "has-changes=$has_changes"

    echo "Selected groups: $selected_groups_list"
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
