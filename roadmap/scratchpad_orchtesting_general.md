# Orchestration Enhancement: General Instruction Handling

## Problem Statement
Current /orch command is too task-focused and doesn't handle general instructions well. The system needs to understand ANY instruction and delegate appropriately to agents.

## Vision
Transform /orch into a general-purpose instruction delegation system that:
- Understands natural language instructions of any type
- Creates appropriate agents for any request
- Handles questions, research, analysis, not just coding tasks
- Maintains context across agent interactions
- Supports agent collaboration on complex requests

## Current Limitations
1. Task-oriented mindset (assumes development tasks)
2. Agents create new branches instead of continuing work
3. No context passing between sequential agents
4. Hardcoded task type classification
5. Limited instruction understanding

## Enhancement Goals
1. **General Instruction Processing**
   - Parse any type of request (questions, research, tasks, analysis)
   - No assumptions about task type
   - Natural language understanding

2. **Smart Agent Creation**
   - Create agents based on actual needs
   - Support continuing work on existing branches
   - Pass context between agents

3. **Flexible Execution**
   - Agents can ask clarifying questions
   - Support for multi-turn conversations
   - Better error handling and recovery

4. **Enhanced Coordination**
   - Agents aware of previous agent work
   - Shared context and memory
   - Collaborative problem solving

## Key Design Questions
1. How to determine when to create new agents vs continue with existing?
2. How to pass full context between agents?
3. How to handle clarifying questions from agents?
4. How to support non-development instructions?
5. How to maintain conversation continuity?

## Next Steps
- /think deep analysis of instruction types and agent needs ✓
- /arch for system design (in progress)
- Implementation plan

---

## /think Deep Analysis Results

### Instruction Categories Identified
1. **Questions** - "Why did X happen?", "What's the status?"
2. **Research** - "Find all uses of...", "Analyze performance"
3. **Tasks** - "Fix bug", "Implement feature"
4. **Conversations** - "Let's discuss", "Help me understand"
5. **Meta-instructions** - "Continue where agent left off", "Ask agent to clarify"

### Key Technical Challenges
1. **Context Preservation** - Full conversation history needed
2. **Branch Management** - Continue existing branches when appropriate
3. **State Awareness** - Know what previous agents discovered
4. **Clarification Handling** - Bidirectional communication

### Core Solution
Transform orchestration from task executor to intelligent instruction router:
- LLM-based understanding (no hardcoded patterns)
- Enhanced Redis for context and relationships
- Support branch continuation
- Enable agent communication
- Trust LLM capabilities

---

## /arch System Architecture

### 1. Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Orchestration Manager                     │
│  ┌─────────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ Instruction     │  │   Context    │  │    Agent      │  │
│  │ Analyzer (LLM)  │  │   Manager    │  │   Factory     │  │
│  └────────┬────────┘  └──────┬───────┘  └───────┬───────┘  │
│           │                   │                   │          │
│           └───────────────────┴───────────────────┘          │
│                              │                               │
└──────────────────────────────┼───────────────────────────────┘
                               │
                    ┌──────────┴──────────┐
                    │   Redis Context DB   │
                    │  ┌───────────────┐  │
                    │  │ Conversations │  │
                    │  ├───────────────┤  │
                    │  │ Agent History │  │
                    │  ├───────────────┤  │
                    │  │ Branch Map    │  │
                    │  ├───────────────┤  │
                    │  │ Results Cache │  │
                    │  └───────────────┘  │
                    └─────────────────────┘
```

### 2. Component Details

#### Instruction Analyzer (LLM-based)
```python
class InstructionAnalyzer:
    """Uses LLM to understand any instruction type"""

    def analyze(self, instruction: str, context: dict) -> InstructionPlan:
        # Send to LLM with full context
        analysis = llm.analyze({
            "instruction": instruction,
            "conversation_history": context.get("history"),
            "previous_agents": context.get("agents"),
            "current_branch": context.get("branch")
        })

        return InstructionPlan(
            intent_type=analysis.intent,  # question/task/research/etc
            continuation_of=analysis.previous_agent_id,
            required_capabilities=analysis.capabilities,
            branch_strategy=analysis.branch_strategy,
            clarifications_needed=analysis.clarifications
        )
```

#### Context Manager
```python
class ContextManager:
    """Manages conversation and agent context via Redis"""

    def __init__(self, redis_client):
        self.redis = redis_client

    def get_conversation_context(self, session_id: str) -> dict:
        """Retrieve full conversation history and agent work"""
        return {
            "history": self.redis.get(f"{session_id}:history"),
            "agents": self.redis.get(f"{session_id}:agents"),
            "branches": self.redis.get(f"{session_id}:branches"),
            "results": self.redis.get(f"{session_id}:results")
        }

    def save_agent_work(self, agent_id: str, work: dict):
        """Persist agent discoveries for future agents"""
        self.redis.set(f"agent:{agent_id}:work", work)
        self.redis.rpush(f"session:{work['session_id']}:agents", agent_id)
