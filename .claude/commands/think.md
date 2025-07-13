# Think Command

**Usage**: `/think [level] [problem/question]` or `/think [problem/question]`

**Purpose**: Engage in systematic problem-solving using sequential thinking methodology with adjustable computation levels.

## Thinking Levels

1. **Light** (`/think light` or `/think l`): 3-4 thoughts - Quick analysis
2. **Medium** (`/think medium` or `/think m`): 5-6 thoughts - Standard reasoning  
3. **Deep** (`/think deep` or `/think d`): 7-8 thoughts - Thorough analysis
4. **Ultra** (`/think ultra` or `/think u`): 10+ thoughts - Maximum budget

## Default Mode

- **Light by Default**: `/think` uses light mode (4 thoughts) for efficient problem-solving
- **Level Override**: Specify level for different analysis depths

## Behavior

Uses the `mcp__sequential-thinking__sequentialthinking` tool to:
- Break down problems into manageable steps
- Allow for revision and course correction during analysis
- Generate and verify solution hypotheses
- Provide reasoning chains appropriate to the selected level
- Handle multi-step solutions with context preservation

## Examples

```
/think What's wrong with this code?                    # Light: 4 thoughts
/think medium How should I refactor this codebase?     # Medium: 6 thoughts  
/think deep What's the root cause of this issue?       # Deep: 8 thoughts
/think ultra Plan architecture for 10M requests        # Ultra: 12+ thoughts

# Short aliases
/think l Quick bug analysis
/think m Design pattern selection
/think d Performance optimization strategy
/think u Complex system architecture
```

## Implementation Notes

- Uses `totalThoughts` parameter to control thinking depth:
  - Light: `totalThoughts: 4`
  - Medium: `totalThoughts: 6` 
  - Deep: `totalThoughts: 8`
  - Ultra: `totalThoughts: 12`
- Can handle uncertainty and explore alternative approaches
- Supports branching and backtracking in reasoning
- Maintains context across multiple reasoning steps
- Generates concrete, actionable solutions
- Efficient by default with light mode for quick problem-solving