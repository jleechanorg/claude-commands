# /copilot_backup - Backup Orchestrator (thin wrapper)

**Purpose**: Fallback orchestrator that delegates to existing commands (/commentfetch, /fixpr, /commentreply, /commentcheck) without reimplementing their logic. See linked docs.

## 🚨 Orchestration Protocol - Delegate to Existing Commands

**ARCHITECTURE**: Thin wrapper that orchestrates existing copilot commands without duplication

```bash
# Initialize variables for orchestration tracking
COVERAGE_RESULT=1
PR_NUMBER=${1:-$(gh pr view --json number --jq .number)}

# Phase 1: Fetch Comments (delegate to /commentfetch)
echo "🔄 Phase 1: Delegating to /commentfetch..."
/commentfetch "$PR_NUMBER" || { echo "❌ Comment fetch failed"; exit 1; }

# Phase 2: Fix Issues (delegate to /fixpr)
echo "🔄 Phase 2: Delegating to /fixpr..."
/fixpr "$PR_NUMBER" || { echo "❌ Issue fixes failed"; exit 1; }

# Phase 3: Generate and Post Replies (delegate to /commentreply)
echo "🔄 Phase 3: Delegating to /commentreply..."
/commentreply || { echo "❌ Comment reply failed"; exit 1; }

# Phase 4: Verify Coverage (delegate to /commentcheck)
echo "🔄 Phase 4: Delegating to /commentcheck..."
if /commentcheck "$PR_NUMBER"; then
    COVERAGE_RESULT=0
    echo "✅ Backup orchestration complete with full coverage"
else
    echo "❌ Coverage verification failed"
fi

exit $COVERAGE_RESULT
```

**Links to Primary Commands**:
- [/commentfetch](./commentfetch.md) - Comment data collection
- [/fixpr](./fixpr.md) - Issue resolution and fixes
- [/commentreply](./commentreply.md) - Response generation and posting
- [/commentcheck](./commentcheck.md) - Coverage verification

## Orchestration Benefits

**✅ No Duplication**: Delegates to existing tested commands
**✅ Maintainability**: Changes to core commands automatically inherited
**✅ Reliability**: Leverages proven implementations
**✅ Simplicity**: Clear orchestration pattern without reimplementing logic

**See Individual Command Documentation**:
- All validation, retry, and processing logic implemented in respective commands
- Error handling patterns documented in primary command files
- Security and type safety maintained by delegated commands
