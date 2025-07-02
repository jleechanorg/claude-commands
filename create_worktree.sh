#!/bin/bash

# This script creates a new Git worktree with a specified name.
# It prepends "worktree_" to the given name and automatically navigates
# into the new worktree directory after creation.
# It also includes checks for name collisions with existing directories and local branches.

# Function to display error messages and exit the script
error_exit() {
    echo "Error: $1" >&2
    exit 1
}

# Function to display informational messages
info_message() {
    echo "Info: $1"
}

# --- 1. Get Worktree Name ---
RAW_WORKTREE_NAME=""

# Check if a worktree name was provided as a command-line argument
if [ -n "$1" ]; then
    RAW_WORKTREE_NAME="$1"
else
    # If no argument, prompt the user for the worktree name
    read -p "Enter the desired base name for the new worktree (e.g., 'my-feature'): " RAW_WORKTREE_NAME
fi

# Validate that a name was entered
if [ -z "$RAW_WORKTREE_NAME" ]; then
    error_exit "Worktree base name cannot be empty. Please provide a name."
fi

# Prepend "worktree_" to the provided name
WORKTREE_NAME="worktree_${RAW_WORKTREE_NAME}"

info_message "Attempting to create a new worktree named '$WORKTREE_NAME'..."

# --- 2. Collision Checks ---

# Check 1: Does a directory with this name already exist in the current location?
if [ -d "$WORKTREE_NAME" ]; then
    error_exit "A directory named '$WORKTREE_NAME' already exists in the current working directory. Please choose a different base name or remove the existing directory."
fi

# Check 2: Does a local branch with this name already exist?
# git show-ref --verify --quiet checks if a ref (like a branch) exists without outputting anything.
# It exits with 0 if it exists, non-zero otherwise.
if git show-ref --verify --quiet "refs/heads/$WORKTREE_NAME"; then
    error_exit "A local Git branch named '$WORKTREE_NAME' already exists. Please choose a different base name for the worktree to create a new, unique branch."
fi

# Check 3: Is this script being run inside a Git repository?
# This is crucial for 'git worktree add' to function.
if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    error_exit "You are not currently inside a Git repository. Please navigate to a Git repository to create a worktree."
fi

# --- 3. Create the Worktree ---

# Use 'git worktree add' to create the new worktree.
# The first argument is the path (directory name) for the new worktree.
# The -b flag explicitly tells Git to create a new branch with the specified name.
# If no starting point is given after the branch name, it defaults to HEAD.
if git worktree add "$WORKTREE_NAME" -b "$WORKTREE_NAME"; then
    info_message "Successfully created new Git worktree '$WORKTREE_NAME' at './$WORKTREE_NAME'."
    echo "A new branch '$WORKTREE_NAME' has been created and checked out in this worktree."
    echo ""

    # --- 4. Navigate into the new Worktree ---
    info_message "Navigating into the new worktree directory: './$WORKTREE_NAME'..."
    cd "$WORKTREE_NAME" || error_exit "Failed to navigate into the new worktree directory."
    info_message "You are now in the new worktree: $(pwd)"
    echo ""
    echo "To list all your worktrees, run:"
    echo "  git worktree list"
else
    # If 'git worktree add' fails for any reason (e.g., permissions, internal Git error)
    error_exit "Failed to create worktree '$WORKTREE_NAME'. Please check the error messages from Git above."
fi
