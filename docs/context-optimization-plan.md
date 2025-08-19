# Context Optimization Plan for /converge System

**Document**: Context Reduction Architecture and Implementation Plan
**Created**: August 18, 2025
**Branch**: converge-command-implementation
**Status**: Implementation Ready

---

## 🎯 Problem Statement

The current /converge system suffers from context exhaustion due to monolithic context accumulation:

**Current Context Consumption**:
- Large file reads: 50-100K tokens per operation
- Historical context buildup: Each step accumulates previous context
- Cross-reference loading: Multiple related files loaded simultaneously
- Monolithic intelligence: One agent tries to maintain awareness of everything

**Result**: Context exhaustion after 2-3 convergence iterations, limiting system effectiveness

---

## 🏗️ Architectural Solution: Independent Subagent Pattern

### Core Design Principle

**FROM**: Monolithic Context Agent
```
Main Agent: [Goal + Plans + History + Files + Memory + Guidelines] = 200K+ tokens
```

**TO**: Distributed File-Coordinated Agents
```
Orchestrator: [Goal + Status] = 5K tokens
├── Goal Agent: [Goal Statement] = 5K tokens
├── Planning Agent: [Goal + Command Index] = 10K tokens  
├── Execution Agents: [Single Task + Required Files] = 15K tokens each
├── Validation Agent: [Criteria + Current State] = 8K tokens
└── Learning Agent: [Outcomes + Patterns] = 5K tokens
```

### State Management: File-Based Coordination

**Session Directory Structure**:
```
/tmp/converge/{branch_name}/
├── session-{timestamp}/
│   ├── goal-spec.json          # Goal definition and success criteria
│   ├── command-index.json      # Lightweight command summaries
│   ├── execution-plan.json     # Step-by-step command plan
│   ├── reviewed-plan.json      # Plan + confidence assessment
│   ├── current-state.json      # Progress tracking
│   ├── session-metadata.json   # Timing, resources, metrics
│   ├── results/
│   │   ├── step-01-output.json # Individual task results
│   │   ├── step-02-output.json
│   │   └── step-NN-output.json
│   └── validation/
│       ├── criteria-status.json
│       └── evidence-log.json
├── command-cache/              # Pre-built command summaries
└── session-history/            # Completed sessions for learning
```

---

## 🚀 Implementation Phases

### Phase 1: Immediate Optimizations (60% Context Reduction)

**What Can Be Done NOW with Normal Subagents (No /orch Required)**:

#### 1.1 Command Index Generation
Create lightweight command summaries to avoid reading full .md files:

**Implementation**:
- **Subagent Task**: "Create command index by reading all .claude/commands/*.md files and extracting purpose, usage, and context requirements"
- **Output**: `/tmp/converge/{branch_name}/command-cache/index.json`
- **Context Savings**: 80% reduction in command discovery (10K vs 50K tokens)

#### 1.2 State Externalization
Move progress tracking from context to filesystem:

**Implementation**:
- **Subagent Task**: "Convert current TodoWrite tracking to JSON file persistence"
- **Output**: `/tmp/converge/{branch_name}/session-{id}/current-state.json`
- **Context Savings**: 70% reduction in state tracking overhead

#### 1.3 Lazy File Loading
Only read files when actually needed for execution:

**Implementation**:
- **Subagent Task**: "Modify file reading patterns to load on-demand rather than preemptively"
- **Result**: Read files only during actual command execution, not planning
- **Context Savings**: 50% reduction in unnecessary file loading

#### 1.4 Goal Processing Agent
Separate goal definition from main workflow:

**Implementation**:
- **Subagent Input**: Raw goal statement only
- **Subagent Task**: "Parse goal, generate success criteria, create goal-spec.json"
- **Output**: `/tmp/converge/{branch_name}/session-{id}/goal-spec.json`
- **Context Usage**: 5K tokens (isolated from main workflow)

### Phase 2: Specialized Agent Architecture (80% Context Reduction)

#### 2.1 Planning Agent (Independent)
**Subagent Specification**:
- **Input**: `goal-spec.json` + `command-index.json`
- **Task**: "Create execution plan using command summaries, not full docs"
- **Output**: `/tmp/converge/{branch_name}/session-{id}/execution-plan.json`
- **Context**: 10K tokens maximum
- **Independence**: No shared context with other agents

