# /execute - Auto-Approval Development Orchestrator

**Purpose**: Complete development workflow with automatic approval and TodoWrite tracking

## 3-Phase Workflow

### Phase 1: Planning
- Complexity assessment (simple/medium/complex)
- Execution method decision (parallel vs sequential)
- Tool requirements analysis
- Timeline estimation
- Implementation approach design

### Phase 2: Auto-Approval
- Built-in approval bypass: "User already approves - proceeding with execution"
- No manual intervention required
- Automatic TodoWrite initialization

### Phase 3: Implementation
- TodoWrite orchestration with progress tracking
- Error handling and recovery
- Completion verification
- Automatic testing and validation

## Usage
```
/execute "implement user authentication"
/execute "add payment processing"
/execute "refactor database layer"
```

## Integration
- Used by `/pr` for implementation phase
- Composes with `/test` for validation
- Integrates with `/pushl` for completion