#!/usr/bin/env bash
# metrics_summary.sh - Analyze token optimization logs and generate impact report
#
# Usage: ./metrics_summary.sh [log_file]

set -euo pipefail

# Setup logging - use dynamic project root detection (matching PreToolUse.sh)
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo "/tmp")
PROJECT_NAME=$(basename "$PROJECT_ROOT" 2>/dev/null || echo "unknown-project")
BRANCH=$(git branch --show-current 2>/dev/null || echo 'unknown')
LOG_FILE="${1:-/tmp/${PROJECT_NAME}/${BRANCH}/hook_modifications.log}"
WARNINGS_LOG_FILE="/tmp/${PROJECT_NAME}/${BRANCH}/session_warnings.log"

if [ ! -f "$LOG_FILE" ]; then
  echo "No log file found at $LOG_FILE"
  exit 1
fi

echo "📊 Token Optimization Impact Report"
echo "==================================="
echo "Source: $LOG_FILE"
echo "Date: $(date)"
echo ""

# Constants
TOKENS_PER_LINE=10
TOKENS_PER_DIFF=500
COST_PER_M_TOKENS=3 # $3.00 blended (approx)

# Process hook modifications log with jq
STATS=$(jq -s '
  reduce .[] as $item (
    {
      read_count: 0,
      read_lines_saved: 0,
      diff_count: 0,
      warnings_count: 0,
      sessions: {}
    };
    
    # Process item
    if $item.tool == "Read" then
      .read_count += 1 |
      .read_lines_saved += ($item.original_lines - $item.modified_lines) |
      if $item.session_id then
        # Initialize session object if it doesn't exist
        if (.sessions[$item.session_id] | length) == 0 then
          .sessions[$item.session_id] = {read_count: 0, read_saved: 0, diff_count: 0}
        else . end |
        .sessions[$item.session_id].read_count += 1 |
        .sessions[$item.session_id].read_saved += ($item.original_lines - $item.modified_lines)
      else . end
    elif $item.tool == "Bash" and $item.optimization == "git_diff_minimal" then
      .diff_count += 1 |
      if $item.session_id then
        # Initialize session object if it doesn't exist
        if (.sessions[$item.session_id] | length) == 0 then
          .sessions[$item.session_id] = {read_count: 0, read_saved: 0, diff_count: 0}
        else . end |
        .sessions[$item.session_id].diff_count += 1
      else . end
    else
      .
    end
  )
' "$LOG_FILE")

# Count warnings from session_warnings.log (separate file)
if [ -f "$WARNINGS_LOG_FILE" ]; then
  WARN_COUNT_FROM_FILE=$(jq -s 'length' "$WARNINGS_LOG_FILE" 2>/dev/null || echo "0")
  # Merge warnings count into stats
  STATS=$(echo "$STATS" | jq --argjson warn_count "$WARN_COUNT_FROM_FILE" '.warnings_count = $warn_count')
else
  STATS=$(echo "$STATS" | jq '.warnings_count = 0')
fi

READ_COUNT=$(echo "$STATS" | jq '.read_count')
READ_SAVED=$(echo "$STATS" | jq '.read_lines_saved')
DIFF_COUNT=$(echo "$STATS" | jq '.diff_count')
WARN_COUNT=$(echo "$STATS" | jq '.warnings_count')

# Calculate Totals
READ_TOKEN_SAVINGS=$((READ_SAVED * TOKENS_PER_LINE))
DIFF_TOKEN_SAVINGS=$((DIFF_COUNT * TOKENS_PER_DIFF))
TOTAL_SAVINGS=$((READ_TOKEN_SAVINGS + DIFF_TOKEN_SAVINGS))

if command -v bc >/dev/null 2>&1; then
  TOTAL_COST_SAVINGS=$(echo "scale=4; $TOTAL_SAVINGS / 1000000 * $COST_PER_M_TOKENS" | bc)
else
  TOTAL_COST_SAVINGS=$(awk "BEGIN {printf \"%.4f\", $TOTAL_SAVINGS / 1000000 * $COST_PER_M_TOKENS}")
fi

echo "📈 Cumulative Savings"
echo "---------------------"
printf "Total Estimated Tokens Saved: %d\n" "$TOTAL_SAVINGS"
printf "Estimated Cost Savings:       $%.4f\n" "$TOTAL_COST_SAVINGS"
echo ""

echo "🔍 Breakdown by Optimization"
echo "----------------------------"
echo "1. Large File Reads"
printf "   - Count:             %d\n" "$READ_COUNT"
printf "   - Lines Skipped:     %d\n" "$READ_SAVED"
printf "   - Est. Tokens Saved: %d\n" "$READ_TOKEN_SAVINGS"
echo ""
echo "2. Git Diff Minimization"
printf "   - Count:             %d\n" "$DIFF_COUNT"
printf "   - Est. Tokens Saved: %d (assumed %d/op)\n" "$DIFF_TOKEN_SAVINGS" "$TOKENS_PER_DIFF"
echo ""
echo "3. Session Health"
printf "   - Warnings Issued:   %d\n" "$WARN_COUNT"
echo ""

echo "📋 Top Sessions by Impact"
echo "-------------------------"
echo "$STATS" | jq -r '
  .sessions | to_entries | sort_by(-(.value.read_saved * 10 + .value.diff_count * 500)) | limit(5; .[]) |
  "Session: " + .key + "\n" +
  "  - Read Opts: " + (.value.read_count//0|tostring) + " (Saved: " + (.value.read_saved//0|tostring) + " lines)\n" +
  "  - Diff Opts: " + (.value.diff_count//0|tostring) + "\n" +
  "  - Est. Tokens: " + ((.value.read_saved//0 * 10 + .value.diff_count//0 * 500)|tostring) + "\n"
'
echo ""

# Trend Analysis (Last 5 entries)
echo "🕒 Recent Optimizations"
echo "-----------------------"
tail -n 5 "$LOG_FILE" | jq -r '
  "[" + .timestamp + "] " +
  if .tool == "Read" then
    "Read: " + .file + " (" + (.original_lines|tostring) + "->" + (.modified_lines|tostring) + " lines, -" + (.reduction_pct|tostring) + "%)"
  elif .tool == "Bash" then
    "Bash: " + .optimization
  else
    "Warning: " + (.messages|tostring) + " msgs"
  end
' 2>/dev/null || echo "(Some log entries could not be parsed)"
