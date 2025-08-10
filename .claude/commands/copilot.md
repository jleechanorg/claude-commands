# /copilot Command - Adaptive Linear PR Analysis

**Usage**: `/copilot [PR_NUMBER]`

**Purpose**: Adaptive PR analysis using smart guard-clause pattern that can handle broken states.

## 🎯 **DEFAULT BEHAVIOR** (No Arguments)
- ✅ **Automatically targets the current branch's PR**
- ✅ **Shows clear confirmation**: `🎯 Targeting current branch PR: #123`

**Examples**:
```bash
/copilot           # ← Applies to current branch PR (most common usage)  
/copilot 1062      # ← Applies to specific PR #1062
```

## 🚨 CRITICAL: EXECUTION GUARANTEE

**MANDATORY STARTUP PROTOCOL**:
```
🤖 /copilot - Starting adaptive PR analysis
🎯 Targeting: [Current branch PR: #123] OR [Specified PR: #456]
🔧 Using smart guard-clause pattern for reliability...
📊 Assessing PR state and building action plan...
🚀 Beginning adaptive workflow based on PR needs...
```

**NEVER FAIL SILENTLY**: Every execution MUST show visible progress through all steps
**ASSESS THEN ACT**: Smart guards assess problems and plan fixes instead of failing immediately
**ADAPTIVE EXECUTION**: Actions adapt to PR state - fix broken tests, resolve conflicts, process comments

## How It Works

The `/copilot` command uses **Adaptive Linear Processing with Smart Guards**:

1. **Assess PR State**: Comprehensive analysis of current condition
2. **Plan Actions**: Build prioritized action list based on assessment
3. **Execute Plan**: Carry out planned actions with rich error reporting
4. **Verify Results**: Confirm all actions completed successfully
5. **Report Status**: Clear final status with full diagnostic information

## 🚨 CRITICAL MANDATE: USE PROPER COMMENT FETCHING

**❌ FORBIDDEN SHORTCUTS**: NEVER use `gh pr view --json comments` or similar simplified GitHub API calls for comment collection
**✅ MANDATORY**: ALWAYS use the actual `/commentfetch` Python implementation for ALL comment collection
**🐛 BUG PREVENTION**: `gh pr view --json comments` only returns general issue comments and MISSES review comments entirely

**EVIDENCE**: Review comments (like `#discussion_rXXXXXXX` URLs) are only available via:
- ✅ `/commentfetch` → calls `gh api repos/owner/repo/pulls/PR/comments` (captures ALL comment types)  
- ❌ `gh pr view --json comments` → only returns general issue comments (INCOMPLETE)

**WHY THIS MATTERS**: A comment asking "see if commentreply catches this" was missed because the copilot workflow used the wrong API endpoint that doesn't include review comments.

## 🚨 ADAPTIVE WORKFLOW STEPS

### Step 1: PR State Assessment (MANDATORY)
```bash
# Get comprehensive PR state - single source of truth
pr_json=$(gh pr view $PR_NUMBER --json state,mergeable,statusCheckRollup,comments,reviews)
PR_STATE=$(echo "$pr_json" | jq -r '.state')
CI_STATE=$(echo "$pr_json" | jq -r '.statusCheckRollup.state // "PENDING"')
MERGEABLE=$(echo "$pr_json" | jq -r '.mergeable')
COMMENT_COUNT=$(echo "$pr_json" | jq '(.comments | length) + (.reviews | length)')

# Build action plan based on assessment
PLANNED_ACTIONS=()
COMPLETED_ACTIONS=()
HIGH_COMMENT_THRESHOLD=${COPILOT_HIGH_COMMENT_THRESHOLD:-30}  # Configurable threshold for high comment count processing
echo "📊 PR Assessment Results:"
echo "   State: $PR_STATE | CI: $CI_STATE | Mergeable: $MERGEABLE | Comments: $COMMENT_COUNT"

# Smart assessment logic
[[ "$PR_STATE" != "OPEN" ]] && { echo "❌ PR is not open - cannot proceed"; exit 1; }

if [[ "$CI_STATE" != "SUCCESS" ]]; then
    echo "🔧 CI issues detected - adding fix to plan"
    PLANNED_ACTIONS+=("fix_ci")
fi

if [[ "$MERGEABLE" == "CONFLICTING" ]]; then
    echo "🔧 Merge conflicts detected - adding resolution to plan"
    PLANNED_ACTIONS+=("resolve_conflicts")
fi

# Always fetch comments for comprehensive data
echo "📊 Comments detected ($COMMENT_COUNT) - always fetching for complete analysis"
PLANNED_ACTIONS+=("fetch_comments")

if [[ "$COMMENT_COUNT" -gt 0 ]]; then
    echo "💬 Comments require processing - adding to plan"
    PLANNED_ACTIONS+=("process_comments")
fi

# Always add sync and report
PLANNED_ACTIONS+=("sync_branch" "report_status")
echo "📋 Planned Actions: ${PLANNED_ACTIONS[*]}"
```

