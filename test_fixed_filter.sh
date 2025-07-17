#!/bin/bash

filter_sensitive_data() {
    local input_file="$1"
    local output_file="$2"
    
    # Create a temporary file for processing
    local temp_file=$(mktemp)
    
    # Copy the original file to temp
    cp "$input_file" "$temp_file"
    
    # Define sensitive patterns to filter out
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
    sed -i -E '/export.*_TOKEN.*=/s/=.*/=[REDACTED]/' "$temp_file"    # Only match _TOKEN (not TOKEN in middle)
    sed -i -E '/export.*AUTH_TOKEN.*=/s/=.*/=[REDACTED]/' "$temp_file"
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
}

# Test the function
filter_sensitive_data test_copilot_fixes.txt test_filtered_output.txt
echo "=== Original ==="
cat test_copilot_fixes.txt
echo -e "\n=== Filtered ==="
cat test_filtered_output.txt