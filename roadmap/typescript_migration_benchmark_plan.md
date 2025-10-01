# TypeScript Migration Benchmark: Genesis vs Ralph

**Purpose**: Head-to-head comparison of Genesis (WorldArchitect.ai orchestration) vs Ralph (standalone ralph-orchestrator) autonomously completing identical TypeScript migration tasks.

**Date Created**: 2025-09-30
**Status**: Ready for execution

## Executive Summary

This benchmark tests the autonomous capabilities of two different orchestration systems (Genesis and Ralph) by tasking them with an identical, complex software migration: converting WorldArchitect.AI's Python Flask backend to a TypeScript FastMCP server while maintaining 100% functional parity.

**Key Constraints**:
- Both agents work in completely separate repositories
- Both have access to same source code and design documents
- Both must meet identical success criteria
- Maximum 50 iterations each
- No human intervention except to start/stop agents

## Benchmark Configuration

### Common Parameters
- **Source Repository**: `/Users/jleechan/projects/worktree_ralph`
- **Engineering Design**: `/Users/jleechan/projects/worktree_ralph/roadmap/mvp_site_typescript_migration_eng_design.md`
- **Test Cases**: `/Users/jleechan/projects/worktree_ralph/testing_llm/*.md`
- **Credentials**: Both agents copy from worktree_worker2
- **Max Iterations**: 50 per agent
- **Success Criteria**: Identical for both agents

### Agent-Specific Parameters

#### Genesis Configuration
- **Agent Type**: Genesis (WorldArchitect.ai orchestration system)
- **Working Directory**: `/Users/jleechan/projects_other/worldai_genesis2` (fresh repo)
- **Command**: `python genesis/genesis.py`
- **Default CLI**: Codex CLI (200K context via OpenRouter)
- **Goal File**: `roadmap/genesis_typescript_migration_benchmark.md`
- **Execution**:
  ```bash
  cd /Users/jleechan/projects/worktree_ralph
  python genesis/genesis.py \
      roadmap/genesis_typescript_migration_benchmark.md \
      50 \
      --verbose
  ```

#### Ralph Configuration
- **Agent Type**: Ralph (standalone ralph-orchestrator)
- **Working Directory**: `/Users/jleechan/projects_other/worldai_ralph2` (fresh repo)
- **Command**: `python -m ralph_orchestrator`
- **Default CLI**: Codex CLI (200K context via OpenRouter)
- **Goal File**: `roadmap/ralph_typescript_migration_benchmark.md`
- **Execution**:
  ```bash
  cd /Users/jleechan/projects_other/ralph-orchestrator
  python -m ralph_orchestrator \
      /Users/jleechan/projects/worktree_ralph/roadmap/ralph_typescript_migration_benchmark.md \
      --agent codex \
      --max-iterations 50 \
      --verbose
  ```

## Success Criteria (Identical for Both)

### 🚨 Mandatory Requirements

Both agents must achieve ALL of the following to be considered successful:

#### 1. Repository Setup
- ✅ Fresh repo created at designated location (worldai_genesis2 or worldai_ralph2)
- ✅ Git initialized with commit history
- ✅ All credentials copied from worktree_worker2 (.env, firebase-service-account.json)
- ✅ TypeScript project initialized with proper configuration

#### 2. Production Server Running
- ✅ Server starts without errors: `npm start` succeeds
- ✅ Health endpoint responds: `curl http://localhost:3001/health` returns 200
- ✅ No initialization errors in server logs
- ✅ Server uses production Firebase/Gemini credentials

#### 3. MCP Tools Listed
- ✅ `curl http://localhost:3001/tools` returns complete tool list
- ✅ CampaignTool, InteractionTool, ExportTool, SettingsTool all present
- ✅ Tool schemas match FastMCP standards

#### 4. Functional Parity
- ✅ All Python API endpoints replicated in TypeScript
- ✅ Side-by-side comparison shows ≥95% response similarity
- ✅ Error handling matches Python behavior exactly
- ✅ API contract preserved for existing frontend

#### 5. Database Integration
- ✅ Campaign creation creates Firestore document
- ✅ Campaign document visible in Firebase Console
- ✅ Document structure matches Python implementation exactly
- ✅ All required fields present with correct types

#### 6. AI Integration
- ✅ Interaction endpoint calls Gemini API successfully
- ✅ Narrative generation produces quality comparable to Python
- ✅ Response structure matches Python exactly
- ✅ Prompt formatting preserved from Python implementation

