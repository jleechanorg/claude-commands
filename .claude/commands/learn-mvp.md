# Learn Command MVP (Memory MCP Integration)

**Usage**: `/learn [correction or observation]`

**Purpose**: Store corrections and patterns in persistent memory using Memory MCP server.

## Phase 1 Implementation: Working Correction Storage

### Automatic Pattern Detection
When user provides corrections, automatically detect and store them:

```python
import re

def detect_correction_patterns(text):
    patterns = [
        r"don't\s+(.*?),\s*(.*)",           # "don't do X, do Y"
        r"use\s+(.*?)\s+instead\s+of\s+(.*?)",  # "use X instead of Y"  
        r"i\s+prefer\s+(.*)",              # "I prefer X"
        r"when\s+(.*?),\s*(.*)",           # "When context, do behavior"
        r"always\s+(.*)",                  # "Always do X"
        r"never\s+(.*)",                   # "Never do X"
    ]
    
    corrections = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            corrections.append({
                'type': 'correction',
                'pattern': match,
                'original_text': text
            })
    
    return corrections
```

### Memory Entity Creation
Store each correction as a persistent memory entity:

```python
def store_correction(correction, context):
    entity_name = f"correction_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Create correction entity
    create_entities([{
        "name": entity_name,
        "entityType": "user_correction", 
        "observations": [
            f"Original text: {correction['original_text']}",
            f"Correction type: {correction['type']}",
            f"Context: {context}",
            f"Pattern: {correction['pattern']}",
            f"Confidence: 0.8",  # Start with high confidence
            f"Created: {datetime.now().isoformat()}"
        ]
    }])
    
    # Link to user preference
    create_relations([{
        "from": "jleechan2015",
        "to": entity_name,
        "relationType": "corrected_with"
    }])
    
    return entity_name
```

### Context Detection
Identify the context when correction was given:

```python
def detect_context(user_message, conversation_history):
    context_indicators = {
        'urgent': ['quick', 'urgent', 'asap', 'immediately', 'fast'],
        'quality': ['careful', 'thorough', 'comprehensive', 'detailed'],
        'coding': ['function', 'class', 'variable', 'import', 'test'],
        'review': ['pr', 'review', 'check', 'verify', 'approve'],
        'workflow': ['command', 'process', 'step', 'procedure']
    }
    
    detected_contexts = []
    text = user_message.lower()
    
    for context, keywords in context_indicators.items():
        if any(keyword in text for keyword in keywords):
            detected_contexts.append(context)
    
    return detected_contexts or ['general']
```

## Enhanced Command Implementation

```python
def enhanced_learn_command(user_input):
    # Extract the learning content
    learning_content = user_input.replace('/learn', '').strip()
    
    # Detect context
    context = detect_context(learning_content, conversation_history)
    
    # Detect correction patterns
    corrections = detect_correction_patterns(learning_content)
    
    if corrections:
        # Store each correction as memory entity
        stored_entities = []
        for correction in corrections:
            entity_name = store_correction(correction, context)
            stored_entities.append(entity_name)
        
        return f"✅ Stored {len(corrections)} corrections as memory entities: {stored_entities}"
    else:
        # Store as general observation
        entity_name = store_general_observation(learning_content, context)
        return f"✅ Stored observation as memory entity: {entity_name}"

def store_general_observation(content, context):
    entity_name = f"observation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    create_entities([{
        "name": entity_name,
        "entityType": "general_observation",
        "observations": [
            f"Content: {content}",
            f"Context: {context}",
            f"Type: general_learning",
            f"Created: {datetime.now().isoformat()}"
        ]
    }])
    
    return entity_name
```

## Memory Query Integration

Before significant actions, query memory for relevant patterns:

```python
def query_relevant_patterns(current_context, action_type):
    # Search for corrections in similar contexts
    query = f"correction context:{current_context} type:{action_type}"
    
    relevant_nodes = search_nodes(query)
    
    applicable_patterns = []
    for node in relevant_nodes:
        # Extract pattern and confidence from observations
        pattern_info = parse_memory_observations(node)
        if pattern_info['confidence'] > 0.6:  # Only apply high-confidence patterns
            applicable_patterns.append(pattern_info)
    
    return applicable_patterns

def apply_memory_patterns(patterns):
    guidance = []
    for pattern in patterns:
        guidance.append(f"• {pattern['rule']} (confidence: {pattern['confidence']})")
    
    if guidance:
        return f"📝 Applying learned patterns:\n" + "\n".join(guidance)
    else:
        return "📝 No relevant patterns found in memory"
```

## Success Tracking

Track when patterns are successfully applied:

```python
def track_pattern_success(applied_patterns, user_feedback):
    # Detect if user provided corrections after applying patterns
    new_corrections = detect_correction_patterns(user_feedback)
    
    for pattern in applied_patterns:
        if new_corrections:
            # Pattern failed, reduce confidence
            update_pattern_confidence(pattern['entity_name'], -0.2)
        else:
            # Pattern worked, increase confidence
            update_pattern_confidence(pattern['entity_name'], +0.1)

def update_pattern_confidence(entity_name, adjustment):
    # Add observation about confidence change
    add_observations([{
        "entityName": entity_name,
        "contents": [
            f"Confidence adjusted by {adjustment}",
            f"Updated: {datetime.now().isoformat()}"
        ]
    }])
```

## Integration Points

1. **Enhanced /learn command**: Processes corrections and stores in memory
2. **Pre-action queries**: Check memory before code generation or decisions  
3. **Success tracking**: Update confidence based on user feedback
4. **Pattern application**: Use high-confidence patterns to guide behavior

## Success Metrics

- ✅ Corrections automatically detected and stored
- ✅ Memory entities created with proper relationships
- ✅ Context-aware pattern retrieval working
- ✅ Confidence scores adjust based on success/failure
- ✅ Fewer repeated corrections over time

This creates a genuine learning system that gets smarter with each interaction.