# Context Usage Estimation Command

**Usage**: `/contexte` or `/con`

**Purpose**: First run context estimation, then provide comprehensive analysis with optimization recommendations for Claude Code CLI conversations.

## 🚨 THREE-PHASE EXECUTION WORKFLOW

### 📊 PHASE 1: CONTEXT ESTIMATION
**Primary Analysis & Baseline Metrics**
- **Execute baseline context analysis** using internal token tracking
- **Calculate current session metrics** including tool usage and complexity  
- **Generate context health status** with traffic light system (Green/Yellow/Orange/Red)
- **Display current token consumption** and remaining capacity

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

#### ⚡ PHASE 1 EXECUTION
**Context Estimation Must Run First**
1. Count and categorize ALL tool operations in current session
2. Estimate token usage from conversation history and tool outputs  
3. Calculate session complexity score based on operation types
4. Determine context health status (Green/Yellow/Orange/Red)
5. Display baseline metrics before proceeding

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

### 📊 PHASE 1: CONTEXT ESTIMATION (MANDATORY FIRST)
```
Execute baseline context analysis:
- Analyze current conversation for ALL tool usage patterns
- Estimate approximate token consumption from session data
- Calculate session complexity score (0-100 scale)
- Determine context health status (Green/Yellow/Orange/Red)
- Display baseline context metrics with clear numbers
- Show percentage of context capacity used
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
