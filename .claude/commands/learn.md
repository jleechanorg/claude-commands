# /learn Command

**Purpose**: The unified learning command that captures and documents learnings with Memory MCP integration for persistent knowledge storage

**Usage**: `/learn [optional: specific learning or context]`

**Note**: This is the single, unified `/learn` command. All learning functionality is consolidated here with Memory MCP integration as the default.

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

**Enhanced Memory MCP Entity Schema**:

**High-Quality Entity Types**:
- `technical_learning` - Specific technical solutions with code/errors
- `implementation_pattern` - Successful code patterns with reusable details  
- `debug_session` - Complete debugging journeys with root causes
- `fix_implementation` - Documented fixes with validation steps
- `workflow_insight` - Process improvements with measurable outcomes
- `architecture_decision` - Design choices with rationale and trade-offs
- `user_preference_pattern` - User interaction patterns with optimization

**Enhanced Observations Format**:
- **Context**: Specific situation with timestamp and circumstances
- **Technical Detail**: Exact errors, code snippets, file locations (file:line)
- **Solution Applied**: Specific steps taken with measurable results
- **References**: PR links, commits, files, documentation URLs
- **Reusable Pattern**: How learning applies to other contexts
- **Verification**: How solution was confirmed (test results, metrics)
- **Related Issues**: Connected problems this addresses

**Quality Requirements**:
- ✅ Specific file paths with line numbers (mvp_site/auth.py:45)
- ✅ Exact error messages or code snippets
- ✅ Actionable implementation steps
- ✅ References to PRs, commits, or external resources
- ✅ Measurable outcomes (test counts, performance metrics)
- ✅ Canonical entity names for disambiguation

**Enhanced Relations**: `fixes`, `implemented_in`, `tested_by`, `caused_by`, `prevents`, `optimizes`, `supersedes`, `requires`

**Enhanced Memory MCP Implementation Steps**:

1. **Enhanced Search & Context**:
   - Extract specific technical terms (file names, error messages, PR numbers)
   - Search: `mcp__memory-server__search_nodes(technical_terms)`
   - Log: "🔍 Memory searched: X relevant memories found"
   - Integrate found context naturally into response

2. **Quality-Enhanced Entity Creation**:
   - Use high-quality entity patterns with specific technical details
   - Include canonical naming: `{system}_{issue}_{timestamp}` format
   - Ensure actionable observations with file:line references
   - Add measurable outcomes and verification steps

3. **Structured Observation Capture**:
   ```json
   {
     "name": "{canonical_identifier}",
     "entityType": "{technical_learning|implementation_pattern|debug_session}",
     "observations": [
       "Context: {specific situation with timestamp}",
       "Technical Detail: {exact error/solution/code with file:line}",
       "Solution Applied: {specific steps taken}",
       "Verification: {test results, metrics, confirmation}",
       "References: {PR URLs, commits, files}",
       "Reusable Pattern: {how to apply elsewhere}"
     ]
   }
   ```

4. **Enhanced Relation Building**:
   - Link fixes to original problems: `{fix} fixes {problem}`
   - Connect implementations to locations: `{solution} implemented_in {file}`
   - Associate patterns with users: `{pattern} preferred_by {user}`
   - Build implementation genealogies: `{new_pattern} supersedes {old_pattern}`

5. **Quality Validation**:
   - ✅ Contains specific technical details (error messages, file paths)
   - ✅ Includes actionable information (reproduction steps, fixes)
   - ✅ References external artifacts (PRs, commits, documentation)
   - ✅ Uses canonical entity names
   - ✅ Provides measurable outcomes
   - ✅ Links to related memories explicitly

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

# Create enhanced entity with high-quality patterns (with error handling)
try:
    mcp__memory-server__create_entities([{
      "name": "{system}_{issue_type}_{timestamp}",  # Canonical naming
      "entityType": "{technical_learning|implementation_pattern|debug_session|workflow_insight}",  # Select appropriate type
      "observations": [
        "Context: {specific situation with timestamp and circumstances}",
        "Technical Detail: {exact error message or code with file:line}",
        "Root Cause: {identified cause with evidence}",
        "Solution Applied: {specific implementation steps taken}",
        "Code Changes: {file paths and line numbers modified}",
        "Verification: {test results, performance metrics, confirmation}",
        "References: {PR URLs, commit hashes, related documentation}",
        "Reusable Pattern: {how this solution applies to other contexts}",
        "Classification: [🚨|⚠️|✅|❌] {reason for classification}"
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