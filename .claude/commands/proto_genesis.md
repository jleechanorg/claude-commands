# /proto_genesis - Interactive Goal Refinement System Setup

**Command Summary**: Sets up goal refinement using `/goal` command, then generates copy-paste command for `proto_genesis.py` execution

**Usage**: `/proto_genesis "goal description"`

**Purpose**: Two-phase goal refinement workflow:
1. **Interactive Goal Setup**: Uses `/goal` to create detailed goal specification with user collaboration
2. **Command Generation**: Provides ready-to-copy `proto_genesis.py` command for execution

## Execution Instructions

When this command is invoked with a goal:

### Phase 1: Interactive Goal Refinement
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
3. **Generate Proto Genesis Execution Command**:
   - Determine the goal directory path from `/goal` output
   - Ask user for preferred number of iterations (default: 10)
   - Generate ready-to-copy command in this format:
   ```bash
   python proto_genesis.py goals/YYYY-MM-DD-HHMM-[slug]/ 10
   ```

4. **Present Copy-Paste Command**:
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

## Workflow Benefits

### Interactive Goal Refinement
- **Structured Process**: Uses `/goal` command's proven goal processing
- **Memory Integration**: Leverages goal patterns and historical data
- **User Collaboration**: Interactive refinement until user satisfaction
- **Persistent Storage**: Goal stored in organized directory structure

### Manual Execution Control
- **Copy-Paste Convenience**: Ready command for terminal execution
- **Iteration Control**: User specifies iteration count upfront
- **Session Independence**: Can execute `ralph.py` later or multiple times
- **Manual Oversight**: User controls when and how execution happens

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
- **Validation**: Use exit criteria from goal directory for consensus

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
