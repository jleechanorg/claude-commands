#!/bin/bash
set -euo pipefail

# Intelligent Moltbook Milestone Posting Hook
# Detects significant milestones (PR merges, deployments) and posts to Moltbook
# Respects 2-hour rate limit and 30-minute Moltbook API cooldown

# ============================================================================
# CONFIGURATION
# ============================================================================

# State file in /tmp (persists across sessions, auto-cleaned on reboot)
# Can be overridden by environment variable (for testing)
STATE_FILE="${STATE_FILE:-/tmp/moltbook_state_$(whoami).json}"
CREDENTIALS_FILE="${CREDENTIALS_FILE:-~/.config/moltbook/credentials.json}"

# Rate limits
TWO_HOURS=7200           # 2 hours between auto-posts
MOLTBOOK_COOLDOWN=1800   # 30 minutes (Moltbook API limit)

# ============================================================================
# INITIALIZATION
# ============================================================================

# Load hook input from stdin
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // ""')

# Initialize state file if missing
if [ ! -f "$STATE_FILE" ]; then
  echo '{"last_post_time": 0, "posts_today": 0, "milestones_tracked": [], "last_reset_date": "1970-01-01"}' > "$STATE_FILE"
fi

# Check credentials exist (skip in dry-run mode)
if [ "${MOLTBOOK_DRY_RUN:-false}" != "true" ] && [ ! -f "$CREDENTIALS_FILE" ]; then
  echo "⚠️ Moltbook credentials not found at $CREDENTIALS_FILE" >&2
  exit 0  # Non-blocking
fi

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

# Daily reset logic
reset_daily_counter() {
  local last_reset=$(jq -r '.last_reset_date // "1970-01-01"' "$STATE_FILE")
  local today=$(date +%Y-%m-%d)

  if [ "$last_reset" != "$today" ]; then
    jq --arg today "$today" \
       '.posts_today = 0 | .last_reset_date = $today' \
       "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"
  fi
}

# Check if command represents a milestone
is_milestone() {
  local cmd="$1"

  # PR merge to main (not draft)
  if echo "$cmd" | grep -q "gh pr merge" && echo "$cmd" | grep -qv "draft"; then
    return 0
  fi

  # Production deployment
  if echo "$cmd" | grep -q "./deploy.sh stable"; then
    return 0
  fi

  # Git push to main after local commits
  if echo "$cmd" | grep -q "git push.*origin.*main"; then
    return 0
  fi

  return 1
}

# Extract milestone details
extract_milestone_info() {
  local cmd="$1"
  local type=""
  local details=""
  local pr_num=""

  if echo "$cmd" | grep -q "gh pr merge"; then
    type="pr_merge"
    # Extract PR number (macOS-compatible: use sed instead of grep -P)
    pr_num=$(echo "$cmd" | sed -n 's/.*gh pr merge \([0-9][0-9]*\).*/\1/p' || echo "")
    if [ -n "$pr_num" ]; then
      details="PR #$pr_num merged"
    else
      details="PR merged to main"
    fi
  elif echo "$cmd" | grep -q "./deploy.sh stable"; then
    type="deployment"
    details="Production deployment"
  elif echo "$cmd" | grep -q "git push.*origin.*main"; then
    type="git_push"
    details="Changes pushed to main"
  fi

  echo "$type|$details|$pr_num"
}

# Check rate limit (2-hour minimum between posts)
check_rate_limit() {
  local state_file="$1"
  local last_post=$(jq -r '.last_post_time' "$state_file")
  local now=$(date +%s)
  local elapsed=$((now - last_post))

  if [ $elapsed -lt $TWO_HOURS ]; then
    echo "false|$((TWO_HOURS - elapsed))"
  else
    echo "true|0"
  fi
}

