# Orchestration System End-to-End Test Planning

## Project Goal
Create comprehensive end-to-end tests that verify the orchestration system's correct code flow: request → A2A → tmux agent creation. Mock external dependencies but NOT internal Python method calls.

## Implementation Plan
Develop a test suite that validates the orchestration workflow by mocking external dependencies (tmux, git, Claude CLI, Redis) while preserving internal Python method calls for authentic code flow verification.

## Current State
Basic test infrastructure exists but needs comprehensive coverage of the orchestration workflow including A2A integration, agent creation, and error handling scenarios.

## Next Steps
1. Create test directory structure
2. Implement mock fixtures for external dependencies
3. Write basic flow tests first
4. Add A2A integration tests
5. Add error handling tests
6. Add performance/load tests

## Key Context

## Key Testing Requirements

### 1. What to Mock (External Dependencies)
- **tmux commands** - Mock subprocess calls to tmux (session creation, listing, etc.)
- **git commands** - Mock worktree creation, branch operations
- **gh CLI** - Mock PR creation and viewing
- **Claude CLI** - Mock the actual Claude execution (subprocess.run for claude command)
- **Redis** - Mock Redis connection/operations if testing with Redis enabled
- **File system** - Use temp directories for agent workspaces and result files

### 2. What NOT to Mock (Internal Code Flow)
- Python method calls between modules
- Task dispatcher logic
- A2A protocol implementation
- Message broker initialization
- Agent creation logic
- Capability scoring algorithms

## Test Scenarios

### Scenario 1: Basic Task Execution Flow
```python
def test_basic_task_flow():
    """Test: User request → orchestrate_unified → task_dispatcher → agent creation"""
    # Given: A simple task request
    task = "Fix all failing tests"
    
    # When: orchestrate_unified.py is called
    # Then: Verify the call chain:
    # 1. UnifiedOrchestration.orchestrate() called
    # 2. TaskDispatcher.analyze_task_and_create_agents() called
    # 3. TaskDispatcher.create_dynamic_agent() called
    # 4. tmux session created (mocked)
    # 5. Agent registered with A2A if available
```

### Scenario 2: A2A Integration Flow
```python
def test_a2a_integration():
    """Test: Agent creation → A2A registration → Redis messaging"""
    # Given: Redis is available
    # When: Agent is created
    # Then: Verify:
    # 1. MessageBroker initialized
    # 2. Agent registered with A2A protocol
    # 3. Redis messages published
    # 4. A2A bridge receives registration
```

### Scenario 3: Fallback to File Coordination
```python
def test_file_coordination_fallback():
    """Test: Redis unavailable → File-based coordination"""
    # Given: Redis connection fails
    # When: System starts
    # Then: Verify:
    # 1. File-based coordination activated
    # 2. Result files created in /tmp/orchestration_results
    # 3. No Redis operations attempted
```

### Scenario 4: Multi-Agent Task Distribution
```python
def test_multi_agent_creation():
    """Test: Complex task → Multiple agents created"""
    # Given: Task requiring parallel work
    task = "Update UI, fix backend bugs, and run all tests"
    
    # When: Task analyzed
    # Then: Verify:
    # 1. Multiple agents created (if LLM decides so)
    # 2. Each agent gets unique workspace
    # 3. Each agent gets unique tmux session
    # 4. All agents registered with A2A
```

### Scenario 5: Agent Restart Handling
```python
def test_agent_restart():
    """Test: Existing conversation → --continue flag used"""
    # Given: Agent conversation file exists
    # When: Agent created with same name
    # Then: Verify --continue flag added to claude command
```

## Shell Scripts vs Direct Python

### Current Approach (Shell Scripts)
**Pros:**
- Quick one-liners from terminal
- Easy for users to remember
- Handles environment setup
- Can be run from any directory

**Cons:**
- Extra layer of indirection
- Harder to test
- Shell script maintenance

### Direct Python Usage
```bash
# Standard orchestration command:
python3 orchestration/orchestrate_unified.py "Fix tests"
```

