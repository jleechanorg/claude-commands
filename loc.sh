#!/bin/bash

# ==============================================================================
# Git Line Counter Script
#
# Description:
# This script calculates the number of lines of code added by a specific author
# in the last month for given file types (.py, .js, .html). It provides a
# breakdown per file type and a total sum.
#
# Usage:
# 1. Save this file as `git-stats.sh` in your project's root directory.
# 2. Give it execute permissions: `chmod +x git-stats.sh`
# 3. Run it from the terminal: `./git-stats.sh`
#
# You can also pass an author's email as an argument to override the default.
# Example: `./git-stats.sh "other-user@example.com"`
# ==============================================================================

# --- Configuration ---

# File extensions to track. Add or remove types as needed.
FILE_TYPES=("py" "js" "html")

# Time frame for the log search.
TIME_FRAME="1 month ago"

# --- Script Logic ---

# Determine the author to search for.
# Use the first script argument if provided, otherwise use the git config.
if [ -n "$1" ]; then
    AUTHOR_EMAIL="$1"
else
    AUTHOR_EMAIL=$(git config user.email)
fi

# Check if the author email was found.
if [ -z "$AUTHOR_EMAIL" ]; then
    echo "Error: Could not determine Git author email."
    echo "Please set it using: git config --global user.email 'your.email@example.com'"
    echo "Or pass it as an argument: ./git-stats.sh 'your.email@example.com'"
    exit 1
fi

echo "📊 Counting lines added by '$AUTHOR_EMAIL' since '$TIME_FRAME'..."
echo "========================================================================"

# Initialize total lines counter
TOTAL_LINES_ADDED=0

# Associative array to hold lines added per file type
declare -A lines_by_type

# --- Main processing loop ---
# Iterate over each defined file type.
for ext in "${FILE_TYPES[@]}"; do
    # Use git log to get the numerical stats for commits matching the criteria.
    # --author: Filters commits by the specified author email.
    # --since:  Filters commits to the specified time frame.
    # --pretty=tformat: Suppresses all commit metadata to get a clean output.
    # --numstat: Provides lines added, lines deleted, and file path.
    # -- "*.${ext}": A pathspec to filter for files with the current extension.
    #
    # The output is piped to awk:
    # awk script '{s+=$1} END {print s+0}' sums the first column (lines added).
    # 's+0' ensures that if there are no results, it prints 0 instead of an empty line.
    lines_added=$(git log --author="$AUTHOR_EMAIL" --since="$TIME_FRAME" --pretty=tformat: --numstat -- "*.$ext" | awk '{s+=$1} END {print s+0}')
    
    # Store the result in the associative array
    lines_by_type[$ext]=$lines_added
    
    # Add the count for the current file type to the grand total.
    TOTAL_LINES_ADDED=$((TOTAL_LINES_ADDED + lines_added))
done


# --- Display Results ---

echo "📈 Breakdown by File Type:"
echo "-----------------------------------"

# Print the results for each file type
printf "%-15s: %d lines\n" "Python (.py)" "${lines_by_type[py]}"
printf "%-15s: %d lines\n" "JavaScript (.js)" "${lines_by_type[js]}"
printf "%-15s: %d lines\n" "HTML (.html)" "${lines_by_type[html]}"

echo "-----------------------------------"
printf "✅ Total Lines Added: %d lines\n" "$TOTAL_LINES_ADDED"
echo "========================================================================"
