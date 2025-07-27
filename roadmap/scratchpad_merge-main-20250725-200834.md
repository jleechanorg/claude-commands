# A2A Orchestration Implementation - Scratchpad (SIMPLIFIED)

**Branch**: merge-main-20250725-200834
**Goal**: Implement A2A protocol as lightweight wrapper over existing tmux orchestration (NO Redis)
**Date**: 2025-07-26

## Current State

### Existing Orchestration Architecture
- **Current Model**: Centralized hub-and-spoke (Claude → Agents)
- **Infrastructure**: tmux sessions + file-based coordination
- **Agents**: frontend, backend, testing, opus-master
- **Communication**: Claude creates/monitors agents, no direct agent-to-agent communication

### Problems with Current Implementation
- Not true A2A - agents don't communicate directly
- Centralized bottleneck through Claude
- Demo/fake code may exist in orchestration/ directory

## DETAILED IMPLEMENTATION MILESTONES

### Milestone 1: Orchestration Audit & Cleanup (45 min) ⚠️ EXTENDED
**Goal**: Complete understanding of current system and remove existing A2A implementations

**A2A File Audit Complete ✅**:
Found 32 files with A2A references - mix of real implementations, POCs, and tests

**Tasks for Opus**:
1. [ ] Analyze orchestration/ directory structure
   - [ ] Map all Python files and their purposes
   - [ ] Identify entry points and main workflows
   - [ ] Document agent creation and management flow

2. [ ] Execute A2A Cleanup Plan
   **DELETE (11 files)**: Over-engineered Redis/SDK implementations
   - [ ] `PRODUCTION_A2A_INTEGRATION_COMPLETE.md` - Outdated Redis claims
   - [ ] `REAL_A2A_INTEGRATION_COMPLETE.md` - Google SDK docs
   - [ ] `REAL_A2A_POC_RESULTS.md` - Historical POC results
   - [ ] `real_a2a_poc.py` - Google SDK POC (299 lines)
   - [ ] `simple_a2a_poc.py` - SDK attempts (195 lines)
   - [ ] `redis_a2a_bridge.py` - **Complex real implementation** (561 lines)
   - [ ] `tasks/pending/a2a_sdk_integration_task.json` - Old task spec
   - [ ] `test_a2a_with_debug_worker.py` - Redis worker tests
   - [ ] `test_production_a2a_integration.py` - Redis production tests
   - [ ] `test_real_a2a.py` - Google SDK tests
   - [ ] `test_real_a2a_flow.py` - Redis flow tests
   - [ ] `test_real_a2a_integration.py` - Complex Redis tests

   **KEEP/MODIFY (6 files)**: Adaptable for simplified approach
   - [ ] `README_A2A_INTEGRATION.md` - Update for file-based wrapper
   - [ ] `config/a2a_config.yaml` - Simplify configuration
   - [ ] `minimal_a2a_poc.py` - Good FastAPI reference
   - [ ] `test_a2a_integration.py` - Adapt for wrapper testing
   - [ ] `test_simple_a2a.py` - Basic test patterns
   - [ ] `tests/test_a2a_integration.py` - Unit test patterns

   **REPLACE (1 file)**: Core implementation
   - [ ] `a2a_integration.py` - Replace 395-line SDK with simple wrapper

3. [ ] Create baseline documentation
   - [ ] Current architecture diagram
   - [ ] Communication flow documentation
   - [ ] List of preserved components

### Milestone 2: A2A Wrapper Design (20 min)
**Goal**: Design file-based A2A protocol layer

**Tasks for Opus**:
1. [ ] Design file-based communication structure
   ```
   /tmp/orchestration/a2a/
   ├── registry.json          # Agent registry
   ├── agents/
   │   ├── {agent-id}/
   │   │   ├── info.json      # Capabilities, status
   │   │   ├── inbox/         # Incoming messages
   │   │   └── outbox/        # Outgoing messages
   ├── tasks/
   │   ├── available/         # Task pool
   │   ├── claimed/           # In-progress tasks
   │   └── completed/         # Finished tasks
   └── heartbeat/             # Agent health monitoring
   ```

