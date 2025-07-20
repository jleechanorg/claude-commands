# Memory Search Optimization Strategies

## Executive Summary
This document analyzes Memory MCP search behavior and provides optimization strategies for efficient memory retrieval in WorldArchitect.AI's LLM response enhancement system.

## Memory MCP Function Analysis

### 1. read_graph()
- **Returns**: Complete knowledge graph with all entities and relations
- **Performance**: Fast (<1ms) for current graph size (~60 entities)
- **Best For**: Initial cache population, relationship analysis
- **Scalability Concern**: Will degrade with thousands of entities

### 2. search_nodes(query)
- **Returns**: Entities matching query in name, type, or observations
- **Performance**: Fast substring search across all text fields
- **Best For**: Topic-based retrieval, pattern matching
- **Key Finding**: Searches all observation text, not just entity names

### 3. open_nodes(names)
- **Returns**: Specific entities by exact name match
- **Performance**: Fastest option for known entities
- **Best For**: Targeted retrieval of known memories
- **Limitation**: Requires exact entity names

## Search Strategy Recommendations

### 1. Context-Based Search Hierarchy
```python
def get_relevant_memories(context):
    """Multi-tier search strategy based on context type"""
    
    # Tier 1: Known entity lookup (fastest)
    if has_specific_entities(context):
        return open_nodes(extract_entity_names(context))
    
    # Tier 2: Topic search (moderate)
    if has_topic_keywords(context):
        return search_nodes(extract_keywords(context))
    
    # Tier 3: Full graph analysis (slowest, most comprehensive)
    if needs_relationship_analysis(context):
        return analyze_graph_relationships(read_graph())
```

### 2. Query Type Optimization

#### For User Queries
- Extract key terms: names, technologies, concepts
- Use search_nodes() with most specific term first
- Example: "git push issue" → search_nodes("git push")

#### For Error Context
- Search for exact error messages first
- Fall back to error type/category
- Example: "ImportError" → search_nodes("ImportError")

#### For Compliance Checks
- Use entity type filtering via search
- Example: search_nodes("compliance_issue")

#### For Historical Context
- Search by PR numbers, dates, or event names
- Example: search_nodes("PR #609")

## Relevance Scoring Algorithm

### Scoring Formula
```python
def calculate_relevance_score(entity, query_context):
    """Score entity relevance to query context"""
    score = 0.0
    
    # Name match (highest weight)
    if query_terms_in(entity.name):
        score += 0.4
    
    # Type match (categorical relevance)
    if entity.entityType == context_category:
        score += 0.2
    
    # Observation relevance (content match)
    observation_matches = count_matches_in_observations(entity)
    score += min(0.3, observation_matches * 0.05)
    
    # Recency bonus (newer = more relevant)
    if has_recent_timestamp(entity):
        score += 0.1
    
    return score
```

### Relevance Thresholds
- **High Relevance**: Score ≥ 0.7 (include always)
- **Medium Relevance**: Score 0.4-0.7 (include if < 5 high relevance)
- **Low Relevance**: Score < 0.4 (exclude unless specifically requested)

## Caching Strategy

### 1. Three-Tier Cache Architecture
```python
class MemoryCache:
    def __init__(self):
        self.hot_cache = {}      # Last 10 queries (TTL: 5 min)
        self.warm_cache = {}     # Last 50 queries (TTL: 30 min)
        self.entity_cache = {}   # All entities by name (TTL: 1 hour)
```

### 2. Cache Key Generation
```python
def generate_cache_key(query_type, query_params):
    """Generate consistent cache keys"""
    if query_type == "search":
        return f"search:{normalize_query(query_params)}"
    elif query_type == "open":
        return f"open:{sorted(query_params)}"
    elif query_type == "graph":
        return "graph:full"
```

### 3. Frequently Accessed Patterns
Based on memory analysis, cache these patterns:
- Compliance issues (searched frequently)
- User preferences (jleechan2015 entity)
- Recent patterns/anti-patterns
- Active PR contexts

