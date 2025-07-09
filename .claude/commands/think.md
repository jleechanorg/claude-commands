# Think Command

**Usage**: `/think [problem/question]`

**Purpose**: Engage in deep, systematic problem-solving using sequential thinking methodology with maximum computation budget.

## Behavior

This command **always** uses the `mcp__sequential-thinking__sequentialthinking` tool with **maximum computation budget** to:
- Break down complex problems into manageable steps
- Allow for revision and course correction during analysis
- Generate and verify solution hypotheses
- Provide detailed reasoning chains
- Handle multi-step solutions with context preservation
- Use the highest level of computational analysis available

## Default Mode

- **Always Ultrathink**: `/think` automatically applies maximum computation budget for the most thorough analysis possible

## Examples

```
/think How should I refactor this codebase to improve maintainability?
/think What's the root cause of this performance issue?
/think Plan the architecture for a new feature that needs to handle 10M requests
```

## Implementation Notes

- Always invokes sequential thinking tool regardless of problem complexity
- Can handle uncertainty and explore alternative approaches
- Supports branching and backtracking in reasoning
- Maintains context across multiple reasoning steps
- Generates concrete, actionable solutions