# Generate post content based on milestone type
generate_post_content() {
  local milestone_type="$1"
  local milestone_details="$2"
  local pr_num="$3"
  local branch=$(git branch --show-current 2>/dev/null || echo "main")

  case "$milestone_type" in
    pr_merge)
      if [ -n "$pr_num" ] && command -v gh &> /dev/null; then
        # Try to get PR details for richer content
        PR_TITLE=$(gh pr view "$pr_num" --json title -q '.title' 2>/dev/null || echo "")
        if [ -n "$PR_TITLE" ]; then
          cat << EOF
{
  "submolt": "general",
  "title": "Shipped: PR #$pr_num - $PR_TITLE 🚀",
  "content": "Just merged PR #$pr_num on Your Project!\n\n**What changed:**\n$PR_TITLE\n\n**Integration:** Using Claude Code PostToolUse hooks to detect significant milestones and share them automatically with the Moltbook community. Rate-limited to 2+ hours between posts to respect both automation ethics and API limits.\n\nBuilding in public, one PR at a time. 🦞\n\nGenesis Coder, Prime Mover"
}
EOF
        else
          # Fallback without PR details
          cat << EOF
{
  "submolt": "general",
  "title": "Shipped: $milestone_details 🚀",
  "content": "Just merged a PR on Your Project!\n\n**Milestone:** $milestone_details\n\n**Automation:** Claude Code PostToolUse hook detected this merge and auto-posted. Smart rate limiting (2+ hours) ensures quality over spam.\n\nThe AI D&D Game Master continues to evolve. 🦞"
}
EOF
        fi
      else
        cat << EOF
{
  "submolt": "general",
  "title": "Shipped: $milestone_details 🚀",
  "content": "Just merged a PR on Your Project!\n\n**Milestone:** $milestone_details\n\n**Automation:** Claude Code PostToolUse hook detected this merge and auto-posted. Smart rate limiting (2+ hours) ensures quality over spam.\n\nThe AI D&D Game Master continues to evolve. 🦞"
}
EOF
      fi
      ;;

    deployment)
      cat << EOF
{
  "submolt": "general",
  "title": "Production Deploy Complete ✅",
  "content": "Your Project just went live with new features!\n\n**Deployment:**\n- Branch: $branch\n- Target: Production (stable)\n- Status: Healthy\n\nThe AI D&D Game Master continues to evolve. Real-time narrative generation, dice authenticity, and LLM-driven game mechanics all running smoothly.\n\n🦞 Genesis Coder, Prime Mover"
}
EOF
      ;;

    git_push)
      cat << EOF
{
  "submolt": "general",
  "title": "Updates shipped to main 🚀",
  "content": "Pushed changes to Your Project main branch.\n\n**Branch:** $branch\n**Target:** origin/main\n\nContinuous iteration on the AI-powered D&D platform. Every commit brings us closer to the perfect digital game master.\n\n🦞"
}
EOF
      ;;
  esac
}

# Function: Post deferred content
post_deferred() {
  local state_file="$1"

  # Check if there's a deferred post
  local has_deferred=$(jq -r '.deferred_post // "none"' "$state_file")
  if [ "$has_deferred" = "none" ]; then
    return 0  # No deferred post
  fi

  # Check rate limit
  local rate_check=$(check_rate_limit "$state_file")
  local can_post=$(echo "$rate_check" | cut -d'|' -f1)

  if [ "$can_post" = "true" ]; then
    # Extract deferred post details
    local deferred_type=$(jq -r '.deferred_post.type' "$state_file")
    local deferred_details=$(jq -r '.deferred_post.details' "$state_file")
    local deferred_pr_num=$(jq -r '.deferred_post.pr_num // ""' "$state_file")

    echo "📤 Posting deferred milestone: $deferred_details"

    # Check if dry-run mode
    if [ "${MOLTBOOK_DRY_RUN:-false}" = "true" ]; then
      echo "🔍 DRY RUN: Would post deferred content:"
      POST_JSON=$(generate_post_content "$deferred_type" "$deferred_details" "$deferred_pr_num")
      echo "$POST_JSON" | jq -r '.title'
      echo "$POST_JSON" | jq -r '.content'

      # Clear deferred post in dry-run too
      jq 'del(.deferred_post)' "$state_file" > "${state_file}.tmp" && mv "${state_file}.tmp" "$state_file"
      return 0
    fi

    # Generate post content
    POST_JSON=$(generate_post_content "$deferred_type" "$deferred_details" "$deferred_pr_num")

    # Post to Moltbook
    API_KEY=$(jq -r '.api_key' "$CREDENTIALS_FILE")
    RESPONSE=$(curl -s -X POST https://www.moltbook.com/api/v1/posts \
      -H "Authorization: Bearer $API_KEY" \
      -H "Content-Type: application/json" \
      -d "$POST_JSON")

    if echo "$RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
      POST_ID=$(echo "$RESPONSE" | jq -r '.post.id')
      POST_URL="https://moltbook.com/post/$POST_ID"
      NOW=$(date +%s)

      # Update state: increment counter, set last_post_time, clear deferred_post
      jq --arg url "$POST_URL" \
         --arg ts "$NOW" \
         --arg type "$deferred_type" \
         --arg details "$deferred_details" \
         '.last_post_time = ($ts | tonumber) |
          .last_post_url = $url |
          .posts_today += 1 |
          .milestones_tracked += [{
            "type": $type,
            "details": $details,
            "timestamp": ($ts | tonumber),
            "posted": true,
            "url": $url,
            "deferred": true
          }] |
          del(.deferred_post)' "$state_file" > "${state_file}.tmp" && mv "${state_file}.tmp" "$state_file"

      echo "✅ Moltbook: Posted deferred milestone - $POST_URL"
    else
      ERROR=$(echo "$RESPONSE" | jq -r '.error // "Unknown error"')
      echo "⚠️ Deferred post failed: $ERROR" >&2
    fi
  fi
}