```

#### Agent Factory
```python
class AgentFactory:
    """Creates appropriate agents based on instruction analysis"""

    def create_agent(self, plan: InstructionPlan, context: dict) -> Agent:
        if plan.continuation_of:
            # Continue existing work
            return self._create_continuation_agent(plan, context)
        else:
            # New agent with full context
            return self._create_contextual_agent(plan, context)

    def _create_continuation_agent(self, plan, context):
        """Agent that continues on existing branch with prior context"""
        previous_work = context.get(f"agent:{plan.continuation_of}:work")
        branch = context.get(f"agent:{plan.continuation_of}:branch")

        return Agent(
            type="continuation",
            branch=branch,  # Use same branch!
            initial_context=previous_work,
            instruction=plan.instruction
        )
```

### 3. Instruction Flow

```
User: "/orch tell the same agent to fix tests and run /copilot"
          │
          ▼
┌─────────────────────┐
│ Instruction Analyzer│ ◄── "Understands 'same agent' means continue"
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Context Manager    │ ◄── "Retrieves agent-7343's work and branch"
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Agent Factory     │ ◄── "Creates continuation agent on same branch"
└──────────┬──────────┘
           │
           ▼
    Continuation Agent
    (Works on task-agent-7343-work branch)
```

### 4. Key Improvements

#### A. No Hardcoded Patterns
```python
# OLD: Hardcoded task classification
if "test" in instruction.lower():
    return TaskType.TESTING

# NEW: LLM understanding
intent = llm.understand_instruction(instruction, full_context)
```

#### B. Branch Continuation
```python
# OLD: Always create new branch
branch = f"task-agent-{agent_id}-work"

# NEW: Smart branch selection
if continuing_work:
    branch = previous_agent.branch
else:
    branch = f"{intent_type}-agent-{agent_id}-work"
```

#### C. Context Preservation
```python
# OLD: Just pass instruction
agent_instruction = task_description

# NEW: Full context
agent_instruction = {
    "current_request": instruction,
    "conversation_history": full_history,
    "previous_discoveries": agent_results,
    "branch_context": branch_info
}
```

### 5. Redis Schema

```
# Conversation tracking
session:{id}:history        # Full conversation history
session:{id}:agents         # List of agents created
session:{id}:current_branch # Active branch

# Agent tracking
agent:{id}:work            # What the agent discovered/did
agent:{id}:branch          # Which branch it worked on
agent:{id}:status          # Current status
agent:{id}:questions       # Any clarifying questions

# Branch mapping
branch:{name}:agents       # Which agents worked on this branch
branch:{name}:pr           # Associated PR if any
```

### 6. Example Scenarios

#### Scenario 1: Question
```
User: /orch why didn't the agent run copilot?
System: Creates research-agent to investigate logs and Redis
Agent: Returns findings about task completion logic
```

#### Scenario 2: Continuation
```
User: /orch tell the same agent to also update the docs
System: Finds previous agent's branch and context
Agent: Continues on same branch with prior knowledge
```

#### Scenario 3: Clarification
```
User: /orch analyze the performance issues
Agent: "Which component: frontend, backend, or database?"
System: Routes question back to user
User: backend API endpoints
Agent: Proceeds with specific analysis
```

---

## Implementation Plan

### Phase 1: Core Infrastructure (Priority: High)
1. **Replace task_dispatcher.py with instruction_analyzer.py**
   - Remove all hardcoded task type patterns
   - Implement LLM-based instruction understanding
   - Support all instruction categories

2. **Enhance Redis context management**
   - Implement conversation history tracking
   - Store agent relationships and discoveries
   - Enable branch mapping

3. **Update agent factory for continuations**
   - Support continuing on existing branches
   - Pass full context to new agents
   - Handle meta-instructions

### Phase 2: Agent Communication (Priority: High)
1. **Bidirectional communication channel**
   - Agent → User clarification requests
   - User → Agent additional instructions
   - Real-time status updates

2. **Context window management**
   - Summarize long conversations
   - Preserve critical context
   - Handle multi-turn interactions

### Phase 3: Testing & Refinement (Priority: Medium)
1. **Test scenarios**
   - Question handling
   - Task continuation
   - Research requests
   - Clarification flows

2. **Performance optimization**
   - Redis query efficiency
   - Context compression
   - Agent startup time

### Phase 4: Advanced Features (Priority: Low)
1. **Multi-agent collaboration**
   - Agents working together
   - Shared discoveries
   - Coordinated branches

2. **Learning system**
   - Remember successful patterns
   - Improve instruction understanding
   - Optimize agent creation

## Key Benefits
1. **Universal instruction handling** - Any request type works
2. **Context preservation** - Agents know full history
3. **Branch continuity** - Work continues where it left off
4. **Natural communication** - Clarifications and questions supported
5. **No hardcoding** - LLM understands intent naturally

## Migration Strategy
1. Keep existing system running
2. Implement new system in parallel
3. Test with select commands first
4. Gradually migrate all orchestration
5. Deprecate old task_dispatcher

## Success Metrics
- Agents correctly continue previous work
- No hardcoded patterns remain
- Any instruction type handled appropriately
- Context preserved across agents
- User satisfaction with natural interaction