#### 7. Test Validation
- ✅ All unit tests pass: `npm run test:unit` exits 0
- ✅ All integration tests pass: `npm run test:integration` exits 0
- ✅ All test cases from `/Users/jleechan/projects/worktree_ralph/testing_llm/*.md` pass
- ✅ No critical test failures or regressions

#### 8. End-to-End Validation
- ✅ Complete user journey works: signup → create campaign → interact → export
- ✅ All test scenarios from `testing_llm/` execute successfully
- ✅ No critical bugs or blocking issues
- ✅ Performance comparable to Python baseline (±20%)

#### 9. Commit and Documentation
- ✅ All changes committed with descriptive messages
- ✅ Git log shows clear development history
- ✅ Benchmark report created with actual metrics (GENESIS_BENCHMARK_REPORT.md or RALPH_BENCHMARK_REPORT.md)

## Evaluation Metrics

### Primary Metrics (Weighted Scoring)

| Metric | Weight | Measurement | Success Threshold |
|--------|--------|-------------|-------------------|
| Completion | 30% | All success criteria met | 100% (binary) |
| Functional Parity | 25% | % of API endpoints working identically | ≥95% |
| Test Coverage | 20% | % of test cases passing | ≥95% |
| Code Quality | 15% | TypeScript compilation, lint errors, test coverage | ≥90% |
| Time Efficiency | 10% | Iterations used / 50 max | Lower is better |

### Secondary Metrics (Qualitative)

| Metric | Description | Evaluation Method |
|--------|-------------|-------------------|
| Autonomous Problem Solving | Ability to debug and fix issues without human intervention | Code review of fix attempts |
| Architecture Quality | Adherence to FastMCP patterns and TypeScript best practices | Code review by human |
| Documentation Quality | Clarity and completeness of benchmark report | Human readability assessment |
| Error Recovery | Number of failed attempts before successful implementation | Git commit history analysis |
| Strategic Planning | Evidence of upfront planning vs reactionary coding | Analysis of commit sequence |

## Execution Protocol

### Pre-Execution Checklist

1. **Environment Verification**:
   ```bash
   # Verify source repo exists
   ls -la /Users/jleechan/projects/worktree_ralph/mvp_site/

   # Verify credentials exist
   ls -la /Users/jleechan/projects/worktree_ralph/.env
   ls -la /Users/jleechan/projects/worktree_ralph/firebase-service-account.json

   # Verify test cases exist
   ls /Users/jleechan/projects/worktree_ralph/testing_llm/*.md

   # Verify Ralph installation
   cd /Users/jleechan/projects_other/ralph-orchestrator
   python -m ralph_orchestrator --help

   # Verify Genesis installation
   cd /Users/jleechan/projects/worktree_ralph
   python genesis/genesis.py --help
   ```

2. **Clean State Verification**:
   ```bash
   # Ensure target directories don't exist
   if [ -d "/Users/jleechan/projects_other/worldai_genesis2" ]; then
       echo "❌ ERROR: worldai_genesis2 already exists - remove before starting"
       exit 1
   fi

   if [ -d "/Users/jleechan/projects_other/worldai_ralph2" ]; then
       echo "❌ ERROR: worldai_ralph2 already exists - remove before starting"
       exit 1
   fi

   echo "✅ Clean state verified - ready to start benchmark"
   ```

### Execution Sequence

**Option 1: Sequential Execution (Recommended for Comparison)**

Run one agent at a time to avoid resource contention and enable better observation:

```bash
# ========================================
# Phase 1: Genesis Benchmark
# ========================================
echo "🚀 Starting Genesis benchmark..."
cd /Users/jleechan/projects/worktree_ralph
python genesis/genesis.py \
    roadmap/genesis_typescript_migration_benchmark.md \
    50 \
    --verbose \
    2>&1 | tee /tmp/genesis_benchmark_$(date +%Y%m%d_%H%M%S).log

# Wait for Genesis to complete (or reach iteration limit)
# Verify Genesis results manually

# ========================================
# Phase 2: Ralph Benchmark
# ========================================
echo "🚀 Starting Ralph benchmark..."
cd /Users/jleechan/projects_other/ralph-orchestrator
python -m ralph_orchestrator \
    /Users/jleechan/projects/worktree_ralph/roadmap/ralph_typescript_migration_benchmark.md \
    --agent codex \
    --max-iterations 50 \
    --verbose \
    2>&1 | tee /tmp/ralph_benchmark_$(date +%Y%m%d_%H%M%S).log
```

