# /gene - Genesis Execution (Auto-Execute)

**Command Summary**: Enhanced `/gen` that automatically executes the genesis.py workflow with fast-gen default mode

**Usage**: `/gene "goal description" [iterations]`

**Purpose**: Single-command goal refinement and execution using the enhanced genesis/genesis.py with fast-gen default mode

## Key Differences from /gen

- **Auto-Execution**: Automatically runs `python genesis/genesis.py` after goal setup
- **Fast-Gen Integration**: Uses the new default fast-gen mode (no --fast-gen flag needed)
- **Streamlined Workflow**: One command does everything from goal to execution
- **Enhanced UX**: Leverages the improved genesis.py interface
- **🚨 Self-Determination**: Genesis automatically detects completion with rigorous exit criteria
- **🔍 Validation Protocol**: End-to-end validation prevents false success claims
- **🔄 Iterate Mode**: Uses --iterate flag to skip initial Cerebras generation, start with iterative refinement

## Execution Instructions

**CRITICAL**: Before running genesis, ensure current project's goal directory is copied to genesis working directory:

```bash
# Copy goals to genesis working directory for context
GENESIS_WORKDIR="/Users/jleechan/projects_other/codex_plus"
CURRENT_GOALS="/Users/jleechan/projects/worktree_ralph/goals"

if [[ -d "$CURRENT_GOALS" ]]; then
    echo "📋 Copying goals directory to genesis working directory..."
    cp -r "$CURRENT_GOALS" "$GENESIS_WORKDIR/"
    echo "✅ Goals copied to $GENESIS_WORKDIR/goals"
fi
```

When this command is invoked with a goal:

```bash
# Smart goal detection: goal directory vs. new prompt
INPUT="$1"
ITERATIONS="${2:-30}"

# Check if input looks like a goal directory path
if [[ "$INPUT" =~ ^goals/ ]] || [[ -d "$INPUT" ]] || [[ -d "goals/$INPUT" ]]; then
    # Goal directory mode
    if [[ -d "$INPUT" ]]; then
        GOAL_DIR="$INPUT"
    elif [[ -d "goals/$INPUT" ]]; then
        GOAL_DIR="goals/$INPUT"
    else
        GOAL_DIR="$INPUT"
    fi

    # Verify goal directory has required files
    if [[ -f "$GOAL_DIR/00-goal-definition.md" ]]; then
        echo "📁 Using existing goal directory: $GOAL_DIR"
        GENESIS_CMD="python \"$PWD/genesis/genesis.py\" \"$GOAL_DIR\" \"$ITERATIONS\" --iterate"
    else
        echo "❌ Goal directory $GOAL_DIR exists but missing goal definition files"
        echo "💡 Use: /gene \"your goal description here\" to create new goals"
        exit 1
    fi
else
    # New goal mode - use --refine
    echo "🔄 Creating new goal with: $INPUT"
    GENESIS_CMD="python \"$PWD/genesis/genesis.py\" --refine \"$INPUT\" \"$ITERATIONS\" --iterate"
fi

# Generate unique session name
SESSION_NAME="gene-$(date +%Y%m%d-%H%M%S)"

# Print raw Python orchestration command
echo '🚀 RAW PYTHON ORCHESTRATION COMMAND:'
echo "======================================="
echo ""
echo "# Genesis Agent Orchestration Command"
echo "# Copy and execute this Python code to run via orchestration:"
echo ""
echo "python3 -c \""
echo "import sys"
echo "sys.path.append('/Users/jleechan/projects/worktree_ralph')"
echo "from orchestrate import TaskOrchestrator"
echo ""
echo "# Genesis Agent Configuration"
echo "agent_config = {"
echo "    'id': 'genesis-${SESSION_NAME}',"
echo "    'type': 'genesis',"
echo "    'session_name': '${SESSION_NAME}',"
echo "    'working_dir': '/Users/jleechan/projects_other/codex_plus',"
echo "    'genesis_cmd': '${GENESIS_CMD}',"
echo "    'environment': {"
echo "        # No environment variables needed - using reasonable defaults"
echo "    },"
echo "    'requires_llm': False"
echo "}"
echo ""
echo "# Initialize orchestrator and execute"
echo "orchestrator = TaskOrchestrator()"
echo "result = orchestrator.execute_genesis_task(agent_config)"
echo "print(f'Genesis task result: {result}')"
echo "\""
echo ""
echo "======================================="
echo ""
echo "📋 Alternative: Direct tmux execution"
echo "tmux new-session -d -s '$SESSION_NAME' env CEREBRAS_API_KEY=\"$CEREBRAS_API_KEY\" bash -c 'source \$HOME/.bashrc && cd /Users/jleechan/projects_other/codex_plus && $GENESIS_CMD; exec bash'"
echo ""
echo "🔄 Session Management:"
echo "  Attach:     tmux attach -t $SESSION_NAME"
echo "  Kill:       tmux kill-session -t $SESSION_NAME"
echo "  Observer:   $PWD/scripts/genesis_observer.sh $SESSION_NAME"
echo ""
echo "📋 Genesis Log Paths (Available after startup):"
echo "  Technical:  /tmp/\$(basename \$GENESIS_WORKDIR)/\$(git branch --show-current 2>/dev/null || echo unknown)/genesis_\$(date +%s).log"
echo "  Human:      /tmp/\$(basename \$GENESIS_WORKDIR)/\$(git branch --show-current 2>/dev/null || echo unknown)/genesis_\$(date +%s)_human.log"
echo ""
echo "📊 Monitor Progress:"
echo "  tail -f /tmp/\$(basename \$GENESIS_WORKDIR)/\$(git branch --show-current 2>/dev/null || echo unknown)/genesis_*_human.log"
echo "  tmux capture-pane -t $SESSION_NAME -p | tail -20"
```

