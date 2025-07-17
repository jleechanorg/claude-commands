# Memory MCP Read Specification

## Overview

This specification defines how to read from Memory MCP for compliance enforcement, learning retrieval, and pattern recognition. Currently, the system is write-only - this spec addresses how to implement read functionality.

## Current State Analysis

### Storage Locations
1. **Local MCP Storage**: `~/.cache/mcp-memory/memory.json`
   - Real-time updates from Memory MCP
   - Source of truth for current session
   
2. **Repository Storage**: `memory/memory.json`
   - Hourly backups (when working)
   - Cross-session persistence
   - Version controlled

3. **Backup Directory**: `memory-backup/memory.json`
   - Secondary backup (purpose unclear)
   - Should probably be removed for clarity

### Current Issues
- Hourly backup failing since 19:00 due to uncommitted changes
- Two memory directories creating confusion
- No read functionality implemented
- Memory MCP functions are mocked, not real

## Read Architecture Design

### 1. Memory MCP Read Functions

```python
# Primary read functions needed
mcp__memory-server__read_graph()      # Get entire knowledge graph
mcp__memory-server__search_nodes(query)  # Search by content
mcp__memory-server__open_nodes(names)    # Get specific entities by name
```

### 2. Compliance Read System

```python
class ComplianceMemoryReader:
    """Read past violations from Memory MCP"""
    
    def get_violation_history(self, violation_type: str = None):
        """Retrieve past compliance violations"""
        # Search for entities with type "compliance_violation"
        results = mcp__memory-server__search_nodes("compliance_violation")
        
        # Filter by specific violation type if provided
        if violation_type:
            results = [r for r in results if violation_type in r.observations]
        
        return results
    
    def get_violation_patterns(self):
        """Analyze patterns in violations"""
        # Read full graph
        graph = mcp__memory-server__read_graph()
        
        # Extract violation entities
        violations = [e for e in graph.entities if e.type == "compliance_violation"]
        
        # Group by type and frequency
        patterns = defaultdict(list)
        for v in violations:
            v_type = extract_violation_type(v)
            patterns[v_type].append(v)
        
        return patterns
    
    def should_remind_about_rule(self, rule_type: str):
        """Check if user should be reminded about a rule"""
        recent_violations = self.get_violation_history(rule_type)
        
        # If >3 violations in last 7 days, return True
        threshold = 3
        recent = filter_by_date(recent_violations, days=7)
        
        return len(recent) >= threshold
```

### 3. Learning Retrieval System

```python
class LearningMemoryReader:
    """Read learnings from Memory MCP"""
    
    def get_learnings_by_category(self, category: str):
        """Get all learnings in a category"""
        query = f"learning-{category}"
        return mcp__memory-server__search_nodes(query)
    
    def get_related_learnings(self, context: str):
        """Find learnings related to current context"""
        # Search for relevant entities
        results = mcp__memory-server__search_nodes(context)
        
        # Filter to learning entities
        learnings = [r for r in results if r.type == "learning"]
        
        return learnings
    
    def get_learning_graph(self):
        """Get full learning knowledge graph with relations"""
        graph = mcp__memory-server__read_graph()
        
        # Extract learning entities and their relations
        learning_graph = {
            "entities": [e for e in graph.entities if e.type == "learning"],
            "relations": [r for r in graph.relations if involves_learning(r)]
        }
        
        return learning_graph
```

### 4. Pre-Response Check System

```python
class PreResponseChecker:
    """Check Memory MCP before responding"""
    
    def __init__(self):
        self.compliance_reader = ComplianceMemoryReader()
        self.learning_reader = LearningMemoryReader()
    
    def check_before_response(self, response_context: dict):
        """Run checks before generating response"""
        reminders = []
        
        # Check for repeated violations
        if self.compliance_reader.should_remind_about_rule("MANDATORY_HEADER"):
            reminders.append("Remember: Include branch header at end of response")
        
        # Check for relevant learnings
        learnings = self.learning_reader.get_related_learnings(response_context["topic"])
        if learnings:
            reminders.append(f"Related learnings: {summarize_learnings(learnings)}")
        
        return reminders
```

### 5. Integration Points

#### A. `/header` Command Enhancement
```python
def header_command():
    # Existing: Check if previous response missing header
    violation_detected = check_previous_response()
    
    # NEW: Check violation history
    reader = ComplianceMemoryReader()
    history = reader.get_violation_history("MANDATORY_HEADER")
    
    if len(history) > 5:
        print(f"⚠️ You've forgotten the header {len(history)} times before!")
        print("Pattern analysis: Usually happens when rushing responses")
```

#### B. `/learn` Command Enhancement
```python
def learn_command(topic):
    # Existing: Save new learning
    save_learning(topic)
    
    # NEW: Check for similar past learnings
    reader = LearningMemoryReader()
    similar = reader.get_related_learnings(topic)
    
    if similar:
        print(f"📚 Found {len(similar)} related learnings:")
        for learning in similar:
            print(f"  - {learning.observations[0]}")
```

#### C. Response Generation Hook
```python
# Hypothetical integration with Claude's response generation
def before_response_hook(context):
    checker = PreResponseChecker()
    reminders = checker.check_before_response(context)
    
    if reminders:
        # Inject reminders into context
        context["system_reminders"] = reminders
```

## Implementation Roadmap

### Phase 1: Fix Storage Issues
1. **Fix backup script**: 
   - Handle uncommitted changes gracefully
   - OR run from a clean worktree
   
2. **Consolidate directories**:
   - Keep only `memory/` directory
   - Remove `memory-backup/` if redundant
   - Update scripts accordingly

### Phase 2: Mock Read Implementation
1. **Create read functions** that work with local JSON
2. **Test compliance checking** with mock data
3. **Build learning retrieval** system

### Phase 3: Real Memory MCP Integration
1. **Replace mocks** with actual MCP calls
2. **Add caching layer** for performance
3. **Implement pre-response hooks**

### Phase 4: Advanced Features
1. **Pattern analysis** across violations
2. **Learning recommendations** based on context
3. **Proactive compliance hints**

## Technical Considerations

### Performance
- Cache frequently accessed data
- Use search instead of full graph reads when possible
- Implement pagination for large result sets

### Reliability
- Fallback to local JSON if MCP unavailable
- Handle missing or corrupted data gracefully
- Log all read operations for debugging

### Privacy
- Only read user's own memory data
- No cross-user memory access
- Respect data retention policies

## Success Metrics

1. **Violation Reduction**: 50% fewer repeated violations
2. **Learning Retrieval**: Successfully surface relevant past learnings
3. **Performance**: Read operations complete in <100ms
4. **Reliability**: 99% uptime for read functionality

## Next Steps

1. Fix the backup script issue (uncommitted changes)
2. Implement Phase 1 storage consolidation
3. Build mock read system for testing
4. Gradually replace with real MCP calls