2. [ ] Create A2A protocol specification
   - [ ] Message format (JSON schema)
   - [ ] Message types (discover, claim, collaborate, status)
   - [ ] File naming conventions (timestamps, UUIDs)
   - [ ] Polling intervals and timeouts

3. [ ] Design agent lifecycle
   - [ ] Registration process
   - [ ] Capability advertisement
   - [ ] Task discovery and claiming
   - [ ] Direct agent messaging
   - [ ] Graceful shutdown

### Milestone 3: Core A2A Implementation (45 min)
**Goal**: Build the A2A wrapper layer

**Tasks for Opus**:
1. [ ] Create a2a_protocol.py
   - [ ] A2AMessage class with serialization
   - [ ] FileBasedMessaging class for inbox/outbox
   - [ ] AgentRegistry for discovery
   - [ ] TaskPool for work distribution

2. [ ] Create a2a_agent_wrapper.py
   - [ ] AgentWrapper class that enhances existing agents
   - [ ] Polling mechanism for inbox monitoring
   - [ ] Message routing and delivery
   - [ ] Status reporting and heartbeat

3. [ ] Modify task_dispatcher.py
   - [ ] Add A2A task broadcasting
   - [ ] Implement task claiming protocol
   - [ ] Enable direct agent assignment
   - [ ] Preserve existing tmux integration

4. [ ] Create a2a_monitor.py
   - [ ] Monitor agent health via heartbeats
   - [ ] Clean up stale agent registrations
   - [ ] Track task progress across agents
   - [ ] Report status to Claude

### Milestone 4: Agent Enhancement (30 min)
**Goal**: Add A2A capabilities to existing agents

**Tasks for Opus**:
1. [ ] Enhance create_agent.py
   - [ ] Wrap agents with A2A capabilities
   - [ ] Auto-register agents on creation
   - [ ] Inject A2A client into agent context

2. [ ] Create agent communication examples
   - [ ] Agent-to-agent task delegation
   - [ ] Collaborative task execution
   - [ ] Status synchronization

3. [ ] Update agent templates
   - [ ] Add A2A client usage examples
   - [ ] Show how to discover other agents
   - [ ] Demonstrate direct messaging

### Milestone 5: Integration & Testing (25 min)
**Goal**: Ensure seamless integration with existing system

**Tasks for Opus**:
1. [ ] Update /orch command handler
   - [ ] Integrate A2A task broadcasting
   - [ ] Show agent discovery in status
   - [ ] Display direct communications

2. [ ] Create test scenarios
   - [ ] Single agent task execution
   - [ ] Multi-agent collaboration
   - [ ] Agent failure and recovery
   - [ ] Task reassignment

3. [ ] Validate backwards compatibility
   - [ ] Existing workflows still function
   - [ ] Non-A2A agents work alongside A2A agents
   - [ ] Performance impact assessment

4. [ ] Create migration guide
   - [ ] How to enable A2A for existing agents
   - [ ] Configuration options
   - [ ] Troubleshooting guide

## OPUS EXECUTION PLAN

### What Opus Will Do (Before Sonnet Handoff)

1. **Phase 1: Foundation (60 min)** ⚠️ EXTENDED
   - Complete orchestration audit and cleanup
   - Execute A2A cleanup plan (delete 11 files, modify 6, replace 1)
   - Create clean baseline

2. **Phase 2: Core Implementation (60 min)**
   - Build a2a_protocol.py with all classes
   - Create a2a_agent_wrapper.py
   - Modify task_dispatcher.py for A2A
   - Implement file-based messaging

3. **Phase 3: Integration (30 min)**
   - Enhance create_agent.py
   - Update /orch command
   - Create basic tests

4. **Phase 4: Documentation (15 min)**
   - Write clear handoff notes
   - Document what was built
   - List remaining Sonnet tasks

### What Sonnet Will Do (After Handoff)

1. **Testing & Validation**
   - Run comprehensive tests
   - Fix any issues found
   - Validate A2A communication

