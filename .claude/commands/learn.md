---
description: /learn Command
type: llm-orchestration
execution_mode: immediate
---
## ⚡ EXECUTION INSTRUCTIONS FOR CLAUDE
**When this command is invoked, YOU (Claude) must execute these steps immediately:**
**This is NOT documentation - these are COMMANDS to execute right now.**
**Use TodoWrite to track progress through multi-phase workflows.**

## 🚨 EXECUTION WORKFLOW

### Phase 1: Execute Documented Workflow

**Action Steps:**
1. Review the reference documentation below and execute the detailed steps sequentially.

## 📋 REFERENCE DOCUMENTATION

# /learn Command

**Purpose**: The unified learning command that captures and documents learnings with native memory integration for persistent knowledge storage

**Usage**: `/learn [optional: specific learning or context]`

**Note**: This is the single, unified `/learn` command. All learning functionality is consolidated here with native memory integration as the default.

**Enhanced Behavior**:
1. **Sequential Thinking Analysis**: Use `/think` mode for deep pattern recognition and learning extraction
2. **Context Analysis**: If no context provided, analyze recent conversation for learnings using enhanced thinking
3. **Existing Learning Check**: Verify if learning exists in CLAUDE.md or lessons.mdc
4. **CLAUDE.md Proposals**: Generate specific CLAUDE.md additions with 🚨/⚠️/✅ classifications
5. **Native Memory Integration**: Persist learnings to Claude's native memory
   - **Universal Usage**: Use `memory_save` for saving learnings
   - **Smart Search**: Use `memory_search` for finding related patterns
   - **Direct Storage**: Save learnings directly with memory_save
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
4. **Native Memory Integration**: Store learnings persistently in native memory
   - **Direct Save**: Use `memory_save` for storing learning content
   - **Search**: Use `memory_search` to find related patterns
   - **Verification**: Check for duplicate entries before saving
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
- **Native Claude Memory**: Persistent memories across conversations
- Failure/success pattern tracking for auto-triggers
- Integration with other slash commands (/integrate, merge detection)

**Enhanced Native Memory Schema**:

**High-Quality Learning Types**:
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
- ✅ Specific file paths with line numbers ($PROJECT_ROOT/auth.py:45)
- ✅ Exact error messages or code snippets
- ✅ Actionable implementation steps
- ✅ References to PRs, commits, or external resources
- ✅ Measurable outcomes (test counts, performance metrics)
- ✅ Canonical entity names for disambiguation

**Enhanced Relations**: `fixes`, `implemented_in`, `tested_by`, `caused_by`, `prevents`, `optimizes`, `supersedes`, `requires`

**Enhanced Native Memory Implementation Steps**:

1. **Enhanced Search & Context**:
   - Extract specific technical terms (file names, error messages, PR numbers)
   - Search: `/memory search "technical terms"` - Use universal composition for optimized search
   - Log results only if found or errors
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

# Search for existing similar learnings

memory_search("[key terms from learning]")

# Save learning to native memory

memory_save({
  "content": "{learning content with context and details}",
  "category": "technical|pattern|workflow|decision",
  "tags": ["implementation", "debugging", "security"]
})
```

**Error Handling Strategy**:
- **Graceful Degradation**: Continue with local file updates if native memory fails
- **User Notification**: Inform user when memory unavailable but learning saved locally
- **Fallback Mode**: Local-only operation when memory completely unavailable
- **Robust Operation**: Never let memory failures prevent learning capture
