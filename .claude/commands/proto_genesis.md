---
description: /proto_genesis - Interactive Goal Refinement System Setup
type: llm-orchestration
execution_mode: immediate
---
## ⚡ EXECUTION INSTRUCTIONS FOR CLAUDE
**When this command is invoked, YOU (Claude) must execute these steps immediately:**
**This is NOT documentation - these are COMMANDS to execute right now.**
**Use TodoWrite to track progress through multi-phase workflows.**

## 🚨 EXECUTION WORKFLOW

### Phase 1: Execution Instructions

**Action Steps:**
When this command is invoked with a goal:

### Phase 1: Interactive Goal Refinement

**Action Steps:**
1. **Execute /goal command**:
   ```bash
   /goal "$GOAL_DESCRIPTION"
   ```

2. **Goal Refinement Collaboration**:
   - Uses `/goal` command's structured goal processing
   - Auto-generates success criteria based on goal patterns
   - Creates goal directory in `goals/YYYY-MM-DD-HHMM-[slug]/`
   - Stores refined goal and exit criteria in structured format
   - User can review and approve the goal specification

### Phase 2: Command Generation

**Action Steps:**
1. **Generate Proto Genesis Execution Command**:
   - Determine the goal directory path from `/goal` output
   - Ask user for preferred number of iterations (default: 10)
   - Generate ready-to-copy command in this format:
   ```bash
   python proto_genesis.py goals/YYYY-MM-DD-HHMM-[slug]/ 10
   ```

2. **Present Copy-Paste Command**:
   ```
   ==========================================
   GOAL REFINED AND READY FOR EXECUTION
   ==========================================

   Goal Directory: goals/[timestamp-slug]/
   Refined Goal: [specific technical description]
   Exit Criteria: [numbered list of criteria]

   COPY AND PASTE THIS COMMAND:
   python proto_genesis.py goals/YYYY-MM-DD-HHMM-[slug]/ 10

   ==========================================
   ```

### Phase 4: Workflow Benefits

**Action Steps:**
1. Review the reference documentation below and execute the detailed steps.

### Phase 5: Manual Execution Control

**Action Steps:**
1. **Copy-Paste Convenience**: Ready command for terminal execution
2. **Iteration Control**: User specifies iteration count upfront
3. **Session Independence**: Can execute `ralph.py` later or multiple times
4. **Manual Oversight**: User controls when and how execution happens

## 📋 REFERENCE DOCUMENTATION

# /proto_genesis - Interactive Goal Refinement System Setup

**Command Summary**: Sets up goal refinement using `/goal` command, then generates copy-paste command for `proto_genesis.py` execution

**Usage**: `/proto_genesis "goal description"`

**Purpose**: Two-phase goal refinement workflow:
1. **Interactive Goal Setup**: Uses `/goal` to create detailed goal specification with user collaboration
2. **Command Generation**: Provides ready-to-copy `proto_genesis.py` command for execution

### Interactive Goal Refinement

- **Structured Process**: Uses `/goal` command's proven goal processing
- **Memory Integration**: Leverages goal patterns and historical data
- **User Collaboration**: Interactive refinement until user satisfaction
- **Persistent Storage**: Goal stored in organized directory structure

## Goal Directory Structure

The `/goal` command creates:
```
goals/YYYY-MM-DD-HHMM-[slug]/
├── 00-goal-definition.md     # Original and refined goal
├── 01-success-criteria.md    # Measurable exit criteria
├── 02-progress-tracking.md   # Progress updates (empty initially)
├── 03-validation-log.md      # Validation attempts (empty initially)
└── metadata.json             # Goal metadata and config
```

## Proto Genesis Integration

The generated command assumes `proto_genesis.py` behavior:
- **Default**: Skip interactive refinement, use goal from directory
- **Progress Tracking**: Update files in goal directory during execution
- **Session Persistence**: Save iteration state in goal directory
- **Self-Determination**: Genesis automatically detects completion using rigorous exit criteria
- **Validation Protocol**: End-to-end validation prevents false success claims

### 🚨 Enhanced Exit Criteria & Self-Determination

**Genesis Self-Determination Protocol**:
Genesis automatically detects completion using rigorous validation:

**Primary Completion Indicators**:
- ✅ **All Success Criteria Met**: Every goal criterion shows validated completion
- ✅ **Evidence-Based Validation**: Demonstrable results with actual output artifacts
- ✅ **End-to-End Testing**: Complete workflows verified, not just component startup
- ✅ **No Critical Gaps**: All identified implementation gaps resolved
- ✅ **Performance Targets**: Measurable outcomes meeting specified targets

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

**Anti-Patterns Prevented**:
- ❌ Startup signal success (claiming "working" because process starts)
- ❌ Partial signal validation (interpreting initialization as completion)
- ❌ Component-only testing (testing parts instead of complete workflows)
- ❌ Assumption-based fixes (assuming problems are solved without verification)

## Example Usage

```bash
/proto_genesis "build a REST API for user management with authentication"
```

**Expected Output**:
```
🎯 GOAL REFINEMENT PHASE
========================

[/goal command execution with interactive refinement]

✅ GOAL REFINED SUCCESSFULLY
============================

Goal Directory: goals/2025-01-22-1530-rest-api-user-mgmt/

Refined Goal: Create a REST API with CRUD endpoints for user management,
JWT-based authentication, password hashing, and comprehensive error handling.

Exit Criteria:
1. User CRUD endpoints (POST, GET, PUT, DELETE) implemented and functional
2. JWT authentication system with login/logout endpoints working
3. Password hashing implemented with secure algorithms
4. All endpoints return proper HTTP status codes and error messages
5. Basic input validation prevents common security issues
6. API documentation created with endpoint specifications

COPY AND PASTE THIS COMMAND:
python proto_genesis.py goals/2025-01-22-1530-rest-api-user-mgmt/ 10

================================
```

## Implementation Notes

- **No Direct Execution**: `/proto_genesis` generates commands but doesn't execute `proto_genesis.py`
- **Goal Directory Dependency**: `proto_genesis.py` expects structured goal directory
- **Manual Control**: User decides when and how to execute the refinement process
- **Session Recovery**: Can re-run `proto_genesis.py` with same goal directory if interrupted
- **Iteration Flexibility**: User can adjust iteration count in generated command

## Exclusion from Export

**IMPORTANT**: This command is explicitly excluded from `/exportcommands` output as specified in requirements. It is an internal development tool for goal refinement workflows.
