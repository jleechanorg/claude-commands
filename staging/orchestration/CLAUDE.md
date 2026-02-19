# Orchestration System

This document inherits from the root project documentation. Please refer to `../CLAUDE.md` for project-wide conventions and guidelines.

## Overview

The orchestration system manages distributed multi-agent communication and task execution using tmux sessions, Redis coordination, and Agent-to-Agent (A2A) protocols. It provides scalable, fault-tolerant operations for parallel task processing.

## File Inventory

### Core Orchestration Components
- `orchestrate_unified.py` - Main orchestration engine and task coordination
- `agent_system.py` - Agent lifecycle management and registration
- `agent_monitor.py` - Real-time agent health monitoring and status tracking
- `task_dispatcher.py` - Distributed task routing and execution management
- `message_broker.py` - Redis-backed inter-agent messaging system
- `recovery_coordinator.py` - Task failure detection and recovery orchestration

### Agent-to-Agent (A2A) Communication
- `a2a_integration.py` - Core A2A communication protocols and message handling
- `a2a_agent_wrapper.py` - Agent wrapper for A2A protocol integration
- `a2a_monitor.py` - A2A communication monitoring and diagnostics
- `A2A_DESIGN.md` - Architecture documentation for A2A communication patterns

### Monitoring and Health Management
- `agent_health_monitor.py` - Comprehensive agent health tracking
- `safe_agent_monitor.py` - Fail-safe monitoring with redundancy
- `dashboard.py` - Real-time orchestration dashboard interface
- `debug_task_flow.py` - Task execution flow debugging utilities
- `debug_worker.py` - Individual agent worker debugging tools

### System Management Scripts
- `start_system.sh` - Orchestration system startup automation
- `start_monitor.sh` - Monitoring system initialization
- `monitor_agents.sh` - Agent status monitoring script
- `cleanup_agents.sh` - Agent cleanup and resource management
- `cleanup_completed_agents.py` - Automated cleanup of completed tasks

### Configuration and Constants
- `config/a2a_config.yaml` - A2A communication configuration
- `constants.py` - System-wide constants and configuration values
- `tmux-agent.conf` - tmux session configuration for agents
- `AGENT_SESSION_CONFIG.md` - Agent session management documentation

### Task Management
- `tasks/task_report.json` - Task execution reports and metrics
- `recovery_metrics.json` - Recovery operation statistics

### Testing Infrastructure (tests/)
- `test_a2a_integration.py` - A2A communication protocol testing
- `test_agent_monitor_restart.py` - Agent restart and recovery testing
- `test_end_to_end.py` - Complete system integration testing
- `test_orchestrate_unified.py` - Main orchestration engine testing
- `test_task_dispatcher.py` - Task dispatch logic validation
- `test_security_validation.py` - Security protocol compliance testing
- `test_tmux_session_lifecycle.py` - tmux session management testing

### Test Support and Fixtures
- `tests/fixtures/mock_claude.py` - Claude API mocking for testing
- `tests/fixtures/mock_redis.py` - Redis connection mocking
- `tests/fixtures/mock_tmux.py` - tmux session mocking
- `tests/run_integration_tests.py` - Integration test suite runner
- `tests/ci_integration_tests.sh` - CI/CD integration testing

## System Architecture

### Multi-Agent Design Principles
1. **Distributed Execution** - Tasks distributed across multiple tmux-based agents
2. **Fault Tolerance** - Automatic recovery from agent failures and system issues
3. **Scalable Communication** - Redis-backed A2A messaging with pub/sub patterns
4. **Resource Management** - Dynamic agent allocation and cleanup
5. **Monitoring Integration** - Comprehensive health monitoring and alerting

### Agent Lifecycle Management
1. **Initialization** - Agent startup with configuration loading and Redis connection
2. **Registration** - Capability announcement and system integration
3. **Task Execution** - Continuous task processing from dispatch queues
4. **Health Reporting** - Regular status updates and performance metrics
5. **Graceful Shutdown** - Clean termination with resource cleanup

### A2A Communication Patterns
- **Message Serialization** - JSON-based message formatting with schema validation
- **Reliable Delivery** - Redis streams with acknowledgment and retry mechanisms
- **Event Broadcasting** - Pub/sub patterns for system-wide notifications
- **Direct Messaging** - Point-to-point agent communication channels
- **Dead Letter Handling** - Failed message recovery and manual intervention

## Development Guidelines

### Agent Development Standards
- **Stateless Design** - Agents maintain no persistent local state
- **Idempotent Operations** - All tasks safely repeatable without side effects
- **Error Handling** - Comprehensive exception handling with recovery strategies
- **Logging Integration** - Structured logging with correlation IDs
- **Security Compliance** - Input validation and secure subprocess execution

### Communication Protocol Requirements
- **Message Validation** - JSON schema validation for all inter-agent messages
- **Timeout Handling** - Configurable timeouts with exponential backoff
- **Circuit Breaker Pattern** - Automatic failure detection and isolation
- **Monitoring Integration** - Message tracking and performance metrics

### Testing Standards
- **Unit Testing** - Individual component testing with mocking frameworks
- **Integration Testing** - End-to-end workflows with real Redis connections
- **Performance Testing** - Load testing and capacity planning validation
- **Security Testing** - Vulnerability assessment and penetration testing

## Operational Management

### System Startup
```bash
./orchestration/start_system.sh start    # Full system initialization
./orchestration/start_monitor.sh         # Monitoring system only
```

### Agent Monitoring
```bash
./orchestration/monitor_agents.sh        # Real-time agent status
python3 orchestration/dashboard.py       # Web-based dashboard
```

### System Cleanup
```bash
./orchestration/cleanup_agents.sh        # Manual cleanup
python3 orchestration/cleanup_completed_agents.py  # Automated cleanup
```

### Debug and Diagnostics
```bash
python3 orchestration/debug_task_flow.py --task-id=<id>
python3 orchestration/debug_worker.py --agent-id=<id>
```

## Quality Assurance

The orchestration system maintains high-quality standards through:
- **Comprehensive Testing** - 90%+ test coverage across all components
- **Monitoring Integration** - Real-time health and performance tracking
- **Security Validation** - Regular security audits and vulnerability assessment
- **Documentation Standards** - Complete API documentation and usage examples
- **Recovery Testing** - Regular disaster recovery simulations

## Common Usage Patterns

### Task Orchestration
```python
from orchestration.orchestrate_unified import OrchestrationEngine
engine = OrchestrationEngine()
task_id = engine.dispatch_task(task_definition, agents=['agent1', 'agent2'])
result = engine.wait_for_completion(task_id)
```

### A2A Communication
```python
from orchestration.a2a_integration import A2AIntegration
a2a = A2AIntegration()
a2a.send_message(target_agent='worker1', message_type='task_request', payload=data)
response = a2a.wait_for_response(correlation_id)
```

See also: [../CLAUDE.md](../CLAUDE.md) for complete project protocols and development guidelines.