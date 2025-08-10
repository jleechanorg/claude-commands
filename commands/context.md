# Context Usage Estimation Command

**Usage**: `/context [--detailed] [--optimize]` or `/con`

**Purpose**: Display estimated current context consumption, session complexity analysis, and optimization recommendations for Claude Code CLI conversations.

## Features

### Basic Context Estimation
- **Current session token usage** (approximate)
- **Remaining context capacity** 
- **Session complexity score**
- **Tool operation count and types**

### Detailed Analysis (`--detailed`)
- **Token breakdown by operation type**
- **Context-heavy operations identified**
- **File read patterns and sizes**
- **API response complexity analysis**

### Optimization Mode (`--optimize`)
- **Specific recommendations for current session**
- **Serena MCP opportunities identified**
- **Context-efficient alternatives suggested**
- **Strategic checkpoint recommendations**

## Implementation

**Execution Method**: Direct analysis using conversation patterns and tool usage tracking

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

## Integration

### Auto-triggered Recommendations:
- High complexity sessions (60+ score): Suggest optimization
- Large file operations detected: Recommend Serena MCP  
- Context approaching 50%: Recommend checkpoint

### Command Composition:
```bash  
/context --optimize    # Show optimization suggestions
/context --detailed    # Comprehensive analysis
```
