# PR #1410 Guidelines - Context Optimization: Comprehensive Solution for 79K Token Cache Reduction

## 🎯 PR-Specific Principles

1. **Hook Safety First**: All hooks must be thread-safe and memory-bounded
2. **Performance Validation**: Claims must be measured, not projected
3. **Graceful Degradation**: Errors should never break core functionality
4. **Configuration-Driven**: All thresholds must be configurable, not hardcoded

## 🚫 PR-Specific Anti-Patterns

### ❌ **Unsafe Singleton Pattern**
```python
# WRONG - Race condition in multi-threaded environment
def __new__(cls):
    if cls._instance is None:  # Multiple threads can pass this check
        cls._instance = super().__new__(cls)
        cls._instance._initialize()
    return cls._instance
```

### ✅ **Thread-Safe Singleton Pattern**
```python
# CORRECT - Thread-safe with double-check locking
import threading

class OptimizedCommandOutputTrimmer:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:  # Double-check pattern
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance
```

### ❌ **Unbounded Statistics Accumulation**
```python
# WRONG - Memory leak in long-running processes
self.stats['original_lines'] += original_count
self.stats['trimmed_lines'] += trimmed_count
self.stats['commands_processed'] += 1
# Stats grow forever without bounds
```

### ✅ **Bounded Statistics with Reset**
```python
# CORRECT - Circular buffer or periodic reset
from collections import deque

class StatsManager:
    def __init__(self, max_entries=1000):
        self.recent_stats = deque(maxlen=max_entries)
        self.summary = {'total_saved': 0, 'count': 0}
    
    def add_stat(self, saved_tokens):
        self.recent_stats.append(saved_tokens)
        self.summary['total_saved'] += saved_tokens
        self.summary['count'] += 1
        
        # Reset summary periodically
        if self.summary['count'] > 10000:
            self.reset_summary()
```

### ❌ **No Input Validation**
```python
# WRONG - DoS vulnerability with massive inputs
input_data = sys.stdin.read()  # Could be gigabytes
trimmed_output = trimmer.process_output(input_data)
```

### ✅ **Input Size Validation**
```python
# CORRECT - Bounded input processing
MAX_INPUT_SIZE = 10 * 1024 * 1024  # 10MB limit

input_data = sys.stdin.read(MAX_INPUT_SIZE)
if len(input_data) >= MAX_INPUT_SIZE:
    sys.stderr.write("Input exceeds maximum size, truncating\\n")
    input_data = input_data[:MAX_INPUT_SIZE]
    
trimmed_output = trimmer.process_output(input_data)
```

### ❌ **Magic Numbers Throughout Code**
```python
# WRONG - Hardcoded values make tuning difficult
if len(output) > 500:  # What is 500?
    sample = output[:500]
    
if original_count > 100:  # Why 100?
    trimmed_lines = self.fast_trim(lines, 50)  # Why 50?
```

### ✅ **Configuration Constants**
```python
# CORRECT - Named constants with documentation
class Config:
    # Sample size for command detection (chars)
    DETECTION_SAMPLE_SIZE = 500
    
    # Threshold for aggressive trimming (lines)
    AGGRESSIVE_TRIM_THRESHOLD = 100
    
    # Default max lines for fast trim
    FAST_TRIM_MAX_LINES = 50
    
# Usage
if len(output) > Config.DETECTION_SAMPLE_SIZE:
    sample = output[:Config.DETECTION_SAMPLE_SIZE]
```

## 📋 Implementation Patterns for This PR

### Performance Monitoring Pattern
```python
# Always measure actual performance, don't assume
start_time = time.perf_counter()
result = expensive_operation()
elapsed_ms = (time.perf_counter() - start_time) * 1000

if elapsed_ms > PERFORMANCE_WARNING_THRESHOLD_MS:
    logger.warning(f"Operation took {elapsed_ms:.1f}ms, exceeding threshold")
```

### Graceful Degradation Pattern
```python
# Always pass through original on error
try:
    processed = process_data(input_data)
    return processed
except Exception as e:
    logger.error(f"Processing failed: {e}", exc_info=True)
    return input_data  # Return original, don't fail
```

## 🔧 Specific Implementation Guidelines

1. **Thread Safety**: Use threading.Lock() for all shared state modifications
2. **Memory Management**: Implement circular buffers for statistics (collections.deque)
3. **Input Validation**: Always validate and limit input sizes before processing
4. **Configuration**: Extract all thresholds to configuration with defaults
5. **Error Handling**: Log full stack traces while still returning safe defaults
6. **Performance Claims**: Measure actual metrics, don't project from theory
7. **Testing**: Include thread safety, memory leak, and DoS resistance tests

## 🚨 Security Considerations

- **DoS Prevention**: Limit input sizes to prevent memory exhaustion
- **Thread Safety**: Prevent race conditions in singleton initialization
- **Error Information**: Don't expose internal paths in error messages
- **Resource Limits**: Implement timeouts and memory limits for processing

## 📊 Quality Gates for This PR

- [ ] All critical thread safety issues resolved
- [ ] Memory leak prevention implemented
- [ ] Input validation added with size limits
- [ ] Magic numbers replaced with configuration
- [ ] Performance claims validated with measurements
- [ ] Comprehensive error handling with logging
- [ ] Tests for edge cases and failure modes

## 🎓 Lessons Learned

1. **Singleton patterns in Python need explicit thread safety** - The GIL doesn't protect object creation
2. **Long-running processes reveal memory leaks** - Always bound accumulating data structures
3. **Hook systems are attack vectors** - Input validation is critical for security
4. **Performance claims need evidence** - Measure, don't estimate
5. **Magic numbers multiply debugging time** - Configuration makes systems maintainable

## 📚 References

- PR #1410: https://github.com/jleechanorg/worldarchitect.ai/pull/1410
- Critical Issues: Thread safety (line 30-34), Memory leak (line 142-144), DoS vector (line 214)
- Python Threading Best Practices: https://docs.python.org/3/library/threading.html
- Singleton Pattern Thread Safety: https://stackoverflow.com/questions/50566934/