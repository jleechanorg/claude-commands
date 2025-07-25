#!/bin/bash
# Example of proper inline comment reply for GitHub PRs

# Function to reply to an inline comment
reply_to_inline_comment() {
    local pr_number="$1"
    local comment_id="$2"
    local reply_body="$3"
    local repo="jleechanorg/worldarchitect.ai"

    echo "🔍 Fetching original comment details..."

    # Get the original comment details
    original_comment=$(gh api "/repos/${repo}/pulls/comments/${comment_id}")

    # Extract required fields
    commit_id=$(echo "$original_comment" | jq -r .commit_id)
    path=$(echo "$original_comment" | jq -r .path)
    line=$(echo "$original_comment" | jq -r .line)

    echo "📝 Posting inline reply to comment ${comment_id}..."
    echo "   Commit: ${commit_id}"
    echo "   Path: ${path}"
    echo "   Line: ${line}"

    # Post the reply
    gh api "/repos/${repo}/pulls/${pr_number}/comments" \
        -f body="${reply_body}" \
        -F in_reply_to="${comment_id}" \
        -f commit_id="${commit_id}" \
        -f path="${path}" \
        -F line="${line}"
}

# Example usage:
# reply_to_inline_comment 820 2221086905 "**[AI Responder]**\n\nYou're right! /pushl already exists..."