#### 2.2 Review Agent (Independent)  
**Subagent Specification**:
- **Input**: `execution-plan.json` + confidence scoring rules
- **Task**: "Assess plan quality and assign confidence score (High/Medium/Low)"
- **Output**: `/tmp/converge/{branch_name}/session-{id}/reviewed-plan.json`
- **Context**: 8K tokens maximum
- **Isolation**: No awareness of goal details or command internals

#### 2.3 Execution Agents (Parallel Independent)
**Subagent Specification**:
- **Input**: Single task from `execution-plan.json`
- **Task**: "Execute one specific command with required files only"
- **Output**: `/tmp/converge/{branch_name}/session-{id}/results/step-{N}-output.json`
- **Context**: 15K tokens per agent
- **Parallelism**: Multiple agents can run simultaneously on independent tasks

#### 2.4 Validation Agent (Independent)
**Subagent Specification**:
- **Input**: `goal-spec.json` + `results/` directory
- **Task**: "Check success criteria against results, provide completion percentage"
- **Output**: `/tmp/converge/{branch_name}/session-{id}/validation/status.json`
- **Context**: 8K tokens maximum
- **Focus**: Only validation logic, no execution awareness

### Phase 3: Advanced Optimization (90% Context Reduction)

#### 3.1 Agent Caching System
- Reuse specialized agents for similar task types
- Agent warm-up pools for common operations
- Shared agent instances across convergence sessions

#### 3.2 Parallel Execution Framework
- Multiple execution agents running simultaneously
- Dependency-aware task scheduling
- Result aggregation and conflict resolution

#### 3.3 Smart State Compression
- Minimal essential state storage
- Progressive context summarization
- Historical pattern compression

---

## 📊 Expected Performance Improvements

### Context Consumption Targets:
| Phase | Current Usage | Target Usage | Reduction |
|-------|--------------|--------------|-----------|
| Baseline | 150-200K tokens | 150-200K tokens | 0% |
| Phase 1 | 150-200K tokens | 60-80K tokens | 60-75% |
| Phase 2 | 60-80K tokens | 30-50K tokens | 75-85% |
| Phase 3 | 30-50K tokens | 15-25K tokens | 85-90% |

### Execution Benefits:
- **Parallel Processing**: Multiple independent agents executing simultaneously
- **Failure Isolation**: One agent failure doesn't crash entire convergence workflow
- **Resume Capability**: Can restart from any step using filesystem state
- **Debug Clarity**: Each agent's input/output clearly defined and traceable
- **Scalability**: Add more agents without increasing main context

---

## 🛠️ Implementation Strategy for Current System

### Immediate Actions (Phase 1 - This Week)

#### 1. Create Command Index System
**Subagent Implementation**:
```bash
# Task for subagent
"Read all files in .claude/commands/ and create a lightweight index with:
- Command name and purpose
- Required context size (low/medium/high) 
- Input/output specifications
- Usage examples
Save to /tmp/converge/{branch_name}/command-cache/index.json"
```

#### 2. Implement State Persistence
**Subagent Implementation**:
```bash
# Task for subagent  
"Convert /converge progress tracking from in-context TodoWrite to:
- JSON file persistence at /tmp/converge/{branch_name}/session-{id}/
- State update functions that write to filesystem
- State reading functions that load from filesystem
- Maintain backward compatibility with existing /converge workflow"
```

#### 3. Goal Processing Separation
**Subagent Implementation**:
```bash
# Task for subagent
"Create independent goal processing agent that:
- Takes raw goal statement as only input
- Generates structured success criteria
- Outputs goal-spec.json with no shared context
- Integrates with existing /goal command workflow"
```

#### 4. Lazy Loading Implementation
**Subagent Implementation**:
```bash
# Task for subagent
"Modify /converge file reading patterns to:
- Load files only when needed for execution
- Use command index for planning instead of full files
- Cache frequently accessed files in session directory
- Implement smart pre-loading for known patterns"
```

### Integration with Existing /converge Workflow

**Enhanced /converge Steps with Subagents**:

```markdown
#### Step 1: Goal Processing (Subagent)
**Subagent**: Goal Processing Agent
- Input: Raw goal statement
- Output: /tmp/converge/{branch}/session-{id}/goal-spec.json
- Context: 5K tokens (isolated)

#### Step 2: Strategic Planning (Subagent)
**Subagent**: Planning Agent  
- Input: goal-spec.json + command-index.json
- Output: /tmp/converge/{branch}/session-{id}/execution-plan.json
- Context: 10K tokens (command summaries only)

#### Step 3: Plan Review (Subagent)
**Subagent**: Review Agent
- Input: execution-plan.json
- Output: /tmp/converge/{branch}/session-{id}/reviewed-plan.json
- Context: 8K tokens (plan assessment only)

#### Steps 4-N: Execution (Parallel Subagents)
**Subagents**: Execution Agents
- Input: Individual tasks from execution-plan.json
- Output: /tmp/converge/{branch}/session-{id}/results/step-{N}-output.json
- Context: 15K tokens each (task-specific files only)
- Parallelism: Independent agents can run simultaneously
```

