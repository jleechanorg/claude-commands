# Memory Integration Hooks Documentation

## Overview
This document describes the integration points for automatic Memory MCP enhancement in WorldArchitect.AI.

## Architecture

### Core Module: `mvp_site/memory_integration.py`
- **MemoryIntegration**: Main class for memory operations
- **MemoryMetrics**: Performance tracking
- **enhance_slash_command()**: Entry point for slash commands

### MCP Interface: `mvp_site/mcp_memory_stub.py`
- Stub implementation for testing
- Replace with actual MCP calls in production
- Functions: `search_nodes()`, `open_nodes()`, `read_graph()`

## Integration Points

### 1. Slash Command Enhancement
Commands that automatically get memory context:
- `/learn` - Previous learnings and patterns
- `/debug` - Related error patterns
- `/think` - Historical analysis patterns
- `/analyze` - Past analysis results
- `/fix` - Previous fixes and solutions

**Usage Example**:
```python
from mvp_site.memory_integration import enhance_slash_command

# In slash command handler
memory_context = enhance_slash_command("/debug", "ImportError in auth module")
# memory_context now contains relevant past debugging experiences
```

### 2. Pre-Response Memory Check
Before generating any response, check for relevant memories:

```python
from mvp_site.memory_integration import memory_integration

# In response generation
user_input = "How do I fix git push issues?"
memory_context = memory_integration.get_enhanced_response_context(user_input)
# Inject memory_context into prompt
```

### 3. Error Context Enhancement
When errors occur, automatically search for similar past issues:

```python
def handle_error(error_msg):
    # Search for similar errors
    memories = memory_integration.search_relevant_memory([error_msg])

    # Add to error context
    if memories:
        print("Similar issues found:")
        for memory in memories:
            print(f"- {memory['name']}: {memory['observations'][0]}")
```

### 4. Compliance Reminder System
Check for repeated violations:

```python
def check_compliance_history(rule_type):
    # Search for past violations
    violations = memory_integration.search_relevant_memory([f"violation {rule_type}"])

    if len(violations) > 3:
        return f"⚠️ Reminder: {rule_type} violated {len(violations)} times before"
    return None
```

## Query Optimization Strategies

### 1. Term Extraction
The system automatically extracts:
- **Entity names**: Capitalized words (GitHub, WorldArchitect)
- **Technical terms**: Non-stop words > 2 chars
- **PR references**: PR #123, PR#456
- **Error patterns**: ImportError, TypeError

### 2. Relevance Scoring
Memories scored by:
- **Name match**: 40% weight
- **Type match**: 20% weight
- **Content match**: 30% weight
- **Recency**: 10% weight (when timestamps available)

### 3. Caching Strategy
- **Hot cache**: 5-minute TTL for recent queries
- **Warm cache**: 30-minute TTL for common queries
- **Entity cache**: 1-hour TTL for entity lookups

## Performance Targets
- Query latency: < 50ms (95th percentile)
- Cache hit rate: > 60%
- Memory limit: Top 5 relevant memories per query

## Error Handling
All memory operations gracefully degrade:
- MCP unavailable → Empty memory context
- Search timeout → Use cached results
- Invalid query → Return empty list

## Testing
Run tests with:
```bash
TESTING=true vpython mvp_site/test_memory_integration.py
```

## Migration to Production

### 1. Replace Stub with Real MCP
In `mcp_memory_stub.py`, replace stubs with:
```python
def search_nodes(query):
    return mcp__memory-server__search_nodes(query)

def open_nodes(names):
    return mcp__memory-server__open_nodes(names)

def read_graph():
    return mcp__memory-server__read_graph()
```

### 2. Add to Command Processing
In command handler:
```python
# Before processing command
memory_context = enhance_slash_command(command, args)

# Add to prompt
if memory_context:
    prompt = memory_context + "\n" + original_prompt
```

### 3. Enable Pre-Response Checks
In response generation:
```python
# Before generating response
memories = memory_integration.get_enhanced_response_context(user_input)

# Add to system prompt
if memories:
    system_prompt += f"\n{memories}"
```

## Monitoring
Track performance with built-in metrics:
```python
metrics = memory_integration.metrics
print(f"Cache hit rate: {metrics.cache_hit_rate:.2%}")
print(f"Avg latency: {metrics.avg_latency:.3f}s")
```

## Future Enhancements
1. **Timestamp tracking** for recency scoring
2. **Relationship graph** navigation
3. **Pattern-based prefetching**
4. **Memory summarization** for large results
5. **User feedback** integration for relevance tuning
