# /pgene - Proto Genesis Execution (Auto-Execute)

**Command Summary**: Enhanced `/pgen` that automatically executes the proto_genesis.py workflow with fast-gen default mode

**Usage**: `/pgene "goal description" [iterations]`

**Purpose**: Single-command goal refinement and execution using the enhanced proto_genesis.py with fast-gen default mode

## Key Differences from /pgen

- **Auto-Execution**: Automatically runs `python proto_genesis.py` after goal setup
- **Fast-Gen Integration**: Uses the new default fast-gen mode (no --fast-gen flag needed)
- **Streamlined Workflow**: One command does everything from goal to execution
- **Enhanced UX**: Leverages the improved proto_genesis.py interface

## Execution Instructions

When this command is invoked with a goal:

### Single-Phase Workflow: Generate + Execute

1. **Fast Goal Generation + Execution**:
   ```bash
   python proto_genesis.py "$GOAL_DESCRIPTION" [iterations]
   ```

2. **Automatic Process**:
   - Uses proto_genesis.py's default fast-gen mode
   - Auto-generates timestamped goal directory
   - Creates goal files using /cereb integration
   - Immediately executes Genesis workflow
   - No manual intervention required

### Command Parameters
- `goal_description`: Required - description of what to build
- `iterations`: Optional - number of iterations (default: 5)

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
/pgene "build a REST API for user management with authentication"
```

**Expected Output**:
```
🚀 GENESIS FAST MODE: GENERATE + EXECUTE
=====================================

Goal: build a REST API for user management with authentication
Directory: goals/2025-09-22-1615-rest-api-user-mgmt/
Max Iterations: 5

📋 STEP 1: Fast Goal Generation with /cereb
✅ Generated: 00-goal-definition.md
✅ Generated: 01-success-criteria.md
✅ Generated: 02-implementation-notes.md
✅ Generated: 03-testing-strategy.md

✅ Goal files generated successfully!

⚡ STEP 2: Executing Genesis workflow
------------------------------

🎯 GENESIS ITERATION 1/5
------------------------
Genesis Principles: One item per loop | Direct claude -p execution | Enhanced context: 2000 tokens | No placeholders

📋 STAGE 1: Planning (Genesis Scheduler)
[Execution continues automatically...]
```

### With Custom Iterations
```bash
/pgene "code fibonacci function" 3
```

### With Pool Size Configuration
```bash
/pgene "build microservice architecture" 10 --pool-size 3
```

## Workflow Benefits

### Streamlined Experience
- **One Command**: Complete workflow from idea to implementation
- **No Manual Steps**: Fully automated generation and execution
- **Fast Results**: Leverages /cereb for rapid goal file creation
- **Enhanced Context**: 2000 token summaries for better continuity

### Quality Assurance
- **Search-First**: Prevents duplicate implementations
- **No Placeholders**: Enforces complete implementations
- **Validation**: Quality checks at each stage
- **Error Recovery**: Loop-back mechanisms for failures

### Solo Developer Optimized
- **Fast Mode Default**: Optimized for solo developer velocity
- **GitHub Safety**: Easy rollbacks via git if issues arise
- **Direct Execution**: No complex delegation patterns
- **Practical Focus**: Architecture quality over enterprise paranoia

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

The command leverages enhanced proto_genesis.py features:
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
- **Immediate Execution**: No delay between generation and execution
- **Enhanced Context**: Better decision making with 2000 token summaries
- **Parallel Processing**: Configurable concurrent operations via pool size

## Implementation Notes

- **Direct Execution**: Unlike `/pgen`, this command runs proto_genesis.py automatically
- **Fast-Gen Integration**: Uses the new default mode of proto_genesis.py
- **Enhanced Features**: Leverages all proto_genesis.py v2 improvements
- **Session Independence**: Creates complete goal directory for future reference
- **Recovery Support**: Can re-run with existing goal directory if needed

## Comparison with /pgen

| Feature | /pgen | /pgene |
|---------|-------|--------|
| Goal Setup | Interactive `/goal` command | Fast /cereb generation |
| Execution | Manual copy-paste | Automatic execution |
| Directory | Pre-created structure | Auto-generated with content |
| Context | Basic goal files | Enhanced 2000 token summaries |
| Speed | 2-phase workflow | Single streamlined workflow |
| Control | Manual execution timing | Immediate execution |

Use `/pgen` when you want manual control over execution timing.
Use `/pgene` when you want immediate end-to-end execution.

## Exclusion from Export

**IMPORTANT**: This command is explicitly excluded from `/exportcommands` output as it is an internal development tool for rapid goal-to-implementation workflows.