### Step 2: Execute Planned Actions (ADAPTIVE)
```bash
# Execute each planned action with rich error handling
for action in "${PLANNED_ACTIONS[@]}"; do
    echo "🚀 Executing: $action"
    
    case $action in
        "fix_ci")
            echo "🔧 Attempting to fix CI issues..."
            if /fixpr "$PR_NUMBER"; then
                echo "✅ CI fixes applied successfully"
                COMPLETED_ACTIONS+=("fix_ci")
            else
                echo "❌ CI fix failed - capturing diagnostics..."
                # Capture detailed error information (supported API)
                echo "ℹ️ CI failures:"
                gh pr view "$PR_NUMBER" --json statusCheckRollup -q '
                  .statusCheckRollup[]?
                  | select(.state=="FAILURE" or .conclusion=="FAILURE")
                  | {name: (.name // .context), detailsUrl: (.detailsUrl // .targetUrl)}'
                exit 1
            fi
            ;;
            
        "resolve_conflicts")
            echo "🔀 Attempting to resolve merge conflicts..."
            if /fixpr "$PR_NUMBER"; then
                echo "✅ Conflicts resolved successfully"
                COMPLETED_ACTIONS+=("resolve_conflicts")
            else
                echo "❌ Conflict resolution failed - manual intervention required"
                exit 1
            fi
            ;;

        "fetch_comments")
            echo "📊 Fetching comments and reviews for comprehensive analysis..."
            echo "🚨 CRITICAL: Using proper /commentfetch implementation (NOT gh pr view shortcuts)"
            if [[ "$COMMENT_COUNT" -gt "$HIGH_COMMENT_THRESHOLD" ]]; then
                echo "⚡ High comment count detected ($COMMENT_COUNT) - focusing on last $HIGH_COMMENT_THRESHOLD for efficiency"
                export COMMENTFETCH_LIMIT="$HIGH_COMMENT_THRESHOLD"
                export COMMENTFETCH_FOCUS="recent"
            else
                echo "📝 Standard comment count ($COMMENT_COUNT) - fetching all"
            fi
            
            # 🚨 MANDATORY: Use actual /commentfetch Python implementation
            # This captures ALL comment types: inline, general, review, and copilot
            # NEVER use gh pr view --json comments (incomplete - misses review comments)
            if /commentfetch "$PR_NUMBER"; then
                echo "✅ Comments fetched successfully with complete API coverage"
                COMPLETED_ACTIONS+=("fetch_comments")
            else
                echo "❌ Comment fetch failed - check commentfetch logs"
                exit 1
            fi
            ;;
            
        "process_comments")
            echo "💬 Processing comments..."
            echo "🚨 CRITICAL: Processing ALL comments including owner testing comments"
            echo "🔧 BUG FIX: No filtering by author - ALL comments get responses"
            if [[ "$COMMENT_COUNT" -gt "$HIGH_COMMENT_THRESHOLD" ]]; then
                echo "⚡ High comment count detected ($COMMENT_COUNT) - processing all systematically"
            fi
            
            # MANDATORY: Process ALL comments without filtering
            # Fixed bug where owner test comments were ignored
            echo "📋 Comment processing scope: ALL comments regardless of:"
            echo "   - Author (owner, bots, external reviewers)"
            echo "   - Content type (technical, testing, simple)"  
            echo "   - Purpose (feedback, debugging, validation)"
            
            if /commentreply "$PR_NUMBER"; then
                echo "✅ Comments processed successfully - ALL comments addressed"
                COMPLETED_ACTIONS+=("process_comments")
            else
                echo "❌ Comment processing failed - check commentreply logs"
                exit 1
            fi
            ;;
            
        "sync_branch")
            echo "🔍 Checking branch sync status..."
            # Atomic git check - refresh state before sync
            git fetch origin >/dev/null 2>&1
            BASE_BRANCH="${BASE_BRANCH:-$(gh pr view "$PR_NUMBER" --json baseRefName -q .baseRefName 2>/dev/null)}"
            if [ -z "$BASE_BRANCH" ] || [ "$BASE_BRANCH" = "null" ]; then
              BASE_BRANCH="$(gh repo view --json defaultBranchRef -q .defaultBranchRef.name 2>/dev/null || echo main)"
            fi
            : "${BASE_BRANCH:=main}"
            if git log --oneline "HEAD..origin/${BASE_BRANCH}" | head -1 | grep -q .; then
                echo "🔄 Syncing with base branch..."
                if /fixpr "$PR_NUMBER"; then
                    echo "✅ Branch synced successfully"
                    COMPLETED_ACTIONS+=("sync_branch")
                else
                    echo "❌ Branch sync failed"
                    exit 1
                fi
            else
                echo "✅ Branch already up to date"
                COMPLETED_ACTIONS+=("sync_branch")
            fi
            ;;
            
        "report_status")
            # Generate comprehensive status report
            ACTIONS_TAKEN_ARR=()
            for completed_action in "${COMPLETED_ACTIONS[@]}"; do
                case $completed_action in
                    "fix_ci") ACTIONS_TAKEN_ARR+=("- ✅ Fixed CI issues") ;;
                    "resolve_conflicts") ACTIONS_TAKEN_ARR+=("- ✅ Resolved merge conflicts") ;;
                    "fetch_comments") ACTIONS_TAKEN_ARR+=("- ✅ Fetched comments and reviews") ;;
                    "process_comments") ACTIONS_TAKEN_ARR+=("- ✅ Processed comments") ;;
                    "sync_branch") ACTIONS_TAKEN_ARR+=("- ✅ Synced with base branch") ;;
                esac
            done

            ACTIONS_TAKEN=""
            if [ ${#ACTIONS_TAKEN_ARR[@]} -gt 0 ]; then
                ACTIONS_TAKEN="\n$(printf "%s\n" "${ACTIONS_TAKEN_ARR[@]}")"
            fi

            # Re-fetch updated PR metadata
            status_json=$(gh pr view "$PR_NUMBER" --json state,statusCheckRollup,mergeable)
            final_state=$(jq -r '.state' <<<"$status_json")
            ci_state=$(jq -r '.statusCheckRollup.state // "PENDING"' <<<"$status_json")
            mergeable=$(jq -r '.mergeable' <<<"$status_json")
            SUCCESS_MSG="✅ **Copilot Analysis Complete - Adaptive Execution**

**Actions Taken**:$ACTIONS_TAKEN

**Final Status**: State: $final_state | CI: $ci_state | Mergeable: $mergeable
🎯 **Smart Guards**: Assessed issues and applied appropriate fixes  
📊 **Adaptive Flow**: Executed only necessary actions based on PR state"

            gh pr comment "$PR_NUMBER" --body "$SUCCESS_MSG"
            echo "✅ Final status posted to PR"
            ;;
    esac
done
```

