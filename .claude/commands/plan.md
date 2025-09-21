# Plan Command - Execute with Approval

**Purpose**: Context-aware planning that requires user approval before implementation. **CONTEXT-AWARE PLANNING** with intelligent tool selection and universal composition.

**Usage**: `/plan` - Present context-aware execution plan with approval workflow

## 🧠 CONTEXT-AWARE PLANNING PROTOCOL

### Phase 0: Context Assessment (MANDATORY FIRST STEP)

**🔍 Context Assessment**: Every planning session MUST begin with context assessment:
```bash
# Check remaining context capacity to inform planning approach
/context
```

**Context-Informed Planning Strategy**:
- **High Context (60%+ remaining)**: Comprehensive analysis and detailed planning
- **Medium Context (30-60% remaining)**: Targeted analysis with efficient tool selection
- **Low Context (< 30% remaining)**: Lightweight planning with essential tasks only

### Phase 1: Strategic Analysis

**Memory Integration**: Automatically consults Memory MCP for relevant patterns, corrections, and user preferences.

**Guidelines Consultation**: Calls `/guidelines` for systematic mistake prevention and protocol compliance.

**Tool Selection Hierarchy** (Context-Optimized):
1. **Serena MCP** - Semantic analysis for efficient context usage
2. **Targeted Reads** - Limited file reads based on context capacity
3. **Focused Implementation** - Claude direct or /cerebras based on task size
4. **Context Preservation** - Reserve capacity for execution and validation

### Phase 2: Execution Plan Presentation

**📋 CONTEXT-ADAPTIVE PLAN FORMAT**:

**🧠 Context Status**: _____% remaining → **[High/Medium/Low]** complexity planning

**🎯 Universal Composition Strategy**:
- **Primary Command**: `/plan` (this command)
- **Composed Commands**: List of commands that will be naturally integrated
- **Tool Selection**: Context-aware hierarchy (Serena MCP → Read → /cerebras/Claude → Bash)

**⚡ Implementation Approach**:
- **Analysis Tasks**: Minimal context consumption using Serena MCP
- **Generation Tasks**: /cerebras for >10 delta lines, Claude for ≤10 lines (per CLAUDE.md)
- **Integration Tasks**: Efficient tool selection based on remaining context
- **Validation**: Context-appropriate testing depth

**🔀 Execution Method Decision** (Context-Optimized):
- **Parallel Tasks** (0 additional tokens): For simple, independent operations <30 seconds
  * Method: Background processes (&), GNU parallel, xargs, or batched tool calls
  * Best for: File searches, test runs, lint operations, data aggregation
- **Sequential Tasks**: For complex workflows requiring coordination >5 minutes
  * Method: Step-by-step with context monitoring
  * Best for: Feature implementation, architectural changes, complex integrations
- **Reference**: See [parallel-vs-subagents.md](./parallel-vs-subagents.md) for full decision criteria

**🚀 Execution Sequence** (Context-Optimized):
1. **Quick Discovery**: Use Serena MCP for targeted analysis
2. **Smart Generation**: /cerebras for large tasks, Claude for integration
3. **Efficient Validation**: Context-appropriate testing and verification
4. **Clean Integration**: Minimal overhead for final steps

**Timeline**: _____ minutes (context-optimized approach)

### Phase 3: Approval Requirement

**❌ NEVER proceed without explicit user approval**

User must respond with "APPROVED" or specific modifications before execution begins.

### Phase 4: Execute Protocol

**After approval, implements the plan directly with context awareness**:
- Monitor context usage throughout execution
- Apply context-saving strategies when needed
- Use universal composition with other commands naturally
- Preserve context for testing and validation

### Phase 5: Consensus Validation

**🎯 Multi-Agent Quality Assurance**

After Phase 4 execution, automatically run `/consensus` command to validate code quality and deployment readiness.

**Implementation**: See [consensus.md](./consensus.md) for complete consensus validation workflow including:
- 3-round multi-agent validation loop
- Automated test execution per round
- Context-aware test selection
- Early termination triggers
- Evidence-based decision making

**Integration**: Phase 5 executes the full `/consensus` workflow with the implemented changes as input, providing comprehensive quality assurance before completion.

## 🔗 UNIVERSAL COMPOSITION PRINCIPLES

**Command Integration**: `/plan` naturally composes with:
- `/think` - Strategic analysis and problem solving
- `/guidelines` - Mistake prevention and protocol compliance
- `/context` - Continuous context monitoring
- `/cerebras` - High-speed code generation for appropriate tasks
- `/consensus` - Multi-agent validation and quality assurance (Phase 5)
- Memory MCP - Pattern recognition and preference application

**Adaptive Workflow**: The planning process adapts based on:
- Available context capacity
- Task complexity and scope
- User preferences from memory
- Guidelines and protocol requirements

## 📊 TOOL SELECTION CRITERIA

**Context-Efficient Tools** (Prioritized):
- ✅ **Serena MCP**: Semantic operations with minimal context consumption
- ✅ **Targeted Reads**: Specific file sections rather than full files
- ✅ **MultiEdit**: Batch edits to minimize tool overhead
- ✅ **Smart Search**: Grep/Glob before reading files

**High-Performance Generation** (When Appropriate):
- ✅ **/cerebras**: For tasks >10 delta lines with clear specifications
- ✅ **Claude Direct**: For ≤10 delta lines and integration work
- ✅ **Universal Composition**: Natural command integration

**Context Preservation**:
- ❌ Avoid unnecessary file reads
- ❌ Minimize redundant operations
- ❌ Skip verbose output when planning
- ✅ Reserve context for execution and validation

## Example Flow

**Context-Aware `/plan` Flow**:
```
User: /plan implement user authentication
Assistant:

Phase 0 - Context Assessment:
/context → 45% remaining → Medium Context Strategy

Phase 1 - Strategic Analysis:
[Memory consultation for auth patterns]
[Guidelines check for security requirements]
[Serena MCP discovery for efficient analysis]

Phase 2 - Execution Plan:
Context Status: 45% remaining → Medium complexity planning
- Analysis: Use Serena MCP for efficient codebase understanding
- Generation: /cerebras for new auth classes, Claude for integration
- Context preservation: Strategic tool selection

Seeking approval to proceed...

User: APPROVED
Assistant: [Executes context-optimized implementation]
```

## Key Characteristics

- ✅ **Context assessment mandatory first step**
- ✅ **Universal composition with other commands**
- ✅ **Context-adaptive planning depth**
- ✅ **Intelligent tool selection hierarchy**
- ✅ **User approval required before execution**
- ✅ **Memory and guidelines integration**
- ✅ **Efficient execution with context preservation**
- ✅ **Multi-agent consensus validation with automated testing**
- ✅ **Quality assurance loop with early termination**
- ✅ **Test-driven validation per consensus round**
