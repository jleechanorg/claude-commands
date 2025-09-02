#!/bin/bash
# Fix 1: Bash 3.x Compatible Array Deduplication and Sorting
# This script provides bash 3.x compatible replacements for readarray operations
# Fixes: "readarray -t" command compatibility issues on macOS and older bash versions

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m' 
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print status messages
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Bash 3.x compatible array deduplication and sorting function
# Usage: dedupe_and_sort_array array_name
# This replaces: readarray -t array_name < <(printf '%s\n' "${array_name[@]}" | sort -u)
dedupe_and_sort_array() {
    local array_name="$1"
    local temp_file
    local line
    local sorted_unique_items=()
    
    # Create secure temporary file
    temp_file=$(mktemp "${TMPDIR:-/tmp}/dedupe_sort_XXXXXX.txt")
    
    # Ensure cleanup on exit
    trap "rm -f '$temp_file'" EXIT
    
    # Check if array exists and has elements
    local array_size
    eval "array_size=\${#$array_name[@]}"
    
    if [ "$array_size" -eq 0 ]; then
        print_warning "Array $array_name is empty, nothing to dedupe/sort"
        return 0
    fi
    
    print_status "Deduplicating and sorting array '$array_name' with $array_size elements"
    
    # Write array elements to temp file (handles special characters and spaces)
    local i
    for ((i = 0; i < array_size; i++)); do
        eval "printf '%s\\n' \"\${$array_name[$i]}\"" >> "$temp_file"
    done
    
    # Sort and deduplicate using external sort command
    sort -u "$temp_file" > "${temp_file}.sorted"
    
    # Clear the original array (bash 3.x compatible)
    eval "$array_name=()"
    
    # Read sorted unique lines back into array (bash 3.x compatible)
    while IFS= read -r line || [[ -n "$line" ]]; do
        # Escape special characters properly for eval
        eval "$array_name+=($(printf %q "$line"))"
    done < "${temp_file}.sorted"
    
    # Get new array size
    eval "array_size=\${#$array_name[@]}"
    
    print_success "Array '$array_name' now contains $array_size unique elements"
    
    # Cleanup
    rm -f "${temp_file}.sorted"
}

# Alternative implementation using associative arrays (if bash 4+ available)
# This is more efficient but requires bash 4+
dedupe_and_sort_array_bash4() {
    local array_name="$1"
    local -A seen_items
    local sorted_unique_items=()
    local item
    local array_size
    
    eval "array_size=\${#$array_name[@]}"
    
    if [ "$array_size" -eq 0 ]; then
        return 0
    fi
    
    print_status "Using bash 4+ optimized deduplication for array '$array_name'"
    
    # Build associative array to track seen items
    local i
    for ((i = 0; i < array_size; i++)); do
        eval "item=\${$array_name[$i]}"
        seen_items["$item"]=1
    done
    
    # Sort the unique keys and rebuild array
    local sorted_keys
    readarray -t sorted_keys < <(printf '%s\n' "${!seen_items[@]}" | sort)
    
    # Clear and repopulate the original array
    eval "$array_name=()"
    for item in "${sorted_keys[@]}"; do
        eval "$array_name+=($(printf %q "$item"))"
    done
    
    eval "array_size=\${#$array_name[@]}"
    print_success "Array '$array_name' optimized to $array_size unique elements"
}

# Function to detect bash version and choose appropriate method
smart_dedupe_and_sort() {
    local array_name="$1"
    
    # Check bash version
    if [ "${BASH_VERSINFO[0]}" -ge 4 ] && command -v readarray >/dev/null 2>&1; then
        print_status "Detected bash ${BASH_VERSION} - using optimized method"
        dedupe_and_sort_array_bash4 "$array_name"
    else
        print_status "Detected bash ${BASH_VERSION} - using compatible method"
        dedupe_and_sort_array "$array_name"
    fi
}

# Function to replace problematic readarray usage in run_tests.sh
fix_run_tests_readarray() {
    local script_path="$1"
    local backup_path="${script_path}.backup.$(date +%Y%m%d_%H%M%S)"
    
    print_status "Analyzing $script_path for readarray usage..."
    
    # Create backup
    cp "$script_path" "$backup_path"
    print_status "Created backup at $backup_path"
    
    # Check if readarray is used
    if grep -q "readarray" "$script_path"; then
        print_warning "Found readarray usage in $script_path - this needs manual replacement"
        print_status "The readarray command should be replaced with the smart_dedupe_and_sort function"
        print_status "Example replacement:"
        echo "  OLD: readarray -t test_files < <(printf '%s\\n' \"\${test_files[@]}\" | sort -u)"
        echo "  NEW: smart_dedupe_and_sort test_files"
        return 1
    else
        print_success "No readarray usage found in $script_path"
        return 0
    fi
}

# Fallback readarray function for older bash versions
# This gets loaded if readarray is not available
setup_readarray_fallback() {
    if ! command -v readarray >/dev/null 2>&1; then
        print_status "Setting up readarray fallback for bash ${BASH_VERSION}"
        
        # Define readarray function
        readarray() {
            local -a options=()
            local array_name=""
            local line
            
            # Parse arguments (simplified - doesn't handle all readarray options)
            while [[ $# -gt 0 ]]; do
                case $1 in
                    -t)
                        # Remove trailing newlines (default behavior we want)
                        shift
                        ;;
                    -*)
                        options+=("$1")
                        shift
                        ;;
                    *)
                        array_name="$1"
                        shift
                        break
                        ;;
                esac
            done
            
            if [[ -z "$array_name" ]]; then
                print_error "readarray: missing array name"
                return 1
            fi
            
            # Clear the array
            eval "$array_name=()"
            
            # Read lines into array
            while IFS= read -r line || [[ -n "$line" ]]; do
                eval "$array_name+=($(printf %q "$line"))"
            done
        }
        
        print_success "readarray fallback function installed"
    else
        print_status "readarray command available - no fallback needed"
    fi
}

# Export functions for use in other scripts
export -f dedupe_and_sort_array
export -f dedupe_and_sort_array_bash4  
export -f smart_dedupe_and_sort
export -f setup_readarray_fallback

# Main execution if run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    print_status "Starting readarray compatibility fix"
    
    # Setup fallback if needed
    setup_readarray_fallback
    
    # Check run_tests.sh if it exists
    if [[ -f "./run_tests.sh" ]]; then
        fix_run_tests_readarray "./run_tests.sh"
    else
        print_warning "run_tests.sh not found in current directory"
    fi
    
    print_success "Readarray compatibility fix completed"
fi