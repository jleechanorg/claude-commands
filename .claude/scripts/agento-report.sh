#!/bin/bash
# agento-report.sh - Detailed PR status report with columns

set -uo pipefail
GH_TOKEN="${GITHUB_TOKEN:-$(gh auth token)}"
REPORT_FILE="/tmp/agento-report.md"

TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
echo "# agento PR Report — $TIMESTAMP" > "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Header
printf "| Status | PR | Title | Stage | CR Approved | Next Step |\n" >> "$REPORT_FILE"
printf "|--------|---|-------|-------|-------------|-----------|\n" >> "$REPORT_FILE"

# Counters
green=0 mergeable_nocr=0 conflict=0 ci_fail=0 pending=0

for REPO in "$GITHUB_REPOSITORY" "jleechanorg/jleechanclaw" "jleechanorg/agent-orchestrator"; do
    PR_LIST=$(curl -s -H "Authorization: Bearer $GH_TOKEN" "https://api.github.com/repos/$REPO/pulls?state=open&per_page=30")

    for row in $(echo "$PR_LIST" | jq -r '.[] | @base64'); do
        pr=$(echo "$row" | base64 -d)
        num=$(echo "$pr" | jq -r '.number')
        title=$(echo "$pr" | jq -r '.title')
        mergeable=$(echo "$pr" | jq -r '.mergeable')
        merge_state=$(echo "$pr" | jq -r '.mergeable_state // "null"')

        # GitHub lazily computes mergeable - re-fetch if null
        if [[ "$mergeable" == "null" ]]; then
            sleep 1
            pr=$(curl -s -H "Authorization: Bearer $GH_TOKEN" "https://api.github.com/repos/$REPO/pulls/$num")
            mergeable=$(echo "$pr" | jq -r '.mergeable')
            merge_state=$(echo "$pr" | jq -r '.mergeable_state // "null"')
        fi

        # Check CR
        cr_json=$(curl -s -H "Authorization: Bearer $GH_TOKEN" "https://api.github.com/repos/$REPO/pulls/$num/reviews")
        cr_approved=$(echo "$cr_json" | jq -r '[.[] | select(.user.login == "coderabbitai[bot]" and .state == "APPROVED")] | length')
        if [[ "$cr_approved" == "0" ]]; then
            comments_json=$(curl -s -H "Authorization: Bearer $GH_TOKEN" "https://api.github.com/repos/$REPO/issues/$num/comments")
            cr_approved=$(echo "$comments_json" | jq -r '[.[] | select(.user.login == "coderabbitai[bot]") | select(.body | test("looks good|all good|LGTM"; "i"))] | length')
            [[ "$cr_approved" -gt 0 ]] && cr_approved=1
        fi

        # Normalize cr_approved to 0 or 1 (handles multiple APPROVED reviews)
        [[ "$cr_approved" -gt 1 ]] && cr_approved=1

        CR_ICON="❌"
        [[ "$cr_approved" -ge 1 ]] && CR_ICON="✅"

        # Check for unresolved review threads (excluding bot comments)
        unresolved_count=0
        if [[ "$mergeable" == "true" && "$cr_approved" -ge 1 ]]; then
            threads_json=$(curl -s -H "Authorization: Bearer $GH_TOKEN" "https://api.github.com/repos/$REPO/pulls/$num/threads")
            unresolved_count=$(echo "$threads_json" | jq -r '[.[] | select(.resolved_at == null)] | length' 2>/dev/null || echo "0")
        fi

        # Status determination - construct URL from repo to ensure correctness
        URL="https://github.com/${REPO}/pull/${num}"
        if [[ "$mergeable" == "null" || "$merge_state" == "null" ]]; then
            STATUS="⏳"
            STAGE="pending_calc"
            NEXT="push to trigger merge calc"
            ((pending++))
        elif [[ "$merge_state" == "dirty" ]]; then
            STATUS="❌"
            STAGE="conflict"
            NEXT="rebase on main"
            ((conflict++))
        elif [[ "$merge_state" == "unstable" ]]; then
            STATUS="⚠️"
            STAGE="ci_failing"
            NEXT="fix CI"
            ((ci_fail++))
        elif [[ "$mergeable" == "true" && "$cr_approved" -ge 1 && "$unresolved_count" -eq 0 ]]; then
            STATUS="✅"
            STAGE="ready"
            NEXT="merge now"
            ((green++))
        elif [[ "$mergeable" == "true" && "$cr_approved" -ge 1 && "$unresolved_count" -gt 0 ]]; then
            STATUS="🔶"
            STAGE="blocked_by_conversations"
            NEXT="resolve review threads"
            ((mergeable_nocr++))
        elif [[ "$mergeable" == "true" ]]; then
            STATUS="🔶"
            STAGE="mergeable"
            NEXT="@coderabbitai all good?"
            ((mergeable_nocr++))
        else
            STATUS="❓"
            STAGE="$merge_state"
            NEXT="check manually"
        fi

        printf "| %s | [#%d](%s) %s | %s | %s | %s |\n" \
            "$STATUS" "$num" "$URL" "$title" "$STAGE" "$CR_ICON" "$NEXT" >> "$REPORT_FILE"
    done
done

echo "" >> "$REPORT_FILE"
echo "---" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
printf "**Summary:** ✅GREEN:$green 🔶NEEDS_CR:$mergeable_nocr ❌CONFLICT:$conflict ⚠️CI_FAIL:$ci_fail ⏳PENDING:$pending\n" >> "$REPORT_FILE"

cat "$REPORT_FILE"
