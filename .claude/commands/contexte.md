# Context Usage Estimation Command

**Usage**: `/contexte` or `/con`

**Purpose**: First run context estimation, then provide comprehensive analysis with optimization recommendations for Claude Code CLI conversations.

## 🎯 UNIVERSAL COMPOSITION PRINCIPLE

**CRITICAL**: This command uses **Universal Composition** - it MUST call the built-in `/context` command first to get actual data, then provide strategic analysis based on that real data.

**❌ NEVER estimate context usage**  
**✅ ALWAYS call `/context` command first**  
**✅ ALWAYS use actual data from `/context` output**

## 🚨 THREE-PHASE EXECUTION WORKFLOW

### 📊 PHASE 1: CONTEXT ESTIMATION (UNIVERSAL COMPOSITION)
**MANDATORY: Execute Built-in `/context` Command First**
- **🎯 CALL `/context` COMMAND DIRECTLY** - Use Claude Code's built-in context analysis
- **Extract actual token metrics** from `/context` output (not estimated)
- **Parse real context breakdown** (Messages, MCP tools, Memory files, etc.)
- **Use actual percentages and token counts** from `/context` command output
- **Never estimate or guess context usage** - only use `/context` command data

### 🔍 PHASE 2: STRATEGIC ANALYSIS
**Pattern Recognition & Optimization Detection**
- **Context breakdown by operation type** (reads, searches, tool calls)
- **Identify context-heavy operations and patterns** in current session
- **Analyze file read efficiency and sizes** for optimization opportunities
- **Evaluate API response complexity** and tool usage patterns

### 💡 PHASE 3: ACTIONABLE RECOMMENDATIONS  
**Tailored Optimization Guidance**
- **Specific optimization suggestions** tailored to current session state
- **Serena MCP integration opportunities** for efficiency gains
- **Context-efficient workflow alternatives** for detected patterns
- **Strategic checkpoint and recovery recommendations** based on usage

## Implementation

**Execution Method**: Three-phase sequential analysis workflow

### 🎯 MANDATORY EXECUTION SEQUENCE:

#### ⚡ PHASE 1 EXECUTION (UNIVERSAL COMPOSITION)
**MANDATORY: Execute `/context` Command First**
1. **🎯 EXECUTE `/context` COMMAND** - Get actual context data from Claude Code CLI
2. **Parse `/context` output** - Extract real token counts, percentages, breakdowns
3. **Use actual metrics only** - Never estimate, always use `/context` command data
4. **Display actual context status** - Show real usage from `/context` output
5. **Determine health status** based on actual percentage from `/context`

#### 🔍 PHASE 2 EXECUTION  
**Strategic Analysis Based on Phase 1 Results**
1. Analyze Phase 1 metrics for optimization opportunities
2. Identify context-heavy operations (large file reads, repeated searches)
3. Detect inefficient tool usage patterns from session data
4. Evaluate potential for Serena MCP optimization
5. Assess checkpoint timing recommendations

#### 💡 PHASE 3 EXECUTION
**Actionable Recommendations Delivery**
1. Provide context-efficient alternatives for detected patterns
2. Deliver strategic workflow improvements based on analysis
3. Offer tool selection hierarchy guidance  
4. Present session management strategies
5. Conclude with immediate next steps

### Context Estimation Algorithm:
1. **Tool Usage Analysis**: Count and categorize all tool operations
2. **Content Size Estimation**: Approximate tokens from tool outputs and responses
3. **Complexity Scoring**: Weight different operation types by context consumption
4. **Optimization Detection**: Identify inefficient patterns and suggest improvements

### Token Estimation Rules:
- **Base conversation**: ~500-1000 tokens
- **Tool operations**: 100-500 tokens each (varies by type)
- **File reads**: Estimated by file size (chars ÷ 4)
- **Web searches**: ~200-800 tokens per search
- **Large responses**: Actual character count ÷ 4
- **Serena MCP**: 50-200 tokens (very efficient)

### Claude Sonnet 4 Limits:
- **Enterprise**: 500K tokens
- **Paid Plans**: 200K tokens
- **Estimation Accuracy**: ±20% variance expected

## Output Formats

### Basic Output:
```
📊 CONTEXT USAGE ESTIMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔹 Estimated Tokens Used: ~15,400 / 500,000 (3.1%)
🔹 Session Complexity: Medium (Score: 34/100)  
🔹 Tools Used: 8 operations (4 types)
🔹 Context Status: ✅ HEALTHY

💡 Quick Tip: Consider /checkpoint if planning complex analysis
```

### Detailed Analysis:
- Token breakdown by operation type
- Identification of context-heavy operations  
- File read patterns and efficiency analysis
- Optimization opportunities and recommendations

## 🚨 EXECUTION INSTRUCTIONS FOR CLAUDE

When `/contexte` is invoked, **MUST EXECUTE ALL THREE PHASES SEQUENTIALLY**:

### 📊 PHASE 1: CONTEXT ESTIMATION (MANDATORY FIRST) - UNIVERSAL COMPOSITION
```
🎯 EXECUTE BUILT-IN `/context` COMMAND:
- ALWAYS call `/context` command first to get actual data
- Extract real token counts from `/context` output  
- Parse actual breakdown (Messages, MCP tools, Memory files, etc.)
- Use real percentages and usage metrics from `/context`
- Never estimate or calculate - only use `/context` command data
- Display actual context status based on `/context` output
```

### 🔍 PHASE 2: STRATEGIC ANALYSIS (BASED ON PHASE 1)
```
Analyze Phase 1 results for optimization opportunities:
- Identify specific context-heavy operations from session
- Suggest context-efficient alternatives for current patterns  
- Recommend Serena MCP opportunities where applicable
- Provide strategic checkpoint guidance based on usage
- Offer workflow improvement suggestions tailored to session
```

### 💡 PHASE 3: ACTIONABLE RECOMMENDATIONS (FINAL PHASE)
```
Deliver immediate actionable advice:
- Specific optimization actions for current session
- Tool selection hierarchy improvements
- Session management strategies  
- Future workflow enhancements
- Next steps for context efficiency
```

## Integration

### Auto-triggered Recommendations:
- High complexity sessions (60+ score): Suggest optimization
- Large file operations detected: Recommend Serena MCP  
- Context approaching 50%: Recommend checkpoint

### Command Usage:
```bash  
/contexte    # Execute all three phases: Context Estimation → Strategic Analysis → Actionable Recommendations
/con         # Alias for /contexte
```