**Option 2: Parallel Execution (For Time Efficiency)**

Run both agents simultaneously in separate tmux sessions:

```bash
# Genesis in tmux session
tmux new-session -d -s genesis_benchmark \
    "cd /Users/jleechan/projects/worktree_ralph && \
     python genesis/genesis.py \
         roadmap/genesis_typescript_migration_benchmark.md \
         50 \
         --verbose \
         2>&1 | tee /tmp/genesis_benchmark_$(date +%Y%m%d_%H%M%S).log; \
     bash"

# Ralph in separate tmux session
tmux new-session -d -s ralph_benchmark \
    "cd /Users/jleechan/projects_other/ralph-orchestrator && \
     python -m ralph_orchestrator \
         /Users/jleechan/projects/worktree_ralph/roadmap/ralph_typescript_migration_benchmark.md \
         --agent codex \
         --max-iterations 50 \
         --verbose \
         2>&1 | tee /tmp/ralph_benchmark_$(date +%Y%m%d_%H%M%S).log; \
     bash"

# Attach to sessions for monitoring
tmux attach -t genesis_benchmark    # Use Ctrl+B, D to detach
tmux attach -t ralph_benchmark      # Use Ctrl+B, D to detach
```

### Monitoring During Execution

```bash
# Monitor Genesis progress
tmux attach -t genesis_benchmark
# OR
tail -f /tmp/genesis_benchmark_*.log

# Monitor Ralph progress
tmux attach -t ralph_benchmark
# OR
tail -f /tmp/ralph_benchmark_*.log

# Check repo creation status
watch -n 10 'ls -la /Users/jleechan/projects_other/ | grep worldai'

# Monitor commit activity
watch -n 30 'cd /Users/jleechan/projects_other/worldai_genesis2 2>/dev/null && git log --oneline | head -5'
watch -n 30 'cd /Users/jleechan/projects_other/worldai_ralph2 2>/dev/null && git log --oneline | head -5'
```

## Post-Execution Validation

### Automated Validation Script

