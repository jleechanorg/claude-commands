#!/bin/bash

# This script backs up specified dotfiles to a directory within this Git repository,
# then commits and pushes those changes if any modifications or new files are detected
# in the backup directory.

# Ensure we are in the script's directory (which should be the repo root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || { echo "Failed to cd to script directory $SCRIPT_DIR"; exit 1; }

echo "Current working directory: $(pwd)"

# Define the backup destination directory within this repo
BACKUP_DIR="./dotfiles_backup" # Relative to the repo root

# Create the backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# --- List of dotfiles to back up ---
# Format: "Source Path in Home Dir|Destination Filename in BACKUP_DIR"
DOTFILES_TO_BACKUP=(
    "$HOME/.bashrc|bashrc_pc.txt"
    "$HOME/.gitconfig|gitconfig_pc.txt" # Example
    # Add more files here if needed:
    # "$HOME/.vimrc|vimrc_cloudworkstation.txt"
)
# --- End of list ---

echo "Starting dotfile backup process..."

# Function to filter sensitive information from files
filter_sensitive_data() {
    local input_file="$1"
    local output_file="$2"

    # Use sed to remove lines containing sensitive patterns
    sed -E '
        # Remove lines with tokens, keys, passwords
        /^[[:space:]]*(export[[:space:]]+)?[A-Z_]*[Tt][Oo][Kk][Ee][Nn][[:space:]]*=/d
        /^[[:space:]]*(export[[:space:]]+)?[A-Z_]*[Kk][Ee][Yy][[:space:]]*=/d
        /^[[:space:]]*(export[[:space:]]+)?[A-Z_]*[Pp][Aa][Ss][Ss][Ww]?[Oo]?[Rr]?[Dd]?[[:space:]]*=/d
        /^[[:space:]]*(export[[:space:]]+)?[A-Z_]*[Ss][Ee][Cc][Rr][Ee][Tt][[:space:]]*=/d
        /^[[:space:]]*(export[[:space:]]+)?[A-Z_]*[Aa][Pp][Ii][[:space:]]*=/d
        /^[[:space:]]*(export[[:space:]]+)?[A-Z_]*[Cc][Rr][Ee][Dd][[:space:]]*=/d
        # Remove webhook URLs and sensitive URLs
        /^[[:space:]]*(export[[:space:]]+)?[A-Z_]*[Ww][Ee][Bb][Hh][Oo][Oo][Kk][[:space:]]*=/d
        /^[[:space:]]*(export[[:space:]]+)?[A-Z_]*[Uu][Rr][Ll][[:space:]]*=.*hooks\.slack\.com/d
        /^[[:space:]]*(export[[:space:]]+)?SLACK_WEBHOOK_URL[[:space:]]*=/d
        # Remove email/username patterns if they look sensitive
        /^[[:space:]]*(export[[:space:]]+)?[A-Z_]*[Ee][Mm][Aa][Ii][Ll][[:space:]]*=/d
        /^[[:space:]]*(export[[:space:]]+)?[A-Z_]*[Uu][Ss][Ee][Rr][[:space:]]*=/d
        # Remove test credentials
        /^[[:space:]]*(export[[:space:]]+)?TEST_PASSWORD[[:space:]]*=/d
        # Remove Firebase UIDs and test credentials
        /^[[:space:]]*(export[[:space:]]+)?FIREBASE.*UID[[:space:]]*=/d
        /^[[:space:]]*(export[[:space:]]+)?.*TEST.*UID[[:space:]]*=/d
        # Remove GCP Project IDs
        /^[[:space:]]*(export[[:space:]]+)?.*PROJECT_ID[[:space:]]*=/d
        /^[[:space:]]*(export[[:space:]]+)?GOOGLE_CLOUD_PROJECT[[:space:]]*=/d
        # Remove Firebase configuration values
        /^[[:space:]]*(export[[:space:]]+)?.*FIREBASE.*ID[[:space:]]*=/d
        /^[[:space:]]*(export[[:space:]]+)?.*MEASUREMENT_ID[[:space:]]*=/d
        /^[[:space:]]*(export[[:space:]]+)?.*MESSAGING_SENDER_ID[[:space:]]*=/d
        /^[[:space:]]*(export[[:space:]]+)?.*FIREBASE.*DOMAIN[[:space:]]*=/d
        /^[[:space:]]*(export[[:space:]]+)?.*FIREBASE.*BUCKET[[:space:]]*=/d
        # Remove secret names
        /^[[:space:]]*(export[[:space:]]+)?.*SECRET_NAME[[:space:]]*=/d
        # Remove GitHub/Git credential helpers with tokens
        /^\[credential/,/^\[/{ /helper.*token/d; /username.*token/d; }
        # Remove real names from gitconfig
        /^[[:space:]]*name[[:space:]]*=/d
        # Remove specific sensitive values (add more patterns as needed)
        /github\.com.*@/d
        /gitlab\.com.*@/d
    ' "$input_file" | sed -E 's|/Users/[^/]+/|/Users/<redacted>/|g' > "$output_file"

    echo "  → Filtered sensitive data from $(basename "$input_file")"
}

# Copy all specified dotfiles first with sensitive data filtering
for entry in "${DOTFILES_TO_BACKUP[@]}"; do
    IFS='|' read -r source_path dest_filename <<< "$entry"

    if [ -z "$source_path" ] || [ -z "$dest_filename" ]; then
        echo "Warning: Invalid DOTFILES_TO_BACKUP entry '$entry'. Skipping."
        continue
    fi

    dest_path="$BACKUP_DIR/$dest_filename"

    if [ -f "$source_path" ]; then
        echo "Processing $source_path to $dest_path"

        # Filter sensitive data instead of direct copy
        filter_sensitive_data "$source_path" "$dest_path"

        # Verify the filtered file was created successfully
        if [ ! -f "$dest_path" ]; then
            echo "Error: Failed to create filtered backup of $source_path"
            exit 1
        fi
    else
        echo "Warning: Source file $source_path not found. Skipping."
    fi
done

# Now, check if the backup directory has any changes (modified, new, or deleted files)
# that Git would commit.
# Stage all changes within the BACKUP_DIR first to correctly detect untracked files as changes.
git add "$BACKUP_DIR/"

# Check if there are any staged changes specifically within BACKUP_DIR
# `git diff --cached --quiet -- "$BACKUP_DIR/"` checks staged changes.
# `git diff --quiet HEAD -- "$BACKUP_DIR/"` checks working tree vs HEAD (for already tracked files).
# A simpler way after `git add` is to check `git status --porcelain "$BACKUP_DIR/"`.
if [ -n "$(git status --porcelain "$BACKUP_DIR/")" ]; then
    echo "Dotfile changes detected in $BACKUP_DIR. Committing and pushing..."
    # The files in BACKUP_DIR are already staged due to the `git add` above.
    # We might want to add the script itself if it changed, though that's usually a manual commit.

    git commit -m "Automated backup of dotfiles from Cloud Workstation: $(date +'%Y-%m-%d %H:%M:%S')"

    # Specify the remote and branch if necessary, default is usually 'origin main' or 'origin master'
    git push

    if [ $? -eq 0 ]; then
        echo "Push successful."
    else
        echo "Error during git push."
    fi
else
    echo "No changes detected in $BACKUP_DIR to back up. Nothing to commit or push."
    # If there were no changes in BACKUP_DIR, we might want to unstage them if `git add` was broad
    # However, since we did `git add "$BACKUP_DIR/"`, only things within it were staged.
    # If you did `git add .` before this check, you'd need `git reset HEAD "$BACKUP_DIR/"` here.
fi

echo "Dotfile backup script finished."
exit 0
