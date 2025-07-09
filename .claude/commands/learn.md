# /learn Command

**Purpose**: Capture and document learnings from corrections and mistakes

**Usage**: `/learn [optional: specific learning or context]`

**Behavior**:
1. If no context provided, analyze recent conversation for learnings
2. Check if learning already exists in CLAUDE.md or lessons.mdc
3. If new, add to appropriate section
4. If exists, check if new context adds value
5. Update self-learning patterns for future recognition

**Examples**:
- `/learn` - Analyze recent mistakes/corrections
- `/learn always use source venv/bin/activate` - Add specific learning
- `/learn playwright is installed, stop saying it isn't` - Correct misconception

**Auto-Learning Categories**:
- **Commands**: Correct command usage patterns
- **Testing**: Test execution methods
- **Tools**: Available tools and their proper usage
- **Misconceptions**: Things Claude wrongly assumes
- **Patterns**: Repeated mistakes to avoid

**Updates**:
- CLAUDE.md for critical rules
- .cursor/rules/lessons.mdc for detailed learnings
- .claude/learnings.md for categorized knowledge base