```bash
#!/bin/bash
# validate_benchmark.sh - Run validation checks on both implementations

GENESIS_DIR="/Users/jleechan/projects_other/worldai_genesis2"
RALPH_DIR="/Users/jleechan/projects_other/worldai_ralph2"
RESULTS_FILE="benchmark_validation_results_$(date +%Y%m%d_%H%M%S).md"

cat > "$RESULTS_FILE" << 'EOF'
# TypeScript Migration Benchmark Validation Results

**Validation Date**: $(date)
**Genesis Directory**: $GENESIS_DIR
**Ralph Directory**: $RALPH_DIR

## Repository Setup Validation

### Genesis
EOF

# Genesis validation
if [ -d "$GENESIS_DIR" ]; then
    echo "✅ Repository exists" >> "$RESULTS_FILE"
    cd "$GENESIS_DIR"
    echo "- Commits: $(git log --oneline | wc -l)" >> "$RESULTS_FILE"
    echo "- Branches: $(git branch -a | wc -l)" >> "$RESULTS_FILE"
    echo "- Files: $(find . -type f -not -path './.git/*' | wc -l)" >> "$RESULTS_FILE"
    [ -f ".env" ] && echo "✅ .env copied" >> "$RESULTS_FILE" || echo "❌ .env missing" >> "$RESULTS_FILE"
    [ -f "firebase-service-account.json" ] && echo "✅ Firebase credentials copied" >> "$RESULTS_FILE" || echo "❌ Firebase credentials missing" >> "$RESULTS_FILE"
else
    echo "❌ Repository does not exist" >> "$RESULTS_FILE"
fi

echo "" >> "$RESULTS_FILE"
echo "### Ralph" >> "$RESULTS_FILE"

# Ralph validation
if [ -d "$RALPH_DIR" ]; then
    echo "✅ Repository exists" >> "$RESULTS_FILE"
    cd "$RALPH_DIR"
    echo "- Commits: $(git log --oneline | wc -l)" >> "$RESULTS_FILE"
    echo "- Branches: $(git branch -a | wc -l)" >> "$RESULTS_FILE"
    echo "- Files: $(find . -type f -not -path './.git/*' | wc -l)" >> "$RESULTS_FILE"
    [ -f ".env" ] && echo "✅ .env copied" >> "$RESULTS_FILE" || echo "❌ .env missing" >> "$RESULTS_FILE"
    [ -f "firebase-service-account.json" ] && echo "✅ Firebase credentials copied" >> "$RESULTS_FILE" || echo "❌ Firebase credentials missing" >> "$RESULTS_FILE"
else
    echo "❌ Repository does not exist" >> "$RESULTS_FILE"
fi

echo "" >> "$RESULTS_FILE"
echo "## Server Startup Validation" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"

# Test Genesis server
if [ -d "$GENESIS_DIR" ]; then
    echo "### Genesis Server" >> "$RESULTS_FILE"
    cd "$GENESIS_DIR"
    if [ -f "package.json" ]; then
        npm install &> /dev/null
        npm run build &> /dev/null
        timeout 30 npm start &> /tmp/genesis_server_test.log &
        GENESIS_PID=$!
        sleep 10
        if curl -s http://localhost:3001/health | grep -q "ok"; then
            echo "✅ Server started successfully" >> "$RESULTS_FILE"
            echo "✅ Health endpoint responded" >> "$RESULTS_FILE"
        else
            echo "❌ Server failed to start or health check failed" >> "$RESULTS_FILE"
        fi
        kill $GENESIS_PID 2>/dev/null
    else
        echo "❌ package.json not found" >> "$RESULTS_FILE"
    fi
fi

# Test Ralph server
if [ -d "$RALPH_DIR" ]; then
    echo "" >> "$RESULTS_FILE"
    echo "### Ralph Server" >> "$RESULTS_FILE"
    cd "$RALPH_DIR"
    if [ -f "package.json" ]; then
        npm install &> /dev/null
        npm run build &> /dev/null
        timeout 30 npm start &> /tmp/ralph_server_test.log &
        RALPH_PID=$!
        sleep 10
        if curl -s http://localhost:3002/health | grep -q "ok"; then
            echo "✅ Server started successfully" >> "$RESULTS_FILE"
            echo "✅ Health endpoint responded" >> "$RESULTS_FILE"
        else
            echo "❌ Server failed to start or health check failed" >> "$RESULTS_FILE"
        fi
        kill $RALPH_PID 2>/dev/null
    else
        echo "❌ package.json not found" >> "$RESULTS_FILE"
    fi
fi

echo "" >> "$RESULTS_FILE"
echo "## Validation Complete" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"
echo "Review full logs:" >> "$RESULTS_FILE"
echo "- Genesis: /tmp/genesis_benchmark_*.log" >> "$RESULTS_FILE"
echo "- Ralph: /tmp/ralph_benchmark_*.log" >> "$RESULTS_FILE"

cat "$RESULTS_FILE"
```

### Manual Validation Checklist

For each agent, verify:

1. **Repository Creation**:
   - [ ] Directory created at correct location
   - [ ] Git initialized with `.git/` directory
   - [ ] README.md exists with agent identifier
   - [ ] Initial commit exists in git log

2. **Credentials Copied**:
   - [ ] `.env` file exists and contains Firebase config
   - [ ] `firebase-service-account.json` exists
   - [ ] Credentials are valid (not dummy/placeholder values)

3. **TypeScript Project Setup**:
   - [ ] `package.json` exists with correct dependencies
   - [ ] `tsconfig.json` exists with strict configuration
   - [ ] `src/` directory created with proper structure
   - [ ] Dependencies installed (`node_modules/` exists)

4. **Server Startup**:
   - [ ] `npm run build` succeeds without errors
   - [ ] `npm start` launches server
   - [ ] Health endpoint responds: `curl http://localhost:3001/health`
   - [ ] No critical errors in console output

5. **MCP Tools**:
   - [ ] `/tools` endpoint returns tool list
   - [ ] CampaignTool present with correct schema
   - [ ] InteractionTool present with correct schema
   - [ ] ExportTool present with correct schema
   - [ ] SettingsTool present with correct schema

6. **Functional Testing**:
   - [ ] Campaign creation endpoint works
   - [ ] Campaign appears in Firebase Console
   - [ ] Interaction endpoint generates narrative
   - [ ] Export endpoint produces downloadable files
   - [ ] Settings endpoints handle CRUD operations

7. **Test Suite**:
   - [ ] Unit tests exist and can be run
   - [ ] Integration tests exist and can be run
   - [ ] Test cases from `testing_llm/` validated
   - [ ] Test coverage reports generated

8. **Documentation**:
   - [ ] Benchmark report exists (GENESIS_BENCHMARK_REPORT.md or RALPH_BENCHMARK_REPORT.md)
   - [ ] Report contains actual metrics (not placeholders)
   - [ ] Learnings and challenges documented
   - [ ] Git commit history shows clear development flow

