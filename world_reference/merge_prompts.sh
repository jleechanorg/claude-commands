#!/bin/bash

# merge_prompts.sh - Merge all markdown files from mvp_site/prompts/ into world_reference/

set -e

# Create world_reference directory if it doesn't exist
mkdir -p world_reference

# Output file
OUTPUT_FILE="world_reference/mvp_site_prompts_merged.md"

# Clear the output file
> "$OUTPUT_FILE"

echo "# MVP Site Prompts - Merged Collection" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "This file contains all markdown files from mvp_site/prompts/ merged together." >> "$OUTPUT_FILE"
echo "Generated on: $(date)" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Find all .md files in mvp_site/prompts/ and process them
find mvp_site/prompts/ -name "*.md" -type f | sort | while read -r file; do
    echo "Processing: $file"
    
    # Add a section header for each file
    echo "## File: $file" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    
    # Add the content of the file
    cat "$file" >> "$OUTPUT_FILE"
    
    # Add separator between files
    echo "" >> "$OUTPUT_FILE"
    echo "---" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
done

echo "✅ Merged prompts saved to: $OUTPUT_FILE"
echo "📊 Total files processed: $(find mvp_site/prompts/ -name "*.md" -type f | wc -l)"
echo "📝 Output file size: $(wc -l < "$OUTPUT_FILE") lines"