## Key Benefits

- **Always Comprehensive**: Fetches all comment data for complete analysis
- **Smart Comment Handling**: Focuses on last 30 comments when PR has high activity
- **Adaptive Intelligence**: Handles broken tests, conflicts, and comments appropriately  
- **Rich Diagnostics**: Detailed error reporting with actionable information
- **Maintains Simplicity**: ~180 lines but much more capable and reliable
- **Linear Predictability**: Clear flow with smart decision points
- **Robust Error Handling**: Captures and reports detailed failure information  
- **Atomic Operations**: Fresh state checks prevent race conditions

## Smart Guards Pattern

Instead of rigid pass/fail guards, each step uses "assess → plan → act" logic:

**Pattern**:
```bash
# Assess the situation
if [[ condition_detected ]]; then
    echo "🔧 Issue detected - adding fix to plan"
    PLANNED_ACTIONS+=("fix_action")  
else
    echo "✅ No issues detected"
fi
```

This maintains linear predictability while adding intelligence to handle real-world PR problems instead of just rejecting them.

## Comment Handling Strategy

The copilot now always fetches comments for comprehensive analysis:

- **Always fetch**: Even if no comments, ensures complete PR data
- **Smart limiting**: When >30 comments, sets `COMMENTFETCH_LIMIT=30` and `COMMENTFETCH_FOCUS="recent"`
- **Environment variables**: Passes limits to `/commentfetch` for optimization
- **Comprehensive processing**: Still processes all actionable comments appropriately

**Key Fix**: Now handles broken tests by adding "fix_ci" to the action plan instead of immediately failing.