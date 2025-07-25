# ⚠️ REFERENCE ONLY - Requires adaptation for your project setup

# Enhanced Execute Command with Memory Integration

**Purpose**: Memory-aware strategic planning and execution with pattern consultation

**Usage**: 
- `/execute-enhanced` or `/ee` - Memory-enhanced execution with pattern guidance
- Automatically queries learned patterns before execution
- Applies user preferences and corrections from memory
- Provides pattern-informed execution strategies

## 🧠 Memory Integration Features

### Pre-Execution Pattern Query
- **Automatic Consultation**: Queries learned patterns relevant to the task
- **Pattern Categorization**: Groups findings by type (corrections, preferences, workflows)
- **Relevance Scoring**: Prioritizes most relevant patterns for the task
- **Context Awareness**: Considers task complexity and intent

### Pattern-Informed Decision Making
- **Execution Approach**: Chooses strategy based on learned patterns
- **Checkpoint Frequency**: Adjusts based on pattern recommendations
- **Tool Selection**: Applies learned tool preferences (e.g., --puppeteer)
- **User Preferences**: Incorporates documented user workflow preferences

### Memory-Enhanced TodoWrite Checklist
```
## EXECUTE PROTOCOL CHECKLIST - ENHANCED WITH MEMORY
- [ ] Context check: ___% remaining
- [ ] Task complexity assessment: [Auto-determined from patterns]
- [ ] Pattern query completed: ✅ YES
- [ ] Memory insights applied: [Count] relevant patterns found
- [ ] High-confidence corrections applied: [Count]
- [ ] User preferences considered: [Count] 
- [ ] Workflow patterns followed: [Count]
- [ ] Execution approach: [Pattern-informed choice]
- [ ] Checkpoint frequency: [Pattern-recommended frequency]
- [ ] Scratchpad location: roadmap/scratchpad_[branch].md
- [ ] PR update strategy: Push at each checkpoint
```

## 🚨 MANDATORY MEMORY CONSULTATION PROTOCOL

### Phase 1: Memory Query
1. **Extract Task Keywords**: Identify key concepts and technical terms
2. **Query Pattern Database**: Search for relevant learned patterns
3. **Analyze Pattern Relevance**: Score patterns by relevance to current task
4. **Categorize Results**: Group by pattern type (correction, preference, workflow, technical)

### Phase 2: Pattern Application
1. **Critical Corrections**: Apply high-confidence corrections immediately
2. **User Preferences**: Incorporate documented user preferences
3. **Workflow Patterns**: Follow established workflow patterns
4. **Technical Insights**: Apply relevant technical knowledge

### Phase 3: Enhanced Execution
1. **Pattern-Informed Strategy**: Choose execution approach based on memory
2. **Dynamic Checkpoint Frequency**: Adjust based on learned patterns
3. **Tool Selection**: Apply learned tool preferences
4. **Progress Tracking**: Enhanced with pattern application notes

## Memory-Guided Execution Examples

### Example 1: Browser Testing Task
```
Task: "implement browser testing for login form"

Memory Query Results:
🚨 CRITICAL CORRECTIONS (2):
  ⚠️ Always use --puppeteer flag for browser tests in Claude Code CLI
  ⚠️ Use test_mode=true&test_user_id=test-user-123 for auth bypass

🎯 USER PREFERENCES (1):
  • Prefer headless=True for automated tests

📋 ESTABLISHED WORKFLOWS (1):
  • Screenshot failures for debugging

Enhanced Approach:
✅ Use Puppeteer MCP with --puppeteer flag
✅ Apply test mode URL parameters for auth bypass
✅ Configure headless mode for automation
✅ Include screenshot capture for failures
```

### Example 2: API Implementation Task
```
Task: "implement user authentication API endpoints"

Memory Query Results:
🚨 CRITICAL CORRECTIONS (1):
  ⚠️ Use POST method for data submission, not GET

📋 ESTABLISHED WORKFLOWS (2):
  • For complex APIs, use subagent coordination
  • Checkpoint every 3-5 files for API work

🔧 TECHNICAL INSIGHTS (1):
  • Apply defensive programming with isinstance() validation

Enhanced Approach:
✅ Use subagent coordination for complex API work
✅ Apply POST methods for data operations
✅ Checkpoint frequency: Every 3-5 files
✅ Include defensive programming patterns
```

## Integration with Standard Execute

### Backward Compatibility
- Standard `/execute` commands continue to work unchanged
- Enhanced version provides additional memory consultation
- Users can choose between standard and enhanced versions
- Gradual migration path available

### Command Aliases
- `/execute-enhanced` - Full memory-enhanced execution
- `/ee` - Short alias for enhanced execution
- `/e+` - Alternative short alias

### Memory Consultation Decision Tree
```
Should consult memory?
├── High complexity task → YES (always consult)
├── Contains correction keywords → YES (fix, debug, error)
├── Technical implementation → YES (api, database, system)
├── User preference indicators → YES (prefer, like, style)
├── Simple single-step task → NO (quick fixes)
└── Default → YES (when in doubt, consult)
```

## Usage Examples

### Basic Enhanced Execution
```
User: /ee implement JSON parsing improvements
Assistant: I'll implement JSON parsing improvements with memory guidance...

🧠 MEMORY CONSULTATION RESULTS:
Found 3 relevant patterns from 15 total patterns

🚨 CRITICAL CORRECTIONS (1):
  ⚠️ Use robust_json_parser.py for JSON handling, not manual parsing

💡 RECOMMENDATIONS (2):
  • Apply defensive programming for malformed JSON
  • Test JSON edge cases thoroughly

**Complexity Assessment**: Medium
**Recommended Approach**: Direct execution with robust parsing patterns
**Checkpoint Frequency**: Every 5 minutes OR 3-5 files

[Enhanced TodoWrite checklist with memory insights applied]

🚀 READY TO EXECUTE - Beginning implementation with pattern-informed approach...
```

### Plan Mode with Memory
```
User: /plan-enhanced implement user dashboard
Assistant: I'll plan user dashboard implementation with memory consultation...

🧠 MEMORY CONSULTATION RESULTS:
Found 4 relevant patterns from 15 total patterns

🎯 USER PREFERENCES (1):
  • For dashboard projects, prefer subagent coordination

📋 ESTABLISHED WORKFLOWS (2):
  • Use worktrees for parallel frontend/backend work
  • Coordinate on API contract at 25% completion

**Execution Strategy**: Subagent coordination with worktrees
- Frontend subagent: UI components and styling
- Backend subagent: API endpoints and data layer
- Sync point: API contract review at 25%

⏸️ PLAN PRESENTED - Waiting for your approval to proceed...
```

## Memory Learning Integration

### Automatic Pattern Capture
- Execution outcomes automatically feed back to learning system
- User corrections during execution are captured as patterns
- Successful approaches are stored as workflow patterns
- Failed approaches are stored as avoidance patterns

### Continuous Improvement
- Each execution improves the memory base
- Patterns become more accurate with usage
- User-specific preferences build over time
- Command behavior adapts to user working style

This enhanced execute command transforms static command execution into an adaptive, learning-enabled system that improves with each interaction.