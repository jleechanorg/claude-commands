# PR #1370 Guidelines - CRDT Memory Backup System

## 🎯 PR-Specific Principles
- **Mathematical Correctness First**: CRDT implementations must satisfy mathematical properties before code quality concerns
- **Property-Based Validation**: All distributed algorithms require property-based tests to validate correctness
- **Collision-Resistant Design**: Use cryptographically secure identifiers in distributed systems
- **Evidence-Based Claims**: Any correctness claims must be backed by passing property tests

## 🚫 PR-Specific Anti-Patterns

### ❌ **CRDT Mathematical Property Violations**
**Problem**: Implementing merge algorithms without ensuring mathematical properties hold
```python
# WRONG - Non-deterministic behavior for identical values
elif new_ts == existing_ts:
    existing_uid = existing['_crdt_metadata'].get('unique_id', '')
    new_uid = entry['_crdt_metadata'].get('unique_id', '')
    if new_uid > existing_uid:
        entries_by_id[entry_id] = entry
    # Missing case: what if new_uid == existing_uid?
    # Result: Input order determines outcome → violates commutativity
```

### ✅ **Mathematically Correct CRDT Implementation**
**Solution**: Add explicit deterministic tiebreaker for all edge cases
```python
# CORRECT - Deterministic behavior in all cases
elif new_ts == existing_ts:
    existing_uid = existing['_crdt_metadata'].get('unique_id', '')
    new_uid = entry['_crdt_metadata'].get('unique_id', '')
    if new_uid > existing_uid:
        entries_by_id[entry_id] = entry
    elif new_uid == existing_uid:
        # Deterministic content-based tiebreaker
        existing_hash = hash(json.dumps(existing, sort_keys=True))
        new_hash = hash(json.dumps(entry, sort_keys=True))
        if new_hash > existing_hash:
            entries_by_id[entry_id] = entry
```

### ❌ **Predictable Unique ID Generation**
**Problem**: Using predictable formats that allow collisions
```python
# WRONG - Predictable format vulnerable to collisions
unique_id = f"{self.host_id}_{entry_id}_{timestamp}_{random_suffix}"
```

### ✅ **Collision-Resistant Unique IDs**
**Solution**: Use cryptographically secure random identifiers
```python
# CORRECT - Collision-resistant unique IDs
unique_id = str(uuid.uuid4())  # 128-bit cryptographically secure
```

### ❌ **Unvalidated Distributed Algorithm Claims**
**Problem**: Claiming CRDT properties without property-based test validation
```python
# WRONG - Claims without validation
def crdt_merge(memory_lists):
    """
    GUARANTEES:
    - Commutativity: merge(A,B) = merge(B,A)  # ❌ Not actually tested
    - Associativity: merge(merge(A,B),C) = merge(A,merge(B,C))  # ❌ Not validated
    """
```

### ✅ **Evidence-Based Correctness Claims**
**Solution**: Back all claims with passing property tests
```python
# CORRECT - Claims backed by tests
def crdt_merge(memory_lists):
    """
    GUARANTEES (validated by property tests):
    - Commutativity: merge(A,B) = merge(B,A)  ✅ test_commutativity() passes
    - Associativity: merge(merge(A,B),C) = merge(A,merge(B,C))  ✅ test_associativity() passes
    """

# Accompanying property tests
@given(st.lists(st.lists(memory_entry_strategy())))
def test_commutativity(memory_lists):
    if len(memory_lists) >= 2:
        result_ab = crdt_merge([memory_lists[0], memory_lists[1]])
        result_ba = crdt_merge([memory_lists[1], memory_lists[0]])
        assert result_ab == result_ba, "Commutativity violation detected"
```

## 📋 Implementation Patterns for This PR

### **CRDT Implementation Checklist**
1. **Mathematical Properties First**: Implement with mathematical correctness as primary goal
2. **Property-Based Testing**: Write Hypothesis tests for all CRDT properties before implementation
3. **Deterministic Tiebreakers**: Handle ALL edge cases explicitly, no implicit behavior
4. **Collision-Resistant IDs**: Use UUID4 or cryptographically secure alternatives
5. **Evidence-Based Documentation**: Only document guarantees that are validated by tests

### **Security Patterns Applied**
1. **Subprocess Safety**: Use `subprocess.run()` with explicit arguments, never `shell=True`
2. **Timeout Enforcement**: All network/Git operations have explicit timeouts (30s)
3. **Input Validation**: JSON structure validation before processing
4. **Path Security**: Validate and sanitize all file paths, reject symlinks

### **Error Handling Patterns**
1. **Graceful Degradation**: Fallback strategies for all external dependencies
2. **Recovery Metadata**: Add minimal recovery metadata for entries missing CRDT data
3. **Memory Bounds**: Explicit limits with monitoring and early failure
4. **Exponential Backoff**: Retry logic for transient failures

## 🔧 Specific Implementation Guidelines

### **CRDT Merge Algorithm Requirements**
- **Single-pass processing**: Avoid multi-pass algorithms that can introduce order dependencies
- **Explicit edge case handling**: Every conditional branch must have deterministic behavior
- **Timestamp normalization**: Convert all timestamps to UTC for consistent comparison
- **Content-based tiebreaking**: When metadata is identical, use deterministic content comparison

### **Testing Requirements**
- **Property tests mandatory**: All CRDT implementations require Hypothesis property tests
- **Integration tests with real backends**: Test with actual Git repositories, not just mocks
- **Parallel execution simulation**: Test concurrent operations that could cause race conditions
- **Memory bounds validation**: Test behavior at and beyond configured limits

### **Security Implementation Standards**
- **No shell=True**: All subprocess calls use explicit argument lists
- **Timeout everything**: External operations require explicit timeout values
- **Input sanitization**: Validate structure and content before processing
- **Error logging**: Log failures without exposing sensitive information

## 🧪 Quality Gates for CRDT Systems

### **Pre-Merge Requirements**
1. ✅ All property tests pass (commutativity, associativity, idempotence)
2. ✅ Integration tests with concurrent operations pass
3. ✅ Memory bounds testing shows graceful failure at limits
4. ✅ Security review confirms no subprocess/timeout vulnerabilities
5. ✅ Performance testing shows acceptable merge times

### **Mathematical Property Validation**
```python
# Required test patterns for any CRDT implementation
def test_commutativity(entries_a, entries_b):
    assert crdt_merge([entries_a, entries_b]) == crdt_merge([entries_b, entries_a])

def test_associativity(entries_a, entries_b, entries_c):
    ab_c = crdt_merge([crdt_merge([entries_a, entries_b]), entries_c])
    a_bc = crdt_merge([entries_a, crdt_merge([entries_b, entries_c])])
    assert ab_c == a_bc

def test_idempotence(entries):
    single = crdt_merge([entries])
    double = crdt_merge([entries, entries])
    assert single == double
```

## 🎯 Historical Context

This PR implements a CRDT-based memory backup system to replace lock-based approaches that were causing race conditions. The key insight is that mathematical correctness of the CRDT implementation is more critical than performance or code elegance - a fast, well-structured CRDT that violates mathematical properties provides no benefit over the original lock-based approach.

**Key Learning**: When implementing distributed algorithms, property-based testing is not optional - it's the only way to validate that theoretical guarantees hold in practice.