**Recommendation**: Use direct Python entry points for orchestration. Benefits:
1. Simpler maintenance
2. Direct integration with Python ecosystem
3. No shell script dependency layer
3. Providing shorter commands
4. Handling common error cases

## Mock Implementation Strategy

### 1. Mock tmux Operations
```python
@patch('subprocess.run')
def test_tmux_session_creation(mock_run):
    """Mock tmux session creation"""
    # Setup mock to succeed for tmux commands
    mock_run.return_value = Mock(returncode=0, stdout='', stderr='')
    
    # Run agent creation
    # Verify tmux new-session called with correct args
```

### 2. Mock Claude Execution
```python
@patch('subprocess.run')
def test_claude_execution(mock_run):
    """Mock claude CLI execution"""
    def side_effect(cmd, **kwargs):
        if 'claude' in cmd[0]:
            # Simulate claude running
            return Mock(returncode=0)
        return original_run(cmd, **kwargs)
    
    mock_run.side_effect = side_effect
```

### 3. Mock Redis (Optional)
```python
@patch('redis.Redis')
def test_with_redis(mock_redis_class):
    """Test with Redis available"""
    mock_redis = Mock()
    mock_redis_class.return_value = mock_redis
    
    # Run orchestration
    # Verify Redis operations called
```

## Test File Structure
```
orchestration/tests/
├── test_orchestrate_unified.py    # Main orchestration tests
├── test_task_dispatcher.py        # Task analysis and agent creation
├── test_a2a_integration.py        # A2A protocol tests
├── test_message_broker.py         # Redis messaging tests
├── test_end_to_end.py            # Full flow integration tests
└── fixtures/                      # Test data and mocks
    ├── mock_tmux.py
    ├── mock_claude.py
    └── mock_redis.py
```

## Key Assertions

### Code Flow Verification
1. Assert method call order matches expected flow
2. Assert correct parameters passed between components
3. Assert no skipped steps in the flow

### Agent Creation Verification
1. Assert agent workspace created
2. Assert tmux session started
3. Assert correct prompt generated
4. Assert result file path created

### A2A Protocol Verification
1. Assert agent registered with correct capabilities
2. Assert messages published to correct channels
3. Assert A2A bridge receives registration

## Implementation Notes

### Using unittest.mock
```python
from unittest.mock import patch, Mock, call

# Track method calls without blocking execution
with patch.object(TaskDispatcher, 'create_dynamic_agent', wraps=dispatcher.create_dynamic_agent) as mock_create:
    # Run test
    # Assert mock_create.called
    # Assert mock_create.call_args
```

### Temporary File System
```python
import tempfile
import shutil

class TestOrchestration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.test_dir)
    
    def tearDown(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.test_dir)
```

### Capturing Logs
```python
import logging

# Capture orchestration logs for verification
with self.assertLogs('orchestration', level='INFO') as cm:
    # Run orchestration
    # Assert expected log messages in cm.output
```

## Next Steps

1. Create test directory structure
2. Implement mock fixtures for external dependencies
3. Write basic flow tests first
4. Add A2A integration tests
5. Add error handling tests
6. Add performance/load tests

## Questions to Resolve

1. Should we test actual LLM task analysis or mock it?
   - **Recommendation**: Mock for unit tests, real for integration tests

2. How to handle async Redis operations in tests?
   - **Recommendation**: Use synchronous mocks for predictability

3. Should we test shell scripts separately?
   - **Recommendation**: Test Python directly, shell scripts are just wrappers

4. How to verify agent actually completes tasks?
   - **Recommendation**: Mock completion by writing to result files

## Success Criteria

- [ ] All code paths covered (>90% coverage)
- [ ] External dependencies properly mocked
- [ ] Internal flow verified without mocking
- [ ] Tests run quickly (<5 seconds total)
- [ ] Clear failure messages when flow breaks
- [ ] Easy to add new test scenarios

## Branch Info
Working on orchestration-clean-from-main branch for PR #944. This test planning supports the clean orchestration system implementation with dynamic agent creation and monitoring capabilities.