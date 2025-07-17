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
# Format: "Source Path in Home Dir" "Destination Filename in BACKUP_DIR"
declare -A DOTFILES_TO_BACKUP=(
    ["$HOME/.bashrc"]="bashrc_pc.txt"
    ["$HOME/.gitconfig"]="gitconfig_pc.txt"
    ["$HOME/.gemini_api_key_secret"]="gemini_api_key_secret_pc.txt"
    # Add more files here if needed:
    # ["$HOME/.vimrc"]="vimrc_cloudworkstation.txt"
)
# --- End of list ---

echo "Starting dotfile backup process..."

# Function to filter sensitive data from dotfiles
filter_sensitive_data() {
    local input_file="$1"
    local output_file="$2"
    
    # Create a temporary file for processing
    local temp_file=$(mktemp)
    
    # Copy the original file to temp
    cp "$input_file" "$temp_file"
    
    # Define sensitive patterns to filter out
    # Note: These patterns will be replaced with [REDACTED] for security
    local sensitive_patterns=(
        # API Keys - Various formats
        "sk-ant-api[0-9][0-9]-[A-Za-z0-9_-]+"              # Anthropic API keys
        "sk-[A-Za-z0-9]{48}"                               # OpenAI API keys
        "AIza[0-9A-Za-z_-]{34,39}"                         # Google/Gemini API keys (variable length)
        "ya29\.[0-9A-Za-z_-]+"                             # Google OAuth tokens
        "AKIA[0-9A-Z]{16}"                                 # AWS Access Keys
        "ASIA[0-9A-Z]{16}"                                 # AWS Session Keys
        "ghp_[A-Za-z0-9]{36}"                              # GitHub Personal Access Tokens
        "gho_[A-Za-z0-9]{36}"                              # GitHub OAuth tokens
        "ghu_[A-Za-z0-9]{36}"                              # GitHub User tokens
        "ghs_[A-Za-z0-9]{36}"                              # GitHub Server tokens
        "ghr_[A-Za-z0-9]{36}"                              # GitHub Refresh tokens
        
        # Generic patterns for common sensitive data
        "['\"][A-Za-z0-9+/]{40,}['\"]"                     # Base64-like long strings in quotes
        "bearer [A-Za-z0-9._-]+"                           # Bearer tokens
        "token [A-Za-z0-9._-]+"                            # Token prefixes
    )
    
    # Apply filtering for each pattern
    for pattern in "${sensitive_patterns[@]}"; do
        sed -i -E "s|$pattern|[REDACTED]|g" "$temp_file"
    done
    
    # Also filter lines containing sensitive environment variable patterns
    sed -i -E '/export.*API_KEY.*=/s/=.*/=[REDACTED]/' "$temp_file"
    sed -i -E '/export.*SECRET.*=/s/=.*/=[REDACTED]/' "$temp_file"
    sed -i -E '/export.*PASSWORD.*=/s/=.*/=[REDACTED]/' "$temp_file"
    # Only filter actual tokens, not config values like MAX_OUTPUT_TOKENS
    sed -i -E '/export.*(AUTH_TOKEN|ACCESS_TOKEN|REFRESH_TOKEN|SESSION_TOKEN|BEARER_TOKEN).*=/s/=.*/=[REDACTED]/' "$temp_file"
    sed -i -E '/export.*PASS.*=/s/=.*/=[REDACTED]/' "$temp_file"
    sed -i -E '/export.*ACCESS_KEY.*=/s/=.*/=[REDACTED]/' "$temp_file"
    sed -i -E '/export.*GEMINI.*=/s/=.*/=[REDACTED]/' "$temp_file"
    
    # Add header to indicate this file has been filtered
    {
        echo "# ======================================================================"
        echo "# FILTERED DOTFILE BACKUP - $(date +'%Y-%m-%d %H:%M:%S')"
        echo "# Original file: $input_file"
        echo "# Sensitive data (API keys, tokens, passwords) has been redacted"
        echo "# ======================================================================"
        echo ""
        cat "$temp_file"
    } > "$output_file"
    
    # Clean up temp file
    rm -f "$temp_file"
    
    echo "  → Filtered sensitive data from $(basename "$input_file")"
}

# Copy all specified dotfiles with sensitive data filtering
for source_path in "${!DOTFILES_TO_BACKUP[@]}"; do
    dest_filename="${DOTFILES_TO_BACKUP[$source_path]}"
    dest_path="$BACKUP_DIR/$dest_filename"

    if [ -f "$source_path" ]; then
        echo "Processing $source_path to $dest_path"
        filter_sensitive_data "$source_path" "$dest_path"
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
