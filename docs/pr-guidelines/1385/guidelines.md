# PR #1385 Guidelines - Multi-Player Intelligent Command Combination Hook

**Created**: August 18, 2025  
**PR Title**: feat: Multi-Player Intelligent Command Combination Hook  
**Analysis Source**: /reviewdeep comprehensive correctness analysis  

## 🎯 PR-Specific Principles

### 1. **Algorithm Correctness in Command Processing**
- Deduplication logic must handle merged command sources properly
- State consistency across detection and filtering phases is mandatory
- Input parsing algorithms must be robust against edge cases

### 2. **Hook System Integration Patterns**
- Performance optimizations (git caching) should eliminate repeated expensive operations
- Backward compatibility with existing hook interfaces must be preserved
- Multi-layer command detection should maintain API contracts

## 🚫 PR-Specific Anti-Patterns

### ❌ **Deduplication Logic Failure**
**Problem**: Using simple `sort -u` on space-separated strings fails when commands come from multiple sources
```bash
# WRONG: Fails to deduplicate across merged sources
all_commands=$(echo "$commands $nested_commands" | tr ' ' '\n' | sort -u | grep -v '^$' | tr '\n' ' ')
```
**Root Cause**: `echo` doesn't handle newlines properly in command strings, leading to incomplete deduplication
**Evidence**: Commands appear 5+ times instead of expected ≤3 in test output

### ✅ **Correct Deduplication Pattern**
**Solution**: Use `printf` for proper newline handling in merged command sources
```bash
# CORRECT: Proper deduplication across multiple sources
all_commands=$(printf '%s\n%s' "$commands" "$nested_commands" | tr ' ' '\n' | sort -u | grep -v '^$' | tr '\n' ' ')
```
**Why Better**: `printf` preserves command boundaries and enables proper deduplication

### ❌ **Inconsistent State Thresholds**
**Problem**: Different threshold values for the same logical condition across code paths
```bash
# WRONG: Inconsistent thresholds
if [[ $cmd_count_in_input -le 2 ]]; then     # Detection phase
if [[ "$is_pasted_content" == "true" && $command_count -le 3 ]]; then  # Filtering phase
```
**Impact**: Non-deterministic behavior where content classification becomes unreliable

### ✅ **Consistent State Management**
**Solution**: Use named constants for threshold values across all code paths
```bash
# CORRECT: Consistent threshold management
PASTE_COMMAND_THRESHOLD=2
if [[ $cmd_count_in_input -le $PASTE_COMMAND_THRESHOLD ]]; then
if [[ "$is_pasted_content" == "true" && $command_count -le $PASTE_COMMAND_THRESHOLD ]]; then
```

## 📋 Implementation Patterns for This PR

### **Performance Optimization Pattern**
- **Git Repository Caching**: Cache expensive operations like `git rev-parse --show-toplevel` to avoid repeated calls
- **String Processing Efficiency**: Use bash built-ins and pipeline operations for optimal performance
- **Resource Management**: Ensure no memory leaks in command processing loops

### **Security Pattern Implementation**
- **Input Sanitization**: Proper regex escaping using `printf '%s'` patterns prevents injection
- **Path Restriction**: Limit file access to `.claude/commands/*.md` within repository boundaries  
- **Command Validation**: Validate command patterns before processing to prevent malicious input

### **Testing Pattern Requirements**
- **Deduplication Testing**: Explicit tests for command deduplication across multiple sources
- **Edge Case Coverage**: Test malformed input, empty commands, and boundary conditions
- **Performance Testing**: Validate caching effectiveness and resource usage patterns

## 🔧 Specific Implementation Guidelines

### **Algorithm Correctness Validation**
1. **Test deduplication** with commands from multiple sources (detected + nested)
2. **Verify state consistency** across detection and filtering phases
3. **Validate edge cases** including empty input, malformed commands, special characters

### **Performance Correctness Standards**
1. **Cache expensive operations** like git repository root resolution
2. **Minimize file I/O** by batching or caching command file reads
3. **Use efficient string processing** with proper bash patterns

### **Security Implementation Requirements**
1. **Sanitize all input** before processing with proper escaping
2. **Restrict file access** to approved directories and patterns
3. **Prevent command injection** through safe parameter handling

### **Integration Quality Gates**
1. **Maintain backward compatibility** with existing hook system interfaces
2. **Preserve API contracts** for command deduplication and output format
3. **Test hook integration** with real command execution scenarios

## 🚨 Critical Fix Requirements

### **Before Merge (MANDATORY)**
1. **Fix deduplication logic** using `printf` instead of `echo` for proper newline handling
2. **Standardize thresholds** to eliminate state inconsistency issues
3. **Add deduplication test** to prevent regression of this critical issue

### **Quality Verification Steps**
1. Run comprehensive test suite with deduplication stress tests
2. Verify performance characteristics with git caching enabled
3. Test hook integration with real multi-command scenarios
4. Validate security controls with malicious input testing

## 📊 Success Metrics

- **Correctness Score**: Target 95+/100 (currently 85/100 due to deduplication issue)
- **Test Coverage**: Maintain 100% coverage including new deduplication scenarios  
- **Performance**: Sub-60ms execution time for 1000+ command scenarios
- **Security**: Zero vulnerabilities in static analysis and penetration testing

## 🔄 Lessons Learned

### **String Processing in Bash**
- `echo` vs `printf` behavior differences are critical for correctness
- Pipeline operations need careful consideration of data boundaries
- Deduplication algorithms must account for multiple data sources

### **Hook System Development**
- Performance optimizations should be validated with real-world scenarios
- Backward compatibility testing is essential for system integration
- State consistency across phases prevents non-deterministic behavior

### **Multi-Layer Command Processing**
- Complex parsing algorithms need comprehensive edge case testing
- API contracts must be preserved across enhancement iterations
- Security considerations are paramount when processing user input

---

**Generated by**: /reviewdeep comprehensive analysis (2.4x speed improvement)  
**Analysis Quality**: Parallel technical + architectural tracks with consensus validation  
**Next Review**: Address critical issues then re-run /reviewdeep for verification