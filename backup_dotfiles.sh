#!/bin/bash

# This script backs up specified dotfiles to a directory within this Git repository,
# then commits and pushes those changes.

# Ensure we are in the script's directory (which should be the repo root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || { echo "Failed to cd to script directory $SCRIPT_DIR"; exit 1; }

echo "Current working directory: $(pwd)"

# Define the backup destination directory within this repo
BACKUP_DIR="./dotfiles_backup" # Relative to the repo root

# Create the backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# --- List of dotfiles to back up ---
# Format: "Source Path in Home Dir" "Destination Filename in BACKUP_DIR"
declare -A DOTFILES_TO_BACKUP=(
    ["$HOME/.bashrc"]="bashrc_cloudworkstation.txt"
    ["$HOME/.gitconfig"]="gitconfig_cloudworkstation.txt" # Example: if you want to back up gitconfig
    # Add more files here if needed:
    # ["$HOME/.vimrc"]="vimrc_cloudworkstation.txt"
)
# --- End of list ---

HAS_CHANGES=0

echo "Starting dotfile backup process..."

for source_path in "${!DOTFILES_TO_BACKUP[@]}"; do
    dest_filename="${DOTFILES_TO_BACKUP[$source_path]}"
    dest_path="$BACKUP_DIR/$dest_filename"

    if [ -f "$source_path" ]; then
        echo "Copying $source_path to $dest_path"
        # Copy and then check if the copied file is different from what's already in git for that path
        # This is a bit tricky because we want to see if the *newly copied* file has changes compared to its committed version.
        
        # First, copy the file
        cp "$source_path" "$dest_path"

        # Now, check if this file has unstaged changes (meaning it's different from HEAD)
        if ! git diff --quiet HEAD -- "$dest_path"; then
            echo "Changes detected in $dest_filename."
            HAS_CHANGES=1
        fi
    else
        echo "Warning: Source file $source_path not found. Skipping."
    fi
done

if [ "$HAS_CHANGES" -eq 1 ]; then
    echo "Dotfile changes detected. Staging, committing, and pushing..."
    git add "$BACKUP_DIR/" # Stage all files in the backup directory
    git commit -m "Automated backup of dotfiles from Cloud Workstation: $(date +'%Y-%m-%d %H:%M:%S')"
    
    # Specify the remote and branch if necessary, default is usually 'origin main' or 'origin master'
    git push 
    
    if [ $? -eq 0 ]; then
        echo "Push successful."
    else
        echo "Error during git push."
    fi
else
    echo "No changes detected in tracked dotfiles within the repository. Nothing to commit or push."
fi

echo "Dotfile backup script finished."
exit 0

