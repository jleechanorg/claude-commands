# Orchestration Manager Product Specification

**Feature**: Multi-Directory Orchestration Manager System
**Command**: `/orchestrate-manager` (alias: `/orchm`)
**Version**: 1.3
**Date**: 2025-10-11
**Status**: Implementation Phase - Production Constraints Integrated
**Framework**: LangGraph v1.0 alpha
**Non-Negotiable**: Slack MCP Integration

## Command Summary

**Usage**
```bash
/orchestrate-manager "<goal>" [--dirs name:path ...] [--auto-detect-worktrees] [--help]
/orchm "<goal>" [--dirs name:path ...] [--auto-detect-worktrees] [--help]
```

**Primary Options**
- `--dirs name:path` — Explicit directory or repository targets (repeatable)
- `--auto-detect-worktrees` — Scan the current repository for available git worktrees
- `--help` — Display inline usage details and advanced flags

**Prerequisites**
- Slack MCP credentials with access to the `#agent-orchestration` channel
- Existing `/orchestrate`-compatible tmux agents (Claude builders + Codex verifiers)
- Redis instance for A2A message transport and task state storage

**Example**
```bash
/orchm "Ship auth feature across API, SDK, docs" \
  --dirs api:~/projects/api \
         sdk:~/projects/sdk \
         docs:~/projects/docs
```

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Goals & Objectives](#goals--objectives)
3. [User Stories](#user-stories)
4. [Feature Requirements](#feature-requirements)
5. [User Journey Maps](#user-journey-maps)
6. [System Interaction Patterns](#system-interaction-patterns)
7. [Success Criteria](#success-criteria)
8. [Metrics & KPIs](#metrics--kpis)

## Executive Summary

### Overview

The Orchestration Manager (`/orchestrate-manager` or `/orchm`) is an advanced multi-directory orchestration system that enables a single manager agent to coordinate multiple coding agents across different directories, worktrees, and even repositories. It extends the existing `/orchestrate` command (which works within a single directory) to support complex, distributed development workflows.

**v1.3 Update**: Integrates production-grade implementation constraints including idempotency guarantees, authority models, source-of-truth architecture, zero-trust verification, and realistic performance targets. Framework selection: **LangGraph (v1.0 alpha)** for graph-based stateful execution with enhanced control over approvals, dependencies, and recovery.

**Key Technology Definitions**:
- **Slack MCP** (Model Context Protocol): Anthropic's standard for structured communication between Claude and external services like Slack. Enables real-time agent collaboration via Slack API with typed message schemas and tool integration.
- **A2A Protocol**: Our internal Agent-to-Agent communication protocol for distributed tmux agents. Note: This is distinct from Google's Agent2Agent (A2A) protocol (launched April 2025), which uses HTTPS/JSON-RPC transport. Our implementation uses Redis Streams-backed messaging optimized for local tmux orchestration with durable delivery and replay.

### User Value Proposition

**For Solo MVP Developers**:
- **Multi-Repository Coordination**: Work on related changes across multiple repos simultaneously (e.g., API server + client library + documentation site)
- **Worktree Management**: Manage parallel development efforts across git worktrees without context switching
- **Agent Specialization**: Dedicated claude agents for coding/testing, codex agents for test verification
- **Collaborative AI**: Agents communicate via Slack, with manager approval flow for suggestions
- **Protocol Compliance**: All agents support A2A protocol and can operate as MCP servers

### Success Metrics

- **Time Savings**: 60%+ reduction in cross-repo coordination overhead
- **Error Reduction**: 80%+ decrease in integration errors across repos
- **Agent Efficiency**: 70%+ agent utilization across all managed directories
- **Communication Quality**: 90%+ manager approval rate for agent suggestions

## Goals & Objectives

### Primary Goals

1. **Multi-Directory Orchestration**: Enable single manager to coordinate agents across unlimited directories/repos
2. **Agent Specialization**: Implement claude (coding/testing) and codex (verification) role separation
3. **Communication System**: Real-time Slack-based agent collaboration with manager approval workflow
4. **Protocol Compliance**: Full A2A protocol support + MCP server wrapping for all agents

### Secondary Goals

1. **Worktree Optimization**: Seamless git worktree management for parallel development
2. **Resource Efficiency**: Intelligent agent reuse and lifecycle management
3. **Error Recovery**: Robust failure handling across distributed agent network
4. **Developer Experience**: Natural language task specification with automatic routing

## User Stories

### US1: Multi-Repository Feature Development

**As a** solo developer working on a fullstack application
**I want** to coordinate changes across API server, client SDK, and docs repos
**So that** I can implement features end-to-end without manual coordination overhead

**Acceptance Criteria**:
- [ ] Manager agent spawns claude/codex pairs in each specified directory
- [ ] Agents work on related tasks simultaneously (API endpoint + SDK method + documentation)
- [ ] Codex agents verify tests pass in each repo before declaring success
- [ ] Manager collects results and reports unified status

**Example Command**:
```bash
/orchm "Add authentication feature to API, update client SDK, and document usage" \
  --dirs api-server:~/projects/api \
        client-sdk:~/projects/sdk \
        docs-site:~/projects/docs
```

### US2: Git Worktree Parallel Development

**As a** developer using git worktrees for feature isolation
**I want** to have agent pairs in each worktree working independently
**So that** I can develop multiple features in parallel without branch conflicts

**Acceptance Criteria**:
- [ ] Manager detects worktrees automatically or accepts explicit paths
- [ ] Each worktree gets dedicated claude (code) + codex (verify) agents
- [ ] Agents stay isolated to their worktree boundaries
- [ ] Results aggregated at manager level with per-worktree status

**Example Command**:
```bash
/orchm "Fix bug #123 in feature-auth worktree and bug #124 in feature-payments worktree" \
  --auto-detect-worktrees
```

### US3: Agent Communication with Manager Approval

**As a** manager agent coordinating multiple coding agents
**I want** agents to collaborate via Slack with my approval for cross-agent suggestions
**So that** agents can help each other while I maintain oversight and control

**Acceptance Criteria**:
- [ ] All agents post to #agent-orchestration Slack channel
- [ ] Manager can give direct orders to any agent
- [ ] Agents can suggest ideas to each other (visible to all in Slack)
- [ ] Manager must explicitly approve agent suggestions before execution
- [ ] Conversation history maintained for transparency and debugging

**Example Interaction**:
```
[Slack #agent-orchestration]
Manager: "@claude-api Implement user authentication endpoint"
Claude-API: "Working on authentication endpoint... need database schema"
Claude-API: "@codex-api Can you verify the existing user table schema?"
Manager: "Approved - @codex-api please check schema and report back"
Codex-API: "Schema verified. Users table has email, password_hash, created_at columns"
Claude-API: "Thanks! Implementing endpoint with those fields"
```

### US4: A2A Protocol and MCP Server Support

**As a** system integrator
**I want** all orchestration agents to support A2A protocol and operate as MCP servers
**So that** external systems can integrate with the orchestration network

**Acceptance Criteria**:
- [ ] Every tmux agent implements A2A protocol for inter-agent messaging
- [ ] Agents can be wrapped as MCP servers exposing orchestration capabilities
- [ ] External MCP clients can send tasks to manager agent
- [ ] A2A messages follow existing protocol specification (JSON schema validation, Redis streams)

**Example Integration**:
```python
# External MCP client sending task to manager
from mcp import Client
client = Client("orchestration-manager-mcp")
result = client.call_tool("coordinate_task", {
    "goal": "Add feature X across all repos",
    "directories": ["api", "sdk", "docs"]
})
```

### US5: Natural Language Goal Specification

**As a** developer
**I want** to specify complex cross-repo tasks in natural language
**So that** I don't need to write detailed task breakdowns for each directory

**Acceptance Criteria**:
- [ ] Manager accepts natural language goal description
- [ ] Manager automatically determines which directories need agents
- [ ] Manager assigns appropriate tasks to each agent based on goal
- [ ] Manager handles task dependencies (e.g., API before SDK)

**Example**:
```bash
/orchm "Upgrade authentication system to use JWT tokens instead of sessions.
        Update API server, regenerate OpenAPI docs, update Python SDK,
        update JavaScript SDK, and add migration guide to docs."
```

## Feature Requirements

### Functional Requirements

#### FR1: Multi-Directory Agent Management

**Description**: Manager spawns and coordinates claude/codex agent pairs across multiple directories

**Requirements**:
- Support unlimited number of directories (limited only by system resources)
- Each directory gets paired agents: claude (coding/testing) + codex (verification)
- Directory can be: local path, git worktree, different repository
- Manager tracks all agent states and aggregates results

#### FR2: Agent Role Specialization

**Description**: Enforce separation of responsibilities between builder and verifier agents (model-agnostic roles)

**Naming Convention**: Use role-based naming (`builder`, `verifier`) rather than model-specific names (`claude`, `codex`) to support future model swaps and fine-tuning.

**Builder Agent Responsibilities**:
- Write code implementations
- Run tests (execute test commands for fast feedback)
- Fix code based on test failures
- Commit changes to git

**Verifier Agent Responsibilities** (Zero-Trust Model):
- **Re-run tests in clean environment** (do NOT trust builder output)
- Enforce quality gates: tests, lint, type-check, coverage thresholds
- Validate acceptance criteria met
- Check code quality standards
- Approve or reject builder agent's work

**Interaction Pattern**:
```
Manager → Builder: "Implement feature X"
Builder → Manager: "Implementation complete, fast-loop tests passing"
Manager → Verifier: "Verify feature X in ~/api"
Verifier → [Re-runs tests in isolated environment]
Verifier → Manager: "Verified: All gates passed (tests: 15/15, coverage: 85%, lint: clean)"
Manager → User: "Feature X complete in directory ~/api (commit: abc123)"
```

**Zero-Trust Rationale**: Builder could have bugs, be compromised, or accidentally report false positives. Verifier provides independent validation by re-executing all quality gates in a clean environment.

#### FR3: Slack Communication System

**Description**: All agents communicate via Slack MCP in dedicated channel

**Requirements**:
- Dedicated #agent-orchestration channel
- Manager posts task assignments (visible to all)
- Agents post status updates and questions
- Agents can @mention each other for suggestions
- Manager must approve all agent-to-agent suggestions before execution
- Conversation threaded by task ID for organization
- **Rate Limiting Mitigation**: Implement message queue with priority levels (critical/normal/debug). Batch non-critical messages every 2 seconds. Critical messages (errors, approval requests) sent immediately. Maximum 1 message/second per bot to comply with Slack API limits

**Message Format**:
```
[Manager → All] 🎯 Task #1234: Add authentication to API server
[Claude-API] 🔨 Starting implementation...
[Claude-API] @Codex-API Need schema verification before proceeding
[Manager] ✅ Approved: @Codex-API verify user table schema
[Codex-API] ✓ Schema verified: email, password_hash, created_at
[Claude-API] 🎉 Implementation complete, tests passing
[Manager] ✅ Task #1234 complete
```

#### FR4: A2A Protocol Support

**Description**: All agents implement A2A (Agent-to-Agent) protocol for distributed communication

**Requirements**:
- JSON message schema validation
- Redis streams for message transport
- Acknowledgment and retry mechanisms
- Dead letter handling for failed messages
- Monitoring and diagnostics integration

**Example A2A Message**:
```json
{
  "message_id": "msg_1234567890",
  "from_agent": "manager",
  "to_agent": "claude-api",
  "message_type": "task_assignment",
  "timestamp": "2025-01-11T10:30:00Z",
  "payload": {
    "task_id": "task_1234",
    "goal": "Implement JWT authentication",
    "directory": "~/projects/api-server",
    "priority": "high"
  },
  "correlation_id": "correlation_abc123"
}
```

#### FR5: MCP Server Wrapping

**Description**: Every tmux orchestration agent can operate as an MCP server

**Requirements**:
- Expose agent capabilities as MCP tools
- Accept external MCP client connections
- Maintain backwards compatibility with tmux-based orchestration
- Support both direct tmux interaction and MCP RPC calls

**MCP Tool Example**:
```json
{
  "name": "assign_task",
  "description": "Assign coding task to directory-specific agent",
  "parameters": {
    "directory": {"type": "string", "description": "Target directory path"},
    "task_description": {"type": "string", "description": "Natural language task"},
    "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]}
  }
}
```

#### FR6: Automatic Directory Detection

**Description**: Manager intelligently determines which directories need agents

**Detection Strategies**:
1. **Explicit paths**: User provides `--dirs` flag with directory mappings
2. **Worktree detection**: Scan current repo for git worktrees
3. **Related repos**: Detect related repositories (e.g., API + SDK in same parent dir)
4. **Natural language parsing**: Extract directory references from goal description

**Example**:
```bash
# Explicit
/orchm "Fix bug X" --dirs api:~/api,sdk:~/sdk

# Worktree auto-detect
/orchm "Fix bug X" --auto-detect-worktrees

# Natural language
/orchm "Update the API server at ~/api and SDK at ~/sdk to use new auth"
# Manager extracts: ~/api, ~/sdk
```

### Non-Functional Requirements

#### NFR1: Performance

- Manager initialization: < 2 seconds
- Agent spawn time: < 3 seconds per agent
- **Slack message latency**: P95 < 2s (tracked, not committed - Slack offers no hard latency SLO). Alert threshold: P95 > 2s.
- **A2A message latency**: < 100ms (same-host), < 500ms (cross-host). Define per-tier SLOs in deployment config.
- Support 20+ concurrent agents without degradation
- **Slack Rate Limiting**: Message batching with 2-second flush intervals to respect Slack API limits (1 message/second per bot). Queue non-critical updates (debug, progress) separately from critical messages (errors, completions)
- **Concurrency Policy**: Max 20 agents per host, queueing with backpressure for additional tasks

#### NFR2: Reliability

- Manager uptime: 99.9% during orchestration session
- Agent crash recovery: automatic restart within 5 seconds (manager heartbeat monitoring every 10s, 3 missed = crash)
- Network partition handling: graceful degradation with local fallback
- **Data persistence**: All task state persisted to Redis (source of truth). Slack is write-through mirror, NOT authoritative.
- **Message delivery**: At-least-once with deduplication (no "zero data loss" guarantee). Idempotent handlers required.
- **Failure Policy**: Max 3 retries per task with exponential backoff. After 3 failures, escalate to human for manual intervention.

#### NFR3: Security

- **Process Isolation**: Ephemeral worktrees per run (`worktrees/{task_id}/{dir_key}`). UID sandbox, allowlist environment variables.
- **Filesystem Boundaries**: Restrict to target directory. Deny `..` path traversal and symlinks.
- **Slack Authentication**: Bot token scoped to single workspace/channel. Rotate per session. Never post secrets to Slack.
- **Token Scoping**: Per-directory env files mounted read-only for secrets.
- **A2A Message Validation**: JSON schema enforcement with correlation IDs.
- **Subprocess Security**: `shell=False`, input sanitization, timeout enforcement.
- **Network Egress Policy**: Allowlist registries and CI endpoints per agent.

#### NFR4: Observability

- Real-time agent status dashboard (via tmux + Slack)
- Structured logging with correlation IDs
- Prometheus metrics for agent health
- Slack-based notification system for critical events

#### NFR5: Usability

- Natural language task specification (no complex syntax required)
- Self-documenting commands (`/orchm --help`)
- Progress visibility (Slack channel shows real-time updates)
- Error messages with actionable suggestions

## User Journey Maps

### Journey 1: Cross-Repo Feature Implementation

**Scenario**: Developer needs to add payment processing across API, SDK, and docs

```
[Start] Developer types command
    ↓
[Manager] Parses goal, identifies 3 directories needed
    ↓
[Manager] Spawns 6 agents: 3 claude (code) + 3 codex (verify)
    ↓
[Manager → Slack] Posts: "🎯 Task: Add payment processing (3 directories)"
    ↓
[Manager → Agents] Assigns subtasks:
    - Claude-API: "Implement /pay endpoint"
    - Claude-SDK: "Add pay() method to SDK"
    - Claude-Docs: "Document payment integration"
    ↓
[Claude agents] Work in parallel, post updates to Slack
    ↓
[Claude-API → Slack] "Need payment provider API key format"
[Claude-SDK → Slack] "@Claude-API what's the endpoint signature?"
[Manager] Approves: "@Claude-API share signature with @Claude-SDK"
    ↓
[Claude agents] Complete implementations, run tests
    ↓
[Claude-API → Codex-API] "Tests running: 23/23 passing"
[Claude-SDK → Codex-SDK] "Tests running: 15/15 passing"
[Claude-Docs → Codex-Docs] "Docs built successfully"
    ↓
[Codex agents] Verify and report to manager
    ↓
[Manager → Slack] "✅ Payment processing complete across all 3 repos"
    ↓
[Manager → User] Returns unified result with commit SHAs from each repo
[End]
```

### Journey 2: Worktree Parallel Development

**Scenario**: Developer working on 2 bugs in separate worktrees

```
[Start] Developer: /orchm "Fix bug #123 and #124" --auto-detect-worktrees
    ↓
[Manager] Scans for worktrees:
    - Finds: worktree_bug123 (~/projects/main-worktrees/bug123)
    - Finds: worktree_bug124 (~/projects/main-worktrees/bug124)
    ↓
[Manager] Spawns 4 agents total (2 per worktree)
    ↓
[Manager → Slack] "🎯 Working on 2 bugs in parallel worktrees"
    ↓
[Agents] Work independently in isolation
[Claude-bug123] Fixes #123, runs tests
[Codex-bug123] Verifies fix
[Claude-bug124] Fixes #124, runs tests
[Codex-bug124] Verifies fix
    ↓
[Manager] Aggregates results
[Manager → Slack] "✅ Both bugs fixed and verified"
    ↓
[Manager → User] "Bug #123: Fixed in worktree_bug123 (commit abc123)
                 Bug #124: Fixed in worktree_bug124 (commit def456)"
[End]
```

### Journey 3: Agent Collaboration with Manager Approval

**Scenario**: Agents need to share information during implementation

```
[Start] Manager assigns task to Claude-API
    ↓
[Claude-API] Starts implementation, encounters question
[Claude-API → Slack] "@Claude-SDK Do you have a helper function for email validation?"
    ↓
[Manager sees suggestion, evaluates]
[Manager → Slack] "✅ Approved: @Claude-SDK share email validation helper with @Claude-API"
    ↓
[Claude-SDK → Slack] "Yes, validate_email() in utils.py:42"
    ↓
[Claude-API] Uses suggested function, continues implementation
[Claude-API → Slack] "Thanks! Used validate_email(), feature complete"
    ↓
[Codex-API] Verifies tests pass
    ↓
[Manager → Slack] "✅ Task complete"
[End]
```

## System Interaction Patterns

### Agent Hierarchy

```
                    Manager Agent
                         |
        +----------------+----------------+
        |                |                |
    Directory A      Directory B      Directory C
        |                |                |
    +---+---+        +---+---+        +---+---+
    |       |        |       |        |       |
Claude-A Codex-A  Claude-B Codex-B  Claude-C Codex-C
```

### Communication Flows

#### 1. Manager → Agent (Task Assignment)
```
Manager --[Slack + A2A]--> Claude Agent
                           ↓
                      Execute Task
                           ↓
                      Run Tests
                           ↓
                  [Slack] "Tests passing"
                           ↓
Manager <--[A2A]-- Codex Agent (Verification)
```

#### 2. Agent → Agent (with Manager Approval)
```
Claude-A --[Slack]--> "Suggestion for Claude-B"
                           ↓
                      Manager sees
                           ↓
                  Manager evaluates
                           ↓
Manager --[Slack]--> "✅ Approved" OR "❌ Denied"
                           ↓
                    (if approved)
                           ↓
Claude-B <--[Slack]-- Receives suggestion
```

#### 3. External MCP Client → Manager
```
MCP Client --[MCP RPC]--> Manager Agent (wrapped as MCP server)
                               ↓
                        Parse request
                               ↓
                        Spawn agents
                               ↓
                        Coordinate work
                               ↓
MCP Client <--[MCP RPC]-- Return results
```

## Success Criteria

### Feature Complete Checklist

- [ ] `/orchm` command alias registered and functional
- [ ] Manager agent spawns claude/codex pairs per directory
- [ ] Slack MCP integration with #agent-orchestration channel
- [ ] Manager can assign tasks to agents via Slack
- [ ] Agents can post updates and suggestions to Slack
- [ ] Manager approval workflow for agent-to-agent suggestions
- [ ] A2A protocol implemented for all agents
- [ ] MCP server wrapping for all tmux agents
- [ ] Automatic worktree detection working
- [ ] Natural language goal parsing functional
- [ ] Multi-repository coordination tested end-to-end
- [ ] Agent crash recovery and health monitoring
- [ ] Comprehensive test coverage (unit + integration)
- [ ] Documentation complete (user guide + architecture)

### Performance Benchmarks

- [ ] Manager initialization < 2s
- [ ] Agent spawn time < 3s per agent
- [ ] Support 20+ concurrent agents
- [ ] Slack message latency < 500ms
- [ ] A2A message latency < 100ms
- [ ] Zero data loss during agent crashes
- [ ] 95% agent utilization during active tasks

### User Acceptance Tests

#### UAT1: Basic Multi-Directory Orchestration
```bash
# Command
/orchm "Add feature X to ~/api and ~/sdk"

# Expected
✅ Manager spawns 4 agents (2 claude, 2 codex)
✅ Tasks assigned correctly to api and sdk agents
✅ Slack channel shows progress updates
✅ Both directories complete successfully
✅ Manager returns unified result
```

#### UAT2: Worktree Auto-Detection
```bash
# Command (in repo with 3 worktrees)
/orchm "Fix bug Y" --auto-detect-worktrees

# Expected
✅ Manager detects all 3 worktrees automatically
✅ Spawns 6 agents (3 claude, 3 codex)
✅ Each worktree processed independently
✅ Results aggregated per worktree
```

#### UAT3: Agent Collaboration
```bash
# Scenario: Claude-API needs info from Claude-SDK

# Expected Slack flow
[Claude-API] "@Claude-SDK What's the SDK version number?"
[Manager] "✅ Approved: @Claude-SDK answer version question"
[Claude-SDK] "Version 2.3.1"
[Claude-API] "Thanks! Updated API compatibility check"
```

#### UAT4: MCP External Integration
```python
# External MCP client
from mcp import Client
client = Client("orchestration-manager-mcp")
result = client.call_tool("coordinate_task", {
    "goal": "Update dependencies in all repos",
    "directories": ["api", "sdk", "docs"]
})

# Expected
✅ Manager receives MCP request
✅ Spawns agents for all 3 directories
✅ Coordinates dependency updates
✅ Returns MCP-formatted result to client
```

## Metrics & KPIs

### Adoption Metrics

- **Command Usage**: # of `/orchm` invocations per week
- **Directory Count**: Average # of directories per orchestration session
- **Agent Count**: Total # of agents spawned per session

### Performance Metrics

- **Time to Complete**: Total time from command to final result (wall clock time)
- **Agent Utilization**: busy_time / wall_time per agent (from heartbeat spans). Baseline: Measure current single-agent `/orchestrate` utilization.
- **Parallel Efficiency**: seq_time / parallel_time computed from run spans. Baseline: Sequential execution time of same tasks.

### Quality Metrics

- **Success Rate**: % of orchestration sessions completing without errors. **Baseline needed**: Establish by measuring current `/orchestrate` success rate over 2 weeks.
- **Test Pass Rate**: % of verifier validations passing on first attempt
- **Manager Approval Rate**: % of agent suggestions approved by manager
- **Communication Clarity**: manager clarifications / task (from Slack thread labels). **Baseline needed**: Manual tracking during beta.

### System Health Metrics

- **Agent Crashes**: # of agent failures per 100 sessions
- **Recovery Time**: Average time to recover from agent crash
- **Slack Latency**: P95 message delivery time
- **A2A Reliability**: % of A2A messages delivered successfully

### Baseline Targets (MVP)

**Note**: Targets marked "baseline needed" require 2-week measurement period before MVP launch.

- Command usage: 10+ sessions/week (solo developer)
- Success rate: ≥80% (baseline needed)
- Agent utilization: ≥60% (baseline needed)
- Test pass rate: ≥70% on first attempt (baseline needed)
- Manager approval rate: ≥85% (baseline needed)
- Agent crashes: <5% per session
- Slack latency (P95): <2s (tracked, not committed)
- A2A reliability: ≥99% (at-least-once delivery with dedup)

### Long-term Targets (Post-MVP)

- Command usage: 50+ sessions/week
- Success rate: ≥95%
- Agent utilization: ≥80%
- Test pass rate: ≥90% on first attempt
- Manager approval rate: ≥95%
- Agent crashes: <1% per session
- Slack latency (P95): <500ms
- A2A reliability: ≥99.9%

---

## Appendix A: Comparison with Existing `/orchestrate`

| Feature | `/orchestrate` (Current) | `/orchestrate-manager` (New) |
|---------|-------------------------|------------------------------|
| Scope | Single directory | Multiple directories/repos |
| Agent types | Generic agents | Claude (code) + Codex (verify) |
| Communication | A2A protocol | A2A + Slack MCP |
| Agent collaboration | Autonomous | Manager-approved suggestions |
| Worktree support | No | Yes (auto-detect) |
| MCP server mode | No | Yes (all agents) |
| Natural language | Basic | Advanced (multi-directory parsing) |

## Appendix B: Slack Channel Structure

**Channel**: `#agent-orchestration`

**Participants**:
- Manager agent (1 per orchestration session)
- Claude agents (1 per directory)
- Codex agents (1 per directory)
- Human user (observer + fallback decision maker)

**Message Types**:
- 🎯 Task assignment (manager → agent)
- 🔨 Status update (agent → all)
- ❓ Question (agent → agent)
- ✅ Approval (manager → agent)
- ❌ Denial (manager → agent)
- 🎉 Completion (agent → manager)
- ⚠️ Error (agent → all)

## Appendix C: A2A Protocol Extension

**New Message Types for Orchestration Manager**:

1. `manager_task_assignment`: Manager assigns task to agent
2. `agent_status_update`: Agent reports progress
3. `agent_collaboration_request`: Agent asks another agent for help
4. `manager_approval`: Manager approves collaboration request
5. `manager_denial`: Manager denies collaboration request
6. `agent_verification_complete`: Codex reports verification results
7. `manager_session_complete`: Manager reports all tasks finished

**Example**:
```json
{
  "message_type": "agent_collaboration_request",
  "from_agent": "claude-api",
  "to_agent": "claude-sdk",
  "timestamp": "2025-01-11T10:30:00Z",
  "payload": {
    "request_type": "information",
    "question": "What's the SDK version number?",
    "requires_manager_approval": true
  }
}
```

---


## Appendix D: LangGraph Implementation Details

### Non-Negotiable Requirements

**Slack MCP Integration**: MANDATORY for all implementation. Real-time agent collaboration via #agent-orchestration channel is core to the design. LangGraph's conditional edges and interrupts enable native support for approval workflows.

### Overview

LangGraph (v1.0 alpha, released September 2025) is selected as the orchestration framework for its graph-based, stateful execution, providing durable workflows, fine-grained control, and seamless integration with LangSmith for observability. It excels in handling complex dependencies, human-in-the-loop approvals, and crash recovery—directly addressing FR3 (approvals), FR1 (multi-dir coordination), and NFR2 (reliability). Recent updates include Python 3.13 compatibility, long-term memory support for persistent state across sessions, and LangGraph Templates for configurable agentic workflows, enabling reusable orchestration patterns.

#### Exact Features

1. **Graph-Based Workflow Definition**
   ```python
   from langgraph.graph import StateGraph, END
   from typing import TypedDict, Annotated
   from langgraph.checkpoint.memory import MemorySaver
   import operator

   class OrchestratorState(TypedDict):
       goal: str
       directories: dict[str, str]  # {name: path}
       current_directory: str
       agent_status: dict[str, str]  # {agent_id: status}
       approval_required: bool
       approved: bool
       results: dict[str, dict]  # {dir: {sha: str, status: str}}
       long_term_memory: Annotated[dict, operator.add]  # v1.0 long-term memory

   # Define graph structure with templates
   workflow = StateGraph(OrchestratorState, checkpointer=MemorySaver())  # Persistent checkpoints

   # Add nodes (agents/operations)
   workflow.add_node("manager", manager_node)
   workflow.add_node("assign_tasks", assign_tasks_node)
   workflow.add_node("execute_directory", execute_directory_node)
   workflow.add_node("request_approval", request_approval_node)
   workflow.add_node("wait_for_approval", wait_for_approval_node)
   workflow.add_node("aggregate_results", aggregate_results_node)

   # Define edges (flow control)
   workflow.add_edge("manager", "assign_tasks")
   workflow.add_edge("assign_tasks", "execute_directory")

   # Conditional edges (decision points) - Native for approvals
   def should_request_approval(state: OrchestratorState) -> str:
       if state["results"][state["current_directory"]].get("cross_directory_impact"):
           return "request_approval"
       return "aggregate_results"

   workflow.add_conditional_edges(
       "execute_directory",
       should_request_approval,
       {"request_approval": "request_approval", "aggregate_results": "aggregate_results"}
   )
   workflow.add_edge("aggregate_results", END)
   ```

2. **Explicit State Management**
   ```python
   def manager_node(state: OrchestratorState) -> OrchestratorState:
       """Manager coordinates task assignment using LangGraph Template"""
       slack_mcp.post_message(
           channel="#agent-orchestration",
           text=f"🎯 Starting orchestration: {state['goal']}"
       )
       # Use LLM for NL decomposition
       subtasks = decompose_goal(state["goal"], state["directories"])  # Custom LLM call
       return {
           **state,
           "agent_status": {f"claude-{dir}": "assigned" for dir in state["directories"]},
           "long_term_memory": {"subtasks": subtasks}  # Persist for recovery
       }

   def execute_directory_node(state: OrchestratorState) -> OrchestratorState:
       """Execute orchestration in single directory via A2A to tmux agent"""
       directory = state["current_directory"]
       # Dispatch A2A to claude tmux session
       a2a_payload = {"goal": state["goal"], "dir": state["directories"][directory]}
       send_a2a("claude-" + directory, "task_assignment", a2a_payload)

       # Wait for completion (poll Redis or stream)
       result = wait_for_a2a_ack("claude-" + directory, state["correlation_id"])
       slack_mcp.post_message(
           channel="#agent-orchestration",
           text=f"[claude-{directory}] Implementation complete: {result['sha']}"
       )
       return {
           **state,
           "results": {**state["results"], directory: result},
           "agent_status": {**state["agent_status"], f"claude-{directory}": "completed"}
       }
   ```

3. **Conditional Logic (Native Approval Workflows)**
   ```python
   def request_approval_node(state: OrchestratorState) -> OrchestratorState:
       """Post approval request to Slack"""
       slack_mcp.post_message(
           channel="#agent-orchestration",
           text=f"⚠️ @Human: Approval required for {state['current_directory']} - {state['results'][state['current_directory']]['suggestion']}"
       )
       return {**state, "approval_required": True}

   def wait_for_approval_node(state: OrchestratorState) -> OrchestratorState:
       """Interrupt and wait for Slack approval (human-in-the-loop)"""
       # LangGraph interrupt: Pause execution
       if not slack_mcp.wait_for_reaction(timeout=300, approved_reactions=["✅"]):
           raise ValueError("Approval timeout - denying")
       return {**state, "approved": True}
   ```

4. **Parallel Execution with Map-Reduce**
   ```python
   from langgraph.pregel import Send

   def fanout_to_directories(state: OrchestratorState):
       """Map: Spawn parallel execution for each directory"""
       return [
           Send("execute_directory", {"current_directory": dir_name, **state})
           for dir_name in state["directories"].keys()
       ]

   # Add map node
   workflow.add_conditional_edges(
       "assign_tasks",
       fanout_to_directories,
       ["execute_directory"]  # Parallel via Pregel engine
   )
   ```

5. **Streaming and Real-Time Updates**
   ```python
   # Compile graph with checkpointing
   app = workflow.compile(checkpointer=MemorySaver())

   # Stream updates in real-time to Slack
   for event in app.stream(initial_state, stream_mode="values"):
       if "results" in event:
           slack_mcp.post_message(
               channel="#agent-orchestration",
               text=f"State update: {event['agent_status']}"
           )
   ```

6. **Checkpointing (Crash Recovery)**
   ```python
   # v1.0 Enhanced checkpointing with long-term memory
   checkpointer = MemorySaver()
   app = workflow.compile(checkpointer=checkpointer)

   # Resume from crash: Use thread_id for session persistence
   result = app.invoke(initial_state, thread_id="session_123")
   ```

7. **LangSmith Integration (Production Debugging)**
   ```python
   import os
   os.environ["LANGCHAIN_TRACING_V2"] = "true"
   os.environ["LANGCHAIN_API_KEY"] = "your_key"
   os.environ["LANGCHAIN_PROJECT"] = "orchestration-manager"  # v1.0 Composite Evaluators for testing

   # Automatic tracing to LangSmith dashboard
   # - View graph execution path with A2A correlations
   # - Inspect state at each node (e.g., approval interrupts)
   # - Monitor Slack MCP latency with performance metrics
   # - Use Templates for reusable workflow configs
   ```

8. **Interrupt and Human-in-the-Loop**
   ```python
   # Define interrupt points for approvals
   workflow.add_node("human_approval", interrupt_before=["wait_for_approval"])

   # Execution pauses at interrupt
   config = {"configurable": {"thread_id": "session_123"}}
   for output in app.stream(initial_state, config=config):
       pass  # Human reviews Slack, then resume

   # Resume
   final = app.invoke(None, config=config)
   ```

#### LangGraph Benefits

**Implementation Speed**:
- 4-6 week timeline (with v1.0 Templates accelerating config)
- ~800-1200 LOC for full graph, but reusable via Templates
- Quick integration with existing A2A/tmux via nodes/tools

**Developer Experience**:
- Explicit state schema (TypedDict) for type-safe orchestration
- Extensive documentation at langchain-ai.github.io/langgraph
- Active community and LangSmith for rapid debugging

**Role-Based Architecture**:
- Manual but flexible role enforcement via nodes (e.g., claude_node, codex_node)
- Agents as composable subgraphs for specialization

**Maintenance**:
- Framework handles coordination and state; ~400 LOC custom vs. 1200+ pure
- v1.0 Updates: Long-term memory reduces Redis load; performance opts for 20+ agents

**Slack MCP Integration**:
- Native interrupts/conditionals for approval timing
- Streaming for real-time Slack posts
- Direct control over message ordering via edges

#### Implementation Notes

- **Environment**: Python 3.13+ (v1.0 compatible)
- **Dependencies**: `langgraph==1.0.0a1`, `langchain`, `redis`, `slack-sdk`, `anthropic`
- **Templates Usage**: Pre-build graph templates for common journeys (e.g., "multi-repo-auth") for reuse
- **Migration Path**: From CrewAI PoC (if prototyped) via subgraph import

---

## Appendix E: Production Implementation Constraints

### Authority Model

**Who Can Approve**:
- **Manager Agent**: Primary approval authority for agent-to-agent suggestions
- **Human User**: Can override manager decisions via Slack reactions or `/approve` commands

**Precedence Rules**:
1. Human approval > Manager approval (human override capability)
2. Explicit denial (❌ or `/deny`) cannot be overridden by lower authority
3. Timeout (5 minutes) → BLOCKED state → escalate to human

**Escalation Path**:
```
Agent Suggestion → Manager Evaluates → {Approve, Deny, Escalate}
                                              ↓
                                          If Escalate
                                              ↓
                                    Human Review (Slack notification)
                                              ↓
                                    {Approve, Deny, Modify}
```

### Task Identity and Idempotency

**Global Task ID**: `t_{timestamp}_{hash}` (e.g., `t_1704988800_a7b3c`)
- Unique across all orchestration sessions
- Used for correlation across A2A messages, Slack threads, and Redis keys

**Per-Directory Run ID**: `r_{dir_key}_{seq}` (e.g., `r_api_001`, `r_sdk_002`)
- Unique within a task
- Enables per-directory retries without affecting other directories

**Idempotency Keys**:
- **Message Deduplication**: `message_id` in A2A envelope → Redis SET with TTL
- **Commit Idempotency**: Check `commits:{task_id}:{dir_key}` before pushing
- **Slack Message Idempotency**: Store `ts` (Slack timestamp) → skip duplicate posts

**Replay Rules**:
- Agent crash → resume from last checkpointed state (LangGraph MemorySaver)
- Duplicate A2A message → skip if `message_id` in `processed_messages:{agent_id}` SET
- Retry logic: Exponential backoff with jitter (1s, 2s, 4s)

### Exactly-Once Semantics

**Redis Streams Reality**: Provides at-least-once delivery, NOT exactly-once.

**Deduplication Strategy**:
```python
def handle_a2a_message(msg):
    msg_id = msg["message_id"]
    agent_id = msg["to"]
    dedup_key = f"processed:{agent_id}:{msg_id}"

    # Try to add to processed set (atomic)
    if redis.set(dedup_key, "1", nx=True, ex=3600):  # 1-hour TTL
        # First time seeing this message → process it
        process_message(msg)
    else:
        # Duplicate → skip silently
        logger.info(f"Skipped duplicate message {msg_id}")
```

**Idempotent Handlers**:
- All agent operations must be idempotent
- File writes: Check file hash before overwriting
- Git commits: Check commit SHA before creating
- Slack posts: Check thread `ts` before posting

### Source of Truth Architecture

**Redis as Primary Store**:
```
orchestrations:{session_id}      # Session metadata
tasks:{task_id}                  # Task state machine
runs:{run_id}                    # Per-directory execution state
messages:{stream}                # A2A event log
processed:{agent_id}:{msg_id}    # Deduplication tracking
```

**Slack as Write-Through Mirror**:
- Manager posts to Slack AFTER updating Redis
- If Slack post fails → log warning, continue (state is safe in Redis)
- Slack downtime → system continues, posts queued for retry

**Recovery from Slack**:
- Slack is NOT used for state recovery
- On manager restart → read state from Redis, rebuild Slack view

### Test Adapter Contract

**Per-Repository Adapter Spec** (`orchm.yaml`):
```yaml
repos:
  api:
    path: ~/projects/api
    test: "pytest -q"              # Exit 0 = pass, non-zero = fail
    lint: "ruff check ."           # Exit 0 = pass
    typecheck: "mypy ."            # Exit 0 = pass
    coverage: "coverage run -m pytest && coverage report --fail-under=80"
    build: null                    # Optional
  sdk:
    path: ~/projects/sdk
    test: "pytest tests/"
    lint: "pylint sdk/"
    typecheck: "mypy sdk/"
    build: "hatch build"           # Optional build step
  docs:
    path: ~/projects/docs
    test: "mkdocs build --strict"  # Link checking
    lint: "markdownlint **/*.md"   # Markdown linting
```

**Adapter Requirements**:
- All commands must be executable from repo root
- Exit codes: 0 = success, non-zero = failure
- STDOUT/STDERR captured for logs
- Timeout: 10 minutes default, configurable per-command

### Git Worktree Rules

**Ephemeral Worktrees**:
```bash
# Create per-run worktree
git worktree add worktrees/t_123/api ~/projects/api
cd worktrees/t_123/api

# Lock branch to prevent conflicts
git config core.repositoryformatversion 0

# Work and commit
# ...

# Cleanup after completion
cd ../..
git worktree remove worktrees/t_123/api --force
```

**Commit Requirements**:
- Clean base: No uncommitted changes before starting
- Signed commits: Use GPG key or SSH signing
- Commit message format: Include `task_id` and `run_id` in footer

**Result Mapping**:
```json
{
  "commits": {
    "api": "abc123def456",
    "sdk": "789ghi012jkl",
    "docs": "345mno678pqr"
  }
}
```

Optional: Tag commits with `task_id` for traceability:
```bash
git tag -a "orchm/t_123" -m "Orchestration task t_123: JWT auth"
```

### Concurrency Policy

**Resource Limits**:
- Max 20 agents per host (configurable)
- Per-host resource quotas: CPU 80%, memory 16GB
- Queue depth: 100 pending tasks

**Backpressure**:
```python
class AgentPool:
    def acquire_agent(self, timeout=60):
        """Block until agent available or timeout"""
        if len(self.active) >= self.max_agents:
            # Wait for agent to finish or timeout
            self.condition.wait(timeout)
            if timeout_expired:
                raise ResourceExhausted("No agents available")
        return self._spawn_agent()
```

**Work-Stealing** (future enhancement):
- If a directory agent is idle while others are busy, reassign tasks
- Requires stateless agent design

### Failure Policy

**Retry Strategy**:
```python
max_retries = 3
backoff = [1, 2, 4]  # seconds

for attempt in range(max_retries):
    try:
        result = execute_task()
        break
    except RecoverableError as e:
        if attempt < max_retries - 1:
            time.sleep(backoff[attempt])
            continue
        else:
            # Final failure → escalate
            escalate_to_human(task_id, error=e)
```

**Abort Criteria**:
- 3 consecutive failures of same task
- Unrecoverable errors (e.g., auth failure, repo not found)
- Timeout exceeded (10 min per directory by default)

**Partial Success Policy**:
- If 2/3 directories succeed, mark orchestration as PARTIAL_SUCCESS
- Post summary to Slack with successful and failed directories
- User decides: retry failures or accept partial

**Rollback Strategy**:
- Git: Revert commits via `git reset --hard` in worktree
- Artifacts: Delete generated files
- State: Mark runs as ABORTED in Redis

### Versioning Across Repos

**Semantic Versioning**:
- API changes → bump SDK major version
- New features → bump SDK minor version
- Bug fixes → bump SDK patch version

**Propagation Strategy**:
```yaml
# In orchestration goal:
"Update API to v2.0, regenerate SDK to v2.0, update docs"

# Manager detects version changes:
- api/version.py: "2.0.0"
- sdk/pyproject.toml: bump to "2.0.0"
- docs/changelog.md: add release notes
```

**Tagging**:
```bash
# After successful orchestration
git tag -a "v2.0.0" -m "Release 2.0.0 via orchm t_123"
git push origin v2.0.0
```

---

## Appendix F: Data Contracts and State Machine

### State Machine (All Agents)

```
NEW → ASSIGNED → RUNNING → WAITING_APPROVAL? → {RUNNING|BLOCKED} → VERIFYING → {SUCCEEDED|FAILED|ABORTED}
```

**State Transitions** (all require durable write + correlation ID):

| From State | Event | To State | Actions |
|------------|-------|----------|---------|
| NEW | Task created | ASSIGNED | Assign to agent, post to Slack |
| ASSIGNED | Agent accepts | RUNNING | Start timer, log start |
| RUNNING | Needs approval | WAITING_APPROVAL | Post approval request to Slack |
| WAITING_APPROVAL | Approved | RUNNING | Resume execution |
| WAITING_APPROVAL | Denied | BLOCKED | Log denial, notify manager |
| WAITING_APPROVAL | Timeout (5min) | BLOCKED | Escalate to human |
| RUNNING | Builder complete | VERIFYING | Spawn verifier agent |
| VERIFYING | All gates pass | SUCCEEDED | Commit, post success |
| VERIFYING | Gate fails | FAILED | Log failure, retry or escalate |
| ANY | Unrecoverable error | ABORTED | Cleanup, notify user |

**Timeout Handling**:
- RUNNING → BLOCKED if no progress for 10 minutes
- WAITING_APPROVAL → BLOCKED if no response for 5 minutes
- VERIFYING → FAILED if verification exceeds 5 minutes

### Data Contract: Task

```json
{
  "task_id": "t_1704988800_a7b3c",
  "goal": "Implement JWT authentication end-to-end across API, SDK, and docs",
  "directories": {
    "api": "~/projects/api-server",
    "sdk": "~/projects/python-sdk",
    "docs": "~/projects/documentation"
  },
  "created_at": "2025-10-11T14:30:00Z",
  "owner": "manager-session-abc123",
  "config": {
    "priority": "high",
    "max_parallel": 4,
    "timeout_per_dir": 600,
    "retry_policy": {
      "max_retries": 3,
      "backoff": [1, 2, 4]
    }
  },
  "state": "RUNNING",
  "runs": ["r_api_001", "r_sdk_001", "r_docs_001"]
}
```

**Field Definitions**:
- `task_id`: Globally unique identifier for this orchestration task
- `goal`: Natural language description of what to achieve
- `directories`: Map of logical names to filesystem paths
- `owner`: Manager agent ID that created this task
- `config.priority`: Used for queueing when resource-constrained
- `config.max_parallel`: Max concurrent directory executions
- `state`: Current task state machine position

### Data Contract: RunResult (Per Directory)

```json
{
  "run_id": "r_api_001",
  "task_id": "t_1704988800_a7b3c",
  "dir_key": "api",
  "dir_path": "~/projects/api-server",
  "state": "SUCCEEDED",
  "started_at": "2025-10-11T14:30:05Z",
  "completed_at": "2025-10-11T14:35:22Z",
  "builder_agent": "builder-api-001",
  "verifier_agent": "verifier-api-001",
  "commits": ["abc123def456"],
  "tests": {
    "command": "pytest -q",
    "passed": 23,
    "failed": 0,
    "duration_s": 12.3,
    "exit_code": 0
  },
  "quality_gates": {
    "lint": {"passed": true, "command": "ruff check .", "exit_code": 0},
    "typecheck": {"passed": true, "command": "mypy .", "exit_code": 0},
    "coverage": {"passed": true, "command": "coverage report", "pct": 87.5}
  },
  "artifacts": {
    "log": "s3://orchm-logs/r_api_001.log",
    "diff": "s3://orchm-artifacts/r_api_001.diff"
  },
  "cross_directory_impact": ["sdk"],
  "retry_count": 0,
  "failure_reason": null
}
```

**Field Definitions**:
- `run_id`: Unique ID for this directory's execution within the task
- `state`: Same state machine as task, but per-directory
- `cross_directory_impact`: List of other directories that depend on this one's changes
- `quality_gates`: Results from verifier's gate enforcement
- `retry_count`: Number of times this run was retried
- `failure_reason`: Error message if state is FAILED or ABORTED

### Data Contract: A2A Message Envelope

```json
{
  "message_id": "m_1704988850_b8c4d",
  "type": "agent_status_update",
  "ts": "2025-10-11T14:30:50Z",
  "from": "builder-api-001",
  "to": "manager-session-abc123",
  "correlation_id": "t_1704988800_a7b3c:r_api_001",
  "payload": {
    "state": "RUNNING",
    "progress_pct": 45,
    "message": "Implemented JWT token generation, running tests..."
  },
  "ttl": 3600,
  "priority": "normal"
}
```

**Message Types**:
- `task_assignment`: Manager → Agent (start work)
- `agent_status_update`: Agent → Manager (progress update)
- `agent_collaboration_request`: Agent → Agent (ask for help)
- `manager_approval`: Manager → Agent (approval granted)
- `manager_denial`: Manager → Agent (approval denied)
- `verification_complete`: Verifier → Manager (gate results)
- `task_complete`: Manager → User (final results)

**Correlation ID Format**: `{task_id}:{run_id}` enables message threading

### Slack Message Design

**Session Channel**: `#orchm-{session_id}`
- One channel per orchestration session
- Prevents multi-session crosstalk
- Channel archived after completion (24-hour retention)

**Thread Structure**:
```
[Manager] 🎯 Task t_123: Implement JWT auth across 3 repos
  ├─ [Builder-API] 🔨 Starting implementation in ~/api...
  ├─ [Builder-API] ⚡ Tests running (23/23 passing)
  ├─ [Verifier-API] 🔍 Re-running tests in clean environment...
  ├─ [Verifier-API] ✅ All gates passed (tests: 23/23, coverage: 87%)
  ├─ [Manager] ✅ API complete (commit: abc123)
  ├─ [Builder-SDK] 🔨 Starting SDK implementation...
  └─ [Manager] ✅ Task t_123 complete across all 3 repos
```

**Approval Workflow**:
```
[Builder-SDK] ❓ @Builder-API What's the token expiry format?
[Manager] ⚠️ Approval required: Builder-SDK → Builder-API collaboration
[Manager] React with ✅ to approve or ❌ to deny (timeout: 5min)
```

**React with** ✅ **or post** `/approve t_123 r_sdk_001`

### CLI and Configuration

**Command-Line Interface**:
```bash
# Explicit directories
/orchm "Add JWT auth" --dirs api:~/api,sdk:~/sdk,docs:~/docs

# Auto-detect worktrees
/orchm "Fix bug #123" --auto-detect-worktrees

# Config file
/orchm "Add feature X" --config orchm.yaml

# Error if multiple sources conflict
/orchm "..." --dirs ... --config ... # ❌ ERROR: Specify only one source
```

**Configuration File Format** (`orchm.yaml`):
```yaml
defaults:
  max_parallel: 4
  timeout_per_dir: 600
  retry_policy:
    max_retries: 3
    backoff: [1, 2, 4]

builder:
  model: "claude-3-5-sonnet-20241022"
  fast_loop_tests: true

verifier:
  model: "claude-3-5-sonnet-20241022"
  quality_gates:
    - "tests"
    - "lint"
    - "typecheck"
    - "coverage>=80"

repos:
  api:
    path: ~/projects/api-server
    test: "pytest -q"
    lint: "ruff check ."
    typecheck: "mypy ."
    coverage: "coverage run -m pytest && coverage report --fail-under=80"

  sdk:
    path: ~/projects/python-sdk
    test: "pytest tests/"
    lint: "pylint sdk/"
    typecheck: "mypy sdk/"
    build: "hatch build"

  docs:
    path: ~/projects/documentation
    test: "mkdocs build --strict"
    lint: "markdownlint **/*.md"
```

### Observability Metrics

**Prometheus Metrics**:
```python
# Latency metrics
a2a_msg_latency_ms = Histogram("a2a_message_latency_milliseconds")
slack_publish_latency_ms = Histogram("slack_publish_latency_milliseconds")

# Task metrics
task_time_s = Histogram("task_duration_seconds", labelnames=["task_id", "dir_key"])
task_success_rate = Counter("task_success_total", labelnames=["dir_key"])
task_failure_rate = Counter("task_failure_total", labelnames=["dir_key", "reason"])

# Resource metrics
agent_cpu_pct = Gauge("agent_cpu_percent", labelnames=["agent_id", "role"])
agent_mem_mb = Gauge("agent_memory_megabytes", labelnames=["agent_id", "role"])

# Quality metrics
verifier_fail_rate = Counter("verifier_gate_failures", labelnames=["dir_key", "gate"])
slack_publish_errors = Counter("slack_publish_errors_total", labelnames=["session_id"])
```

**Structured Logging**:
```json
{
  "timestamp": "2025-10-11T14:30:50Z",
  "level": "INFO",
  "task_id": "t_1704988800_a7b3c",
  "run_id": "r_api_001",
  "correlation_id": "t_1704988800_a7b3c:r_api_001",
  "agent_id": "builder-api-001",
  "message": "Tests completed: 23 passed, 0 failed",
  "context": {
    "duration_s": 12.3,
    "exit_code": 0,
    "command": "pytest -q"
  }
}
```

### Testing Plan

**Contract Tests** (A2A schema validation):
```python
def test_a2a_message_schema():
    msg = {"message_id": "m_123", "type": "agent_status_update", ...}
    validate_schema(msg, A2A_SCHEMA)  # JSON Schema validation

def test_idempotency():
    msg_id = "m_duplicate"
    handle_message(msg_id, payload)
    handle_message(msg_id, payload)  # Should be skipped
    assert_processed_once(msg_id)
```

**Adapter Tests** (per repo):
```python
def test_api_adapter():
    result = run_command("pytest -q", cwd="~/projects/api")
    assert result.exit_code == 0
    assert "passed" in result.stdout

def test_adapter_timeout():
    result = run_command("sleep 1000", timeout=1)
    assert result.timed_out
```

**End-to-End Test**:
```python
def test_cross_repo_orchestration():
    # Start orchestration
    task_id = manager.create_task(
        goal="Add /auth endpoint to API, update SDK, document in docs",
        dirs={"api": "~/api", "sdk": "~/sdk", "docs": "~/docs"}
    )

    # Wait for completion
    result = manager.wait_for_completion(task_id, timeout=600)

    # Assert commits
    assert len(result.commits) == 3
    assert result.commits["api"] != result.commits["sdk"]

    # Assert Slack thread
    thread = slack.get_thread(task_id)
    assert "✅ Task t_" in thread.messages[-1].text
```

**Chaos Test**:
```python
def test_verifier_crash_recovery():
    task_id = start_task(...)
    wait_for_state(task_id, "VERIFYING")

    # Kill verifier mid-run
    kill_agent("verifier-api-001")

    # Manager should detect crash and restart
    wait_for_agent_restart("verifier-api", timeout=10)

    # Task should complete successfully
    assert wait_for_completion(task_id).state == "SUCCEEDED"
```

---

**Document Control**

| Field       | Details                                                                  |
|-------------|--------------------------------------------------------------------------|
| Author      | Genesis Coder (Claude)                                                   |
| Reviewers   | [To be assigned]                                                         |
| Status      | Implementation Phase v1.3 – Production Constraints Integrated            |
| Next Steps  | Begin LangGraph implementation for US1 with production-grade patterns    |