2. **Polish & Enhancement**
   - Add error handling
   - Implement retries
   - Add logging

3. **Documentation**
   - Update command documentation
   - Create usage examples
   - Write troubleshooting guide

## Technical Implementation Details

### File-Based A2A Communication Structure
```
/tmp/orchestration/a2a/
├── registry.json              # Central agent registry
├── agents/
│   ├── {agent-id}/
│   │   ├── info.json         # Agent capabilities and status
│   │   ├── inbox/            # Incoming messages (other agents write here)
│   │   │   └── {timestamp}_{from}_msg.json
│   │   ├── outbox/           # Outgoing messages (agent writes here)
│   │   │   └── {timestamp}_{to}_msg.json
│   │   └── heartbeat.json    # Last activity timestamp
├── tasks/
│   ├── available/            # Tasks waiting to be claimed
│   │   └── {task-id}.json
│   ├── claimed/              # Tasks being worked on
│   │   └── {task-id}_{agent-id}.json
│   └── completed/            # Finished tasks
│       └── {task-id}_complete.json
└── logs/
    └── a2a_activity.log      # A2A protocol activity log
```

### A2A Message Schema
```python
{
    "id": "unique-message-id",
    "from_agent": "agent-id",
    "to_agent": "agent-id" | "broadcast",
    "message_type": "discover" | "claim" | "delegate" | "status" | "result",
    "timestamp": 1234567890.123,
    "payload": {
        # Message-specific data
    },
    "reply_to": "original-message-id"  # Optional
}
```

### Agent Capabilities Schema
```python
{
    "agent_id": "unique-agent-id",
    "agent_type": "frontend" | "backend" | "testing" | "opus-master",
    "capabilities": ["javascript", "react", "testing", "python"],
    "status": "idle" | "busy" | "offline",
    "current_task": "task-id" | null,
    "created_at": 1234567890.123,
    "last_heartbeat": 1234567890.123,
    "workspace": "/path/to/agent/workspace"
}
```

## Success Criteria

### Must Have (Opus Completes)
- ✅ A2A protocol layer implemented
- ✅ File-based messaging working
- ✅ Agents can discover each other
- ✅ Tasks can be claimed via A2A
- ✅ Existing /orch still works

### Nice to Have (Sonnet Completes)
- ✅ Full test coverage
- ✅ Comprehensive error handling
- ✅ Performance optimizations
- ✅ Advanced collaboration patterns
- ✅ Monitoring dashboard

## A2A Cleanup Analysis Summary

### Current A2A State Discovery ✅
**Found**: 32 files with A2A references in orchestration/
**Assessment**: Mix of **real implementations**, POCs, and tests

**Key Finding**: The existing A2A system is **authentic and functional** but **over-engineered**
- `redis_a2a_bridge.py` (561 lines) - Sophisticated Redis orchestration with circuit breakers, load balancing
- `a2a_integration.py` (395 lines) - Complex Google A2A SDK integration
- Multiple comprehensive test suites for Redis-based workflows

**Cleanup Decision**: DELETE complex implementations, KEEP adaptable patterns
- **DELETE**: 11 files (Redis/SDK over-engineering)
- **MODIFY**: 6 files (update for simplified approach)
- **REPLACE**: 1 core file (SDK → simple wrapper)

**Impact**: Removes ~2000+ lines of complex but functional A2A code in favor of simple file-based wrapper

## Context & Notes

- **User Request**: "something simpler. No redis. Just use A2A protocol as a wrapper"
- **Key Insight**: A2A as lightweight wrapper over existing tmux system
- **Critical**: No Redis dependency - pure file-based communication
- **Architecture**: Enhance with wrapper, don't replace existing system
- **Cleanup Required**: Remove over-engineered but functional Redis/SDK implementations
- **Opus Focus**: Core implementation, get it working
- **Sonnet Focus**: Polish, test, document

---

**Status**: Detailed plan ready for Opus execution (with A2A cleanup plan)
**Next**: Start with orchestration audit and A2A cleanup
**Handoff**: After core A2A implementation is working
