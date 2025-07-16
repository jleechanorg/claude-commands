# /learn Command

**Purpose**: Capture and document learnings from corrections and mistakes with enhanced analysis and persistent Memory MCP integration

**Usage**: `/learn [optional: specific learning or context]`

**Enhanced Behavior**:
1. **Sequential Thinking Analysis**: Use `/think` mode for deep pattern recognition and learning extraction
2. **Context Analysis**: If no context provided, analyze recent conversation for learnings using enhanced thinking
3. **Existing Learning Check**: Verify if learning exists in CLAUDE.md or lessons.mdc
4. **CLAUDE.md Proposals**: Generate specific CLAUDE.md additions with 🚨/⚠️/✅ classifications
5. **Memory MCP Integration**: Persist learnings to knowledge graph with entity creation and relations
6. **Automatic PR Workflow**: Create separate learning branch and PR for CLAUDE.md updates
7. **Pattern Recognition**: Identify repeated mistakes and successful recovery patterns
8. **Auto-Learning Integration**: Support automatic triggering from other commands

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
2. **Classification**: Categorize learnings as 🚨 Critical, ⚠️ Mandatory, ✅ Best Practice, or ❌ Anti-Pattern
3. **Proposal Generation**: Create specific CLAUDE.md rule proposals with exact placement
4. **Memory MCP Integration**: Store learnings persistently in knowledge graph
   - **Version Check**: Verify backup script is current using `memory/check_backup_version.sh`
   - **Entity Creation**: Create learning entities with proper schema
   - **Duplicate Detection**: Search existing graph to prevent redundant entries
   - **Relation Building**: Connect related learnings and patterns
   - **Observation Addition**: Add learning content to existing entities when appropriate
5. **Branch Choice**: Offer user choice between:
   - **Current PR**: Include learning changes in existing work (related context)
   - **Clean Branch**: Create independent learning PR from fresh main branch
6. **Implementation**: Apply changes according to user's branching preference
7. **Documentation**: Generate PR with detailed rationale and evidence
8. **Branch Management**: Return to original context or manage clean branch appropriately

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
- **Memory MCP Knowledge Graph**: Persistent entities and relations across conversations
- Failure/success pattern tracking for auto-triggers
- Integration with other slash commands (/integrate, merge detection)

**Memory MCP Entity Schema**:
- **Entity Types**: 
  - `learning` - General learnings and corrections
  - `pattern` - Recurring patterns (🚨 Critical, ⚠️ Mandatory)
  - `lesson` - Specific technical lessons (✅ Best Practices)
  - `context` - Project/domain context (❌ Anti-patterns, tool availability)
- **Observations**: Learning content, classification, category, context, evidence
- **Relations**: `relates_to`, `caused_by`, `prevents`, `applies_to`
- **Duplicate Detection**: Search existing entities before creating new ones
- **Error Handling**: Graceful fallback when Memory MCP unavailable

**Memory MCP Implementation Steps**:
1. **Parse Learning Content**: Extract key terms and concepts from learning
2. **Search Existing Graph**: Use `mcp__memory-server__search_nodes` with key terms
3. **Entity Decision Logic**:
   - If similar entity found: Use `mcp__memory-server__add_observations` to extend
   - If no similar entity: Use `mcp__memory-server__create_entities` to create new
4. **Relation Building**: Use `mcp__memory-server__create_relations` to connect related concepts
5. **Validation**: Confirm successful integration and report results

**Integration Function Calls**:
```
# Check backup script version consistency
memory/check_backup_version.sh || echo "Warning: Backup script version mismatch"

# Search for existing similar learnings (with error handling)
try:
    mcp__memory-server__search_nodes(query="[key terms from learning]")
except Exception as e:
    log_error("Memory MCP search failed: " + str(e))
    fallback_to_local_only_mode()

# Create new entity if needed (with error handling)
try:
    mcp__memory-server__create_entities([{
      "name": "[descriptive-learning-name]",
      "entityType": "[learning|pattern|lesson|context]",
      "observations": [
        "Classification: [🚨|⚠️|✅|❌]",
        "Category: [Commands|Testing|Tools|Misconceptions|Patterns]",
        "Content: [actual learning content]",
        "Context: [what triggered this learning]",
        "Evidence: [examples or error messages]"
      ]
    }])
except Exception as e:
    log_error("Memory MCP entity creation failed: " + str(e))
    notify_user("Learning saved locally only - Memory MCP unavailable")

# Build relations to related concepts (with error handling)
try:
    mcp__memory-server__create_relations([{
      "from": "[learning-name]",
      "to": "[related-concept]",
      "relationType": "[relates_to|caused_by|prevents|applies_to]"
    }])
except Exception as e:
    log_error("Memory MCP relation creation failed: " + str(e))
    # Relations are optional - continue without them
```

**Error Handling Strategy**:
- **Graceful Degradation**: Continue with local file updates if Memory MCP fails
- **User Notification**: Inform user when Memory MCP unavailable but learning saved locally
- **Fallback Mode**: Local-only operation when Memory MCP completely unavailable
- **Robust Operation**: Never let Memory MCP failures prevent learning capture