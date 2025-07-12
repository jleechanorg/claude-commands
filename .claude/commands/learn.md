# /learn Command

**Purpose**: Capture and document learnings from corrections and mistakes with enhanced analysis

**Usage**: `/learn [optional: specific learning or context]`

**Enhanced Behavior**:
1. **Sequential Thinking Analysis**: Use `/think` mode for deep pattern recognition and learning extraction
2. **Context Analysis**: If no context provided, analyze recent conversation for learnings using enhanced thinking
3. **Existing Learning Check**: Verify if learning exists in CLAUDE.md or lessons.mdc
4. **CLAUDE.md Proposals**: Generate specific CLAUDE.md additions with 🚨/⚠️/✅ classifications
5. **Automatic PR Workflow**: Create separate learning branch and PR for CLAUDE.md updates
6. **Pattern Recognition**: Identify repeated mistakes and successful recovery patterns
7. **Auto-Learning Integration**: Support automatic triggering from other commands

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

**Enhanced Workflow**:
1. **Deep Analysis**: Use sequential thinking to analyze patterns and extract insights
2. **Classification**: Categorize learnings as 🚨 Critical, ⚠️ Mandatory, or ✅ Best Practice
3. **Proposal Generation**: Create specific CLAUDE.md rule proposals with exact placement
4. **Branch Choice**: Offer user choice between:
   - **Current PR**: Include learning changes in existing work (related context)
   - **Clean Branch**: Create independent learning PR from fresh main branch
5. **Implementation**: Apply changes according to user's branching preference
6. **Documentation**: Generate PR with detailed rationale and evidence
7. **Branch Management**: Return to original context or manage clean branch appropriately

**Auto-Trigger Scenarios**:
- **Merge Intentions**: Triggered by "ready to merge", "merge this", "ship it"
- **Failure Recovery**: After 3+ failed attempts followed by success
- **Integration**: Automatically called by `/integrate` command
- **Manual Request**: Direct `/learn` invocation

**Learning Categories**:
- **🚨 Critical Rules**: Patterns that prevent major failures
- **⚠️ Mandatory Processes**: Required workflow steps discovered
- **✅ Best Practices**: Successful patterns to follow
- **❌ Anti-Patterns**: Patterns to avoid based on failures

**Updates & Integration**:
- CLAUDE.md for critical rules (via automatic PR)
- .cursor/rules/lessons.mdc for detailed technical learnings
- .claude/learnings.md for categorized knowledge base
- Failure/success pattern tracking for auto-triggers
- Integration with other slash commands (/integrate, merge detection)