## Comparison Analysis

After both agents complete (or reach iteration limit), perform comparative analysis:

### Quantitative Comparison

```bash
# Create comparison report
cat > benchmark_comparison_$(date +%Y%m%d_%H%M%S).md << 'EOF'
# Genesis vs Ralph Benchmark Comparison

| Metric | Genesis | Ralph | Winner |
|--------|---------|-------|--------|
| **Completion Status** | [Complete/Partial/Failed] | [Complete/Partial/Failed] | [Genesis/Ralph/Tie] |
| **Iterations Used** | X / 50 | X / 50 | [Lower is better] |
| **Git Commits** | X | X | [Indicates progress] |
| **Files Created** | X | X | [Indicates completeness] |
| **Lines of Code** | X | X | [Comparable scope] |
| **Server Startup** | [✅/❌] | [✅/❌] | [Both must succeed] |
| **Tools Listed** | X / 4 | X / 4 | [4/4 required] |
| **Test Cases Passing** | X / Y | X / Y | [Higher % wins] |
| **API Parity** | X% | X% | [≥95% required] |
| **Build Time** | Xs | Xs | [Faster is better] |
| **Response Time** | Xms | Xms | [Comparable required] |

## Qualitative Assessment

### Genesis Strengths
- [Observed strengths from code review]
- [Architecture decisions]
- [Problem-solving approach]

### Genesis Weaknesses
- [Observed weaknesses]
- [Areas of struggle]
- [Incomplete implementations]

### Ralph Strengths
- [Observed strengths]
- [Architecture decisions]
- [Problem-solving approach]

### Ralph Weaknesses
- [Observed weaknesses]
- [Areas of struggle]
- [Incomplete implementations]

## Winner Determination

**Overall Winner**: [Genesis/Ralph/Tie]

**Justification**: [Detailed explanation based on metrics and qualitative assessment]

## Recommendations for Future Development

### For Genesis
- [Improvements based on performance]

### For Ralph
- [Improvements based on performance]

### For Benchmark Design
- [Improvements to benchmark methodology]
EOF
```

## Expected Timeline

| Phase | Duration | Description |
|-------|----------|-------------|
| Pre-execution setup | 30 minutes | Verify environment, create goal files |
| Genesis execution | 8-24 hours | Agent autonomous work (50 iterations) |
| Ralph execution | 8-24 hours | Agent autonomous work (50 iterations) |
| Post-execution validation | 2-4 hours | Run validation scripts, manual checks |
| Comparison analysis | 2-4 hours | Detailed comparison and report generation |
| **Total** | **20-56 hours** | **Full benchmark cycle** |

## Risk Mitigation

### Known Risks

1. **Agent Stalls/Infinite Loops**:
   - **Mitigation**: 50 iteration hard limit, monitor progress every 10 iterations
   - **Contingency**: Kill agent if stuck on same task for >10 iterations

2. **Credential/Environment Issues**:
   - **Mitigation**: Pre-validate all credentials before starting benchmark
   - **Contingency**: Not considered agent failure if environment setup was wrong

3. **Resource Exhaustion** (CPU/Memory/API quotas):
   - **Mitigation**: Monitor system resources, use rate limiting for APIs
   - **Contingency**: Pause/resume capability with checkpoints

4. **Incomplete Implementations**:
   - **Mitigation**: Clear success criteria, work evidence requirements
   - **Evaluation**: Partial credit for partial completion based on scoring matrix

5. **Unfair Comparison** (one agent gets better starting position):
   - **Mitigation**: Identical goal files, source code access, credentials
   - **Verification**: Both start from truly empty repositories

## Success Declaration

An agent is declared **successful** if and only if:

1. **Repository created** at designated location with git history
2. **Credentials copied** from source repository
3. **Server starts** without errors and health check passes
4. **All 4 MCP tools** listed at `/tools` endpoint
5. **Campaign creation** works end-to-end with Firebase verification
6. **Interaction endpoint** generates narratives via Gemini API
7. **≥90% of test cases** from `testing_llm/` pass
8. **Benchmark report** exists with actual metrics
9. **Git commits** show clear development history

An agent is declared **the winner** if:
- They achieve success while the other agent fails, OR
- Both succeed but one uses fewer iterations, OR
- Both succeed with same iterations but one has higher quality code/tests

---

**This benchmark is ready for execution. Both agents have identical starting conditions and success criteria. May the best orchestration system win!**