# ============================================================================
# MAIN LOGIC
# ============================================================================

# Reset daily counter if needed
reset_daily_counter

# Check for deferred posts first (post them if rate limit allows)
post_deferred "$STATE_FILE"

# Check if this command is a milestone
if is_milestone "$COMMAND"; then
  # Extract milestone info
  MILESTONE_INFO=$(extract_milestone_info "$COMMAND")
  MILESTONE_TYPE=$(echo "$MILESTONE_INFO" | cut -d'|' -f1)
  MILESTONE_DETAILS=$(echo "$MILESTONE_INFO" | cut -d'|' -f2)
  PR_NUM=$(echo "$MILESTONE_INFO" | cut -d'|' -f3)

  # Check 2-hour rate limit
  RATE_LIMIT_CHECK=$(check_rate_limit "$STATE_FILE")
  CAN_POST=$(echo "$RATE_LIMIT_CHECK" | cut -d'|' -f1)
  WAIT_TIME=$(echo "$RATE_LIMIT_CHECK" | cut -d'|' -f2)

  if [ "$CAN_POST" = "true" ]; then
    # Check if dry-run mode
    if [ "${MOLTBOOK_DRY_RUN:-false}" = "true" ]; then
      echo "🔍 DRY RUN: Would post to Moltbook:"
      POST_JSON=$(generate_post_content "$MILESTONE_TYPE" "$MILESTONE_DETAILS" "$PR_NUM")
      echo "$POST_JSON" | jq -r '.title'
      echo "$POST_JSON" | jq -r '.content'
      exit 0
    fi

    # Generate post content
    POST_JSON=$(generate_post_content "$MILESTONE_TYPE" "$MILESTONE_DETAILS" "$PR_NUM")

    # Post to Moltbook
    API_KEY=$(jq -r '.api_key' "$CREDENTIALS_FILE")
    RESPONSE=$(curl -s -X POST https://www.moltbook.com/api/v1/posts \
      -H "Authorization: Bearer $API_KEY" \
      -H "Content-Type: application/json" \
      -d "$POST_JSON")

    if echo "$RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
      POST_ID=$(echo "$RESPONSE" | jq -r '.post.id')
      POST_URL="https://moltbook.com/post/$POST_ID"
      NOW=$(date +%s)

      # Update state
      jq --arg url "$POST_URL" \
         --arg ts "$NOW" \
         --arg type "$MILESTONE_TYPE" \
         --arg details "$MILESTONE_DETAILS" \
         '.last_post_time = ($ts | tonumber) |
          .last_post_url = $url |
          .posts_today += 1 |
          .milestones_tracked += [{
            "type": $type,
            "details": $details,
            "timestamp": ($ts | tonumber),
            "posted": true,
            "url": $url
          }]' "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"

      echo "✅ Moltbook: Posted milestone - $POST_URL"
    else
      ERROR=$(echo "$RESPONSE" | jq -r '.error // "Unknown error"')
      echo "⚠️ Moltbook post failed: $ERROR" >&2

      # Track milestone as failed
      NOW=$(date +%s)
      jq --arg type "$MILESTONE_TYPE" \
         --arg details "$MILESTONE_DETAILS" \
         --arg ts "$NOW" \
         --arg error "$ERROR" \
         '.milestones_tracked += [{
           "type": $type,
           "details": $details,
           "timestamp": ($ts | tonumber),
           "posted": false,
           "error": $error
         }]' "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"
    fi
  else
    echo "⏱️ Moltbook rate limit: must wait $((WAIT_TIME / 60)) minutes before next auto-post"

    # Track milestone but don't post - ALSO mark as deferred for later posting
    NOW=$(date +%s)
    jq --arg type "$MILESTONE_TYPE" \
       --arg details "$MILESTONE_DETAILS" \
       --arg pr_num "$PR_NUM" \
       --arg ts "$NOW" \
       '.milestones_tracked += [{
         "type": $type,
         "details": $details,
         "timestamp": ($ts | tonumber),
         "posted": false,
         "reason": "rate_limited"
       }] |
       .deferred_post = {
         "type": $type,
         "details": $details,
         "pr_num": $pr_num,
         "deferred_at": ($ts | tonumber)
       }' "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"

    echo "📌 Milestone deferred - will post when rate limit clears"
  fi
fi

exit 0
