# Specialized Agents Guide for WorldArchitect.AI

**How to leverage pre-configured agents for efficient development**

## Overview

Specialized agents in `.claude/agents/` are pre-configured Claude instances optimized for specific domains. They complement your subagent delegation strategy by transforming the 20% of strategic delegations from ad-hoc to systematic.

## Quick Start

1. **Agents are automatically available** - Claude detects and uses them based on task descriptions
2. **Explicit invocation**: Use `Task: "Ask game-mechanics agent to implement critical hit rules"`
3. **Check available agents**: `ls .claude/agents/`

## Available Specialized Agents

### 🎮 game-mechanics
**Purpose**: D&D 5e game logic, combat systems, character progression
**When to use**:
- Implementing new game rules
- Refactoring combat mechanics
- Adding character abilities
- Balancing gameplay elements

### 🤖 ai-prompts
**Purpose**: Gemini API prompt engineering for NPCs, quests, world generation
**When to use**:
- Creating new NPC personalities
- Optimizing narrative generation
- Reducing prompt token usage
- Testing prompt effectiveness

### 🔥 firebase-backend
**Purpose**: Firestore operations, authentication, security rules, APIs
**When to use**:
- Designing data models
- Implementing security rules
- Optimizing database queries
- Building API endpoints

## Integration with Subagent Strategy

### Direct Execution (80% - Default)
Continue using direct execution for:
- Quick fixes and small edits
- Running existing scripts
- Simple debugging
- Sequential workflows

### Specialized Agent Delegation (20% - Strategic)
Use specialized agents when:
- Task matches agent's domain expertise
- Work requires sustained focus on one area
- Multiple related changes needed
- Domain-specific best practices apply

## Usage Examples

### Example 1: Multi-Layer Feature
```
Task: "Implement a guild system feature"

This automatically delegates to multiple agents:
- game-mechanics: Guild mechanics and rules
- firebase-backend: Guild data model and API
- ai-prompts: Guild-related NPC dialogues
```

### Example 2: Focused Development
```
Task: "Ask ai-prompts agent to create a complete prompt system for
      dynamic merchant NPCs with personality traits and haggling"

Direct delegation to specific agent for deep, focused work.
```

### Example 3: Complex Refactoring
```
Task: "Refactor the combat system to support area-of-effect spells"

game-mechanics agent handles:
- Combat service modifications
- Spell effect calculations
- Test coverage for new mechanics
```

## Best Practices

1. **Let Claude Choose**: Often Claude will automatically select the right agent
2. **Be Specific**: Clear task descriptions improve agent selection
3. **Combine Agents**: Complex features may use multiple specialists
4. **Trust Boundaries**: Agents respect their configured permissions
5. **Iterate**: Refine agent prompts based on results

## Creating New Agents

Template for new agents:
```yaml
---
name: agent-name
description: Clear description of when to use this agent
tools: tool1, tool2, tool3  # Optional
---

Detailed system prompt explaining:
- Core responsibilities
- Key files and directories
- Best practices
- Example tasks
```

## Performance Benefits

- **Reduced Setup Time**: No need to explain context repeatedly
- **Consistent Quality**: Agents maintain domain best practices
- **Automatic Delegation**: Claude routes tasks intelligently
- **Context Isolation**: Each agent has clean context window
- **Specialized Expertise**: Deep knowledge in specific domains

## When NOT to Use Specialized Agents

- Simple tasks that take < 2 minutes
- One-off questions or clarifications
- Tasks requiring cross-domain coordination
- When you need direct control over execution

## Monitoring Agent Performance

Track in your scratchpad:
- Which agents handle which features
- Task completion times
- Quality of outputs
- Patterns that work well

## Future Enhancements

Consider creating agents for:
- 🧪 **test-automation**: Playwright/browser testing specialist
- 🎨 **frontend-ui**: UI/UX and JavaScript specialist
- 📊 **analytics**: Performance monitoring and optimization
- 🔒 **security-audit**: Security scanning and fixes
- 📚 **documentation**: README and API documentation

## Conclusion

Specialized agents transform your strategic 20% delegations from manual, ad-hoc processes into systematic, high-quality workflows. They're not a replacement for direct execution but rather a powerful complement for complex, domain-specific work.

Remember: You're still a solo developer. These agents are specialized tools in your toolkit, not a team to manage. Use them to multiply your effectiveness on complex tasks while maintaining simplicity for routine work.