2. **Orchestration Integration**:
   - **GenesisAgent Type**: Uses specialized orchestration agent for tmux management
   - **Raw Command Output**: Prints Python orchestration command for manual execution
   - **Deterministic Operation**: No LLM required for tmux session management
   - **Simplified Configuration**: Uses reasonable defaults without environment variables
   - **Session Isolation**: Each genesis run gets unique session identifier
   - **Alternative Execution**: Direct tmux command also provided as fallback

### Command Parameters
- `goal_description`: Required - description of what to build
- `iterations`: Optional - number of iterations (default: 30)

## 🚨 Enhanced Exit Criteria & Self-Determination

### Genesis Self-Determination Protocol
Genesis now automatically detects completion using rigorous validation:

**Primary Completion Indicators**:
- ✅ **All Success Criteria Met**: Every goal criterion shows validated completion
- ✅ **Evidence-Based Validation**: Demonstrable results with actual output artifacts
- ✅ **End-to-End Testing**: Complete workflows verified, not just component startup
- ✅ **No Critical Gaps**: All identified implementation gaps resolved
- ✅ **Performance Targets**: Sub-200ms coordination overhead achieved (where applicable)

**Consensus Response Analysis**:
Genesis automatically completes when consensus assessment contains:
- **Explicit Completion**: "All exit criteria satisfied", "100% complete", "Implementation complete"
- **High Progress**: Overall progress ≥95% with no critical implementation gaps
- **Evidence Validation**: "Objective achieved", "Requirements met", "Fully operational"
- **Gap Resolution**: "No critical gaps remaining", "All requirements satisfied"

**🚨 Validation Requirements**:
- **Functional Tests**: All claimed functionality must execute successfully end-to-end
- **Performance Benchmarks**: Measurable outcomes meeting specified targets
- **Integration Tests**: Complete workflows verified in target environment
- **Documentation Complete**: Implementation guides enable independent reproduction

### Observer-Only Monitoring
- **Monitor Script**: Observes Genesis progress without making completion decisions
- **No False Completion**: Monitor never declares Genesis "complete" based on superficial signals
- **Self-Determination**: Only Genesis determines its own completion based on consensus analysis

**Anti-Patterns Prevented**:
- ❌ Startup signal success (claiming "working" because process starts)
- ❌ Partial signal validation (interpreting initialization as completion)
- ❌ Component-only testing (testing parts instead of complete workflows)
- ❌ Assumption-based fixes (assuming problems are solved without verification)

## Enhanced Features (Proto Genesis v2)

### Fast Generation
- **Default Mode**: Fast generation + execution is now default behavior
- **Auto-Directory**: Generates `goals/YYYY-MM-DD-HHMM-[slug]/` automatically
- **Immediate Execution**: No manual copy-paste needed
- **2000 Token Context**: Enhanced context preservation (up from 200 tokens)

### Execution Options
- **Pool Size**: Configurable via `--pool-size N` (default: 5)
- **Direct Execution**: All operations use `claude -p` directly
- **Search-First**: Validates before building to prevent duplicates
- **Quality Control**: No-placeholders policy enforced

## Example Usage

```bash
/gene "build a REST API for user management with authentication"
```

**Expected Output**:
```
🚀 RAW PYTHON ORCHESTRATION COMMAND:
=======================================

# Genesis Agent Orchestration Command
# Copy and execute this Python code to run via orchestration:

python3 -c "
import sys
sys.path.append('/Users/jleechan/projects/worktree_ralph')
from orchestrate import TaskOrchestrator

# Genesis Agent Configuration
agent_config = {
    'id': 'genesis-gene-20250923-0945',
    'type': 'genesis',
    'session_name': 'gene-20250923-0945',
    'working_dir': '/Users/jleechan/projects_other/codex_plus',
    'genesis_cmd': 'python /Users/jleechan/projects/worktree_ralph/genesis/genesis.py --refine "build a REST API for user management with authentication" 5 --iterate',
    'environment': {},
    'requires_llm': False
}

# Initialize orchestrator and execute
orchestrator = TaskOrchestrator()
result = orchestrator.execute_genesis_task(agent_config)
print(f'Genesis task result: {result}')
"

=======================================

📋 Alternative: Direct tmux execution
tmux new-session -d -s 'gene-20250923-0945' bash -c 'cd /Users/jleechan/projects_other/codex_plus && python /Users/jleechan/projects/worktree_ralph/genesis/genesis.py --refine "build a REST API for user management with authentication" 5 --iterate; exec bash'

🔄 Session Management:
  Attach:     tmux attach -t gene-20250923-0945
  Kill:       tmux kill-session -t gene-20250923-0945
```

