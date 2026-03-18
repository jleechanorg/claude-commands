#!/usr/bin/env bash
# Simple bash loop: poll gh status and CI, post @coderabbitai all good?
# No automation/ library — manage PRs directly in chat or run: ai_orch --agent-cli cursor --async --worktree "Fix PR #N..."
#
# Usage:
#   ./scripts/check-pr-status.sh        # loop forever, ping CR + sleep 5 min
#   ./scripts/check-pr-status.sh --once # run once and exit
#   PING_CODERABBIT=false ./scripts/check-pr-status.sh  # skip CR pings
#   FETCH_ALL=true ./scripts/check-pr-status.sh         # check all open (default: only TARGET_PRS)

set -euo pipefail

INTERVAL_SEC=300    # 5 min
ONCE=false
[[ "${1:-}" == "--once" ]] && ONCE=true
PING_CODERABBIT="${PING_CODERABBIT:-true}"

# PRs to check. FETCH_ALL=true fetches all open from REPOS.
TARGET_PRS=( "jleechanorg/your-project.com:5965" "jleechanorg/your-project.com:5966" "jleechanorg/your-project.com:5976" )
FETCH_ALL="${FETCH_ALL:-false}"
REPOS=( "jleechanorg/your-project.com" "jleechanorg/jleechanclaw" )

fetch_prs() {
  local prs=()
  for repo in "${REPOS[@]}"; do
    while IFS= read -r line; do
      [[ -z "$line" ]] && continue
      prs+=( "$repo:$line" )
    done < <(gh pr list -R "$repo" --state open --json number -q '.[].number' 2>/dev/null || true)
  done
  printf '%s\n' "${prs[@]}"
}

check_one() {
  local repo="$1"
  local num="$2"
  echo ""
  echo "══════════════════════════════════════════════════════════════"
  echo "  $repo #$num"
  echo "══════════════════════════════════════════════════════════════"
  echo ""

  gh pr view "$num" -R "$repo" --json state,title,url -q '"\(.state) | \(.title)\n\(.url)"' 2>/dev/null || echo "  (pr view failed)"

  echo ""
  echo "--- CI Checks ---"
  gh pr checks "$num" -R "$repo" 2>/dev/null | tail -20 || echo "  (no checks or failed)"

  echo ""
  echo "--- Recent Comments ---"
  gh api "repos/$repo/issues/$num/comments" --jq '.[-3:] | .[] | "  [\(.user.login)] \(.body | split("\n")[0])"' 2>/dev/null | tail -5 || echo "  (no comments or failed)"
  echo ""
}

while true; do
  echo ""
  echo "╔══════════════════════════════════════════════════════════════╗"
  echo "║  PR status check @ $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
  echo "╚══════════════════════════════════════════════════════════════╝"

  PRS=()
  if [[ "$FETCH_ALL" == "true" ]]; then
    while IFS= read -r line; do
      [[ -n "$line" ]] && PRS+=( "$line" )
    done < <(fetch_prs)
    PRS=( $(printf '%s\n' "${TARGET_PRS[@]}" "${PRS[@]}" | sort -u) )
  else
    PRS=( "${TARGET_PRS[@]}" )
  fi

  for entry in "${PRS[@]}"; do
    repo="${entry%%:*}"
    num="${entry##*:}"
    check_one "$repo" "$num"
    # Seek CodeRabbit approval (throttle: max once per PR per hour)
    if [[ "$PING_CODERABBIT" == "true" ]]; then
      marker="/tmp/check-pr-status.cr.${repo//\//_}.$num"
      now=$(date +%s)
      last=$(cat "$marker" 2>/dev/null || echo "0")
      if (( now - last >= 3600 )); then
        echo "  → Posting @coderabbitai all good?"
        if gh pr comment "$num" -R "$repo" --body "@coderabbitai all good?" 2>/dev/null; then
          echo "$now" > "$marker"
        else
          echo "  (comment failed)"
        fi
      else
        echo "  → CR ping skipped (throttled, next in $(( 3600 - (now - last) ))s)"
      fi
    fi
  done

  if [[ "$ONCE" == true ]]; then
    echo "Done (--once). ${#PRS[@]} PRs checked."
    exit 0
  fi
  echo ""
  echo "Next cycle in ${INTERVAL_SEC}s ($((${INTERVAL_SEC} / 60)) min) — ${#PRS[@]} PRs"
  sleep "$INTERVAL_SEC"
done
