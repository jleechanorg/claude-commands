---
description: "/benchg-ts - TypeScript Migration Benchmark: Genesis vs Ralph"
type: orchestration
execution_mode: immediate
---
# /benchg-ts - TypeScript Migration Benchmark: Genesis vs Ralph

**Command Summary**: Execute concurrent TypeScript migration benchmarks comparing Genesis and Ralph orchestration systems.

## Prerequisites
- WorldAI Genesis installation
- Ralph Orchestrator installation
- TypeScript migration test cases in `testing_llm/`
- Valid credentials in `.env`

## Execution

```bash
echo "🔍 PREREQUISITE VERIFICATION"
echo "============================"

# Environment-configurable variables with defaults
PROJECTS_DIR="${PROJECTS_DIR:-$HOME/projects}"
PROJECTS_OTHER_DIR="${PROJECTS_OTHER_DIR:-$HOME/projects_other}"
WORKTREE_RALPH_DIR="${WORKTREE_RALPH_DIR:-$PROJECTS_DIR/worktree_ralph}"

# Verify source repository
if [[ ! -d "$WORKTREE_RALPH_DIR" ]]; then
    echo "❌ Error: Source repository not found at $WORKTREE_RALPH_DIR"
    exit 1
fi
echo "✅ Source repository found"

# Verify credentials
if [[ ! -f "$WORKTREE_RALPH_DIR/testing_http/testing_full/.env" ]]; then
    echo "❌ Error: Credentials not found at $WORKTREE_RALPH_DIR/testing_http/testing_full/.env"
    exit 1
fi
echo "✅ Credentials found"

# Verify engineering design document
if [[ ! -f "$WORKTREE_RALPH_DIR/roadmap/mvp_site_typescript_migration_eng_design.md" ]]; then
    echo "❌ Error: Engineering design not found"
    exit 1
fi
echo "✅ Engineering design found"

# Verify test cases
TEST_CASE_COUNT=$(find "$WORKTREE_RALPH_DIR/testing_llm" -name "*.md" 2>/dev/null | wc -l)
if [[ $TEST_CASE_COUNT -eq 0 ]]; then
    echo "❌ Error: No test cases found in testing_llm/"
    exit 1
fi
echo "✅ Found $TEST_CASE_COUNT test cases"

# Verify Ralph installation
if [[ ! -d "$PROJECTS_OTHER_DIR/ralph-orchestrator" ]]; then
    echo "❌ Error: Ralph installation not found at $PROJECTS_OTHER_DIR/ralph-orchestrator"
    exit 1
fi
echo "✅ Ralph installation found"

# Verify Genesis installation
if [[ ! -f "$WORKTREE_RALPH_DIR/genesis/genesis.py" ]]; then
    echo "❌ Error: Genesis installation not found"
    exit 1
fi
echo "✅ Genesis installation found"

# Verify benchmark goal files
if [[ ! -f "$WORKTREE_RALPH_DIR/roadmap/genesis_typescript_migration_benchmark.md" ]]; then
    echo "❌ Error: Genesis benchmark goal file missing"
    exit 1
fi
if [[ ! -f "$WORKTREE_RALPH_DIR/roadmap/ralph_typescript_migration_benchmark.md" ]]; then
    echo "❌ Error: Ralph benchmark goal file missing"
    exit 1
fi
echo "✅ Benchmark goal files found"

# Verify target directories don't exist
if [[ -d "$PROJECTS_OTHER_DIR/worldai_genesis2" ]]; then
    echo "❌ Error: Target directory worldai_genesis2 already exists"
    echo "   Run: rm -rf \"$PROJECTS_OTHER_DIR/worldai_genesis2\""
    exit 1
fi
if [[ -d "$PROJECTS_OTHER_DIR/worldai_ralph2" ]]; then
    echo "❌ Error: Target directory worldai_ralph2 already exists"
    echo "   Run: rm -rf \"$PROJECTS_OTHER_DIR/worldai_ralph2\""
    exit 1
fi
echo "✅ Clean state verified - no existing benchmark directories"

echo ""
echo "🏆 TYPESCRIPT MIGRATION BENCHMARK: Genesis vs Ralph"
echo "===================================================="
echo ""
echo "📋 Configuration:"
echo "  Source: $PROJECT_ROOT"
echo "  Genesis Target: $PROJECTS_OTHER_DIR/worldai_genesis2"
echo "  Ralph Target: $PROJECTS_OTHER_DIR/worldai_ralph2"
echo "  Max Iterations: 50 per agent"
echo "  Test Cases: $TEST_CASE_COUNT files in testing_llm/"
echo "  Log File: $BENCHMARK_LOG"
echo ""

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BENCHMARK_LOG="/tmp/ts_migration_benchmark_$TIMESTAMP.log"

echo "🚀 PHASE 1: GENESIS EXECUTION"
echo "=================================="
echo ""

GENESIS_SESSION="genesis-ts-migration-$(date +%Y%m%d-%H%M%S)"
GENESIS_DIR="$PROJECTS_OTHER_DIR/worldai_genesis2"

echo "📋 Launching Genesis with orchestration command:"
echo "   Session: $GENESIS_SESSION"
echo "   Target: $GENESIS_DIR"
echo "   Goal File: roadmap/genesis_typescript_migration_benchmark.md"
echo ""

# Execute Genesis using /gene command
cd "$WORKTREE_RALPH_DIR"

# Create Genesis orchestration command
python3 genesis/genesis.py \
    --session "$GENESIS_SESSION" \
    --goal roadmap/genesis_typescript_migration_benchmark.md \
    --output-dir "$GENESIS_DIR" \
    --max-iterations 50 \
    --verbose \
    2>&1 | tee -a "$BENCHMARK_LOG" | tee "/tmp/genesis_benchmark_$TIMESTAMP.log" &

echo "✅ Genesis launched in background (PID: $!)"
echo ""

echo "🚀 PHASE 2: RALPH EXECUTION"
echo "==============================="
echo ""

RALPH_SESSION="ralph-ts-migration-$(date +%Y%m%d-%H%M%S)"
RALPH_DIR="$PROJECTS_OTHER_DIR/worldai_ralph2"

echo "📋 Launching Ralph with orchestration command:"
echo "   Session: $RALPH_SESSION"
echo "   Target: $RALPH_DIR"
echo "   Goal File: roadmap/ralph_typescript_migration_benchmark.md"
echo ""

# Execute Ralph
cd "$PROJECTS_OTHER_DIR/ralph-orchestrator"

python -m ralph_orchestrator \
    "$WORKTREE_RALPH_DIR/roadmap/ralph_typescript_migration_benchmark.md" \
    --output-dir "$RALPH_DIR" \
    --agent codex \
    --max-iterations 50 \
    --verbose \
    2>&1 | tee -a "$BENCHMARK_LOG" | tee "/tmp/ralph_benchmark_$TIMESTAMP.log" &

echo "✅ Ralph launched in background (PID: $!)"
echo ""

echo "📊 MONITORING"
echo "============="
echo "Benchmarking in progress. Monitor logs at:"
echo "  Combined: $BENCHMARK_LOG"
echo "  Genesis: /tmp/genesis_benchmark_$TIMESTAMP.log"
echo "  Ralph:   /tmp/ralph_benchmark_$TIMESTAMP.log"
echo ""
echo "Run /cons when both agents finish to compare results."
```

## Integration
- Orchestrated via `agent-orchestrator` Python module
- Integrates with `/cons` for code quality review
- Produces structured reports comparable to `/benchg`

Perfect for comprehensive evaluation of TypeScript migration capabilities and orchestration system comparison.