### With Custom Iterations
```bash
/gene "code fibonacci function" 3
```

### With Pool Size Configuration
```bash
/gene "build microservice architecture" 10 --pool-size 3
```

## Workflow Benefits

### Streamlined Experience
- **One Command**: Complete workflow from idea to implementation
- **Orchestration Ready**: Generates Python code for deterministic execution
- **Fast Results**: Leverages /cereb for rapid goal file creation
- **Enhanced Context**: 2000 token summaries for better continuity
- **GenesisAgent Integration**: Uses specialized orchestration agent type
- **Dual Execution**: Raw Python command + fallback tmux execution

### Quality Assurance
- **Search-First**: Prevents duplicate implementations
- **No Placeholders**: Enforces complete implementations
- **Validation**: Quality checks at each stage
- **Error Recovery**: Loop-back mechanisms for failures
- **Session Persistence**: Review complete execution history in tmux

### Solo Developer Optimized
- **Fast Mode Default**: Optimized for solo developer velocity
- **GitHub Safety**: Easy rollbacks via git if issues arise
- **Direct Execution**: No complex delegation patterns
- **Practical Focus**: Architecture quality over enterprise paranoia
- **Autonomous Development**: Long-running tasks with detach/reattach capability

## Generated Directory Structure

The command creates and populates:
```
goals/YYYY-MM-DD-HHMM-[slug]/
├── 00-goal-definition.md     # Generated goal specification
├── 01-success-criteria.md    # Generated exit criteria
├── 02-implementation-notes.md # Generated technical approach
├── 03-testing-strategy.md    # Generated validation strategy
├── fix_plan.md               # Living plan document (created during execution)
├── GENESIS.md                # Self-improvement learnings (created during execution)
└── proto_genesis_session.json # Session state and progress
```

## Proto Genesis v2 Integration

The command leverages enhanced genesis/genesis.py features:
- **Fast-Gen Default**: No flag needed, fast generation is default
- **Enhanced Summaries**: 2000 token context between stages
- **Direct Execution**: All calls use `claude -p` directly
- **Configurable Pool**: `--pool-size` parameter for concurrency
- **Auto-Detection**: Smart argument parsing and directory generation
- **Quality Control**: No-placeholders policy and search-first validation

## Error Handling

- **Generation Failures**: Clear error messages with recovery suggestions
- **Execution Failures**: Loop-back mechanisms and error recovery
- **Argument Validation**: Helpful error messages for invalid input
- **Session Recovery**: Can resume interrupted sessions

## Performance Characteristics

- **Fast Generation**: ~30-60 seconds for goal file creation via /cereb
- **Orchestration Ready**: Instant Python command generation for execution
- **Enhanced Context**: Better decision making with 2000 token summaries
- **Deterministic Operation**: GenesisAgent requires no LLM for tmux management
- **Session Persistence**: Tmux sessions survive terminal disconnections
- **Dual Execution Modes**: Python orchestration + direct tmux fallback
- **Autonomous Operation**: Can run unattended for hours via orchestration system

## Implementation Notes

- **Orchestration Integration**: Generates Python code for GenesisAgent execution
- **Fast-Gen Integration**: Uses the new default mode of genesis/genesis.py
- **Deterministic Tmux**: GenesisAgent manages sessions without LLM requirement
- **Dual Execution**: Python orchestration command + direct tmux fallback
- **Session Independence**: Creates complete goal directory for future reference
- **Recovery Support**: Can re-run with existing goal directory if needed

## Comparison with /pgen

| Feature | /pgen | /gene |
|---------|-------|--------|
| Goal Setup | Interactive `/goal` command | Fast /cereb generation |
| Execution | Manual copy-paste | Python orchestration command generation |
| Directory | Pre-created structure | Auto-generated with content |
| Context | Basic goal files | Enhanced 2000 token summaries |
| Speed | 2-phase workflow | Single streamlined workflow |
| Control | Manual execution timing | GenesisAgent orchestration ready |
| Monitoring | No built-in monitoring | Orchestration system + tmux fallback |
| Persistence | Terminal-dependent | Deterministic tmux session management |
| Observability | Limited output | Full verbose logging via orchestration |

Use `/pgen` when you want manual control over execution timing.
Use `/gene` when you want Python orchestration command generation for GenesisAgent execution.

## Exclusion from Export

**IMPORTANT**: This command is explicitly excluded from `/exportcommands` output as it is an internal development tool for rapid goal-to-implementation workflows.
