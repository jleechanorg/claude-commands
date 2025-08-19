# Tmux Agent Creation Directory Requirement

## Overview
During `/orchconverge` operations, all tmux agents **must** be created in Claude's current working directory to ensure proper execution context and file system access.

## Key Requirements

### 1. Agent Creation Directory
- Tmux agents must be instantiated in Claude's current working directory
- Absolute paths should be avoided; use relative paths from working directory
- Directory context is established at orchestration initialization

### 2. Context Preservation
- Working directory context ensures agents access correct configuration files
- File I/O operations depend on proper directory context
- Environment variables and relative path resolutions require consistent directory

### 3. Execution Criticality
- Agent execution failures will occur if directory context is lost
- Convergence operations rely on shared file access within working directory
- Directory changes during agent lifecycle break orchestration integrity

### 4. Implementation Guidance

#### Agent Initialization
```bash
# Correct approach
cd $CLAUDE_WORKING_DIR
tmux new-session -d -s agent_session

# Incorrect approach 
tmux new-session -d -s agent_session -c /different/path
```

#### Integration Requirements
- Orchestration system must preserve working directory context
- Agent communication protocols should reference relative paths
- File access operations must be scoped to working directory
- Directory validation should occur before agent creation

## Impact
Failure to adhere to this requirement will result in:
- File not found errors during convergence
- Context mismatch between agents
- Orchestration operation failures
- Inconsistent agent behavior across environments

## Integration with Orchestration System

### Directory Context Validation
Before creating any tmux agents, the orchestration system must:
1. Verify current working directory matches Claude's execution context
2. Validate that required files and configurations are accessible
3. Set proper environment variables for agent execution
4. Document working directory for debugging purposes

### Agent Lifecycle Management
- All agent operations must maintain working directory consistency
- File operations should use relative paths when possible
- Directory changes within agents require explicit documentation
- Agent cleanup must account for working directory state

## Compliance Verification
To ensure compliance with this requirement:
- Log working directory at agent creation time
- Validate file access before executing convergence operations
- Monitor agent execution for directory-related errors
- Test agent creation in different directory contexts during development