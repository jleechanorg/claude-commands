#!/bin/bash

# This script creates a single text file snapshot of the entire repository.

# Define the name of the file that will contain the output.
OUTPUT_FILE="repo_snapshot.txt"

# Start with a clean slate by overwriting the file if it exists.
echo "Creating repository snapshot..."
echo "Generated on: $(date)" > "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Find all files in the current directory and subdirectories.
# Exclude the .git directory, venv, __pycache__, .bak files, and the output file itself.
# For each file found, run a loop.
find . -type f \
    -not -path "./.git/*" \
    -not -path "*/__pycache__/*" \
    -not -path "*/venv/*" \
    -not -name "*.bak" \
    -not -name "$OUTPUT_FILE" | while read -r filepath; do
    
    filename=$(basename "$filepath")

    # Print a clear separator and the file metadata to the output file.
    echo "--- FILE START ---" >> "$OUTPUT_FILE"
    echo "Location: $filepath" >> "$OUTPUT_FILE"
    echo "Name: $filename" >> "$OUTPUT_FILE"
    echo "--- CONTENT ---" >> "$OUTPUT_FILE"
    
    # Check if the current file is DejaVuSans.ttf
    if [[ "$filename" == "DejaVuSans.ttf" ]]; then
        echo "--- CONTENT SKIPPED (Binary Font File) ---" >> "$OUTPUT_FILE"
    else
        # Append the actual content of the file for other files.
        cat "$filepath" >> "$OUTPUT_FILE"
    fi
    
    # Print a separator at the end of the file content for clarity.
    # The two blank lines make the final text file easier to read.
    echo "" >> "$OUTPUT_FILE"
    echo "--- FILE END ---" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
done

echo "Snapshot complete."
echo "The file '$OUTPUT_FILE' has been created in your current directory."
echo "Please upload this file so I can analyze the state of the repository."