## Implementation Examples

### 1. Smart Memory Retrieval
```python
async def get_enhanced_context(user_query):
    """Get relevant memories for user query"""
    
    # Check hot cache first
    cache_key = generate_cache_key("search", user_query)
    if cached := hot_cache.get(cache_key):
        return cached
    
    # Extract search terms
    terms = extract_key_terms(user_query)
    
    # Parallel search for efficiency
    results = await asyncio.gather(
        search_nodes(terms[0]) if terms else None,
        open_nodes(extract_entity_names(user_query)),
        search_nodes(detect_error_pattern(user_query))
    )
    
    # Merge and score results
    all_entities = merge_unique(results)
    scored = [(calculate_relevance_score(e, user_query), e) 
              for e in all_entities]
    
    # Return top relevant memories
    relevant = [e for score, e in sorted(scored, reverse=True) 
                if score >= 0.4][:5]
    
    # Cache result
    hot_cache[cache_key] = relevant
    return relevant
```

### 2. Pattern-Based Prefetching
```python
def prefetch_related_memories(current_context):
    """Prefetch likely next queries based on patterns"""
    
    if "compliance" in current_context:
        # Prefetch related compliance patterns
        asyncio.create_task(search_nodes("pattern"))
        asyncio.create_task(search_nodes("anti-pattern"))
    
    if "PR #" in current_context:
        # Prefetch GitHub-related memories
        asyncio.create_task(search_nodes("GitHub"))
        asyncio.create_task(search_nodes("pull request"))
```

### 3. Relationship Graph Navigation
```python
def get_related_context(entity_name, depth=1):
    """Get related entities via relationship graph"""
    
    # Get full graph (cached)
    graph = get_cached_graph()
    
    # Find entity
    entity = next(e for e in graph["entities"] 
                  if e["name"] == entity_name)
    
    # Get related entities
    related = set()
    relations = [r for r in graph["relations"] 
                 if r["from"] == entity_name or r["to"] == entity_name]
    
    for rel in relations:
        related.add(rel["to"] if rel["from"] == entity_name else rel["from"])
    
    # Get entities
    return [e for e in graph["entities"] if e["name"] in related]
```

## Performance Optimization Tips

### 1. Query Optimization
- Use most specific search terms
- Prefer open_nodes() when entity names known
- Batch multiple searches in parallel

### 2. Cache Warming
- Preload frequently accessed entities on startup
- Refresh entity cache hourly
- Keep hot cache small but fresh

### 3. Search Term Extraction
- Focus on nouns and technical terms
- Remove common words ("the", "is", "about")
- Use stemming for better matches

### 4. Memory Growth Management
- Implement pagination for large result sets
- Archive old memories to separate storage
- Use summary entities for historical data

## Monitoring and Metrics

### Key Metrics to Track
1. **Cache Hit Rate**: Target > 60% for hot cache
2. **Query Latency**: Target < 50ms for 95th percentile
3. **Relevance Accuracy**: Track user feedback on memory relevance
4. **Memory Growth Rate**: Monitor entity count growth

### Implementation
```python
class MemoryMetrics:
    def __init__(self):
        self.cache_hits = 0
        self.cache_misses = 0
        self.query_times = []
        self.relevance_feedback = []
    
    def record_query(self, cached, latency):
        if cached:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
        self.query_times.append(latency)
    
    @property
    def cache_hit_rate(self):
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / total if total > 0 else 0
```

## Conclusion

The Memory MCP provides fast, flexible search capabilities suitable for real-time LLM enhancement. Key optimizations:

1. **Use tiered search strategy** based on query specificity
2. **Implement smart caching** with hot/warm/cold tiers
3. **Score relevance** based on multiple factors
4. **Prefetch related memories** based on context patterns
5. **Monitor performance** to maintain sub-50ms latency

With these optimizations, the memory system can efficiently enhance LLM responses with relevant historical context while maintaining fast response times.