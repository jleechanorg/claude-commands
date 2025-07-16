#!/bin/bash
# Learn command - Document learnings and improvements
# Usage: ./learn.sh [learning-description]

echo "=== Learning Documentation ==="
echo ""
echo "This command helps capture learnings and improvements."
echo ""

learning="${*:-No specific learning provided}"

# Create learning entry
timestamp=$(date +"%Y-%m-%d %H:%M:%S")
branch=$(git branch --show-current)

learning_file="learnings.md"
if [ ! -f "$learning_file" ]; then
    echo "# Learnings and Improvements" > "$learning_file"
    echo "" >> "$learning_file"
fi

# Append learning
echo "## $timestamp - Branch: $branch" >> "$learning_file"
echo "$learning" >> "$learning_file"
echo "" >> "$learning_file"

echo "✅ Learning documented in $learning_file"
echo ""
echo "Learning: $learning"
echo ""
echo "Next steps:"
echo "1. Review learnings periodically"
echo "2. Update documentation based on learnings"
echo "3. Share learnings with team"