---

## 🔧 Technical Implementation Details

### File Format Specifications

#### goal-spec.json
```json
{
  "goal_statement": "Original goal text",
  "parsed_objective": "Structured objective",
  "success_criteria": [
    {
      "id": "criterion_1",
      "description": "Specific measurable outcome",
      "validation_method": "How to verify completion",
      "priority": "high|medium|low"
    }
  ],
  "estimated_complexity": "high|medium|low",
  "created_timestamp": "2025-08-18T12:00:00Z"
}
```

#### command-index.json
```json
{
  "commands": {
    "/converge": {
      "purpose": "Goal achievement through iterative cycles",
      "context_requirement": "medium",
      "typical_usage": "Complex multi-step goals",
      "execution_time": "5-30 minutes"
    },
    "/cerebras": {
      "purpose": "Fast code generation",
      "context_requirement": "low", 
      "typical_usage": "Code/script/document creation",
      "execution_time": "30-60 seconds"
    }
  },
  "categories": {
    "code_generation": ["/cerebras", "/execute"],
    "planning": ["/plan", "/execute"], 
    "validation": ["/goal", "/test"]
  },
  "updated_timestamp": "2025-08-18T12:00:00Z"
}
```

#### current-state.json
```json
{
  "session_id": "session-20250818-1200",
  "current_phase": "execution|planning|validation|learning",
  "completed_steps": ["step_1", "step_2"],
  "current_step": "step_3",
  "remaining_steps": ["step_4", "step_5"],
  "iteration_count": 2,
  "success_percentage": 60,
  "context_usage": {
    "tokens_used": 45000,
    "tokens_remaining": 155000
  },
  "last_updated": "2025-08-18T12:30:00Z"
}
```

### Agent Communication Protocol

**No Direct Communication**: Agents communicate only through filesystem
- **Input**: Read JSON files from session directory
- **Output**: Write JSON files to session directory  
- **Coordination**: Orchestrator polls file timestamps
- **State**: All state persisted to filesystem, not context

**Benefits**:
- **Isolation**: Agent failures don't propagate
- **Parallelism**: Multiple agents can work simultaneously
- **Resume**: Can restart from any point using filesystem state
- **Debug**: Clear audit trail of all agent inputs/outputs

---

## 🎯 Success Metrics

### Context Efficiency Targets:
- **Phase 1**: 60% reduction in context consumption
- **Phase 2**: 80% reduction with parallel execution capability
- **Phase 3**: 90% reduction with full optimization

### Performance Targets:
- **Execution Speed**: 2-3x faster through parallelism
- **Failure Recovery**: 95% successful resume from interruption
- **Context Utilization**: Never exceed 50% of available context
- **Scalability**: Support 10+ parallel execution agents

### User Experience Targets:
- **Transparency**: Clear visibility into agent activities
- **Reliability**: Consistent performance across context sizes
- **Flexibility**: Easy to add new agent types and capabilities
- **Maintainability**: Simple debugging and troubleshooting

---

## 📋 Implementation Checklist

### Phase 1 (Immediate):
- [ ] Create command index generation system
- [ ] Implement state persistence to /tmp/converge/{branch_name}/
- [ ] Separate goal processing into independent subagent
- [ ] Implement lazy loading for file operations
- [ ] Test context reduction with existing /converge workflow

### Phase 2 (Next Sprint):  
- [ ] Implement specialized planning agent
- [ ] Create independent review agent with confidence scoring
- [ ] Build parallel execution agent framework
- [ ] Develop validation agent for success criteria checking
- [ ] Integrate all agents with main /converge orchestrator

### Phase 3 (Future):
- [ ] Implement agent caching and reuse system
- [ ] Build advanced parallel execution scheduler
- [ ] Create smart state compression algorithms
- [ ] Optimize cross-agent communication patterns
- [ ] Performance tune entire system for maximum efficiency

This plan provides a clear path from the current monolithic context approach to a distributed, efficient, and scalable agent architecture that can handle complex convergence tasks without context exhaustion.