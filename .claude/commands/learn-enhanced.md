# Learn Command (Enhanced with Pattern Recognition)

**Usage**: `/learn [specific learning or observation]`

**Purpose**: Capture lessons learned from mistakes, corrections, user feedback, or observed patterns. This enhanced version automatically detects patterns and updates the cognitive enhancement system.

## Behavior

When invoked, the command will:

1. **Pattern Detection**: Analyze the learning for implicit patterns
   - Code style preferences ("use X instead of Y")
   - Review feedback patterns
   - Workflow preferences
   - Context-dependent behaviors

2. **Deep Analysis**: Use sequential thinking to understand:
   - Why this pattern matters
   - When it should apply
   - How it relates to existing patterns
   - Confidence level assignment

3. **Documentation Updates**:
   - Update PATTERNS.md with new/reinforced patterns
   - Adjust confidence levels based on confirmations/contradictions
   - Update CONTEXT_AWARENESS.md if context-dependent

4. **Memory Integration**:
   - Create/update memory entities for the pattern
   - Establish relationships with related patterns
   - Track pattern success/failure rates

5. **Automatic Categorization**:
   - Code Style: Naming, formatting, structure preferences
   - Review Preferences: What to focus on, how to communicate
   - Workflow Patterns: Order of operations, tool usage
   - Quality Standards: Testing requirements, documentation needs
   - Context Behaviors: Urgency responses, mode switching

## Auto-Detection Triggers

The enhanced /learn automatically activates when:
- User corrects behavior: "Don't do X, do Y instead"
- User expresses preference: "I prefer...", "Always...", "Never..."
- Pattern emerges from multiple interactions
- Context-specific instruction given: "When urgent, focus on..."
- Review feedback indicates consistent preference

## Pattern Confidence Levels

- **100%**: Explicit rule in CLAUDE.md or consistent user correction
- **90-99%**: Multiple confirmations, no contradictions
- **80-89%**: Clear pattern with occasional exceptions
- **70-79%**: Emerging pattern, needs more data
- **60-69%**: Tentative pattern, under observation
- **<60%**: Insufficient data or contradictory evidence

## Integration with Cognitive Enhancement

1. **Pattern Application**: Future code generation checks PATTERNS.md
2. **Context Awareness**: Applies patterns based on detected context
3. **Continuous Learning**: Each success/failure updates confidence
4. **Memory Queries**: Can retrieve related patterns and their history

## Examples

### Simple Learning
```
/learn When user says "quick fix", they expect focused changes with targeted testing, not comprehensive refactoring
```

### Auto-Detected Pattern
```
User: "Use 'feat:' not 'feature:' in commit messages"
[Auto-learns: Commit prefix preference pattern with 100% confidence]
```

### Context-Dependent Learning
```
/learn In emergency contexts, minimal documentation is acceptable but must be followed up
```

### Review Preference Learning
```
/learn User focuses heavily on error handling in code reviews - always ensure comprehensive try/catch blocks
```

## Implementation Details

The command:
1. Extracts the pattern using regex and NLP techniques
2. Categorizes based on keywords and context
3. Updates relevant documentation files
4. Creates memory entities with observations
5. Links patterns to form a knowledge graph
6. Adjusts future behavior based on patterns

## Benefits Over Basic /learn

- **Automatic Pattern Recognition**: No need to explicitly state patterns
- **Context Sensitivity**: Understands when patterns apply
- **Confidence Tracking**: Patterns strengthen or weaken over time
- **Relationship Mapping**: Sees connections between patterns
- **Behavioral Adaptation**: Actually changes AI behavior, not just documents

This enhanced version transforms /learn from a simple note-taking tool into an intelligent system that continuously improves its alignment with user preferences and working style.