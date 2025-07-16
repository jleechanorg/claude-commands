# Learn Command (Working MVP)

**Usage**: `/learn [correction or observation]`

**Purpose**: Store corrections and patterns in persistent memory that actually works.

## Enhanced Learn Implementation

When you use `/learn`, it will:

1. **Auto-detect correction patterns** like "don't do X, do Y"
2. **Store in persistent memory** (local file + eventual Memory MCP)
3. **Track context** (urgent, coding, review, etc.)
4. **Build confidence scores** based on success/failure

## Example Usage

```
/learn Don't use inline imports, use module-level imports instead
→ ✅ Stored correction: dont_do_instead (context: coding)

/learn I prefer structured commit messages with prefixes  
→ ✅ Stored correction: preference (context: workflow)

/learn When urgent, focus on surgical fixes not comprehensive refactoring
→ ✅ Stored correction: context_behavior (context: urgent, coding)
```

## How It Works

```python
# Pattern detection
corrections = detect_correction_patterns(user_input)
# → Finds "don't X, do Y", "I prefer X", "when Y, do Z", etc.

# Context detection  
context = detect_context(user_input)
# → Identifies urgent/quality/coding/review/workflow contexts

# Storage
entity_id = store_correction(correction, context)
# → Saves to ~/.cache/claude-learning/learning_memory.json

# Future application
patterns = query_relevant_patterns(current_context)
# → Retrieves applicable patterns for current situation
```

## Memory Structure

```json
{
  "entities": {
    "correction_20250714_091243": {
      "type": "user_correction",
      "correction_type": "dont_do_instead",
      "pattern": ["inline imports", "module-level imports"],
      "context": ["coding"],
      "confidence": 0.8,
      "applied_count": 0,
      "success_count": 0
    }
  }
}
```

## Integration Points

1. **Before code generation**: Query memory for relevant patterns
2. **After user feedback**: Update confidence scores
3. **Context-aware application**: Different patterns for different situations
4. **Continuous learning**: System gets smarter over time

## Current Status

✅ Working local file storage  
✅ Pattern detection working  
✅ Context detection working  
✅ Memory persistence working  
⚠️ Memory MCP integration pending (permission fix needed)  
🔄 Next: Integration with actual command processing

This creates a genuine learning system that remembers your corrections and gets better over time.